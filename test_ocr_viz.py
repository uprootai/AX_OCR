#!/usr/bin/env python3
from playwright.sync_api import sync_playwright

def test_ocr():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page(viewport={'width': 1920, 'height': 1080})
        
        page.goto("http://localhost:5173/analyze", wait_until="networkidle")
        
        # Select image sample
        page.locator("select").first.select_option(value="/samples/sample2_interm_shaft.jpg")
        page.wait_for_timeout(1000)
        
        # Enable only OCR
        ocr_cb = page.locator('input[type="checkbox"]').first
        if not ocr_cb.is_checked():
            ocr_cb.check()
        
        # Click analyze
        page.locator('button:has-text("분석 시작")').click()
        page.wait_for_selector('text=/분석 완료/', timeout=60000)
        page.wait_for_timeout(2000)
        
        # Click OCR tab
        page.locator('button:has-text("OCR")').click()
        page.wait_for_timeout(1000)
        page.screenshot(path="/home/uproot/ax/poc/screenshot_ocr_check.png")
        
        # Check for canvas
        canvases = page.locator('canvas').all()
        print(f"Found {len(canvases)} canvas elements")
        
        # Scroll down
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1000)
        page.screenshot(path="/home/uproot/ax/poc/screenshot_ocr_scrolled.png")
        
        page.wait_for_timeout(3000)
        browser.close()
        
        return len(canvases) > 0

if __name__ == "__main__":
    success = test_ocr()
    print("✅ Canvas found!" if success else "❌ No canvas found")
