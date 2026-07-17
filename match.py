"""
Suitability - v0

Given a person's fit constraints and a small set of candidate products,
ask the model to rank products by fit and explain its reasoning -
including when it's uncertain because data is missing.

Usage:
    export ANTHROPIC_API_KEY=your_key_here
    python match.py
"""

import json
import os
import sys
from anthropic import Anthropic

CONSTRAINTS_FILE = "constraints.txt"
PRODUCTS_FILE = "products.json"
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
   size_chart is marked "unavailable", say so explicitly in your reasoning
   and lower your confidence for that recommendation.
2. Distinguish between what you know (stated measurements, stated
   constraints) and what you're inferring (e.g. reasoning from a model's
   height/size on a product page). Label inferences as inferences.
3. If a product conflicts with an explicit "fits to avoid" constraint,
   flag that clearly even if the measurements otherwise look fine.
4. Give each product a confidence level: High, Medium, or Low - based on
   how much real data supports the recommendation, not on how good the
   match seems.
5. Be concise. One short paragraph of reasoning per product, not an essay.

Return your answer as JSON matching this shape:
{
  "rankings": [
    {
      "product_id": "...",
      "product_title": "...",
      "rank": 1,
      "confidence": "High" | "Medium" | "Low",
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


def load_products(path):
    if not os.path.exists(path):
        sys.exit(f"Error: {path} not found. Run this script from the repo root.")
    with open(path, "r") as f:
        return json.load(f)


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


def print_results(results):
    rankings = results.get("rankings", [])
    if not rankings:
        print("No rankings returned.")
        return

    rankings.sort(key=lambda r: r.get("rank", 999))

    print("\n" + "=" * 60)
    print("FIT RECOMMENDATIONS")
    print("=" * 60 + "\n")

    for r in rankings:
        print(f"#{r.get('rank')} - {r.get('product_title')} "
              f"[{r.get('product_id')}]")
        print(f"Confidence: {r.get('confidence')}")
        print(f"Reasoning: {r.get('reasoning')}")
        print("-" * 60)


def main():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit(
            "Error: ANTHROPIC_API_KEY environment variable not set.\n"
            "Run: export ANTHROPIC_API_KEY=your_key_here"
        )

    constraints_text = load_constraints(CONSTRAINTS_FILE)
    products = load_products(PRODUCTS_FILE)

    print(f"Loaded {len(products)} candidate products. Asking the model to rank them...")

    results = get_recommendations(constraints_text, products)
    print_results(results)

    # Also save to file for reference / for the README to link to
    with open("last_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nSaved full results to last_results.json")


if __name__ == "__main__":
    main()