"""
DAG Validator
워크플로우의 DAG 유효성을 검사하는 모듈
- 순환 참조 검증
- 고아 노드 검증
- 타입 호환성 검증
"""
import logging
from typing import Dict, List, Set, Tuple
from collections import defaultdict

from .dag_algorithms import detect_cycle, topological_sort, find_parallel_groups

logger = logging.getLogger(__name__)


class DAGValidator:
    """DAG 검증기"""

    def __init__(self, nodes: List[Dict], edges: List[Dict]):
        """
        Args:
            nodes: 노드 목록 (각각 {'id': str, 'type': str, ...})
            edges: 엣지 목록 (각각 {'source': str, 'target': str, ...})
        """
        self.nodes = {node['id']: node for node in nodes}
        self.edges = edges
        self.adjacency_list = self._build_adjacency_list()
        self.reverse_adjacency_list = self._build_reverse_adjacency_list()

        # Debug logging
        logger.info(f"[DAGValidator] Nodes: {list(self.nodes.keys())}")
        logger.info(f"[DAGValidator] Node types: {[(n['id'], n.get('type')) for n in nodes]}")
        logger.info(f"[DAGValidator] Edges (source -> target): {[(e['source'], '->', e['target']) for e in edges]}")
        logger.info(f"[DAGValidator] Adjacency list: {self.adjacency_list}")

    def _build_adjacency_list(self) -> Dict[str, List[str]]:
        """인접 리스트 생성 (노드 -> [자식 노드들])"""
        adj = defaultdict(list)
        for edge in self.edges:
            adj[edge['source']].append(edge['target'])
        return dict(adj)

    def _build_reverse_adjacency_list(self) -> Dict[str, List[str]]:
        """역 인접 리스트 생성 (노드 -> [부모 노드들])"""
        rev_adj = defaultdict(list)
        for edge in self.edges:
            rev_adj[edge['target']].append(edge['source'])
        return dict(rev_adj)

    def validate_all(self) -> Tuple[bool, List[str]]:
        """
        모든 검증 수행

        Returns:
            (is_valid, error_messages)
        """
        errors = []

        # 1. 순환 참조 검사
        has_cycle, cycle_nodes = detect_cycle(self.nodes, self.adjacency_list)
        if has_cycle:
            errors.append(f"순환 참조가 발견되었습니다: {' -> '.join(cycle_nodes)}")

        # 2. 고아 노드 검사
        orphan_nodes = self.find_orphan_nodes()
        if orphan_nodes:
            errors.append(f"연결되지 않은 고아 노드: {', '.join(orphan_nodes)}")

        # 3. 루트 노드 존재 검사
        root_nodes = self.find_root_nodes()
        if not root_nodes:
            errors.append("시작 노드(루트)가 없습니다")

        # 4. 리프 노드 존재 검사
        leaf_nodes = self.find_leaf_nodes()
        if not leaf_nodes:
            errors.append("종료 노드(리프)가 없습니다")

        # 5. 엣지 유효성 검사
        invalid_edges = self.validate_edges()
        if invalid_edges:
            errors.append(f"유효하지 않은 엣지: {invalid_edges}")

        return len(errors) == 0, errors

    def find_orphan_nodes(self) -> List[str]:
        """
        고아 노드 찾기 (들어오는/나가는 엣지가 하나도 없는 노드)
        단, 단일 루트 노드나 단일 리프 노드는 제외
        """
        if len(self.nodes) == 1:
            return []

        orphans = []
        for node_id in self.nodes:
            has_incoming = node_id in self.reverse_adjacency_list
            has_outgoing = node_id in self.adjacency_list

            # 들어오고 나가는 엣지 모두 없으면 고아
            if not has_incoming and not has_outgoing:
                orphans.append(node_id)

        return orphans

    def find_root_nodes(self) -> List[str]:
        """루트 노드 찾기 (들어오는 엣지가 없는 노드)"""
        roots = []
        for node_id in self.nodes:
            if node_id not in self.reverse_adjacency_list:
                # 고아 노드가 아닌지 확인
                if node_id in self.adjacency_list or len(self.nodes) == 1:
                    roots.append(node_id)
        return roots

    def find_leaf_nodes(self) -> List[str]:
        """리프 노드 찾기 (나가는 엣지가 없는 노드)"""
        leaves = []
        for node_id in self.nodes:
            if node_id not in self.adjacency_list:
                # 고아 노드가 아닌지 확인
                if node_id in self.reverse_adjacency_list or len(self.nodes) == 1:
                    leaves.append(node_id)
        return leaves

    def validate_edges(self) -> List[str]:
        """
        엣지 유효성 검사
        - source와 target 노드가 존재하는지
        """
        invalid = []
        for edge in self.edges:
            source = edge['source']
            target = edge['target']

            if source not in self.nodes:
                invalid.append(f"엣지의 source 노드 '{source}'가 존재하지 않습니다")
            if target not in self.nodes:
                invalid.append(f"엣지의 target 노드 '{target}'가 존재하지 않습니다")
            if source == target:
                invalid.append(f"자기 자신으로의 엣지는 허용되지 않습니다: {source}")

        return invalid

    def topological_sort(self) -> List[str]:
        """
        위상 정렬 수행 (알고리즘 위임)

        Returns:
            정렬된 노드 ID 목록

        Raises:
            ValueError: 순환 참조가 있는 경우
        """
        return topological_sort(self.nodes, self.adjacency_list)

    def find_parallel_groups(self) -> List[List[str]]:
        """
        병렬 실행 가능한 노드 그룹 찾기 (알고리즘 위임)

        Returns:
            [[노드1, 노드2], [노드3], ...]
        """
        return find_parallel_groups(
            self.nodes,
            self.adjacency_list,
            self.reverse_adjacency_list
        )
