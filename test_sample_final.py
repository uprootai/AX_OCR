from playwright.sync_api import sync_playwright
import time

def test_sample_selector():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        print("="*70)
        print(" 📋 SAMPLE IMAGE SELECTOR - FINAL TEST")
        print("="*70)
        
        # Navigate
        print("\n1️⃣  NAVIGATION")
        page.goto("http://localhost:5173/test/gateway")
        page.wait_for_load_state("networkidle")
        time.sleep(2)
        print("   └─ ✅ Page loaded\n")
        
        # Scroll to upload section
        print("2️⃣  SCROLLING TO UPLOAD SECTION")
        heading = page.locator('h3:has-text("1. 파일 업로드")')
        if heading.count() > 0:
            heading.scroll_into_view_if_needed()
            time.sleep(1)
            print("   └─ ✅ Scrolled successfully\n")
        
        # Take initial screenshot
        page.screenshot(path="/home/uproot/ax/poc/final_upload_section.png")
        print("3️⃣  SCREENSHOTS")
        print("   ├─ 📸 Initial state saved\n")
        
        # Check sample section
        print("4️⃣  SAMPLE BUTTONS CHECK")
        sample_text = page.locator('text="또는 샘플 이미지로 빠르게 테스트"')
        sample_count = sample_text.count()
        print(f"   ├─ Sample label: {'✅ Found' if sample_count > 0 else '❌ Not found'}")
        
        # Count sample buttons
        buttons = page.locator('button:has-text("합성 테스트 도면")')
        button_count = buttons.count()
        print(f"   ├─ Sample buttons: {button_count} found")
        
        if button_count > 0:
            # List all buttons
            for i in range(button_count):
                btn = buttons.nth(i)
                text = btn.inner_text()
                print(f"   │  {i+1}. {text[:30]}...")
            
            # Click first button
            print(f"   └─ Clicking first sample button...\n")
            buttons.first.click()
            time.sleep(3)
            
            # Check if file loaded
            print("5️⃣  FILE LOADING CHECK")
            preview = page.locator('text="synthetic_random_synthetic_test_000003.jpg"')
            if preview.count() > 0:
                print("   ├─ ✅ File preview appeared!")
                
                # Check file size
                size = page.locator('text=/140.*KB/')
                if size.count() > 0:
                    print("   ├─ ✅ File size displayed!")
                
                # Take final screenshot
                page.screenshot(path="/home/uproot/ax/poc/final_with_sample.png")
                print("   └─ 📸 Final screenshot saved\n")
            else:
                print("   └─ ❌ File preview NOT found\n")
        
        print("="*70)
        print(" ✅ TEST COMPLETED!")
        print("="*70)
        print("\n📁 Screenshots saved:")
        print("   • /home/uproot/ax/poc/final_upload_section.png")
        print("   • /home/uproot/ax/poc/final_with_sample.png")
        print("="*70)
        
        time.sleep(3)
        browser.close()

if __name__ == "__main__":
    test_sample_selector()
