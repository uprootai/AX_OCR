"""
Standard Validator Service
ISO/ASME 규격 검증

PPT 슬라이드 13 [WHAT-4] 도메인 지식 엔진 설계:
- ISO 1101, ASME Y14.5 규격 자동 검증
- 나사, 표면조도, 재질 등 표준 규격 인식
"""

import re
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


class StandardValidator:
    """ISO/ASME 규격 검증 서비스"""

    def __init__(self):
        # ISO 공차 등급 테이블 (IT 등급)
        self.iso_tolerance_grades = {
            "IT01": 0.3, "IT0": 0.5, "IT1": 0.8,
            "IT2": 1.2, "IT3": 2, "IT4": 3,
            "IT5": 4, "IT6": 6, "IT7": 10,
            "IT8": 14, "IT9": 25, "IT10": 40,
            "IT11": 60, "IT12": 100, "IT13": 140,
            "IT14": 250, "IT15": 400, "IT16": 600,
            "IT17": 1000, "IT18": 1500
        }

        # ISO 구멍 기준 공차 (대문자)
        self.hole_tolerance_symbols = [
            "A", "B", "C", "CD", "D", "E", "EF", "F", "FG", "G",
            "H", "J", "JS", "K", "M", "N", "P", "R", "S", "T",
            "U", "V", "X", "Y", "Z", "ZA", "ZB", "ZC"
        ]

        # ISO 축 기준 공차 (소문자)
        self.shaft_tolerance_symbols = [
            "a", "b", "c", "cd", "d", "e", "ef", "f", "fg", "g",
            "h", "j", "js", "k", "m", "n", "p", "r", "s", "t",
            "u", "v", "x", "y", "z", "za", "zb", "zc"
        ]

        # GD&T 기호 (ISO 1101 / ASME Y14.5)
        self.gdt_symbols = {
            "⏊": "perpendicularity",
            "∥": "parallelism",
            "⌒": "circularity",
            "⌭": "cylindricity",
            "◎": "concentricity",
            "⌖": "position",
            "↗": "angularity",
            "⏤": "flatness",
            "⌓": "straightness",
            "⊚": "circular_runout",
            "⊛": "total_runout",
            "⬒": "symmetry",
            "⏥": "profile_line",
            "⌓": "profile_surface"
        }

        # 표면조도 규격 (ISO 4287)
        self.surface_finish_grades = {
            "N1": 0.025, "N2": 0.05, "N3": 0.1, "N4": 0.2,
            "N5": 0.4, "N6": 0.8, "N7": 1.6, "N8": 3.2,
            "N9": 6.3, "N10": 12.5, "N11": 25, "N12": 50
        }

        # 나사 규격
        self.thread_standards = {
            "metric": r"M(\d+(?:\.\d+)?)(x(\d+(?:\.\d+)?))?",  # M10, M10x1.5
            "unc": r"(\d+/?\d*)-(\d+)\s*UNC",  # 1/4-20 UNC
            "unf": r"(\d+/?\d*)-(\d+)\s*UNF",  # 1/4-28 UNF
            "bsp": r"G(\d+/?\d*)",  # G1/4
            "npt": r"(\d+/?\d*)\s*NPT",  # 1/4 NPT
        }

        logger.info("Standard Validator initialized")

    async def validate(
        self,
        dimension: Optional[str] = None,
        tolerance: Optional[str] = None,
        gdt_symbol: Optional[str] = None,
        surface_finish: Optional[str] = None,
        thread_spec: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        규격 검증 수행

        Args:
            dimension: 치수 값 (예: "50")
            tolerance: 공차 (예: "H7", "±0.1")
            gdt_symbol: GD&T 기호 (예: "⏊0.05")
            surface_finish: 표면조도 (예: "Ra1.6")
            thread_spec: 나사 규격 (예: "M10x1.5")

        Returns:
            검증 결과 (is_valid, errors, warnings, suggestions, matched_standards)
        """
        result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "suggestions": [],
            "matched_standards": []
        }

        # 공차 검증
        if tolerance:
            tol_result = self._validate_tolerance(tolerance, dimension)
            self._merge_result(result, tol_result)

        # GD&T 검증
        if gdt_symbol:
            gdt_result = self._validate_gdt(gdt_symbol)
            self._merge_result(result, gdt_result)

        # 표면조도 검증
        if surface_finish:
            sf_result = self._validate_surface_finish(surface_finish)
            self._merge_result(result, sf_result)

        # 나사 규격 검증
        if thread_spec:
            thread_result = self._validate_thread(thread_spec)
            self._merge_result(result, thread_result)

        return result

    def _validate_tolerance(
        self,
        tolerance: str,
        dimension: Optional[str]
    ) -> Dict[str, Any]:
        """ISO 공차 검증"""
        result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "suggestions": [],
            "matched_standards": []
        }

        # ISO fit tolerance 패턴 (H7, g6 등)
        fit_pattern = r"([A-Za-z]{1,2})(\d{1,2})"
        match = re.match(fit_pattern, tolerance)

        if match:
            symbol, grade = match.groups()
            grade_num = int(grade)

            # 기호 검증
            if symbol.upper() in [s.upper() for s in self.hole_tolerance_symbols]:
                result["matched_standards"].append("ISO 286-2 (구멍 기준)")
            elif symbol.lower() in self.shaft_tolerance_symbols:
                result["matched_standards"].append("ISO 286-2 (축 기준)")
            else:
                result["warnings"].append(f"비표준 공차 기호: {symbol}")

            # 등급 검증
            if 1 <= grade_num <= 18:
                result["matched_standards"].append(f"ISO IT{grade_num}")
            else:
                result["errors"].append(f"유효하지 않은 공차 등급: IT{grade_num} (IT1-IT18 범위)")
                result["is_valid"] = False

            # 정밀도 권장사항
            if grade_num <= 6:
                result["suggestions"].append(f"IT{grade_num}은 정밀 공차입니다. 연삭 또는 호닝 가공이 필요할 수 있습니다.")
            elif grade_num >= 11:
                result["suggestions"].append(f"IT{grade_num}은 거친 공차입니다. 일반 선삭/밀링으로 충분합니다.")

        # 대칭 공차 패턴 (±0.1)
        elif tolerance.startswith("±"):
            try:
                value = float(tolerance[1:])
                result["matched_standards"].append("ISO 2768 (일반 공차)")

                if value < 0.01:
                    result["warnings"].append(f"±{value}mm는 매우 정밀한 공차입니다.")
                elif value > 1.0:
                    result["suggestions"].append(f"±{value}mm는 느슨한 공차입니다.")

            except ValueError:
                result["errors"].append(f"공차 값 파싱 실패: {tolerance}")
                result["is_valid"] = False

        else:
            result["warnings"].append(f"인식되지 않은 공차 형식: {tolerance}")

        return result

    def _validate_gdt(self, gdt_symbol: str) -> Dict[str, Any]:
        """GD&T 기호 검증 (ISO 1101 / ASME Y14.5)"""
        result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "suggestions": [],
            "matched_standards": []
        }

        # GD&T 기호 + 공차값 분리
        symbol = gdt_symbol[0] if gdt_symbol else ""
        value_str = gdt_symbol[1:] if len(gdt_symbol) > 1 else ""

        if symbol in self.gdt_symbols:
            gdt_type = self.gdt_symbols[symbol]
            result["matched_standards"].append(f"ISO 1101 ({gdt_type})")
            result["matched_standards"].append(f"ASME Y14.5 ({gdt_type})")

            # 공차값 검증
            try:
                if value_str:
                    value = float(value_str)
                    if value <= 0:
                        result["errors"].append("GD&T 공차값은 양수여야 합니다.")
                        result["is_valid"] = False
                    elif value < 0.005:
                        result["warnings"].append(f"{gdt_type} {value}mm는 매우 정밀한 공차입니다.")
            except ValueError:
                pass

        else:
            # 텍스트 기반 GD&T 검색
            gdt_keywords = {
                "perpendicularity": "직각도",
                "parallelism": "평행도",
                "circularity": "진원도",
                "cylindricity": "원통도",
                "position": "위치도",
                "flatness": "평면도",
                "straightness": "진직도",
                "runout": "흔들림"
            }

            found = False
            for key, korean in gdt_keywords.items():
                if key in gdt_symbol.lower() or korean in gdt_symbol:
                    result["matched_standards"].append(f"ISO 1101 ({key})")
                    found = True
                    break

            if not found:
                result["warnings"].append(f"인식되지 않은 GD&T 기호: {gdt_symbol}")

        return result

    def _validate_surface_finish(self, surface_finish: str) -> Dict[str, Any]:
        """표면조도 검증 (ISO 4287)"""
        result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "suggestions": [],
            "matched_standards": []
        }

        # Ra 패턴 (Ra1.6, Ra 3.2 등)
        ra_pattern = r"Ra\s*(\d+(?:\.\d+)?)"
        match = re.search(ra_pattern, surface_finish, re.IGNORECASE)

        if match:
            ra_value = float(match.group(1))
            result["matched_standards"].append("ISO 4287 (표면조도)")

            # 가공 방법 제안
            if ra_value <= 0.8:
                result["suggestions"].append(f"Ra{ra_value}μm: 연삭, 호닝, 래핑 가공 권장")
            elif ra_value <= 3.2:
                result["suggestions"].append(f"Ra{ra_value}μm: 정밀 선삭/밀링 가공 권장")
            elif ra_value <= 12.5:
                result["suggestions"].append(f"Ra{ra_value}μm: 일반 선삭/밀링 가공 가능")
            else:
                result["suggestions"].append(f"Ra{ra_value}μm: 황삭 수준, 후가공 불필요")

        # N등급 패턴 (N7 등)
        n_pattern = r"N(\d{1,2})"
        n_match = re.search(n_pattern, surface_finish)
        if n_match:
            n_grade = f"N{n_match.group(1)}"
            if n_grade in self.surface_finish_grades:
                ra_equiv = self.surface_finish_grades[n_grade]
                result["matched_standards"].append(f"ISO 1302 ({n_grade} = Ra{ra_equiv}μm)")

        if not match and not n_match:
            result["warnings"].append(f"인식되지 않은 표면조도 형식: {surface_finish}")

        return result

    def _validate_thread(self, thread_spec: str) -> Dict[str, Any]:
        """나사 규격 검증"""
        result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "suggestions": [],
            "matched_standards": []
        }

        # Metric 나사 (M10, M10x1.5)
        metric_match = re.match(self.thread_standards["metric"], thread_spec)
        if metric_match:
            diameter = float(metric_match.group(1))
            pitch = metric_match.group(3)

            result["matched_standards"].append("ISO 68-1 (Metric Thread)")

            if pitch:
                result["suggestions"].append(f"M{diameter}x{pitch} 가는 피치 나사")
            else:
                result["suggestions"].append(f"M{diameter} 보통 피치 나사")

            return result

        # UNC 나사
        unc_match = re.match(self.thread_standards["unc"], thread_spec, re.IGNORECASE)
        if unc_match:
            result["matched_standards"].append("ASME B1.1 (Unified National Coarse)")
            return result

        # UNF 나사
        unf_match = re.match(self.thread_standards["unf"], thread_spec, re.IGNORECASE)
        if unf_match:
            result["matched_standards"].append("ASME B1.1 (Unified National Fine)")
            return result

        result["warnings"].append(f"인식되지 않은 나사 규격: {thread_spec}")
        return result

    def _merge_result(
        self,
        target: Dict[str, Any],
        source: Dict[str, Any]
    ):
        """결과 병합"""
        if not source["is_valid"]:
            target["is_valid"] = False
        target["errors"].extend(source["errors"])
        target["warnings"].extend(source["warnings"])
        target["suggestions"].extend(source["suggestions"])
        target["matched_standards"].extend(source["matched_standards"])
