from playwright.sync_api import sync_playwright
import time

def test():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page(viewport={'width': 1400, 'height': 1200})
        
        page.goto("http://localhost:5173/test/gateway")
        page.wait_for_load_state("networkidle")
        time.sleep(2)
        
        # Scroll down a bit to see sample buttons
        page.evaluate("window.scrollTo(0, 600)")
        time.sleep(1)
        
        # Take screenshot
        page.screenshot(path="/home/uproot/ax/poc/complete_view.png")
        print("✅ Complete view screenshot saved!")
        
        # Highlight sample buttons
        buttons = page.locator('button:has-text("합성 테스트 도면")')
        for i in range(buttons.count()):
            buttons.nth(i).evaluate("el => el.style.outline = '3px solid #ef4444'")
        
        time.sleep(1)
        page.screenshot(path="/home/uproot/ax/poc/complete_view_highlighted.png")
        print("✅ Highlighted screenshot saved!")
        
        time.sleep(2)
        browser.close()

if __name__ == "__main__":
    test()
