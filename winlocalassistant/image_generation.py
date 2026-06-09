from __future__ import annotations

import base64
import json
import os
import re
import time
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .safe_io import atomic_write_bytes, atomic_write_text

DEFAULT_SDWEBUI_URL = "http://127.0.0.1:7860"
DEFAULT_COMFYUI_URL = "http://127.0.0.1:8188"
DEFAULT_IMAGE_NEGATIVE_PROMPT = (
    "worst quality, low quality, lowres, blurry, out of focus, jpeg artifacts, "
    "distorted face, deformed face, asymmetrical face, warped face, duplicate face, "
    "bad eyes, crossed eyes, uneven eyes, malformed pupils, warped mouth, bad teeth, "
    "bad anatomy, disfigured, mutated, extra limbs, extra fingers, missing fingers, "
    "text artifacts, watermark, logo, signature, nsfw, nude, naked, exposed genitals"
)
GENERAL_QUALITY_PROMPT = "high quality, sharp focus, coherent composition, clean details, no text artifacts"
FACE_QUALITY_PROMPT = (
    "high quality, sharp focus, natural facial proportions, symmetrical eyes, detailed eyes, "
    "coherent face, realistic skin texture, fully clothed, non-explicit"
)
PERSON_PROMPT_RE = re.compile(r"\b(face|portrait|person|people|human|woman|man|girl|boy|character|mascot|selfie)\b", re.IGNORECASE)
UNSAFE_PROMPT_RE = re.compile(r"\b(naked|nude|nudity|nsfw|topless|porn|explicit)\b", re.IGNORECASE)


@dataclass
class ImageGenerationResult:
    ok: bool
    backend: str
    message: str
    path: str = ""
    details: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["details"] = data.get("details") or {}
        return data


def _now_id() -> str:
    return time.strftime("%Y%m%d_%H%M%S") + f"_{int(time.time() * 1000) % 1000:03d}"


def _env(name: str, default: str = "") -> str:
    return (os.environ.get(name) or default).strip()


def _slug(text: str, limit: int = 64) -> str:
    s = re.sub(r"[^A-Za-z0-9._-]+", "_", text or "generated_image").strip("._")
    return (s or "generated_image")[:limit]


def _negative_prompt() -> str:
    configured = _env("NOVA_IMAGE_NEGATIVE_PROMPT", DEFAULT_IMAGE_NEGATIVE_PROMPT)
    required = ["distorted face", "deformed face", "bad eyes", "bad anatomy", "nsfw", "nude", "naked"]
    lower = configured.lower()
    missing = [term for term in required if term not in lower]
    return ", ".join([configured, *missing]) if missing else configured


def prepare_image_prompt(prompt: str) -> dict[str, Any]:
    """Return prompt text tuned for fewer malformed faces and safer body prompts."""
    original = (prompt or "").strip()
    cleaned = re.sub(r"\b(ignore|avoid|no)\s+(naked|nude|nudity|nsfw)\b", "fully clothed", original, flags=re.IGNORECASE)
    cleaned = UNSAFE_PROMPT_RE.sub("fully clothed", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" ,")
    safety_rewritten = cleaned != original
    if safety_rewritten and "non-explicit" not in cleaned.lower():
        cleaned = f"{cleaned}, non-explicit, modest clothing"
    enhance = _env("NOVA_IMAGE_ENHANCE_PROMPT", "1").lower() not in {"0", "false", "no", "off"}
    quality_prompt = _env("NOVA_IMAGE_QUALITY_PROMPT", "")
    if enhance and not quality_prompt:
        quality_prompt = FACE_QUALITY_PROMPT if PERSON_PROMPT_RE.search(cleaned or original) else GENERAL_QUALITY_PROMPT
    enhanced = cleaned
    if quality_prompt and quality_prompt.lower() not in enhanced.lower():
        enhanced = f"{enhanced}, {quality_prompt}" if enhanced else quality_prompt
    return {
        "original_prompt": original,
        "prompt": enhanced,
        "negative_prompt": _negative_prompt(),
        "quality_prompt": quality_prompt,
        "safety_rewritten": safety_rewritten,
    }


