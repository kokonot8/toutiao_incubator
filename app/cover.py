import json

from app.llm import ask_llm
from app.utils import ensure_dirs, read_text, write_text, now_id
from app.prompt import COVER_BRIEF_PROMPT
from app.image_generator import generate_image_hf


def make_cover_brief(article_file: str) -> dict:
    article = read_text(article_file)

    result = ask_llm(
        system_prompt=COVER_BRIEF_PROMPT,
        user_prompt=article,
        temperature=0.7,
    )

    try:
        return json.loads(result)
    except Exception:
        return {
            "core_visual": "一个年轻人独自站在城市街头，神情犹豫",
            "scene": "真实城市街道",
            "subject": "普通年轻人",
            "emotion": "迷茫、悬念",
            "camera": "中景，纪录片摄影感",
            "lighting": "自然光，略微阴天",
            "visual_style": "真实摄影风格",
            "background_keywords": ["city street", "young person"],
            "image_prompt": (
                "Realistic documentary photography of a young person "
                "standing alone on a city street, looking uncertain, "
                "natural light, cinematic composition, no text, no watermark"
            ),
            "negative_prompt": (
                "text, words, title, watermark, logo, cartoon, anime, "
                "illustration, exaggerated expression"
            ),
            "reason": result,
        }


def build_final_prompt(brief: dict) -> str:
    image_prompt = brief.get("image_prompt", "")
    negative_prompt = brief.get(
        "negative_prompt",
        "text, watermark, logo, cartoon, anime",
    )

    return f"""
{image_prompt}

Realistic editorial cover image, documentary photography, natural lighting, high quality.

Do not include: {negative_prompt}
""".strip()


def make_cover(article_file: str):
    ensure_dirs()

    brief = make_cover_brief(article_file)

    cover_id = now_id()
    brief_path = f"data/covers/{cover_id}.json"
    prompt_path = f"data/covers/{cover_id}_prompt.txt"
    image_path = f"data/covers/{cover_id}.png"

    final_prompt = build_final_prompt(brief)

    write_text(
        brief_path,
        json.dumps(brief, ensure_ascii=False, indent=2),
    )

    write_text(prompt_path, final_prompt)

    generate_image_hf(
        prompt=final_prompt,
        output_path=image_path,
    )

    print("封面视觉方案：")
    print(json.dumps(brief, ensure_ascii=False, indent=2))

    print(f"\n图片 Prompt 已保存: {prompt_path}")
    print(f"封面图片已生成: {image_path}")
    # 返回生成的封面信息，便于后续入库或发布流程使用
    return {
        "cover_id": cover_id,
        "brief_path": brief_path,
        "prompt_path": prompt_path,
        "image_path": image_path,
    }