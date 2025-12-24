# eDOCr v1 모델 다운로드 정보

## 📦 모델 자동 다운로드 메커니즘

### 1. download_and_verify() 함수

**위치**: `eDOCr/keras_ocr/tools.py:501-530`

**동작 방식**:
```python
def download_and_verify(url, sha256=None, cache_dir=None, verbose=True, filename=None):
    """
    1. cache_dir이 None이면 get_default_cache_dir() 호출 (기본: ~/.keras-ocr)
    2. filename이 None이면 URL에서 파일명 추출
    3. 캐시 디렉토리에 파일 경로 생성: {cache_dir}/{filename}
    4. 파일이 없거나 sha256 해시가 맞지 않으면:
       - urllib.request.urlretrieve(url, filepath)로 다운로드
    5. sha256 검증
    6. 파일 경로 반환
    """
```

### 2. 기본 캐시 디렉토리

**함수**: `get_default_cache_dir()`
**위치**: `eDOCr/keras_ocr/tools.py:478-500`

**기본 경로**:
- Linux/Mac: `~/.keras-ocr/`
- Windows: `C:\Users\{username}\.keras-ocr\`

**Docker 컨테이너 내부**:
- `/root/.keras-ocr/` (root 사용자)

---

## 📥 eDOCr v1 모델 다운로드 정보

### 모델 1: recognizer_infoblock.h5

```python
url = "https://github.com/javvi51/eDOCr/releases/download/v1.0.0/recognizer_infoblock.h5"
sha256 = "e0a317e07ce75235f67460713cf1b559e02ae2282303eec4a1f76ef211fcb8e8"
cache_path = "~/.keras-ocr/recognizer_infoblock.h5"
file_size = ~67 MB
```

**다운로드 링크**: https://github.com/javvi51/eDOCr/releases/download/v1.0.0/recognizer_infoblock.h5

**용도**:
- 도면 인포블록(제목 블록) OCR
- 도면 번호, 개정, 제목, 재료 등 메타데이터 추출

**알파벳**: `string.digits + string.ascii_letters + ',.:-/'`

---

### 모델 2: recognizer_dimensions.h5

```python
url = "https://github.com/javvi51/eDOCr/releases/download/v1.0.0/recognizer_dimensions.h5"
sha256 = "a1c27296b1757234a90780ccc831762638b9e66faf69171f5520817130e05b8f"
cache_path = "~/.keras-ocr/recognizer_dimensions.h5"
file_size = ~67 MB
```

**다운로드 링크**: https://github.com/javvi51/eDOCr/releases/download/v1.0.0/recognizer_dimensions.h5

**용도**:
- 치수 텍스트 인식
- 공차 값 추출
- 수치 및 단위 파싱

**알파벳**: `string.digits + 'AaBCDRGHhMmnx' + '(),.+-±:/°"⌀'`

---

### 모델 3: recognizer_gdts.h5

```python
url = "https://github.com/javvi51/eDOCr/releases/download/v1.0.0/recognizer_gdts.h5"
sha256 = "58acf6292a43ff90a344111729fc70cf35f0c3ca4dfd622016456c0b29ef2a46"
cache_path = "~/.keras-ocr/recognizer_gdts.h5"
file_size = ~67 MB
```

**다운로드 링크**: https://github.com/javvi51/eDOCr/releases/download/v1.0.0/recognizer_gdts.h5

**용도**:
- 기하 공차(GD&T) 기호 인식
- GD&T 값 및 데이텀 추출

**GD&T 기호**: `⏤⏥○⌭⌒⌓⏊∠⫽⌯⌖◎↗⌰`
**FCF 기호**: `ⒺⒻⓁⓂⓅⓈⓉⓊ`
**알파벳**: `string.digits + ',.⌀ABCD' + GDT_symbols`

---

## 🔄 다운로드 프로세스

### API 서버 시작 시:

```
1. @app.on_event("startup") 실행
2. load_models() 함수 호출
3. 각 모델에 대해 keras_tools.download_and_verify() 호출

   모델 1:
   - Looking for /root/.keras-ocr/recognizer_infoblock.h5
   - 파일 없음 → Downloading...
   - urllib.request.urlretrieve() 실행
   - GitHub Releases에서 다운로드
   - sha256 검증
   - ✅ 완료

   모델 2:
   - Looking for /root/.keras-ocr/recognizer_dimensions.h5
   - 파일 없음 → Downloading...
   - 다운로드 및 검증
   - ✅ 완료

   모델 3:
   - Looking for /root/.keras-ocr/recognizer_gdts.h5
   - 파일 없음 → Downloading...
   - 다운로드 및 검증
   - ✅ 완료

4. logger.info("✅ eDOCr v1 models loaded successfully!")
```

### 재시작 시:

```
1. load_models() 함수 호출
2. 각 모델에 대해 download_and_verify() 호출
3. 파일이 이미 존재하고 sha256 일치
   - "Looking for /root/.keras-ocr/recognizer_infoblock.h5"
   - 파일 있음, 해시 일치 → 다운로드 스킵
