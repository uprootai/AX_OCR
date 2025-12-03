"""
DAG Validator 테스트
"""
import pytest
from blueprintflow.validators.dag_validator import DAGValidator


class TestDAGValidatorBasics:
    """DAGValidator 기본 기능 테스트"""

    def test_simple_linear_workflow(self):
        """선형 워크플로우 검증 테스트"""
        nodes = [
            {"id": "node1", "type": "imageinput"},
            {"id": "node2", "type": "yolo"},
            {"id": "node3", "type": "edocr2"},
        ]
        edges = [
            {"source": "node1", "target": "node2"},
            {"source": "node2", "target": "node3"},
        ]

        validator = DAGValidator(nodes, edges)
        is_valid, errors = validator.validate_all()

        assert is_valid is True
        assert errors == []

    def test_single_node_workflow(self):
        """단일 노드 워크플로우 검증"""
        nodes = [{"id": "node1", "type": "imageinput"}]
        edges = []

        validator = DAGValidator(nodes, edges)
        is_valid, errors = validator.validate_all()

        assert is_valid is True

    def test_parallel_branches(self):
        """병렬 분기 워크플로우 검증"""
        nodes = [
            {"id": "input", "type": "imageinput"},
            {"id": "yolo", "type": "yolo"},
            {"id": "edgnet", "type": "edgnet"},
            {"id": "merge", "type": "merge"},
        ]
        edges = [
            {"source": "input", "target": "yolo"},
            {"source": "input", "target": "edgnet"},
            {"source": "yolo", "target": "merge"},
            {"source": "edgnet", "target": "merge"},
        ]

        validator = DAGValidator(nodes, edges)
        is_valid, errors = validator.validate_all()

        assert is_valid is True


class TestDAGValidatorCycleDetection:
    """순환 참조 검출 테스트"""

    def test_direct_cycle(self):
        """직접 순환 검출"""
        nodes = [
            {"id": "node1", "type": "test"},
            {"id": "node2", "type": "test"},
        ]
        edges = [
            {"source": "node1", "target": "node2"},
            {"source": "node2", "target": "node1"},
        ]

        validator = DAGValidator(nodes, edges)
        is_valid, errors = validator.validate_all()

        assert is_valid is False
        assert any("순환 참조" in err for err in errors)

    def test_indirect_cycle(self):
        """간접 순환 검출"""
        nodes = [
            {"id": "A", "type": "test"},
            {"id": "B", "type": "test"},
            {"id": "C", "type": "test"},
        ]
        edges = [
            {"source": "A", "target": "B"},
            {"source": "B", "target": "C"},
            {"source": "C", "target": "A"},
        ]

        validator = DAGValidator(nodes, edges)
        is_valid, errors = validator.validate_all()

        assert is_valid is False
        assert any("순환 참조" in err for err in errors)


class TestDAGValidatorOrphanNodes:
    """고아 노드 검출 테스트"""

    def test_orphan_node_detection(self):
        """고아 노드 검출"""
        nodes = [
            {"id": "node1", "type": "imageinput"},
            {"id": "node2", "type": "yolo"},
            {"id": "orphan", "type": "test"},  # 연결 안 됨
        ]
        edges = [
            {"source": "node1", "target": "node2"},
        ]

        validator = DAGValidator(nodes, edges)
        orphans = validator.find_orphan_nodes()

        assert "orphan" in orphans


