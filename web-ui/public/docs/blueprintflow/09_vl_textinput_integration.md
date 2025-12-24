# VL API + TextInput 통합 가이드

## 🎯 목표

VL (Vision-Language) API에 **이미지 + 텍스트 프롬프트**를 함께 전달하여 더 정확한 분석 결과를 얻습니다.

---

## 📋 현재 상태

### VL API 현재 구현

**파일**: `models/vl-api/api_server.py`

**현재 입력**:
- ✅ `image` (파일 업로드)
- ❌ `prompt` (텍스트 프롬프트) - **미구현**

**문제**:
- VL 모델에 "무엇을 분석할지" 지시 불가
- 일반적인 분석만 수행
- 사용자 맞춤 질문 불가

---

## 🚀 구현 방안

### Phase 1: VL API에 prompt 파라미터 추가

#### 1-1. API 서버 코드 수정

**파일**: `models/vl-api/api_server.py`

```python
# ✅ 기존 코드 (이미지만)
@app.post("/api/v1/analyze")
async def analyze_image(
    file: UploadFile = File(...),
    model: str = Form("blip2"),
):
    # 이미지 분석...
    return {"caption": "...", "objects": [...]}
```

```python
# ✅ 개선 코드 (이미지 + 프롬프트)
@app.post("/api/v1/analyze")
async def analyze_image(
    file: UploadFile = File(...),
    model: str = Form("blip2"),
    prompt: Optional[str] = Form(None),  # ✅ 추가
):
    """
    VL 모델로 이미지 분석

    Args:
        file: 입력 이미지
        model: 사용할 VL 모델 (blip2, llava, etc.)
        prompt: 분석 질문/프롬프트 (선택사항)
            예: "이 이미지에서 용접 기호를 찾아주세요"
    """

    # 이미지 로드
    image = load_image(file)

    # 프롬프트가 있으면 질문-답변 모드, 없으면 일반 캡셔닝
    if prompt:
        # VQA (Visual Question Answering) 모드
        result = vl_model.answer_question(image, prompt)
        return {
            "mode": "vqa",
            "question": prompt,
            "answer": result["answer"],
            "confidence": result.get("confidence", 1.0)
        }
    else:
        # 일반 이미지 캡셔닝 모드
        caption = vl_model.generate_caption(image)
        objects = vl_model.detect_objects(image)
        return {
            "mode": "captioning",
            "caption": caption,
            "objects": objects
        }
```

#### 1-2. /api/v1/info 업데이트

```python
@app.get("/api/v1/info")
async def get_api_info():
    return {
        "id": "vl",
        "name": "VL",
        "display_name": "Vision-Language Model",
        "description": "이미지와 텍스트를 함께 이해하는 멀티모달 AI",
        "endpoint": "/api/v1/analyze",
        "method": "POST",
        "requires_image": True,

        # ✅ inputs 정의
        "inputs": [
            {
                "name": "image",
                "type": "file",
                "description": "분석할 이미지",
                "required": True
            },
            {
                "name": "prompt",  # ✅ 추가!
                "type": "string",
                "description": "이미지에 대한 질문 또는 분석 요청",
                "required": False
            }
        ],

        # ✅ 출력 정의
        "outputs": [
            {
                "name": "mode",
                "type": "string",
                "description": "분석 모드 (vqa 또는 captioning)"
            },
            {
                "name": "answer",
                "type": "string",
                "description": "질문에 대한 답변 (VQA 모드)"
            },
            {
                "name": "caption",
                "type": "string",
                "description": "이미지 설명 (캡셔닝 모드)"
            }
        ],

        # ✅ inputMappings 추가 (GenericAPIExecutor용)
        "input_mappings": {
            "prompt": "inputs.text"  # TextInput의 text → API의 prompt
        },

        "parameters": [
            {
                "name": "model",
                "type": "select",
                "options": ["blip2", "llava", "instructblip"],
                "default": "blip2",
                "description": "사용할 VL 모델"
            }
        ],

        "blueprintflow": {
            "icon": "👁️",
            "color": "#ec4899",
            "category": "api"
        }
    }
```

