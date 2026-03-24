"""Florence-2-base zero-shot test on T5 bearing drawing"""
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

for task in ['<OCR>', '<CAPTION>', '<MORE_DETAILED_CAPTION>']:
    inputs = processor(text=task, images=img, return_tensors='pt').to('cuda')
    try:
        with torch.no_grad():
            generated = model.generate(
                input_ids=inputs['input_ids'],
                pixel_values=inputs['pixel_values'],
                max_new_tokens=512,
                num_beams=1,
                early_stopping=False,
            )
        result = processor.batch_decode(generated, skip_special_tokens=False)[0]
        parsed = processor.post_process_generation(result, task=task, image_size=img.size)
        print(f'\n=== {task} ===')
        print(str(parsed)[:500])
    except Exception as e:
        print(f'\n=== {task} FAILED ===')
        print(f'{type(e).__name__}: {e}')
        import traceback
        traceback.print_exc()
        break

del model, processor
torch.cuda.empty_cache()
print('\nDone.')
