# Zepto Checkout Bank/Card Offers Scraper

Logs into Zepto once, then scrapes the bank/credit-card offers from the
checkout "Coupon & Offers" panel and saves them as clean JSON.

## What we used, and why

- **Python** — the language the scripts are written in.
- **[Playwright](https://playwright.dev/python/)** — controls a real
  Chrome browser from Python. Used instead of a plain HTTP request
  because Zepto's checkout data is protected by bot detection (AWS WAF)
  and requires being logged in — a real browser gets past both.
- **`re`** (built into Python) — pulls the bank name and promo code out
  of each offer's text.
- **`json`** (built into Python) — saves the results as a `.json` file.

## The two files

- **`login_setup.py`** — run once. Opens a browser so you can log into
  Zepto manually (phone + OTP), then saves that session to
  `auth_state.json`.
- **`scrape_offers.py`** — the scraper. Reuses the saved login, opens
  the offers panel, filters to bank/card offers only, and saves them to
  `offers.json`.

## Setup

```bash
pip install playwright
playwright install chromium
```

## Usage

**1. Log in once:**
```bash
python login_setup.py
```
A browser window opens — log in manually (phone + OTP), then press
Enter in the terminal. This creates `auth_state.json`.

**2. Run the scraper:**
```bash
python scrape_offers.py
```
Prints the offers and saves them to `offers.json`.

## Output format

```json
{
  "bank_or_card": "IndusInd Bank",
  "headline": "Flat ₹100 off with IndusInd Bank Credit Cards",
  "condition": "Shop for ₹737 more to unlock",
  "promo_code": "ZEPINDCC",
  "status": "Locked"
}
```

## Notes

- Don't share `auth_state.json` — it's your login session.
- If your session expires, just re-run `python login_setup.py`.

