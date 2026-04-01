#!/usr/bin/env python3
"""뷰 감지 캡쳐 생성 — ASSY 도면 4개 뷰 바운딩 박스 + 메인 뷰 표시

생성물:
1. 전체 도면 + 4개 뷰 bbox (빨강=상단보조, 초록=정면(메인), 파랑=SECTION, 노랑=ISO)
2. 메인 뷰(정면도) 크롭 확대
3. SECTION E-3 크롭 확대
"""

import io
import os
import re
import sys
import time
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
from services.dimension_ensemble import _auto_detect_section, _detect_drawing_views

import requests

PADDLE_URL = "http://localhost:5006/api/v1/ocr"
PDF_BASE = Path("/home/uproot/ax/poc/apply-company/dsebearing/PJT/04_부품도면")
OUT_DIR = Path("/home/uproot/ax/poc/docs-site-starlight/public/images/gt-validation")

GT = {
    "TD0062015": {"name": "T1", "od": 360, "id": 190, "w": 200,
                  "pdf": "01_저널베어링/TD0062015 Rev.A(T1 BEARING ASSY(360X190)).pdf"},
    "TD0062021": {"name": "T2", "od": 380, "id": 190, "w": 200,
                  "pdf": "01_저널베어링/TD0062021 Rev.A(T2 BEARING ASSY(380X190)).pdf"},
    "TD0062026": {"name": "T3", "od": 380, "id": 260, "w": 260,
                  "pdf": "01_저널베어링/TD0062026 Rev.A(T3 BEARING ASSY(380X260)).pdf"},
    "TD0062031": {"name": "T4", "od": 420, "id": 260, "w": 260,
                  "pdf": "01_저널베어링/TD0062031 Rev.B(T4 BEARING ASSY (420x260)).pdf"},
    "TD0062037": {"name": "T5", "od": 1036, "id": 580, "w": 200,
                  "pdf": "01_저널베어링/TD0062037 Rev.A(T5 BEARING ASSY (1036X580)).pdf"},
    "TD0062050": {"name": "T8", "od": 500, "id": 260, "w": 200,
                  "pdf": "01_저널베어링/TD0062050 Rev.B(T8 BEARING ASSY 500x260).pdf"},
    "TD0060710": {"name": "Thrust", "od": 515, "id": 440, "w": 48,
                  "pdf": "02_스러스트베어링/TD0060710 Rev.B(THRUST BEARING ASSY(515X440)).pdf"},
}

VIEW_COLORS = {
    "auxiliary_view": ("#E53935", "Auxiliary (보조도)"),   # 빨강
    "main_view":      ("#43A047", "Main View (정면도)"),   # 초록
    "section_view":   ("#1E88E5", "SECTION E-3"),          # 파랑
    "iso_view":       ("#FDD835", "ISO VIEW"),             # 노랑
}


def get_font(size=16):
    for path in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def pdf_to_image(pdf_path, dpi=150):
    import fitz
    doc = fitz.open(str(pdf_path))
    page = doc[0]
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat)
    png = pix.tobytes("png")
    doc.close()
    return Image.open(io.BytesIO(png))


def paddle_ocr(png_bytes, timeout=120):
    try:
        resp = requests.post(PADDLE_URL,
            files={"file": ("img.jpg", png_bytes, "image/jpeg")},
            timeout=timeout)
        resp.raise_for_status()
        return resp.json().get("detections", [])
    except Exception as e:
        print(f"  ⚠ OCR failed: {e}")
        return []


def img_to_bytes(img, fmt="JPEG"):
    buf = io.BytesIO()
    if fmt == "JPEG":
        img = img.convert("RGB")
    img.save(buf, format=fmt, quality=90)
    return buf.getvalue()


