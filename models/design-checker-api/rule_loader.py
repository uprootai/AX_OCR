"""
Rule Loader - 카테고리별 YAML 규칙 로더
TECHCROSS BWMS 체크리스트 규칙 관리

구조:
config/
├── _active.yaml              # 활성화된 규칙 파일 목록
├── common/
│   └── base_rules.yaml       # 공통 규칙 (ALL)
├── ecs/
│   └── ecs_rules.yaml        # ECS 전용 규칙
├── hychlor/
│   └── hychlor_rules.yaml    # HYCHLOR 전용 규칙
└── custom/
    └── {customer}_rules.yaml # 고객사별 커스텀 규칙
"""

import logging
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# 카테고리 정의
CATEGORIES = {
    "common": "공통 규칙 (모든 시스템)",
    "ecs": "ECS 시스템 전용",
    "hychlor": "HYCHLOR 시스템 전용",
    "custom": "고객사별 커스텀 규칙"
}

DEFAULT_ACTIVE_CONFIG = {
    "version": "1.0",
    "description": "BWMS 체크리스트 규칙 활성화 설정",
    "last_updated": None,
    "active_profiles": [
        "common/base_rules.yaml",
        "ecs/ecs_rules.yaml",
        "hychlor/hychlor_rules.yaml"
    ],
    "disabled_rules": []  # 개별 규칙 비활성화
}


