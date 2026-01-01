"""
VL API Services
VL 모델 호출 서비스
"""

from .vl_service import (
    encode_image_to_base64,
    call_claude_api,
    call_openai_gpt4v_api,
    call_local_vl_api,
    parse_json_from_text,
    get_available_models,
    get_florence_model,
    get_florence_processor,
    get_florence_device,
    set_model_state,
    ANTHROPIC_API_KEY,
    OPENAI_API_KEY,
    # LLaVA-CoT 스타일 다단계 추론
    call_cot_reasoning,
    classify_drawing_with_cot,
    COT_SYSTEM_PROMPT,
    COT_CLASSIFICATION_PROMPT,
)

__all__ = [
    'encode_image_to_base64',
    'call_claude_api',
    'call_openai_gpt4v_api',
    'call_local_vl_api',
    'parse_json_from_text',
    'get_available_models',
    'get_florence_model',
    'get_florence_processor',
    'get_florence_device',
    'set_model_state',
    'ANTHROPIC_API_KEY',
    'OPENAI_API_KEY',
    # LLaVA-CoT 스타일 다단계 추론
    'call_cot_reasoning',
    'classify_drawing_with_cot',
    'COT_SYSTEM_PROMPT',
    'COT_CLASSIFICATION_PROMPT',
]
