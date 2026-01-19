"""
DWG Parsing Service
ODA File Converter + ezdxf 파이프라인으로 DWG 파일 파싱

DWG 파일 → ODA Converter → DXF 파일 → ezdxf → 엔티티 추출
"""

import os
import subprocess
import tempfile
import shutil
import logging
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

logger = logging.getLogger(__name__)

# ODA File Converter 경로 (환경변수 또는 기본 경로)
ODA_CONVERTER_PATH = os.getenv(
    "ODA_CONVERTER_PATH",
    "/usr/local/bin/ODAFileConverter"
)

# 대체 경로들
ODA_CONVERTER_PATHS = [
    ODA_CONVERTER_PATH,
    "/opt/ODAFileConverter/ODAFileConverter",
    "/usr/bin/ODAFileConverter",
    "ODAFileConverter",  # PATH에서 찾기
]


def find_oda_converter() -> Optional[str]:
    """ODA File Converter 실행 파일 찾기"""
    for path in ODA_CONVERTER_PATHS:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path
        # which 명령으로 찾기
        try:
            result = subprocess.run(
                ["which", path.split("/")[-1]],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except Exception:
            pass
    return None


def is_oda_available() -> bool:
    """ODA File Converter 사용 가능 여부 확인"""
    return find_oda_converter() is not None


def convert_dwg_to_dxf(
    dwg_path: str,
    output_dir: Optional[str] = None,
    dxf_version: str = "ACAD2018"
) -> Tuple[bool, str, str]:
    """
    DWG 파일을 DXF로 변환

    Args:
        dwg_path: DWG 파일 경로
        output_dir: 출력 디렉토리 (None이면 임시 디렉토리)
        dxf_version: DXF 버전 (ACAD2018, ACAD2013, ACAD2010 등)

    Returns:
        (success, dxf_path, error_message)
    """
    oda_path = find_oda_converter()
    if not oda_path:
        return False, "", "ODA File Converter not found. Install from https://www.opendesign.com/guestfiles/oda_file_converter"

    if not os.path.exists(dwg_path):
        return False, "", f"DWG file not found: {dwg_path}"

    # 출력 디렉토리 설정
    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="dwg_convert_")
    else:
        os.makedirs(output_dir, exist_ok=True)

    # 입력 디렉토리 (ODA는 디렉토리 단위로 변환)
    input_dir = os.path.dirname(os.path.abspath(dwg_path))
    dwg_filename = os.path.basename(dwg_path)

    # ODA File Converter 실행
    # 형식: ODAFileConverter <input_dir> <output_dir> <output_version> <output_type> <recurse> <audit> [filter]
    # output_type: DXF=1, DWG=0
    try:
        cmd = [
            oda_path,
            input_dir,
            output_dir,
            dxf_version,
            "DXF",  # 출력 형식
            "0",    # recurse: 0=하위 디렉토리 제외
            "1",    # audit: 1=복구 시도
            dwg_filename  # 특정 파일만 변환
        ]

        logger.info(f"Running ODA converter: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120  # 2분 타임아웃
        )

        if result.returncode != 0:
            logger.error(f"ODA converter failed: {result.stderr}")
            return False, "", f"ODA converter error: {result.stderr}"

        # 변환된 DXF 파일 찾기
        dxf_filename = Path(dwg_filename).stem + ".dxf"
        dxf_path = os.path.join(output_dir, dxf_filename)

        if os.path.exists(dxf_path):
            logger.info(f"DWG to DXF conversion successful: {dxf_path}")
            return True, dxf_path, ""
        else:
            # 대소문자 다를 수 있음
            for f in os.listdir(output_dir):
                if f.lower().endswith(".dxf"):
                    dxf_path = os.path.join(output_dir, f)
                    return True, dxf_path, ""

            return False, "", f"DXF file not found in output directory: {output_dir}"

    except subprocess.TimeoutExpired:
        return False, "", "ODA converter timed out (>120s)"
    except Exception as e:
        return False, "", f"ODA converter exception: {str(e)}"


