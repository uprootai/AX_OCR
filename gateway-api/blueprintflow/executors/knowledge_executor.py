"""
Knowledge Engine Executor
Neo4j + GraphRAG + VectorRAG 기반 도메인 지식 엔진

PPT 슬라이드 13 [WHAT-4] 도메인 지식 엔진 구현:
- Neo4j 기반 유사 부품 검색
- GraphRAG + VectorRAG 하이브리드 검색
- ISO/ASME 규격 자동 검증
"""
from typing import Dict, Any, Optional, List
import httpx
import logging
import os
import re

from .base_executor import BaseNodeExecutor
from .executor_registry import ExecutorRegistry

logger = logging.getLogger(__name__)

# Knowledge API 기본 URL
KNOWLEDGE_API_URL = os.environ.get("KNOWLEDGE_API_URL", "http://knowledge-api:5007")


class KnowledgeExecutor(BaseNodeExecutor):
    """
    Knowledge Engine 실행기

    PPT 6단계 비용 산정 로직 중 2단계(유사 부품 검색) 담당:
    1. 도면 정보 추출 (eDOCr2/PaddleOCR) → 여기서 받음
    2. 유사 부품 검색 (Knowledge Engine) ← 여기서 수행
    3. 재질별 단가 데이터베이스 조회
    4. 공차 정밀도 → 가공 난이도 산정
    5. 공정별 비용 계산
    6. 최종 견적서 생성
    """

    def __init__(self, node_id: str, node_type: str, parameters: Dict[str, Any]):
        super().__init__(node_id, node_type, parameters)
        self.api_url = KNOWLEDGE_API_URL
        self.logger.info(f"KnowledgeExecutor 초기화 (API: {self.api_url})")

    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Knowledge Engine 실행

        입력:
        - ocr_results: OCR 결과 (치수, 공차, 재질 정보)
        - query: 직접 검색 쿼리 (선택)

        출력:
        - similar_parts: 유사 부품 목록
        - validation_result: 규격 검증 결과
        - cost_estimate: 비용 추정
        """
        self.logger.info(f"Knowledge Engine 실행 시작")

        # 파라미터 추출
        search_mode = self.parameters.get("search_mode", "hybrid")
        graph_weight = self.parameters.get("graph_weight", 0.6)
        top_k = self.parameters.get("top_k", 5)
        validate_standards = self.parameters.get("validate_standards", True)
        include_cost = self.parameters.get("include_cost", True)
        material_filter = self.parameters.get("material_filter", "all")

        result = {
            "similar_parts": [],
            "validation_result": None,
            "cost_estimate": None,
            "search_mode": search_mode,
            "api_url": self.api_url
        }

        # 쿼리 구성
        query = self._build_query(inputs)

        if not query:
            self.logger.warning("검색 쿼리가 비어있음 - 스킵")
            result["warning"] = "검색할 쿼리가 없습니다"
            return result

        self.logger.info(f"검색 쿼리: {query}")

        try:
            # 1. 유사 부품 검색
            similar_parts = await self._search_similar_parts(
                query=query,
                search_mode=search_mode,
                graph_weight=graph_weight,
                top_k=top_k,
                material_filter=material_filter
            )
            result["similar_parts"] = similar_parts

            # 2. 규격 검증 (옵션)
            if validate_standards:
                validation_result = await self._validate_standards(inputs)
                result["validation_result"] = validation_result

            # 3. 비용 추정 (옵션)
            if include_cost and similar_parts:
                cost_estimate = self._estimate_cost(similar_parts)
                result["cost_estimate"] = cost_estimate

            self.logger.info(f"Knowledge Engine 완료: {len(similar_parts)}개 유사 부품 발견")

        except Exception as e:
            self.logger.error(f"Knowledge Engine 오류: {e}")
            result["error"] = str(e)
            # 폴백: Mock 데이터 반환
            result["similar_parts"] = self._get_mock_similar_parts()
            result["fallback"] = True

        return result

    def _build_query(self, inputs: Dict[str, Any]) -> str:
        """
        입력에서 검색 쿼리 구성

        OCR 결과에서 치수, 공차, 재질 정보를 추출하여 쿼리 생성
        """
        query_parts = []

        # 직접 쿼리 (TextInput에서 연결)
        if "query" in inputs and inputs["query"]:
            return inputs["query"]

        if "text" in inputs and inputs["text"]:
            return inputs["text"]

        # OCR 결과에서 추출
        ocr_results = inputs.get("ocr_results") or inputs.get("text_results") or []

        if isinstance(ocr_results, list):
            for item in ocr_results:
                if isinstance(item, dict):
                    text = item.get("text") or item.get("content", "")
                else:
                    text = str(item)

                # 치수 패턴 (Ø50, 100±0.1, R20 등)
                dimension_patterns = [
                    r"[ØφΦ]\d+(?:\.\d+)?",  # Ø50, φ100
                    r"\d+(?:\.\d+)?[±]\d+(?:\.\d+)?",  # 100±0.1
                    r"[Rr]\d+(?:\.\d+)?",  # R20
                    r"\d+(?:\.\d+)?\s*[Hh][0-9]+",  # 50 H7
                    r"\d+(?:\.\d+)?\s*[Gg][0-9]+",  # 50 g6
                ]

                for pattern in dimension_patterns:
                    matches = re.findall(pattern, text)
                    query_parts.extend(matches)

                # 재질 패턴
                material_patterns = [
                    r"SUS\d+[A-Za-z]*",  # SUS304, SUS316L
                    r"S[0-9]+C",  # S45C
                    r"SCM\d+",  # SCM440
                    r"AL\d+",  # AL6061
                    r"A\d{4}",  # A6061
                ]

                for pattern in material_patterns:
                    matches = re.findall(pattern, text.upper())
                    query_parts.extend(matches)

        # 중복 제거 및 결합
        unique_parts = list(dict.fromkeys(query_parts))
        return " ".join(unique_parts[:10])  # 최대 10개 키워드

    async def _search_similar_parts(
        self,
        query: str,
        search_mode: str,
        graph_weight: float,
        top_k: int,
        material_filter: str
    ) -> List[Dict[str, Any]]:
        """
        유사 부품 검색 API 호출
        """
        endpoint = f"{self.api_url}/api/v1/similar-parts"

        payload = {
            "query": query,
            "mode": search_mode,
            "top_k": top_k,
            "graph_weight": graph_weight
        }

        if material_filter != "all":
            payload["material_filter"] = material_filter

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(endpoint, json=payload)

                if response.status_code == 200:
                    data = response.json()
                    return data.get("similar_parts", [])
                else:
                    self.logger.warning(f"유사 부품 검색 실패: {response.status_code}")
                    return self._get_mock_similar_parts()
        except Exception as e:
            self.logger.error(f"유사 부품 검색 오류: {e}")
            return self._get_mock_similar_parts()

    async def _validate_standards(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        ISO/ASME 규격 검증
        """
        endpoint = f"{self.api_url}/api/v1/validate/standard"

        # OCR 결과에서 검증 대상 추출
        validation_items = self._extract_validation_items(inputs)

        if not validation_items:
            return {"message": "검증 대상 없음"}

        results = {
            "is_valid": True,
            "items": [],
            "errors": [],
            "warnings": [],
            "matched_standards": []
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                for item in validation_items:
                    response = await client.post(endpoint, json=item)

                    if response.status_code == 200:
                        item_result = response.json()
                        results["items"].append(item_result)

                        if not item_result.get("is_valid", True):
                            results["is_valid"] = False

                        results["errors"].extend(item_result.get("errors", []))
                        results["warnings"].extend(item_result.get("warnings", []))
                        results["matched_standards"].extend(item_result.get("matched_standards", []))
        except Exception as e:
            self.logger.error(f"규격 검증 오류: {e}")
            results["error"] = str(e)

        # 중복 제거
        results["matched_standards"] = list(set(results["matched_standards"]))

        return results

    def _extract_validation_items(self, inputs: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        OCR 결과에서 규격 검증 대상 추출
        """
        items = []
        ocr_results = inputs.get("ocr_results") or inputs.get("text_results") or []

        if isinstance(ocr_results, list):
            for item in ocr_results:
                if isinstance(item, dict):
                    text = item.get("text") or item.get("content", "")
                else:
                    text = str(item)

                # 공차 패턴 (H7, g6, ±0.1)
                tolerance_match = re.search(r"([A-Za-z]{1,2})(\d{1,2})|([±][0-9.]+)", text)
                if tolerance_match:
                    items.append({
                        "tolerance": tolerance_match.group(0),
                        "dimension": self._extract_dimension(text)
                    })

                # 나사 패턴 (M10, M10x1.5)
                thread_match = re.search(r"M\d+(?:x\d+(?:\.\d+)?)?", text)
                if thread_match:
                    items.append({
                        "thread_spec": thread_match.group(0)
                    })

                # 표면조도 패턴 (Ra1.6)
                surface_match = re.search(r"Ra\s*\d+(?:\.\d+)?", text, re.IGNORECASE)
                if surface_match:
                    items.append({
                        "surface_finish": surface_match.group(0)
                    })

        return items[:20]  # 최대 20개

    def _extract_dimension(self, text: str) -> Optional[str]:
        """텍스트에서 치수 추출"""
        match = re.search(r"(\d+(?:\.\d+)?)\s*[Hh][0-9]+", text)
        if match:
            return match.group(1)
        return None

    def _estimate_cost(self, similar_parts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        유사 부품 기반 비용 추정

        PPT 6단계 비용 산정 로직 중 2단계 결과 활용
        """
        if not similar_parts:
            return {"estimated": False, "reason": "유사 부품 없음"}

        # 유사 부품의 비용 정보 집계
        costs = []
        for part in similar_parts:
            if "cost" in part and part["cost"]:
                costs.append(part["cost"])
            elif "estimated_cost" in part and part["estimated_cost"]:
                costs.append(part["estimated_cost"])

        if not costs:
            return {
                "estimated": False,
                "reason": "유사 부품에 비용 정보 없음",
                "reference_parts": len(similar_parts)
            }

        avg_cost = sum(costs) / len(costs)
        min_cost = min(costs)
        max_cost = max(costs)

        return {
            "estimated": True,
            "average_cost": round(avg_cost, 2),
            "min_cost": round(min_cost, 2),
            "max_cost": round(max_cost, 2),
            "reference_count": len(costs),
            "confidence": min(len(costs) / 5, 1.0),  # 5개 이상이면 신뢰도 100%
            "currency": "KRW"
        }

    def _get_mock_similar_parts(self) -> List[Dict[str, Any]]:
        """
        폴백용 Mock 유사 부품 데이터
        """
        return [
            {
                "part_id": "MOCK-001",
                "name": "샤프트 Ø50 H7",
                "material": "S45C",
                "similarity": 0.85,
                "dimensions": {"diameter": 50, "length": 100},
                "tolerance": "H7",
                "cost": 45000,
                "manufacturing_history": {
                    "process": ["선삭", "연삭"],
                    "lead_time_days": 3
                }
            },
            {
                "part_id": "MOCK-002",
                "name": "부싱 Ø48 H6",
                "material": "SUS304",
                "similarity": 0.72,
                "dimensions": {"diameter": 48, "length": 80},
                "tolerance": "H6",
                "cost": 52000,
                "manufacturing_history": {
                    "process": ["선삭", "호닝"],
                    "lead_time_days": 4
                }
            },
            {
                "part_id": "MOCK-003",
                "name": "플랜지 Ø52 H7",
                "material": "S45C",
                "similarity": 0.68,
                "dimensions": {"diameter": 52, "length": 30},
                "tolerance": "H7",
                "cost": 38000,
                "manufacturing_history": {
                    "process": ["선삭", "밀링"],
                    "lead_time_days": 2
                }
            }
        ]

    def validate_parameters(self) -> tuple[bool, Optional[str]]:
        """파라미터 유효성 검사"""
        search_mode = self.parameters.get("search_mode", "hybrid")
        if search_mode not in ["graph", "vector", "hybrid"]:
            return False, f"잘못된 search_mode: {search_mode}"

        graph_weight = self.parameters.get("graph_weight", 0.6)
        if not 0 <= graph_weight <= 1:
            return False, f"graph_weight는 0~1 범위여야 함: {graph_weight}"

        top_k = self.parameters.get("top_k", 5)
        if not 1 <= top_k <= 20:
            return False, f"top_k는 1~20 범위여야 함: {top_k}"

        return True, None

    def get_input_schema(self) -> Dict[str, Any]:
        """입력 스키마"""
        return {
            "type": "object",
            "properties": {
                "ocr_results": {
                    "type": "array",
                    "description": "OCR 결과 (치수, 공차, 재질 정보)"
                },
                "query": {
                    "type": "string",
                    "description": "직접 검색 쿼리"
                }
            }
        }

    def get_output_schema(self) -> Dict[str, Any]:
        """출력 스키마"""
        return {
            "type": "object",
            "properties": {
                "similar_parts": {
                    "type": "array",
                    "description": "유사 부품 목록"
                },
                "validation_result": {
                    "type": "object",
                    "description": "규격 검증 결과"
                },
                "cost_estimate": {
                    "type": "object",
                    "description": "비용 추정 결과"
                }
            }
        }


# 레지스트리에 등록
ExecutorRegistry.register("knowledge", KnowledgeExecutor)
