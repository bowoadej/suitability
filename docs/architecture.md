# Target Specification: The Agentic Commerce Journey (v1.0 Architecture)

> ⚠️ **Scope Note:** The codebase in `main` (`v0.1`) implements the core foundation: deterministic single-item suitability matching against hard constraints. This document specifies the target end-to-end architecture (`v1.0+`) required to expand that engine across the full e-commerce lifecycle—from high-friction search compression to delegated authorization and handoffs.

---

## 1. The Core Paradigm Shift

Traditional e-commerce is built around synchronous, human-driven navigation: 

$$\text{Search} \longrightarrow \text{Filter Tabs} \longrightarrow \text{Evaluate Trade-offs} \longrightarrow \text{Checkout (3DS)}$$

In that model, **user intent is implicit in the clicks**. High trust exists because the user physically verifies the item at every step on their own device.

When delegating this journey to an agent, that implicit trust breaks. An agent cannot "feel" if a merchant looks legitimate or if a trade-off makes sense. To bridge this gap, the e-commerce journey must be redesigned around **search compression, delegated mandates, and explicit trust boundaries**:

$$\text{User Mandate} \longrightarrow \text{Multi-Merchant Search} \longrightarrow \text{Suitability Scoring} \longrightarrow \left[ \begin{array}{l} \text{Auto-Execute (Low Stakes)} \\ \text{Prepared Cart Handoff (High Stakes)} \end{array} \right]$$

---

## 2. End-to-End E-Commerce Journey Mapping

Here is how each phase of the traditional funnel transforms when shifting from our current single-item matcher (`v0.1`) to the target agentic architecture (`v1.0+`):

| Phase | Traditional E-Commerce | Current Engine (`v0.1`) | Target Agentic Rail (`v1.0+`) |
| :--- | :--- | :--- | :--- |
| **1. Intent & Constraints** | Manual filters (price, size, dates) on a merchant site | Structured input JSON (`rules.json`) | Cryptographically signed **User Delegation Mandate** defining strict boundaries |
| **2. Discovery & Search** | User opens 15 tabs across multiple vendors | Evaluates local/mocked single product data | Asynchronous multi-vendor scraping & API aggregation |
| **3. Qualification** | User manually reads reviews and spec sheets | **Deterministic rule-matching engine** (Pass/Fail) | **Composite Suitability Engine** balancing trade-offs across multiple items/vendors |
| **4. Trust Boundary** | User makes a manual gut-check decision | Outputs binary suitability score | Evaluates risk score: triggers **Auto-Execute** vs **Human Handoff** |
| **5. Execution** | User fills cart, inputs card, completes 3DS | Simulates completion | Submits tokenized payment with attached **Audit Reasoning Trail** |

---

## 3. System Architecture & Flow

---

## 4. API & Payload Specifications

### Phase 1: Delegation Policy (`POST /v1/mandates`)
Before searching, the user delegates authority with precise parameters:

```json
{
  "mandate_id": "mnd_88293011",
  "user_id": "usr_991823",
  "scope": {
    "category": "event_equipment_rental",
    "max_budget_cents": 15000,
    "currency": "GBP",
    "required_delivery_date": "2026-08-15"
  },
  "trust_policy": {
    "auto_purchase_below_cents": 15000,
    "require_human_approval_if": ["vendor_rating_below_4.5", "composite_dependency_detected"]
  }
}


JSON
{
  "transaction_id": "txn_77123982",
  "mandate_id": "mnd_88293011",
  "merchant": "London Bouncy Castles Ltd",
  "amount_cents": 11000,
  "suitability_audit": {
    "options_evaluated": 14,
    "rules_passed": [
      "Dimensions fit yard bounds (15x15ft)",
      "Delivery window matches required date",
      "Price £110 is £40 under maximum threshold"
    ],
    "confidence_score": 0.96
  }
}


JSON
{
  "handoff_id": "hdf_993021",
  "status": "awaiting_human_approval",
  "reason": "Composite purchase detected: Venue cost impacts catering budget constraint.",
  "prepared_checkout_url": "[https://app.suitability.internal/handoff/hdf_993021](https://app.suitability.internal/handoff/hdf_993021)",
  "summary": {
    "shortlisted_option": "St. George's Hall - Evening Slot",
    "total_cost_cents": 250000,
    "unlocked_tradeoffs": "Secures venue, but leaves remaining catering budget at £1,200."
  }
}