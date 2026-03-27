# S04: BOM 매칭 + 불일치 판정

> TAG→Part List→ERP BOM 매칭 + 불일치 판정 UI

## 상태: ✅ Done (2026-03-27)

## 구현 내용
- `BmtWorkflowSection.tsx` Step 3 (BOM 매칭) 구현
- 불일치 3건 하이라이트 (B02/PI02/V06) + "실제 오류"/"정상 차이" 판정 버튼
- 필터 탭 (전체 25 / 매칭 19 / 불일치 3 / 미매핑 3)
- 25개 TAG 전체 테이블 (상태 아이콘 + 결과 배지 + 판정 컬럼)
- PUT /bmt/{session_id}/bom-match/{tag} 호출

## 완료 조건
- [x] 구현 완료
- [x] tsc --noEmit 에러 0
- [x] Docker 배포 후 UI 확인
