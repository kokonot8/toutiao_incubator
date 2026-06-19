import os
import json
from typing import List, Optional, Dict

import requests

from app.db import get_session
from app.models import GeneratedPost


def queue_post(account: str, topic: str, title: str, content: str, output_path: str = "", image_path: str = "") -> int:
    """把生成好的文章入库为待审帖。返回数据库 id。"""
    session = get_session()
    review = {
        "output_path": output_path,
        "image_path": image_path,
        "published": False,
    }
    post = GeneratedPost(
        account=account,
        topic=topic,
        title=title,
        content=content,
        review_json=json.dumps(review, ensure_ascii=False),
    )
    session.add(post)
    session.commit()
    session.refresh(post)
    return post.id


def list_pending() -> List[GeneratedPost]:
    session = get_session()
    posts = session.query(GeneratedPost).order_by(GeneratedPost.created_at.desc()).all()
    pending = []
    for p in posts:
        try:
            r = json.loads(p.review_json or "{}")
        except Exception:
            r = {}
        if not r.get("published"):
            pending.append(p)
    return pending


def get_post(post_id: int) -> Optional[GeneratedPost]:
    session = get_session()
    return session.get(GeneratedPost, post_id)


def update_post_review(
    post_id: int,
    title: str,
    content: str,
    extra: Optional[Dict] = None,
) -> None:
    session = get_session()
    post = session.get(GeneratedPost, post_id)
    if not post:
        raise ValueError("找不到对应的待审帖")
    post.title = title
    post.content = content
    try:
        review = json.loads(post.review_json or "{}")
    except Exception:
        review = {}
    if extra:
        review.update(extra)
    post.review_json = json.dumps(review, ensure_ascii=False)
    session.add(post)
    session.commit()


def publish_post(post_id: int, dry_run: bool = True) -> dict:
    post = get_post(post_id)
    if not post:
        raise ValueError("找不到对应的待审帖")

    try:
        review = json.loads(post.review_json or "{}")
    except Exception:
        review = {}

    api_url = os.getenv("TOUTIAO_API_URL")
    api_token = os.getenv("TOUTIAO_API_TOKEN")

    payload = {
        "title": post.title,
        "content": post.content,
        "account": post.account,
    }

    if dry_run:
        resp = {"ok": True, "dry_run": True, "would_post": payload, "image_path": review.get("image_path")}
    else:
        if not api_url:
            raise RuntimeError("缺少 TOUTIAO_API_URL，请在 .env 中设置")

        headers = {}
        if api_token:
            headers["Authorization"] = f"Bearer {api_token}"

        files = {}
        image_path = review.get("image_path")
        if image_path and os.path.exists(image_path):
            files["image"] = open(image_path, "rb")

        try:
            r = requests.post(api_url, data=payload, files=files or None, headers=headers, timeout=30)
            try:
                resp = r.json()
            except Exception:
                resp = {"status_code": r.status_code, "text": r.text}
        finally:
            if files:
                files["image"].close()

    # 更新发布状态（dry_run 仍记录尝试结果但不标记为发布）
    if not dry_run:
        review["published"] = True
        review["publish_response"] = resp
        session = get_session()
        db_post = session.get(GeneratedPost, post_id)
        db_post.review_json = json.dumps(review, ensure_ascii=False)
        session.add(db_post)
        session.commit()

    return resp