def parse_dxf(dxf_path: str) -> Dict[str, Any]:
    """
    DXF 파일을 파싱하여 엔티티 추출

    Returns:
        {
            "metadata": {...},
            "layers": [...],
            "entities": {
                "lines": [...],
                "polylines": [...],
                "circles": [...],
                "arcs": [...],
                "texts": [...],
                "mtexts": [...],
                "blocks": [...],
                "inserts": [...]
            },
            "statistics": {...}
        }
    """
    try:
        import ezdxf
    except ImportError:
        return {"error": "ezdxf not installed. Run: pip install ezdxf"}

    if not os.path.exists(dxf_path):
        return {"error": f"DXF file not found: {dxf_path}"}

    try:
        doc = ezdxf.readfile(dxf_path)
    except Exception as e:
        return {"error": f"Failed to read DXF file: {str(e)}"}

    result = {
        "metadata": extract_metadata(doc),
        "layers": extract_layers(doc),
        "entities": {
            "lines": [],
            "polylines": [],
            "circles": [],
            "arcs": [],
            "texts": [],
            "mtexts": [],
            "inserts": [],  # 블록 참조
        },
        "blocks": extract_blocks(doc),
        "statistics": {}
    }

    # 모델 스페이스에서 엔티티 추출
    msp = doc.modelspace()

    for entity in msp:
        entity_type = entity.dxftype()

        if entity_type == "LINE":
            result["entities"]["lines"].append(extract_line(entity))
        elif entity_type == "LWPOLYLINE":
            result["entities"]["polylines"].append(extract_lwpolyline(entity))
        elif entity_type == "POLYLINE":
            result["entities"]["polylines"].append(extract_polyline(entity))
        elif entity_type == "CIRCLE":
            result["entities"]["circles"].append(extract_circle(entity))
        elif entity_type == "ARC":
            result["entities"]["arcs"].append(extract_arc(entity))
        elif entity_type == "TEXT":
            result["entities"]["texts"].append(extract_text(entity))
        elif entity_type == "MTEXT":
            result["entities"]["mtexts"].append(extract_mtext(entity))
        elif entity_type == "INSERT":
            result["entities"]["inserts"].append(extract_insert(entity))

    # 통계
    result["statistics"] = {
        "total_entities": sum(len(v) for v in result["entities"].values()),
        "lines": len(result["entities"]["lines"]),
        "polylines": len(result["entities"]["polylines"]),
        "circles": len(result["entities"]["circles"]),
        "arcs": len(result["entities"]["arcs"]),
        "texts": len(result["entities"]["texts"]),
        "mtexts": len(result["entities"]["mtexts"]),
        "inserts": len(result["entities"]["inserts"]),
        "blocks": len(result["blocks"]),
        "layers": len(result["layers"])
    }

    return result


def extract_metadata(doc) -> Dict[str, Any]:
    """DXF 문서 메타데이터 추출"""
    header = doc.header
    return {
        "version": doc.dxfversion,
        "encoding": doc.encoding,
        "units": header.get("$INSUNITS", 0),  # 0=Unitless, 1=Inches, 4=Millimeters
        "extmin": list(header.get("$EXTMIN", (0, 0, 0)))[:2],  # 도면 범위 최소
        "extmax": list(header.get("$EXTMAX", (0, 0, 0)))[:2],  # 도면 범위 최대
    }


def extract_layers(doc) -> List[Dict[str, Any]]:
    """레이어 정보 추출"""
    layers = []
    for layer in doc.layers:
        layers.append({
            "name": layer.dxf.name,
            "color": layer.dxf.color,
            "linetype": layer.dxf.linetype,
            "is_on": layer.is_on(),
            "is_locked": layer.is_locked(),
            "is_frozen": layer.is_frozen(),
        })
    return layers


def extract_blocks(doc) -> List[Dict[str, Any]]:
    """블록 정의 추출"""
    blocks = []
    for block in doc.blocks:
        if block.name.startswith("*"):  # 시스템 블록 제외
            continue

        block_entities = []
        for entity in block:
            block_entities.append({
                "type": entity.dxftype(),
                "layer": entity.dxf.layer if hasattr(entity.dxf, "layer") else None
            })

        blocks.append({
            "name": block.name,
            "base_point": list(block.base_point)[:2] if block.base_point else [0, 0],
            "entity_count": len(block_entities),
            "entity_types": list(set(e["type"] for e in block_entities))
        })
    return blocks


def extract_line(entity) -> Dict[str, Any]:
    """LINE 엔티티 추출"""
    return {
        "type": "LINE",
        "layer": entity.dxf.layer,
        "start": [entity.dxf.start.x, entity.dxf.start.y],
        "end": [entity.dxf.end.x, entity.dxf.end.y],
        "color": entity.dxf.color if hasattr(entity.dxf, "color") else None,
        "linetype": entity.dxf.linetype if hasattr(entity.dxf, "linetype") else None,
    }


