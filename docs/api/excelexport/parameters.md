# Excel Export API

> P&ID 분석 결과 Excel 내보내기
> **포트**: 5020 | **카테고리**: Analysis | **GPU**: 불필요

---

## 개요

P&ID 분석 결과를 Excel 파일로 내보냅니다. Equipment, Valve, Checklist, Deviation을 각 시트에 분리하여 정리합니다.

---

## 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/api/v1/pid-features/{session_id}/export` | Excel 파일 생성 |

---

## 파라미터

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `session_id` | string | (필수) | 세션 ID (경로) |
| `export_type` | string | (필수) | 내보내기 범위 |
| `project_name` | string | "Unknown Project" | 프로젝트명 |
| `drawing_no` | string | "N/A" | 도면 번호 |
| `include_rejected` | boolean | false | 거부된 항목 포함 |

### export_type 옵션

- `all`: 모든 시트 포함
- `valve`: Valve 시트만
- `equipment`: Equipment 시트만
- `checklist`: Checklist 시트만
- `deviation`: Deviation 시트만

---

## 응답

- **Content-Type**: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- **Content-Disposition**: `attachment; filename=PID_Analysis_{type}_{drawing_no}_{date}.xlsx`

---

## 사용 예시

```bash
curl -X POST "http://localhost:5020/api/v1/pid-features/sess_123/export?export_type=all&project_name=BWMS" \
  -o analysis.xlsx
```

---

**최종 수정**: 2026-01-17
