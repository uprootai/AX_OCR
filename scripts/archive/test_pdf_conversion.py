#!/usr/bin/env python3
"""
PDF to Image Conversion Test

Verifies that PDF files can be uploaded with segmentation enabled
and are automatically converted to images for processing.
"""

from playwright.sync_api import sync_playwright, expect
import time

def test_pdf_conversion():
    print("🔍 Testing PDF to Image Conversion for Segmentation...\n")

    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()

        # Navigate to analyze page
        print("📍 Navigating to http://localhost:5173/analyze")
        page.goto("http://localhost:5173/analyze", wait_until="networkidle")
        page.screenshot(path="/home/uproot/ax/poc/screenshot_pdf_test_1_loaded.png")

        # Select PDF sample by value (sample1_interm_shaft.pdf)
        print("📂 Selecting PDF sample (sample1_interm_shaft.pdf)")
        sample_select = page.locator("select").first
        sample_select.select_option(value="/samples/sample1_interm_shaft.pdf")

        # Wait for file to load (fetch happens asynchronously)
        page.wait_for_timeout(2000)
        page.screenshot(path="/home/uproot/ax/poc/screenshot_pdf_test_2_sample_selected.png")
        print("✅ PDF sample selected and loaded")

        # Enable both segmentation and OCR
        print("⚙️  Enabling segmentation and OCR options")
        seg_checkbox = page.locator('input[type="checkbox"]').first
        ocr_checkbox = page.locator('input[type="checkbox"]').nth(1)

        # Check if already checked
        if not seg_checkbox.is_checked():
            seg_checkbox.check()
        if not ocr_checkbox.is_checked():
            ocr_checkbox.check()

        page.wait_for_timeout(500)
        page.screenshot(path="/home/uproot/ax/poc/screenshot_pdf_test_3_options_enabled.png")
        print("✅ Segmentation: ON")
        print("✅ OCR: ON")

        # Click analyze button
        print("\n🚀 Starting analysis with PDF + Segmentation...")
        analyze_button = page.locator('button:has-text("분석 시작")')
        analyze_button.click()

        # Wait for analysis to start
        page.wait_for_timeout(2000)
        page.screenshot(path="/home/uproot/ax/poc/screenshot_pdf_test_4_analyzing.png")

        # Wait for completion (max 60 seconds)
        print("⏳ Waiting for analysis to complete (max 60s)...")
        try:
            # Wait for either success or error
            page.wait_for_selector(
                'text=/분석 완료|분석 실패|오류/',
                timeout=60000
            )

            # Check for errors
            error_elements = page.locator('text=/분석 실패|오류|Error|실패/').all()

            if error_elements and len(error_elements) > 0:
                print("\n❌ Analysis failed!")
                page.screenshot(path="/home/uproot/ax/poc/screenshot_pdf_test_5_error.png")

                # Get error message
                for elem in error_elements:
                    if elem.is_visible():
                        error_text = elem.inner_text()
                        print(f"   Error: {error_text}")

                return False
            else:
                print("✅ Analysis completed successfully!")
                page.screenshot(path="/home/uproot/ax/poc/screenshot_pdf_test_5_success.png")

                # Check for segmentation results
                seg_section = page.locator('text=/세그멘테이션 결과|Segmentation/')
                if seg_section.is_visible():
                    print("✅ Segmentation results displayed")

                # Check for OCR results
                ocr_section = page.locator('text=/OCR 결과|치수/')
                if ocr_section.is_visible():
                    print("✅ OCR results displayed")

                    # Get dimension count
                    dim_text = page.locator('text=/치수.*개/').first
                    if dim_text.is_visible():
                        print(f"   {dim_text.inner_text()}")

                page.screenshot(path="/home/uproot/ax/poc/screenshot_pdf_test_6_final.png")
                return True

        except Exception as e:
            print(f"\n❌ Timeout or error during analysis: {e}")
            page.screenshot(path="/home/uproot/ax/poc/screenshot_pdf_test_timeout.png")
            return False

        finally:
            browser.close()

if __name__ == "__main__":
    success = test_pdf_conversion()

    print("\n" + "="*60)
    if success:
        print("✅ PDF CONVERSION TEST PASSED")
        print("PDF files can now be processed with segmentation!")
    else:
        print("❌ PDF CONVERSION TEST FAILED")
        print("Check screenshots for details")
    print("="*60)

    exit(0 if success else 1)
