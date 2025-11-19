"""
Tolerance Service

Skin Model API 호출 및 공차 예측 처리
"""
import os
import logging
from typing import Dict, Any, List
import httpx
from fastapi import HTTPException

logger = logging.getLogger(__name__)

# Configuration
SKINMODEL_URL = os.getenv("SKINMODEL_URL", "http://skinmodel-api:5003")


async def call_skinmodel_tolerance(
    dimensions: List[Dict],
    material: Dict,
    material_type: str = 'steel',
    manufacturing_process: str = 'machining',
    correlation_length: float = 10.0
) -> Dict[str, Any]:
    """
    Skin Model API 호출 - 데이터 형식 변환 포함

    Args:
        dimensions: 치수 목록
        material: 재질 정보
        material_type: 재질 타입 (기본 'steel')
        manufacturing_process: 제조 공정 (기본 'machining')
        correlation_length: 상관 길이 (기본 10.0)

    Returns:
        Skin Model 공차 예측 결과 dict
    """
    try:
        logger.info(f"Calling Skin Model API with {len(dimensions)} dimensions")
        logger.info(
            f"  material_type={material_type}, "
            f"manufacturing_process={manufacturing_process}, "
            f"correlation_length={correlation_length}"
        )

        # Transform dimensions to match Skin Model API format
        # Only include dimensions with valid numeric values
        transformed_dimensions = []
        skipped_count = 0

        for dim in dimensions:
            # Validate that the value can be converted to float
            value_str = str(dim.get("value", ""))
            try:
                # Try to parse as float (this filters out non-numeric values)
                value_float = float(value_str)

                transformed_dim = {
                    "type": dim.get("type", "length"),
                    "value": value_float,
                    "unit": dim.get("unit", "mm")
                }

                # Parse tolerance string (e.g., "±0.1" -> 0.1)
                tolerance_str = dim.get("tolerance")
                if tolerance_str:
                    try:
                        # Remove ± symbol and convert to float
                        tolerance_value = float(str(tolerance_str).replace("±", "").strip())
                        transformed_dim["tolerance"] = tolerance_value
                    except (ValueError, AttributeError):
                        # If parsing fails, skip tolerance field (it's optional)
                        pass

                transformed_dimensions.append(transformed_dim)

            except (ValueError, TypeError):
                # Skip non-numeric values (e.g., "1mm", "(8)45", "Rev. 1", etc.)
                skipped_count += 1
                logger.warning(f"Skipping non-numeric dimension value: {value_str}")
                continue

        if skipped_count > 0:
            logger.info(f"Filtered out {skipped_count} non-numeric dimensions from {len(dimensions)} total")

        if not transformed_dimensions:
            logger.warning("No valid numeric dimensions for Skin Model after filtering")
            return {
                "status": "skipped",
                "data": {
                    "message": "No valid numeric dimensions available for tolerance analysis",
                    "skipped_count": skipped_count
                }
            }

        async with httpx.AsyncClient(timeout=30.0) as client:
            data = {
                "dimensions": transformed_dimensions,
                "material": material,
                "manufacturing_process": manufacturing_process,
                "correlation_length": correlation_length
            }

            logger.info(f"Sending to Skin Model: {data}")

            response = await client.post(
                f"{SKINMODEL_URL}/api/v1/tolerance",
                json=data
            )

            logger.info(f"Skin Model API status: {response.status_code}")

            if response.status_code == 200:
                skinmodel_response = response.json()
                logger.info(f"Skin Model response keys: {skinmodel_response.keys()}")
                if 'data' in skinmodel_response and 'manufacturability' in skinmodel_response['data']:
                    manu_data = skinmodel_response['data']['manufacturability']
                    logger.info(
                        f"Skin Model manufacturability: {manu_data.get('score', 0)}%, "
                        f"difficulty: {manu_data.get('difficulty', 'Unknown')}"
                    )
                return skinmodel_response
            else:
                logger.error(f"Skin Model error response: {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Skin Model failed: {response.text}"
                )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Skin Model API call failed: {type(e).__name__}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Skin Model error: {str(e)}")
