"""
Request Models for Gateway API

요청 관련 Pydantic 모델들을 정의합니다.
"""
from pydantic import BaseModel, Field


class ProcessRequest(BaseModel):
    """도면 처리 요청"""
    use_segmentation: bool = Field(True, description="EDGNet 세그멘테이션 사용")
    use_ocr: bool = Field(True, description="eDOCr2 OCR 사용")
    use_tolerance: bool = Field(True, description="Skin Model 공차 예측 사용")
    visualize: bool = Field(True, description="시각화 생성")


class QuoteRequest(BaseModel):
    """견적서 생성 요청"""
    material_cost_per_kg: float = Field(5.0, description="재료 단가 (USD/kg)")
    machining_rate_per_hour: float = Field(50.0, description="가공 시간당 비용 (USD/hour)")
    tolerance_premium_factor: float = Field(1.2, description="공차 정밀도 비용 계수")
