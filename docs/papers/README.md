# Research Papers

> AX BlueprintFlow 시스템에서 사용하는 핵심 기술들의 참조 논문

## 논문 목록

### OCR & 도면 분석 (기존 시스템)
| # | 제목 | 기술 | API |
|---|------|------|-----|
| 01 | [eDOCr - OCR on Drawings](01_OCR_Engineering_Drawings.md) | eDOCr v1 | eDOCr2 |
| 02 | [eDOCr2 - VL Integration](02_eDOCr2_Vision_Language_Integration.md) | eDOCr v2 | eDOCr2 |
| 03 | [Skin Model - Tolerance](03_Geometric_Tolerance_Additive_Manufacturing.md) | Skin Model | SkinModel |
| 04 | [EDGNet - Graph Segmentation](04_Graph_Neural_Network_Engineering_Drawings.md) | EDGNet | EDGNet |

### 객체 검출 & 이미지 처리
| # | 제목 | 기술 | API |
|---|------|------|-----|
| 05 | [YOLOv11 Object Detection](05_YOLOv11_Object_Detection.md) | YOLOv11 | YOLO |
| 08 | [ESRGAN Super Resolution](08_ESRGAN_Super_Resolution.md) | ESRGAN | ESRGAN |

### OCR 엔진
| # | 제목 | 기술 | API |
|---|------|------|-----|
| 06 | [PaddleOCR PP-OCR](06_PaddleOCR_PP-OCR.md) | PP-OCR | PaddleOCR |
| 07 | [TrOCR Transformer OCR](07_TrOCR_Transformer_OCR.md) | TrOCR | TrOCR |
| 11 | [Tesseract LSTM OCR](11_Tesseract_LSTM_OCR.md) | Tesseract | Tesseract |
| 12 | [Surya Multilingual OCR](12_Surya_OCR_Multilingual.md) | Surya | Surya OCR |
| 13 | [DocTR Document OCR](13_DocTR_Document_OCR.md) | DocTR | DocTR |
| 14 | [EasyOCR Ready-to-use](14_EasyOCR_Ready_to_Use.md) | EasyOCR | EasyOCR |
| 15 | [OCR Ensemble Voting](15_OCR_Ensemble_Voting.md) | Ensemble | OCR Ensemble |

### AI & 지식 그래프
| # | 제목 | 기술 | API |
|---|------|------|-----|
| 09 | [Qwen2-VL Vision Language](09_Qwen2-VL_Vision_Language.md) | Qwen2-VL | VL |
| 10 | [GraphRAG Knowledge Graph](10_GraphRAG_Knowledge_Graph.md) | GraphRAG | Knowledge |

---

## 새 API 추가 시 논문 정리 가이드

### 1. 논문 검색
```bash
# Claude Code에서 WebSearch 사용
# 검색 쿼리 예시:
# "[기술명] paper arxiv [년도]"
# "[모델명] official paper"
```

### 2. 논문 작성
1. `TEMPLATE.md` 복사
2. 파일명: `XX_[기술명]_[카테고리].md` (XX = 번호)
3. 섹션별 내용 작성:
   - 논문 정보 (arXiv, 저자, 게재지)
   - 연구 배경
   - 핵심 방법론
   - 성능
   - AX 시스템 적용

### 3. Docs 페이지 업데이트
`web-ui/src/pages/docs/Docs.tsx`의 `docStructure`에 추가:
```typescript
{
  name: 'Research Papers',
  path: 'papers',
  type: 'folder',
  children: [
    // 기존 항목들...
    { name: '[새 논문명]', path: '/docs/papers/XX_[파일명].md', type: 'file' },
  ],
},
```

### 4. 이 README 업데이트
위 논문 목록 테이블에 새 항목 추가

---

*마지막 업데이트: 2025-12-06*
*총 15개 논문/기술 문서 정리 완료*
