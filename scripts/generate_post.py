import os
import datetime
import requests
import google.generativeai as genai
import re
import urllib.parse
import json
import time

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
cover_filename = "cover.jpg"
cover_physical_path = os.path.join(image_dir, cover_filename)
correct_front_matter_img_path = f"posts/{date_compact}/{cover_filename}"

# モデル設定
model = genai.GenerativeModel('gemini-2.5-flash')

# --- テーマの取得 ---
THEME_FILE = "themes.json"
specific_theme = None

if os.path.exists(THEME_FILE):
    try:
        with open(THEME_FILE, "r", encoding="utf-8") as f:
            themes = json.load(f)
        specific_theme = themes.get(date_str)
        if specific_theme:
            print(f"★ Theme found for today: {specific_theme}")
    except Exception as e:
        print(f"Error reading themes.json: {e}")

if specific_theme:
    theme_instruction = f"テーマ: 「{specific_theme}」について、深く掘り下げて書いてください。"
else:
    theme_instruction = "テーマ: 「今日のPythonテクニック」または「最新のAIニュース」から1つ選んで書いてください。"


def download_ai_image(prompt_text, save_path):
    """画像生成・保存関数"""
    try:
        encoded_prompt = urllib.parse.quote(prompt_text)
        # seedを時間で変えてバリエーションを出す
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1200&height=630&nologo=true&seed={int(time.time())}"
        print(f"Downloading image: {prompt_text[:30]}...")
        
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                f.write(response.content)
            print(f"Saved to: {save_path}")
            return True
        else:
            print(f"Download failed: {response.status_code}")
    except Exception as e:
        print(f"Image download error: {e}")
    return False

def process_body_images(content, save_dir, web_path_prefix):
    """本文中の [[IMG: プロンプト]] を検索し、画像を生成して置換する"""
    matches = re.findall(r'\[\[IMG:\s*(.*?)\]\]', content)
    new_content = content
    
    for i, prompt_text in enumerate(matches):
        filename = f"body-{i+1}.jpg"
        save_path = os.path.join(save_dir, filename)
        web_path = f"{web_path_prefix}/{filename}"
        
        print(f"Found body image request: {prompt_text}")
        full_prompt = f"{prompt_text} professional tech illustration 4k"
        
        if download_ai_image(full_prompt, save_path):
            markdown_image = f"![{prompt_text}](./assets/img/{web_path})"
            new_content = new_content.replace(f"[[IMG:{prompt_text}]]", markdown_image)
            new_content = new_content.replace(f"[[IMG: {prompt_text}]]", markdown_image)
        else:
            new_content = new_content.replace(f"[[IMG:{prompt_text}]]", "")
            new_content = new_content.replace(f"[[IMG: {prompt_text}]]", "")
            
    return new_content

# --- 1. 記事生成 ---
prompt = f"""
あなたは**「コストパフォーマンスの追求をこよなく愛し、製品やソフトウェアのポテンシャルを骨の髄までしゃぶり尽くすことに情熱を燃やす、実利主義の辛口テックブロガー」**です。
以下のテーマについて、読者が「ここまでやるか？」と驚くような、しかし実用的でコストパフォーマンスに優れた「極限活用術（ハック）」の記事を書いてください。

## 執筆テーマ
{theme_instruction}

## ターゲット読者（ペルソナ）
- 「買ったのに使いこなせていない」という罪悪感を持つ人。
- カタログスペックよりも「現場でどう役に立つか」を知りたい人。
- 「自動化」「時短」「固定費削減」という言葉に弱い人。

## 記事の構成と執筆ルール
1. **トーン＆マナー**:
   - 丁寧語だが、情熱的で少し辛口。「〜ですよね」という共感よりも、「〜すべきです」「〜は金の無駄です」と言い切るスタイル。
   - 抽象的な表現（「便利です」「おすすめです」）は禁止。「作業時間が30分減ります」「年間1万円浮きます」と具体的に書く。

2. **本文構成**:
   - **導入**: 読者の抱える「無駄」を指摘し、本記事で得られる「利益（時間・金）」を提示する。
   - **極限活用ハック (3〜5選)**:
     - 単なる機能紹介はNG。
     - 「この製品とアプリXを組み合わせる」「この設定をOFFにして逆に〜に使う」といった応用的な使い方を書く。
   - **推奨設定・注意点**: 失敗しやすいポイントを先回りして教える。
   - **まとめ**: 「今日からすぐやるべきアクション」を提示して締める。

3. **アフィリエイトリンクの配置（重要）**:
   - 記事内で紹介した具体的な**製品名やサービス名**が登場したら、その直後（または段落の終わり）に必ず検索リンクを置くこと。
   - **Markdownの表（テーブル）は使用禁止**（スマホ表示崩れ防止のため）。
   - リンクは以下の形式で記述し、`製品名`の部分にはその文脈で紹介した具体的な商品名を入れること。
   - 形式: `▷ [🛒 Amazonで「製品名」を検索](https://www.amazon.co.jp/s?k=製品名) | [🔴 楽天で「製品名」を検索](https://search.rakuten.co.jp/search/mall/製品名)`
   - 記事の最後にも「今回紹介したアイテムリスト」として箇条書きでリンクを再掲すること。

4. **画像生成プロンプトの挿入**:
   - 記事の理解を助ける挿絵が必要な箇所に、以下の形式で2〜3回挿入すること。
   - 形式: `[[IMG: 英語の画像生成プロンプト]]`
   - プロンプト例: `workspace desk setup with multiple monitors and mechanical keyboard, cinematic lighting, photorealistic 8k`
   - ※プロンプトは具体的かつ写実的なシーンを描写する英語にすること。

## 必須フォーマット (厳守)
以下のFront Matter形式で開始し、その後にMarkdown本文を続けること。

---
layout: post
toc: true
read_time: true
show_date: true
title: "【極限活用】(ここに刺激的なタイトル)"
date: "{date_str}"
img: "{correct_front_matter_img_path}"
tags: [Productivity, LifeHack, Gadget, Python]
category: tech
author: "Gemini Bot"
description: "(ここに80文字程度のSEOを意識した記事概要)"
---

(ここから本文を開始)
<tweet>(ここに記事のハイライトとなる「パンチライン（名言）」を1つ書く)</tweet>

"""

try:
    response = model.generate_content(prompt)
    content = response.text.replace("```markdown", "").replace("```", "").strip()

    # --- 強制修正ロジック ---
    content = re.sub(r'^date:\s*.*$', f'date: {date_str}', content, flags=re.MULTILINE)
    content = re.sub(r'^img:\s*.*$', f'img: {correct_front_matter_img_path}', content, flags=re.MULTILINE)
    if "toc: true" not in content:
        content = re.sub(r'layout: post', 'layout: post\ntoc: true', content)

    # --- 2. 画像生成処理 ---
    print("--- Generating Cover Image ---")
    image_prompt = f"{specific_theme if specific_theme else 'technology python ai'} professional header 4k"
    if not download_ai_image(image_prompt, cover_physical_path):
        print("Warning: Cover image generation failed.")

    print("--- Processing Body Images ---")
    web_path_prefix = f"posts/{date_compact}"
    content = process_body_images(content, image_dir, web_path_prefix)

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