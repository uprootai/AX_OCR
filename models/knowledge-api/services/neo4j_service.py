"""
Neo4j Service
도면 전용 그래프 DB 서비스

스키마:
- Component (부품)
- Dimension (치수)
- Tolerance (공차)
- Process (공정)
- Material (재질)
- Project (과거 프로젝트)

관계:
- Component -[HAS_DIM]-> Dimension
- Dimension -[HAS_TOL]-> Tolerance
- Component -[REQUIRES]-> Process
- Component -[MADE_OF]-> Material
- Component -[PART_OF]-> Project
"""

import logging
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# Neo4j driver (optional import)
try:
    from neo4j import AsyncGraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    logger.warning("neo4j package not installed, using mock service")


class Neo4jService:
    """Neo4j 그래프 DB 서비스"""

    def __init__(self, uri: str, user: str, password: str):
        self.uri = uri
        self.user = user
        self.password = password
        self.driver = None
        self._connected = False

    async def connect(self):
        """Neo4j 연결"""
        if not NEO4J_AVAILABLE:
            logger.warning("Neo4j driver not available, using mock mode")
            self._connected = False
            return

        try:
            self.driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
            # Verify connectivity
            async with self.driver.session() as session:
                await session.run("RETURN 1")
            self._connected = True
            logger.info(f"Connected to Neo4j at {self.uri}")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            self._connected = False
            raise

    async def close(self):
        """연결 종료"""
        if self.driver:
            await self.driver.close()
            self._connected = False
            logger.info("Neo4j connection closed")

    async def is_connected(self) -> bool:
        """연결 상태 확인"""
        if not self.driver or not self._connected:
            return False
        try:
            async with self.driver.session() as session:
                await session.run("RETURN 1")
            return True
        except Exception:
            return False

    async def init_schema(self):
        """그래프 스키마 초기화 (인덱스 및 제약조건)"""
        if not self._connected:
            logger.warning("Neo4j not connected, skipping schema init")
            return

        constraints = [
            # Component 노드 제약조건
            "CREATE CONSTRAINT component_id IF NOT EXISTS FOR (c:Component) REQUIRE c.id IS UNIQUE",
            # Dimension 노드 제약조건
            "CREATE CONSTRAINT dimension_id IF NOT EXISTS FOR (d:Dimension) REQUIRE d.id IS UNIQUE",
            # Tolerance 노드 제약조건
            "CREATE CONSTRAINT tolerance_id IF NOT EXISTS FOR (t:Tolerance) REQUIRE t.id IS UNIQUE",
            # Process 노드 제약조건
            "CREATE CONSTRAINT process_name IF NOT EXISTS FOR (p:Process) REQUIRE p.name IS UNIQUE",
            # Material 노드 제약조건
            "CREATE CONSTRAINT material_name IF NOT EXISTS FOR (m:Material) REQUIRE m.name IS UNIQUE",
            # Project 노드 제약조건
            "CREATE CONSTRAINT project_id IF NOT EXISTS FOR (p:Project) REQUIRE p.id IS UNIQUE",
        ]

        indexes = [
            # 검색 성능을 위한 인덱스
            "CREATE INDEX component_name IF NOT EXISTS FOR (c:Component) ON (c.name)",
            "CREATE INDEX dimension_value IF NOT EXISTS FOR (d:Dimension) ON (d.value)",
            "CREATE INDEX tolerance_type IF NOT EXISTS FOR (t:Tolerance) ON (t.type)",
        ]

        async with self.driver.session() as session:
            for constraint in constraints:
                try:
                    await session.run(constraint)
                except Exception as e:
                    logger.debug(f"Constraint may already exist: {e}")

            for index in indexes:
                try:
                    await session.run(index)
                except Exception as e:
                    logger.debug(f"Index may already exist: {e}")

        logger.info("Neo4j schema initialized")

    async def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Cypher 쿼리 실행"""
        if not self._connected:
            return []

        async with self.driver.session() as session:
            result = await session.run(query, parameters or {})
            records = await result.data()
            return records

    async def create_component(
        self,
        name: str,
        part_id: Optional[str] = None,
        part_number: Optional[str] = None,
        category: Optional[str] = None,
        material: Optional[str] = None,
        manufacturer: Optional[str] = None,
        unit_price: Optional[float] = None,
        specifications: Optional[Dict] = None,
        dimensions: List[Dict] = None,
        tolerances: List[Dict] = None,
        processes: List[Dict] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        부품 컴포넌트 생성 (그래프 관계 포함)

        Component --HAS_DIM--> Dimension --HAS_TOL--> Tolerance
        Component --REQUIRES--> Process
        Component --MADE_OF--> Material
        """
        # 사용자 지정 part_id가 있으면 사용, 없으면 UUID 생성
        component_id = part_id or str(uuid.uuid4())[:8]
        dimensions = dimensions or []
        tolerances = tolerances or []
        processes = processes or []
        metadata = metadata or {}
        specifications = specifications or {}

        if not self._connected:
            logger.warning("Neo4j not connected, returning mock ID")
            return f"mock-{component_id}"

        async with self.driver.session() as session:
            # 1. Component 노드 생성 (모든 속성 포함)
            await session.run(
                """
                CREATE (c:Component {
                    id: $id,
                    part_id: $part_id,
                    name: $name,
                    part_number: $part_number,
                    category: $category,
                    manufacturer: $manufacturer,
                    unit_price: $unit_price,
                    specifications: $specifications,
                    created_at: $created_at,
                    metadata: $metadata
                })
                """,
                {
                    "id": component_id,
                    "part_id": part_id,
                    "name": name,
                    "part_number": part_number,
                    "category": category,
                    "manufacturer": manufacturer,
                    "unit_price": unit_price,
                    "specifications": str(specifications) if specifications else "{}",
                    "created_at": datetime.now().isoformat(),
                    "metadata": str(metadata)
                }
            )

            # 2. Material 노드 및 관계 생성
            if material:
                await session.run(
                    """
                    MERGE (m:Material {name: $material})
                    WITH m
                    MATCH (c:Component {id: $component_id})
                    MERGE (c)-[:MADE_OF]->(m)
                    """,
                    {"material": material, "component_id": component_id}
                )

            # 3. Dimension 노드 및 관계 생성
            for i, dim in enumerate(dimensions):
                dim_id = f"{component_id}-dim-{i}"
                await session.run(
                    """
                    CREATE (d:Dimension {
                        id: $dim_id,
                        value: $value,
                        unit: $unit,
                        type: $type
                    })
                    WITH d
                    MATCH (c:Component {id: $component_id})
                    MERGE (c)-[:HAS_DIM]->(d)
                    """,
                    {
                        "dim_id": dim_id,
                        "value": dim.get("value", ""),
                        "unit": dim.get("unit", "mm"),
                        "type": dim.get("type", "linear"),
                        "component_id": component_id
                    }
                )

            # 4. Tolerance 노드 및 관계 생성
            for i, tol in enumerate(tolerances):
                tol_id = f"{component_id}-tol-{i}"
                await session.run(
                    """
                    CREATE (t:Tolerance {
                        id: $tol_id,
                        type: $type,
                        grade: $grade,
                        upper: $upper,
                        lower: $lower
                    })
                    WITH t
                    MATCH (c:Component {id: $component_id})
                    MATCH (c)-[:HAS_DIM]->(d:Dimension)
                    WITH t, d LIMIT 1
                    MERGE (d)-[:HAS_TOL]->(t)
                    """,
                    {
                        "tol_id": tol_id,
                        "type": tol.get("type", ""),
                        "grade": tol.get("grade"),
                        "upper": tol.get("upper"),
                        "lower": tol.get("lower"),
                        "component_id": component_id
                    }
                )

            # 5. Process 노드 및 관계 생성
            for proc in processes:
                await session.run(
                    """
                    MERGE (p:Process {name: $name})
                    ON CREATE SET p.estimated_time = $time, p.estimated_cost = $cost
                    WITH p
                    MATCH (c:Component {id: $component_id})
                    MERGE (c)-[:REQUIRES]->(p)
                    """,
                    {
                        "name": proc.get("name", "UNKNOWN"),
                        "time": proc.get("estimated_time"),
                        "cost": proc.get("estimated_cost"),
                        "component_id": component_id
                    }
                )

        logger.info(f"Created component {name} with ID {component_id}")
        return component_id

    async def find_similar_components(
        self,
        dimensions: List[str],
        tolerance: Optional[str] = None,
        material: Optional[str] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """유사한 컴포넌트 검색"""
        if not self._connected:
            return []

        # Cypher 쿼리: 치수, 공차, 재질이 유사한 컴포넌트 검색
        query = """
        MATCH (c:Component)-[:HAS_DIM]->(d:Dimension)
        WHERE d.value IN $dimensions
        WITH c, COUNT(d) as dim_match

        OPTIONAL MATCH (c)-[:HAS_DIM]->(:Dimension)-[:HAS_TOL]->(t:Tolerance)
        WHERE t.type = $tolerance OR $tolerance IS NULL

        OPTIONAL MATCH (c)-[:MADE_OF]->(m:Material)
        WHERE m.name = $material OR $material IS NULL

        RETURN c.id as part_id, c.name as name,
               dim_match * 1.0 / $dim_count as similarity,
               COLLECT(DISTINCT d.value) as dimensions,
               t.type as tolerance,
               m.name as material
        ORDER BY similarity DESC
        LIMIT $top_k
        """

        async with self.driver.session() as session:
            result = await session.run(
                query,
                {
                    "dimensions": dimensions,
                    "dim_count": len(dimensions) if dimensions else 1,
                    "tolerance": tolerance,
                    "material": material,
                    "top_k": top_k
                }
            )
            records = await result.data()

        return records

    async def get_component_with_cost(
        self,
        component_id: str
    ) -> Optional[Dict[str, Any]]:
        """컴포넌트 및 과거 비용 정보 조회"""
        if not self._connected:
            return None

        query = """
        MATCH (c:Component {id: $id})
        OPTIONAL MATCH (c)-[:HAS_DIM]->(d:Dimension)
        OPTIONAL MATCH (d)-[:HAS_TOL]->(t:Tolerance)
        OPTIONAL MATCH (c)-[:REQUIRES]->(p:Process)
        OPTIONAL MATCH (c)-[:MADE_OF]->(m:Material)
        OPTIONAL MATCH (c)-[:PART_OF]->(proj:Project)

        RETURN c.id as id, c.name as name,
               COLLECT(DISTINCT d.value) as dimensions,
               COLLECT(DISTINCT t.type) as tolerances,
               COLLECT(DISTINCT p.name) as processes,
               m.name as material,
               proj.cost as past_cost,
               proj.date as project_date
        """

        async with self.driver.session() as session:
            result = await session.run(query, {"id": component_id})
            records = await result.data()

        return records[0] if records else None
