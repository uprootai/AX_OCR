"""
BMT Excel Lookup Executor
TAG 리스트 + Part List 엑셀에서 TAG → 품목코드 매핑 수행

입력: TAG 리스트 + Part List 엑셀 경로 또는 base64 데이터
출력: {TAG: 품목코드} 매핑
"""
import re
import os
import base64
import tempfile
import zipfile
import logging
import xml.etree.ElementTree as ET
from typing import Dict, Any, Optional, List

from .base_executor import BaseNodeExecutor
from .executor_registry import ExecutorRegistry

logger = logging.getLogger(__name__)


def read_part_list_xlsx(xlsx_path: str) -> Dict[str, str]:
    """
    Part List 엑셀에서 TAG → 품목코드 매핑 추출

    구조:
    - VALVE LIST: B열(TAG) → Y열(품목코드)
    - SENSOR LIST: B열(TAG) → M열(품목코드)
    """
    mapping: Dict[str, str] = {}

    try:
        with zipfile.ZipFile(xlsx_path) as z:
            # 공유 문자열 테이블 로드
            ss: List[str] = []
            if "xl/sharedStrings.xml" in z.namelist():
                tree = ET.parse(z.open("xl/sharedStrings.xml"))
                ns = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
                for si in tree.findall(".//s:si", ns):
                    ss.append("".join(t.text or "" for t in si.findall(".//s:t", ns)))

            ns3 = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"

            # sheet1 (VALVE LIST), sheet2 (SENSOR LIST)
            for sheet_idx in [1, 2]:
                sp = f"xl/worksheets/sheet{sheet_idx}.xml"
                if sp not in z.namelist():
                    continue

                tree = ET.parse(z.open(sp))
                for row in tree.findall(f".//{{{ns3}}}row"):
                    cells: Dict[str, str] = {}
                    for c in row:
                        v = c.find(f"{{{ns3}}}v")
                        ref = c.attrib.get("r", "")
                        col = "".join(filter(str.isalpha, ref))
                        if v is not None and v.text:
                            if c.attrib.get("t") == "s" and int(v.text) < len(ss):
                                cells[col] = ss[int(v.text)]
                            else:
                                cells[col] = v.text

                    tag = cells.get("B", "").strip().upper()
                    # Y열 우선 (VALVE LIST), M열 폴백 (SENSOR LIST)
                    code = cells.get("Y", cells.get("M", "")).strip()

                    if (
                        tag
                        and code
                        and tag != "-"
                        and tag not in ("CODE", "NO.")
                        and len(code) > 5
                    ):
                        mapping[tag] = code
    except Exception as e:
        logger.error(f"Part List 엑셀 읽기 실패: {e}")

    return mapping


class ExcelLookupExecutor(BaseNodeExecutor):
    """BMT Part List 엑셀 매핑 실행기"""

    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        TAG → 품목코드 매핑 수행

        Parameters (inputs):
            - tags: TAG 리스트 (tag_filter_executor 출력)
            - part_list_path: Part List 엑셀 파일 경로 (직접 지정)
            - part_list_file: Part List 엑셀 base64 데이터 (업로드)

        Parameters (node config):
            - part_list_path: 기본 Part List 엑셀 경로

        Returns:
            - mapping: {TAG: 품목코드} 딕셔너리
            - total_mappings: 매핑 건수
            - unmapped_tags: 매핑되지 않은 TAG 리스트
            - tags: 원본 TAG 리스트 패스스루
        """
        # TAG 리스트 가져오기
        tags = inputs.get("tags", [])
        if not tags:
            logger.warning("TAG 리스트가 비어있습니다")

        # Part List 엑셀 경로 결정
        xlsx_path = self._resolve_xlsx_path(inputs, context)
        if not xlsx_path:
            raise ValueError(
                "Part List 엑셀 파일을 지정해주세요. "
                "(part_list_path 파라미터 또는 part_list_file 업로드)"
            )

        # 엑셀에서 매핑 읽기
        full_mapping = read_part_list_xlsx(xlsx_path)
        logger.info(f"Part List에서 {len(full_mapping)}개 매핑 로드됨")

        # TAG에 해당하는 매핑만 추출
        tag_mapping = {}
        unmapped = []
        for tag in tags:
            code = full_mapping.get(tag, "")
            if code:
                tag_mapping[tag] = code
            else:
                unmapped.append(tag)

        logger.info(
            f"매핑 결과: {len(tag_mapping)}개 매핑, {len(unmapped)}개 미매핑"
        )

        return {
            "mapping": tag_mapping,
            "total_mappings": len(tag_mapping),
            "unmapped_tags": unmapped,
            "tags": tags,
        }

    def _resolve_xlsx_path(
        self, inputs: Dict[str, Any], context: Dict[str, Any]
    ) -> Optional[str]:
        """엑셀 파일 경로 결정 (파라미터 > 입력 > context 순)"""
        # 1. 노드 파라미터의 경로
        path = self.parameters.get("part_list_path", "")
        if path and os.path.exists(path):
            return path

        # 2. inputs의 경로
        path = inputs.get("part_list_path", "")
        if path and os.path.exists(path):
            return path

        # 3. base64 업로드 파일
        file_data = inputs.get("part_list_file") or self.parameters.get("part_list_file")
        if file_data:
            return self._save_temp_file(file_data)

        # 4. context의 global inputs
        global_inputs = context.get("inputs", {})
        path = global_inputs.get("part_list_path", "")
        if path and os.path.exists(path):
            return path

        file_data = global_inputs.get("part_list_file")
        if file_data:
            return self._save_temp_file(file_data)

        return None

    def _save_temp_file(self, file_data: Any) -> Optional[str]:
        """base64 또는 dict 파일 데이터를 임시 파일로 저장"""
        try:
            if isinstance(file_data, dict):
                b64 = file_data.get("data", file_data.get("content", ""))
            elif isinstance(file_data, str):
                b64 = file_data
            else:
                return None

            if not b64:
                return None

            # data URL prefix 제거
            if b64.startswith("data:"):
                b64 = b64.split(",", 1)[1]

            data = base64.b64decode(b64)
            tmp = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
            tmp.write(data)
            tmp.close()
            return tmp.name
        except Exception as e:
            logger.error(f"임시 파일 저장 실패: {e}")
            return None

    def validate_parameters(self) -> tuple[bool, Optional[str]]:
        """파라미터 유효성 검사"""
        return True, None

    def get_input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "TAG 리스트",
                },
                "part_list_path": {
                    "type": "string",
                    "description": "Part List 엑셀 파일 경로",
                },
                "part_list_file": {
                    "type": "string",
                    "description": "Part List 엑셀 base64 데이터",
                },
            },
            "required": ["tags"],
        }

    def get_output_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "mapping": {
                    "type": "object",
                    "description": "TAG → 품목코드 매핑 딕셔너리",
                },
                "total_mappings": {"type": "integer", "description": "매핑 건수"},
                "unmapped_tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "매핑되지 않은 TAG 리스트",
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "원본 TAG 리스트 패스스루",
                },
            },
        }


# 실행기 등록
ExecutorRegistry.register("excel_lookup", ExcelLookupExecutor)
