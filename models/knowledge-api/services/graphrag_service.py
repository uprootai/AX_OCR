"""
GraphRAG Service
그래프 기반 검색 증강 생성 (Retrieval-Augmented Generation)

PPT 슬라이드 13 [WHAT-4] 도메인 지식 엔진 설계:
- 그래프 탐색으로 유사 부품 및 관계 검색
- Component → Dimension → Tolerance → Process 관계 추론
"""

import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


class GraphRAGService:
    """GraphRAG 서비스 - Neo4j 기반 그래프 검색"""

    def __init__(self, neo4j_service):
        self.neo4j = neo4j_service
        logger.info("GraphRAG service initialized")

    async def search(
        self,
        query: str,
        dimensions: Optional[List[str]] = None,
        tolerance: Optional[str] = None,
        material: Optional[str] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        그래프 기반 검색

        1. 치수/공차/재질로 유사 부품 검색
        2. 관계 그래프 탐색
        3. 유사도 점수 계산
        """
        results = []

        # 치수 기반 검색
        if dimensions:
            similar = await self._search_by_dimensions(dimensions, tolerance, material, top_k)
            results.extend(similar)

        # 재질 기반 검색
        if material and not dimensions:
            by_material = await self._search_by_material(material, top_k)
            results.extend(by_material)

        # 텍스트 쿼리 기반 검색 (파싱)
        if query and not dimensions:
            parsed = self._parse_query(query)
            if parsed.get("dimensions"):
                similar = await self._search_by_dimensions(
                    parsed["dimensions"],
                    parsed.get("tolerance"),
                    parsed.get("material"),
                    top_k
                )
                results.extend(similar)

        return results[:top_k]

    async def find_similar_parts(
        self,
        dimensions: List[str],
        tolerance: Optional[str] = None,
        material: Optional[str] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        유사 부품 검색 (PPT 6단계 비용 산정의 2단계)

        GraphRAG로 비슷한 크기, 공차, 재질의 과거 프로젝트 검색
        """
        if not self.neo4j:
            return self._get_mock_similar_parts(dimensions, tolerance, material, top_k)

        try:
            results = await self.neo4j.find_similar_components(
                dimensions=dimensions,
                tolerance=tolerance,
                material=material,
                top_k=top_k
            )

            # 과거 비용 정보 추가
            enriched_results = []
            for r in results:
                if r.get("part_id"):
                    cost_info = await self.neo4j.get_component_with_cost(r["part_id"])
                    if cost_info:
                        r["past_cost"] = cost_info.get("past_cost")
                        r["past_processes"] = cost_info.get("processes", [])
                        r["project_date"] = cost_info.get("project_date")
                enriched_results.append(r)

            return enriched_results

        except Exception as e:
            logger.error(f"Similar parts search failed: {e}")
            return self._get_mock_similar_parts(dimensions, tolerance, material, top_k)

    async def _search_by_dimensions(
        self,
        dimensions: List[str],
        tolerance: Optional[str],
        material: Optional[str],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """치수 기반 검색"""
        if not self.neo4j:
            return []

        try:
            return await self.neo4j.find_similar_components(
                dimensions=dimensions,
                tolerance=tolerance,
                material=material,
                top_k=top_k
            )
        except Exception as e:
            logger.error(f"Dimension search failed: {e}")
            return []

    async def _search_by_material(
        self,
        material: str,
        top_k: int
    ) -> List[Dict[str, Any]]:
        """재질 기반 검색"""
        if not self.neo4j:
            return []

        query = """
        MATCH (c:Component)-[:MADE_OF]->(m:Material {name: $material})
        OPTIONAL MATCH (c)-[:HAS_DIM]->(d:Dimension)
        RETURN c.id as part_id, c.name as name,
               COLLECT(d.value) as dimensions,
               m.name as material,
               0.8 as similarity
        LIMIT $top_k
        """

        try:
            results = await self.neo4j.execute_query(
                query,
                {"material": material, "top_k": top_k}
            )
            return results
        except Exception as e:
            logger.error(f"Material search failed: {e}")
            return []

    def _parse_query(self, query: str) -> Dict[str, Any]:
        """
        쿼리 텍스트 파싱

        예: "SUS304 Ø50 H7" → {material: "SUS304", dimensions: ["50"], tolerance: "H7"}
        """
        import re

        result = {
            "dimensions": [],
            "tolerance": None,
            "material": None
        }

        # 재질 패턴 (SUS304, AL6061, SS400 등)
        material_patterns = [
            r'(SUS\d+[A-Z]?)',
            r'(AL\d+[A-Z]?\d*)',
            r'(SS\d+)',
            r'(S45C)',
            r'(SCM\d+)',
        ]
        for pattern in material_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                result["material"] = match.group(1).upper()
                break

        # 치수 패턴 (Ø50, 50mm, 50x30 등)
        dim_patterns = [
            r'[ØΦφ](\d+(?:\.\d+)?)',  # 직경
            r'(\d+(?:\.\d+)?)\s*(?:mm|MM)',  # mm 단위
            r'(\d+(?:\.\d+)?)\s*[xX×]\s*(\d+(?:\.\d+)?)',  # LxW 형식
        ]
        for pattern in dim_patterns:
            matches = re.findall(pattern, query)
            for m in matches:
                if isinstance(m, tuple):
                    result["dimensions"].extend([str(d) for d in m if d])
                else:
                    result["dimensions"].append(str(m))

        # 공차 패턴 (H7, h6, g6, ±0.1 등)
        tol_patterns = [
            r'([A-Z][0-9]+)',  # H7, F8 등 (대문자 = 구멍)
            r'([a-z][0-9]+)',  # h6, g6 등 (소문자 = 축)
            r'(±\d+(?:\.\d+)?)',  # ±0.1 등
        ]
        for pattern in tol_patterns:
            match = re.search(pattern, query)
            if match:
                result["tolerance"] = match.group(1)
                break

        return result

    def _get_mock_similar_parts(
        self,
        dimensions: List[str],
        tolerance: Optional[str],
        material: Optional[str],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """Mock 데이터 (Neo4j 미연결 시)"""
        mock_data = [
            {
                "part_id": "MOCK-001",
                "name": "유사부품 A",
                "similarity": 0.95,
                "dimensions": dimensions,
                "tolerance": tolerance or "H7",
                "material": material or "SUS304",
                "past_cost": 84205,
                "past_processes": ["TURNING", "MILLING", "GRINDING"],
                "project_date": "2024-10-15"
            },
            {
                "part_id": "MOCK-002",
                "name": "유사부품 B",
                "similarity": 0.88,
                "dimensions": [str(float(d) * 1.1) for d in dimensions] if dimensions else ["55"],
                "tolerance": tolerance or "H7",
                "material": material or "SUS304",
                "past_cost": 92150,
                "past_processes": ["TURNING", "MILLING"],
                "project_date": "2024-09-20"
            },
            {
                "part_id": "MOCK-003",
                "name": "유사부품 C",
                "similarity": 0.82,
                "dimensions": [str(float(d) * 0.9) for d in dimensions] if dimensions else ["45"],
                "tolerance": "H8",
                "material": material or "AL6061",
                "past_cost": 65800,
                "past_processes": ["TURNING", "DRILLING"],
                "project_date": "2024-08-10"
            },
        ]
        return mock_data[:top_k]
