# S03: TAG 검출 확인/수정 UI

> 크롭별 TAG bbox 오버레이 + 승인/수정/삭제 HITL

## 상태: ✅ Done (2026-03-27)

## 구현 내용
- `BmtWorkflowSection.tsx` Step 2 (TAG 확인) 구현
- 크롭 OCR 오버레이 이미지 표시 (docs-site e11-ocr-*.png)
- 크롭별 TAG 목록 (BOM 상태 아이콘 + Part List 코드)
- 승인(✅)/삭제(🗑️) 버튼 → PUT /bmt/{session_id}/tags/{tag_id} 호출
- 크롭 네비게이션 탭 + 이전/다음 버튼
- CROP_IMAGE_MAP으로 크롭 이름 → 이미지 URL 매핑
- nginx에 /bom/bmt-visuals/ alias 추가

## 완료 조건
- [x] 구현 완료
- [x] tsc --noEmit 에러 0
- [x] Docker 배포 후 UI 확인
