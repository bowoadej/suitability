"""
fetch_feed.py - v0

Pulls live product data from a real Shopify store (Represent Clo) via the
official Storefront API, and converts it into the same shape products.json
already uses, so match.py doesn't need to change at all.

Usage:
    export SHOPIFY_STOREFRONT_TOKEN=your_token_here
    export SHOPIFY_SHOP_DOMAIN=uk.representclo.com
    python fetch_feed.py

Note on data quality: standard Shopify product/variant data typically only
includes size labels (S/M/L/XL) and price/availability - not numeric body
measurements (chest, sleeve length, etc.) the way the hand-curated entries
in products.json have. This script is honest about that gap rather than
inventing measurements that aren't actually returned by the API.
"""

import json
import os
import sys
import requests

SHOP_DOMAIN = os.environ.get("SHOPIFY_SHOP_DOMAIN", "uk.representclo.com")
API_VERSION = "unstable"
OUTPUT_FILE = "live_products.json"

GRAPHQL_QUERY = """
{
  products(first: 10, query: "product_type:*") {
    edges {
      node {
        id
        title
        description
        handle
        onlineStoreUrl
        productType
        vendor
        variants(first: 20) {
          edges {
            node {
              id
              title
              availableForSale
              price {
                amount
                currencyCode
              }
              selectedOptions {
                name
                value
              }
            }
          }
        }
      }
    }
  }
}
"""


def fetch_live_products(token):
    url = f"https://{SHOP_DOMAIN}/api/{API_VERSION}/graphql.json"
    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Storefront-Access-Token": token,
    }

    response = requests.post(url, headers=headers, json={"query": GRAPHQL_QUERY})

    if response.status_code != 200:
        sys.exit(f"Error: Shopify API returned {response.status_code}\n{response.text}")

    data = response.json()

    if "errors" in data:
        sys.exit(f"Error: GraphQL query failed\n{json.dumps(data['errors'], indent=2)}")

    return data["data"]["products"]["edges"]


def convert_to_products_schema(shopify_products):
    """
    Convert Shopify's product/variant shape into the same structure used in
    products.json, so match.py can consume either file without modification.
    """
    converted = []

    for edge in shopify_products:
        node = edge["node"]

        # Pull size options across all variants
        sizes_seen = {}
        for variant_edge in node["variants"]["edges"]:
            variant = variant_edge["node"]
            size_option = next(
                (opt["value"] for opt in variant["selectedOptions"] if opt["name"].lower() == "size"),
                None,
            )
            if size_option:
                sizes_seen[size_option] = {
                    "available": variant["availableForSale"],
                    "price": variant["price"]["amount"],
                    "currency": variant["price"]["currencyCode"],
                }

        product_id = node["id"].split("/")[-1]  # Shopify IDs are full GIDs, take the numeric tail

        # Skip anything with no size variants at all - not a wearable/fit-relevant
        # product (gift cards, etc), rather than maintaining a brittle name-based exclusion list
        if not sizes_seen:
            continue

        description = node.get("description") or ""
        if len(description) > 300:
            # truncate at the last space before 300 chars, not mid-word
            description = description[:300].rsplit(" ", 1)[0] + "..."

        converted.append({
            "id": f"represent-{product_id}",
            "brand": "Represent",
            "collection": node.get("vendor"),  # Shopify's "vendor" field is actually the internal collection/season name here, not the brand
            "region": "UK",
            "retailer": "Represent (direct)",
            "url": node.get("onlineStoreUrl") or f"https://{SHOP_DOMAIN}/products/{node['handle']}",
            "title": node["title"],
            "description": description,
            "category": node.get("productType") or "unknown",
            "fit_descriptor": "Not provided as a separate structured field by the live API - check the description text for fit language (e.g. 'oversized fit', 'slim', embedded measurements like the waist range sometimes given for a specific size). Do not assume a fit style beyond what the description actually states.",
            "size_unit": "label only (S/M/L/XL etc.) - no numeric measurements available from this data source, except where a measurement happens to be mentioned in the free-text description",
            "size_chart": {
                "sizes_by_availability": sizes_seen,
                "note": "This data came from a live Shopify Storefront API call, not a hand-curated size chart. Only size labels, price, and stock are available - no structured body or garment measurements. Reason conservatively given this limited data, and flag low confidence where measurement-based reasoning would normally apply - unless the description text happens to state a real measurement.",
            },
            "source_type": "live_api",
        })

    return converted


def main():
    token = os.environ.get("SHOPIFY_STOREFRONT_TOKEN")
    if not token:
        sys.exit(
            "Error: SHOPIFY_STOREFRONT_TOKEN environment variable not set.\n"
            "Run: export SHOPIFY_STOREFRONT_TOKEN=your_token_here"
        )

    print(f"Fetching live products from {SHOP_DOMAIN}...")
    raw_products = fetch_live_products(token)
    print(f"Retrieved {len(raw_products)} products.")

    converted = convert_to_products_schema(raw_products)

    with open(OUTPUT_FILE, "w") as f:
        json.dump(converted, f, indent=2)

    print(f"Saved {len(converted)} products to {OUTPUT_FILE}")
    print("Run match.py against this file to test live-data reasoning "
          "(you'll need to point PRODUCTS_FILE at it, or merge it into products.json).")


if __name__ == "__main__":
    main()