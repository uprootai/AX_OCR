"""Connectivity Analyzer Service - P&ID 심볼 연결 분석 서비스

P&ID 도면에서 심볼 간의 연결 관계를 분석하고 연결 그래프를 구성합니다.
Line Detector 결과와 심볼 검출 결과를 결합하여 배관/배선 연결을 추적합니다.
"""
import math
import uuid
import logging
from typing import Dict, Any, List, Optional, Tuple, Set
from collections import defaultdict
from dataclasses import dataclass, field

from schemas.line import Line, Intersection, Point, LineType

logger = logging.getLogger(__name__)


@dataclass
class SymbolNode:
    """연결 그래프의 심볼 노드"""
    id: str
    class_name: str
    center: Tuple[float, float]
    bbox: Dict[str, float]
    connections: List[str] = field(default_factory=list)  # 연결된 심볼 ID
    connected_lines: List[str] = field(default_factory=list)  # 연결된 선 ID
    tag: Optional[str] = None  # 태그/라벨 (있는 경우)


@dataclass
class Connection:
    """심볼 간 연결"""
    id: str
    source_id: str
    target_id: str
    line_ids: List[str]  # 연결에 사용된 선 ID들
    connection_type: str  # 'direct', 'through_lines', 'inferred'
    confidence: float
    path_length: float  # 연결 경로 길이 (픽셀)


@dataclass
class ConnectivityGraph:
    """연결 그래프"""
    nodes: Dict[str, SymbolNode]
    connections: List[Connection]
    orphan_symbols: List[str]  # 연결되지 않은 심볼 ID
    statistics: Dict[str, Any]


