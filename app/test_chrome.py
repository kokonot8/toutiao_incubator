from pathlib import Path
from playwright.sync_api import sync_playwright

with sync_playwright() as pw:
    profile_dir = Path("data/browser_profile/test").resolve()
    profile_dir.mkdir(parents=True, exist_ok=True)

    context = pw.chromium.launch_persistent_context(
        user_data_dir=str(profile_dir),
        headless=False,
        executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    )

    page = context.pages[0] if context.pages else context.new_page()
    page.goto("https://www.baidu.com")
    input("看到浏览器后按回车关闭")
    context.close()