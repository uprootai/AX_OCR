#!/bin/bash

# Test API response structure
echo "Testing Gateway API response..."

# Use the sample image
SAMPLE_PATH="/home/uproot/ax/poc/datasets/combined/images/test/synthetic_random_synthetic_test_000001.jpg"

# Call the API
curl -X POST "http://localhost:8000/api/v1/process" \
  -F "file=@${SAMPLE_PATH}" \
  -F "pipeline_mode=speed" \
  -F "use_ocr=true" \
  -F "use_segmentation=true" \
  -F "use_tolerance=true" \
  -F "visualize=true" \
  -F "yolo_visualize=true" \
  2>/dev/null | jq '{
    status: .status,
    has_data: (.data != null),
    has_yolo: (.data.yolo_results != null),
    yolo_keys: (.data.yolo_results | keys),
    has_viz: (.data.yolo_results.visualized_image != null),
    viz_length: (.data.yolo_results.visualized_image | length)
  }'
