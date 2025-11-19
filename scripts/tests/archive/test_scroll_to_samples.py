from playwright.sync_api import sync_playwright
import time

def test():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page(viewport={'width': 1400, 'height': 1000})
        
        page.goto("http://localhost:5173/test/gateway")
        page.wait_for_load_state("networkidle")
        time.sleep(2)
        
        # Scroll to find sample section
        page.evaluate("window.scrollTo(0, 1400)")
        time.sleep(1)
        
        # Take screenshot
        page.screenshot(path="/home/uproot/ax/poc/sample_section_view.png")
        print("✅ Sample section screenshot saved!")
        
        time.sleep(2)
        browser.close()

if __name__ == "__main__":
    test()
