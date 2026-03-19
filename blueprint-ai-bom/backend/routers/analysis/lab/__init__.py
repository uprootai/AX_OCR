"""Lab Router Package — 실험/비교 분석용 라우터 모음

각 Lab 카테고리별 라우터:
- dimension_lab_router: OD/ID/W 분류 방법론 비교, Ground Truth, 70셀 매트릭스
- (향후) material_lab_router: 소재 분류 실험
- (향후) tolerance_lab_router: 공차 해석 실험
"""
from .dimension_lab_router import router as dimension_lab_router
from .batch_eval_router import router as batch_eval_router

__all__ = [
    'dimension_lab_router',
    'batch_eval_router',
]
