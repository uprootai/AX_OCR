#!/usr/bin/env python3

from playwright.sync_api import sync_playwright
import time

def test_detailed_analysis():
    print("🔍 Starting detailed OCR Visualization analysis...\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()

        try:
            # Navigate and setup
            print("📍 Navigating and setting up...")
            page.goto("http://localhost:5173/analyze", wait_until="networkidle")
            time.sleep(1)

            # Select sample file
            sample_select = page.locator("select").first
            sample_select.select_option(index=1)
            time.sleep(2)

            # Enable OCR
            ocr_checkbox = page.locator('input[type="checkbox"]').first
            if not ocr_checkbox.is_checked():
                ocr_checkbox.check()

            # Start analysis
            analyze_button = page.locator('button:has-text("분석 시작")')
            analyze_button.click()

            print("⏳ Waiting for analysis...")
            page.wait_for_selector('text=분석 완료', timeout=60000)
            time.sleep(2)

            # Click OCR tab
            ocr_tab = page.locator('button:has-text("OCR")')
            ocr_tab.click()
            time.sleep(1)

            # Take high-quality screenshots
            print("\n📸 Taking detailed screenshots...\n")

            # Full page screenshot
            page.screenshot(path="analysis-full-page.png", full_page=True)
            print("   ✓ Full page screenshot saved: analysis-full-page.png")

            # Find and zoom into visualization
            visualization_section = page.locator('text=OCR 인식 위치 시각화').locator('..')
            if visualization_section.count() > 0:
                visualization_section.screenshot(path="analysis-visualization-section.png")
                print("   ✓ Visualization section screenshot: analysis-visualization-section.png")

            # Canvas screenshot
            canvas = page.locator('canvas').first
            if canvas.count() > 0:
                canvas.screenshot(path="analysis-canvas-only.png")
                print("   ✓ Canvas screenshot: analysis-canvas-only.png")

            # Details list screenshot
            details = page.locator('text=인식된 항목 상세').locator('..')
            if details.count() > 0:
                details.screenshot(path="analysis-details-list.png")
                print("   ✓ Details list screenshot: analysis-details-list.png")

            # Get detailed information
            print("\n📊 Extracting detailed information...\n")

            # Get dimension count
            dimensions_text = page.locator('text=/치수.*개/').first
            if dimensions_text.count() > 0:
                print(f"   Dimensions: {dimensions_text.inner_text()}")

            # Get GDT count
            gdt_text = page.locator('text=/GD&T.*개/').first
            if gdt_text.count() > 0:
                print(f"   GD&T: {gdt_text.inner_text()}")

            # Get all detail items
            detail_items = page.locator('.flex.items-center.gap-2.p-2.rounded').all()
            print(f"\n   Total detail items found: {len(detail_items)}")

            print("\n   Detail items:")
            for i, item in enumerate(detail_items[:10], 1):  # Show first 10
                text = item.inner_text()
                print(f"   {i}. {text}")

            # Get OCR stats from top section
            print("\n📈 OCR Statistics:")
            dimensions_stat = page.locator('text=Dimensions').locator('..').locator('p.text-3xl').first
            if dimensions_stat.count() > 0:
                print(f"   Dimensions count: {dimensions_stat.inner_text()}")

            gdt_stat = page.locator('text=GD&T').locator('..').locator('p.text-3xl').first
            if gdt_stat.count() > 0:
                print(f"   GD&T count: {gdt_stat.inner_text()}")

            text_blocks_stat = page.locator('text=Text Blocks').locator('..').locator('p.text-3xl').first
            if text_blocks_stat.count() > 0:
                print(f"   Text Blocks count: {text_blocks_stat.inner_text()}")

            print("\n" + "="*60)
            print("✅ Detailed analysis complete!")
            print("="*60)

        except Exception as error:
            print(f"❌ Test failed with error: {error}")
            page.screenshot(path="analysis-error.png")
        finally:
            browser.close()

if __name__ == "__main__":
    test_detailed_analysis()
