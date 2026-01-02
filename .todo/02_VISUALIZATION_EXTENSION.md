# 시각화 기능 확장 계획

> PID Composer의 레이어 합성/SVG 오버레이 패턴을
> 다른 노드에도 적용하는 계획

---

## 현재 PID Composer 기능

### 제공 기능
1. **서버 사이드 이미지 렌더링** (OpenCV)
   - 심볼/라인/텍스트/영역 레이어 합성
   - PNG/JPG/WebP 출력
   - 범례 추가

2. **클라이언트 SVG 오버레이**
   - 인터랙티브 CSS 클래스
   - data-* 속성으로 메타데이터 포함
   - 호버 효과, 클릭 이벤트 지원

3. **스타일 커스터마이징**
   - 색상, 두께, 투명도
   - 라벨 표시 on/off
   - 레이어별 활성화 제어

---

## 확장 대상 노드

### 1. YOLO Detection (우선순위: HIGH)
**현재 상태**: 이미지에 bbox만 그려서 반환
**개선안**: PID Composer와 유사한 SVG 오버레이 추가

```yaml
# 추가할 출력
outputs:
  - name: svg_overlay
    type: string
    description: 검출 결과 SVG 오버레이 (프론트엔드용)
```

**작업 항목**:
- [ ] yolo-api에 svg_generator.py 추가
- [ ] detection_router.py에 include_svg 파라미터 추가
- [ ] 프론트엔드 YOLOResultViewer 컴포넌트 수정

---

### 2. Line Detector (우선순위: HIGH)
**현재 상태**: 라인 좌표만 JSON으로 반환
**개선안**: 라인 타입별 색상 구분 SVG

```yaml
# 라인 타입별 색상
line_colors:
  pipe: "#FF0000"      # 빨강
  signal: "#0000FF"    # 파랑
  dashed: "#808080"    # 회색 점선
  instrument: "#00FF00" # 초록
```

**작업 항목**:
- [ ] line-detector-api에 svg_generator.py 추가
- [ ] 라인 스타일별 SVG 스타일 정의
- [ ] include_svg 파라미터 추가

---

### 3. OCR 결과 (우선순위: MEDIUM)
**현재 상태**: 텍스트 + bbox JSON
**개선안**: 텍스트 영역 하이라이트 SVG

```yaml
# OCR SVG 스타일
text_styles:
  dimension: "#FFA500"   # 치수 - 오렌지
  tag: "#00CED1"         # 태그 - 청록
  note: "#9370DB"        # 노트 - 보라
```

**작업 항목**:
- [ ] edocr2-api에 svg_generator.py 추가
- [ ] 텍스트 카테고리별 스타일 적용
- [ ] paddleocr, tesseract 등에도 동일 패턴 적용

---

### 4. Blueprint AI BOM (우선순위: MEDIUM)
**현재 상태**: 검출 결과 테이블 표시
**개선안**: 이미지 위에 인터랙티브 오버레이

**작업 항목**:
- [ ] 세션별 SVG 오버레이 생성
- [ ] 클릭 시 검증 패널 연동
- [ ] 검증 상태별 색상 표시 (승인/거부/대기)

---

## 공통 SVG 유틸리티

### 위치: `web-ui/src/utils/svgOverlay.ts`

```typescript
// 공통 SVG 오버레이 유틸리티
interface OverlayOptions {
  width: number;
  height: number;
  interactive?: boolean;
  showLabels?: boolean;
}

interface BBoxItem {
  bbox: { x: number; y: number; width: number; height: number };
  label?: string;
  confidence?: number;
  color?: string;
  category?: string;
}

export function createSvgOverlay(
  items: BBoxItem[],
  options: OverlayOptions
): string {
  // SVG 생성 로직
}

export function parseSvgOverlay(svg: string): BBoxItem[] {
  // SVG → 데이터 파싱
}
```

**작업 항목**:
- [ ] 공통 SVG 유틸리티 모듈 생성
- [ ] PIDOverlayViewer를 제네릭 OverlayViewer로 리팩토링
- [ ] 각 노드별 뷰어에서 공통 컴포넌트 사용

---

## 프론트엔드 컴포넌트 구조

```
web-ui/src/components/overlay/
├── OverlayViewer.tsx        # 공통 오버레이 뷰어
├── OverlayControls.tsx      # 레이어 토글, 스타일 설정
├── OverlayLegend.tsx        # 범례 컴포넌트
├── hooks/
│   ├── useOverlayData.ts    # 오버레이 데이터 관리
│   └── useOverlayStyle.ts   # 스타일 상태 관리
└── types.ts                 # 공통 타입 정의
```

---

## 백엔드 SVG 생성 패턴

### 공통 구조 (각 API에 적용)

```python
# services/svg_generator.py 템플릿

from typing import List, Dict, Any, Tuple

def generate_svg_overlay(
    items: List[Dict[str, Any]],
    image_size: Tuple[int, int],
    style: Dict[str, Any] = None
) -> str:
    """SVG 오버레이 생성"""
    width, height = image_size

    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {width} {height}" '
        f'class="detection-overlay">'
    ]

    # 스타일 정의
    svg_parts.append(generate_styles(style))

    # 아이템 렌더링
    for item in items:
        svg_parts.append(render_item(item, style))

    svg_parts.append('</svg>')
    return '\n'.join(svg_parts)
```

---

## 우선순위 및 일정

| 작업 | 우선순위 | 예상 작업량 | 의존성 |
|------|----------|-------------|--------|
| 공통 SVG 유틸리티 | P0 | 2시간 | 없음 |
| YOLO SVG 확장 | P1 | 3시간 | 공통 유틸리티 |
| Line Detector SVG | P1 | 2시간 | 공통 유틸리티 |
| OCR SVG 확장 | P2 | 3시간 | 공통 유틸리티 |
| Blueprint AI BOM 연동 | P2 | 4시간 | YOLO SVG |
| 제네릭 OverlayViewer | P2 | 4시간 | 모든 SVG 완료 |
