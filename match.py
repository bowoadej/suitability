"""
Suitability - v0

Given a person's fit constraints and a set of candidate products, ask the
model to rank products by fit and explain its reasoning - including when
it's uncertain because data is missing, and including a self-check pass
over its own confidence ratings.

Usage:
    export ANTHROPIC_API_KEY=your_key_here
    python match.py                        # hand-curated products.json (default)
    python match.py --source live           # live_products.json (run fetch_feed.py first)
    python match.py --source merged         # both, combined

Live data:
    export SHOPIFY_STOREFRONT_TOKEN=your_token_here
    python fetch_feed.py                    # writes live_products.json
    python match.py --source merged
"""

import argparse
import json
import os
import sys
from anthropic import Anthropic

CONSTRAINTS_FILE = "constraints.txt"
CURATED_PRODUCTS_FILE = "products.json"
LIVE_PRODUCTS_FILE = "live_products.json"
MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = """You are a fit-matching assistant. You are given a person's
fit constraints (some fields may be marked "unknown" - these are intentionally
unspecified, not zero or average) and a list of candidate products with
whatever size/fit data is available for each.

Your job: rank the products from best to worst fit for this specific person,
and explain your reasoning for each one.

Rules you must follow:
1. Never silently assume a default value for a missing measurement. If a
   recommendation depends on a field marked "unknown" or a product's
   size_chart is marked "unavailable" (or notes it has no numeric
   measurements, as live-API data sometimes does), say so explicitly in
   your reasoning and lower your confidence for that recommendation.
2. Distinguish between what you know (stated measurements, stated
   constraints) and what you're inferring (e.g. reasoning from a style
   descriptor or a model's height/size on a product page, with no numeric
   measurement to back it up). Label inferences as inferences.
3. If a product conflicts with an explicit "fits to avoid" constraint,
   flag that clearly even if the measurements otherwise look fine.
4. Give each product a confidence level: High, Medium, or Low - based on
   how much real data supports the recommendation, not on how good the
   match seems.
5. Give each product an evidence_type: "measurement" if the recommendation
   is grounded in an actual numeric measurement comparison (body vs garment
   measurements), or "descriptor" if it rests on fit language / style
   descriptors / inference with no supporting number. Be consistent: two
   similarly-evidenced products should not receive different confidence
   levels without a stated reason for the difference.
6. Be concise. One short paragraph of reasoning per product, not an essay.

Return your answer as JSON matching this shape:
{
  "rankings": [
    {
      "product_id": "...",
      "product_title": "...",
      "rank": 1,
      "confidence": "High" | "Medium" | "Low",
      "evidence_type": "measurement" | "descriptor",
      "reasoning": "..."
    }
  ]
}

Return ONLY the JSON, no other text, no markdown code fences.
"""


def load_constraints(path):
    if not os.path.exists(path):
        sys.exit(f"Error: {path} not found. Run this script from the repo root.")
    with open(path, "r") as f:
        return f.read()


def load_json_list(path):
    if not os.path.exists(path):
        sys.exit(f"Error: {path} not found. Run this script from the repo root.")
    with open(path, "r") as f:
        return json.load(f)


def load_products(source):
    """
    Load candidate products according to --source:
      curated - hand-curated products.json only (default)
      live    - live_products.json only (run fetch_feed.py first)
      merged  - both, combined and de-duplicated by id
    """
    if source == "curated":
        return load_json_list(CURATED_PRODUCTS_FILE)

    if source == "live":
        if not os.path.exists(LIVE_PRODUCTS_FILE):
            sys.exit(
                f"Error: {LIVE_PRODUCTS_FILE} not found.\n"
                f"Run fetch_feed.py first:\n"
                f"  export SHOPIFY_STOREFRONT_TOKEN=your_token_here\n"
                f"  python fetch_feed.py"
            )
        return load_json_list(LIVE_PRODUCTS_FILE)

    if source == "merged":
        curated = load_json_list(CURATED_PRODUCTS_FILE)
        live = []
        if os.path.exists(LIVE_PRODUCTS_FILE):
            live = load_json_list(LIVE_PRODUCTS_FILE)
        else:
            print(
                f"Note: {LIVE_PRODUCTS_FILE} not found - running with curated "
                f"products only. Run fetch_feed.py to include live data."
            )

        merged, seen_ids = [], set()
        for product in curated + live:
            pid = product.get("id")
            if pid in seen_ids:
                print(f"Warning: duplicate product id '{pid}' - keeping first occurrence.")
                continue
            seen_ids.add(pid)
            merged.append(product)
        return merged

    sys.exit(f"Error: unknown source '{source}'")


