"""SessionService cache behavior tests."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.session_service import SessionService


def test_list_sessions_by_project_tracks_project_updates(tmp_path):
    upload_dir = tmp_path / "uploads"
    results_dir = tmp_path / "results"
    service = SessionService(upload_dir, results_dir)

    service.create_session(
        session_id="session-a",
        filename="a.png",
        file_path=str(upload_dir / "session-a" / "original.png"),
        project_id="project-1",
    )
    service.create_session(
        session_id="session-b",
        filename="b.png",
        file_path=str(upload_dir / "session-b" / "original.png"),
        project_id="project-2",
    )

    assert [s["session_id"] for s in service.list_sessions_by_project("project-1")] == ["session-a"]

    service.update_session("session-a", {"project_id": "project-2"})

    assert service.list_sessions_by_project("project-1") == []
    assert {
        session["session_id"]
        for session in service.list_sessions_by_project("project-2")
    } == {"session-a", "session-b"}


def test_list_sessions_returns_response_copies_without_transient_image_data(tmp_path):
    upload_dir = tmp_path / "uploads"
    results_dir = tmp_path / "results"
    service = SessionService(upload_dir, results_dir)

    service.create_session(
        session_id="session-a",
        filename="a.png",
        file_path=str(upload_dir / "session-a" / "original.png"),
    )
    service.sessions["session-a"]["image_base64"] = "cached-image"

    listed_sessions = service.list_sessions(limit=1)

    assert "image_base64" not in listed_sessions[0]
    assert service.get_session("session-a")["image_base64"] == "cached-image"