---

### Phase 2: BlueprintFlow 노드 정의 업데이트

**파일**: `web-ui/src/config/nodeDefinitions.ts`

```typescript
vl: {
  type: 'vl',
  label: 'VL Model',
  category: 'api',
  color: '#ec4899',
  icon: 'Eye',
  description: '이미지와 텍스트를 함께 이해하는 Vision-Language 모델',

  inputs: [
    {
      name: 'image',
      type: 'Image',
      description: '📄 분석할 이미지',
    },
    {
      name: 'text',  // ✅ 추가!
      type: 'string',
      description: '❓ 질문 또는 분석 요청 (선택사항)',
    },
  ],

  outputs: [
    {
      name: 'mode',
      type: 'string',
      description: '분석 모드',
    },
    {
      name: 'answer',
      type: 'string',
      description: '💬 질문에 대한 답변 (VQA 모드)',
    },
    {
      name: 'caption',
      type: 'string',
      description: '📝 이미지 설명 (캡셔닝 모드)',
    },
  ],

  parameters: [
    {
      name: 'model',
      type: 'select',
      default: 'blip2',
      options: ['blip2', 'llava', 'instructblip'],
      description: '사용할 VL 모델',
    },
  ],

  examples: [
    '이미지 + 질문으로 정확한 정보 추출',
    '"이 도면의 치수를 알려줘" 같은 자연어 질문',
    '용접 기호, 공차 정보 등 특정 요소 찾기',
  ],

  usageTips: [
    '💡 프롬프트 없이 사용 시: 일반 이미지 캡셔닝',
    '💡 프롬프트와 함께 사용 시: 질문-답변 모드 (더 정확)',
    '💡 TextInput과 연결하여 사용자 질문 전달',
  ],

  recommendedInputs: [
    {
      from: 'imageinput',
      field: 'image',
      reason: '분석할 도면 이미지',
    },
    {
      from: 'textinput',  // ✅ 추가!
      field: 'text',
      reason: '특정 질문이나 분석 요청',
    },
  ],
}
```

---

### Phase 3: VL Executor 업데이트

**파일**: `gateway-api/blueprintflow/executors/vl_executor.py`

```python
class VLExecutor(BaseNodeExecutor):
    """Vision-Language 모델 실행기"""

    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        # 이미지 준비
        file_bytes = prepare_image_for_api(inputs, context)

        # 파라미터
        model = self.parameters.get("model", "blip2")

        # ✅ 프롬프트 가져오기 (있으면)
        prompt = inputs.get("text")  # TextInput에서 전달받은 텍스트

        # VL API 호출
        async with httpx.AsyncClient(timeout=60.0) as client:
            files = {"file": ("image.jpg", file_bytes, "image/jpeg")}
            data = {
                "model": model,
            }

            # ✅ 프롬프트가 있으면 추가
            if prompt:
                data["prompt"] = prompt

            response = await client.post(
                "http://vl-api:5004/api/v1/analyze",
                files=files,
                data=data
            )

        if response.status_code == 200:
            result = response.json()

            # 출력 구조화
            output = {
                "mode": result.get("mode", "captioning"),
                "model_used": model,
            }

            # VQA 모드
            if result.get("mode") == "vqa":
                output["answer"] = result.get("answer", "")
                output["question"] = prompt
                output["confidence"] = result.get("confidence", 1.0)
            # 캡셔닝 모드
            else:
                output["caption"] = result.get("caption", "")
                output["objects"] = result.get("objects", [])

            return output
        else:
            raise Exception(f"VL API 호출 실패: {response.status_code}")
```

---

## 🎨 사용 예시

### 예시 1: 도면 치수 추출

**워크플로우**:
```
┌─────────────┐
│ ImageInput  │ (기계 도면 업로드)
└──────┬──────┘
       │ image
       ↓
┌─────────────┐
│ TextInput   │ text: "이 도면의 모든 치수 값을 추출해주세요"
└──────┬──────┘
       │ text
       ↓
┌─────────────┐
│ VL Model    │
│             │
│ image ←─────┼─ ImageInput.image
│ text ←──────┼─ TextInput.text
│ model: blip2│
└──────┬──────┘
       │
       ↓ answer: "검출된 치수: Ø50, L100, ..."
```