def extract_lwpolyline(entity) -> Dict[str, Any]:
    """LWPOLYLINE 엔티티 추출"""
    points = []
    for point in entity.get_points():
        points.append([point[0], point[1]])  # x, y만

    return {
        "type": "LWPOLYLINE",
        "layer": entity.dxf.layer,
        "points": points,
        "is_closed": entity.closed,
        "color": entity.dxf.color if hasattr(entity.dxf, "color") else None,
        "linetype": entity.dxf.linetype if hasattr(entity.dxf, "linetype") else None,
    }


def extract_polyline(entity) -> Dict[str, Any]:
    """POLYLINE 엔티티 추출"""
    points = []
    for vertex in entity.vertices:
        points.append([vertex.dxf.location.x, vertex.dxf.location.y])

    return {
        "type": "POLYLINE",
        "layer": entity.dxf.layer,
        "points": points,
        "is_closed": entity.is_closed,
        "color": entity.dxf.color if hasattr(entity.dxf, "color") else None,
    }


def extract_circle(entity) -> Dict[str, Any]:
    """CIRCLE 엔티티 추출"""
    return {
        "type": "CIRCLE",
        "layer": entity.dxf.layer,
        "center": [entity.dxf.center.x, entity.dxf.center.y],
        "radius": entity.dxf.radius,
        "color": entity.dxf.color if hasattr(entity.dxf, "color") else None,
    }


def extract_arc(entity) -> Dict[str, Any]:
    """ARC 엔티티 추출"""
    return {
        "type": "ARC",
        "layer": entity.dxf.layer,
        "center": [entity.dxf.center.x, entity.dxf.center.y],
        "radius": entity.dxf.radius,
        "start_angle": entity.dxf.start_angle,
        "end_angle": entity.dxf.end_angle,
        "color": entity.dxf.color if hasattr(entity.dxf, "color") else None,
    }


def extract_text(entity) -> Dict[str, Any]:
    """TEXT 엔티티 추출"""
    return {
        "type": "TEXT",
        "layer": entity.dxf.layer,
        "text": entity.dxf.text,
        "insert": [entity.dxf.insert.x, entity.dxf.insert.y],
        "height": entity.dxf.height,
        "rotation": entity.dxf.rotation if hasattr(entity.dxf, "rotation") else 0,
        "color": entity.dxf.color if hasattr(entity.dxf, "color") else None,
    }


def extract_mtext(entity) -> Dict[str, Any]:
    """MTEXT 엔티티 추출"""
    return {
        "type": "MTEXT",
        "layer": entity.dxf.layer,
        "text": entity.text,  # MTEXT는 .text 속성 사용
        "insert": [entity.dxf.insert.x, entity.dxf.insert.y],
        "char_height": entity.dxf.char_height,
        "width": entity.dxf.width if hasattr(entity.dxf, "width") else None,
        "rotation": entity.dxf.rotation if hasattr(entity.dxf, "rotation") else 0,
        "color": entity.dxf.color if hasattr(entity.dxf, "color") else None,
    }


def extract_insert(entity) -> Dict[str, Any]:
    """INSERT (블록 참조) 엔티티 추출"""
    return {
        "type": "INSERT",
        "layer": entity.dxf.layer,
        "block_name": entity.dxf.name,
        "insert": [entity.dxf.insert.x, entity.dxf.insert.y],
        "scale": [
            entity.dxf.xscale if hasattr(entity.dxf, "xscale") else 1,
            entity.dxf.yscale if hasattr(entity.dxf, "yscale") else 1,
        ],
        "rotation": entity.dxf.rotation if hasattr(entity.dxf, "rotation") else 0,
        "color": entity.dxf.color if hasattr(entity.dxf, "color") else None,
    }


def parse_dwg(dwg_path: str, cleanup: bool = True) -> Dict[str, Any]:
    """
    DWG 파일을 파싱하여 엔티티 추출 (메인 함수)

    Args:
        dwg_path: DWG 파일 경로
        cleanup: 임시 DXF 파일 삭제 여부

    Returns:
        파싱 결과 딕셔너리
    """
    # 1. DWG → DXF 변환
    success, dxf_path, error = convert_dwg_to_dxf(dwg_path)

    if not success:
        # ODA 없으면 DXF 직접 시도 (DWG로 오인한 경우)
        if dwg_path.lower().endswith(".dxf"):
            return parse_dxf(dwg_path)

        return {
            "error": error,
            "oda_available": is_oda_available(),
            "suggestion": "Install ODA File Converter or provide DXF file directly"
        }

    try:
        # 2. DXF 파싱
        result = parse_dxf(dxf_path)
        result["source_format"] = "DWG"
        result["converted_from"] = dwg_path
        return result
    finally:
        # 3. 정리
        if cleanup and dxf_path:
            try:
                output_dir = os.path.dirname(dxf_path)
                if output_dir.startswith(tempfile.gettempdir()):
                    shutil.rmtree(output_dir, ignore_errors=True)
            except Exception:
                pass


