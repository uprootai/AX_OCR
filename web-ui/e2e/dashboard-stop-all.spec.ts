import { test, expect } from '@playwright/test';

test.describe('Dashboard Stop All 기능 테스트', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:5173/dashboard');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);
  });

  test('각 카테고리별 Stop All 버튼 순차 클릭', async ({ page }) => {
    // 모든 Stop All 버튼 찾기
    const stopButtons = page.locator('button:has-text("Stop All")');
    const count = await stopButtons.count();

    console.log(`\n총 ${count}개의 Stop All 버튼 발견\n`);

    // 각 버튼을 인덱스로 클릭 (위에서부터 아래로)
    for (let i = 0; i < count; i++) {
      const button = stopButtons.nth(i);

      // 버튼이 보이는지 확인
      if (await button.isVisible()) {
        // 버튼의 부모 요소에서 카테고리 이름 추출 시도
        const buttonText = await button.textContent();
        console.log(`\n=== 버튼 ${i + 1}/${count} 클릭 ===`);

        // 확인 다이얼로그 처리
        page.once('dialog', async dialog => {
          console.log(`다이얼로그: ${dialog.message().split('\n')[0]}`);
          await dialog.accept();
        });

        await button.click();

        // 처리 대기
        await page.waitForTimeout(3000);

        console.log(`버튼 ${i + 1} 처리 완료`);
      }
    }

    // 최종 대기
    await page.waitForTimeout(2000);

    // 스크린샷
    await page.screenshot({
      path: 'e2e/screenshots/dashboard-after-stop-all.png',
      fullPage: true
    });

    console.log('\n=== 모든 Stop All 버튼 클릭 완료 ===');
  });
});
