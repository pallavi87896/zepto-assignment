"""
scrape_offers.py
-----------------
Scrapes bank/card offers from Zepto's "Coupon & Offers" panel and prints
a clean JSON list, saved to offers.json.

Only offers under Zepto's own "Card" filter are included, which
corresponds to bank credit/debit card offers (excludes UPI, Wallet,
PayLater, generic coupons, delivery discounts, etc).

Prerequisite:
    Run login_setup.py once first to create auth_state.json.

Usage:
    python scrape_offers.py
"""

import json
from playwright.sync_api import sync_playwright

# A search query + &cart=open reliably opens the cart/offers panel
# without needing to fully complete a checkout flow.
SEARCH_URL = "https://www.zepto.com/search?query=Biscuit&cart=open"
AUTH_STATE_FILE = "auth_state.json"
OUTPUT_FILE = "offers.json"


import re


def extract_bank_name(headline):
    """
    Extracts the bank/card name directly from the offer's own headline
    text, instead of matching against a hardcoded list of bank names
    (which would silently miss any bank not in the list).

    Every observed headline follows the pattern:
        "... with <NAME> Credit/Debit Card(s)"
        "... off <NAME> Credit/Debit Card(s)"   (when "with" is absent)
    e.g. "Flat ₹100 off with IndusInd Bank Credit Cards" -> "IndusInd Bank"
         "Flat ₹1,500 Off ICICI Bank Credit Card."       -> "ICICI Bank"
         "Get ₹50 off with Novio Credit Card"            -> "Novio"

    "with" is tried first since it's the more common/specific marker;
    "off" is a fallback for the handful of headlines that omit "with".
    """
    if not headline:
        return None

    match = re.search(r"\bwith\s+(.+?)\s+(?:Credit|Debit)\s+Cards?\b", headline, re.I)
    if not match:
        match = re.search(r"\boff\s+(.+?)\s+(?:Credit|Debit)\s+Cards?\b", headline, re.I)

    if match:
        return match.group(1).strip(" .,")
    return None


def parse_card(card):
    """
    Given one offer-card element from the "Card" tab, extract the fields
    we care about.

    NOTE: cards do NOT all share the same fixed span order. "Locked"
    cards (ones needing a higher cart value to unlock) include an extra
    status span ("Locked") that unlocked cards don't have, which shifts
    positions. So instead of trusting span order, we:
      - get the bank/card name by parsing the headline text itself
        (see extract_bank_name) - not a hardcoded bank list
      - find the promo code by pattern-matching (short, no spaces,
        mostly uppercase/digits - Zepto's codes look like "ZEPINDCC")
      - find the min-order/condition line by looking for the span that
        mentions "Shop for" / "Valid on" / "orders above"
    """
    spans = card.query_selector_all("span")
    span_texts = [s.inner_text().strip() for s in spans if s.inner_text().strip()]
    # asks for the visible rendered text inside which includes hiddent texts as well in fact all the text that the human sees and the filter removes the spans tht have empty string like where we hv icons or pngs.

    headline = span_texts[0] if span_texts else None
    # e trust position [0] specifically because, across all 35 real offers we tested, the first visible span was always the headline — that's an empirical finding from actually looking at the scraped output, not an assumption made in advance.
    bank_name = extract_bank_name(headline)

    condition = None
    promo_code = None
    lock_status = None

    for text in span_texts[1:]:
        if text in ("Locked", "Apply"):
            lock_status = text
        elif re.fullmatch(r"[A-Z0-9]{4,20}", text):
            promo_code = text
        elif any(
            phrase in text
            for phrase in ("Shop for", "Valid on", "orders above", "unlock")
        ):
            condition = text

    return {
        "bank_or_card": bank_name,
        "headline": headline,
        "condition": condition,
        "promo_code": promo_code,
        "status": lock_status,
    }


def main():
    with sync_playwright() as p:
        # run some setup code and give me a handle (p) to work with and guarantee cleanup runs after it finishes even if theres an error

        browser = p.chromium.launch(headless=True)
        # starts a browser invisibly n works

        context = browser.new_context(storage_state=AUTH_STATE_FILE)
        # creates a fresh isolated browsing profile
        page = context.new_page()
        # Opens one tab within that context.
        page.goto(SEARCH_URL)
        page.wait_for_timeout(3000)

        # The cart drawer shows a short "Coupons & offers" summary with a
        # "View all payment offers >" link - click that to open the full
        # panel with the Coupons / Payment Offers tabs.
        try:
            page.get_by_text("View all payment offers", exact=False).click(timeout=10000)
        except Exception as e:
            page.screenshot(path="debug_2_failed_view_all_link.png", full_page=True)
            print("Could not find 'View all payment offers' link.")
            print("Saved debug_2_failed_view_all_link.png - open it to see current state")
            raise e

        page.wait_for_timeout(1500)
        page.screenshot(path="debug_3_after_view_all_click.png", full_page=True)

        # This should open the full "Coupon & Offers" panel with
        # Coupons / Payment Offers tabs. Make sure "Payment Offers" is
        # selected (it may already default to it since we came from that link).
        try:
            page.get_by_text("Payment Offers", exact=True).click(timeout=10000)
        except Exception:
            print("'Payment Offers' tab not clickable/found - it may already be selected, continuing...")

        page.wait_for_timeout(1000)

        # Filter down to just "Card" offers (bank credit/debit cards only)
        try:
            page.get_by_text("Card", exact=True).click(timeout=10000)
        except Exception as e:
            page.screenshot(path="debug_4_failed_card_filter.png", full_page=True)
            print("Could not find 'Card' filter chip.")
            print("Saved debug_4_failed_card_filter.png - open it to see current state")
            raise e

        page.wait_for_timeout(1000)

        cards = page.query_selector_all("div.rounded-xl.border.p-3")
        print(f"Found {len(cards)} card offers")
        # lets you embed Python expressions directly inside a string using {}. len(cards) counts how many elements were found.

        offers = [parse_card(card) for card in cards]
        # 

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(offers, f, indent=2, ensure_ascii=False)
            # f is our handle to the open file. json.dump(offers, f, ...) serializes our Python list-of-dicts into JSON text and writes it directly into that file. indent=2 makes the output nicely formatted with 2-space indentation (instead of one dense unreadable line). ensure_ascii=False — without this flag, json.dump would convert non-ASCII characters like ₹ into escape sequences like \u20b9; setting it False keeps them as actual readable characters in the file.

        print(json.dumps(offers, indent=2, ensure_ascii=False))
        print(f"\nSaved {len(offers)} offers to {OUTPUT_FILE}")
        # Same idea, but json.dumps (with an s — "dump string") returns the JSON as a Python string instead of writing to a file, which we then hand to print() so it shows up in your terminal too.

        browser.close()


if __name__ == "__main__":
    main()

    # This is a very standard Python idiom. __name__ is a special built-in variable every Python file automatically has. When you run a file directly (python scrape_offers.py), Python sets __name__ to the string "__main__" for that file. But if this file were instead imported by some other script (import scrape_offers), __name__ would be set to "scrape_offers" instead — not "__main__". This check means: "only actually run main() if this file was executed directly, not if someone else imported it as a module to reuse its functions.