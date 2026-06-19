import json
import pyperclip
from typing import List

from app.llm import ask_llm
from app.utils import (
    ensure_dirs,
    read_text,
    write_text,
    now_id,
)
from app.prompt import (
    GENERATE_TOPICS_PROMPT,
    PLAN_TOPIC_PROMPT,
    TITLE_PROMPT,
    DRAFT_PROMPT,
    HUMANIZE_PROMPT,
)
from app.cover import make_cover
from app.publisher import queue_post


def generate_topics(account_name: str) -> str:
    style_profile = read_text(f"data/style_profiles/{account_name}.json")

    user_prompt = f"""
账号风格：
{style_profile}

请基于该账号风格和当前网络热点，生成 10 个适合该账号的候选选题。
"""

    return ask_llm(
        system_prompt=GENERATE_TOPICS_PROMPT,
        user_prompt=user_prompt,
        temperature=0.8,
    )


def choose_topics(topics_json: str) -> List[str]:
    try:
        data = json.loads(topics_json)
        return [topic.strip() for topic in data.get("topics", []) if topic.strip()]
    except Exception:
        lines = [
            line.strip(" -0123456789.、")
            for line in topics_json.splitlines()
            if line.strip()
        ]
        return lines


def plan_topic(account_name: str, topic: str) -> str:
    style_profile = read_text(f"data/style_profiles/{account_name}.json")

    user_prompt = f"""
账号风格：
{style_profile}

用户主题：
{topic}
"""

    return ask_llm(
        system_prompt=PLAN_TOPIC_PROMPT,
        user_prompt=user_prompt,
        temperature=0.6,
    )


def generate_titles(account_name: str, topic_plan: str) -> str:
    style_profile = read_text(f"data/style_profiles/{account_name}.json")

    user_prompt = f"""
账号风格：
{style_profile}

选题规划：
{topic_plan}
"""

    return ask_llm(
        system_prompt=TITLE_PROMPT,
        user_prompt=user_prompt,
        temperature=0.8,
    )


def choose_first_title(titles_json: str) -> str:
    try:
        data = json.loads(titles_json)
        return data["titles"][0]
    except Exception:
        # 防止模型偶尔没按 JSON 返回
        lines = [
            line.strip(" -0123456789.、")
            for line in titles_json.splitlines()
            if line.strip()
        ]
        return lines[0] if lines else ""


def write_draft(account_name: str, topic_plan: str, title: str) -> str:
    style_profile = read_text(f"data/style_profiles/{account_name}.json")

    prompt = DRAFT_PROMPT.format(
        style_profile=style_profile,
        topic_plan=topic_plan,
        title=title,
    )

    return ask_llm(
        system_prompt="你是今日头条内容创作者。",
        user_prompt=prompt,
        temperature=0.85,
    )


def humanize_article(article: str) -> str:
    return ask_llm(
        system_prompt=HUMANIZE_PROMPT,
        user_prompt=article,
        temperature=0.75,
    )


def write_article(account_name: str, topic: str, copy: bool = True):
    ensure_dirs()

    topic_plan = plan_topic(account_name, topic)
    titles_json = generate_titles(account_name, topic_plan)
    title = choose_first_title(titles_json)
    draft = write_draft(account_name, topic_plan, title)
    final_article = humanize_article(draft)

    article_id = now_id()
    output_path = f"data/outputs/{article_id}.txt"

    full_output = f"""# 选题规划

{topic_plan}

# 候选标题

{titles_json}

# 最终文章

{final_article}
"""

    write_text(output_path, full_output)

    # 生成封面并把文章入队待审
    try:
        cover_info = make_cover(output_path)
        image_path = cover_info.get("image_path")
    except Exception:
        image_path = ""

    post_id = queue_post(
        account=account_name,
        topic=topic,
        title=title,
        content=final_article,
        output_path=output_path,
        image_path=image_path,
    )

    if copy:
        pyperclip.copy(final_article)

    print(final_article)
    print(f"\n已保存: {output_path}")
    print(f"已生成封面: {image_path}")
    print(f"已入库待审，帖子 id={post_id}")
    if copy:
        print("已复制最终文章到剪贴板")