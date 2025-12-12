OCR_FIELD_MAPPINGS = {
    "paddleocr": {"text_results": "texts"},
    "ocr_ensemble": {"results": "texts"},
    # 나머지는 이미 "texts" 사용
}

def normalize_ocr_output(api_id: str, raw_output: dict) -> dict:
    """OCR 출력을 표준 형식으로 변환"""
    mapping = OCR_FIELD_MAPPINGS.get(api_id, {})

    normalized = {
        "texts": [],
        "full_text": raw_output.get("full_text", ""),
        "visualized_image": raw_output.get("visualized_image"),
    }

    # 필드명 변환
    for src, dst in mapping.items():
        if src in raw_output:
            normalized[dst] = raw_output[src]

    # 변환 없이 그대로 사용하는 경우
    if "texts" in raw_output and "texts" not in normalized:
        normalized["texts"] = raw_output["texts"]

    # 특수 필드 유지 (eDOCr2)
    for special in ["dimensions", "gdt_symbols", "tables"]:
        if special in raw_output:
            normalized[special] = raw_output[special]

    return normalized