def build_user_prompt(constraints_text, products):
    return f"""FIT CONSTRAINTS:
{constraints_text}

CANDIDATE PRODUCTS:
{json.dumps(products, indent=2)}

Rank these products by fit for this person and explain your reasoning,
following the rules in your instructions."""


def get_recommendations(constraints_text, products):
    client = Anthropic()  # reads ANTHROPIC_API_KEY from environment

    response = client.messages.create(
        model=MODEL,
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": build_user_prompt(constraints_text, products)}
        ],
    )

    raw_text = response.content[0].text.strip()

    # Defensive: strip markdown fences if the model adds them anyway
    if raw_text.startswith("```"):
        raw_text = raw_text.strip("`")
        if raw_text.startswith("json"):
            raw_text = raw_text[4:].strip()

    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        print("Warning: model output wasn't valid JSON. Raw output below:\n")
        print(raw_text)
        sys.exit(1)


def audit_confidence(rankings):
    """
    Self-check pass over the model's own confidence ratings, ported from
    the known-unknowns library's auditConfidence logic.

    Returns a list of warning dicts: {"type": ..., "message": ..., "products": [...]}
    """
    warnings = []

    if not rankings:
        return warnings

    # Check 1: top-ranked result has Low confidence.
    top = rankings[0]
    if top.get("confidence") == "Low":
        warnings.append({
            "type": "top-rank-low-confidence",
            "message": (
                f"Top-ranked item '{top.get('product_title')}' has LOW confidence - "
                f"this is the best guess available, not a verified strong match."
            ),
            "products": [top.get("product_id")],
        })

    # Check 2: inconsistent confidence among descriptor-only (non-measurement)
    # rankings. This is the exact bug documented in the README - two
    # similarly-evidenced products rated High and Low with no stated reason.
    inferred_group = [r for r in rankings if r.get("evidence_type") != "measurement"]
    distinct_confidences = {r.get("confidence") for r in inferred_group}

    if len(inferred_group) > 1 and len(distinct_confidences) > 1:
        suspicious_high = [r for r in inferred_group if r.get("confidence") == "High"]
        if suspicious_high:
            warnings.append({
                "type": "inconsistent-inferred-confidence",
                "message": (
                    "Multiple descriptor-only (no numeric measurement) rankings "
                    "have inconsistent confidence levels. The following are rated "
                    "High despite resting on inference rather than measurement, "
                    "while other descriptor-only rankings in this result are rated "
                    "lower - check the reasoning states an actual reason for the "
                    "difference, not just model inconsistency."
                ),
                "products": [r.get("product_id") for r in suspicious_high],
            })

    return warnings


def print_results(results):
    rankings = results.get("rankings", [])
    if not rankings:
        print("No rankings returned.")
        return

    rankings.sort(key=lambda r: r.get("rank", 999))

    print("\n" + "=" * 60)
    print("FIT RECOMMENDATIONS")
    print("=" * 60 + "\n")

    warnings = audit_confidence(rankings)
    for w in warnings:
        print(f"⚠️  {w['message']}\n")

    for r in rankings:
        confidence = r.get("confidence")
        marker = {"High": "●●●", "Medium": "●●○", "Low": "●○○"}.get(confidence, "???")

        print(f"#{r.get('rank')} - {r.get('product_title')} "
              f"[{r.get('product_id')}]")
        print(f"Confidence: {confidence} {marker}  Evidence: {r.get('evidence_type', 'unspecified')}")
        print(f"Reasoning: {r.get('reasoning')}")
        print("-" * 60)

    print("\nNote: rank is the model's best guess at fit. Confidence reflects")
    print("how much real data supports that guess. A low-ranked item with High")
    print("confidence (e.g. a confirmed poor match) can be more trustworthy")
    print("than a top-ranked item with Low confidence.")


def parse_args():
    parser = argparse.ArgumentParser(description="Rank candidate products by fit.")
    parser.add_argument(
        "--source",
        choices=["curated", "live", "merged"],
        default="curated",
        help="Which product data to rank: hand-curated products.json (default), "
             "live_products.json from fetch_feed.py, or both merged.",
    )
    return parser.parse_args()


def main():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit(
            "Error: ANTHROPIC_API_KEY environment variable not set.\n"
            "Run: export ANTHROPIC_API_KEY=your_key_here"
        )

    args = parse_args()

    constraints_text = load_constraints(CONSTRAINTS_FILE)
    products = load_products(args.source)

    print(f"Source: {args.source}")
    print(f"Loaded {len(products)} candidate products. Asking the model to rank them...")

    results = get_recommendations(constraints_text, products)
    print_results(results)

    # Also save to file for reference / for the README to link to
    with open("last_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nSaved full results to last_results.json")


if __name__ == "__main__":
    main()
