from pathlib import Path
from app.utils import ensure_dirs

def import_samples(account_name: str, source_file: str):
    ensure_dirs()

    src = Path(source_file)
    if not src.exists():
        raise FileNotFoundError(f"找不到样本文件: {source_file}")

    target = Path(f"data/samples/{account_name}.txt")
    target.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

    print(f"已导入样本: {target}")