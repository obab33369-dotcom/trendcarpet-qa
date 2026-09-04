import os
import torch
from PIL import Image
import gc

# Module-level variables to hold lazy-loaded models
_model = None
_processor = None
_device = "cuda" if torch.cuda.is_available() else "cpu"

def get_florence2_model():
    """Lazy loads Microsoft Florence-2-base locally on CUDA/CPU."""
    global _model, _processor
    if _model is None:
        import transformers
        
        # 1. Monkeypatch PretrainedConfig for forced_bos_token_id attribute error in newer transformers versions
        orig_getattribute = transformers.configuration_utils.PretrainedConfig.__getattribute__
        def safe_getattribute(self, key):
            try:
                return orig_getattribute(self, key)
            except AttributeError as e:
                if key == "forced_bos_token_id":
                    return None
                raise e
        transformers.configuration_utils.PretrainedConfig.__getattribute__ = safe_getattribute

        # 2. Monkeypatch PreTrainedModel for _supports_sdpa initialization order bug
        orig_sdpa = transformers.modeling_utils.PreTrainedModel._sdpa_can_dispatch
        def safe_sdpa(self, *args, **kwargs):
            has_lm = hasattr(self, "language_model")
            _d = None
            if not has_lm:
                class DummyLM:
                    _supports_sdpa = True
                    _supports_flash_attn_2 = True
                _d = DummyLM()
                self.language_model = _d
            try:
                res = orig_sdpa(self, *args, **kwargs)
            finally:
                if not has_lm and hasattr(self, "language_model") and getattr(self, "language_model") is _d:
                    delattr(self, "language_model")
            return res
        transformers.modeling_utils.PreTrainedModel._sdpa_can_dispatch = safe_sdpa

        # 3. Monkeypatch PreTrainedTokenizerBase for additional_special_tokens missing attribute
        orig_token_getattr = transformers.tokenization_utils_base.PreTrainedTokenizerBase.__getattr__
        def safe_token_getattr(self, key):
            try:
                return orig_token_getattr(self, key)
            except AttributeError as e:
                if key == "additional_special_tokens":
                    return []
                raise e
        transformers.tokenization_utils_base.PreTrainedTokenizerBase.__getattr__ = safe_token_getattr

        # 4. Monkeypatch EncoderDecoderCache to support indexing/subscripting in newer transformers
        from transformers.cache_utils import EncoderDecoderCache
        def cache_getitem(self, index):
            if not isinstance(index, int):
                raise TypeError("Indices must be integers")
            if index < 0:
                index = len(self) + index
            for i, layer_cache in enumerate(self):
                if i == index:
                    return layer_cache
            raise IndexError("cache index out of range")
        EncoderDecoderCache.__getitem__ = cache_getitem

        # 5. Monkeypatch PreTrainedModel.__init__ to wrap prepare_inputs_for_generation to handle empty past_key_values
        orig_model_init = transformers.modeling_utils.PreTrainedModel.__init__
        def safe_model_init(self, *args, **kwargs):
            orig_model_init(self, *args, **kwargs)
            if hasattr(self, "prepare_inputs_for_generation"):
                orig_prepare = self.prepare_inputs_for_generation
                def safe_prepare(self_obj, decoder_input_ids, past_key_values=None, *p_args, **p_kwargs):
                    if past_key_values is not None:
                        is_empty = False
                        if hasattr(past_key_values, "get_seq_length"):
                            try:
                                if past_key_values.get_seq_length() == 0:
                                    is_empty = True
                            except Exception:
                                pass
                        if is_empty:
                            past_key_values = None
                    return orig_prepare(decoder_input_ids, past_key_values, *p_args, **p_kwargs)
                self.prepare_inputs_for_generation = safe_prepare.__get__(self, self.__class__)
        transformers.modeling_utils.PreTrainedModel.__init__ = safe_model_init

        from transformers import AutoProcessor, AutoModelForCausalLM
        
        print(f"[VLM Manager] Loading microsoft/Florence-2-base on {_device}...")
        torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        
        # Use local cache to speed up loading
        _model = AutoModelForCausalLM.from_pretrained(
            "microsoft/Florence-2-base", 
            trust_remote_code=True, 
            torch_dtype=torch_dtype
        ).to(_device)
        
        _processor = AutoProcessor.from_pretrained(
            "microsoft/Florence-2-base", 
            trust_remote_code=True
        )
        print("[VLM Manager] Florence-2 loaded successfully.")
    return _model, _processor

