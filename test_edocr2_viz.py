#!/usr/bin/env python3
from playwright.sync_api import sync_playwright
import time

def test_edocr2_visualization():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page(viewport={'width': 1920, 'height': 1080})

        # Go to TestEdocr2 page
        page.goto("http://localhost:5173/test/edocr2", wait_until="networkidle")
        page.wait_for_timeout(1000)

        # Take screenshot before upload
        page.screenshot(path="/home/uproot/ax/poc/screenshot_edocr2_before.png")

        # Select image file
        file_input = page.locator('input[type="file"]')
        file_input.set_input_files('/home/uproot/ax/poc/web-ui/public/samples/sample2_interm_shaft.jpg')
        page.wait_for_timeout(1000)

        # Click OCR 실행 button
        page.locator('button:has-text("OCR 실행")').click()

        # Wait for results
        try:
            page.wait_for_selector('text=/OCR 결과/', timeout=60000)
            page.wait_for_timeout(3000)
            print("✅ OCR 완료")
        except Exception as e:
            print(f"❌ OCR 실패: {e}")
            browser.close()
            return False

        # Scroll to find visualization
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1000)

        # Take screenshot after OCR
        page.screenshot(path="/home/uproot/ax/poc/screenshot_edocr2_after.png", full_page=True)

        # Check for OCR Visualization
        viz_heading = page.locator('h3:has-text("OCR 인식 위치 시각화")')
        if viz_heading.count() > 0:
            print("✅ OCR 시각화 제목 발견")
        else:
            print("❌ OCR 시각화 제목 없음")

        # Check for canvas
        canvases = page.locator('canvas').all()
        print(f"Found {len(canvases)} canvas elements")

        # Check for legend items
        legend_items = page.locator('text=/치수.*개/').all()
        print(f"Found {len(legend_items)} legend items")

        # Wait a bit more
        page.wait_for_timeout(3000)

        browser.close()

        return len(canvases) > 0

if __name__ == "__main__":
    success = test_edocr2_visualization()
    if success:
        print("\n✅ 시각화 컴포넌트 발견!")
    else:
        print("\n❌ 시각화 컴포넌트 없음")
