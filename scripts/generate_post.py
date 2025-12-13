import os
import datetime
import time
import requests # 画像ダウンロード用
import google.generativeai as genai

# APIキーの取得
API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("GEMINI_API_KEY is not set")

genai.configure(api_key=API_KEY)

# 日付設定
today = datetime.date.today()
date_str = today.strftime('%Y-%m-%d')
date_compact = today.strftime('%Y%m%d')

# 画像保存用ディレクトリの作成 (assets/img/posts/YYYYMMDD)
image_dir = os.path.join("assets", "img", "posts", date_compact)
os.makedirs(image_dir, exist_ok=True)
image_filename = "cover.jpg"
image_path = os.path.join(image_dir, image_filename)

# フロントマター用のパス (テーマの仕様に合わせて調整)
front_matter_img_path = f"posts/{date_compact}/{image_filename}"

# モデル設定
model = genai.GenerativeModel('gemini-2.5-flash')

def download_ai_image(prompt_text, save_path):
    """Pollinations.aiを使って画像を生成・保存する"""
    try:
        # URLエンコードしてAPIを叩く (seedを固定しないことで毎回違う画像になる)
        url = f"https://image.pollinations.ai/prompt/{prompt_text}?width=1200&height=630&nologo=true"
        print(f"Downloading image from: {url}")
        response = requests.get(url, timeout=20)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                f.write(response.content)
            print(f"Image saved to: {save_path}")
            return True
    except Exception as e:
        print(f"Image download failed: {e}")
    return False

# --- 1. 記事生成 ---
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

try:
    response = model.generate_content(prompt)
    content = response.text
    content = content.replace("```markdown", "").replace("```", "").strip()

    # --- 2. 画像生成 ---
    # 記事の内容に関連するキーワードで画像を生成
    # (簡易的に「technology, ai, python」などを指定。記事内容から抽出も可能だが今回は固定で安定させる)
    if not download_ai_image("futuristic technology artificial intelligence python programming style 4k", image_path):
        # 失敗したらデフォルト画像やエラーログなどを検討
        print("Warning: Cover image generation failed.")

    # --- 3. ファイル保存 ---
    filename = f"{date_str}-daily-update.md"
    filepath = os.path.join("_posts", filename)
    os.makedirs("_posts", exist_ok=True)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Successfully generated post: {filepath}")

except Exception as e:
    print(f"Error occurred: {e}")
    exit(1)