def query_florence2_bbox(image_input, text_query):
    """
    Runs local Florence-2 Phrase Grounding to detect a semantic part in the image.
    Accepts either an image file path (str) or a PIL Image object.
    Returns: Bounding box as [x_min, y_min, x_max, y_max] or None if not found.
    """
    model, processor = get_florence2_model()
    
    try:
        if isinstance(image_input, str):
            with Image.open(image_input) as raw_img:
                img = raw_img.convert("RGB")
                w, h = img.size
                return _run_florence_on_pil_img(model, processor, img, text_query, w, h, os.path.basename(image_input))
        else:
            img = image_input.convert("RGB")
            w, h = img.size
            return _run_florence_on_pil_img(model, processor, img, text_query, w, h, "PIL Image")
    except Exception as e:
        print(f"  [VLM Error] Florence-2 failed: {e}")
        return None

def _run_florence_on_pil_img(model, processor, img, text_query, w, h, img_label):
    task_prompt = '<CAPTION_TO_PHRASE_GROUNDING>'
    prompt = task_prompt + text_query
    
    # Downscale image if either dimension exceeds 768px to avoid CUDA device-side assertion errors
    max_dim = 768
    if w > max_dim or h > max_dim:
        scale = max_dim / max(w, h)
        new_w, new_h = int(w * scale), int(h * scale)
        img_resized = img.resize((new_w, new_h), Image.Resampling.BILINEAR)
        # print(f"  [VLM Manager] Downscaled image from {w}x{h} to {new_w}x{new_h} for processing")
    else:
        img_resized = img
        
    # Prepare inputs
    torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32
    inputs = processor(text=prompt, images=img_resized, return_tensors="pt").to(_device, torch_dtype)
    
    # Run model inference
    with torch.no_grad():
        generated_ids = model.generate(
            input_ids=inputs["input_ids"],
            pixel_values=inputs["pixel_values"],
            max_new_tokens=1024,
            early_stopping=False,
            do_sample=False,
            num_beams=3,
        )
        
    generated_text = processor.batch_decode(generated_ids, skip_special_tokens=False)[0]
    parsed_answer = processor.post_process_generation(
        generated_text, 
        task=task_prompt, 
        image_size=(w, h)
    )
    
    # Extract results
    result = parsed_answer.get(task_prompt, {})
    bboxes = result.get('bboxes', [])
    
    if not bboxes:
        print(f"  [VLM Warning] Query '{text_query}' returned no boxes in {img_label}")
        return None
        
    # Merge boxes if there are multiple (e.g. multiple chair legs)
    x_min = min(box[0] for box in bboxes)
    y_min = min(box[1] for box in bboxes)
    x_max = max(box[2] for box in bboxes)
    y_max = max(box[3] for box in bboxes)
    
    bbox = [int(x_min), int(y_min), int(x_max), int(y_max)]
    print(f"  [VLM Success] Query '{text_query}' found box: {bbox}")
    return bbox

def unload_florence2_model():
    """Unloads model from GPU VRAM to prevent fragmentation."""
    global _model, _processor
    if _model is not None:
        print("[VLM Manager] Unloading Florence-2 from VRAM...")
        _model = None
        _processor = None
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            print("[VLM Manager] CUDA cache cleared.")

if __name__ == "__main__":
    # Test file
    import sys
    if len(sys.argv) > 2:
        img = sys.argv[1]
        query = sys.argv[2]
        res = query_florence2_bbox(img, query)
        print("Result:", res)
        unload_florence2_model()

