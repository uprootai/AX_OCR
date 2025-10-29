#!/usr/bin/env python3
from playwright.sync_api import sync_playwright

def test_ocr_visualize():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page(viewport={'width': 1920, 'height': 1080})

        # Go to TestEdocr2 page
        page.goto("http://localhost:5173/test/edocr2", wait_until="networkidle")
        page.wait_for_timeout(1000)

        # Select image file
        file_input = page.locator('input[type="file"]')
        file_input.set_input_files('/home/uproot/ax/poc/web-ui/public/samples/sample2_interm_shaft.jpg')
        page.wait_for_timeout(1000)

        # Check visualize option
        visualize_cb = page.locator('input[type="checkbox"]').nth(3)  # 4th checkbox (visualize)
        visualize_cb.check()
        page.wait_for_timeout(500)

        # Listen to API responses
        responses = []
        def handle_response(response):
            if '/api/v1/ocr' in response.url:
                responses.append(response)

        page.on('response', handle_response)

        # Click OCR 실행 button
        page.locator('button:has-text("OCR 실행")').click()

        # Wait for results
        try:
            page.wait_for_selector('text=/OCR 결과/', timeout=60000)
            page.wait_for_timeout(2000)
            print("✅ OCR 완료")
        except Exception as e:
            print(f"❌ OCR 실패: {e}")
            browser.close()
            return

        # Get response data
        if responses:
            response = responses[0]
            try:
                data = response.json()
                print("\n=== API Response ===")
                print(f"Status: {data.get('status')}")
                if 'data' in data:
                    result_data = data['data']
                    print(f"Dimensions: {len(result_data.get('dimensions', []))}")
                    print(f"GDT: {len(result_data.get('gdt', []))}")

                    # Check for visualization fields
                    if 'visualization_url' in result_data:
                        print(f"✅ visualization_url: {result_data['visualization_url']}")
                    else:
                        print("❌ No visualization_url field")

                    if 'visualization' in result_data:
                        print(f"✅ visualization: {result_data['visualization']}")
                    else:
                        print("❌ No visualization field")

                    # Print all keys
                    print(f"\nAll keys in data: {list(result_data.keys())}")
            except Exception as e:
                print(f"Error parsing response: {e}")

        page.screenshot(path="/home/uproot/ax/poc/screenshot_ocr_visualize.png", full_page=True)
        page.wait_for_timeout(2000)
        browser.close()

if __name__ == "__main__":
    test_ocr_visualize()
