import os
from pathlib import Path

from dotenv import load_dotenv
from huggingface_hub import InferenceClient

load_dotenv()

from typing import Optional

def generate_image_hf(
    prompt: str,
    output_path: str,
    model: Optional[str] = None,
):
    token = os.getenv("HF_TOKEN")
    if not token:
        raise RuntimeError("缺少 HF_TOKEN，请在 .env 里设置。")

    model = model or os.getenv(
        "HF_IMAGE_MODEL",
        "stabilityai/stable-diffusion-xl-base-1.0",
    )

    client = InferenceClient(api_key=token)

    image = client.text_to_image(
        prompt=prompt,
        model=model,
    )

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)
    return output_path