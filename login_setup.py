from playwright.sync_api import sync_playwright
# imports sync_api
with sync_playwright() as p:
    # starts playwright engine when the block ends the background processes terminate as well

    browser = p.chromium.launch(headless=False)
    # launches the chromium browser
      # headless=False = you SEE the browser
    context = browser.new_context()
    # creates a fresh profile so nothing previous cookies or sessions interfere
    page = context.new_page()

    page.goto("https://www.zepto.com")
    # Opens a new tab and navigates to Zepto's homepage.

    input("Log in manually in the browser window (enter phone, OTP, etc). Once you're logged in and can see the homepage, press Enter here...")
    # pauses the python script and expects to press enter in the terminal. meanwhile the browser remains open u log in u do anything

    context.storage_state(path="auth_state.json")

    # stores the auth cookies n sessions it basically store the entire localStorage into a json file 
    print("Saved login session to auth_state.json")

    browser.close()