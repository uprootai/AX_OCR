---
name: presentation-guide
description: PPT/PDF 발표자료 생성 가이드. python-pptx 디자인 규격, 검증 체크리스트, 메트릭 카드 패턴 포함. 성과발표, 투자IR, 고객 제안서 등 산출물 생성 시 참조.
---

# Presentation Guide — 발표자료 생성 스킬

---

## 디자인 규격

### 색상 팔레트

| 용도 | 배경 (BG) | 텍스트 (DARK) | 사용처 |
|------|-----------|--------------|--------|
| 100% 달성 | `#E2EFDA` | `#548235` | 달성도, 성공 지표 |
| 90% 달성 | `#FFF2CC` | `#BF8F00` | 높은 달성도 |
| 80% 달성 | `#FCEACD` | `#C55A11` | 중간 달성도 |
| 70% 달성 | `#FCE4D6` | `#C00000` | 주의 필요 |
| 정보 카드 | `#D6E4F0` | `#2E75B6` | 매출, 수치 정보 |
| 헤더/강조 | `#1F4E79` | `#FFFFFF` | 테이블 헤더 |

### 폰트 크기

| 요소 | 크기 | 볼드 |
|------|------|------|
| 슬라이드 제목 | 18pt | O |
| 본문 텍스트 | 14pt | X |
| 테이블 내용 | 12pt | X |
| 메트릭 카드 숫자 | 28pt | O |
| 메트릭 카드 라벨 | 11pt | X |
| 각주/출처 | 10pt | X |

### 메트릭 카드 패턴 (python-pptx)

```python
from pptx.enum.shapes import MSO_SHAPE

def add_metric_card(slide, left, top, width, height,
                    value_text, label_text, bg_hex, value_color, label_color=None):
    shape = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = RGBColor(
        int(bg_hex[0:2], 16), int(bg_hex[2:4], 16), int(bg_hex[4:6], 16)
    )
    shape.line.fill.background()
    shape.adjustments[0] = 0.08  # 모서리 둥글기

    tf = shape.text_frame
    tf.word_wrap = True
    # 큰 숫자
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    run = p.add_run()
    run.text = value_text
    run.font.size = Pt(28)
    run.font.bold = True
    run.font.color.rgb = value_color
    # 라벨
    p2 = tf.add_paragraph()
    p2.alignment = PP_ALIGN.CENTER
    run2 = p2.add_run()
    run2.text = label_text
    run2.font.size = Pt(11)
    run2.font.color.rgb = label_color or RGBColor(0x80, 0x80, 0x80)
```

### 테이블 셀 배경색

```python
def set_cell_bg(cell, hex_color):
    from pptx.oxml.ns import qn
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    for existing in tcPr.findall(qn("a:solidFill")):
        tcPr.remove(existing)
    solidFill = tcPr.makeelement(qn("a:solidFill"), {})
    srgbClr = solidFill.makeelement(qn("a:srgbClr"), {"val": hex_color})
    solidFill.append(srgbClr)
    tcPr.append(solidFill)
```

---

## 3중 검증 체크리스트

### 1단계: PDF 원본 대조

```bash
# PDF에서 수치 추출
python3 -c "
import fitz
doc = fitz.open('보고서.pdf')
for page in doc:
    print(page.get_text())
"
```

- 매출액, 고용, 투자, 지재권 수치 일치 확인
- 날짜/등록번호 정확성

### 2단계: 코드베이스 대조

- 노드 수: `nodeDefinitions.ts`의 실제 개수
- 템플릿 수: `templateDefinitions.ts`의 실제 개수
- API 수: `apiRegistry.ts`의 실제 개수
- BOM 버전: `api_server.py`의 VERSION 값

### 3단계: 수치 체크리스트

- [ ] 총 사업비
- [ ] 정부지원금 / 기업부담금
- [ ] 집행률
- [ ] 매출액
- [ ] 신규 고용
- [ ] 지재권 (특허 + SW)
- [ ] 8대 목표 달성도
- [ ] API 서비스 수

---

## 슬라이드 구성 원칙

1. **한 슬라이드 = 한 메시지**: 핵심 수치 3-5개 + 보조 텍스트
2. **빈 공간 활용**: 하단 40%가 비면 메트릭 카드 배치
3. **컬러코딩 일관성**: 100%=초록, 90%=노랑, 80%=주황, 정보=파랑
4. **숫자 먼저**: 텍스트 설명보다 큰 숫자가 먼저 보이도록

---

## 참조 스크립트

- `docs/초기창업패키지/presentation/generate_pptx.py` — v6 기준 전체 코드
- `.claude/skills/diagram-strategy.md` — 다이어그램 컴포넌트 (docs-site용)
