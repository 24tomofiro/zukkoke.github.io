import os
import datetime
import google.generativeai as genai

# APIキーの取得
API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("GEMINI_API_KEY is not set")

genai.configure(api_key=API_KEY)

# 今日の日付
today = datetime.date.today()
date_str = today.strftime('%Y-%m-%d')
date_compact = today.strftime('%Y%m%d')

# モデル設定：指定された gemini-2.5-flash を使用
# ※もし将来的にモデル名が変更されたり、まだ利用できない場合はエラー(404)になる可能性があります。
# その場合は 'gemini-1.5-flash' や 'gemini-2.0-flash-exp' などに戻してください。
model = genai.GenerativeModel('gemini-2.5-flash')

# プロンプト：フォーマットを厳密に定義
prompt = f"""
あなたはプロのテックブロガーです。
以下の「必須フォーマットルール」に**一字一句正確に従って**、GitHub Pages (Jekyll) 用のMarkdown記事を作成してください。

## テーマ
「今日のPythonテクニック」または「最新のAIニュース」から1つ選んで書いてください。

## 必須フォーマットルール (厳守)
1. **Front Matter (ヘッダー)**:
   - 記事の先頭には必ずFront Matterをつけること。
   - `title` と `description` の値は、**必ずダブルクォーテーション (") で囲むこと**。これはJekyllのビルドエラーを防ぐため必須です。
   
   【正しいFront Matterの例】
   ---
   layout: post
   read_time: true
   show_date: true
   title: "記事のタイトルをここに書く"
   date: {date_str}
   img: posts/{date_compact}/cover.jpg
   tags: [Tag1, Tag2]
   category: tech
   author: Gemini Bot
   description: "記事の概要をここに書く。必ず引用符で囲むこと。"
   ---

2. **本文の記法**:
   - `<tweet>強調したいポイント</tweet>` を1回以上使うこと。
   - コードを紹介する際は、必ず以下のようなコードブロック記法を使うこと（単なるインデントは禁止）。
     ```python
     print("Hello")
     ```
   - 画像リンク形式: `![Alt text](./assets/img/posts/{date_compact}/image.jpg)`
   - 画像キャプション: `<small>図1: 説明文</small>`

## 出力
Markdownの本文のみを出力してください（冒頭の ```markdown や文末の ``` は含めないでください）。
"""

# コンテンツ生成
try:
    response = model.generate_content(prompt)
    content = response.text

    # 不要なMarkdown記法（```markdown ... ```）が混じっていた場合のみ削除
    if content.startswith("```markdown"):
        content = content.replace("```markdown", "", 1)
    if content.startswith("```"):
        content = content.replace("```", "", 1)
    if content.endswith("```"):
        content = content[:-3]
    
    content = content.strip()

    # ファイル保存処理
    filename = f"{date_str}-daily-update.md"
    filepath = os.path.join("_posts", filename)

    # フォルダがない場合は作成
    os.makedirs("_posts", exist_ok=True)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Successfully generated: {filepath}")

except Exception as e:
    print(f"Error occurred: {e}")
    # GitHub Actionsでエラーを検知させるためにexitコードを返す
    exit(1)