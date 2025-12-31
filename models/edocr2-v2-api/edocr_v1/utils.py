"""
eDOCr v1 Utility Functions
유틸리티 함수 및 상수 정의
"""

import re
import logging
import string
from pathlib import Path
from typing import Dict, Any, List, Tuple

logger = logging.getLogger(__name__)

# =====================
# Constants
# =====================

# Directories
BASE_DIR = Path(__file__).parent.parent  # edocr2-v2-api/
UPLOAD_DIR = BASE_DIR / "uploads"
RESULTS_DIR = BASE_DIR / "results"

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

# eDOCr v1 alphabets
GDT_SYMBOLS = '\u23e4\u23e5\u25cb\u232d\u2312\u2313\u23ca\u2220\u2afd\u232f\u2316\u25ce\u2197\u2330'
FCF_SYMBOLS = '\u24ba\u24bb\u24c1\u24c2\u24c5\u24c8\u24c9\u24ca'
EXTRA = '(),.+-\u00b1:/"'
ALPHABET_DIMENSIONS = string.digits + 'AaBCDRGHhMmnx' + EXTRA
ALPHABET_INFOBLOCK = string.digits + string.ascii_letters + ',.:-/'
ALPHABET_GDTS = string.digits + ',.\u2300ABCD' + GDT_SYMBOLS


# =====================
# Helper Functions
# =====================

def convert_to_serializable(obj: Any) -> Any:
    """Convert numpy types to Python native types for JSON serialization"""
    import numpy as np

    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_to_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_to_serializable(item) for item in obj]
    else:
        return obj


def allowed_file(filename: str) -> bool:
    """Validate file extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def extract_bbox_info(bbox: List) -> Dict[str, int]:
    """Extract bounding box information from eDOCr bbox format"""
    bbox_info = {}
    if bbox and len(bbox) >= 4:
        x_coords = [pt[0] for pt in bbox if len(pt) >= 2]
        y_coords = [pt[1] for pt in bbox if len(pt) >= 2]
        if x_coords and y_coords:
            bbox_info = {
                'x': int(min(x_coords)),
                'y': int(min(y_coords)),
                'width': int(max(x_coords) - min(x_coords)),
                'height': int(max(y_coords) - min(y_coords))
            }

    if not bbox_info:
        bbox_info = {'x': 0, 'y': 0, 'width': 0, 'height': 0}

    return bbox_info


def transform_edocr_to_ui_format(
    dimension_dict: List[Dict],
    gdt_dict: List[Dict],
    infoblock_dict: Dict
) -> Tuple[List[Dict], List[Dict], Dict]:
    """
    Transform eDOCr v1 output format to UI-compatible format

    eDOCr v1 format:
    - dimensions: [{'pred': {...}, 'bbox': [[x,y], ...], ...}, ...]
    - gdt: [{'pred': {...}, 'bbox': [[x,y], ...], ...}, ...]
    - text: {various keys with values}

    UI expected format:
    - dimensions: [{type, value, unit, tolerance, location: {x, y}}, ...]
    - gdt: [{type, value, datum, location: {x, y}}, ...]
    - text: {drawing_number, revision, title, material, notes, total_blocks}
    """
    # Transform dimensions
    ui_dimensions = []
    for dim in dimension_dict:
        try:
            pred = dim.get('pred', {})
            # eDOCr v1 uses 'box' not 'bbox'
            bbox = dim.get('box', dim.get('bbox', [[0, 0]]))

            # eDOCr v1 uses 'value' or 'nominal', not 'text'
            text = str(pred.get('value', pred.get('nominal', '0')))

            # Determine dimension type based on text patterns
            dim_type = 'linear'
            if '\u00d8' in text or '\u2300' in text:
                dim_type = 'diameter'
            elif 'R' in text[:2]:  # Radius at start
                dim_type = 'radius'

            # Extract numeric value
            value_match = re.search(r'[\d.]+', text.replace('\u00d8', '').replace('\u2300', '').replace('R', ''))
            value = float(value_match.group()) if value_match else 0.0

            # Extract tolerance if present (e.g., "+0.1/-0.05" or "0.1")
            tolerance = None
            if '+' in text or '\u00b1' in text:
                tolerance = text[text.find('+'):] if '+' in text else text[text.find('\u00b1'):]

            # Calculate bounding box
            bbox_info = extract_bbox_info(bbox)

            ui_dimensions.append({
                'type': dim_type,
                'value': value,
                'unit': 'mm',  # Default unit for engineering drawings
                'tolerance': tolerance,
                'bbox': bbox_info
            })
        except Exception as e:
            logger.warning(f"Failed to transform dimension: {e}")
            continue

    # Transform GD&T
    ui_gdt = []
    for gdt in gdt_dict:
        try:
            pred = gdt.get('pred', {})
            # eDOCr v1 uses 'box' not 'bbox'
            bbox = gdt.get('box', gdt.get('bbox', [[0, 0]]))

            # eDOCr v1 uses 'value' or 'nominal', not 'text'
            text = str(pred.get('value', pred.get('nominal', '')))

            # Extract GD&T type (first symbol)
            gdt_type = text[0] if text else 'unknown'

            # Extract tolerance value
            value_match = re.search(r'[\d.]+', text)
            value = float(value_match.group()) if value_match else 0.0

            # Extract datum (capital letters)
            datum_match = re.search(r'[A-Z]', text[1:]) if len(text) > 1 else None
            datum = datum_match.group() if datum_match else None

            # Calculate bounding box
            bbox_info = extract_bbox_info(bbox)

            ui_gdt.append({
                'type': gdt_type,
                'value': value,
                'datum': datum,
                'bbox': bbox_info
            })
        except Exception as e:
            logger.warning(f"Failed to transform GD&T: {e}")
            continue

    # Transform text/infoblock
    ui_text = {
        'drawing_number': None,
        'revision': None,
        'title': None,
        'material': None,
        'notes': [],
        'total_blocks': 0
    }

    if isinstance(infoblock_dict, dict):
        # eDOCr v1 infoblock format varies, try to extract common fields
        ui_text['drawing_number'] = infoblock_dict.get('drawing_number') or infoblock_dict.get('part_number')
        ui_text['revision'] = infoblock_dict.get('revision') or infoblock_dict.get('rev')
        ui_text['title'] = infoblock_dict.get('title') or infoblock_dict.get('drawing_title')
        ui_text['material'] = infoblock_dict.get('material') or infoblock_dict.get('mat')

        # Collect all other text as notes
        notes = []
        excluded_keys = {'drawing_number', 'part_number', 'revision', 'rev', 'title', 'drawing_title', 'material', 'mat'}
        for key, value in infoblock_dict.items():
            if key not in excluded_keys and value:
                notes.append(f"{key}: {value}")
        ui_text['notes'] = notes
        ui_text['total_blocks'] = len(infoblock_dict)

    return ui_dimensions, ui_gdt, ui_text


def init_directories():
    """Initialize required directories"""
    UPLOAD_DIR.mkdir(exist_ok=True)
    RESULTS_DIR.mkdir(exist_ok=True)
