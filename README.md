# Toutiao Agent MVP

一个最小可跑的“对标账号风格生成今日头条文案”CLI。

本产品提供 PC 版和移动版两种使用方式。
PC 版为半自动发布 Agent：用户完成一次头条号网页登录后，系统可自动分析对标账号、生成选题、标题、正文和封面，并自动打开头条号后台填写内容、上传封面，用户仅需最后检查并点击发布即可。

移动版为内容生成工作台（微信小程序或移动网页）：用户可在手机上随时生成选题、文章和封面图片，一键复制正文、保存封面，但由于今日头条目前未开放图文发布 API，移动端暂不支持自动发帖，需用户手动打开头条 App 完成发布。

这样既满足轻量用户随时创作的需求，也为重度运营用户提供高效率的半自动发布能力。

## 安装

```bash
cd toutiao_agent
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
cp .env.example .env
# 然后把 .env 里的 DEEPSEEK_API_KEY 改成你的 key
```

## 使用

### 1. 导入对标账号样本

准备一个 txt 文件，例如 `samples/account_a.txt`：

```txt
TITLE: 第一个标题
正文正文正文

---
TITLE: 第二个标题
正文正文正文
```

导入：

```bash
python -m app.cli import-samples account_a samples/account_a.txt
```

### 2. 分析风格

```bash
python -m app.cli analyze-style account_a
```

### 3. 生成文章

```bash
python -m app.cli write account_a --topic "荷兰找工作为什么这么难"
```

当你没有明确主题时，也可以直接让工具自动生成候选话题并选择：

```bash
python -m app.cli write account_a
```

如果你只想先看候选话题，可以使用：

```bash
python -m app.cli suggest account_a
```

生成结果会保存到 `outputs/`，也会尝试复制到剪贴板。
