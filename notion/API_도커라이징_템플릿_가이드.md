# API 도커라이징 템플릿 가이드

> 새 API 추가 시 참고할 수 있는 표준 템플릿

---

## 위치

```
\\wsl.localhost\Ubuntu-22.04\home\uproot\ax\dockerize-sample\
```

---

## 제공 샘플

| 샘플 | 포트 | 용도 |
|------|------|------|
| `yolo-api/` | 5005 | 도면 심볼 검출 |
| `paddleocr-api/` | 5006 | 도면 텍스트 인식 |

---

## 핵심 패턴

두 샘플 모두 **95% 동일한 구조**를 따름

```
my-api/
├── Dockerfile           # 컨테이너 빌드
├── requirements.txt     # Python 의존성
├── api_server.py        # FastAPI 서버 (3개 엔드포인트)
├── services/            # 비즈니스 로직
└── utils/               # 유틸리티
```

**표준 엔드포인트**:
- `GET /api/v1/health` - 헬스체크
- `GET /api/v1/info` - API 정보
- `POST /api/v1/process` - 메인 처리 (detect, ocr 등)

---

## 새 API 추가 방법

```bash
# 1. 샘플 복사
cp -r paddleocr-api my-new-api
cd my-new-api

# 2. 수정할 파일
# - api_server.py: 엔드포인트 이름, 파라미터
# - services/: 비즈니스 로직 교체
# - requirements.txt: 필요한 라이브러리

# 3. 테스트
docker build -t my-api .
docker run -d -p 5007:5007 my-api
curl http://localhost:5007/api/v1/health
```

---

## 포함 문서

| 문서 | 내용 |
|------|------|
| `README.md` | 통합 가이드 |
| `GUIDE.md` | 도커라이징 상세 가이드 |
| `VERIFICATION_GUIDE.md` | L1-L5 검증 체크리스트 |

---

*위치: `ax/dockerize-sample/`*
