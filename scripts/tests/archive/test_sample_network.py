from playwright.sync_api import sync_playwright
import time

def test():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page(viewport={'width': 1400, 'height': 1200})

        # Listen to network requests
        requests = []
        responses = []

        page.on("request", lambda req: requests.append({
            "url": req.url,
            "method": req.method
        }))

        page.on("response", lambda res: responses.append({
            "url": res.url,
            "status": res.status,
            "ok": res.ok
        }))

        # Listen to console
        page.on("console", lambda msg: print(f"[Console {msg.type}] {msg.text}"))
        page.on("pageerror", lambda err: print(f"[Error] {err}"))

        print("📍 1. 페이지 로딩...")
        page.goto("http://localhost:5173/test/gateway")
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        print("📍 2. 샘플 버튼 클릭...")
        sample_buttons = page.locator('button:has-text("합성 테스트 도면")')
        print(f"   샘플 버튼 개수: {sample_buttons.count()}")

        if sample_buttons.count() > 0:
            # Clear previous requests/responses
            requests.clear()
            responses.clear()

            sample_buttons.first.click()
            print("   버튼 클릭됨, 대기 중...")
            time.sleep(5)

            # Print network activity
            print("\n📡 Network Requests:")
            for req in requests[-10:]:
                print(f"   {req['method']} {req['url']}")

            print("\n📡 Network Responses:")
            for res in responses[-10:]:
                status_icon = "✅" if res['ok'] else "❌"
                print(f"   {status_icon} {res['status']} {res['url']}")

            # Check if file preview appeared
            file_preview = page.locator('text=업로드된 파일')
            if file_preview.is_visible():
                print("\n✅ 파일 미리보기 표시됨!")

                # Get file type
                file_type = page.locator('text=타입').locator('..').locator('span.font-medium')
                if file_type.is_visible():
                    print(f"   파일 타입: {file_type.text_content()}")

                # Check for image
                img = page.locator('img[alt*="미리보기"]')
                if img.is_visible():
                    print("   ✅ 이미지 표시됨!")
                else:
                    print("   ❌ 이미지 없음")
            else:
                print("\n❌ 파일 미리보기 표시 안됨")

            # Take screenshot
            page.screenshot(path="/home/uproot/ax/poc/test_network_debug.png")

        time.sleep(3)
        browser.close()

if __name__ == "__main__":
    test()
