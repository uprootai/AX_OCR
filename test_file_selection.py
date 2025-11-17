from playwright.sync_api import sync_playwright
import time

def test_file_selection():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        print("📍 Step 1: Navigating to Gateway test page...")
        page.goto("http://localhost:5173/test/gateway")
        page.wait_for_load_state("networkidle")
        time.sleep(1)
        
        # Scroll to file upload section
        print("📍 Step 2: Scrolling to file upload section...")
        heading = page.locator('h3:has-text("1. 파일 업로드")')
        if heading.count() > 0:
            heading.scroll_into_view_if_needed()
            time.sleep(1)
        
        # Find file input
        print("\n🔍 Step 3: Finding file input...")
        file_input = page.locator('input[type="file"]')
        
        if file_input.count() > 0:
            print("   ✅ File input found!")
            
            # Test file selection
            test_file = "/home/uproot/ax/poc/datasets/combined/images/test/synthetic_random_synthetic_test_000003.jpg"
            
            print(f"\n📁 Step 4: Selecting test file...")
            print(f"   File: {test_file}")
            
            # Set file
            file_input.set_input_files(test_file)
            time.sleep(2)
            
            # Check if file preview appears
            print("\n🔍 Step 5: Checking for file preview...")
            file_preview = page.locator('text="synthetic_random_synthetic_test_000003.jpg"')
            
            if file_preview.count() > 0:
                print("   ✅ File preview appeared!")
            else:
                print("   ❌ File preview NOT found!")
            
            # Check for file size display
            file_size = page.locator('text=/140.*KB/')
            if file_size.count() > 0:
                print("   ✅ File size displayed!")
            else:
                print("   ⚠️  File size not found")
            
            # Take screenshot
            print("\n📸 Step 6: Taking screenshot...")
            page.screenshot(path="screenshot_file_selected.png")
            print("   Screenshot saved: screenshot_file_selected.png")
            
            # Check for remove button
            remove_button = page.locator('button:has-text("파일 제거")')
            if remove_button.count() > 0:
                print("   ✅ Remove button found!")
            else:
                print("   ⚠️  Remove button not found")
            
        else:
            print("   ❌ File input NOT found!")
        
        print("\n" + "="*60)
        print("✅ File selection test completed!")
        print("="*60)
        
        time.sleep(3)
        browser.close()

if __name__ == "__main__":
    test_file_selection()
