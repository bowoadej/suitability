# Target Specification: Delegated Payment Journey & Handoff Rails

> ⚠️ **Implementation Notice:** This document defines the **target payment architecture** for production-grade agentic execution (`v1.0+`). The current code in `main` implements single-item constraint eligibility (`v0.1`). The specifications below detail the cryptographic mandates, payment gateway interactions, and handoff protocols required to scale to autonomous purchasing.

---

## 1. Context & Problem Statement

Standard e-commerce payment rails rely on synchronous, in-session human checkout (User -> Merchant Gateway -> 3DS Verification). 

Agentic commerce introduces asynchronous, delegated purchasing where an AI agent acts on the user's behalf without real-time human presence. To secure this without friction, payment infrastructure must move from static stored payment credentials to **scoped, cryptographically bound mandates** with deterministic fallback triggers.

---

## 2. System Architecture & Trust Boundaries
Today there is a high-level of trust when I am making a payment on my device. The intent drives my purchase. However when I hand this action to an agent. I need to have implicit trust in its actions, and that they will act in my best interest.

---

## 3. Sequence Flow: Autonomous Low-Stakes Execution

The sequence below outlines how an agent autonomously negotiates and settles a transaction within pre-approved user constraints:

---
---

## 4. API & Payload Specifications

### 4.1 Step A: User Authorization Mandate (`POST /v1/mandates`)

Before the agent initiates an external search or transaction, the client app registers an explicit delegation policy:

```json
{
  "mandate_id": "mnd_88293011",
  "user_id": "usr_991823",
  "agent_id": "agnt_suitability_v1",
  "constraints": {
    "max_spend_cents": 15000,
    "currency": "GBP",
    "merchant_category_codes": ["7999", "7394"],
    "allowed_merchants": ["London Bouncy Castles Ltd"],
    "expires_at": "2026-08-01T23:59:59Z"
  },
  "trust_tier": "low_stakes_auto_approve",
  "signature": "sig_ed25519_9983a0021b..."
}

Execution Payload with Audit Trail (POST /v1/checkout/execute)
Upon selecting an item that satisfies all suitability constraints, the agent submits the tokenized mandate along with a structured reasoning trace to serve as an immutable audit log:

{
  "transaction_id": "txn_77123982",
  "mandate_token": "tok_mnd_88293011_sub_01",
  "merchant_id": "mer_london_castles",
  "amount_cents": 11000,
  "currency": "GBP",
  "agent_execution_meta": {
    "evaluated_options_count": 14,
    "matching_criteria": [
      "Vendor rating: 4.8/5",
      "Exact match on yard dimensions (15x15ft)",
      "Delivery slot confirmed for 2026-08-15"
    ],
    "price_delta_from_max_cents": -4000,
    "confidence_score": 0.96
  }
}