import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import numpy as np

st.title("Canvas Background Image Test")

# 테스트용 이미지 생성
width, height = 600, 400
# 체커보드 패턴 생성
img_array = np.zeros((height, width, 3), dtype=np.uint8)
for i in range(0, height, 50):
    for j in range(0, width, 50):
        if (i//50 + j//50) % 2 == 0:
            img_array[i:i+50, j:j+50] = [200, 200, 200]
        else:
            img_array[i:i+50, j:j+50] = [100, 100, 100]

# 빨간 박스 그리기 (참조용)
img_array[50:150, 50:200] = [255, 0, 0]
img_array[200:300, 300:450] = [0, 255, 0]

st.write("### 원본 이미지 (체커보드 + 색상 박스)")
st.image(img_array, use_column_width=False, width=width)

# PIL Image로 변환
pil_img = Image.fromarray(img_array, mode='RGB')

st.write("### 방법 1: PIL Image를 background_image로")
try:
    canvas1 = st_canvas(
        fill_color="rgba(255, 255, 0, 0.3)",
        stroke_width=3,
        stroke_color="#0000FF",
        background_image=pil_img,
        update_streamlit=True,
        height=height,
        width=width,
        drawing_mode="rect",
        key="canvas1",
    )
    st.success("PIL Image 방식 성공!")
except Exception as e:
    st.error(f"PIL Image 방식 실패: {e}")

st.write("### 방법 2: Numpy Array를 background_image로")
try:
    canvas2 = st_canvas(
        fill_color="rgba(255, 255, 0, 0.3)",
        stroke_width=3,
        stroke_color="#0000FF",
        background_image=img_array,
        update_streamlit=True,
        height=height,
        width=width,
        drawing_mode="rect",
        key="canvas2",
    )
    st.success("Numpy Array 방식 성공!")
except Exception as e:
    st.error(f"Numpy Array 방식 실패: {e}")

st.write("### 방법 3: 배경 없이")
canvas3 = st_canvas(
    fill_color="rgba(255, 255, 0, 0.3)",
    stroke_width=3,
    stroke_color="#0000FF",
    background_color="#FFFFFF",
    update_streamlit=True,
    height=height,
    width=width,
    drawing_mode="rect",
    key="canvas3",
)