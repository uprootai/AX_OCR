# PDF Export API

> P&ID 분석 결과 PDF 리포트 내보내기
> **포트**: 5020 | **카테고리**: Analysis | **GPU**: 불필요

---

## 개요

P&ID 분석 결과를 전문적인 PDF 리포트로 내보냅니다. TECHCROSS BWMS 스타일의 표지, 요약 통계, 상세 목록을 포함합니다.

---

## 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/api/v1/pid-features/{session_id}/export/pdf` | PDF 리포트 생성 |

---

## 파라미터

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `session_id` | string | (필수) | 세션 ID (경로) |
| `export_type` | string | all | 내보내기 범위 |
| `project_name` | string | "Unknown Project" | PDF 표지 프로젝트명 |
| `drawing_no` | string | "N/A" | 도면 번호 |
| `include_rejected` | boolean | false | 거부된 항목 포함 |

### export_type 옵션

- `all`: 모든 섹션 포함
- `valve`: Valve Signal List만
- `equipment`: Equipment List만
- `checklist`: Design Checklist만
- `deviation`: Deviation Report만

---

## 응답

- **Content-Type**: `application/pdf`
- **Content-Disposition**: `attachment; filename=PID_Report_{type}_{drawing_no}_{date}.pdf`

---

## 사용 예시

```bash
curl -X POST "http://localhost:5020/api/v1/pid-features/sess_123/export/pdf?export_type=all&project_name=BWMS&drawing_no=DWG-001" \
  -o report.pdf
```

---

**최종 수정**: 2026-01-17
