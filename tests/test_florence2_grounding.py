"""Florence-2-base grounding + region tasks on T5 bearing drawing"""
import torch
from transformers import AutoProcessor, AutoModelForCausalLM
from PIL import Image
import warnings
warnings.filterwarnings("ignore")

print('Loading Florence-2-base...')
model_id = 'microsoft/Florence-2-base'
model = AutoModelForCausalLM.from_pretrained(
    model_id, trust_remote_code=True, torch_dtype=torch.float32,
    attn_implementation="eager",
)
processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
model = model.to('cuda').eval()
print(f'Model on GPU. VRAM: {torch.cuda.memory_allocated()/1024**3:.1f}GB')

img = Image.open('/home/uproot/ax/poc/blueprint-ai-bom/data/dse_batch_test/converted_pngs/TD0062037.png')
max_side = 1024
ratio = min(max_side / img.width, max_side / img.height)
if ratio < 1:
    img = img.resize((int(img.width * ratio), int(img.height * ratio)))
print(f'Image: {img.size}')


def run_task(task_prompt, task_type=None):
    """Run a Florence-2 task and return parsed result."""
    inputs = processor(text=task_prompt, images=img, return_tensors='pt').to('cuda')
    with torch.no_grad():
        generated = model.generate(
            input_ids=inputs['input_ids'],
            pixel_values=inputs['pixel_values'],
            max_new_tokens=1024,
            num_beams=3,
        )
    result = processor.batch_decode(generated, skip_special_tokens=False)[0]
    task_key = task_type or task_prompt
    parsed = processor.post_process_generation(result, task=task_key, image_size=img.size)
    return parsed


# 1. Object Detection — what objects does it see?
print('\n=== <OD> Object Detection ===')
try:
    r = run_task('<OD>')
    for k, v in r.items():
        if isinstance(v, dict):
            labels = v.get('labels', [])
            bboxes = v.get('bboxes', [])
            print(f'  Found {len(labels)} objects')
            for lbl, bbox in zip(labels[:10], bboxes[:10]):
                print(f'    {lbl}: {bbox}')
        else:
            print(f'  {k}: {str(v)[:200]}')
except Exception as e:
    print(f'  FAILED: {e}')

# 2. Caption to Phrase Grounding — locate "dimension" text
print('\n=== <CAPTION_TO_PHRASE_GROUNDING> ===')
for phrase in ['outer diameter', 'dimension text', 'bearing']:
    try:
        r = run_task(f'<CAPTION_TO_PHRASE_GROUNDING>{phrase}', '<CAPTION_TO_PHRASE_GROUNDING>')
        print(f'  "{phrase}": {str(r)[:300]}')
    except Exception as e:
        print(f'  "{phrase}" FAILED: {e}')

# 3. Open Vocabulary Detection — find dimension-related objects
print('\n=== <OPEN_VOCABULARY_DETECTION> ===')
for query in ['circle', 'dimension line', 'text number']:
    try:
        r = run_task(f'<OPEN_VOCABULARY_DETECTION>{query}', '<OPEN_VOCABULARY_DETECTION>')
        print(f'  "{query}": {str(r)[:300]}')
    except Exception as e:
        print(f'  "{query}" FAILED: {e}')

# 4. OCR with Region — get text bounding boxes
print('\n=== <OCR_WITH_REGION> ===')
try:
    r = run_task('<OCR_WITH_REGION>')
    ocr_data = r.get('<OCR_WITH_REGION>', {})
    labels = ocr_data.get('labels', []) if isinstance(ocr_data, dict) else []
    quads = ocr_data.get('quad_boxes', []) if isinstance(ocr_data, dict) else []
    print(f'  Found {len(labels)} text regions')
    # Show first 20 with positions
    for lbl, quad in zip(labels[:20], quads[:20]):
        print(f'    "{lbl}" @ {[round(x) for x in quad[:4]]}...')
except Exception as e:
    print(f'  FAILED: {e}')

# 5. Region to Description — describe the center area (where bearing is)
print('\n=== <REGION_TO_DESCRIPTION> center region ===')
try:
    w, h = img.size
    # Center 50% of the image
    cx1, cy1, cx2, cy2 = int(w*0.25), int(h*0.25), int(w*0.75), int(h*0.75)
    loc_str = f'<REGION_TO_DESCRIPTION><loc_{cx1}><loc_{cy1}><loc_{cx2}><loc_{cy2}>'
    r = run_task(loc_str, '<REGION_TO_DESCRIPTION>')
    print(f'  Center region: {str(r)[:300]}')
except Exception as e:
    print(f'  FAILED: {e}')

del model, processor
torch.cuda.empty_cache()
print('\nDone.')
