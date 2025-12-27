"""리비전 비교 서비스 테스트

revision_comparator.py 단위 테스트
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
import numpy as np

from services.revision_comparator import (
    RevisionComparator,
    RevisionChange,
    ComparisonResult,
    ChangeType,
    ChangeCategory,
    Severity,
    revision_comparator,
)


class TestRevisionComparator:
    """RevisionComparator 클래스 테스트"""

    def test_singleton_instance(self):
        """싱글톤 인스턴스 확인"""
        assert revision_comparator is not None
        assert isinstance(revision_comparator, RevisionComparator)

    def test_change_type_enum(self):
        """ChangeType enum 테스트"""
        assert ChangeType.ADDED.value == "added"
        assert ChangeType.REMOVED.value == "removed"
        assert ChangeType.MODIFIED.value == "modified"
        assert ChangeType.MOVED.value == "moved"

    def test_change_category_enum(self):
        """ChangeCategory enum 테스트"""
        assert ChangeCategory.DIMENSION.value == "dimension"
        assert ChangeCategory.SYMBOL.value == "symbol"
        assert ChangeCategory.NOTE.value == "note"
        assert ChangeCategory.GEOMETRY.value == "geometry"

    def test_severity_enum(self):
        """Severity enum 테스트"""
        assert Severity.CRITICAL.value == "critical"
        assert Severity.WARNING.value == "warning"
        assert Severity.INFO.value == "info"


class TestSymbolComparison:
    """심볼 비교 테스트"""

    def setup_method(self):
        self.comparator = RevisionComparator()

    def test_compare_symbols_added(self):
        """심볼 추가 감지"""
        symbols_old = []
        symbols_new = [
            {"id": "sym1", "class_name": "weld", "bbox": [100, 100, 150, 150], "confidence": 0.9}
        ]

        changes = self.comparator._compare_symbols(symbols_old, symbols_new)

        assert len(changes) == 1
        assert changes[0].change_type == ChangeType.ADDED
        assert changes[0].category == ChangeCategory.SYMBOL
        assert "weld" in changes[0].description

    def test_compare_symbols_removed(self):
        """심볼 삭제 감지"""
        symbols_old = [
            {"id": "sym1", "class_name": "bolt", "bbox": [100, 100, 150, 150], "confidence": 0.85}
        ]
        symbols_new = []

        changes = self.comparator._compare_symbols(symbols_old, symbols_new)

        assert len(changes) == 1
        assert changes[0].change_type == ChangeType.REMOVED
        assert changes[0].category == ChangeCategory.SYMBOL
        assert "bolt" in changes[0].description

    def test_compare_symbols_modified(self):
        """심볼 수정 감지"""
        symbols_old = [
            {"id": "sym1", "class_name": "bolt", "bbox": [100, 100, 150, 150], "confidence": 0.85}
        ]
        symbols_new = [
            {"id": "sym1", "class_name": "nut", "bbox": [100, 100, 150, 150], "confidence": 0.9}
        ]

        changes = self.comparator._compare_symbols(symbols_old, symbols_new)

        assert len(changes) == 1
        assert changes[0].change_type == ChangeType.MODIFIED
        assert "bolt" in changes[0].old_value
        assert "nut" in changes[0].new_value

    def test_compare_symbols_unchanged(self):
        """심볼 변경 없음"""
        symbols = [
            {"id": "sym1", "class_name": "weld", "bbox": [100, 100, 150, 150], "confidence": 0.9}
        ]

        changes = self.comparator._compare_symbols(symbols, symbols)

        assert len(changes) == 0


class TestDimensionComparison:
    """치수 비교 테스트"""

    def setup_method(self):
        self.comparator = RevisionComparator()

    def test_compare_dimensions_added(self):
        """치수 추가 감지"""
        dims_old = []
        dims_new = [
            {"value": "25mm", "bbox": [200, 200, 250, 220], "confidence": 0.95}
        ]

        changes = self.comparator._compare_dimensions(dims_old, dims_new)

        assert len(changes) == 1
        assert changes[0].change_type == ChangeType.ADDED
        assert changes[0].category == ChangeCategory.DIMENSION
        assert changes[0].severity == Severity.CRITICAL
        assert "25mm" in changes[0].description

    def test_compare_dimensions_removed(self):
        """치수 삭제 감지"""
        dims_old = [
            {"value": "10mm", "bbox": [200, 200, 250, 220], "confidence": 0.95}
        ]
        dims_new = []

        changes = self.comparator._compare_dimensions(dims_old, dims_new)

        assert len(changes) == 1
        assert changes[0].change_type == ChangeType.REMOVED
        assert changes[0].category == ChangeCategory.DIMENSION
        assert "10mm" in changes[0].old_value


class TestNoteComparison:
    """노트 비교 테스트"""

    def setup_method(self):
        self.comparator = RevisionComparator()

    def test_compare_notes_added(self):
        """노트 추가 감지"""
        notes_old = {"notes": []}
        notes_new = {
            "notes": [
                {"text": "재질: SUS304", "category": "material", "confidence": 0.9}
            ]
        }

        changes = self.comparator._compare_notes(notes_old, notes_new)

        assert len(changes) >= 1
        added_notes = [c for c in changes if c.change_type == ChangeType.ADDED]
        assert len(added_notes) >= 1

    def test_compare_notes_removed(self):
        """노트 삭제 감지"""
        notes_old = {
            "notes": [
                {"text": "열처리: HRC 58-62", "category": "heat_treatment", "confidence": 0.85}
            ]
        }
        notes_new = {"notes": []}

        changes = self.comparator._compare_notes(notes_old, notes_new)

        assert len(changes) >= 1
        removed_notes = [c for c in changes if c.change_type == ChangeType.REMOVED]
        assert len(removed_notes) >= 1


class TestDeduplication:
    """중복 제거 테스트"""

    def setup_method(self):
        self.comparator = RevisionComparator()

    def test_deduplicate_changes(self):
        """중복 변경 제거"""
        changes = [
            RevisionChange(
                id="1",
                change_type=ChangeType.ADDED,
                category=ChangeCategory.SYMBOL,
                description="심볼 추가",
            ),
            RevisionChange(
                id="2",
                change_type=ChangeType.ADDED,
                category=ChangeCategory.SYMBOL,
                description="심볼 추가",  # 중복
            ),
            RevisionChange(
                id="3",
                change_type=ChangeType.REMOVED,
                category=ChangeCategory.SYMBOL,
                description="심볼 삭제",
            ),
        ]

        unique = self.comparator._deduplicate_changes(changes)

        assert len(unique) == 2  # 중복 제거됨


class TestCountByField:
    """필드별 카운트 테스트"""

    def setup_method(self):
        self.comparator = RevisionComparator()

    def test_count_by_change_type(self):
        """변경 타입별 카운트"""
        changes = [
            RevisionChange(id="1", change_type=ChangeType.ADDED, category=ChangeCategory.SYMBOL, description=""),
            RevisionChange(id="2", change_type=ChangeType.ADDED, category=ChangeCategory.DIMENSION, description=""),
            RevisionChange(id="3", change_type=ChangeType.REMOVED, category=ChangeCategory.NOTE, description=""),
        ]

        counts = self.comparator._count_by_field(changes, "change_type")

        assert counts["added"] == 2
        assert counts["removed"] == 1

    def test_count_by_category(self):
        """카테고리별 카운트"""
        changes = [
            RevisionChange(id="1", change_type=ChangeType.ADDED, category=ChangeCategory.SYMBOL, description=""),
            RevisionChange(id="2", change_type=ChangeType.ADDED, category=ChangeCategory.DIMENSION, description=""),
            RevisionChange(id="3", change_type=ChangeType.ADDED, category=ChangeCategory.SYMBOL, description=""),
        ]

        counts = self.comparator._count_by_field(changes, "category")

        assert counts["symbol"] == 2
        assert counts["dimension"] == 1


class TestCompareRevisions:
    """전체 비교 테스트"""

    def setup_method(self):
        self.comparator = RevisionComparator()

    @pytest.mark.asyncio
    async def test_compare_revisions_basic(self):
        """기본 비교 테스트"""
        session_old = {
            "session_id": "old-session",
            "symbols": [
                {"id": "sym1", "class_name": "weld", "confidence": 0.9}
            ],
            "dimensions": [
                {"value": "10mm", "confidence": 0.95}
            ],
            "notes_extraction": {"notes": []}
        }
        session_new = {
            "session_id": "new-session",
            "symbols": [
                {"id": "sym1", "class_name": "weld", "confidence": 0.9},
                {"id": "sym2", "class_name": "bolt", "confidence": 0.85}
            ],
            "dimensions": [
                {"value": "10mm", "confidence": 0.95},
                {"value": "25mm", "confidence": 0.9}
            ],
            "notes_extraction": {"notes": []}
        }

        result = await self.comparator.compare_revisions(session_old, session_new)

        assert isinstance(result, ComparisonResult)
        assert result.session_id_old == "old-session"
        assert result.session_id_new == "new-session"
        assert result.total_changes >= 2  # 최소 심볼 1개 + 치수 1개 추가
        assert result.added_count >= 2

    @pytest.mark.asyncio
    async def test_compare_revisions_empty_sessions(self):
        """빈 세션 비교"""
        session_old = {"session_id": "old"}
        session_new = {"session_id": "new"}

        result = await self.comparator.compare_revisions(session_old, session_new)

        assert result.total_changes == 0
        assert result.added_count == 0
        assert result.removed_count == 0


class TestVLMParsing:
    """VLM 응답 파싱 테스트"""

    def setup_method(self):
        self.comparator = RevisionComparator()

    def test_parse_vlm_response_valid(self):
        """유효한 VLM 응답 파싱"""
        content = '''
        Here is the analysis:
        {
            "changes": [
                {
                    "change_type": "modified",
                    "category": "dimension",
                    "description": "치수 변경: 10mm → 12mm",
                    "old_value": "10mm",
                    "new_value": "12mm",
                    "severity": "critical"
                }
            ],
            "summary": "1개 치수 변경"
        }
        '''

        changes = self.comparator._parse_vlm_response(content)

        assert len(changes) == 1
        assert changes[0].change_type == ChangeType.MODIFIED
        assert changes[0].category == ChangeCategory.DIMENSION
        assert changes[0].old_value == "10mm"
        assert changes[0].new_value == "12mm"

    def test_parse_vlm_response_invalid(self):
        """잘못된 VLM 응답 처리"""
        content = "This is not valid JSON"

        changes = self.comparator._parse_vlm_response(content)

        assert len(changes) == 0  # 에러 시 빈 리스트


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
