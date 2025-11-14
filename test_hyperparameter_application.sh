#!/bin/bash
##
# 하이퍼파라미터 적용 테스트 스크립트
#
# 목적: Settings 페이지에서 변경한 하이퍼파라미터가 실제 API 호출에 적용되는지 검증
#
# 테스트 시나리오:
# 1. 기본값으로 API 호출 (conf=0.25, iou=0.7)
# 2. 변경된 값으로 API 호출 (conf=0.5, iou=0.6) - Settings에서 저장한 값
# 3. 검출 결과 비교 (높은 conf 임계값 → 검출 개수 감소 예상)
##

set -e

echo "======================================"
echo "  하이퍼파라미터 적용 테스트"
echo "======================================"
echo ""

# 테스트 이미지 경로
TEST_IMAGE="/home/uproot/ax/reference/02. 수요처 및 도메인 자료/2. 도면(샘플)/A12-311197-9 Rev.2 Interm Shaft-Acc_y_1.jpg"

if [ ! -f "$TEST_IMAGE" ]; then
    echo "❌ 테스트 이미지를 찾을 수 없습니다: $TEST_IMAGE"
    exit 1
fi

echo "📁 테스트 이미지: $(basename "$TEST_IMAGE")"
echo ""

# 1. 기본 하이퍼파라미터로 API 호출
echo "========================================="
echo "테스트 1: 기본 하이퍼파라미터"
echo "========================================="
echo "Parameters: conf=0.25, iou=0.7 (기본값)"
echo ""

response1=$(curl -s -X POST "http://localhost:5005/api/v1/detect" \
  -F "file=@${TEST_IMAGE}" \
  -F "conf_threshold=0.25" \
  -F "iou_threshold=0.7" \
  -F "imgsz=1280" \
  -F "visualize=false")

detections1=$(echo "$response1" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('total_detections', 0))")
time1=$(echo "$response1" | python3 -c "import sys, json; data=json.load(sys.stdin); print(f\"{data.get('processing_time', 0):.2f}\")")

echo "✅ 검출 개수: $detections1"
echo "⏱️  처리 시간: ${time1}s"
echo ""

# 2. 변경된 하이퍼파라미터로 API 호출 (Settings에서 저장한 값)
echo "========================================="
echo "테스트 2: 변경된 하이퍼파라미터 (Settings)"
echo "========================================="
echo "Parameters: conf=0.5, iou=0.6 (Settings에서 저장)"
echo ""

response2=$(curl -s -X POST "http://localhost:5005/api/v1/detect" \
  -F "file=@${TEST_IMAGE}" \
  -F "conf_threshold=0.5" \
  -F "iou_threshold=0.6" \
  -F "imgsz=1280" \
  -F "visualize=false")

detections2=$(echo "$response2" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('total_detections', 0))")
time2=$(echo "$response2" | python3 -c "import sys, json; data=json.load(sys.stdin); print(f\"{data.get('processing_time', 0):.2f}\")")

echo "✅ 검출 개수: $detections2"
echo "⏱️  처리 시간: ${time2}s"
echo ""

# 3. 더 높은 임계값으로 테스트 (극단적 케이스)
echo "========================================="
echo "테스트 3: 높은 임계값 (극단적)"
echo "========================================="
echo "Parameters: conf=0.8, iou=0.5"
echo ""

response3=$(curl -s -X POST "http://localhost:5005/api/v1/detect" \
  -F "file=@${TEST_IMAGE}" \
  -F "conf_threshold=0.8" \
  -F "iou_threshold=0.5" \
  -F "imgsz=1280" \
  -F "visualize=false")

detections3=$(echo "$response3" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('total_detections', 0))")
time3=$(echo "$response3" | python3 -c "import sys, json; data=json.load(sys.stdin); print(f\"{data.get('processing_time', 0):.2f}\")")

echo "✅ 검출 개수: $detections3"
echo "⏱️  처리 시간: ${time3}s"
echo ""

# 결과 비교
echo "========================================="
echo "📊 결과 비교"
echo "========================================="
echo ""
printf "| %-20s | %-15s | %-15s |\n" "테스트" "검출 개수" "처리 시간"
echo "|----------------------|-----------------|-----------------|"
printf "| %-20s | %-15s | %-15s |\n" "기본값 (0.25/0.7)" "$detections1" "${time1}s"
printf "| %-20s | %-15s | %-15s |\n" "Settings (0.5/0.6)" "$detections2" "${time2}s"
printf "| %-20s | %-15s | %-15s |\n" "높은값 (0.8/0.5)" "$detections3" "${time3}s"
echo ""

# 검증
echo "========================================="
echo "✅ 검증 결과"
echo "========================================="
echo ""

if [ "$detections1" -gt "$detections2" ] && [ "$detections2" -gt "$detections3" ]; then
    echo "✅ PASS: 신뢰도 임계값이 높아질수록 검출 개수가 감소했습니다"
    echo "   - 이는 하이퍼파라미터가 정상적으로 적용되고 있음을 의미합니다"
    echo ""
    echo "   기본값($detections1) > Settings($detections2) > 높은값($detections3)"
elif [ "$detections1" -eq "$detections2" ] && [ "$detections2" -eq "$detections3" ]; then
    echo "❌ FAIL: 모든 테스트에서 동일한 검출 개수가 나왔습니다"
    echo "   - 하이퍼파라미터가 적용되지 않고 있을 수 있습니다"
    echo "   - 또는 테스트 이미지에 검출할 객체가 없을 수 있습니다"
else
    echo "⚠️  WARNING: 예상과 다른 패턴이 나타났습니다"
    echo "   - conf 임계값: 0.25 < 0.5 < 0.8"
    echo "   - 검출 개수: $detections1, $detections2, $detections3"
    echo "   - 일반적으로 임계값이 높아질수록 검출 개수가 감소해야 합니다"
fi

echo ""
echo "======================================"
echo "  테스트 완료"
echo "======================================"
