"""
BOMExecutor 파일 업로드 및 테이블 import 메서드
GT 파일, 단가 파일 업로드, Table Detector 결과 import
"""

import logging

logger = logging.getLogger(__name__)


class BOMFileOpsMixin:
    """BOM 파일 업로드 및 테이블 import 믹스인"""

    async def _upload_gt_file(self, session_id: str, gt_file: dict, image_width: int, image_height: int):
        """Builder에서 첨부된 GT 파일을 BOM 세션에 업로드

        Args:
            session_id: BOM 세션 ID
            gt_file: {"name": "labels.txt", "content": "data:...;base64,..."}
            image_width: 이미지 너비
            image_height: 이미지 높이
        """
        import base64

        try:
            gt_name = gt_file.get("name", "labels.txt")
            gt_content = gt_file.get("content", "")

            if not gt_content:
                logger.warning("GT 파일 내용이 비어있습니다")
                return

            # Data URL 디코딩
            if "," in gt_content:
                gt_bytes = base64.b64decode(gt_content.split(",", 1)[1])
            else:
                gt_bytes = gt_content.encode("utf-8")

            # GT 파일 업로드 (filename은 세션의 이미지명과 매칭)
            success, _, error = await self._post_api(
                "/api/ground-truth/upload",
                files={"file": (gt_name, gt_bytes, "text/plain")},
                data={
                    "filename": "image",
                    "image_width": str(image_width),
                    "image_height": str(image_height),
                },
                timeout=30
            )
            if success:
                logger.info(f"GT 파일 업로드 완료: {gt_name} → 세션 {session_id}")
            else:
                logger.warning(f"GT 파일 업로드 실패: {error}")

        except Exception as e:
            logger.error(f"GT 파일 업로드 중 오류: {e}")

    async def _upload_pricing_file(self, session_id: str, pricing_file: dict):
        """Builder에서 첨부된 단가 파일을 BOM 세션에 업로드

        Args:
            session_id: BOM 세션 ID
            pricing_file: {"name": "pricing.json", "content": "data:...;base64,..."}
        """
        import base64

        try:
            name = pricing_file.get("name", "pricing.json")
            content = pricing_file.get("content", "")

            if not content:
                logger.warning("단가 파일 내용이 비어있습니다")
                return

            # Data URL 디코딩
            if "," in content:
                file_bytes = base64.b64decode(content.split(",", 1)[1])
            else:
                file_bytes = content.encode("utf-8")

            success, _, error = await self._post_api(
                f"/bom/{session_id}/pricing",
                files={"file": (name, file_bytes, "application/json")},
                timeout=30
            )
            if success:
                logger.info(f"단가 파일 업로드 완료: {name} → 세션 {session_id}")
            else:
                logger.warning(f"단가 파일 업로드 실패: {error}")

        except Exception as e:
            logger.error(f"단가 파일 업로드 중 오류: {e}")

    async def _import_tables(self, session_id: str, tables: list, regions: list = None):
        """Gateway Table Detector 결과를 BOM 세션의 table_results 필드에 저장

        Table Detector 출력 형식:
        tables: [{"headers": [...], "data": [[...]], "html": "...", "source_region": "title_block"}, ...]

        프론트엔드 기대 형식 (table_results):
        [{"table_id": "...", "rows": N, "cols": M, "cells": [{text, row, col}], "html": "..."}]
        """
        try:
            table_results = []

            for i, table in enumerate(tables):
                headers = table.get("headers", [])
                data = table.get("data", [])
                rows_count = len(data) + (1 if headers else 0)
                cols_count = len(headers) if headers else (len(data[0]) if data else 0)

                # headers + data → cells 배열 변환
                cells = []
                if headers:
                    for col_idx, header_text in enumerate(headers):
                        cells.append({"text": str(header_text), "row": 0, "col": col_idx})
                for row_idx, row_data in enumerate(data):
                    actual_row = row_idx + (1 if headers else 0)
                    if isinstance(row_data, list):
                        for col_idx, cell_text in enumerate(row_data):
                            cells.append({"text": str(cell_text), "row": actual_row, "col": col_idx})
                    elif isinstance(row_data, dict):
                        for col_idx, (_, cell_text) in enumerate(row_data.items()):
                            cells.append({"text": str(cell_text), "row": actual_row, "col": col_idx})

                table_results.append({
                    "table_id": f"gateway_table_{i}",
                    "rows": rows_count,
                    "cols": cols_count,
                    "cells": cells,
                    "headers": headers,
                    "html": table.get("html", ""),
                    "source_region": table.get("source_region", ""),
                    "confidence": table.get("confidence", 0.9),
                })

            if table_results:
                success, _, error = await self._patch_api(
                    f"/sessions/{session_id}",
                    json_data={"table_results": table_results},
                    timeout=30
                )
                if success:
                    logger.info(f"테이블 import 완료: {len(table_results)}개 테이블 → table_results")
                else:
                    logger.warning(f"테이블 import 실패: {error}")
        except Exception as e:
            logger.warning(f"테이블 import 중 오류 (무시): {e}")
