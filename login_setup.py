from playwright.sync_api import sync_playwright
# imports sync_api
with sync_playwright() as p:
    

    browser = p.chromium.launch(headless=False)
   
    context = browser.new_context()
    
    page = context.new_page()

    page.goto("https://www.zepto.com")
    
    input("Log in manually in the browser window (enter phone, OTP, etc). Once you're logged in and can see the homepage, press Enter here...")
   

    context.storage_state(path="auth_state.json")

    print("Saved login session to auth_state.json")

    browser.close()