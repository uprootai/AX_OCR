"""
워크플로우 스키마 테스트
"""
import pytest
from blueprintflow.schemas.workflow import (
    WorkflowNode,
    WorkflowEdge,
    WorkflowDefinition,
    WorkflowExecutionRequest,
    NodeExecutionStatus,
    WorkflowExecutionResponse
)


class TestWorkflowNode:
    """WorkflowNode 모델 테스트"""

    def test_create_basic_node(self):
        """기본 노드 생성 테스트"""
        node = WorkflowNode(id="node1", type="yolo")
        assert node.id == "node1"
        assert node.type == "yolo"
        assert node.parameters == {}
        assert node.label is None

    def test_create_node_with_parameters(self):
        """파라미터가 있는 노드 생성 테스트"""
        node = WorkflowNode(
            id="node1",
            type="yolo",
            label="YOLO Detection",
            parameters={"confidence": 0.5, "model_type": "detect"}
        )
        assert node.parameters["confidence"] == 0.5
        assert node.label == "YOLO Detection"

    def test_node_with_position(self):
        """위치 정보가 있는 노드 테스트"""
        node = WorkflowNode(
            id="node1",
            type="edocr2",
            position={"x": 100, "y": 200}
        )
        assert node.position["x"] == 100
        assert node.position["y"] == 200


class TestWorkflowEdge:
    """WorkflowEdge 모델 테스트"""

    def test_create_basic_edge(self):
        """기본 엣지 생성 테스트"""
        edge = WorkflowEdge(id="edge1", source="node1", target="node2")
        assert edge.id == "edge1"
        assert edge.source == "node1"
        assert edge.target == "node2"

    def test_edge_with_handles(self):
        """핸들 정보가 있는 엣지 테스트"""
        edge = WorkflowEdge(
            id="edge1",
            source="node1",
            target="node2",
            sourceHandle="output",
            targetHandle="input"
        )
        assert edge.sourceHandle == "output"
        assert edge.targetHandle == "input"

    def test_edge_with_condition(self):
        """조건부 엣지 테스트"""
        edge = WorkflowEdge(
            id="edge1",
            source="if1",
            target="node2",
            condition={"branch": "true"}
        )
        assert edge.condition["branch"] == "true"


class TestWorkflowDefinition:
    """WorkflowDefinition 모델 테스트"""

    def test_create_simple_workflow(self):
        """간단한 워크플로우 생성 테스트"""
        workflow = WorkflowDefinition(
            name="Test Workflow",
            nodes=[
                WorkflowNode(id="node1", type="imageinput"),
                WorkflowNode(id="node2", type="yolo"),
            ],
            edges=[
                WorkflowEdge(id="edge1", source="node1", target="node2")
            ]
        )
        assert workflow.name == "Test Workflow"
        assert len(workflow.nodes) == 2
        assert len(workflow.edges) == 1
        assert workflow.version == "1.0.0"

    def test_workflow_with_description(self):
        """설명이 있는 워크플로우 테스트"""
        workflow = WorkflowDefinition(
            name="Test",
            description="This is a test workflow",
            nodes=[WorkflowNode(id="n1", type="test")],
            edges=[]
        )
        assert workflow.description == "This is a test workflow"

    def test_workflow_empty_nodes_raises_error(self):
        """빈 노드 목록 시 에러 발생 테스트"""
        with pytest.raises(ValueError, match="최소 1개 이상의 노드"):
            WorkflowDefinition(name="Empty", nodes=[], edges=[])

    def test_workflow_duplicate_node_ids_raises_error(self):
        """중복된 노드 ID 시 에러 발생 테스트"""
        with pytest.raises(ValueError, match="노드 ID는 중복될 수 없습니다"):
            WorkflowDefinition(
                name="Duplicate",
                nodes=[
                    WorkflowNode(id="node1", type="test"),
                    WorkflowNode(id="node1", type="test2"),
                ],
                edges=[]
            )


class TestWorkflowExecutionRequest:
    """WorkflowExecutionRequest 모델 테스트"""

    def test_create_execution_request(self):
        """실행 요청 생성 테스트"""
        workflow = WorkflowDefinition(
            name="Test",
            nodes=[WorkflowNode(id="n1", type="test")],
            edges=[]
        )
        request = WorkflowExecutionRequest(
            workflow=workflow,
            inputs={"image": "base64data"}
        )
        assert request.inputs["image"] == "base64data"
        assert request.config == {}


class TestNodeExecutionStatus:
    """NodeExecutionStatus 모델 테스트"""

    def test_create_pending_status(self):
        """대기 중 상태 생성 테스트"""
        status = NodeExecutionStatus(node_id="node1", status="pending")
        assert status.status == "pending"
        assert status.progress == 0.0

    def test_create_completed_status(self):
        """완료 상태 생성 테스트"""
        status = NodeExecutionStatus(
            node_id="node1",
            status="completed",
            progress=1.0,
            output={"result": "success"}
        )
        assert status.status == "completed"
        assert status.progress == 1.0
        assert status.output["result"] == "success"

    def test_create_failed_status(self):
        """실패 상태 생성 테스트"""
        status = NodeExecutionStatus(
            node_id="node1",
            status="failed",
            error="Connection timeout"
        )
        assert status.status == "failed"
        assert status.error == "Connection timeout"


class TestWorkflowExecutionResponse:
    """WorkflowExecutionResponse 모델 테스트"""

    def test_create_running_response(self):
        """실행 중 응답 생성 테스트"""
        response = WorkflowExecutionResponse(
            execution_id="exec-123",
            status="running",
            workflow_name="Test",
            node_statuses=[]
        )
        assert response.execution_id == "exec-123"
        assert response.status == "running"

    def test_create_completed_response(self):
        """완료 응답 생성 테스트"""
        response = WorkflowExecutionResponse(
            execution_id="exec-123",
            status="completed",
            workflow_name="Test",
            node_statuses=[
                NodeExecutionStatus(node_id="n1", status="completed", progress=1.0)
            ],
            final_output={"detections": []},
            execution_time_ms=1500.5
        )
        assert response.status == "completed"
        assert response.final_output["detections"] == []
        assert response.execution_time_ms == 1500.5
