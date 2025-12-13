import os
import datetime
import requests
import google.generativeai as genai
import re
import urllib.parse
import json # ★追加

# APIキーの取得
API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("GEMINI_API_KEY is not set")

genai.configure(api_key=API_KEY)

# --- 日付とパスの確定 ---
today = datetime.date.today()
date_str = today.strftime('%Y-%m-%d')
date_compact = today.strftime('%Y%m%d')

# 画像保存用設定
image_dir = os.path.join("assets", "img", "posts", date_compact)
os.makedirs(image_dir, exist_ok=True)
image_filename = "cover.jpg"
image_physical_path = os.path.join(image_dir, image_filename)
correct_front_matter_img_path = f"posts/{date_compact}/{image_filename}"

# モデル設定
model = genai.GenerativeModel('gemini-2.5-flash')

# --- ★追加機能: テーマの取得 ---
THEME_FILE = "themes.json" # ルートディレクトリにある前提
specific_theme = None

if os.path.exists(THEME_FILE):
    try:
        with open(THEME_FILE, "r", encoding="utf-8") as f:
            themes = json.load(f)
        # 今日の日付のテーマがあるか確認
        specific_theme = themes.get(date_str)
        if specific_theme:
            print(f"★ Theme found for today: {specific_theme}")
        else:
            print("No theme found for today. Using random topic.")
    except Exception as e:
        print(f"Error reading themes.json: {e}")
else:
    print(f"{THEME_FILE} not found. Using random topic.")

# テーマの決定
if specific_theme:
    theme_instruction = f"テーマ: 「{specific_theme}」について、深く掘り下げて書いてください。"
else:
    theme_instruction = "テーマ: 「今日のPythonテクニック」または「最新のAIニュース」から1つ選んで書いてください。"


def download_ai_image(prompt_text, save_path):
    """画像生成・保存関数"""
    try:
        encoded_prompt = urllib.parse.quote(prompt_text)
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1200&height=630&nologo=true"
        print(f"Downloading image from: {url}")
        
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                f.write(response.content)
            print(f"Image saved to: {save_path}")
            return True
        else:
            print(f"Download failed with status: {response.status_code}")
    except Exception as e:
        print(f"Image download failed: {e}")
    return False

# --- 1. 記事生成 ---
prompt = f"""
あなたはプロのテックブロガーです。
以下のルールに従って、GitHub Pages (Jekyll) 用のMarkdown記事を作成してください。

## 執筆テーマ
{theme_instruction}

## 必須フォーマットルール (厳守)
1. **Front Matter**:
   - `title`, `description` は必ずダブルクォーテーション (") で囲む。
   - `date`: {date_str}
   - `img`: {correct_front_matter_img_path}
   
   例:
   ---
   layout: post
   read_time: true
   show_date: true
   title: "記事タイトル"
   date: {date_str}
   img: {correct_front_matter_img_path}
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
Markdownの本文のみ出力。
"""

try:
    response = model.generate_content(prompt)
    content = response.text.replace("```markdown", "").replace("```", "").strip()

    # --- 強制修正ロジック ---
    content = re.sub(r'^date:\s*.*$', f'date: {date_str}', content, flags=re.MULTILINE)
    content = re.sub(r'^img:\s*.*$', f'img: {correct_front_matter_img_path}', content, flags=re.MULTILINE)

    # --- 2. 画像生成 ---
    # テーマに基づいたキーワードで画像を生成
    image_prompt = f"{specific_theme if specific_theme else 'technology python ai'} professional header 4k"
    if not download_ai_image(image_prompt, image_physical_path):
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