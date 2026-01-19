#!/usr/bin/env python3
"""
BlueprintFlow Template API Test
Tests each template workflow directly via gateway API
"""

import requests
import base64
import json
import time
import sys
from pathlib import Path

GATEWAY_URL = "http://localhost:8000"
SAMPLE_IMAGE = "/home/uproot/ax/poc/web-ui/public/samples/sample3_s60me_shaft.jpg"

# Templates to test
TEMPLATES = [
    {
        "name": "Speed Pipeline",
        "workflow": {
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
            ]
        }
    },
    {
        "name": "Basic OCR Pipeline",
        "workflow": {
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
            ]
        }
    },
    {
        "name": "P&ID Analysis Pipeline",
        "workflow": {
            "name": "P&ID Analysis Pipeline",
            "nodes": [
                {"id": "imageinput_1", "type": "imageinput", "label": "P&ID Input", "parameters": {}},
                {"id": "yolo_1", "type": "yolo", "label": "YOLO P&ID", "parameters": {"model_type": "pid_class_aware", "confidence": 0.25, "use_sahi": True}},
                {"id": "linedetector_1", "type": "linedetector", "label": "Line Detector", "parameters": {"method": "lsd"}},
                {"id": "pidanalyzer_1", "type": "pidanalyzer", "label": "PID Analyzer", "parameters": {"generate_bom": True}},
                {"id": "designchecker_1", "type": "designchecker", "label": "Design Checker", "parameters": {"severity_threshold": "warning"}}
            ],
            "edges": [
                {"id": "e1", "source": "imageinput_1", "target": "yolo_1"},
                {"id": "e2", "source": "imageinput_1", "target": "linedetector_1"},
                {"id": "e3", "source": "yolo_1", "target": "pidanalyzer_1"},
                {"id": "e4", "source": "linedetector_1", "target": "pidanalyzer_1"},
                {"id": "e5", "source": "pidanalyzer_1", "target": "designchecker_1"}
            ]
        }
    },
    {
        "name": "Accuracy Pipeline",
        "workflow": {
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
            ]
        }
    },
    {
        "name": "VL-Assisted Analysis",
        "workflow": {
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
            ]
        }
    },
    {
        "name": "OCR Ensemble Pipeline",
        "workflow": {
            "name": "OCR Ensemble Pipeline",
            "nodes": [
                {"id": "imageinput_1", "type": "imageinput", "label": "Image Input", "parameters": {}},
                {"id": "esrgan_1", "type": "esrgan", "label": "ESRGAN", "parameters": {"scale": 2}},
                {"id": "yolo_1", "type": "yolo", "label": "YOLO", "parameters": {"confidence": 0.3}},
                {"id": "ocr_ensemble_1", "type": "ocr_ensemble", "label": "OCR Ensemble", "parameters": {}},
                {"id": "edocr2_1", "type": "edocr2", "label": "Dimension OCR", "parameters": {}},
                {"id": "skinmodel_1", "type": "skinmodel", "label": "Tolerance", "parameters": {}}
            ],
            "edges": [
                {"id": "e1", "source": "imageinput_1", "target": "esrgan_1"},
                {"id": "e2", "source": "esrgan_1", "target": "yolo_1"},
                {"id": "e3", "source": "yolo_1", "target": "ocr_ensemble_1"},
                {"id": "e4", "source": "yolo_1", "target": "edocr2_1"},
                {"id": "e5", "source": "edocr2_1", "target": "skinmodel_1"}
            ]
        }
    },
    {
        "name": "Multi-OCR Comparison",
        "workflow": {
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
            ]
        }
    },
    {
        "name": "Knowledge-Enhanced Analysis",
        "workflow": {
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
            ]
        }
    },
    {
        "name": "Complete Drawing Analysis",
        "workflow": {
            "name": "Complete Drawing Analysis",
            "nodes": [
                {"id": "imageinput_1", "type": "imageinput", "label": "Drawing Input", "parameters": {}},
                {"id": "esrgan_1", "type": "esrgan", "label": "Image Enhancement", "parameters": {"scale": 2}},
                {"id": "yolo_1", "type": "yolo", "label": "Symbol Detection", "parameters": {"confidence": 0.35}},
                {"id": "edgnet_1", "type": "edgnet", "label": "Segmentation", "parameters": {}},
                {"id": "edocr2_1", "type": "edocr2", "label": "Dimension OCR", "parameters": {}},
                {"id": "ocr_ensemble_1", "type": "ocr_ensemble", "label": "OCR Ensemble", "parameters": {}},
                {"id": "skinmodel_1", "type": "skinmodel", "label": "Tolerance Analysis", "parameters": {}},
                {"id": "vl_1", "type": "vl", "label": "AI Description", "parameters": {"prompt": "Describe this engineering drawing"}},
                {"id": "merge_1", "type": "merge", "label": "Final Results", "parameters": {}}
            ],
            "edges": [
                {"id": "e1", "source": "imageinput_1", "target": "esrgan_1"},
                {"id": "e2", "source": "esrgan_1", "target": "yolo_1"},
                {"id": "e3", "source": "esrgan_1", "target": "edgnet_1"},
                {"id": "e4", "source": "yolo_1", "target": "ocr_ensemble_1"},
                {"id": "e5", "source": "edgnet_1", "target": "edocr2_1"},
                {"id": "e6", "source": "edocr2_1", "target": "skinmodel_1"},
                {"id": "e7", "source": "ocr_ensemble_1", "target": "vl_1"},
                {"id": "e8", "source": "skinmodel_1", "target": "vl_1"},
                {"id": "e9", "source": "vl_1", "target": "merge_1"}
            ]
        }
    }
]

