# Features 동기화 빠른 수정 가이드

> 생성일: 2025-12-26
> 목적: 세 파일 간 features 정의 동기화

---

## 수정 대상 파일

1. `web-ui/src/config/nodes/inputNodes.ts` (빌더 - ImageInput)
2. `web-ui/src/config/nodes/bomNodes.ts` (빌더 - Blueprint AI BOM)
3. `blueprint-ai-bom/frontend/src/pages/workflow/sections/ActiveFeaturesSection.tsx` (워크플로우)

---

## 수정 1: inputNodes.ts 아이콘 통일

**위치**: line 23, 26, 29

```typescript
// AS-IS (BOM_FEATURES)
gdt_parsing: { label: 'GD&T 파싱', hint: 'SkinModel 노드 필요', icon: '📐' },
pid_connectivity: { label: 'P&ID 연결성', hint: 'PID Analyzer 노드 필요', icon: '🔗' },
welding_symbol_parsing: { label: '용접 기호 파싱', hint: 'YOLO 학습 필요', icon: '🔩' },

// TO-BE (checkboxGroup과 동기화)
gdt_parsing: { label: 'GD&T 파싱', hint: 'SkinModel 노드 필요', icon: '🔧' },
pid_connectivity: { label: 'P&ID 연결성', hint: 'PID Analyzer 노드 필요', icon: '🔀' },
welding_symbol_parsing: { label: '용접 기호 파싱', hint: 'YOLO 학습 필요', icon: '⚡' },
```

---

## 수정 2: ActiveFeaturesSection.tsx 아이콘 통일

**위치**: FEATURE_CONFIG 객체

```typescript
// AS-IS
gdt_parsing: { icon: '📐', ... },
pid_connectivity: { icon: '🔗', ... },

// TO-BE (inputNodes.ts checkboxGroup과 동기화)
gdt_parsing: { icon: '🔧', ... },
pid_connectivity: { icon: '🔀', ... },
```

---

## 수정 3: ActiveFeaturesSection.tsx 중복 키 정리

```typescript
// 삭제 대상 (중복)
welding_symbol: { ... },      // welding_symbol_parsing으로 통일
surface_roughness: { ... },   // surface_roughness_parsing으로 통일
```

---

## 수정 4: bomNodes.ts 누락 features 추가

**위치**: features options 배열

```typescript
// 추가 필요 (기본 검출 그룹)
{ value: 'symbol_verification', label: '✅ 심볼 검증', icon: '✅', group: '기본 검출', description: '검출된 심볼 승인/거부/수정' },
{ value: 'dimension_verification', label: '✅ 치수 검증', icon: '✅', group: '기본 검출', description: 'OCR 치수 승인/거부/수정' },
{ value: 'gt_comparison', label: '📊 GT 비교', icon: '📊', group: '기본 검출', description: 'Ground Truth 비교 및 메트릭' },

// 추가 필요 (BOM 생성 그룹)
{ value: 'bom_generation', label: '📋 BOM 생성', icon: '📋', group: 'BOM 생성', description: 'Excel/CSV/JSON 부품 목록 생성' },

// 추가 필요 (장기 로드맵 그룹)
{ value: 'drawing_region_segmentation', label: '🗺️ 영역 세분화', icon: '🗺️', group: '장기 로드맵', description: '정면도/측면도/단면도 자동 구분' },
{ value: 'notes_extraction', label: '📋 노트 추출', icon: '📋', group: '장기 로드맵', description: '재료/열처리/공차 노트 추출' },
{ value: 'revision_comparison', label: '🔄 리비전 비교', icon: '🔄', group: '장기 로드맵', description: '버전 간 변경점 자동 감지' },
{ value: 'vlm_auto_classification', label: '🤖 VLM 자동 분류', icon: '🤖', group: '장기 로드맵', description: '도면 타입 AI 분류' },
```

---

## 수정 5: inputNodes.ts에 relation_extraction 추가

**위치**: BOM_FEATURES 및 checkboxGroup options

```typescript
// BOM_FEATURES에 추가
relation_extraction: { label: '심볼-치수 관계', hint: '', icon: '🔗' },

// checkboxGroup options에 추가 (GD&T / 기계 그룹)
{ value: 'relation_extraction', label: '심볼-치수 관계', icon: '🔗', group: 'GD&T / 기계', description: '심볼과 치수 간의 공간적 관계 분석' },

// FEATURE_NODE_RECOMMENDATIONS에 추가
relation_extraction: {
  nodes: ['yolo', 'edocr2'],
  description: '검출된 심볼과 OCR 치수 간 관계 매핑',
},
```

---

## 최종 아이콘 표준 (18개 features)

| Feature | Icon | Group |
|---------|------|-------|
| symbol_detection | 🎯 | 기본 검출 |
| symbol_verification | ✅ | 기본 검출 |
| dimension_ocr | 📏 | 기본 검출 |
| dimension_verification | ✅ | 기본 검출 |
| gt_comparison | 📊 | 기본 검출 |
| gdt_parsing | 🔧 | GD&T / 기계 |
| line_detection | 📐 | GD&T / 기계 |
| relation_extraction | 🔗 | GD&T / 기계 |
| welding_symbol_parsing | ⚡ | GD&T / 기계 |
| surface_roughness_parsing | 🔲 | GD&T / 기계 |
| pid_connectivity | 🔀 | P&ID |
| bom_generation | 📋 | BOM 생성 |
| title_block_ocr | 📝 | BOM 생성 |
| quantity_extraction | 🔢 | BOM 생성 |
| balloon_matching | 🎈 | BOM 생성 |
| drawing_region_segmentation | 🗺️ | 장기 로드맵 |
| notes_extraction | 📋 | 장기 로드맵 |
| revision_comparison | 🔄 | 장기 로드맵 |
| vlm_auto_classification | 🤖 | 장기 로드맵 |

---

## 검증 명령어

```bash
# 세 파일의 feature 키 비교
grep -oP "value: '[^']+'" web-ui/src/config/nodes/inputNodes.ts | sort | uniq
grep -oP "value: '[^']+'" web-ui/src/config/nodes/bomNodes.ts | sort | uniq
grep -oP "^\s+[a-z_]+:" blueprint-ai-bom/frontend/src/pages/workflow/sections/ActiveFeaturesSection.tsx | sort | uniq

# 아이콘 비교
grep -oP "icon: '[^']+'" web-ui/src/config/nodes/inputNodes.ts | sort | uniq
```

---

**작성자**: Claude Code (Opus 4.5)
