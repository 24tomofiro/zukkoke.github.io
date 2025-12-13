import os
import datetime
import google.generativeai as genai

# GitHub Actionsの環境変数からAPIキーを取得
API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("GEMINI_API_KEY is not set")

genai.configure(api_key=API_KEY)

# 今日の日付
today = datetime.date.today()
date_str = today.strftime('%Y-%m-%d')
date_compact = today.strftime('%Y%m%d')

# 生成するモデルの設定
model = genai.GenerativeModel('gemini-1.5-flash')

# プロンプト（あなたが指定したフォーマットを厳守させる）
prompt = f"""
あなたはプロのテックブロガーです。以下のフォーマットルールに厳密に従って、GitHub Pages用のMarkdown記事を1つ作成してください。

## テーマ
「今日のPythonの豆知識」または「AI技術の最新トレンド」について、ランダムに1つ選んで書いてください。

## 必須フォーマットルール
1. Front Matterを必ず含めること。
   - layout: post
   - read_time: true
   - show_date: true
   - title: (魅力的なタイトル)
   - date: {date_str}
   - img: posts/{date_compact}/cover.jpg (※画像パスはこの形式で固定)
   - tags: [関連するタグ]
   - category: tech
   - author: Gemini Bot
   - description: (記事の要約)
2. 本文中に最低1回は `<tweet>強調したいポイント</tweet>` というカスタムタグを使用すること。
3. 可能な限り `<iframe ...>` でYouTube動画を埋め込むか、それが無理ならその旨は書かず自然な文章にする。
4. 画像を入れる場合は `![Alt text](./assets/img/posts/{date_compact}/sample.jpg)` の形式にする。
   (※キャプションとして `<small>... </small>` をつけること)
5. コードブロックは適切に使用すること。

## 出力
Markdownの生テキストのみを出力してください（冒頭の ```markdown は不要）。
"""

# 記事生成
response = genai.generate_text(prompt=prompt) # 旧APIまたは新APIに合わせて調整
# gemini-1.5系を使う場合は以下
response = model.generate_content(prompt)
content = response.text

# ```markdown 等の不要な装飾を削除（念のため）
content = content.replace("```markdown", "").replace("```", "").strip()

# ファイル名の決定 (例: 2025-12-13-daily-update.md)
# 簡易的に固定ファイル名にしていますが、本来はタイトルから英語ファイル名を生成するのがベストです
filename = f"{date_str}-daily-update.md"
filepath = os.path.join("_posts", filename)

# ファイル書き出し
with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print(f"Successfully generated: {filepath}")