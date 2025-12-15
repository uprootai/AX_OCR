#!/usr/bin/env python3
"""
streamlit-drawable-canvas 버전별 배경 이미지 테스트
"""

import subprocess
import time

versions = ["0.9.3", "0.9.2", "0.9.0", "0.8.0"]

test_code = '''
import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import numpy as np

st.title(f"Canvas Version Test")

# 테스트용 이미지 생성
width, height = 600, 400
img_array = np.zeros((height, width, 3), dtype=np.uint8)

# 체커보드 패턴
for i in range(0, height, 50):
    for j in range(0, width, 50):
        if (i//50 + j//50) % 2 == 0:
            img_array[i:i+50, j:j+50] = [200, 200, 200]
        else:
            img_array[i:i+50, j:j+50] = [100, 100, 100]

# 참조용 색상 박스
img_array[50:150, 50:200] = [255, 0, 0]  # 빨간색
img_array[200:300, 300:450] = [0, 255, 0]  # 초록색

# PIL Image로 변환
pil_img = Image.fromarray(img_array, mode="RGB")

st.write(f"### streamlit-drawable-canvas 버전: {st_canvas.__version__ if hasattr(st_canvas, "__version__") else "Unknown"}")

col1, col2 = st.columns(2)

with col1:
    st.write("원본 이미지")
    st.image(img_array, width=300)

with col2:
    st.write("Canvas with Background")
    try:
        # PIL Image를 배경으로 사용
        canvas_result = st_canvas(
            fill_color="rgba(255, 255, 0, 0.3)",
            stroke_width=3,
            stroke_color="#0000FF",
            background_image=pil_img,
            update_streamlit=True,
            height=200,
            width=300,
            drawing_mode="rect",
            key="test_canvas",
        )
        st.success("✅ PIL Image 배경 성공!")
    except Exception as e:
        st.error(f"❌ 오류: {e}")

        # numpy array 시도
        try:
            canvas_result = st_canvas(
                fill_color="rgba(255, 255, 0, 0.3)",
                stroke_width=3,
                stroke_color="#0000FF",
                background_image=img_array,
                update_streamlit=True,
                height=200,
                width=300,
                drawing_mode="rect",
                key="test_canvas_numpy",
            )
            st.warning("⚠️ Numpy array로 대체 성공")
        except Exception as e2:
            st.error(f"❌ Numpy array도 실패: {e2}")
'''

for version in versions:
    print(f"\n=== Testing version {version} ===")

    # 버전 설치
    print(f"Installing streamlit-drawable-canvas=={version}...")
    subprocess.run(["pip", "install", f"streamlit-drawable-canvas=={version}", "--quiet"], check=True)

    # 테스트 파일 생성
    with open("version_test.py", "w") as f:
        f.write(test_code)

    print(f"Test at http://localhost:850{versions.index(version)+4}/")
    print("Check if background image is visible in the canvas")

    # 각 버전을 다른 포트로 실행
    port = 8504 + versions.index(version)
    subprocess.Popen(["streamlit", "run", "version_test.py", "--server.port", str(port)])

    time.sleep(3)

print("\n=== All versions are running ===")
print("Check each URL to see which version supports background images properly:")
for i, version in enumerate(versions):
    print(f"  Version {version}: http://localhost:{8504+i}/")