def load_image_base64(image_path: str) -> str:
    """Load image and convert to base64"""
    with open(image_path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')

def test_workflow(name: str, workflow: dict, image_base64: str) -> dict:
    """Test a workflow via API"""
    print(f"\n{'='*50}")
    print(f"Testing: {name}")
    print(f"Nodes: {len(workflow['nodes'])}")
    print(f"{'='*50}")

    # Build proper request with workflow wrapper
    request_body = {
        "workflow": workflow,
        "inputs": {"image": image_base64}
    }

    try:
        start_time = time.time()
        response = requests.post(
            f"{GATEWAY_URL}/api/v1/workflow/execute",
            json=request_body,
            timeout=180
        )
        elapsed = time.time() - start_time

        if response.status_code == 200:
            result = response.json()
            status = result.get("status", "unknown")

            # Get node statuses
            node_statuses = result.get("node_statuses", [])
            success_count = sum(1 for n in node_statuses if n.get("status") == "completed")
            fail_count = sum(1 for n in node_statuses if n.get("status") == "failed")

            if status == "completed" and fail_count == 0:
                print(f"✅ PASSED - {success_count}/{len(workflow['nodes'])} nodes completed ({elapsed:.1f}s)")
                return {"status": "passed", "time": elapsed, "nodes": success_count}
            else:
                print(f"⚠️ PARTIAL - {success_count} success, {fail_count} failed ({elapsed:.1f}s)")
                # Print failed nodes
                for n in node_statuses:
                    if n.get("status") == "failed":
                        error_msg = n.get('error') or 'Unknown error'
                        print(f"   ❌ {n.get('node_id')}: {str(error_msg)[:80]}")
                return {"status": "partial", "time": elapsed, "success": success_count, "fail": fail_count}
        else:
            print(f"❌ FAILED - HTTP {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return {"status": "failed", "error": response.text[:200]}

    except requests.exceptions.Timeout:
        print(f"⏱️ TIMEOUT - Request timed out after 180s")
        return {"status": "timeout"}
    except Exception as e:
        print(f"❌ ERROR - {str(e)[:200]}")
        return {"status": "error", "error": str(e)[:200]}

def main():
    print("=" * 60)
    print("BlueprintFlow Template API Test")
    print("=" * 60)

    # Check image exists
    if not Path(SAMPLE_IMAGE).exists():
        print(f"❌ Sample image not found: {SAMPLE_IMAGE}")
        sys.exit(1)

    print(f"\nLoading image: {SAMPLE_IMAGE}")
    image_base64 = load_image_base64(SAMPLE_IMAGE)
    print(f"Image size: {len(image_base64)} chars (base64)")

    # Run tests
    results = []
    for i, template in enumerate(TEMPLATES, 1):
        print(f"\n[{i}/{len(TEMPLATES)}]", end="")
        result = test_workflow(template["name"], template["workflow"], image_base64)
        result["name"] = template["name"]
        results.append(result)

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    passed = sum(1 for r in results if r["status"] == "passed")
    partial = sum(1 for r in results if r["status"] == "partial")
    failed = sum(1 for r in results if r["status"] in ["failed", "error", "timeout"])

    print(f"✅ Passed:  {passed}")
    print(f"⚠️ Partial: {partial}")
    print(f"❌ Failed:  {failed}")
    print(f"Total:     {len(results)}")

    print("\nDetails:")
    for r in results:
        status_icon = "✅" if r["status"] == "passed" else "⚠️" if r["status"] == "partial" else "❌"
        print(f"  {status_icon} {r['name']}: {r['status']}")

    sys.exit(0 if failed == 0 else 1)

if __name__ == "__main__":
    main()
