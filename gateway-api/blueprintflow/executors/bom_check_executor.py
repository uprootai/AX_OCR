"""
BMT BOM Check Executor
품목코드가 ERP BOM .1 레벨에 존재하는지 확인

입력: TAG→품목코드 매핑 + ERP BOM 엑셀 경로
출력: 매칭/불일치/미매핑 결과 리포트
"""
import os
import base64
import tempfile
import zipfile
import logging
import xml.etree.ElementTree as ET
from typing import Dict, Any, Optional, List, Set

from .base_executor import BaseNodeExecutor
from .executor_registry import ExecutorRegistry

logger = logging.getLogger(__name__)


def read_erp_bom_xlsx(xlsx_path: str) -> Set[str]:
    """
    ERP BOM 엑셀에서 .1 레벨 품목코드 추출

    구조: A열이 '.1'인 행의 C열이 품목코드
    """
    codes: Set[str] = set()

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
            sp = "xl/worksheets/sheet1.xml"
            if sp in z.namelist():
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

                    if cells.get("A", "") == ".1":
                        code = cells.get("C", "").strip()
                        if code:
                            codes.add(code)
    except Exception as e:
        logger.error(f"ERP BOM 엑셀 읽기 실패: {e}")

    return codes


class BomCheckExecutor(BaseNodeExecutor):
    """BMT ERP BOM 검증 실행기"""

    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        품목코드가 ERP BOM에 존재하는지 검증

        Parameters (inputs):
            - mapping: {TAG: 품목코드} 딕셔너리 (excel_lookup 출력)
            - tags: 전체 TAG 리스트
            - unmapped_tags: 매핑되지 않은 TAG 리스트
            - erp_bom_path: ERP BOM 엑셀 경로 (직접 지정)
            - erp_bom_file: ERP BOM 엑셀 base64 데이터 (업로드)

        Parameters (node config):
            - erp_bom_path: 기본 ERP BOM 엑셀 경로

        Returns:
            - matched: 매칭된 TAG 리스트
            - mismatched: 불일치 TAG 리스트 (Part List에는 있지만 ERP BOM에 없음)
            - unmapped: Part List에 없는 TAG 리스트
            - details: TAG별 상세 결과
            - summary: 요약 통계
        """
        # 매핑 데이터 가져오기
        tag_mapping = inputs.get("mapping", {})
        tags = inputs.get("tags", list(tag_mapping.keys()))
        unmapped_from_input = inputs.get("unmapped_tags", [])

        # ERP BOM 엑셀 경로 결정
        xlsx_path = self._resolve_xlsx_path(inputs, context)
        if not xlsx_path:
            raise ValueError(
                "ERP BOM 엑셀 파일을 지정해주세요. "
                "(erp_bom_path 파라미터 또는 erp_bom_file 업로드)"
            )

        # ERP BOM 코드 읽기
        erp_codes = read_erp_bom_xlsx(xlsx_path)
        logger.info(f"ERP BOM에서 {len(erp_codes)}개 품목코드 로드됨")

        # 검증 수행
        matched = []
        mismatched = []
        unmapped = list(unmapped_from_input)
        details = []

        for tag in sorted(tags):
            pl_code = tag_mapping.get(tag, "")
            if not pl_code:
                if tag not in unmapped:
                    unmapped.append(tag)
                details.append({
                    "tag": tag,
                    "part_list_code": None,
                    "in_erp_bom": False,
                    "status": "unmapped",
                    "status_label": "미매핑 (Part List에 없음)",
                })
            elif pl_code in erp_codes:
                matched.append(tag)
                details.append({
                    "tag": tag,
                    "part_list_code": pl_code,
                    "in_erp_bom": True,
                    "status": "matched",
                    "status_label": "매칭",
                })
            else:
                mismatched.append(tag)
                details.append({
                    "tag": tag,
                    "part_list_code": pl_code,
                    "in_erp_bom": False,
                    "status": "mismatched",
                    "status_label": "불일치 (ERP BOM 누락)",
                })

        summary = {
            "total_tags": len(tags),
            "matched_count": len(matched),
            "mismatched_count": len(mismatched),
            "unmapped_count": len(unmapped),
            "erp_bom_codes_count": len(erp_codes),
            "match_rate": (
                round(len(matched) / len(tags) * 100, 1) if tags else 0
            ),
        }

        logger.info(
            f"BOM 검증 결과: 매칭 {len(matched)}, "
            f"불일치 {len(mismatched)}, 미매핑 {len(unmapped)}"
        )

        return {
            "matched": matched,
            "mismatched": mismatched,
            "unmapped": unmapped,
            "details": details,
            "summary": summary,
        }

    def _resolve_xlsx_path(
        self, inputs: Dict[str, Any], context: Dict[str, Any]
    ) -> Optional[str]:
        """엑셀 파일 경로 결정 (파라미터 > 입력 > context 순)"""
        # 1. 노드 파라미터의 경로
        path = self.parameters.get("erp_bom_path", "")
        if path and os.path.exists(path):
            return path

        # 2. inputs의 경로
        path = inputs.get("erp_bom_path", "")
        if path and os.path.exists(path):
            return path

        # 3. base64 업로드 파일
        file_data = inputs.get("erp_bom_file") or self.parameters.get("erp_bom_file")
        if file_data:
            return self._save_temp_file(file_data)

        # 4. context의 global inputs
        global_inputs = context.get("inputs", {})
        path = global_inputs.get("erp_bom_path", "")
        if path and os.path.exists(path):
            return path

        file_data = global_inputs.get("erp_bom_file")
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
                "mapping": {
                    "type": "object",
                    "description": "TAG → 품목코드 매핑 딕셔너리",
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "전체 TAG 리스트",
                },
                "erp_bom_path": {
                    "type": "string",
                    "description": "ERP BOM 엑셀 파일 경로",
                },
                "erp_bom_file": {
                    "type": "string",
                    "description": "ERP BOM 엑셀 base64 데이터",
                },
            },
            "required": ["mapping"],
        }

    def get_output_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "matched": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "BOM 매칭 TAG 리스트",
                },
                "mismatched": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "BOM 불일치 TAG 리스트",
                },
                "unmapped": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Part List 미매핑 TAG 리스트",
                },
                "details": {
                    "type": "array",
                    "description": "TAG별 상세 결과",
                },
                "summary": {
                    "type": "object",
                    "description": "요약 통계",
                },
            },
        }


# 실행기 등록
ExecutorRegistry.register("bom_check", BomCheckExecutor)
