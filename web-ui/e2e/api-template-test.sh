#!/bin/bash

# Template Execution API Test Script
# Tests each template workflow directly via gateway API

GATEWAY_URL="http://localhost:8000"
SAMPLE_IMAGE="/home/uproot/ax/poc/samples/S60ME-C INTERM-SHAFT_대 주조전.jpg"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "========================================"
echo "BlueprintFlow Template API Test"
echo "========================================"
echo ""

# Check if sample image exists
if [ ! -f "$SAMPLE_IMAGE" ]; then
    echo -e "${RED}Sample image not found: $SAMPLE_IMAGE${NC}"
    exit 1
fi

# Convert image to base64
IMAGE_BASE64=$(base64 -w 0 "$SAMPLE_IMAGE")

# Test counter
PASS=0
FAIL=0

# Function to test a workflow
test_workflow() {
    local name="$1"
    local workflow="$2"

    echo -e "${YELLOW}Testing: $name${NC}"

    # Execute workflow via API
    response=$(curl -s -X POST "$GATEWAY_URL/api/v1/workflow/execute" \
        -H "Content-Type: application/json" \
        -d "$workflow" \
        --max-time 120)

    # Check response
    status=$(echo "$response" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('status', 'unknown'))" 2>/dev/null)

    if [ "$status" == "completed" ]; then
        echo -e "  ${GREEN}✓ PASSED${NC} - Status: $status"
        ((PASS++))
    elif [ "$status" == "failed" ]; then
        error=$(echo "$response" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('error', 'Unknown')[:100])" 2>/dev/null)
        echo -e "  ${RED}✗ FAILED${NC} - Error: $error"
        ((FAIL++))
    else
        echo -e "  ${RED}✗ ERROR${NC} - Response: ${response:0:100}"
        ((FAIL++))
    fi
    echo ""
}

# Test 1: Speed Pipeline (simplest)
echo "1. Speed Pipeline (3 nodes)"
test_workflow "Speed Pipeline" '{
    "name": "Speed Pipeline",
    "description": "Test",
    "nodes": [
        {"id": "imageinput_1", "type": "imageinput", "label": "Image Input", "parameters": {}},
        {"id": "yolo_1", "type": "yolo", "label": "YOLO", "parameters": {"confidence": 0.5}},
        {"id": "edocr2_1", "type": "edocr2", "label": "OCR", "parameters": {}}
    ],
    "edges": [
        {"id": "e1", "source": "imageinput_1", "target": "yolo_1"},
        {"id": "e2", "source": "yolo_1", "target": "edocr2_1"}
    ],
    "inputs": {"image": "'"$IMAGE_BASE64"'"}
}'

# Test 2: Basic OCR Pipeline
echo "2. Basic OCR Pipeline (4 nodes)"
test_workflow "Basic OCR Pipeline" '{
    "name": "Basic OCR Pipeline",
    "nodes": [
        {"id": "imageinput_1", "type": "imageinput", "label": "Image Input", "parameters": {}},
        {"id": "yolo_1", "type": "yolo", "label": "YOLO", "parameters": {"confidence": 0.5}},
        {"id": "edocr2_1", "type": "edocr2", "label": "OCR", "parameters": {}},
        {"id": "skinmodel_1", "type": "skinmodel", "label": "Tolerance", "parameters": {}}
    ],
    "edges": [
        {"id": "e1", "source": "imageinput_1", "target": "yolo_1"},
        {"id": "e2", "source": "yolo_1", "target": "edocr2_1"},
        {"id": "e3", "source": "edocr2_1", "target": "skinmodel_1"}
    ],
    "inputs": {"image": "'"$IMAGE_BASE64"'"}
}'

