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

This is an early, deliberately minimal version:
- Product data is a small, hand-picked static set — no live scraping or retailer API integration yet
- No purchase/checkout flow
- Single LLM call, no multi-agent orchestration yet

The goal of v0 is to prove the reasoning approach works before adding live data sources or a purchase journey (which will need real API credentials and auth, saved for a later version).

## How It Works

1. `constraints.txt` — your fit constraints in plain language
2. `products.json` — candidate products (title, description, size chart text)
3. `match.py` — sends both to the model and asks it to rank products by fit, with reasoning
4. Output — a ranked markdown list with a one-line rationale per product

A note on uncertainty: rather than requiring every measurement upfront, constraints are layered — required fields first, optional ones added over time. When a recommendation depends on a field that isn't provided, the agent says so and lowers its confidence, instead of silently assuming an average.

## Stack

Python, Claude API (Anthropic)

## Roadmap

- [ ] Expand product set beyond hand-picked examples
- [ ] Pull from a live product feed or retailer API
- [ ] Add purchase journey (pending API creds / env var setup)
- [ ] Generalize constraint input beyond my own fit profile
- [ ] Normalize sizing across brands/regions using body measurements rather than label

## Why This Exists

This is a working exploration of a broader question I'm thinking about: as agents start shopping on people's behalf, who defines whether a product is "right" — the business selling it, or the customer's actual constraints? This project is a small, concrete attempt to build the second version.