def capture_views(img, name, gt, out_path, image_path):
    """전체 도면 + 4개 뷰 bbox + 메인 뷰 라벨"""
    sec_region = _auto_detect_section(image_path, paddle_ocr, img_to_bytes)
    if not sec_region:
        print(f"  ⚠ SECTION auto-detect failed for {name}")
        return None

    w, h = img.size
    views = _detect_drawing_views(sec_region.get("ocr_dets", []), w, h)
    print(f"  Views detected: {list(views.keys())}")

    canvas = img.copy().convert("RGB")
    draw = ImageDraw.Draw(canvas)
    font = get_font(max(16, h // 60))
    font_sm = get_font(max(12, h // 80))

    # 각 뷰 bbox 그리기
    for view_key, region in views.items():
        color, label = VIEW_COLORS.get(view_key, ("#999", view_key))
        x1 = int(region["left"] * w)
        y1 = int(region["top"] * h)
        x2 = int(region["right"] * w)
        y2 = int(region["bottom"] * h)

        # 3px 두께 박스
        for i in range(3):
            draw.rectangle([x1 - i, y1 - i, x2 + i, y2 + i], outline=color)

        # 라벨 배경 + 텍스트
        tw = font.getlength(label) if hasattr(font, 'getlength') else len(label) * 10
        draw.rectangle([x1, y1 - 25, x1 + tw + 10, y1], fill=color)
        draw.text((x1 + 5, y1 - 23), label, fill="white", font=font_sm)

        # 메인 뷰 강조 (굵은 테두리 + 별표)
        if view_key == "main_view":
            for i in range(3, 6):
                draw.rectangle([x1 - i, y1 - i, x2 + i, y2 + i], outline=color)
            draw.text((x1 + 5, y2 - 25), "★ MAIN VIEW", fill=color, font=font)

    # GT 정보 라벨
    gt_text = f"{name}  GT: OD={gt['od']}  ID={gt['id']}  W={gt['w']}"
    draw.rectangle([10, 5, 10 + font.getlength(gt_text) + 20, 35], fill="#000000")
    draw.text((20, 8), gt_text, fill="white", font=font)

    # 축소
    max_w = 1400
    if canvas.width > max_w:
        ratio = max_w / canvas.width
        canvas = canvas.resize((max_w, int(canvas.height * ratio)), Image.LANCZOS)

    canvas.save(out_path, quality=85)
    print(f"  ✓ Views: {out_path.name}")
    return views


def capture_main_view_crop(img, views, name, gt, out_path):
    """메인 뷰(정면도) 크롭 확대"""
    front = views.get("main_view")
    if not front:
        print(f"  ⚠ No front_view for {name}")
        return

    w, h = img.size
    x1 = int(front["left"] * w)
    y1 = int(front["top"] * h)
    x2 = int(front["right"] * w)
    y2 = int(front["bottom"] * h)
    cropped = img.crop((x1, y1, x2, y2))

    canvas = cropped.copy().convert("RGB")
    draw = ImageDraw.Draw(canvas)
    cw, ch = canvas.size
    font = get_font(max(14, ch // 40))

    # 라벨
    label = f"{name} — FRONT VIEW (Main)  |  GT: OD={gt['od']} ID={gt['id']}"
    draw.rectangle([0, 0, cw, 30], fill="#43A047")
    draw.text((10, 5), label, fill="white", font=font)

    # 축소
    max_w = 800
    if canvas.width > max_w:
        ratio = max_w / canvas.width
        canvas = canvas.resize((max_w, int(canvas.height * ratio)), Image.LANCZOS)

    canvas.save(out_path, quality=85)
    print(f"  ✓ Main view crop: {out_path.name}")


def capture_section_crop(img, views, name, gt, out_path):
    """SECTION E-3 크롭 확대"""
    section = views.get("section_view")
    if not section:
        print(f"  ⚠ No section_view for {name}")
        return

    w, h = img.size
    x1 = int(section["left"] * w)
    y1 = int(section["top"] * h)
    x2 = int(section["right"] * w)
    y2 = int(section["bottom"] * h)
    cropped = img.crop((x1, y1, x2, y2))

    canvas = cropped.copy().convert("RGB")
    draw = ImageDraw.Draw(canvas)
    cw, ch = canvas.size
    font = get_font(max(14, ch // 40))

    label = f"{name} — SECTION E-3  |  GT: OD={gt['od']} ID={gt['id']} W={gt['w']}"
    draw.rectangle([0, 0, cw, 30], fill="#1E88E5")
    draw.text((10, 5), label, fill="white", font=font)

    max_w = 600
    if canvas.width > max_w:
        ratio = max_w / canvas.width
        canvas = canvas.resize((max_w, int(canvas.height * ratio)), Image.LANCZOS)

    canvas.save(out_path, quality=85)
    print(f"  ✓ Section crop: {out_path.name}")


def run():
    print("뷰 감지 캡쳐 생성")
    print("=" * 60)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for drawing_no, gt in GT.items():
        pdf_path = PDF_BASE / gt["pdf"]
        if not pdf_path.exists():
            print(f"⚠ {gt['name']} ({drawing_no}): PDF 없음 — {pdf_path}")
            continue

        name = gt["name"].lower()
        print(f"\n{gt['name']} ({drawing_no})")

        img = pdf_to_image(pdf_path, dpi=150)

        # 임시 이미지 (auto-detect에 경로 필요)
        tmp_path = str(OUT_DIR / f"_tmp_{name}.jpg")
        img.convert("RGB").save(tmp_path, quality=90)

        try:
            # 1. 전체 도면 + 4개 뷰 bbox
            views = capture_views(
                img, gt["name"], gt,
                OUT_DIR / f"{name}_views_v8.jpg",
                image_path=tmp_path,
            )

            if views:
                # 2. 메인 뷰 크롭
                capture_main_view_crop(
                    img, views, gt["name"], gt,
                    OUT_DIR / f"{name}_main_view.jpg",
                )
                # 3. SECTION 크롭
                capture_section_crop(
                    img, views, gt["name"], gt,
                    OUT_DIR / f"{name}_section_crop.jpg",
                )
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

        time.sleep(1)  # OCR rate limit

    print(f"\n완료: {OUT_DIR}")
    for f in sorted(OUT_DIR.glob("*_v8*")) + sorted(OUT_DIR.glob("*_main_*")) + sorted(OUT_DIR.glob("*_section_crop*")):
        print(f"  {f.name} ({f.stat().st_size // 1024}KB)")


if __name__ == "__main__":
    run()
