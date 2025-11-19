import requests
import json

# Test API response
print("🧪 Testing Gateway API response structure...")

sample_path = "/home/uproot/ax/poc/datasets/combined/images/test/synthetic_random_synthetic_test_000001.jpg"

with open(sample_path, 'rb') as f:
    files = {'file': f}
    data = {
        'pipeline_mode': 'speed',
        'use_ocr': 'true',
        'use_segmentation': 'true',
        'use_tolerance': 'true',
        'visualize': 'true',
        'yolo_visualize': 'true'
    }

    print("📡 Calling API...")
    response = requests.post('http://localhost:8000/api/v1/process', files=files, data=data)

    print(f"✅ Status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()

        print(f"\n📊 Response Structure:")
        print(f"  - status: {result.get('status')}")
        print(f"  - has data: {result.get('data') is not None}")
        print(f"  - has yolo_results: {'yolo_results' in result.get('data', {})}")

        if 'yolo_results' in result.get('data', {}):
            yolo = result['data']['yolo_results']
            print(f"\n🎯 YOLO Results:")
            print(f"  - keys: {list(yolo.keys())}")
            print(f"  - has visualized_image: {'visualized_image' in yolo}")
            if 'visualized_image' in yolo:
                viz = yolo['visualized_image']
                print(f"  - visualized_image type: {type(viz)}")
                print(f"  - visualized_image length: {len(viz) if viz else 0}")
                print(f"  - first 50 chars: {viz[:50] if viz else 'None'}")
        else:
            print(f"\n❌ No yolo_results in response!")
            print(f"Available keys: {list(result.get('data', {}).keys())}")
    else:
        print(f"❌ Error: {response.text[:500]}")
