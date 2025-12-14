import os
import datetime
import requests
import google.generativeai as genai
import re
import urllib.parse
import json
import time
import csv

# ==========================================
#  基本設定
# ==========================================

# APIキーの取得
API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("GEMINI_API_KEY is not set")

genai.configure(api_key=API_KEY)

# モデル設定
model = genai.GenerativeModel('gemini-2.5-flash')

# ==========================================
#  日付・ID設定
# ==========================================
now = datetime.datetime.now()

# 1. Front Matter用 (記事内の表示日付)
datetime_str = now.strftime('%Y-%m-%d %H:%M:%S') 

# 2. 画像フォルダ用ID (ユニーク性重視)
unique_id = now.strftime('%Y%m%d_%H%M%S')

# 3. 記事ファイル名用 (Jekyll認識用 YYYY-MM-DD)
file_date_prefix = now.strftime('%Y-%m-%d')
file_time_suffix = now.strftime('%H%M')

# 画像保存用ディレクトリ (物理パス: assets/img/posts/ID)
image_dir = os.path.join("assets", "img", "posts", unique_id)
os.makedirs(image_dir, exist_ok=True)

cover_filename = "cover.jpg"
cover_physical_path = os.path.join(image_dir, cover_filename)

# Front Matter用パス (テーマ仕様: "posts/ID/file.jpg")
front_matter_img_path = f"posts/{unique_id}/{cover_filename}"

# ==========================================
#  CSV管理ロジック
# ==========================================
IDEAS_FILE = "ideas.csv"

