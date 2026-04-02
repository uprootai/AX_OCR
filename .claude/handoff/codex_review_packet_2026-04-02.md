# Codex 검토 패킷 — gt-validation 페이지 전체 검토

> **목적**: `http://localhost:3001/customer-cases/dsebearing/ensemble/gt-validation/` 페이지의 문서 정합성, 수치 정확성, 이미지 일관성을 검토하고 개선 사항을 제안한다.

## 검토 대상 파일

```
docs-site-starlight/src/content/docs/customer-cases/dsebearing/ensemble/gt-validation.mdx
```

## 검토 항목

### 1. 수치 정합성
- 문서 내 테이블 수치가 실제 스크립트 실행 결과와 일치하는지
- 특히 다음 테이블들:
  - v7 최종 결과 (7/7, 7/7, 5/7)
  - GRADIENT_ALT 전체 도면 검증 (T1~T8)
  - 돌출부 4방향 최대치 (N/S/E/W)
  - 전체 도면 직선 투사 결과 (히트 수)
  - S01 화살촉 쌍 + 투사선 필터 (248개, 123쌍, 72쌍)

### 2. 이미지-텍스트 일관성
- 이미지 헤더의 수치와 문서 테이블 수치가 일치하는지
- 이미지 파일이 실제로 존재하고 올바르게 참조되는지
- `public/images/gt-validation/steps/` 디렉토리 내 파일 목록 확인

### 3. 섹션 구조
- h2/h3/h4 헤딩 계층이 논리적인지
- 중복되는 내용이 없는지 (특히 "전체 도면 투사" 관련 내용이 여러 곳에 있었음)
- 시각화 범례가 실제 이미지와 일치하는지

### 4. 알려진 문제
- 투사선 필터 72/123 통과 — 사선 치수선 포함, 개선 필요
- T4/T8 고해상도(6623px) 화살촉 4개만 검출
- OD/ID 미검출 원인이 명확히 문서화되었는지
- 돌출부 이미지가 전체 도면 투사 이미지와 sync되지 않음 (전체 도면은 이전 돌출부 기준)

### 5. 스크립트 검증
아래 스크립트들이 오류 없이 실행되는지 확인:
```bash
# 동심원 5단계
python3 blueprint-ai-bom/scripts/generate_concentric_steps.py

# ALT 전 도면 검증
python3 blueprint-ai-bom/scripts/generate_concentric_alt_all.py

# 돌출부 4방향
python3 blueprint-ai-bom/scripts/generate_protrusion_detect.py

# 전체 도면 투사 + 돌출부
python3 blueprint-ai-bom/scripts/s08_cardinal_v3_fullpage.py

# S01 통합
python3 blueprint-ai-bom/scripts/s01_cardinal_integration.py
```

## 핵심 기술 결정 (검토 시 참고)

| 결정 | 이유 | 검증 포인트 |
|------|------|-----------|
| HOUGH_GRADIENT_ALT | 3D 누적기로 동심원 검출 | 4도면 모두 3개 동심원 일관 검출? |
| S01 Black Hat 화살촉 | 치수선 화살촉만 정밀 검출 | 248개 vs 1296개 비교 정확? |
| 4방향 solid 스캔 | 치수선/텍스트 오인 방지 | E/W 플랜지가 외원 바깥으로 잡히는지 |
| 투사선 접선 방향 | N/S→수평, E/W→수직 | 도면 치수선 배치와 물리적으로 맞는지 |

## 빌드 + 배포 (변경 시)
```bash
cd docs-site-starlight && npx astro build && \
docker cp dist/. docs-site:/usr/share/nginx/html/ && \
docker exec docs-site nginx -s reload
```