def _http_json(url: str, payload: dict[str, Any] | None = None, *, timeout: float = 2.0) -> dict[str, Any] | None:
    try:
        data = None
        headers = {"Accept": "application/json"}
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=data, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
        if not raw:
            return {}
        return json.loads(raw.decode("utf-8", errors="replace"))
    except Exception:
        return None


def _is_sdwebui_available(url: str | None = None) -> bool:
    root = (url or _env("NOVA_SDWEBUI_URL", DEFAULT_SDWEBUI_URL)).rstrip("/")
    return _http_json(root + "/sdapi/v1/options", timeout=0.8) is not None


def _is_comfyui_available(url: str | None = None) -> bool:
    root = (url or _env("NOVA_COMFYUI_URL", DEFAULT_COMFYUI_URL)).rstrip("/")
    return _http_json(root + "/system_stats", timeout=0.8) is not None


def _diffusers_import_available() -> bool:
    try:
        import diffusers  # noqa: F401
        import PIL  # noqa: F401
        import torch  # noqa: F401
        return True
    except Exception:
        return False


def image_generation_status() -> dict[str, Any]:
    """Return real image backend availability without doing a generation."""
    configured = (_env("NOVA_IMAGE_BACKEND", "auto") or "auto").lower()
    sd_url = _env("NOVA_SDWEBUI_URL", DEFAULT_SDWEBUI_URL)
    comfy_url = _env("NOVA_COMFYUI_URL", DEFAULT_COMFYUI_URL)
    diffusers_model = _env("NOVA_DIFFUSERS_MODEL", "")
    status = {
        "configured_backend": configured,
        "sdwebui": {"url": sd_url, "available": _is_sdwebui_available(sd_url)},
        "comfyui": {"url": comfy_url, "available": _is_comfyui_available(comfy_url), "note": "status detection only unless a custom workflow integration is added"},
        "diffusers": {
            "installed": _diffusers_import_available(),
            "model": diffusers_model or "not set",
            "download_allowed": _env("NOVA_ALLOW_DIFFUSERS_DOWNLOAD", "0") in {"1", "true", "yes", "on"},
        },
        "svg_draft": {"available": True, "note": "draft placeholder only, not real image generation"},
    }
    ready = bool(status["sdwebui"]["available"] or (status["diffusers"]["installed"] and (diffusers_model or status["diffusers"]["download_allowed"])))
    status["ready_for_real_generation"] = ready
    return status


def render_image_generation_status() -> str:
    s = image_generation_status()
    lines = [
        "Image generation status",
        "",
        f"Configured backend: `{s['configured_backend']}`",
        f"Real generation ready: {'yes' if s['ready_for_real_generation'] else 'no'}",
        "",
        f"- Stable Diffusion WebUI API: {'available' if s['sdwebui']['available'] else 'not reachable'} at `{s['sdwebui']['url']}`",
        f"- Diffusers: {'installed' if s['diffusers']['installed'] else 'not installed'}; model: `{s['diffusers']['model']}`; download allowed: {s['diffusers']['download_allowed']}",
        f"- ComfyUI: {'reachable' if s['comfyui']['available'] else 'not reachable'} at `{s['comfyui']['url']}` (not used automatically yet)",
        "- SVG draft fallback: available, but this is not real image generation",
        "",
        "To enable real local image generation, use one of these:",
        "1. Run AUTOMATIC1111/Stable Diffusion WebUI with `--api`, then set `NOVA_IMAGE_BACKEND=sdwebui` if needed.",
        "2. Install `diffusers torch pillow accelerate`, set `NOVA_IMAGE_BACKEND=diffusers`, and set `NOVA_DIFFUSERS_MODEL` to a local model folder or Hugging Face model id.",
        "",
        "Use `/image-draft PROMPT` when you only want the old SVG placeholder card.",
    ]
    return "\n".join(lines)


