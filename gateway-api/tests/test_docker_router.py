"""
Docker Router Unit Tests
subprocess_utils와 constants 모듈 테스트
"""

import pytest
from unittest.mock import patch, MagicMock


class TestSubprocessUtils:
    """Subprocess Utilities 테스트"""

    def test_run_docker_command_invalid_action(self):
        """잘못된 action에 대한 처리"""
        from utils.subprocess_utils import run_docker_command

        success, message = run_docker_command("invalid", "container")

        assert success is False
        assert "Invalid action" in message

    @patch('utils.subprocess_utils.subprocess.run')
    def test_run_docker_command_success(self, mock_run):
        """성공적인 docker 명령어 실행"""
        from utils.subprocess_utils import run_docker_command

        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        success, message = run_docker_command("start", "test-container")

        assert success is True
        assert "Successfully" in message

    @patch('utils.subprocess_utils.subprocess.run')
    def test_run_docker_command_failure(self, mock_run):
        """docker 명령어 실패 시 처리"""
        from utils.subprocess_utils import run_docker_command

        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="Error")

        success, message = run_docker_command("start", "test-container")

        assert success is False
        assert "Error" in message

    @patch('utils.subprocess_utils.subprocess.run')
    def test_get_docker_containers_parse(self, mock_run):
        """docker ps 출력 파싱 테스트"""
        from utils.subprocess_utils import get_docker_containers

        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="yolo-api\tUp 2 hours\t0.0.0.0:5005->5005/tcp\n",
            stderr=""
        )

        containers = get_docker_containers()

        assert len(containers) == 1
        assert containers[0]["name"] == "yolo-api"
        assert "Up 2 hours" in containers[0]["status"]

    @patch('utils.subprocess_utils.subprocess.run')
    def test_get_docker_containers_empty(self, mock_run):
        """빈 컨테이너 목록 테스트"""
        from utils.subprocess_utils import get_docker_containers

        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        containers = get_docker_containers()

        assert containers == []

    @patch('utils.subprocess_utils.subprocess.run')
    def test_get_docker_logs(self, mock_run):
        """docker logs 조회 테스트"""
        from utils.subprocess_utils import get_docker_logs

        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Log line 1\nLog line 2\n",
            stderr=""
        )

        logs = get_docker_logs("test-container", lines=100)

        assert "Log line 1" in logs

    @patch('utils.subprocess_utils.subprocess.run')
    def test_run_command(self, mock_run):
        """범용 명령어 실행 테스트"""
        from utils.subprocess_utils import run_command

        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="output",
            stderr=""
        )

        success, stdout, stderr = run_command(["echo", "hello"])

        assert success is True
        assert stdout == "output"


class TestConstants:
    """Constants 모듈 테스트"""

    def test_docker_service_mapping_has_yolo(self):
        """DOCKER_SERVICE_MAPPING에 yolo 포함 확인"""
        from constants import DOCKER_SERVICE_MAPPING

        assert "yolo" in DOCKER_SERVICE_MAPPING
        assert DOCKER_SERVICE_MAPPING["yolo"] == "yolo-api"

    def test_docker_service_mapping_has_all_services(self):
        """모든 주요 서비스 포함 확인"""
        from constants import DOCKER_SERVICE_MAPPING

        required = ["yolo", "edocr2", "paddleocr", "edgnet", "vl", "skinmodel"]
        for service in required:
            assert service in DOCKER_SERVICE_MAPPING

    def test_get_container_name_existing(self):
        """존재하는 서비스명 변환"""
        from constants import get_container_name

        assert get_container_name("yolo") == "yolo-api"
        assert get_container_name("edocr2") == "edocr2-v2-api"
        assert get_container_name("paddleocr") == "paddleocr-api"

    def test_get_container_name_fallback(self):
        """존재하지 않는 서비스명 fallback"""
        from constants import get_container_name

        assert get_container_name("unknown") == "unknown-api"
        assert get_container_name("custom") == "custom-api"

    def test_gpu_enabled_services(self):
        """GPU 지원 서비스 목록 확인"""
        from constants import GPU_ENABLED_SERVICES, is_gpu_enabled_service

        assert "yolo" in GPU_ENABLED_SERVICES
        assert "edocr2" in GPU_ENABLED_SERVICES
        assert is_gpu_enabled_service("yolo") is True
        assert is_gpu_enabled_service("unknown") is False

    def test_alias_mappings(self):
        """별칭 매핑 확인 (언더스코어/하이픈)"""
        from constants import DOCKER_SERVICE_MAPPING

        # 하이픈과 언더스코어 모두 동일한 컨테이너로 매핑
        assert DOCKER_SERVICE_MAPPING.get("line_detector") == DOCKER_SERVICE_MAPPING.get("line-detector")
        assert DOCKER_SERVICE_MAPPING.get("pid_analyzer") == DOCKER_SERVICE_MAPPING.get("pid-analyzer")
