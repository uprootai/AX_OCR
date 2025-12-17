"""
DAG Algorithms
DAG 관련 알고리즘 구현체
- 순환 참조 탐지 (DFS)
- 위상 정렬 (Kahn's algorithm)
- 병렬 그룹 찾기 (BFS)
"""
import logging
from typing import Dict, List, Set, Tuple
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


def detect_cycle(
    nodes: Dict[str, Dict],
    adjacency_list: Dict[str, List[str]]
) -> Tuple[bool, List[str]]:
    """
    DFS를 사용한 순환 참조 탐지

    Args:
        nodes: 노드 딕셔너리
        adjacency_list: 인접 리스트

    Returns:
        (has_cycle, cycle_path)
    """
    visited = set()
    rec_stack = set()
    parent = {}

    def dfs(node: str, path: List[str]) -> Tuple[bool, List[str]]:
        visited.add(node)
        rec_stack.add(node)
        path.append(node)

        for neighbor in adjacency_list.get(node, []):
            if neighbor not in visited:
                parent[neighbor] = node
                has_cycle, cycle = dfs(neighbor, path.copy())
                if has_cycle:
                    return True, cycle
            elif neighbor in rec_stack:
                # 순환 발견: neighbor부터 현재 노드까지가 사이클
                cycle_start_idx = path.index(neighbor)
                return True, path[cycle_start_idx:] + [neighbor]

        rec_stack.remove(node)
        return False, []

    for node_id in nodes:
        if node_id not in visited:
            has_cycle, cycle = dfs(node_id, [])
            if has_cycle:
                return True, cycle

    return False, []


def topological_sort(
    nodes: Dict[str, Dict],
    adjacency_list: Dict[str, List[str]]
) -> List[str]:
    """
    위상 정렬 (Kahn's algorithm)

    Args:
        nodes: 노드 딕셔너리
        adjacency_list: 인접 리스트

    Returns:
        정렬된 노드 ID 목록

    Raises:
        ValueError: 순환 참조가 있는 경우
    """
    # 진입 차수 계산
    in_degree = {node_id: 0 for node_id in nodes}
    for node_id in nodes:
        for neighbor in adjacency_list.get(node_id, []):
            in_degree[neighbor] += 1

    logger.info(f"[TopologicalSort] In-degrees: {in_degree}")

    # 진입 차수가 0인 노드들로 시작
    queue = deque([node_id for node_id, degree in in_degree.items() if degree == 0])
    logger.info(f"[TopologicalSort] Initial queue (in_degree=0): {list(queue)}")
    result = []

    while queue:
        node = queue.popleft()
        result.append(node)
        logger.info(f"[TopologicalSort] Processing: {node}, neighbors: {adjacency_list.get(node, [])}")

        # 인접 노드의 진입 차수 감소
        for neighbor in adjacency_list.get(node, []):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
                logger.info(f"[TopologicalSort] Added to queue: {neighbor}")

    logger.info(f"[TopologicalSort] Final result: {result}")

    # 모든 노드가 정렬되지 않았다면 순환 참조 존재
    if len(result) != len(nodes):
        raise ValueError("순환 참조가 존재하여 위상 정렬을 수행할 수 없습니다")

    return result


def find_parallel_groups(
    nodes: Dict[str, Dict],
    adjacency_list: Dict[str, List[str]],
    reverse_adjacency_list: Dict[str, List[str]]
) -> List[List[str]]:
    """
    병렬 실행 가능한 노드 그룹 찾기
    같은 레벨(depth)에 있는 노드들을 그룹화

    Args:
        nodes: 노드 딕셔너리
        adjacency_list: 인접 리스트
        reverse_adjacency_list: 역 인접 리스트

    Returns:
        [[노드1, 노드2], [노드3], ...]
    """
    # 먼저 위상 정렬 실행 (순환 참조 검증)
    topological_sort(nodes, adjacency_list)

    # 루트 노드 찾기
    roots = []
    for node_id in nodes:
        if node_id not in reverse_adjacency_list:
            if node_id in adjacency_list or len(nodes) == 1:
                roots.append(node_id)

    # BFS로 레벨별 노드 그룹화
    visited = set()
    queue = deque([(root, 0) for root in roots])
    level_dict = defaultdict(list)

    while queue:
        node, level = queue.popleft()
        if node in visited:
            continue

        visited.add(node)
        level_dict[level].append(node)

        for child in adjacency_list.get(node, []):
            if child not in visited:
                queue.append((child, level + 1))

    # 레벨 순서대로 정렬
    levels = []
    for level in sorted(level_dict.keys()):
        levels.append(level_dict[level])

    return levels