def render_image_setup_wizard() -> str:
    s = image_generation_status()
    lines = [
        "# Image Setup Wizard",
        "",
        "Image generation status",
        "",
        f"Current backend setting: `{s['configured_backend']}`",
        f"Ready for real generation/editing: {'yes' if s['ready_for_real_generation'] else 'no'}",
        "",
        "## Pick One Backend",
        "1. Stable Diffusion WebUI: start it with `--api`, then set `NOVA_IMAGE_BACKEND=sdwebui` and optionally `NOVA_SDWEBUI_URL=http://127.0.0.1:7860`.",
        "2. Diffusers: install `diffusers torch pillow accelerate`, set `NOVA_IMAGE_BACKEND=diffusers`, and set `NOVA_DIFFUSERS_MODEL` to a local model folder or model id.",
        "3. ComfyUI: Nova currently detects ComfyUI status for image/video planning; use SD WebUI or Diffusers for `/image-generate` and `/image-edit` until a concrete ComfyUI image workflow is configured.",
        "",
        "## Test Commands",
        "1. `/image-status`",
        "2. `/image-generate a small friendly robot in a workshop`",
        "3. Attach or upload a PNG/JPG, then run `/image-edit latest => make the lighting warmer while preserving composition`.",
        "4. `/image-draft a labelled placeholder card` only when you intentionally want a non-AI SVG draft.",
        "",
        "## Safety Checks",
        "- `/image-generate` refuses to fake real image generation when no backend is ready.",
        "- `/image-edit` refuses to run unless the source image exists inside the workspace or upload context.",
        "- Unsafe nude/NSFW prompt fragments are rewritten toward fully clothed, non-explicit output and reinforced in the negative prompt.",
    ]
    return "\n".join(lines)


