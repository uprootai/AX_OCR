"""BOM Migration Service - 기존 프로젝트 BOM 데이터 마이그레이션

기존 bom_items.json에 신규 필드 추가:
- assembly_drawing_number: 소속 핑크 어셈블리 도면번호
- parent_item_no 복구 (소실된 경우)
- doc_revision: matched_file에서 추출
- 빈 신규 필드 초기화 (bom_revision, part_no, size, weight_kg, remark)
"""

import re
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def migrate_bom_items(project_dir: Path) -> Dict[str, Any]:
    """기존 bom_items.json에 신규 필드 추가 + parent_item_no 복구

    Args:
        project_dir: 프로젝트 디렉토리 경로

    Returns:
        마이그레이션 결과 통계
    """
    bom_file = project_dir / "bom_items.json"
    if not bom_file.exists():
        return {"status": "skip", "reason": "bom_items.json 없음"}

    with open(bom_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 리스트 또는 dict 형태 모두 지원
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict) and data.get("items"):
        items = data["items"]
    else:
        return {"status": "skip", "reason": "items 필드 없음"}

    stats = {
        "total_items": len(items),
        "parent_fixed": 0,
        "assembly_dwg_added": 0,
        "doc_revision_added": 0,
        "fields_initialized": 0,
    }

    # 1. parent_item_no 복구 + assembly_drawing_number 할당
    current_assembly = None
    current_assembly_dwg = None
    current_subassembly = None

    for item in items:
        level = item.get("level", "part")

        if level == "assembly":
            current_assembly = item.get("item_no")
            current_assembly_dwg = item.get("drawing_number")
            current_subassembly = None
            if item.get("parent_item_no") is not None:
                item["parent_item_no"] = None
                stats["parent_fixed"] += 1
            item["assembly_drawing_number"] = current_assembly_dwg
            stats["assembly_dwg_added"] += 1

        elif level == "subassembly":
            current_subassembly = item.get("item_no")
            if item.get("parent_item_no") != current_assembly:
                item["parent_item_no"] = current_assembly
                stats["parent_fixed"] += 1
            item["assembly_drawing_number"] = current_assembly_dwg
            stats["assembly_dwg_added"] += 1

        elif level == "part":
            expected_parent = current_subassembly or current_assembly
            if item.get("parent_item_no") != expected_parent:
                item["parent_item_no"] = expected_parent
                stats["parent_fixed"] += 1
            item["assembly_drawing_number"] = current_assembly_dwg
            stats["assembly_dwg_added"] += 1

    # 2. doc_revision 추출 (matched_file에서)
    for item in items:
        if item.get("doc_revision"):
            continue
        matched_file = item.get("matched_file", "")
        if matched_file:
            m = re.search(r'Rev\.([A-Z0-9]+)', matched_file)
            if m:
                item["doc_revision"] = m.group(1)
                stats["doc_revision_added"] += 1

    # 3. 신규 필드 초기화 (없는 필드만)
    new_fields = {
        "assembly_drawing_number": None,
        "bom_revision": None,
        "doc_revision": None,
        "part_no": None,
        "size": None,
        "weight_kg": None,
        "remark": None,
    }
    for item in items:
        for field, default in new_fields.items():
            if field not in item:
                item[field] = default
                stats["fields_initialized"] += 1

    # 4. 저장
    if isinstance(data, dict):
        data["items"] = items
        save_data = data
    else:
        save_data = items

    with open(bom_file, "w", encoding="utf-8") as f:
        json.dump(save_data, f, ensure_ascii=False, indent=2)

    stats["status"] = "ok"
    logger.info(
        f"BOM 마이그레이션 완료: {project_dir.name} → "
        f"parent 수정={stats['parent_fixed']}, "
        f"assembly_dwg 추가={stats['assembly_dwg_added']}, "
        f"doc_rev 추가={stats['doc_revision_added']}"
    )

    return stats
