"""
VL Service
VL 모델 호출 함수 (Claude, OpenAI, Local BLIP)
"""

import os
import io
import json
import base64
import logging
import re
from typing import Dict, List, Union

import httpx
import torch
from PIL import Image
from fastapi import HTTPException

logger = logging.getLogger(__name__)

# Configuration
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Global state (set by lifespan)
_available_models: List[str] = []
_florence_model = None
_florence_processor = None
_florence_device = None


def get_available_models() -> List[str]:
    """사용 가능한 모델 목록 반환"""
    return _available_models


def get_florence_model():
    """Florence/BLIP 모델 반환"""
    return _florence_model


def get_florence_processor():
    """Florence/BLIP 프로세서 반환"""
    return _florence_processor


def get_florence_device():
    """Florence/BLIP 디바이스 반환"""
    return _florence_device


def set_model_state(models: List[str], model, processor, device):
    """모델 상태 설정 (lifespan에서 호출)"""
    global _available_models, _florence_model, _florence_processor, _florence_device
    _available_models = models
    _florence_model = model
    _florence_processor = processor
    _florence_device = device


def encode_image_to_base64(image_bytes: bytes) -> str:
    """이미지를 base64로 인코딩"""
    return base64.b64encode(image_bytes).decode('utf-8')


async def call_claude_api(
    image_bytes: bytes,
    prompt: str,
    model: str = "claude-3-5-sonnet-20241022",
    max_tokens: int = 4096,
    temperature: float = 0.0
) -> str:
    """
    Claude API 호출

    Args:
        image_bytes: 이미지 바이트 데이터
        prompt: 프롬프트
        model: 모델명
        max_tokens: 최대 토큰 수
        temperature: 생성 다양성 (0-1, 0=결정적, 1=창의적)

    Returns:
        모델 응답 텍스트
    """
    if not ANTHROPIC_API_KEY:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not set")

    try:
        # 이미지를 base64로 인코딩
        base64_image = encode_image_to_base64(image_bytes)

        # 이미지 형식 감지
        img = Image.open(io.BytesIO(image_bytes))
        image_format = img.format.lower() if img.format else "png"
        if image_format == "jpg":
            image_format = "jpeg"

        # Claude API 요청
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": model,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": f"image/{image_format}",
                                        "data": base64_image
                                    }
                                },
                                {
                                    "type": "text",
                                    "text": prompt
                                }
                            ]
                        }
                    ]
                }
            )

            if response.status_code != 200:
                logger.error(f"Claude API error: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Claude API error: {response.text}"
                )

            result = response.json()
            text = result["content"][0]["text"]

            logger.info(f"Claude API response: {len(text)} characters")
            return text

    except Exception as e:
        logger.error(f"Claude API call failed: {e}")
        raise HTTPException(status_code=500, detail=f"Claude API error: {str(e)}")


async def call_openai_gpt4v_api(
    image_bytes: bytes,
    prompt: str,
    model: str = "gpt-4o",
    max_tokens: int = 4096,
    temperature: float = 0.0
) -> str:
    """
    OpenAI GPT-4V API 호출

    Args:
        image_bytes: 이미지 바이트 데이터
        prompt: 프롬프트
        model: 모델명
        max_tokens: 최대 토큰 수
        temperature: 생성 다양성 (0-1, 0=결정적, 1=창의적)

    Returns:
        모델 응답 텍스트
    """
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not set")

    try:
        # 이미지를 base64로 인코딩
        base64_image = encode_image_to_base64(image_bytes)

        # 이미지 형식 감지
        img = Image.open(io.BytesIO(image_bytes))
        image_format = img.format.lower() if img.format else "png"
        if image_format == "jpg":
            image_format = "jpeg"

        # OpenAI API 요청
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": prompt
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/{image_format};base64,{base64_image}"
                                    }
                                }
                            ]
                        }
                    ],
                    "max_tokens": max_tokens,
                    "temperature": temperature
                }
            )

            if response.status_code != 200:
                logger.error(f"OpenAI API error: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"OpenAI API error: {response.text}"
                )

            result = response.json()
            text = result["choices"][0]["message"]["content"]

            logger.info(f"OpenAI API response: {len(text)} characters")
            return text

    except Exception as e:
        logger.error(f"OpenAI API call failed: {e}")
        raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(e)}")