def get_next_idea_and_update_csv(file_path):
    if not os.path.exists(file_path):
        return None

    target_row = None
    all_rows = []
    
    try:
        with open(file_path, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            all_rows = list(reader)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return None

    for row in all_rows:
        status = row.get('ステータス', '').strip()
        if status not in ['済', 'Done', 'Complete']:
            target_row = row
            row['ステータス'] = '済'
            row['記事化日'] = datetime_str 
            
            p_name = row.get('製品・サービス名')
            if p_name:
                 print(f"★ Found new idea: {p_name}")
            else:
                 print(f"★ Warning: '製品・サービス名' column is empty. Keys: {list(row.keys())}")
            break
    
    if not target_row:
        print("No new ideas found in CSV. Using Default.")
        return None

    try:
        with open(file_path, mode='w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_rows)
            print("CSV updated.")
    except Exception as e:
        print(f"Error updating CSV: {e}")
        return None

    return target_row

# ==========================================
#  テーマ設定
# ==========================================
idea_data = get_next_idea_and_update_csv(IDEAS_FILE)

if idea_data:
    product_name = idea_data.get('製品・サービス名', 'ガジェット').replace("/", " ")
    details = idea_data.get('極限活用法・その価値', '')
    price = idea_data.get('推定価格', '')
    
    if product_name is None or product_name == "None":
        product_name = "ガジェット"

    theme_instruction = f"""
    今回の執筆対象製品: 「{product_name}」 (推定価格: {price})
    この製品の「極限活用法」として、以下のアイデアを核にして記事を膨らませてください：
    {details}
    """
else:
    print("Fallback to default theme.")
    theme_instruction = "テーマ: 「最新の低価格ガジェット活用術」について書いてください。"
    product_name = "ガジェット"

# ==========================================
#  画像DL関数
# ==========================================
def download_ai_image(prompt_text, save_path):
    try:
        encoded_prompt = urllib.parse.quote(prompt_text)
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1200&height=630&nologo=true&seed={unique_id}"
        print(f"Downloading image: {prompt_text[:30]}...")
        
        time.sleep(1) 
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

def process_body_images(content, save_dir, web_path_unique_id):
    matches = re.findall(r'\[\[IMG:\s*(.*?)\]\]', content)
    new_content = content
    
    for i, prompt_text in enumerate(matches):
        filename = f"body-{i+1}.jpg"
        save_path = os.path.join(save_dir, filename)
        
        # 本文内画像の絶対パス (Jekyll用)
        web_path_full = f"/assets/img/posts/{web_path_unique_id}/{filename}"
        
        print(f"Found body image request: {prompt_text}")
        full_prompt = f"{prompt_text} professional tech illustration 4k"
        
        if download_ai_image(full_prompt, save_path):
            markdown_image = f"![{prompt_text}]({web_path_full})"
            new_content = new_content.replace(f"[[IMG:{prompt_text}]]", markdown_image)
            new_content = new_content.replace(f"[[IMG: {prompt_text}]]", markdown_image)
        else:
            new_content = new_content.replace(f"[[IMG:{prompt_text}]]", "")
            new_content = new_content.replace(f"[[IMG: {prompt_text}]]", "")
            
    return new_content

# ==========================================
#  プロンプト作成 (目次部分をHTML形式に変更)
# ==========================================
prompt = f"""
あなたは**「コストパフォーマンスの追求をこよなく愛し、ガジェット製品はもちろんのこと日用品やキッチン用品などあらゆる製品やソフトウェアのポテンシャルを骨の髄までしゃぶり尽くすことに情熱を燃やす、実利主義の辛口ライフハックブロガー」**です。
以下のテーマについて、読者が「ここまでやるか？」と驚くような、しかし実用的でコストパフォーマンスに優れた「極限活用術（ハック）」の記事を書いてください。

## 執筆テーマ
{theme_instruction}

## ★最重要：目次（HTMLリスト形式）の作成ルール
記事の冒頭（導入文の直後）に、以下の**HTMLタグ形式**で「クリックで開閉する目次」を必ず作成してください。
**Markdownの箇条書き（- [ ]）は使用しないでください（崩れます）。**

<details style="border: 1px solid #ddd; padding: 10px; border-radius: 5px; margin-bottom: 20px;">
<summary style="cursor: pointer; font-weight: bold;">📖 目次 (クリックで開く)</summary>
<ul>
  <li><a href="#section-1">1. はじめに</a></li>
  <li><a href="#section-2">2. 具体的な活用法</a></li>
  <li><a href="#section-3">3. 導入手順</a></li>
  <li><a href="#section-4">4. 注意点</a></li>
  <li><a href="#section-5">5. まとめ</a></li>
</ul>
</details>

## ★最重要：見出し（##, ###）のルール
リンクを機能させるため、見出しのID（#xxx）は自動生成されるルールに従ってください。
1. **記号禁止**: 見出しに絵文字、句読点、カッコを使わない。
2. **【重要】見出しとIDの強制ルール（最重要）**:
   - リンク切れを防ぐため、見出しには必ず **GitHub Pages互換のID明示記法 `{#id}`** を付与すること。
   - 目次の `href` と、見出しの `{#id}` は、**完全に一致する英語ベースのID**（section-1など）を使用すること。日本語IDは使用禁止（エンコードエラーの原因となるため）。
   
   **記述パターン:**
   - 目次: `<li><a href="#section-1">1. はじめに</a></li>`
   - 見出し: `## 1. はじめに {{#section-1}}`
   
   - 目次: `<li><a href="#section-2">2. 具体的な活用法</a></li>`
   - 見出し: `## 2. 具体的な活用法 {{#section-2}}`

   **ルール:**
   - 見出しテキスト（「1. はじめに」など）は自由に変えてよいが、ID（`#section-1` 等）は連番で固定すること。
   - 絵文字は見出しテキストにもIDにも含めないこと。

## 執筆ルール
1. **トーン＆マナー**:
   - 丁寧語だが、情熱的で少し辛口。基本的にはですます調とする
   - 抽象的な表現は避け、「作業時間が30分減る」「年間1万円浮く」と具体的に書く。

2. **【重要】見出し（##, ###）のルール**:
   - **絵文字使用禁止**: 見出しに絵文字（🚀など）を含めると、目次リンクが機能しなくなるため絶対に使わないこと。
   - **リンク禁止**: 見出しの中にリンクを含めないこと。
   - **記号禁止**: カッコや引用符などの記号を見出しに使わず、プレーンなテキストにすること。
   - 悪い例: `## 🚀 活用法 [リンク]`
   - 良い例: `## 活用法`

3. **【重要】目次のルール**:
   - **本文中に「目次」というセクションやリストを自分で書かないこと。** - システム側で自動生成するため、あなたが書くと二重になり、かつリンクとして機能しません。

## 記事の構成
1. **導入**: 読者の抱える「無駄」を指摘し、利益を提示する。
2. **プルダウン目次**: 上記のHTML形式で配置。
3. **極限活用ハック (3〜5選)**: 具体的な応用例を書く。
4. **注意点**: 失敗しやすいポイントを教える。
5. **まとめ**: アクションプラン。

## アフィリエイトリンク（表組み禁止）
   - 製品名が登場したら、その直後に検索リンクを置く。
   - **Markdownの表（テーブル）は使用禁止**。
   - リンク形式: `▷ [🛒 Amazonで「{product_name}」を検索](https://www.amazon.co.jp/s?k={product_name})`
   - 記事末尾にもリストとして再掲する。

## 画像生成
   - 挿絵が必要な箇所に `[[IMG: 英語プロンプト]]` を2〜3回挿入。
    - 例: `[[IMG: A high-tech workspace with gadgets, minimalistic style, 4k]]`

## 必須フォーマット
以下のFront Matter形式で開始すること。
**注意: `toc: false` に設定して、動かないサイドバー目次を消すこと。**

---
layout: post
toc: false
read_time: true
show_date: true
title: "【極限活用】(ここに刺激的なタイトル)"
date: {datetime_str}
img: {front_matter_img_path}
tags: [Productivity, LifeHack, Gadget, {product_name}]
category: tech
author: "Gemini Bot"
description: "(ここに80文字程度のSEOを意識した記事概要)"
---

(ここから本文)
<tweet>(パンチライン)</tweet>
"""

# ==========================================
#  記事生成実行
# ==========================================
max_retries = 3
for attempt in range(max_retries):
    try:
        print(f"Generating content with gemini-2.5-flash (Attempt {attempt+1}/{max_retries})...")
        response = model.generate_content(prompt)
        content = response.text.replace("```markdown", "").replace("```", "").strip()
        break 
    except Exception as e:
        print(f"Error occurred: {e}")
        if attempt < max_retries - 1:
            wait_time = 20
            print(f"Waiting {wait_time} seconds before retry...")
            time.sleep(wait_time)
        else:
            print("Max retries reached. Exiting.")
            exit(1)

# ==========================================
#  後処理・保存
# ==========================================
content = re.sub(r'^date:\s*.*$', f'date: {datetime_str}', content, flags=re.MULTILINE)
content = re.sub(r'^img:\s*.*$', f'img: {front_matter_img_path}', content, flags=re.MULTILINE)

# toc: true があったら false に書き換える
content = re.sub(r'toc:\s*true', 'toc: false', content)
if "toc: false" not in content:
    content = re.sub(r'layout: post', 'layout: post\ntoc: false', content)

# --- 画像生成 ---
print("--- Generating Cover Image ---")
image_prompt = f"{product_name} technology minimal workspace professional 4k"
if not download_ai_image(image_prompt, cover_physical_path):
    print("Warning: Cover image generation failed.")

print("--- Processing Body Images ---")
content = process_body_images(content, image_dir, unique_id)

# --- ファイル保存 ---
safe_product_name = re.sub(r'[\\/*?:"<>|]', "", product_name)
filename = f"{file_date_prefix}-{file_time_suffix}-{safe_product_name}.md"

filepath = os.path.join("_posts", filename)
os.makedirs("_posts", exist_ok=True)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print(f"Successfully generated post: {filepath}")