"""
False Positive Filtering

도면 메타데이터를 치수로 오인식한 결과 필터링
"""
import re


def is_false_positive(text: str) -> bool:
    """
    False Positive 판별: 도면 메타데이터인지 확인

    필터링 대상:
    - 도면 번호 (Rev, DWG, E3, 12-016840 등)
    - 참조 번호 (412-311197 등)
    - 공차 병합 오인식 (+0+0, -0.1-0.2 등)

    Args:
        text: 검증할 텍스트

    Returns:
        True if false positive, False if valid dimension
    """
    # 패턴 1: Revision 번호 (Rev.3, Rev.1 등)
    if re.search(r'\bRev\.?\d+\b', text, re.IGNORECASE):
        return True

    # 패턴 2: DWG 번호
    if re.search(r'\bDWG\b', text, re.IGNORECASE):
        return True

    # 패턴 3: 하이픈으로 연결된 긴 번호 (12-016840, 412-311197 등)
    if re.match(r'^\d{2,}-\d{5,}', text):
        return True

    # 패턴 4: 문서 번호 (E3003810 등)
    if re.match(r'^[A-Z]\d{6,}', text):
        return True

    # 패턴 5: 공차 병합 오인식 (+0+0, -0.1-0.2, +0.2+0 등)
    if re.match(r'^[+-]\d+\.?\d*[+-]\d+\.?\d*$', text):
        return True

    # 패턴 6: ME-C, S60, S60/65ME-C 같은 기종 번호
    if re.search(r'\bME-C\b|^S\d{2}(/\d{2})?ME-C$', text, re.IGNORECASE):
        return True

    # 패턴 7: 괄호로 감싸진 revision (Rev.3), (Rev.1) 등
    if re.search(r'\(Rev\.\d+\)', text, re.IGNORECASE):
        return True

    return False