# Test 3: P&ID Analysis Pipeline
echo "3. P&ID Analysis Pipeline (5 nodes)"
test_workflow "P&ID Analysis Pipeline" '{
    "name": "P&ID Analysis Pipeline",
    "nodes": [
        {"id": "imageinput_1", "type": "imageinput", "label": "P&ID Input", "parameters": {}},
        {"id": "yolo_1", "type": "yolo", "label": "YOLO P&ID", "parameters": {"model_type": "pid_class_aware", "confidence": 0.25, "use_sahi": true}},
        {"id": "linedetector_1", "type": "linedetector", "label": "Line Detector", "parameters": {"method": "lsd"}},
        {"id": "pidanalyzer_1", "type": "pidanalyzer", "label": "PID Analyzer", "parameters": {"generate_bom": true}},
        {"id": "designchecker_1", "type": "designchecker", "label": "Design Checker", "parameters": {"severity_threshold": "warning"}}
    ],
    "edges": [
        {"id": "e1", "source": "imageinput_1", "target": "yolo_1"},
        {"id": "e2", "source": "imageinput_1", "target": "linedetector_1"},
        {"id": "e3", "source": "yolo_1", "target": "pidanalyzer_1"},
        {"id": "e4", "source": "linedetector_1", "target": "pidanalyzer_1"},
        {"id": "e5", "source": "pidanalyzer_1", "target": "designchecker_1"}
    ],
    "inputs": {"image": "'"$IMAGE_BASE64"'"}
}'

# Test 4: Accuracy Pipeline
echo "4. Accuracy Pipeline (6 nodes)"
test_workflow "Accuracy Pipeline" '{
    "name": "Accuracy Pipeline",
    "nodes": [
        {"id": "imageinput_1", "type": "imageinput", "label": "Image Input", "parameters": {}},
        {"id": "yolo_1", "type": "yolo", "label": "YOLO", "parameters": {"confidence": 0.35}},
        {"id": "edgnet_1", "type": "edgnet", "label": "Segmentation", "parameters": {}},
        {"id": "edocr2_1", "type": "edocr2", "label": "eDOCr2", "parameters": {}},
        {"id": "paddleocr_1", "type": "paddleocr", "label": "PaddleOCR", "parameters": {}},
        {"id": "merge_1", "type": "merge", "label": "Merge", "parameters": {}}
    ],
    "edges": [
        {"id": "e1", "source": "imageinput_1", "target": "yolo_1"},
        {"id": "e2", "source": "yolo_1", "target": "edgnet_1"},
        {"id": "e3", "source": "edgnet_1", "target": "edocr2_1"},
        {"id": "e4", "source": "edgnet_1", "target": "paddleocr_1"},
        {"id": "e5", "source": "edocr2_1", "target": "merge_1"},
        {"id": "e6", "source": "paddleocr_1", "target": "merge_1"}
    ],
    "inputs": {"image": "'"$IMAGE_BASE64"'"}
}'

# Test 5: VL-Assisted Analysis
echo "5. VL-Assisted Analysis (4 nodes)"
test_workflow "VL-Assisted Analysis" '{
    "name": "VL-Assisted Analysis",
    "nodes": [
        {"id": "imageinput_1", "type": "imageinput", "label": "Drawing Input", "parameters": {}},
        {"id": "textinput_1", "type": "textinput", "label": "Prompt", "parameters": {"text": "Describe this drawing"}},
        {"id": "vl_1", "type": "vl", "label": "VL Model", "parameters": {}},
        {"id": "yolo_1", "type": "yolo", "label": "YOLO", "parameters": {"confidence": 0.4}}
    ],
    "edges": [
        {"id": "e1", "source": "imageinput_1", "target": "vl_1"},
        {"id": "e2", "source": "textinput_1", "target": "vl_1"},
        {"id": "e3", "source": "vl_1", "target": "yolo_1"}
    ],
    "inputs": {"image": "'"$IMAGE_BASE64"'"}
}'

# Test 6: OCR Ensemble Pipeline
echo "6. OCR Ensemble Pipeline (5 nodes)"
test_workflow "OCR Ensemble Pipeline" '{
    "name": "OCR Ensemble Pipeline",
    "nodes": [
        {"id": "imageinput_1", "type": "imageinput", "label": "Image Input", "parameters": {}},
        {"id": "esrgan_1", "type": "esrgan", "label": "ESRGAN", "parameters": {"scale": 2}},
        {"id": "yolo_1", "type": "yolo", "label": "YOLO", "parameters": {"confidence": 0.3}},
        {"id": "ocr_ensemble_1", "type": "ocr_ensemble", "label": "OCR Ensemble", "parameters": {}},
        {"id": "skinmodel_1", "type": "skinmodel", "label": "Tolerance", "parameters": {}}
    ],
    "edges": [
        {"id": "e1", "source": "imageinput_1", "target": "esrgan_1"},
        {"id": "e2", "source": "esrgan_1", "target": "yolo_1"},
        {"id": "e3", "source": "yolo_1", "target": "ocr_ensemble_1"},
        {"id": "e4", "source": "ocr_ensemble_1", "target": "skinmodel_1"}
    ],
    "inputs": {"image": "'"$IMAGE_BASE64"'"}
}'

