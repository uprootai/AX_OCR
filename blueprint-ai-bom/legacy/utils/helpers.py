"""
Helper Utilities
일반적인 헬퍼 유틸리티 함수들
"""

def safe_mean(values):
    """안전한 평균 계산 - 빈 배열 처리"""
    if not values or len(values) == 0:
        return 0.0
    return sum(values) / len(values)