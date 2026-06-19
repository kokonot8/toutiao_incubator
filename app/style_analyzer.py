import json
from app.llm import ask_llm
from app.utils import ensure_dirs, read_text, write_text
from app.prompt import STYLE_ANALYSIS_PROMPT


def analyze_style(account_name: str):
    ensure_dirs()

    sample_path = f"data/samples/{account_name}.txt"
    samples = read_text(sample_path)

    result = ask_llm(
        system_prompt=STYLE_ANALYSIS_PROMPT,
        user_prompt=samples,
        temperature=0.2,
    )

    output_path = f"data/style_profiles/{account_name}.json"
    write_text(output_path, result)

    print(f"风格画像已生成: {output_path}")
    print(result)