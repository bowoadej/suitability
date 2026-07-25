"""
size_charts.py

Brand-level, general body-measurement-to-size reference charts. This is
NOT a garment-specific size chart (like the numeric measurements already
hand-curated in products.json for other brands) - it's the general chart
a brand publishes mapping label sizes (S/M/L/XL) to expected body
measurements, which is what's actually available for brands whose live
product feed only returns label sizes (e.g. via fetch_feed.py).

Sourced from each brand's own published body-measurement guide. Sourced
directly, not inferred or estimated by this script - see SOURCE_URL per
brand. If a brand isn't listed here, sizing normalization simply isn't
available for it yet and callers should fall back to label-only handling.

IMPORTANT: this is still one level less precise than a garment's own size
chart (fit varies style to style even within a brand - see Represent's
own guidance that jeans use a different chart to general clothing, and a
given style's actual cut can vary from the general guide). Callers should
mark anything sourced from here as "estimated-measurement" evidence, not
"measurement" - a real garment size chart with product-specific numbers
is a stronger source than a brand's general guide.
"""

# Waist is stored as a single expected value (as Represent publishes it,
# not a range); chest is stored as [low, high] since Represent publishes
# a range per size.
REPRESENT = {
    "source_url": "https://representclo.com/pages/body-measurements",
    "clothing": {
        "XS":  {"chest_in": [33, 34], "waist_in": 28},
        "S":   {"chest_in": [35, 36], "waist_in": 30},
        "M":   {"chest_in": [37, 38], "waist_in": 32},
        "L":   {"chest_in": [39, 40], "waist_in": 34},
        "XL":  {"chest_in": [41, 42], "waist_in": 36},
        "XXL": {"chest_in": [43, 44], "waist_in": 38},
    },
    # Represent publishes a separate (currently identical, but not
    # guaranteed to stay that way) chart for denim specifically.
    "denim": {
        "XS":  {"chest_in": [33, 34], "waist_in": 28},
        "S":   {"chest_in": [35, 36], "waist_in": 30},
        "M":   {"chest_in": [37, 38], "waist_in": 32},
        "L":   {"chest_in": [39, 40], "waist_in": 34},
        "XL":  {"chest_in": [41, 42], "waist_in": 36},
        "XXL": {"chest_in": [43, 44], "waist_in": 38},
    },
}

BRAND_SIZE_CHARTS = {
    "Represent": REPRESENT,
}

# Category strings (as returned by a brand's product feed, lowercased)
# that should use the "denim" chart instead of "clothing", per brand.
DENIM_CATEGORY_HINTS = {
    "Represent": ("denim", "jean"),
}


def get_chart_for_product(brand, category):
    """
    Return (chart_dict, chart_name) for a given brand + product category,
    or (None, None) if this brand isn't in BRAND_SIZE_CHARTS yet.
    """
    brand_charts = BRAND_SIZE_CHARTS.get(brand)
    if not brand_charts:
        return None, None

    category_lower = (category or "").lower()
    denim_hints = DENIM_CATEGORY_HINTS.get(brand, ())
    if any(hint in category_lower for hint in denim_hints) and "denim" in brand_charts:
        return brand_charts["denim"], "denim"

    return brand_charts.get("clothing"), "clothing"


def estimate_measurements_for_sizes(brand, category, size_labels):
    """
    Given a brand, a product category, and a list of size labels actually
    in stock/available for a product, return a dict of
    {size_label: {"chest_in": [...], "waist_in": ...}} for whichever
    labels have a matching entry in the brand's chart. Labels with no
    match (unusual/custom sizing) are simply omitted, not guessed at.
    """
    chart, chart_name = get_chart_for_product(brand, category)
    if not chart:
        return {}, None

    estimates = {}
    for label in size_labels:
        entry = chart.get(label.upper().strip())
        if entry:
            estimates[label] = entry

    return estimates, chart_name