class RuleLoader:
    """카테고리별 YAML 규칙 로더"""

    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self._ensure_structure()

    def _ensure_structure(self):
        """폴더 구조 생성"""
        # 카테고리 폴더 생성
        for category in CATEGORIES.keys():
            (self.config_dir / category).mkdir(parents=True, exist_ok=True)

        # _active.yaml 생성 (없는 경우)
        active_file = self.config_dir / "_active.yaml"
        if not active_file.exists():
            self._save_active_config(DEFAULT_ACTIVE_CONFIG)
            logger.info("Created default _active.yaml")

    def _get_active_config(self) -> Dict[str, Any]:
        """활성화 설정 로드"""
        active_file = self.config_dir / "_active.yaml"
        if active_file.exists():
            with open(active_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or DEFAULT_ACTIVE_CONFIG
        return DEFAULT_ACTIVE_CONFIG

    def _save_active_config(self, config: Dict[str, Any]):
        """활성화 설정 저장"""
        config["last_updated"] = datetime.now().isoformat()
        active_file = self.config_dir / "_active.yaml"
        with open(active_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    def load_all_rules(self) -> Dict[str, Dict[str, Any]]:
        """
        모든 활성화된 규칙 로드

        Returns:
            Dict[rule_id, rule_dict]: 규칙 ID를 키로 하는 딕셔너리
        """
        active_config = self._get_active_config()
        all_rules = {}
        loaded_files = []
        disabled_rules = set(active_config.get("disabled_rules", []))

        for profile_path in active_config.get("active_profiles", []):
            full_path = self.config_dir / profile_path
            if full_path.exists():
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        data = yaml.safe_load(f)

                    if data and "rules" in data:
                        for rule in data["rules"]:
                            rule_id = rule.get("rule_id") or rule.get("id")
                            if rule_id and rule_id not in disabled_rules:
                                # rule_id 키 표준화
                                rule["rule_id"] = rule_id
                                rule["id"] = rule_id
                                rule["_source_file"] = profile_path
                                all_rules[rule_id] = rule

                        loaded_files.append(profile_path)
                        logger.debug(f"Loaded {len(data['rules'])} rules from {profile_path}")

                except Exception as e:
                    logger.warning(f"Failed to load {profile_path}: {e}")
            else:
                logger.debug(f"Profile not found: {profile_path}")

        logger.info(f"Loaded {len(all_rules)} rules from {len(loaded_files)} files")
        return all_rules

    def save_rules(
        self,
        rules: List[Dict[str, Any]],
        category: str,
        filename: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        규칙을 카테고리 폴더에 저장

        Args:
            rules: 규칙 목록
            category: 카테고리 (common, ecs, hychlor, custom)
            filename: 파일명 (없으면 자동 생성)
            metadata: 추가 메타데이터

        Returns:
            저장된 파일 경로
        """
        if category not in CATEGORIES:
            raise ValueError(f"Invalid category: {category}. Must be one of {list(CATEGORIES.keys())}")

        # 파일명 생성
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{category}_rules_{timestamp}.yaml"

        # 경로 생성
        file_path = self.config_dir / category / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # YAML 데이터 구성
        data = {
            "version": "1.0",
            "category": category,
            "category_description": CATEGORIES[category],
            "created_at": datetime.now().isoformat(),
            "rules_count": len(rules),
            "rules": rules
        }

        if metadata:
            data.update(metadata)

        # 저장
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

        # _active.yaml에 추가 (없는 경우)
        self._add_to_active(f"{category}/{filename}")

        logger.info(f"Saved {len(rules)} rules to {file_path}")
        return str(file_path)

    def _add_to_active(self, profile_path: str):
        """활성화 목록에 추가"""
        config = self._get_active_config()
        if profile_path not in config["active_profiles"]:
            config["active_profiles"].append(profile_path)
            self._save_active_config(config)
            logger.info(f"Added {profile_path} to active profiles")

    def remove_from_active(self, profile_path: str):
        """활성화 목록에서 제거"""
        config = self._get_active_config()
        if profile_path in config["active_profiles"]:
            config["active_profiles"].remove(profile_path)
            self._save_active_config(config)
            logger.info(f"Removed {profile_path} from active profiles")

    def disable_rule(self, rule_id: str):
        """개별 규칙 비활성화"""
        config = self._get_active_config()
        if rule_id not in config.get("disabled_rules", []):
            if "disabled_rules" not in config:
                config["disabled_rules"] = []
            config["disabled_rules"].append(rule_id)
            self._save_active_config(config)
            logger.info(f"Disabled rule: {rule_id}")

    def enable_rule(self, rule_id: str):
        """개별 규칙 활성화"""
        config = self._get_active_config()
        if rule_id in config.get("disabled_rules", []):
            config["disabled_rules"].remove(rule_id)
            self._save_active_config(config)
            logger.info(f"Enabled rule: {rule_id}")

    def get_status(self) -> Dict[str, Any]:
        """현재 상태 조회"""
        config = self._get_active_config()
        all_rules = self.load_all_rules()

        # 카테고리별 통계
        category_stats = {}
        for category in CATEGORIES.keys():
            category_dir = self.config_dir / category
            files = list(category_dir.glob("*.yaml"))
            category_stats[category] = {
                "files": len(files),
                "file_list": [f.name for f in files]
            }

        return {
            "config_dir": str(self.config_dir),
            "active_profiles": config.get("active_profiles", []),
            "disabled_rules": config.get("disabled_rules", []),
            "total_rules_loaded": len(all_rules),
            "categories": category_stats,
            "last_updated": config.get("last_updated")
        }

    def list_files(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """규칙 파일 목록 조회"""
        files = []
        categories = [category] if category else CATEGORIES.keys()

        config = self._get_active_config()
        active_profiles = set(config.get("active_profiles", []))

        for cat in categories:
            cat_dir = self.config_dir / cat
            if cat_dir.exists():
                for f in cat_dir.glob("*.yaml"):
                    profile_path = f"{cat}/{f.name}"
                    try:
                        with open(f, 'r', encoding='utf-8') as file:
                            data = yaml.safe_load(file)
                            rules_count = len(data.get("rules", [])) if data else 0
                    except Exception:
                        rules_count = 0

                    files.append({
                        "category": cat,
                        "filename": f.name,
                        "path": profile_path,
                        "rules_count": rules_count,
                        "is_active": profile_path in active_profiles,
                        "modified": f.stat().st_mtime
                    })

        return sorted(files, key=lambda x: x["modified"], reverse=True)


# 싱글톤 인스턴스
rule_loader = RuleLoader()