def parse_dwg_bytes(
    file_bytes: bytes,
    filename: str = "drawing.dwg",
    cleanup: bool = True
) -> Dict[str, Any]:
    """
    바이트 데이터에서 DWG 파싱 (업로드된 파일용)

    Args:
        file_bytes: DWG 파일 바이트
        filename: 원본 파일명
        cleanup: 임시 파일 삭제 여부

    Returns:
        파싱 결과 딕셔너리
    """
    temp_dir = tempfile.mkdtemp(prefix="dwg_upload_")
    temp_path = os.path.join(temp_dir, filename)

    try:
        # 바이트를 파일로 저장
        with open(temp_path, "wb") as f:
            f.write(file_bytes)

        # 확장자에 따라 처리
        if filename.lower().endswith(".dxf"):
            return parse_dxf(temp_path)
        else:
            return parse_dwg(temp_path, cleanup=False)  # 이미 temp 디렉토리
    finally:
        if cleanup:
            shutil.rmtree(temp_dir, ignore_errors=True)


def extract_pid_elements(parsed_data: Dict) -> Dict[str, List]:
    """
    파싱된 DXF 데이터에서 P&ID 요소 추출

    - 라인 (배관, 신호선)
    - 텍스트 (태그, 라벨)
    - 블록 참조 (심볼)

    Returns:
        {
            "lines": [...],      # 연결선 (좌표 기반)
            "symbols": [...],    # 블록 참조 → 심볼 후보
            "texts": [...],      # 텍스트 → OCR 대체
        }
    """
    if "error" in parsed_data:
        return {"error": parsed_data["error"]}

    entities = parsed_data.get("entities", {})

    # 1. 라인 추출 (LINE + POLYLINE)
    lines = []

    for line in entities.get("lines", []):
        lines.append({
            "type": "line",
            "start": line["start"],
            "end": line["end"],
            "layer": line["layer"],
            "linetype": line.get("linetype", "CONTINUOUS"),
        })

    for polyline in entities.get("polylines", []):
        points = polyline["points"]
        for i in range(len(points) - 1):
            lines.append({
                "type": "polyline_segment",
                "start": points[i],
                "end": points[i + 1],
                "layer": polyline["layer"],
                "linetype": polyline.get("linetype", "CONTINUOUS"),
            })
        # 닫힌 폴리라인
        if polyline.get("is_closed") and len(points) > 2:
            lines.append({
                "type": "polyline_segment",
                "start": points[-1],
                "end": points[0],
                "layer": polyline["layer"],
                "linetype": polyline.get("linetype", "CONTINUOUS"),
            })

    # 2. 심볼 추출 (INSERT = 블록 참조)
    symbols = []
    for insert in entities.get("inserts", []):
        symbols.append({
            "type": "block_reference",
            "block_name": insert["block_name"],
            "position": insert["insert"],
            "scale": insert["scale"],
            "rotation": insert["rotation"],
            "layer": insert["layer"],
        })

    # 원 → 밸브/펌프 후보
    for circle in entities.get("circles", []):
        symbols.append({
            "type": "circle",
            "position": circle["center"],
            "radius": circle["radius"],
            "layer": circle["layer"],
        })

    # 3. 텍스트 추출
    texts = []
    for text in entities.get("texts", []):
        texts.append({
            "type": "text",
            "content": text["text"],
            "position": text["insert"],
            "height": text["height"],
            "layer": text["layer"],
        })

    for mtext in entities.get("mtexts", []):
        texts.append({
            "type": "mtext",
            "content": mtext["text"],
            "position": mtext["insert"],
            "height": mtext["char_height"],
            "layer": mtext["layer"],
        })

    return {
        "lines": lines,
        "symbols": symbols,
        "texts": texts,
        "statistics": {
            "lines": len(lines),
            "symbols": len(symbols),
            "texts": len(texts),
        }
    }


# 테스트용 유틸리티
def get_dwg_info() -> Dict[str, Any]:
    """DWG 파싱 기능 정보 반환"""
    return {
        "oda_available": is_oda_available(),
        "oda_path": find_oda_converter(),
        "supported_formats": ["DWG", "DXF"],
        "output_entities": [
            "LINE", "LWPOLYLINE", "POLYLINE",
            "CIRCLE", "ARC",
            "TEXT", "MTEXT",
            "INSERT (Block Reference)"
        ],
        "install_oda": "https://www.opendesign.com/guestfiles/oda_file_converter"
    }
