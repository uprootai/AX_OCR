#!/usr/bin/env python3
"""
OpenAPI 스펙 내보내기 스크립트
사용법: python scripts/export_openapi.py [output_path]
"""
import sys
import json
from pathlib import Path

# 프로젝트 루트를 path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from api_server import app


def export_openapi(output_path: str = None):
    """OpenAPI 스펙을 JSON 파일로 내보내기"""
    openapi_schema = app.openapi()

    if output_path is None:
        output_path = project_root / "docs" / "openapi.json"
    else:
        output_path = Path(output_path)

    # 디렉토리 생성
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # JSON 파일로 저장
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(openapi_schema, f, indent=2, ensure_ascii=False)

    print(f"OpenAPI spec exported to: {output_path}")
    print(f"Total paths: {len(openapi_schema.get('paths', {}))}")
    print(f"Total schemas: {len(openapi_schema.get('components', {}).get('schemas', {}))}")

    return output_path


if __name__ == "__main__":
    output = sys.argv[1] if len(sys.argv) > 1 else None
    export_openapi(output)
