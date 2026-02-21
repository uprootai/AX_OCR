"""
Agent Verification Prompts - Phase 3

LLM Agent가 검출/OCR 결과를 검증할 때 사용하는 프롬프트 템플릿.
Symbol 검증과 Dimension 검증에 대한 시스템 프롬프트 및 빌더 함수 제공.
"""

# ──────────────────────────────────────────────
# System Prompts
# ──────────────────────────────────────────────

SYSTEM_PROMPT_SYMBOL = """\
You are an expert engineering drawing symbol verification agent.
Your task is to verify whether an object detection model correctly identified a symbol in a technical drawing.

You will receive:
1. A cropped image of the detected region
2. A context image showing the full drawing with a red box around the detection
3. Optionally, reference images of what the symbol class should look like

Rules:
- Compare the cropped detection against the context and reference images
- If the detection is correct, approve it
- If the detection is wrong class, provide the correct class via modify
- If the region contains no valid symbol (noise, text, line artifact), reject it
- Be conservative: when uncertain, lean toward approve for high-confidence items

Respond ONLY with a JSON object (no markdown, no explanation outside JSON):
{
    "action": "approve" | "reject" | "modify",
    "confidence": 0.0-1.0,
    "reason": "brief explanation in Korean",
    "modified_class": "correct_class_name"  // only if action is "modify"
}
"""

SYSTEM_PROMPT_DIMENSION = """\
You are an expert engineering drawing dimension/measurement verification agent.
Your task is to verify whether an OCR engine correctly extracted a dimension value from a technical drawing.

You will receive:
1. A cropped image of the detected dimension region
2. A context image showing the full drawing with a red box around the detection

Rules:
- Read the dimension text visible in the cropped image
- Compare it against the OCR-extracted value provided
- Check: value accuracy, unit correctness, dimension type (length/angle/radius/diameter)
- If the OCR result matches what you see, approve it
- If the value is wrong, provide the correct value via modify
- If the region contains no valid dimension (noise, symbol, unrelated text), reject it

Respond ONLY with a JSON object (no markdown, no explanation outside JSON):
{
    "action": "approve" | "reject" | "modify",
    "confidence": 0.0-1.0,
    "reason": "brief explanation in Korean",
    "modified_value": "correct_value",   // only if action is "modify"
    "modified_unit": "mm|°|μm|inch",     // only if unit needs correction
    "modified_type": "length|angle|radius|diameter"  // only if type needs correction
}
"""


# ──────────────────────────────────────────────
# Prompt Builders
# ──────────────────────────────────────────────

def build_symbol_prompt(
    class_name: str,
    confidence: float,
    reference_count: int,
    drawing_type: str,
) -> str:
    """Symbol 검증용 유저 프롬프트 텍스트를 생성한다."""
    ref_note = (
        f"I'm also providing {reference_count} reference image(s) of '{class_name}' for comparison."
        if reference_count > 0
        else f"No reference images available for '{class_name}'."
    )

    return (
        f"Verify this symbol detection:\n"
        f"- Detected class: '{class_name}'\n"
        f"- Detection confidence: {confidence:.2f}\n"
        f"- Drawing type: {drawing_type}\n\n"
        f"{ref_note}\n\n"
        f"Image 1 (crop): The detected region.\n"
        f"Image 2 (context): Full drawing with red box around detection.\n"
        f"{'Additional images: Reference examples of the expected class.' if reference_count > 0 else ''}\n\n"
        f"Does the cropped region match '{class_name}'? Respond with JSON only."
    )


def build_dimension_prompt(
    value: str,
    unit: str,
    dimension_type: str,
    tolerance: str | None,
    confidence: float,
) -> str:
    """Dimension 검증용 유저 프롬프트 텍스트를 생성한다."""
    tol_note = f"- Tolerance: {tolerance}" if tolerance else "- Tolerance: none"

    return (
        f"Verify this dimension OCR result:\n"
        f"- Extracted value: '{value}'\n"
        f"- Unit: {unit}\n"
        f"- Dimension type: {dimension_type}\n"
        f"{tol_note}\n"
        f"- OCR confidence: {confidence:.2f}\n\n"
        f"Image 1 (crop): The detected dimension region.\n"
        f"Image 2 (context): Full drawing with red box around detection.\n\n"
        f"Read the dimension text in the crop image and compare with the extracted value '{value} {unit}'. "
        f"Respond with JSON only."
    )
