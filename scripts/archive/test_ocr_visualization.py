#!/usr/bin/env python3

from playwright.sync_api import sync_playwright
import time

def test_ocr_visualization():
    print("🚀 Starting OCR Visualization test...\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()

        try:
            # Step 1: Navigate to Analyze page
            print("📍 Step 1: Navigate to Analyze page...")
            page.goto("http://localhost:5173/analyze", wait_until="networkidle")
            time.sleep(1)
            page.screenshot(path="screenshot-01-analyze-page.png")
            print("   ✓ Screenshot saved: screenshot-01-analyze-page.png\n")

            # Step 2: Select sample file
            print("📍 Step 2: Select sample image file...")
            sample_select = page.locator("select").first
            # Try to find the option with "Image"
            options = page.locator("select option").all_text_contents()
            print(f"   Available options: {options}")

            # Select the image sample
            sample_select.select_option(index=1)  # Second option should be the image
            time.sleep(2)
            page.screenshot(path="screenshot-02-file-selected.png")
            print("   ✓ Sample file selected\n")

            # Step 3: Check OCR option
            print("📍 Step 3: Enable OCR option...")
            ocr_checkbox = page.locator('input[type="checkbox"]').first
            if not ocr_checkbox.is_checked():
                ocr_checkbox.check()
            page.screenshot(path="screenshot-03-ocr-enabled.png")
            print("   ✓ OCR option enabled\n")

            # Step 4: Click analyze button
            print("📍 Step 4: Click analyze button...")
            analyze_button = page.locator('button:has-text("분석 시작")')
            analyze_button.click()
            print("   ✓ Analysis started, waiting for completion...\n")

            # Wait for analysis to complete
            print("⏳ Waiting for analysis to complete...")
            page.wait_for_selector('text=분석 완료', timeout=60000)
            time.sleep(2)
            page.screenshot(path="screenshot-04-analysis-complete.png")
            print("   ✓ Analysis completed!\n")

            # Step 5: Click OCR tab
            print("📍 Step 5: Click OCR tab...")
            ocr_tab = page.locator('button:has-text("OCR")')
            ocr_tab.click()
            time.sleep(1)
            page.screenshot(path="screenshot-05-ocr-tab.png")
            print("   ✓ OCR tab opened\n")

            # Step 6: Check for OCRVisualization component
            print("📍 Step 6: Check for OCR Visualization component...")

            # Look for visualization title
            visualization_title_count = page.locator('text=OCR 인식 위치 시각화').count()
            print(f"   - Visualization title found: {'✓ YES' if visualization_title_count > 0 else '✗ NO'}")

            # Look for canvas element
            canvas_count = page.locator('canvas').count()
            print(f"   - Canvas elements found: {canvas_count}")

            # Look for legend items
            legend_dimensions = page.locator('text=치수').count()
            legend_gdt = page.locator('text=GD&T').count()
            print(f"   - Legend '치수' found: {'✓ YES' if legend_dimensions > 0 else '✗ NO'}")
            print(f"   - Legend 'GD&T' found: {'✓ YES' if legend_gdt > 0 else '✗ NO'}")

            # Take full page screenshot
            page.screenshot(path="screenshot-06-final.png", full_page=True)
            print("   ✓ Full page screenshot saved: screenshot-06-final.png\n")

            # Scroll down to see if visualization is below
            print("📍 Step 7: Scroll down to find visualization...")
            page.evaluate("window.scrollBy(0, 500)")
            time.sleep(0.5)
            page.screenshot(path="screenshot-07-scrolled.png", full_page=True)
            print("   ✓ Scrolled screenshot saved\n")

            # Final check
            visualization_exists = visualization_title_count > 0 and canvas_count > 0

            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print("📊 TEST RESULTS:")
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print(f"OCR Visualization Component: {'✅ FOUND' if visualization_exists else '❌ NOT FOUND'}")
            print(f"- Visualization Title: {'✓' if visualization_title_count > 0 else '✗'}")
            print(f"- Canvas Element: {'✓' if canvas_count > 0 else '✗'}")
            print(f"- Legend Items: {'✓' if legend_dimensions > 0 and legend_gdt > 0 else '✗'}")
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

            if not visualization_exists:
                print("⚠️  WARNING: OCR Visualization component not found!")
                print("Please check the screenshots to debug the issue.\n")
            else:
                print("🎉 SUCCESS: OCR Visualization component is working!\n")

            # Save page HTML for debugging
            html_content = page.content()
            with open("page-content.html", "w") as f:
                f.write(html_content)
            print("💾 Page HTML saved to: page-content.html\n")

        except Exception as error:
            print(f"❌ Test failed with error: {error}")
            page.screenshot(path="screenshot-error.png")
            print("   Error screenshot saved: screenshot-error.png\n")
        finally:
            browser.close()
            print("✅ Test completed!\n")

if __name__ == "__main__":
    test_ocr_visualization()
