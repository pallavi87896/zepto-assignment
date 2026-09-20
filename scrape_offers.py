import json
import re
from playwright.sync_api import sync_playwright

SEARCH_URL = "https://www.zepto.com/search?query=Biscuit&cart=open"
AUTH_STATE_FILE = "auth_state.json"
OUTPUT_FILE = "offers.json"


def extract_bank_name(text):

    if not text:
        return None

    match = re.search(r"\bwith\s+(.+?)\s+(?:Credit|Debit)\s+Cards?\b", text, re.I)
    if not match:
        match = re.search(r"\boff\s+(.+?)\s+(?:Credit|Debit)\s+Cards?\b", text, re.I)

    return match.group(1).strip(" .,") if match else None


def parse_card(card):
    
    spans = card.query_selector_all("span")
    span_texts = [s.inner_text().strip() for s in spans if s.inner_text().strip()]

    headline = span_texts[0] if span_texts else None

    description = None
    bank_name = extract_bank_name(headline)
    if bank_name:
        description = headline

    condition = None
    promo_code = None
    lock_status = None

    for text in span_texts[1:]:
        if text in ("Locked", "Apply"):
            lock_status = text
            continue

        if re.fullmatch(r"[A-Z0-9]{4,20}", text):
            promo_code = text
            continue

        if bank_name is None:
            candidate = extract_bank_name(text)
            if candidate:
                bank_name = candidate
                description = text
                continue

        if any(
            phrase in text
            for phrase in ("Shop for", "Valid on", "orders above", "unlock")
        ):
            condition = text

    return {
        "bank_or_card": bank_name,
        "headline": headline,
        "description": description,
        "condition": condition,
        "promo_code": promo_code,
        "status": lock_status,
    }


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state=AUTH_STATE_FILE)
        page = context.new_page()

        page.goto(SEARCH_URL)
        page.wait_for_timeout(3000)

        
        page.get_by_text("payment offers", exact=False).click(timeout=10000)
        page.wait_for_timeout(1500)

        
        try:
            page.get_by_text("Payment Offers", exact=True).click(timeout=10000)
        except Exception:
            pass
        page.wait_for_timeout(1000)

        
        page.get_by_text("Card", exact=True).click(timeout=10000)
        page.wait_for_timeout(1000)

        cards = page.query_selector_all("div.rounded-xl.border.p-3")
        offers = [parse_card(card) for card in cards]

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(offers, f, indent=2, ensure_ascii=False)

        print(json.dumps(offers, indent=2, ensure_ascii=False))
        print(f"\nSaved {len(offers)} offers to {OUTPUT_FILE}")

        browser.close()


if __name__ == "__main__":
    main()