async def call_local_vl_api(
    image_bytes: bytes,
    prompt: str = "",
    mode: str = "caption"
) -> str:
    """
    로컬 VL 모델 호출 (BLIP)

    Args:
        image_bytes: 이미지 바이트 데이터
        prompt: 프롬프트 (선택사항, BLIP는 conditional generation 지원)
        mode: 'caption' (기본) 또는 'vqa'

    Returns:
        모델 응답 텍스트
    """
    if _florence_model is None:
        raise HTTPException(status_code=500, detail="Local VL model not loaded")

    try:
        # 이미지 로드
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")

        # BLIP은 conditional captioning 지원
        if prompt and prompt.strip():
            # 프롬프트가 있으면 conditional generation
            inputs = _florence_processor(
                images=img,
                text=prompt,
                return_tensors="pt"
            ).to(_florence_device)
        else:
            # 프롬프트 없으면 unconditional captioning
            inputs = _florence_processor(
                images=img,
                return_tensors="pt"
            ).to(_florence_device)

        # 추론
        with torch.no_grad():
            generated_ids = _florence_model.generate(
                **inputs,
                max_new_tokens=100,
                num_beams=3
            )

        # 디코딩
        generated_text = _florence_processor.decode(
            generated_ids[0], skip_special_tokens=True
        )

        return generated_text.strip()

    except Exception as e:
        logger.error(f"Local VL inference failed: {e}")
        raise HTTPException(status_code=500, detail=f"Local VL error: {str(e)}")