**결과**:
```json
{
  "mode": "vqa",
  "question": "이 도면의 모든 치수 값을 추출해주세요",
  "answer": "검출된 치수: 직경 Ø50mm, 길이 L100mm, 공차 ±0.05mm",
  "confidence": 0.92
}
```

---

### 예시 2: 용접 기호 찾기

**워크플로우**:
```
[ImageInput] ──┬──→ [VL Model]
               │     text: "용접 기호를 모두 찾아줘"
[TextInput] ───┘
```

**결과**:
```json
{
  "mode": "vqa",
  "question": "용접 기호를 모두 찾아줘",
  "answer": "필렛 용접 기호 3개, 맞대기 용접 기호 1개 발견",
  "confidence": 0.88
}
```

---

### 예시 3: 프롬프트 없이 사용

**워크플로우**:
```
[ImageInput] ──→ [VL Model]
                 (프롬프트 연결 안 함)
```

**결과**:
```json
{
  "mode": "captioning",
  "caption": "기계 부품 설계 도면, 원통형 샤프트, 치수 표기 포함",
  "objects": ["shaft", "dimension", "centerline"]
}
```

---

## 📊 비교: 프롬프트 유무

| 모드 | 프롬프트 | 결과 |
|------|---------|------|
| **캡셔닝** | ❌ 없음 | "기계 부품 도면입니다" (일반적) |
| **VQA** | ✅ "치수를 알려줘" | "Ø50mm, L100mm" (구체적) |

**결론**: 프롬프트를 사용하면 **훨씬 정확한 정보**를 얻을 수 있습니다.

---

## 🔧 구현 체크리스트

### VL API 서버 (Backend)
- [ ] `/api/v1/analyze`에 `prompt` 파라미터 추가
- [ ] VQA 모드 구현 (질문-답변)
- [ ] 캡셔닝 모드 유지 (하위 호환성)
- [ ] `/api/v1/info`에 inputs, input_mappings 추가

### Gateway API (Executor)
- [ ] `vl_executor.py`에서 `inputs.get("text")` 처리
- [ ] prompt를 VL API로 전달
- [ ] 출력 파싱 (mode, answer, caption)

### Web UI (Frontend)
- [ ] `nodeDefinitions.ts` VL 노드에 `text` input 추가
- [ ] `recommendedInputs`에 TextInput 추가
- [ ] 사용 가이드 업데이트

### 테스트
- [ ] TextInput + VL 워크플로우 테스트
- [ ] 프롬프트 유무 결과 비교
- [ ] 다양한 질문 시나리오 검증

---

## 🎯 기대 효과

### Before (프롬프트 없음)
```
ImageInput → VL Model → "기계 부품 도면"
                         (모호한 일반 설명)
```

### After (프롬프트 있음)
```
ImageInput ─┬─→ VL Model → "Ø50mm, L100mm, ±0.05mm"
            │              (정확한 치수 정보)
TextInput ──┘
"치수 추출"
```

**개선점**:
- ✅ 정확도 향상 (30% → 90%)
- ✅ 사용자 의도 반영
- ✅ 맞춤형 분석 가능

---

## 📝 향후 확장

### 1. Multi-turn 대화
```
사용자: "이 도면의 치수는?"
VL: "Ø50mm입니다"
사용자: "공차는?"
VL: "±0.05mm입니다"
```

### 2. Chain of Thought
```
TextInput: "단계별로 분석: 1) 용접 기호 찾기 2) 치수 추출 3) 공차 검증"
VL: "1단계 - 용접 기호 3개 발견..."
```

### 3. 다국어 지원
```
TextInput: "Extract all dimensions in English"
VL: "Detected dimensions: Ø50mm, L100mm..."
```

---

**Last Updated**: 2025-11-22
**Status**: 📋 구현 가이드 (실제 구현 필요)
**Priority**: High (VL API 활용도 대폭 향상)
