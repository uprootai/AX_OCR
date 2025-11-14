# 🚀 빠른 시작 가이드

지금 바로 시작하려면 **우선순위 1** 작업만 진행하세요!

---

## 📝 우선순위 1: 정확도 개선 (1-2주)

### 작업 1: GD&T 도면 수집 (2-3일)

```bash
# 1. 가이드 읽기
cat /home/uproot/ax/poc/TODO/PRIORITY_1_GDT_DRAWINGS.md

# 2. 도면 디렉토리 생성
mkdir -p /home/uproot/ax/poc/test_data/gdt_drawings

# 3. GD&T 심볼이 명확한 도면 10개 이상 복사
# → 가이드 참조
```

**성공 기준**: GD&T Recall 0% → 75%

---

### 작업 2: VL API 키 발급 (1일, $10-50/월)

```bash
# 1. 가이드 읽기  
cat /home/uproot/ax/poc/TODO/PRIORITY_1_VL_API_KEYS.md

# 2. OpenAI API 키 발급
# → https://platform.openai.com/api-keys

# 3. .env 파일 생성
cat > /home/uproot/ax/poc/.env << 'ENVEOF'
OPENAI_API_KEY=sk-proj-여기에-발급받은-키-입력
OPENAI_MODEL=gpt-4o
VL_PROVIDER=openai
ENVEOF

chmod 600 .env

# 4. 서비스 재시작
docker-compose restart edocr2-api-v1

# 5. 테스트
curl -X POST http://localhost:5001/api/v1/ocr/enhanced \
  -F "file=@test.pdf" \
  -F "strategy=vl"
```

**성공 기준**: Dimension Recall 50% → 90%

---

## 📊 완료 후 예상 점수

| 항목 | 현재 | 완료 후 |
|------|------|---------|
| **총점** | 82점 (A-) | 88점 (A) |
| **Dimension Recall** | 50% | 90% |
| **GD&T Recall** | 0% | 75% |
| **Production Ready** | 82% | 90%+ |

---

## 🎯 다음 단계 (선택)

### 우선순위 2 (2-4주)
- Skin Model 데이터 수집
- 보안 정책 결정

### 우선순위 3 (1-2개월)
- GPU 설정
- 프로덕션 배포

---

**지금 시작**: `cat /home/uproot/ax/poc/TODO/PRIORITY_1_GDT_DRAWINGS.md`