class TestDAGValidatorRootLeaf:
    """루트/리프 노드 테스트"""

    def test_find_root_nodes(self):
        """루트 노드 찾기"""
        nodes = [
            {"id": "root", "type": "imageinput"},
            {"id": "middle", "type": "yolo"},
            {"id": "leaf", "type": "merge"},
        ]
        edges = [
            {"source": "root", "target": "middle"},
            {"source": "middle", "target": "leaf"},
        ]

        validator = DAGValidator(nodes, edges)
        roots = validator.find_root_nodes()

        assert "root" in roots
        assert len(roots) == 1

    def test_find_leaf_nodes(self):
        """리프 노드 찾기"""
        nodes = [
            {"id": "root", "type": "imageinput"},
            {"id": "middle", "type": "yolo"},
            {"id": "leaf", "type": "merge"},
        ]
        edges = [
            {"source": "root", "target": "middle"},
            {"source": "middle", "target": "leaf"},
        ]

        validator = DAGValidator(nodes, edges)
        leaves = validator.find_leaf_nodes()

        assert "leaf" in leaves
        assert len(leaves) == 1

    def test_multiple_roots(self):
        """다중 루트 노드"""
        nodes = [
            {"id": "root1", "type": "imageinput"},
            {"id": "root2", "type": "textinput"},
            {"id": "merge", "type": "merge"},
        ]
        edges = [
            {"source": "root1", "target": "merge"},
            {"source": "root2", "target": "merge"},
        ]

        validator = DAGValidator(nodes, edges)
        roots = validator.find_root_nodes()

        assert len(roots) == 2
        assert "root1" in roots
        assert "root2" in roots


class TestDAGValidatorEdgeValidation:
    """엣지 유효성 검증 테스트"""

    def test_invalid_source_node(self):
        """존재하지 않는 소스 노드"""
        nodes = [{"id": "node1", "type": "test"}]
        edges = [{"source": "nonexistent", "target": "node1"}]

        validator = DAGValidator(nodes, edges)
        invalid = validator.validate_edges()

        assert len(invalid) > 0
        assert any("nonexistent" in err for err in invalid)

    def test_invalid_target_node(self):
        """존재하지 않는 타겟 노드"""
        nodes = [{"id": "node1", "type": "test"}]
        edges = [{"source": "node1", "target": "nonexistent"}]

        validator = DAGValidator(nodes, edges)
        invalid = validator.validate_edges()

        assert len(invalid) > 0
        assert any("nonexistent" in err for err in invalid)

    def test_self_loop_detection(self):
        """자기 자신으로의 엣지 검출"""
        nodes = [{"id": "node1", "type": "test"}]
        edges = [{"source": "node1", "target": "node1"}]

        validator = DAGValidator(nodes, edges)
        invalid = validator.validate_edges()

        assert len(invalid) > 0
        assert any("자기 자신" in err for err in invalid)


class TestDAGValidatorTopologicalSort:
    """위상 정렬 테스트"""

    def test_simple_topological_sort(self):
        """간단한 위상 정렬"""
        nodes = [
            {"id": "A", "type": "test"},
            {"id": "B", "type": "test"},
            {"id": "C", "type": "test"},
        ]
        edges = [
            {"source": "A", "target": "B"},
            {"source": "B", "target": "C"},
        ]

        validator = DAGValidator(nodes, edges)
        sorted_nodes = validator.topological_sort()

        # A가 B보다 먼저, B가 C보다 먼저
        assert sorted_nodes.index("A") < sorted_nodes.index("B")
        assert sorted_nodes.index("B") < sorted_nodes.index("C")


class TestDAGValidatorParallelGroups:
    """병렬 그룹 찾기 테스트"""

    def test_parallel_groups_simple(self):
        """병렬 그룹 찾기 - 간단한 케이스"""
        nodes = [
            {"id": "input", "type": "imageinput"},
            {"id": "yolo", "type": "yolo"},
            {"id": "edgnet", "type": "edgnet"},
            {"id": "output", "type": "merge"},
        ]
        edges = [
            {"source": "input", "target": "yolo"},
            {"source": "input", "target": "edgnet"},
            {"source": "yolo", "target": "output"},
            {"source": "edgnet", "target": "output"},
        ]

        validator = DAGValidator(nodes, edges)
        groups = validator.find_parallel_groups()

        # yolo와 edgnet은 같은 레벨에서 병렬 실행 가능해야 함
        assert len(groups) >= 1
        # input이 첫 그룹에 있어야 함
        assert "input" in groups[0]
