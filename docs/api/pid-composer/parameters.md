# PID Composer API

> P&ID 도면 레이어 합성 및 시각화
> **포트**: 5021 | **카테고리**: Analysis | **GPU**: 불필요

---

## 개요

P&ID 도면에 심볼, 라인, 텍스트, 영역 레이어를 합성하여 시각화합니다. 서버 사이드 이미지 렌더링 및 클라이언트용 SVG 오버레이 생성을 지원합니다.

---

## 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/api/v1/compose` | 이미지에 레이어 합성 |
| POST | `/api/v1/compose/svg` | SVG 오버레이만 생성 |
| POST | `/api/v1/compose/layers` | 빈 캔버스에 레이어 합성 |
| POST | `/api/v1/preview` | 스타일 미리보기 |
| GET | `/api/v1/info` | 서비스 정보 |
| GET | `/health` | 헬스체크 |

---

## 파라미터

### 레이어 제어

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `enabled_layers` | multiselect | [symbols, lines, texts, regions] | 활성화할 레이어 |
| `output_format` | select | png | 출력 형식 (png, jpg, webp) |
| `include_svg` | boolean | true | SVG 오버레이 포함 |
| `include_legend` | boolean | false | 범례 포함 |

### 심볼 스타일

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `symbol_color` | color | #FF7800 | 심볼 색상 |
| `symbol_thickness` | slider | 2 | 테두리 두께 (1-10) |
| `symbol_fill_alpha` | slider | 0.1 | 채우기 투명도 (0-1) |
| `show_symbol_labels` | boolean | true | 라벨 표시 |

### 라인 스타일

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `line_thickness` | slider | 2 | 라인 두께 (1-10) |
| `show_flow_arrows` | boolean | false | 플로우 화살표 표시 |

### 텍스트 스타일

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `text_color` | color | #FFA500 | 텍스트 색상 |
| `show_text_values` | boolean | true | 텍스트 값 표시 |

### 영역 스타일

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `region_fill_alpha` | slider | 0.15 | 영역 투명도 (0-0.5) |
| `show_region_labels` | boolean | true | 영역 라벨 표시 |

---

## 사용 예시

```bash
curl -X POST http://localhost:5021/api/v1/compose \
  -H "Content-Type: application/json" \
  -d '{
    "image_base64": "<base64_encoded_image>",
    "layers": {
      "symbols": [{"bbox": {"x": 100, "y": 100, "width": 50, "height": 40}, "class_name": "Valve"}]
    },
    "enabled_layers": ["symbols"],
    "include_svg": true
  }'
```

---

**최종 수정**: 2026-01-17
