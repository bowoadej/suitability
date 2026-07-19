# Suitability

**An agent that decides if a product fits you — not the other way around.**

## The Problem

Finding clothes that fit isn't a search problem, it's a matching problem — and most retailer search doesn't solve it. If you have a harder-to-fit body (long torso, narrow shoulders, inconsistent sizing across brands, etc.), the real answer usually lives in a Reddit thread or forum post, not in the product filters.

This project asks a simple question: what if an agent reasoned about *your* specific constraints against a product, instead of you scrolling through threads trying to guess?

## What It Does (v0)

Given:
- A plain-language description of your fit constraints (body shape, known brand/size quirks, things to avoid)
- A small set of candidate products (title, description, size chart notes)

The agent returns a ranked shortlist of products with **plain-language reasoning** for why each one is — or isn't — a good match.

This is the core mechanic the whole project is built around: not just filtering by category or price, but the agent evaluating *suitability* against your specific constraints and explaining its reasoning.

## Status

**v0 is working, and the reasoning holds up under real constraints.** The strongest result so far: candidate jeans (a Big & Tall range) had a size chart where the only option with the right leg length (38") had a waist nowhere near mine (36.5–37.5" vs my actual 42"), and the sizes that *did* fit my waist only went up to a shorter leg length. No single size satisfied both constraints at once — and the agent caught this, unprompted, by reasoning about waist and length *together* rather than checking each one in isolation. That's the actual thesis in action: most retail search treats each attribute as an independent filter; real fit is a joint condition, and a product can pass every filter individually while still failing the combination.

A second, earlier catch still holds as supporting evidence: a different pair of jeans whose longest available inseam (35") fell short of a stated 38" inseam constraint — flagged as a well-evidenced poor match rather than glossed over.

Also demonstrated: when the same kind of reasoning (a style descriptor implying a fit conflict, with no supporting measurement) showed up in two different products, the agent was initially inconsistent about how confident to be — rating one High and a near-identical case Low with no stated reason for the difference. Tightening the prompt to explicitly distinguish "measurement-backed conflict" from "descriptor-only conflict" fixed this in the next run, with the reasoning now stating *why* two similar-looking conflicts get different confidence levels.

Now running against 8 real products across 6 UK retailers (Uniqlo, Next, Zara, adidas, Boohoo, Moss, ASOS, Levi's/ASOS), still deliberately minimal:
- Product data is a small, hand-picked static set — no live scraping or retailer API integration yet
- No purchase/checkout flow
- Single LLM call, no multi-agent orchestration yet

**A note on uncertainty:** rather than requiring every measurement upfront, constraints are layered — required fields first, optional ones added over time. When a recommendation depends on a field that isn't provided (by the person or the product listing), the agent says so explicitly and lowers its confidence, instead of silently assuming an average.

The goal of v0 was to prove the reasoning approach works before adding live data sources or a purchase journey (which will need real API credentials and auth, saved for a later version). That's now demonstrated, including holding up as constraints and product data have grown more complex — next is expanding data breadth further and improving how rank vs. confidence is displayed.

## How It Works

1. `constraints.txt` — your fit constraints in plain language
2. `products.json` — candidate products (title, description, size chart text)
3. `match.py` — sends both to the model and asks it to rank products by fit, with reasoning
4. Output — a ranked markdown list with a one-line rationale per product

## Stack

Python, Claude API (Anthropic)

## Roadmap

- [x] Populate "fits to avoid" and known brand/size data — done, and the agent now uses both correctly
- [x] Expand product set beyond the first 4 hand-picked examples — now at 8, across 6 retailers
- [ ] Rethink how rank and confidence are displayed together — a top-ranked but low-confidence result can still look stronger than it is; a warning now fires when this happens, but full re-ranking by confidence isn't built yet
- [ ] Normalize sizing across brands/regions using body measurements rather than label size (L, M, etc.)
- [ ] Pull from a live product feed or retailer API
- [ ] Add purchase journey (pending API creds / env var setup)
- [ ] Generalize constraint input beyond my own fit profile

## Why This Exists

This is a working exploration of a broader question I'm thinking about: as agents start shopping on people's behalf, who defines whether a product is "right" — the business selling it, or the customer's actual constraints? This project is a small, concrete attempt to build the second version.