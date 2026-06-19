import os
import json
import time
from pathlib import Path
from typing import List

from app.publisher import get_post


def _try_select_and_fill(page, selectors: List[str], text: str) -> bool:
    for sel in selectors:
        try:
            el = page.query_selector(sel)
            if not el:
                continue

            tag = page.eval_on_selector(sel, "el => el.tagName.toLowerCase()")

            if tag in ("input", "textarea"):
                page.fill(sel, text)
            else:
                page.eval_on_selector(
                    sel,
                    """
                    (el, value) => {
                        el.focus();
                        el.innerText = value;
                        el.dispatchEvent(new InputEvent('input', {
                            bubbles: true,
                            inputType: 'insertText',
                            data: value
                        }));
                        el.dispatchEvent(new Event('change', {
                            bubbles: true
                        }));
                    }
                    """,
                    text,
                )

            return True

        except Exception:
            continue

    return False


def _try_upload_file(page, selectors: List[str], file_path: str) -> bool:
    for sel in selectors:
        try:
            input_el = page.query_selector(sel)
            if input_el:
                input_el.set_input_files(file_path)
                return True
        except Exception:
            continue
    return False


def _connect_existing_chrome(pw, cdp_url: str):
    print(f"尝试通过 CDP 连接到 Chrome: {cdp_url} ...")

    browser = pw.chromium.connect_over_cdp(cdp_url)

    contexts = browser.contexts
    if not contexts:
        raise RuntimeError("CDP 已连接，但没有可用 browser context")

    context = contexts[0]
    page = context.pages[0] if context.pages else context.new_page()

    print("已通过 CDP 连接到现有 Chrome。")
    return browser, context, page


def _launch_fallback_context(pw):
    print("回退到 Playwright 持久化浏览器。")

    profile_dir = Path("data/browser_profile/toutiao").resolve()
    profile_dir.mkdir(parents=True, exist_ok=True)

    context = pw.chromium.launch_persistent_context(
        user_data_dir=str(profile_dir),
        headless=False,
    )

    page = context.pages[0] if context.pages else context.new_page()
    return None, context, page


def publish_via_playwright(post_id: int, headless: bool = False):
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        raise RuntimeError(
            "Playwright is required. Install with: "
            "`python -m pip install playwright` and "
            "`python -m playwright install chromium`."
        )

    post = get_post(post_id)
    if not post:
        raise ValueError("找不到对应的待审帖")

    try:
        review = json.loads(post.review_json or "{}")
    except Exception:
        review = {}

    title = post.title
    content = post.content
    image_path = review.get("image_path")

    base_url = os.getenv("TOUTIAO_WEB_URL", "https://mp.toutiao.com")
    new_post_url = os.getenv("TOUTIAO_NEW_POST_URL")
    cdp_url = os.getenv("TOUTIAO_CDP_URL", "http://127.0.0.1:9222")

    connected_via_cdp = False
    browser = None
    context = None
    page = None

    with sync_playwright() as pw:
        try:
            browser, context, page = _connect_existing_chrome(pw, cdp_url)
            connected_via_cdp = True

        except Exception as e:
            print("CDP 连接失败原因：", repr(e))
            print(
                "如果想连接已登录 Chrome，请先关闭所有 Chrome，然后用命令启动：\n"
                r'"C:\Program Files\Google\Chrome\Application\chrome.exe" '
                r'--remote-debugging-port=9222 '
                r'--user-data-dir="C:\Users\kokon\Desktop\chrome_toutiao_profile"'
                "\n并确认这个地址能打开： http://127.0.0.1:9222/json/version\n"
            )
            browser, context, page = _launch_fallback_context(pw)

        if new_post_url:
            page.goto(new_post_url, wait_until="domcontentloaded")
        else:
            page.goto(base_url, wait_until="domcontentloaded")

        print(
            "已打开头条号后台。\n"
            "如果你还没登录，请先在浏览器里完成登录。\n"
            "然后手动进入“写文章/图文”页面，再回到终端按回车继续。"
        )
        input()

        title_selectors = [
            'input[placeholder*="标题"]',
            'input[placeholder*="请输入标题"]',
            'textarea[placeholder*="标题"]',
            'input[name="title"]',
            '#title',
        ]

        filled_title = _try_select_and_fill(page, title_selectors, title)
        if filled_title:
            print("已尝试填写标题。")
        else:
            print("未能自动填写标题，请手工粘贴。")

        content_selectors = [
            'div[contenteditable="true"]',
            '[contenteditable="true"]',
            'textarea[name="content"]',
            'textarea[placeholder*="正文"]',
            'textarea[placeholder*="内容"]',
        ]

        filled_content = _try_select_and_fill(page, content_selectors, content)
        if filled_content:
            print("已尝试填写正文。")
        else:
            print("未能自动填写正文，请手工粘贴/编辑。")

        if image_path and os.path.exists(image_path):
            file_selectors = [
                'input[type="file"]',
                'input[name="cover"]',
            ]

            uploaded = _try_upload_file(page, file_selectors, image_path)
            if uploaded:
                print("已尝试上传封面图片。")
            else:
                print("未能自动上传封面图片，请手工上传。")
        else:
            print("未找到封面图片，或路径不存在：", image_path)

        print("已完成自动填充。请人工检查并点击发布。按 Ctrl+C 关闭程序。")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("关闭发布浏览器。")
        finally:
            try:
                if connected_via_cdp:
                    # 不关闭你手动打开的 Chrome，只断开连接
                    if browser is not None:
                        browser.close()
                else:
                    if context is not None:
                        context.close()
            except Exception:
                pass