def _create_svg_draft(prompt: str, *, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"image_draft_{_now_id()}.svg"
    title = (prompt or "image draft").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")[:220]
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="640" viewBox="0 0 1024 640">
  <defs><linearGradient id="g" x1="0" x2="1" y1="0" y2="1"><stop stop-color="#dbeafe"/><stop offset="1" stop-color="#f8fafc"/></linearGradient></defs>
  <rect width="1024" height="640" fill="url(#g)"/>
  <rect x="72" y="82" width="880" height="476" rx="32" fill="white" stroke="#2563eb" stroke-width="4"/>
  <text x="512" y="220" text-anchor="middle" font-family="Segoe UI, Arial" font-size="42" font-weight="700" fill="#0f172a">SVG draft only</text>
  <text x="512" y="302" text-anchor="middle" font-family="Segoe UI, Arial" font-size="26" fill="#1e3a8a">{title}</text>
  <text x="512" y="390" text-anchor="middle" font-family="Segoe UI, Arial" font-size="20" fill="#475569">This is not AI image generation. Configure SD WebUI or Diffusers for real images.</text>
</svg>\n'''
    atomic_write_text(path, svg)
    return path


def create_svg_draft(prompt: str, *, output_dir: Path) -> Path:
    return _create_svg_draft(prompt, output_dir=output_dir)


def _generate_sdwebui(prompt: str, *, output_dir: Path, width: int, height: int, steps: int, seed: int) -> ImageGenerationResult:
    root = _env("NOVA_SDWEBUI_URL", DEFAULT_SDWEBUI_URL).rstrip("/")
    if not _is_sdwebui_available(root):
        return ImageGenerationResult(False, "sdwebui", "Stable Diffusion WebUI API is not reachable. Start WebUI with --api or choose another backend.", details={"url": root})
    prompt_meta = prepare_image_prompt(prompt)
    payload = {
        "prompt": prompt_meta["prompt"],
        "negative_prompt": prompt_meta["negative_prompt"],
        "steps": max(1, min(int(steps), 80)),
        "width": max(64, min(int(width), 2048)),
        "height": max(64, min(int(height), 2048)),
        "batch_size": 1,
        "n_iter": 1,
        "seed": int(seed),
        "sampler_name": _env("NOVA_SDWEBUI_SAMPLER", "Euler a"),
    }
    timeout = float(_env("NOVA_IMAGE_TIMEOUT_SEC", "420") or "420")
    result = _http_json(root + "/sdapi/v1/txt2img", payload, timeout=timeout)
    if not result or not result.get("images"):
        return ImageGenerationResult(False, "sdwebui", "Stable Diffusion WebUI returned no image data.", details={"url": root})
    raw = str(result["images"][0])
    if "," in raw and raw.startswith("data:"):
        raw = raw.split(",", 1)[1]
    data = base64.b64decode(raw)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"generated_image_{_now_id()}_{_slug(prompt_meta['prompt'], 24)}.png"
    atomic_write_bytes(path, data)
    return ImageGenerationResult(True, "sdwebui", "Generated a real image with Stable Diffusion WebUI.", str(path), {"url": root, "width": width, "height": height, "steps": steps, "seed": seed, **prompt_meta})


def _image_b64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


def _generate_sdwebui_img2img(prompt: str, source_image: Path, *, output_dir: Path, width: int, height: int, steps: int, seed: int, strength: float) -> ImageGenerationResult:
    root = _env("NOVA_SDWEBUI_URL", DEFAULT_SDWEBUI_URL).rstrip("/")
    if not _is_sdwebui_available(root):
        return ImageGenerationResult(False, "sdwebui", "Stable Diffusion WebUI API is not reachable. Start WebUI with --api or choose another backend.", details={"url": root})
    prompt_meta = prepare_image_prompt(prompt)
    payload = {
        "prompt": prompt_meta["prompt"],
        "negative_prompt": prompt_meta["negative_prompt"],
        "init_images": [_image_b64(source_image)],
        "denoising_strength": max(0.05, min(float(strength), 1.0)),
        "steps": max(1, min(int(steps), 80)),
        "width": max(64, min(int(width), 2048)),
        "height": max(64, min(int(height), 2048)),
        "batch_size": 1,
        "n_iter": 1,
        "seed": int(seed),
        "sampler_name": _env("NOVA_SDWEBUI_SAMPLER", "Euler a"),
    }
    timeout = float(_env("NOVA_IMAGE_TIMEOUT_SEC", "420") or "420")
    result = _http_json(root + "/sdapi/v1/img2img", payload, timeout=timeout)
    if not result or not result.get("images"):
        return ImageGenerationResult(False, "sdwebui", "Stable Diffusion WebUI returned no edited image data.", details={"url": root, "source": str(source_image)})
    raw = str(result["images"][0])
    if "," in raw and raw.startswith("data:"):
        raw = raw.split(",", 1)[1]
    data = base64.b64decode(raw)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"edited_image_{_now_id()}_{_slug(prompt_meta['prompt'], 24)}.png"
    atomic_write_bytes(path, data)
    return ImageGenerationResult(True, "sdwebui", "Edited a real image with Stable Diffusion WebUI.", str(path), {"url": root, "source": str(source_image), "width": width, "height": height, "steps": steps, "seed": seed, "strength": strength, **prompt_meta})


def _generate_diffusers(prompt: str, *, output_dir: Path, width: int, height: int, steps: int, seed: int) -> ImageGenerationResult:
    model_id = _env("NOVA_DIFFUSERS_MODEL", "")
    allow_download = _env("NOVA_ALLOW_DIFFUSERS_DOWNLOAD", "0").lower() in {"1", "true", "yes", "on"}
    if not model_id:
        if not allow_download:
            return ImageGenerationResult(False, "diffusers", "Diffusers backend is not configured. Set NOVA_DIFFUSERS_MODEL to a local model folder/model id, or set NOVA_ALLOW_DIFFUSERS_DOWNLOAD=1 to allow first-run model download.", details={})
        model_id = "stable-diffusion-v1-5/stable-diffusion-v1-5"
    try:
        import torch
        from diffusers import AutoPipelineForText2Image
    except Exception as exc:
        return ImageGenerationResult(False, "diffusers", "Diffusers backend is not installed. Install diffusers, torch, pillow, and accelerate.", details={"error": str(exc)})
    try:
        cuda = bool(torch.cuda.is_available())
        dtype = torch.float16 if cuda else torch.float32
        pipe = AutoPipelineForText2Image.from_pretrained(model_id, torch_dtype=dtype, use_safetensors=True)
        if cuda:
            try:
                pipe.enable_model_cpu_offload()
            except Exception:
                pipe = pipe.to("cuda")
        else:
            pipe = pipe.to("cpu")
        try:
            pipe.enable_vae_slicing()
        except Exception:
            import logging as _wla_logging
            _wla_logging.getLogger(__name__).debug("Suppressed optional exception", exc_info=True)
        gen_device = "cuda" if cuda else "cpu"
        generator = torch.Generator(device=gen_device).manual_seed(int(seed))
        prompt_meta = prepare_image_prompt(prompt)
        image = pipe(
            prompt_meta["prompt"],
            negative_prompt=prompt_meta["negative_prompt"],
            width=max(64, min(int(width), 2048)),
            height=max(64, min(int(height), 2048)),
            num_inference_steps=max(1, min(int(steps), 80)),
            generator=generator,
        ).images[0]
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / f"generated_image_{_now_id()}_{_slug(prompt_meta['prompt'], 24)}.png"
        image.save(path)
        return ImageGenerationResult(True, "diffusers", "Generated a real image with Diffusers.", str(path), {"model": model_id, "device": gen_device, "width": width, "height": height, "steps": steps, "seed": seed, **prompt_meta})
    except Exception as exc:
        return ImageGenerationResult(False, "diffusers", "Diffusers image generation failed.", details={"model": model_id, "error": repr(exc)})


def _edit_diffusers(prompt: str, source_image: Path, *, output_dir: Path, width: int, height: int, steps: int, seed: int, strength: float) -> ImageGenerationResult:
    model_id = _env("NOVA_DIFFUSERS_MODEL", "")
    allow_download = _env("NOVA_ALLOW_DIFFUSERS_DOWNLOAD", "0").lower() in {"1", "true", "yes", "on"}
    if not model_id:
        if not allow_download:
            return ImageGenerationResult(False, "diffusers", "Diffusers image editing is not configured. Set NOVA_DIFFUSERS_MODEL to a local model folder/model id, or set NOVA_ALLOW_DIFFUSERS_DOWNLOAD=1 to allow first-run model download.", details={"source": str(source_image)})
        model_id = "stable-diffusion-v1-5/stable-diffusion-v1-5"
    try:
        import torch
        from diffusers import AutoPipelineForImage2Image
        from PIL import Image
    except Exception as exc:
        return ImageGenerationResult(False, "diffusers", "Diffusers image editing dependencies are not installed. Install diffusers, torch, pillow, and accelerate.", details={"error": str(exc)})
    try:
        cuda = bool(torch.cuda.is_available())
        dtype = torch.float16 if cuda else torch.float32
        pipe = AutoPipelineForImage2Image.from_pretrained(model_id, torch_dtype=dtype, use_safetensors=True)
        if cuda:
            try:
                pipe.enable_model_cpu_offload()
            except Exception:
                pipe = pipe.to("cuda")
        else:
            pipe = pipe.to("cpu")
        source = Image.open(source_image).convert("RGB")
        if width and height:
            source = source.resize((max(64, min(int(width), 2048)), max(64, min(int(height), 2048))))
        gen_device = "cuda" if cuda else "cpu"
        generator = torch.Generator(device=gen_device).manual_seed(int(seed))
        prompt_meta = prepare_image_prompt(prompt)
        image = pipe(
            prompt_meta["prompt"],
            image=source,
            negative_prompt=prompt_meta["negative_prompt"],
            strength=max(0.05, min(float(strength), 1.0)),
            num_inference_steps=max(1, min(int(steps), 80)),
            generator=generator,
        ).images[0]
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / f"edited_image_{_now_id()}_{_slug(prompt_meta['prompt'], 24)}.png"
        image.save(path)
        return ImageGenerationResult(True, "diffusers", "Edited a real image with Diffusers.", str(path), {"model": model_id, "device": gen_device, "source": str(source_image), "width": source.width, "height": source.height, "steps": steps, "seed": seed, "strength": strength, **prompt_meta})
    except Exception as exc:
        return ImageGenerationResult(False, "diffusers", "Diffusers image editing failed.", details={"model": model_id, "source": str(source_image), "error": repr(exc)})


def generate_image(prompt: str, *, output_dir: Path, backend: str = "auto", width: int = 512, height: int = 512, steps: int = 25, seed: int | None = None) -> ImageGenerationResult:
    prompt = (prompt or "").strip()
    if not prompt:
        return ImageGenerationResult(False, "none", "No image prompt supplied.")
    backend = (_env("NOVA_IMAGE_BACKEND", backend or "auto") or "auto").lower().strip()
    seed = int(seed if seed is not None else int(time.time()) % 2_147_483_647)
    if backend in {"svg", "draft", "placeholder"}:
        path = _create_svg_draft(prompt, output_dir=output_dir)
        return ImageGenerationResult(True, "svg_draft", "Created an SVG draft placeholder. This is not real AI image generation.", str(path), {"prompt": prompt})
    if backend in {"sdwebui", "automatic1111", "a1111"}:
        return _generate_sdwebui(prompt, output_dir=output_dir, width=width, height=height, steps=steps, seed=seed)
    if backend == "diffusers":
        return _generate_diffusers(prompt, output_dir=output_dir, width=width, height=height, steps=steps, seed=seed)
    if backend == "auto":
        if _is_sdwebui_available():
            return _generate_sdwebui(prompt, output_dir=output_dir, width=width, height=height, steps=steps, seed=seed)
        # Only auto-run diffusers when it is explicitly configured; otherwise it may unexpectedly download GBs of weights.
        if _diffusers_import_available() and (_env("NOVA_DIFFUSERS_MODEL") or _env("NOVA_ALLOW_DIFFUSERS_DOWNLOAD", "0").lower() in {"1", "true", "yes", "on"}):
            return _generate_diffusers(prompt, output_dir=output_dir, width=width, height=height, steps=steps, seed=seed)
        # No real backend is ready. Do not create a placeholder from /image-generate,
        # because users interpret that command as real image generation. Use /image-draft
        # explicitly for labelled SVG placeholders.
        return ImageGenerationResult(
            False,
            "none",
            "Image generation is not ready: no real image-generation backend is configured or reachable. Run /image-status for setup details, or use /image-draft for a labelled SVG placeholder.",
            "",
            details=image_generation_status(),
        )
    return ImageGenerationResult(False, backend, f"Unknown image backend `{backend}`. Use auto, sdwebui, diffusers, or svg.", details=image_generation_status())


def edit_image(prompt: str, source_image: Path, *, output_dir: Path, backend: str = "auto", width: int = 512, height: int = 512, steps: int = 25, seed: int | None = None, strength: float = 0.55) -> ImageGenerationResult:
    prompt = (prompt or "").strip()
    source_image = Path(source_image)
    if not prompt:
        return ImageGenerationResult(False, "none", "No image edit prompt supplied.")
    if not source_image.exists() or not source_image.is_file():
        return ImageGenerationResult(False, "none", "Source image file not found.", details={"source": str(source_image)})
    backend = (_env("NOVA_IMAGE_BACKEND", backend or "auto") or "auto").lower().strip()
    seed = int(seed if seed is not None else int(time.time()) % 2_147_483_647)
    if backend in {"sdwebui", "automatic1111", "a1111"}:
        return _generate_sdwebui_img2img(prompt, source_image, output_dir=output_dir, width=width, height=height, steps=steps, seed=seed, strength=strength)
    if backend == "diffusers":
        return _edit_diffusers(prompt, source_image, output_dir=output_dir, width=width, height=height, steps=steps, seed=seed, strength=strength)
    if backend == "auto":
        if _is_sdwebui_available():
            return _generate_sdwebui_img2img(prompt, source_image, output_dir=output_dir, width=width, height=height, steps=steps, seed=seed, strength=strength)
        if _diffusers_import_available() and (_env("NOVA_DIFFUSERS_MODEL") or _env("NOVA_ALLOW_DIFFUSERS_DOWNLOAD", "0").lower() in {"1", "true", "yes", "on"}):
            return _edit_diffusers(prompt, source_image, output_dir=output_dir, width=width, height=height, steps=steps, seed=seed, strength=strength)
        return ImageGenerationResult(
            False,
            "none",
            "Image editing is not ready: no real image-editing backend is configured or reachable. Run /image-status for setup details.",
            "",
            details={**image_generation_status(), "source": str(source_image)},
        )
    return ImageGenerationResult(False, backend, f"Unknown image backend `{backend}`. Use auto, sdwebui, or diffusers.", details=image_generation_status())


# NOVA_MEDIA_V55_3_160
IMAGE_STYLE_PRESETS: dict[str, dict[str, Any]] = {
    "cinematic": {"size": "1344x768", "prefix": "cinematic lighting, coherent composition, dynamic camera angle", "steps": 28},
    "concept": {"size": "1024x1024", "prefix": "concept art, clean silhouette, readable shapes, polished design", "steps": 24},
    "photo": {"size": "1024x768", "prefix": "natural photography, realistic lighting, sharp subject, believable lens", "steps": 25},
    "poster": {"size": "1024x1536", "prefix": "poster composition, strong focal point, readable layout, no text artifacts", "steps": 30},
    "sprite": {"size": "768x768", "prefix": "game asset, isolated subject, clean edges, orthographic readable design", "steps": 20},
}


def build_image_prompt_plan(prompt: str, *, style: str = "cinematic", variations: int = 4, size: str | None = None) -> dict[str, Any]:
    """Create a deterministic image-generation prompt pack before invoking heavy backends.

    This improves media UX because Nova can show exactly what it will ask SD WebUI,
    Diffusers, or ComfyUI to create instead of silently using a weak/default prompt.
    """
    base = (prompt or "").strip() or "a polished Nova media image"
    style_key = (style or "cinematic").strip().lower()
    preset = IMAGE_STYLE_PRESETS.get(style_key, IMAGE_STYLE_PRESETS["cinematic"])
    requested_size = size or str(preset.get("size") or "1024x768")
    try:
        count = max(1, min(int(variations), 8))
    except Exception:
        count = 4
    prepared = prepare_image_prompt(base)
    variants: list[dict[str, Any]] = []
    variant_suffixes = [
        "hero composition, clear foreground subject",
        "wide establishing composition, environmental storytelling",
        "close detail shot, expressive texture and lighting",
        "alternate angle, stronger color contrast",
        "clean product-style framing",
        "dramatic backlight and atmosphere",
        "simple readable thumbnail composition",
        "high-detail final render direction",
    ]
    seed_base = abs(hash(base + style_key)) % 1_000_000
    prefix = str(preset.get("prefix") or "")
    for idx in range(count):
        prompt_text = ", ".join(x for x in [prefix, prepared["prompt"], variant_suffixes[idx]] if x)
        variants.append({
            "id": f"image_variant_{idx+1}",
            "prompt": prompt_text,
            "negative_prompt": prepared["negative_prompt"],
            "style": style_key,
            "size": requested_size,
            "steps": int(preset.get("steps") or 25),
            "seed": seed_base + idx + 1,
            "safety_rewritten": prepared.get("safety_rewritten", False),
        })
    return {
        "ok": True,
        "original_prompt": base,
        "style": style_key,
        "size": requested_size,
        "variation_count": count,
        "backend_ready": image_generation_status().get("ready_for_real_generation", False),
        "variants": variants,
        "next_steps": [
            "Review the prompt pack.",
            "Run /image-generate with the preferred variant prompt when a real backend is ready.",
            "Use /image-draft only for non-AI placeholder drafts.",
        ],
    }


def render_image_prompt_plan_markdown(plan: dict[str, Any]) -> str:
    lines = [
        "# Nova Image Prompt Plan",
        "",
        f"Prompt: {plan.get('original_prompt','')}",
        f"Style: `{plan.get('style','cinematic')}`  Size: `{plan.get('size','')}`",
        f"Real backend ready: {'yes' if plan.get('backend_ready') else 'no'}",
        "",
        "## Variants",
    ]
    for item in plan.get("variants", []):
        lines.append(f"- **{item.get('id')}** seed={item.get('seed')} steps={item.get('steps')} size={item.get('size')}")
        lines.append(f"  - Prompt: {item.get('prompt')}")
        lines.append(f"  - Negative: {item.get('negative_prompt')}")
    lines += ["", "## Next", *[f"- {x}" for x in plan.get("next_steps", [])]]
    return "\n".join(lines)


def write_image_prompt_pack(prompt: str, output_dir: Path | str, *, style: str = "cinematic", variations: int = 4, size: str | None = None) -> Path:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    plan = build_image_prompt_plan(prompt, style=style, variations=variations, size=size)
    path = output_dir / "image_prompt_pack.json"
    atomic_write_text(path, json.dumps(plan, indent=2), encoding="utf-8")
    md = output_dir / "IMAGE_PROMPT_PACK.md"
    atomic_write_text(md, render_image_prompt_plan_markdown(plan), encoding="utf-8")
    return path
