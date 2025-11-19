from playwright.sync_api import sync_playwright
import time

def test():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=['--start-maximized'])
        page = browser.new_page(viewport={'width': 1920, 'height': 1080})
        
        page.goto("http://localhost:5173/test/gateway")
        page.wait_for_load_state("networkidle")
        time.sleep(2)
        
        # Scroll to upload section
        heading = page.locator('h3:has-text("1. 파일 업로드")')
        heading.scroll_into_view_if_needed()
        time.sleep(1)
        
        # Wait for sample buttons to be visible
        sample_buttons = page.locator('button:has-text("합성 테스트 도면")')
        sample_buttons.first.wait_for(state='visible', timeout=5000)
        
        # Take full section screenshot
        upload_card = page.locator('h3:has-text("1. 파일 업로드")').locator('..')
        upload_card.screenshot(path="/home/uproot/ax/poc/upload_card_full.png")
        print("✅ Upload card screenshot saved!")
        
        time.sleep(2)
        browser.close()

if __name__ == "__main__":
    test()