# Test 7: Multi-OCR Comparison
echo "7. Multi-OCR Comparison (7 nodes)"
test_workflow "Multi-OCR Comparison" '{
    "name": "Multi-OCR Comparison",
    "nodes": [
        {"id": "imageinput_1", "type": "imageinput", "label": "Image Input", "parameters": {}},
        {"id": "yolo_1", "type": "yolo", "label": "YOLO", "parameters": {"confidence": 0.4}},
        {"id": "edocr2_1", "type": "edocr2", "label": "eDOCr2", "parameters": {}},
        {"id": "paddleocr_1", "type": "paddleocr", "label": "PaddleOCR", "parameters": {}},
        {"id": "tesseract_1", "type": "tesseract", "label": "Tesseract", "parameters": {}},
        {"id": "trocr_1", "type": "trocr", "label": "TrOCR", "parameters": {}},
        {"id": "merge_1", "type": "merge", "label": "Merge", "parameters": {}}
    ],
    "edges": [
        {"id": "e1", "source": "imageinput_1", "target": "yolo_1"},
        {"id": "e2", "source": "yolo_1", "target": "edocr2_1"},
        {"id": "e3", "source": "yolo_1", "target": "paddleocr_1"},
        {"id": "e4", "source": "yolo_1", "target": "tesseract_1"},
        {"id": "e5", "source": "yolo_1", "target": "trocr_1"},
        {"id": "e6", "source": "edocr2_1", "target": "merge_1"},
        {"id": "e7", "source": "paddleocr_1", "target": "merge_1"},
        {"id": "e8", "source": "tesseract_1", "target": "merge_1"},
        {"id": "e9", "source": "trocr_1", "target": "merge_1"}
    ],
    "inputs": {"image": "'"$IMAGE_BASE64"'"}
}'

# Test 8: Knowledge-Enhanced Analysis
echo "8. Knowledge-Enhanced Analysis (6 nodes)"
test_workflow "Knowledge-Enhanced Analysis" '{
    "name": "Knowledge-Enhanced Analysis",
    "nodes": [
        {"id": "imageinput_1", "type": "imageinput", "label": "Drawing Input", "parameters": {}},
        {"id": "textinput_1", "type": "textinput", "label": "Query", "parameters": {"text": "GD&T symbols meaning"}},
        {"id": "yolo_1", "type": "yolo", "label": "Symbol Detection", "parameters": {"confidence": 0.4}},
        {"id": "knowledge_1", "type": "knowledge", "label": "Knowledge Query", "parameters": {}},
        {"id": "edocr2_1", "type": "edocr2", "label": "OCR", "parameters": {}},
        {"id": "merge_1", "type": "merge", "label": "Merge", "parameters": {}}
    ],
    "edges": [
        {"id": "e1", "source": "imageinput_1", "target": "yolo_1"},
        {"id": "e2", "source": "textinput_1", "target": "knowledge_1"},
        {"id": "e3", "source": "yolo_1", "target": "edocr2_1"},
        {"id": "e4", "source": "edocr2_1", "target": "merge_1"},
        {"id": "e5", "source": "knowledge_1", "target": "merge_1"}
    ],
    "inputs": {"image": "'"$IMAGE_BASE64"'"}
}'

echo "========================================"
echo "Test Results Summary"
echo "========================================"
echo -e "${GREEN}Passed: $PASS${NC}"
echo -e "${RED}Failed: $FAIL${NC}"
echo "Total: $((PASS + FAIL))"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${YELLOW}Some tests failed. Check the logs above.${NC}"
    exit 1
fi
