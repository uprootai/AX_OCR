# AX 도면 분석 시스템 - 인사이트 아카이브

> 벤치마크 테스트, 실험 결과, 최적화 인사이트 문서화

---

## 디렉토리 구조

```
docs/insights/
├── README.md                    # 이 파일
├── benchmarks/                  # 벤치마크 테스트 결과
│   ├── 2024-12-09_esrgan-ocr-benchmark.md
│   └── ...
├── optimizations/               # 최적화 실험 결과
│   └── ...
├── model-comparisons/           # 모델 비교 분석
│   └── ...
└── lessons-learned/             # 교훈 및 베스트 프랙티스
    └── ...
```

---

## 인사이트 카테고리

### 1. Benchmarks (벤치마크)
파이프라인 성능 측정 및 비교 결과

### 2. Optimizations (최적화)
하이퍼파라미터 튜닝, 전처리 실험 결과

### 3. Model Comparisons (모델 비교)
OCR 엔진, 검출 모델 간 비교 분석

### 4. Lessons Learned (교훈)
실무 적용 시 발견한 문제점과 해결책

---

## 문서 작성 가이드

### 템플릿
```markdown
# [제목]

- **날짜**: YYYY-MM-DD
- **작성자**: [이름]
- **카테고리**: benchmark | optimization | comparison | lesson

## 개요
[테스트/실험 목적]

## 환경
- 이미지: [파일명, 해상도]
- 파이프라인: [노드 구성]
- 파라미터: [주요 설정값]

## 결과
[정량적 결과 - 표, 그래프]

## 인사이트
[발견한 핵심 통찰]

## 권장 사항
[다음 단계, 개선 방향]
```

---

## 최근 인사이트

| 날짜 | 제목 | 카테고리 | 핵심 발견 |
|------|------|----------|----------|
| 2024-12-09 | ESRGAN-OCR 전처리 벤치마크 | benchmark | 업스케일 시 검출량↑, 오인식률도↑ |

---

## 활용 방법

1. **모델 선택 시**: `model-comparisons/` 참고
2. **파이프라인 설계 시**: `benchmarks/` 참고
3. **문제 해결 시**: `lessons-learned/` 참고
4. **파라미터 튜닝 시**: `optimizations/` 참고

---

*Managed by AX Team*
