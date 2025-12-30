#!/usr/bin/env python3
"""BWMS P&ID 샘플 이미지 생성 스크립트

TECHCROSS 워크플로우 테스트용 합성 P&ID 이미지를 생성합니다.

포함 요소:
- SIGNAL FOR BWMS 점선 박스 영역 (밸브 시그널 리스트)
- 장비 심볼 및 태그 (ECU, FMU, ANU 등)
- 배관 라인 (실선/점선)
- 밸브 심볼 (XV, SV, CV 등)
- 타이틀 블록
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, Circle, Rectangle, FancyArrowPatch
import numpy as np
from pathlib import Path


def draw_valve_symbol(ax, x, y, valve_id, valve_type="XV", size=0.8):
    """밸브 심볼 그리기 (이중 삼각형)"""
    # 밸브 심볼 (보타이 모양)
    triangle1 = plt.Polygon(
        [(x - size/2, y), (x, y + size/3), (x, y - size/3)],
        fill=False, edgecolor='black', linewidth=1.5
    )
    triangle2 = plt.Polygon(
        [(x + size/2, y), (x, y + size/3), (x, y - size/3)],
        fill=False, edgecolor='black', linewidth=1.5
    )
    ax.add_patch(triangle1)
    ax.add_patch(triangle2)

    # 밸브 ID 레이블
    ax.text(x, y - size/2 - 0.3, valve_id, ha='center', va='top',
            fontsize=9, fontweight='bold', fontfamily='monospace')


def draw_equipment_box(ax, x, y, width, height, tag, eq_type="ECU"):
    """장비 박스 그리기"""
    rect = FancyBboxPatch(
        (x - width/2, y - height/2), width, height,
        boxstyle="round,pad=0.05,rounding_size=0.1",
        fill=True, facecolor='lightblue', edgecolor='black', linewidth=2
    )
    ax.add_patch(rect)

    # 장비 타입
    ax.text(x, y + 0.2, eq_type, ha='center', va='center',
            fontsize=11, fontweight='bold')
    # 태그
    ax.text(x, y - 0.3, tag, ha='center', va='center',
            fontsize=8, fontfamily='monospace')


def draw_signal_box(ax, x, y, width, height, title, valve_ids):
    """SIGNAL FOR BWMS 점선 박스 그리기"""
    # 점선 박스
    rect = Rectangle(
        (x, y), width, height,
        fill=False, edgecolor='black', linewidth=2,
        linestyle='--'
    )
    ax.add_patch(rect)

    # 타이틀 (OCR-friendly: 큰 폰트, 명확한 간격)
    ax.text(x + width/2, y + height + 0.5, title,
            ha='center', va='bottom', fontsize=16, fontweight='bold',
            fontfamily='sans-serif',
            bbox=dict(boxstyle='square,pad=0.3', facecolor='yellow', edgecolor='black', linewidth=2))

    # 밸브 ID 리스트 (OCR-friendly: 큰 폰트, 명확한 간격)
    for i, vid in enumerate(valve_ids):
        row = i // 3
        col = i % 3
        vx = x + 2.0 + col * 4  # 더 넓은 간격
        vy = y + height - 2.0 - row * 1.8  # 더 넓은 줄 간격
        ax.text(vx, vy, vid, ha='center', va='center',
                fontsize=12, fontweight='bold', fontfamily='monospace',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='black', linewidth=1.5))


def draw_pump_symbol(ax, x, y, tag, size=1.0):
    """펌프 심볼 그리기"""
    circle = Circle((x, y), size/2, fill=False, edgecolor='black', linewidth=2)
    ax.add_patch(circle)

    # 삼각형 (유체 방향)
    triangle = plt.Polygon(
        [(x + size/2, y), (x + size, y + size/3), (x + size, y - size/3)],
        fill=True, facecolor='black'
    )
    ax.add_patch(triangle)

    # 태그
    ax.text(x, y - size/2 - 0.4, tag, ha='center', va='top',
            fontsize=9, fontweight='bold', fontfamily='monospace')


def draw_tank_symbol(ax, x, y, tag, width=2, height=3):
    """탱크 심볼 그리기"""
    # 탱크 본체
    rect = Rectangle((x - width/2, y - height/2), width, height,
                     fill=True, facecolor='lightgray', edgecolor='black', linewidth=2)
    ax.add_patch(rect)

    # 탱크 상단 (반원)
    theta = np.linspace(0, np.pi, 50)
    arc_x = x + (width/2) * np.cos(theta)
    arc_y = y + height/2 + (width/4) * np.sin(theta)
    ax.plot(arc_x, arc_y, 'k-', linewidth=2)

    # 태그
    ax.text(x, y, tag, ha='center', va='center',
            fontsize=10, fontweight='bold')


def draw_pipe_line(ax, points, style='solid', color='black'):
    """파이프 라인 그리기"""
    x_coords = [p[0] for p in points]
    y_coords = [p[1] for p in points]

    linestyle = '-' if style == 'solid' else '--'
    ax.plot(x_coords, y_coords, linestyle, color=color, linewidth=2)


def create_bwms_pid():
    """BWMS P&ID 생성"""
    # 이미지 크기 최적화: 1600x1200 픽셀 목표 (OCR 친화적)
    fig, ax = plt.subplots(1, 1, figsize=(16, 12))
    ax.set_xlim(0, 48)
    ax.set_ylim(0, 36)
    ax.set_aspect('equal')
    ax.axis('off')

    # ========== 타이틀 블록 ==========
    title_rect = Rectangle((0.5, 0.5), 47, 4, fill=True,
                           facecolor='white', edgecolor='black', linewidth=2)
    ax.add_patch(title_rect)

    ax.text(24, 3.5, "BWMS SYSTEM P&ID", ha='center', va='center',
            fontsize=20, fontweight='bold')
    ax.text(24, 2, "BALLAST WATER MANAGEMENT SYSTEM - ECS TYPE",
            ha='center', va='center', fontsize=14)
    ax.text(24, 1, "TECHCROSS CO., LTD.  |  DWG NO: TC-BWMS-001  |  REV: A",
            ha='center', va='center', fontsize=10, fontfamily='monospace')

    # ========== SIGNAL FOR BWMS 영역 1 (좌측) ==========
    signal_box1_valves = [
        "XV-101", "XV-102", "XV-103",
        "SV-201", "SV-202", "SV-203",
        "CV-301", "CV-302", "BV-401"
    ]
    draw_signal_box(ax, 1, 20, 14, 10, "SIGNAL FOR BWMS (REQUIRED)", signal_box1_valves)

    # ========== SIGNAL FOR BWMS 영역 2 (우측) ==========
    signal_box2_valves = [
        "XV-501", "XV-502", "NV-601",
        "RV-701", "TV-801", "SV-901"
    ]
    draw_signal_box(ax, 33, 20, 14, 10, "SIGNAL FOR BWMS (ALARM BY-PASS)", signal_box2_valves)

    # ========== 장비 영역 ==========
    # ECU (Electrolysis Cell Unit)
    draw_equipment_box(ax, 10, 14, 4, 2.5, "ECU-001", "ECU")
    draw_equipment_box(ax, 10, 10, 4, 2.5, "ECU-002", "ECU")

    # FMU (Filter Module Unit)
    draw_equipment_box(ax, 20, 14, 4, 2.5, "FMU-001", "FMU")

    # ANU (Analyzer Unit)
    draw_equipment_box(ax, 30, 14, 4, 2.5, "ANU-001", "ANU")

    # TSU (TRO Sensor Unit)
    draw_equipment_box(ax, 40, 14, 4, 2.5, "TSU-001", "TSU")

    # ========== 펌프 ==========
    draw_pump_symbol(ax, 6, 7, "P-101", 1.2)
    draw_pump_symbol(ax, 15, 7, "P-102", 1.2)

    # ========== 탱크 ==========
    draw_tank_symbol(ax, 25, 7, "T-101", 3, 4)
    draw_tank_symbol(ax, 38, 7, "T-102", 3, 4)

    # ========== 밸브 심볼 ==========
    # 메인 라인 밸브들
    draw_valve_symbol(ax, 8, 14, "XV-101", size=0.8)
    draw_valve_symbol(ax, 14, 14, "XV-102", size=0.8)
    draw_valve_symbol(ax, 24, 14, "SV-201", size=0.8)
    draw_valve_symbol(ax, 34, 14, "CV-301", size=0.8)

    # 바이패스 라인 밸브들
    draw_valve_symbol(ax, 8, 10, "XV-103", size=0.8)
    draw_valve_symbol(ax, 14, 10, "SV-202", size=0.8)

    # ========== 파이프 라인 ==========
    # 메인 라인 (실선)
    draw_pipe_line(ax, [(2, 14), (8, 14)], 'solid')
    draw_pipe_line(ax, [(8, 14), (14, 14)], 'solid')
    draw_pipe_line(ax, [(14, 14), (20, 14)], 'solid')
    draw_pipe_line(ax, [(20, 14), (24, 14)], 'solid')
    draw_pipe_line(ax, [(24, 14), (30, 14)], 'solid')
    draw_pipe_line(ax, [(30, 14), (34, 14)], 'solid')
    draw_pipe_line(ax, [(34, 14), (40, 14)], 'solid')
    draw_pipe_line(ax, [(40, 14), (46, 14)], 'solid')

    # 바이패스 라인 (점선)
    draw_pipe_line(ax, [(8, 14), (8, 10)], 'dashed')
    draw_pipe_line(ax, [(8, 10), (14, 10)], 'dashed')
    draw_pipe_line(ax, [(14, 10), (14, 14)], 'dashed')

    # 펌프 연결
    draw_pipe_line(ax, [(6, 7), (6, 10), (8, 10)], 'solid')
    draw_pipe_line(ax, [(15, 7), (15, 10), (14, 10)], 'solid')

    # 탱크 연결
    draw_pipe_line(ax, [(25, 9), (25, 12), (20, 12), (20, 14)], 'solid')
    draw_pipe_line(ax, [(38, 9), (38, 12), (40, 12), (40, 14)], 'solid')

    # ========== 테두리 ==========
    border = Rectangle((0.2, 0.2), 47.6, 35.6, fill=False,
                       edgecolor='black', linewidth=3)
    ax.add_patch(border)

    # ========== 범례 ==========
    legend_y = 32
    ax.text(2, legend_y, "LEGEND:", fontsize=10, fontweight='bold')

    # 밸브 타입 설명
    ax.text(2, legend_y - 1, "XV: Shut-off Valve", fontsize=8)
    ax.text(2, legend_y - 1.8, "SV: Solenoid Valve", fontsize=8)
    ax.text(2, legend_y - 2.6, "CV: Control Valve", fontsize=8)
    ax.text(10, legend_y - 1, "BV: Ball Valve", fontsize=8)
    ax.text(10, legend_y - 1.8, "NV: Needle Valve", fontsize=8)
    ax.text(10, legend_y - 2.6, "RV: Relief Valve", fontsize=8)

    # 장비 설명
    ax.text(20, legend_y - 1, "ECU: Electrolysis Cell Unit", fontsize=8)
    ax.text(20, legend_y - 1.8, "FMU: Filter Module Unit", fontsize=8)
    ax.text(20, legend_y - 2.6, "ANU: Analyzer Unit", fontsize=8)
    ax.text(32, legend_y - 1, "TSU: TRO Sensor Unit", fontsize=8)
    ax.text(32, legend_y - 1.8, "T: Tank", fontsize=8)
    ax.text(32, legend_y - 2.6, "P: Pump", fontsize=8)

    return fig


def main():
    """메인 함수"""
    # 출력 경로
    output_dir = Path("/home/uproot/ax/poc/web-ui/public/samples")
    output_path = output_dir / "bwms_pid_techcross_sample.png"

    print("BWMS P&ID 샘플 이미지 생성 중...")

    # P&ID 생성
    fig = create_bwms_pid()

    # 저장 (OCR-friendly: 적절한 크기, ~1600x1200 픽셀)
    fig.savefig(output_path, dpi=100, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close(fig)

    print(f"✅ 이미지 저장 완료: {output_path}")

    # 이미지 정보
    from PIL import Image
    img = Image.open(output_path)
    print(f"   크기: {img.size[0]} x {img.size[1]} pixels")
    print(f"   파일 크기: {output_path.stat().st_size / 1024:.1f} KB")

    return output_path


if __name__ == "__main__":
    main()
