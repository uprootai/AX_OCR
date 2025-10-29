#!/usr/bin/env python3
"""
Tooltip 테스트

툴팁이 제대로 표시되고 커서 스타일이 올바른지 확인합니다.
"""

from playwright.sync_api import sync_playwright
import time

def test_tooltip():
    print("🔍 Testing Tooltip functionality...\n")

    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=False)  # headless=False로 실제 브라우저 열기
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()

        # Navigate to analyze page
        print("📍 Navigating to http://localhost:5173/analyze")
        page.goto("http://localhost:5173/analyze", wait_until="networkidle")
        page.screenshot(path="/home/uproot/ax/poc/screenshot_tooltip_1_initial.png")

        # Select sample and run analysis
        print("📂 Selecting image sample")
        sample_select = page.locator("select").first
        sample_select.select_option(value="/samples/sample2_interm_shaft.jpg")
        page.wait_for_timeout(1000)

        # Enable OCR and segmentation
        print("⚙️  Enabling OCR and segmentation")
        ocr_checkbox = page.locator('input[type="checkbox"]').first
        seg_checkbox = page.locator('input[type="checkbox"]').nth(1)
        if not ocr_checkbox.is_checked():
            ocr_checkbox.check()
        if not seg_checkbox.is_checked():
            seg_checkbox.check()

        # Click analyze
        print("🚀 Starting analysis...")
        analyze_button = page.locator('button:has-text("분석 시작")')
        analyze_button.click()

        # Wait for completion
        print("⏳ Waiting for analysis to complete...")
        page.wait_for_selector('text=/분석 완료/', timeout=60000)
        page.wait_for_timeout(2000)
        page.screenshot(path="/home/uproot/ax/poc/screenshot_tooltip_2_complete.png")

        # Test OCR tab tooltips
        print("\n📊 Testing OCR tab tooltips...")
        ocr_tab = page.locator('button:has-text("OCR")')
        ocr_tab.click()
        page.wait_for_timeout(500)

        # Find Dimensions tooltip element
        dimensions_label = page.locator('text="Dimensions"').filter(has=page.locator('xpath=ancestor::div[contains(@class, "bg-accent")]')).first

        print("  Testing 'Dimensions' tooltip:")
        # Get cursor style
        cursor_style = dimensions_label.evaluate('el => window.getComputedStyle(el).cursor')
        print(f"    - Cursor style: {cursor_style}")

        # Hover over the element
        dimensions_label.hover()
        page.wait_for_timeout(1000)  # Wait for tooltip to appear
        page.screenshot(path="/home/uproot/ax/poc/screenshot_tooltip_3_dimensions_hover.png")

        # Check if tooltip is visible
        tooltip = page.locator('div[role="tooltip"]')
        if tooltip.is_visible():
            tooltip_text = tooltip.inner_text()
            print(f"    ✅ Tooltip visible: {tooltip_text}")
        else:
            print("    ❌ Tooltip NOT visible")

        # Test GD&T tooltip
        print("\n  Testing 'GD&T' tooltip:")
        gdt_label = page.locator('text="GD&T"').filter(has=page.locator('xpath=ancestor::div[contains(@class, "bg-accent")]')).first
        cursor_style = gdt_label.evaluate('el => window.getComputedStyle(el).cursor')
        print(f"    - Cursor style: {cursor_style}")

        gdt_label.hover()
        page.wait_for_timeout(1000)
        page.screenshot(path="/home/uproot/ax/poc/screenshot_tooltip_4_gdt_hover.png")

        tooltip = page.locator('div[role="tooltip"]')
        if tooltip.is_visible():
            tooltip_text = tooltip.inner_text()
            print(f"    ✅ Tooltip visible: {tooltip_text}")
        else:
            print("    ❌ Tooltip NOT visible")

        # Test segmentation tab
        print("\n📊 Testing Segmentation tab tooltips...")
        seg_tab = page.locator('button:has-text("세그멘테이션")')
        seg_tab.click()
        page.wait_for_timeout(500)

        # Test Contours tooltip
        print("\n  Testing 'Contours' tooltip:")
        contours_label = page.locator('text="Contours"').first
        cursor_style = contours_label.evaluate('el => window.getComputedStyle(el).cursor')
        print(f"    - Cursor style: {cursor_style}")

        contours_label.hover()
        page.wait_for_timeout(1000)
        page.screenshot(path="/home/uproot/ax/poc/screenshot_tooltip_5_contours_hover.png")

        tooltip = page.locator('div[role="tooltip"]')
        if tooltip.is_visible():
            tooltip_text = tooltip.inner_text()
            print(f"    ✅ Tooltip visible: {tooltip_text}")
        else:
            print("    ❌ Tooltip NOT visible")

        # Test Components tooltip at top
        print("\n  Testing 'Components' tooltip:")
        components_label = page.locator('text="Components"').first
        cursor_style = components_label.evaluate('el => window.getComputedStyle(el).cursor')
        print(f"    - Cursor style: {cursor_style}")

        components_label.hover()
        page.wait_for_timeout(1000)
        page.screenshot(path="/home/uproot/ax/poc/screenshot_tooltip_6_components_hover.png")

        tooltip = page.locator('div[role="tooltip"]')
        if tooltip.is_visible():
            tooltip_text = tooltip.inner_text()
            print(f"    ✅ Tooltip visible: {tooltip_text}")
        else:
            print("    ❌ Tooltip NOT visible")

        print("\n⏸️  Keeping browser open for 5 seconds for manual inspection...")
        page.wait_for_timeout(5000)

        browser.close()

        print("\n" + "="*60)
        print("✅ Tooltip test completed!")
        print("="*60)

if __name__ == "__main__":
    test_tooltip()
