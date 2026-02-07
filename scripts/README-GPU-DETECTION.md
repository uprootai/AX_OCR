# Docker GPU 자동 감지 스크립트

컨테이너 시작 시 GPU 가용성을 자동으로 체크하고 환경변수를 설정합니다.

## 사용법

### 1. Dockerfile에 스크립트 복사

```dockerfile
# 스크립트 복사 (빌드 컨텍스트에 docker-gpu-entrypoint.sh 필요)
COPY docker-gpu-entrypoint.sh /usr/local/bin/docker-gpu-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-gpu-entrypoint.sh

# 환경변수 기본값 설정
ENV USE_GPU=auto

# 엔트리포인트 설정 (폴백 포함)
ENTRYPOINT ["/bin/bash", "-c", "if [ -x /usr/local/bin/docker-gpu-entrypoint.sh ]; then exec /usr/local/bin/docker-gpu-entrypoint.sh \"$@\"; else exec \"$@\"; fi", "--"]
CMD ["python", "api_server.py"]
```

### 2. 서비스 디렉토리에 스크립트 복사

```bash
cp scripts/docker-gpu-entrypoint.sh models/my-api/docker-gpu-entrypoint.sh
```

### 3. docker-compose.yml 환경변수 설정

```yaml
services:
  my-api:
    environment:
      - USE_GPU=auto  # auto|true|false
```

## 환경변수

### 입력

| 변수 | 값 | 설명 |
|------|-----|------|
| `USE_GPU` | `auto` | (기본값) GPU 감지 시 사용, 없으면 CPU |
| `USE_GPU` | `true` | GPU 강제 사용 (없으면 경고 후 CPU) |
| `USE_GPU` | `false` | CPU 강제 사용 (GPU 무시) |

### 출력 (스크립트가 설정)

| 변수 | 값 | 설명 |
|------|-----|------|
| `GPU_AVAILABLE` | `true`/`false` | GPU 감지 여부 |
| `GPU_COUNT` | 숫자 | 사용 가능한 GPU 수 |
| `GPU_NAME` | 문자열 | GPU 모델명 |
| `CUDA_VISIBLE_DEVICES` | (빈 문자열) | `USE_GPU=false`인 경우 설정 |

## 적용된 서비스

| 서비스 | 상태 |
|--------|------|
| `yolo-api` | ✅ 적용됨 |
| `edocr2-v2-api` | ⏳ 미적용 |
| `paddleocr-api` | ⏳ 미적용 (기존 USE_GPU 사용) |
| `trocr-api` | ⏳ 미적용 |
| `esrgan-api` | ⏳ 미적용 |

## 시작 로그 예시

```
🚀 GPU Mode: Auto-detected (1x NVIDIA GeForce RTX 3090)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔧 GPU Detection Summary
   GPU_AVAILABLE: true
   GPU_COUNT: 1
   GPU_NAME: NVIDIA GeForce RTX 3090
   USE_GPU: auto
   CUDA_VISIBLE_DEVICES: all
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## GPU 감지 방법 (우선순위)

1. `nvidia-smi` 명령어 실행
2. `/dev/nvidia*` 디바이스 파일 체크
3. PyTorch `torch.cuda.is_available()` 호출