class ConnectivityAnalyzer:
    """P&ID 심볼 연결 분석기"""

    def __init__(
        self,
        proximity_threshold: float = 50.0,  # 직접 연결 판단 거리 (픽셀)
        line_endpoint_threshold: float = 30.0,  # 선 끝점과 심볼 연결 거리
        max_path_length: float = 500.0,  # 최대 연결 경로 길이
    ):
        self.proximity_threshold = proximity_threshold
        self.line_endpoint_threshold = line_endpoint_threshold
        self.max_path_length = max_path_length
        logger.info(f"ConnectivityAnalyzer 초기화 (proximity={proximity_threshold}px)")

    def analyze(
        self,
        symbols: List[Dict[str, Any]],
        lines: Optional[List[Dict[str, Any]]] = None,
        intersections: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        심볼 간 연결 관계 분석

        Args:
            symbols: 심볼 검출 결과 (id, class_name, bbox 포함)
            lines: 선 검출 결과 (optional)
            intersections: 교차점 정보 (optional)

        Returns:
            연결 그래프 및 분석 결과
        """
        # 1. 심볼 노드 생성
        nodes = self._create_symbol_nodes(symbols)

        if not nodes:
            return self._empty_result()

        # 2. 연결 분석
        if lines:
            # 선 기반 연결 분석
            connections = self._analyze_line_connections(
                nodes, lines, intersections or []
            )
        else:
            # 근접성 기반 연결 분석 (선 정보 없을 때)
            connections = self._analyze_proximity_connections(nodes)

        # 3. 고립된 심볼 찾기
        connected_ids = set()
        for conn in connections:
            connected_ids.add(conn.source_id)
            connected_ids.add(conn.target_id)
        orphan_symbols = [sid for sid in nodes.keys() if sid not in connected_ids]

        # 4. 통계 계산
        statistics = self._calculate_statistics(nodes, connections, orphan_symbols)

        # 5. 결과 반환
        return {
            "nodes": {sid: self._node_to_dict(node) for sid, node in nodes.items()},
            "connections": [self._connection_to_dict(conn) for conn in connections],
            "orphan_symbols": orphan_symbols,
            "statistics": statistics,
        }

    def _create_symbol_nodes(self, symbols: List[Dict]) -> Dict[str, SymbolNode]:
        """심볼 목록을 노드로 변환"""
        nodes = {}

        for symbol in symbols:
            symbol_id = symbol.get("id", str(uuid.uuid4()))
            bbox = symbol.get("bbox", {})

            # bbox가 없거나 불완전한 경우 스킵
            if not bbox or not all(k in bbox for k in ["x1", "y1", "x2", "y2"]):
                continue

            center = (
                (bbox["x1"] + bbox["x2"]) / 2,
                (bbox["y1"] + bbox["y2"]) / 2,
            )

            nodes[symbol_id] = SymbolNode(
                id=symbol_id,
                class_name=symbol.get("class_name", "unknown"),
                center=center,
                bbox=bbox,
                tag=symbol.get("tag"),
            )

        return nodes

    def _analyze_line_connections(
        self,
        nodes: Dict[str, SymbolNode],
        lines: List[Dict],
        intersections: List[Dict],
    ) -> List[Connection]:
        """선 기반 연결 분석"""
        connections = []

        # 1. 각 심볼에 연결된 선 찾기
        symbol_lines: Dict[str, List[str]] = defaultdict(list)
        line_symbols: Dict[str, List[str]] = defaultdict(list)

        for line_data in lines:
            line_id = line_data.get("id", "")
            start = line_data.get("start", {})
            end = line_data.get("end", {})

            if not start or not end:
                continue

            start_point = (start.get("x", 0), start.get("y", 0))
            end_point = (end.get("x", 0), end.get("y", 0))

            # 선 끝점과 가까운 심볼 찾기
            for symbol_id, node in nodes.items():
                if self._is_point_near_symbol(start_point, node):
                    symbol_lines[symbol_id].append(line_id)
                    line_symbols[line_id].append(symbol_id)

                if self._is_point_near_symbol(end_point, node):
                    symbol_lines[symbol_id].append(line_id)
                    line_symbols[line_id].append(symbol_id)

        # 2. 같은 선에 연결된 심볼들을 연결
        processed_pairs: Set[Tuple[str, str]] = set()

        for line_id, connected_symbols in line_symbols.items():
            # 같은 선에 연결된 심볼 쌍
            for i, source_id in enumerate(connected_symbols):
                for target_id in connected_symbols[i+1:]:
                    pair = tuple(sorted([source_id, target_id]))
                    if pair in processed_pairs:
                        continue
                    processed_pairs.add(pair)

                    # 연결 거리 계산
                    source_node = nodes[source_id]
                    target_node = nodes[target_id]
                    path_length = self._calculate_distance(
                        source_node.center, target_node.center
                    )

                    connections.append(Connection(
                        id=str(uuid.uuid4()),
                        source_id=source_id,
                        target_id=target_id,
                        line_ids=[line_id],
                        connection_type="through_lines",
                        confidence=0.8,
                        path_length=path_length,
                    ))

                    # 노드에 연결 정보 추가
                    source_node.connections.append(target_id)
                    source_node.connected_lines.append(line_id)
                    target_node.connections.append(source_id)
                    target_node.connected_lines.append(line_id)

        # 3. 교차점을 통한 간접 연결 분석
        connections.extend(
            self._analyze_intersection_connections(
                nodes, lines, intersections, processed_pairs
            )
        )

        return connections

    def _analyze_intersection_connections(
        self,
        nodes: Dict[str, SymbolNode],
        lines: List[Dict],
        intersections: List[Dict],
        processed_pairs: Set[Tuple[str, str]],
    ) -> List[Connection]:
        """교차점을 통한 간접 연결 분석"""
        connections = []

        # 선 ID로 빠른 조회
        line_map = {l.get("id"): l for l in lines}

        for intersection in intersections:
            line_ids = intersection.get("line_ids", [])
            if len(line_ids) < 2:
                continue

            # 교차하는 선들에 연결된 심볼 찾기
            connected_symbols = set()
            for line_id in line_ids:
                line = line_map.get(line_id)
                if not line:
                    continue

                start = line.get("start", {})
                end = line.get("end", {})

                for symbol_id, node in nodes.items():
                    if (self._is_point_near_symbol(
                            (start.get("x", 0), start.get("y", 0)), node) or
                        self._is_point_near_symbol(
                            (end.get("x", 0), end.get("y", 0)), node)):
                        connected_symbols.add(symbol_id)

            # 교차점을 통해 연결된 심볼 쌍 생성
            symbol_list = list(connected_symbols)
            for i, source_id in enumerate(symbol_list):
                for target_id in symbol_list[i+1:]:
                    pair = tuple(sorted([source_id, target_id]))
                    if pair in processed_pairs:
                        continue
                    processed_pairs.add(pair)

                    source_node = nodes[source_id]
                    target_node = nodes[target_id]
                    path_length = self._calculate_distance(
                        source_node.center, target_node.center
                    )

                    # 경로가 너무 길면 스킵
                    if path_length > self.max_path_length:
                        continue

                    connections.append(Connection(
                        id=str(uuid.uuid4()),
                        source_id=source_id,
                        target_id=target_id,
                        line_ids=line_ids,
                        connection_type="through_intersection",
                        confidence=0.6,
                        path_length=path_length,
                    ))

        return connections

    def _analyze_proximity_connections(
        self,
        nodes: Dict[str, SymbolNode],
    ) -> List[Connection]:
        """근접성 기반 연결 분석 (선 정보 없을 때)"""
        connections = []
        processed_pairs: Set[Tuple[str, str]] = set()

        node_list = list(nodes.items())

        for i, (source_id, source_node) in enumerate(node_list):
            for target_id, target_node in node_list[i+1:]:
                distance = self._calculate_distance(
                    source_node.center, target_node.center
                )

                if distance <= self.proximity_threshold:
                    pair = tuple(sorted([source_id, target_id]))
                    if pair in processed_pairs:
                        continue
                    processed_pairs.add(pair)

                    confidence = max(0.3, 1.0 - (distance / self.proximity_threshold))

                    connections.append(Connection(
                        id=str(uuid.uuid4()),
                        source_id=source_id,
                        target_id=target_id,
                        line_ids=[],
                        connection_type="proximity",
                        confidence=confidence,
                        path_length=distance,
                    ))

                    source_node.connections.append(target_id)
                    target_node.connections.append(source_id)

        return connections

    def _is_point_near_symbol(
        self,
        point: Tuple[float, float],
        node: SymbolNode,
    ) -> bool:
        """점이 심볼 근처에 있는지 확인"""
        bbox = node.bbox
        margin = self.line_endpoint_threshold

        # 확장된 bbox 내에 있는지 확인
        return (
            bbox["x1"] - margin <= point[0] <= bbox["x2"] + margin and
            bbox["y1"] - margin <= point[1] <= bbox["y2"] + margin
        )

    def _calculate_distance(
        self,
        p1: Tuple[float, float],
        p2: Tuple[float, float],
    ) -> float:
        """두 점 사이 거리"""
        return math.sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2)

    def _calculate_statistics(
        self,
        nodes: Dict[str, SymbolNode],
        connections: List[Connection],
        orphan_symbols: List[str],
    ) -> Dict[str, Any]:
        """연결 통계 계산"""
        total_symbols = len(nodes)
        total_connections = len(connections)

        # 연결 수 분포
        connection_counts = defaultdict(int)
        for node in nodes.values():
            connection_counts[len(node.connections)] += 1

        # 클래스별 통계
        class_stats = defaultdict(lambda: {"count": 0, "connected": 0})
        for symbol_id, node in nodes.items():
            class_stats[node.class_name]["count"] += 1
            if node.connections:
                class_stats[node.class_name]["connected"] += 1

        # 연결 타입 분포
        connection_types = defaultdict(int)
        for conn in connections:
            connection_types[conn.connection_type] += 1

        return {
            "total_symbols": total_symbols,
            "total_connections": total_connections,
            "orphan_count": len(orphan_symbols),
            "connectivity_ratio": (
                (total_symbols - len(orphan_symbols)) / total_symbols
                if total_symbols > 0 else 0
            ),
            "avg_connections_per_symbol": (
                sum(len(n.connections) for n in nodes.values()) / total_symbols
                if total_symbols > 0 else 0
            ),
            "connection_distribution": dict(connection_counts),
            "class_statistics": dict(class_stats),
            "connection_type_distribution": dict(connection_types),
        }

    def _node_to_dict(self, node: SymbolNode) -> Dict[str, Any]:
        """SymbolNode를 dict로 변환"""
        return {
            "id": node.id,
            "class_name": node.class_name,
            "center": {"x": node.center[0], "y": node.center[1]},
            "bbox": node.bbox,
            "connections": node.connections,
            "connected_lines": node.connected_lines,
            "tag": node.tag,
        }

    def _connection_to_dict(self, conn: Connection) -> Dict[str, Any]:
        """Connection을 dict로 변환"""
        return {
            "id": conn.id,
            "source_id": conn.source_id,
            "target_id": conn.target_id,
            "line_ids": conn.line_ids,
            "connection_type": conn.connection_type,
            "confidence": conn.confidence,
            "path_length": conn.path_length,
        }

    def _empty_result(self) -> Dict[str, Any]:
        """빈 결과"""
        return {
            "nodes": {},
            "connections": [],
            "orphan_symbols": [],
            "statistics": {
                "total_symbols": 0,
                "total_connections": 0,
                "orphan_count": 0,
                "connectivity_ratio": 0,
                "avg_connections_per_symbol": 0,
            },
        }

    def find_path(
        self,
        graph: Dict[str, Any],
        source_id: str,
        target_id: str,
    ) -> Optional[List[str]]:
        """
        두 심볼 사이의 연결 경로 찾기 (BFS)

        Args:
            graph: analyze() 결과
            source_id: 시작 심볼 ID
            target_id: 목표 심볼 ID

        Returns:
            경로 (심볼 ID 목록) 또는 None
        """
        nodes = graph.get("nodes", {})
        if source_id not in nodes or target_id not in nodes:
            return None

        # BFS
        from collections import deque

        queue = deque([(source_id, [source_id])])
        visited = {source_id}

        while queue:
            current, path = queue.popleft()

            if current == target_id:
                return path

            node = nodes.get(current, {})
            for neighbor in node.get("connections", []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))

        return None  # 경로 없음

    def get_connected_component(
        self,
        graph: Dict[str, Any],
        symbol_id: str,
    ) -> List[str]:
        """
        심볼이 속한 연결 컴포넌트의 모든 심볼 ID 반환

        Args:
            graph: analyze() 결과
            symbol_id: 시작 심볼 ID

        Returns:
            연결된 심볼 ID 목록
        """
        nodes = graph.get("nodes", {})
        if symbol_id not in nodes:
            return []

        # DFS
        visited = set()
        stack = [symbol_id]

        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)

            node = nodes.get(current, {})
            for neighbor in node.get("connections", []):
                if neighbor not in visited:
                    stack.append(neighbor)

        return list(visited)