4. ✅ 즉시 로드 완료 (다운로드 없음)
```

---

## 📊 다운로드 크기 및 시간

| 모델 | 크기 | 다운로드 시간 (예상) |
|------|------|----------------------|
| recognizer_infoblock.h5 | ~67 MB | 10-30초 |
| recognizer_dimensions.h5 | ~67 MB | 10-30초 |
| recognizer_gdts.h5 | ~67 MB | 10-30초 |
| **전체** | **~200 MB** | **30초-2분** |

**첫 시작 시**: 모든 모델 다운로드 (200MB, 1-2분)
**재시작 시**: 다운로드 없음 (즉시)

---

## 🐳 Docker 컨테이너에서

### 볼륨 마운트를 통한 캐시 공유

**docker-compose.v1.yml**에 추가 가능:
```yaml
services:
  edocr2:
    volumes:
      - ./uploads:/app/uploads
      - ./results:/app/results
      - ./keras-ocr-cache:/root/.keras-ocr  # 모델 캐시
```

**장점**:
- 컨테이너 재생성 시 모델 재다운로드 불필요
- 호스트에서 모델 파일 확인 가능
- 디스크 공간 절약

### 현재 설정 (볼륨 없음)

**상태**: 모델이 컨테이너 내부에만 저장
**영향**:
- 컨테이너 삭제 시 모델도 삭제
- 재생성 시 모델 재다운로드 필요
- 200MB 다운로드 (1-2분)

---

## 🔍 모델 다운로드 확인 방법

### 1. 로컬 확인
```bash
# 호스트 시스템에서
ls -lh ~/.keras-ocr/
# recognizer_infoblock.h5
# recognizer_dimensions.h5
# recognizer_gdts.h5
```

### 2. Docker 컨테이너 내부 확인
```bash
# 컨테이너 접속
docker exec -it edocr2-api-v1 bash

# 모델 파일 확인
ls -lh /root/.keras-ocr/

# 크기 확인
du -sh /root/.keras-ocr/
# 예상 출력: 200M /root/.keras-ocr/
```

### 3. API 로그 확인
```bash
docker-compose -f docker-compose.v1.yml logs -f

# 예상 로그:
# Looking for /root/.keras-ocr/recognizer_infoblock.h5
# Downloading /root/.keras-ocr/recognizer_infoblock.h5
# ...
# ✅ eDOCr v1 models loaded successfully!
```

### 4. Health Check
```bash
curl http://localhost:5001/api/v1/health

# 응답:
{
  "status": "healthy",
  "service": "eDOCr v1 API",
  "version": "1.0.0",
  "edocr_available": true,
  "models_loaded": true  # ✅ true면 성공
}
```

---

## ⚠️ 주의사항

### 1. 네트워크 연결 필요
- 모델 다운로드 시 GitHub 접속 필요
- 방화벽 설정 확인
- `https://github.com` 접근 가능 여부 확인

### 2. 디스크 공간
- 최소 500MB 여유 공간 필요 (모델 200MB + 기타)
- Docker 이미지 크기: ~2-3GB

### 3. 다운로드 실패 시
- 재시도: 컨테이너 재시작
- 수동 다운로드:
  ```bash
  mkdir -p ~/.keras-ocr
  cd ~/.keras-ocr

  # 각 모델 다운로드
  wget https://github.com/javvi51/eDOCr/releases/download/v1.0.0/recognizer_infoblock.h5
  wget https://github.com/javvi51/eDOCr/releases/download/v1.0.0/recognizer_dimensions.h5
  wget https://github.com/javvi51/eDOCr/releases/download/v1.0.0/recognizer_gdts.h5

  # 볼륨 마운트하여 Docker 실행
  ```

### 4. sha256 검증 실패
- 파일 손상된 경우
- 해결: 파일 삭제 후 재다운로드
  ```bash
  rm ~/.keras-ocr/recognizer_*.h5
  # 컨테이너 재시작
  ```

---

## 📝 수동 다운로드 (오프라인 환경)

### 1. 모델 다운로드 스크립트

```bash
#!/bin/bash
# download_models.sh

CACHE_DIR="$HOME/.keras-ocr"
mkdir -p "$CACHE_DIR"

echo "Downloading eDOCr v1 models..."

# Model 1: Infoblock
wget -O "$CACHE_DIR/recognizer_infoblock.h5" \
  "https://github.com/javvi51/eDOCr/releases/download/v1.0.0/recognizer_infoblock.h5"

# Model 2: Dimensions
wget -O "$CACHE_DIR/recognizer_dimensions.h5" \
  "https://github.com/javvi51/eDOCr/releases/download/v1.0.0/recognizer_dimensions.h5"

# Model 3: GD&T
wget -O "$CACHE_DIR/recognizer_gdts.h5" \
  "https://github.com/javvi51/eDOCr/releases/download/v1.0.0/recognizer_gdts.h5"

echo "✅ Models downloaded to $CACHE_DIR"
ls -lh "$CACHE_DIR"
```

### 2. 실행
```bash
chmod +x download_models.sh
./download_models.sh
```

---

## 🔗 참고 링크

- **GitHub Releases**: https://github.com/javvi51/eDOCr/releases/tag/v1.0.0
- **eDOCr 논문**: https://www.frontiersin.org/articles/10.3389/fmtec.2023.1154132/full
- **keras-ocr**: https://github.com/faustomorales/keras-ocr

---

## 📈 모델 정보 요약

| 항목 | 값 |
|------|-----|
| 모델 개수 | 3개 |
| 총 크기 | ~200MB |
| 다운로드 소스 | GitHub Releases |
| 캐시 위치 | `~/.keras-ocr/` |
| 자동 다운로드 | ✅ 지원 |
| sha256 검증 | ✅ 지원 |
| 재시작 시 재다운로드 | ❌ 불필요 (캐시 사용) |

---

**문서 버전**: 1.0
**작성일**: 2025-10-29
