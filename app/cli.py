import typer

from app.importer import import_samples
from app.style_analyzer import analyze_style
from app.writer import generate_topics, choose_topics, write_article
from app.cover import make_cover
from app.utils import ensure_dirs
from app.publisher import list_pending, get_post, update_post_review, publish_post
from typing import Optional
import click
from app.publisher_playwright import publish_via_playwright

app = typer.Typer()


@app.command()
def init():
    """
    初始化目录。
    """
    ensure_dirs()
    print("目录已初始化")


@app.command()
def import_samples_cmd(
    account: str,
    source_file: str,
):
    """
    导入对标账号样本。

    例：
    python -m app.cli import-samples-cmd demo samples/demo.txt
    """
    import_samples(account, source_file)


@app.command()
def analyze(
    account: str,
):
    """
    分析账号风格。

    例：
    python -m app.cli analyze demo
    """
    analyze_style(account)


@app.command()
def write(
    account: str,
    topic: Optional[str] = None,
    copy: bool = True,
):
    """
    根据账号风格和主题生成文章。如果不提供 topic，则会自动生成候选话题并让你选择。

    例：
    python -m app.cli write demo "荷兰找工作为什么这么难"
    python -m app.cli write demo
    """
    if not topic:
        topics_json = generate_topics(account)
        topics = choose_topics(topics_json)

        if not topics:
            raise ValueError("未能生成候选话题，请先检查账号风格是否已分析")

        print("自动生成的话题候选：")
        for idx, candidate in enumerate(topics, start=1):
            print(f"{idx}. {candidate}")

        choice = typer.prompt("请选择要生成的主题（输入序号，默认 1）", default="1")
        try:
            index = max(0, min(len(topics) - 1, int(choice.strip()) - 1))
        except ValueError:
            index = 0
        topic = topics[index]
        print(f"已选择主题：{topic}\n")

    write_article(account, topic, copy=copy)


@app.command()
def suggest(
    account: str,
    count: int = 10,
):
    """
    根据账号风格自动生成候选话题。

    例：
    python -m app.cli suggest demo
    """
    topics_json = generate_topics(account)
    topics = choose_topics(topics_json)
    print("自动生成的话题候选：")
    for idx, candidate in enumerate(topics[:count], start=1):
        print(f"{idx}. {candidate}")



@app.command()
def review(
    account: Optional[str] = None,
):
    """
    列出待审帖子并进入编辑/发布流程。

    例：
    python -m app.cli review demo
    """
    posts = list_pending()
    if account:
        posts = [p for p in posts if p.account == account]

    if not posts:
        print("当前没有待审帖子。")
        return

    print("待审帖子：")
    for idx, p in enumerate(posts, start=1):
        print(f"{idx}. id={p.id} account={p.account} title={p.title}")

    choice = typer.prompt("选择要审阅的序号（默认 1）", default="1")
    try:
        index = max(0, min(len(posts) - 1, int(choice.strip()) - 1))
    except ValueError:
        index = 0

    post = posts[index]

    editable = f"TITLE: {post.title}\n\n{post.content}"
    edited = click.edit(editable)
    if edited is None:
        print("未做修改，保持原内容。")
        title = post.title
        content = post.content
    else:
        # 简单解析：以第一行以 TITLE: 开头为标题，其余为正文
        lines = edited.splitlines()
        if lines and lines[0].startswith("TITLE:"):
            title = lines[0].split("TITLE:", 1)[1].strip()
            content = "\n".join(lines[2:]).strip() if len(lines) > 2 else ""
        else:
            # 回退到全文作为内容
            title = post.title
            content = edited

    update_post_review(post.id, title, content)
    print(f"已保存修改，id={post.id}")

    if typer.confirm("现在发布到今日头条？", default=False):
        resp = publish_post(post.id, dry_run=False)
        print("发布响应：")
        print(resp)


@app.command()
def publish(
    post_id: Optional[int] = None,
    dry_run: bool = True,
):
    """
    发布指定的待审帖（或交互选择）。

    例：
    python -m app.cli publish 12 --dry-run=False
    """
    if post_id is None:
        posts = list_pending()
        if not posts:
            print("当前没有待审帖子。")
            return
        print("待审帖子：")
        for idx, p in enumerate(posts, start=1):
            print(f"{idx}. id={p.id} account={p.account} title={p.title}")
        choice = typer.prompt("选择要发布的序号（默认 1）", default="1")
        try:
            index = max(0, min(len(posts) - 1, int(choice.strip()) - 1))
        except ValueError:
            index = 0
        post = posts[index]
        post_id = post.id

    if not typer.confirm(f"确认发布帖子 id={post_id} ?", default=False):
        print("已取消")
        return

    resp = publish_post(post_id, dry_run=dry_run)
    print("发布响应：")
    print(resp)


@app.command()
def publish_web(
    post_id: Optional[int] = None,
    headless: bool = False,
):
    """
    使用 Playwright 打开网页半自动发布（打开浏览器并填写内容，停在发布前）。

    例：
    python -m app.cli publish-web 12
    """
    if post_id is None:
        posts = list_pending()
        if not posts:
            print("当前没有待审帖子。")
            return
        print("待审帖子：")
        for idx, p in enumerate(posts, start=1):
            print(f"{idx}. id={p.id} account={p.account} title={p.title}")
        choice = typer.prompt("选择要发布的序号（默认 1）", default="1")
        try:
            index = max(0, min(len(posts) - 1, int(choice.strip()) - 1))
        except ValueError:
            index = 0
        post = posts[index]
        post_id = post.id

    print("将在浏览器中打开并协助填写，按 Ctrl+C 关闭时会结束会话。")
    publish_via_playwright(post_id, headless=headless)


@app.command()
def cover(
    article_file: str,
):
    """
    根据文章生成封面图。

    例：
    python -m app.cli cover data/outputs/xxx.txt
    """
    make_cover(article_file)


if __name__ == "__main__":
    app()