def parse_json_from_text(text: str) -> Union[Dict, List]:
    """
    텍스트에서 JSON 추출 및 파싱

    모델이 ```json ... ``` 형태로 감싼 경우 처리
    """
    try:
        # 코드 블록 제거
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        # JSON 파싱
        return json.loads(text)
    except json.JSONDecodeError as e:
        logger.warning(f"JSON parsing failed, attempting to extract: {e}")
        # 단순히 중괄호 또는 대괄호로 시작하는 부분 찾기
        json_pattern = r'(\{.*\}|\[.*\])'
        match = re.search(json_pattern, text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except:
                pass

        # 실패 시 원본 텍스트 반환
        logger.error(f"Could not parse JSON from text: {text[:200]}")
        raise ValueError(f"Failed to parse JSON: {text[:200]}")


# ============================================================================
# LLaVA-CoT 스타일 다단계 추론 (Chain-of-Thought)
# arXiv 2411.10440: LLaVA-CoT - Let Vision Language Models Reason Step-by-Step
# ============================================================================

COT_SYSTEM_PROMPT = """You are an expert visual reasoning system that analyzes images through systematic multi-step reasoning.

For each question about an image, you MUST follow this 4-stage reasoning process:

1. **SUMMARY**: Briefly summarize the question and identify what needs to be determined.

2. **VISUAL INTERPRETATION**: Describe what you observe in the image that is relevant to the question. Focus on specific visual elements, components, labels, symbols, and any text visible.

3. **LOGICAL REASONING**: Based on your visual observations, reason through the problem step by step. Consider relationships between elements, apply domain knowledge, and build your logical argument.

4. **CONCLUSION**: State your final answer clearly and concisely, directly addressing the original question.

You MUST structure your response EXACTLY in this JSON format:
```json
{
    "summary": "Brief restatement of the question and what needs to be determined",
    "visual_interpretation": "Detailed description of relevant visual elements observed",
    "logical_reasoning": "Step-by-step reasoning based on observations",
    "conclusion": "Clear and concise final answer"
}
```

IMPORTANT: Always respond with valid JSON in the exact format above. Do not include any text outside the JSON block."""


async def call_cot_reasoning(
    image_bytes: bytes,
    question: str,
    model: str = "gpt-4o-mini",
    temperature: float = 0.0
) -> Dict[str, str]:
    """
    LLaVA-CoT 스타일 다단계 추론 수행

    4단계 추론 프로세스:
    1. Summary (요약)
    2. Visual Interpretation (시각 해석)
    3. Logical Reasoning (논리 추론)
    4. Conclusion (결론)

    Args:
        image_bytes: 이미지 바이트 데이터
        question: 사용자 질문
        model: 모델명
        temperature: 생성 다양성

    Returns:
        추론 단계별 결과 딕셔너리
    """
    # 전체 프롬프트 구성
    full_prompt = f"""{COT_SYSTEM_PROMPT}

User Question: {question}

Analyze the image and provide your response in the required JSON format."""

    # 모델 호출
    if model.startswith("claude"):
        response_text = await call_claude_api(
            image_bytes, full_prompt, model, temperature=temperature
        )
    elif model.startswith("gpt"):
        response_text = await call_openai_gpt4v_api(
            image_bytes, full_prompt, model, temperature=temperature
        )
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported model for CoT: {model}")

    # JSON 파싱
    try:
        result = parse_json_from_text(response_text)

        # 필수 키 확인
        required_keys = ["summary", "visual_interpretation", "logical_reasoning", "conclusion"]
        for key in required_keys:
            if key not in result:
                result[key] = ""
                logger.warning(f"Missing CoT key: {key}")

        logger.info(f"CoT reasoning completed with {len(result)} steps")
        return result

    except Exception as e:
        logger.error(f"CoT parsing failed: {e}")
        # 폴백: 원본 텍스트를 conclusion으로 사용
        return {
            "summary": "Failed to parse structured response",
            "visual_interpretation": "",
            "logical_reasoning": "",
            "conclusion": response_text
        }


# ============================================================================
# 도면 분류용 CoT 프롬프트 (Blueprint AI BOM 연동)
# ============================================================================

COT_CLASSIFICATION_PROMPT = """You are an expert engineering drawing classifier that analyzes drawings through systematic multi-step reasoning.

Your task is to classify this engineering drawing into one of these categories:
- **MECHANICAL**: General mechanical/engineering drawings (part drawings, assembly drawings)
- **PID**: Piping and Instrumentation Diagrams (P&ID, process flow diagrams)
- **ELECTRICAL**: Electrical diagrams (wiring diagrams, circuit diagrams)
- **ASSEMBLY**: Assembly drawings showing how parts fit together
- **DETAIL**: Detail views with specific dimensions and tolerances
- **LAYOUT**: Layout or arrangement drawings
- **OTHER**: None of the above categories

Follow this 4-stage reasoning process:

```json
{
    "summary": "State what type of drawing needs to be classified",
    "visual_interpretation": "Describe key visual elements: symbols used, layout style, text/labels, line types, etc.",
    "logical_reasoning": "Based on observations, explain which category best fits and why. Consider: Symbol types (valves, pumps = P&ID; nuts, bolts = mechanical), Label formats (tag numbers = P&ID; part numbers = mechanical), Drawing style (process flow = P&ID; orthographic views = mechanical)",
    "conclusion": "State the classification category (MECHANICAL, PID, ELECTRICAL, ASSEMBLY, DETAIL, LAYOUT, or OTHER) and confidence level (high/medium/low)"
}
```"""


async def classify_drawing_with_cot(
    image_bytes: bytes,
    model: str = "gpt-4o-mini",
    temperature: float = 0.0
) -> Dict[str, str]:
    """
    도면 분류를 위한 CoT 추론

    Args:
        image_bytes: 이미지 바이트 데이터
        model: 모델명
        temperature: 생성 다양성

    Returns:
        분류 결과 및 추론 과정
    """
    full_prompt = f"""{COT_CLASSIFICATION_PROMPT}

Analyze this engineering drawing and classify it. Respond with valid JSON only."""

    if model.startswith("claude"):
        response_text = await call_claude_api(
            image_bytes, full_prompt, model, temperature=temperature
        )
    elif model.startswith("gpt"):
        response_text = await call_openai_gpt4v_api(
            image_bytes, full_prompt, model, temperature=temperature
        )
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported model: {model}")

    try:
        result = parse_json_from_text(response_text)
        logger.info(f"Drawing classification with CoT: {result.get('conclusion', 'unknown')}")
        return result
    except Exception as e:
        logger.error(f"Classification CoT parsing failed: {e}")
        return {
            "summary": "Classification analysis",
            "visual_interpretation": "",
            "logical_reasoning": "",
            "conclusion": response_text
        }
