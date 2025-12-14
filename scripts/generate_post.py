import os
import datetime
import requests
import google.generativeai as genai
import re
import urllib.parse
import json
import time
import csv

# APIキーの取得
API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("GEMINI_API_KEY is not set")

genai.configure(api_key=API_KEY)

# ==========================================
#  日付設定
# ==========================================
now = datetime.datetime.now()
date_str = now.strftime('%Y-%m-%d')            # 2025-12-14
datetime_str = now.strftime('%Y-%m-%d %H:%M:%S') 
unique_id = now.strftime('%Y%m%d_%H%M%S')     # 画像フォルダ・ファイル名用

# 画像保存用設定
image_dir = os.path.join("assets", "img", "posts", unique_id)
os.makedirs(image_dir, exist_ok=True)

cover_filename = "cover.jpg"
cover_physical_path = os.path.join(image_dir, cover_filename)
correct_front_matter_img_path = f"/assets/img/posts/{unique_id}/{cover_filename}"

# モデル設定
model = genai.GenerativeModel('gemini-2.5-flash')

# --- CSV管理ロジック ---
IDEAS_FILE = "ideas.csv"

def get_next_idea_and_update_csv(file_path):
    if not os.path.exists(file_path):
        # CSVがない場合はNoneを返してデフォルトテーマへ
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
            # ステータス更新
            row['ステータス'] = '済'
            row['記事化日'] = datetime_str 
            print(f"★ Found new idea: {row.get('製品名')}")
            break
    
    if not target_row:
        print("No new ideas found in CSV (All done). Using Default.")
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

# 実行
idea_data = get_next_idea_and_update_csv(IDEAS_FILE)

if idea_data:
    product_name = idea_data.get('製品名', 'ガジェット').replace("/", " ")
    details = idea_data.get('活用詳細', '')
    price = idea_data.get('推定価格', '')
    
    theme_instruction = f"""
    今回の執筆対象製品: 「{product_name}」 (推定価格: {price})
    この製品の「極限活用法」として、以下のアイデアを核にして記事を膨らませてください：
    {details}
    """
else:
    print("Fallback to default theme.")
    theme_instruction = "テーマ: 「最新の低価格ガジェット活用術」について書いてください。"
    product_name = "ガジェット"

# --- 画像DL関数 ---
def download_ai_image(prompt_text, save_path):
    try:
        encoded_prompt = urllib.parse.quote(prompt_text)
        # seedにunique_idを使用して完全にランダム化
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1200&height=630&nologo=true&seed={unique_id}"
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

def process_body_images(content, save_dir, web_path_unique_id):
    matches = re.findall(r'\[\[IMG:\s*(.*?)\]\]', content)
    new_content = content
    
    for i, prompt_text in enumerate(matches):
        filename = f"body-{i+1}.jpg"
        save_path = os.path.join(save_dir, filename)
        web_path = f"posts/{web_path_unique_id}/{filename}"
        
        print(f"Found body image request: {prompt_text}")
        full_prompt = f"{prompt_text} professional tech illustration 4k"
        
        if download_ai_image(full_prompt, save_path):
            markdown_image = f"![{prompt_text}](/assets/img/{web_path})"
            new_content = new_content.replace(f"[[IMG:{prompt_text}]]", markdown_image)
            new_content = new_content.replace(f"[[IMG: {prompt_text}]]", markdown_image)
        else:
            new_content = new_content.replace(f"[[IMG:{prompt_text}]]", "")
            new_content = new_content.replace(f"[[IMG: {prompt_text}]]", "")
            
    return new_content

# --- 記事生成 ---
# ★修正ポイント: 目次リンク切れを防ぐための「見出しルール」と「目次自動生成の禁止」を追加
prompt = f"""
あなたは**「コストパフォーマンスの追求をこよなく愛し、製品やソフトウェアのポテンシャルを骨の髄までしゃぶり尽くすことに情熱を燃やす、実利主義の辛口テックブロガー」**です。
以下のテーマについて、読者が「ここまでやるか？」と驚くような、しかし実用的でコストパフォーマンスに優れた「極限活用術（ハック）」の記事を書いてください。

## 執筆テーマ
{theme_instruction}

## ターゲット読者
- 「買ったのに使いこなせていない」という罪悪感を持つ人。
- カタログスペックよりも「現場でどう役に立つか」を知りたい人。

## 記事の構成と執筆ルール
1. **トーン＆マナー**:
   - 丁寧語だが、情熱的で少し辛口。
   - 抽象的な表現は避け、「作業時間が30分減る」「年間1万円浮く」と具体的に書く。

2. **【重要】見出し（##, ###）のルール**:
   - **絵文字使用禁止**: 見出しに絵文字（🚀など）を含めると、目次リンクが機能しなくなるため絶対に使わないこと。
   - **リンク禁止**: 見出しの中にリンクを含めないこと。
   - **記号禁止**: カッコや引用符などの記号を見出しに使わず、プレーンなテキストにすること。
   - 悪い例: `## 🚀 活用法 [リンク]`
   - 良い例: `## 活用法`

3. **【重要】目次のルール**:
   - **本文中に「目次」というセクションやリストを自分で書かないこと。** - システム側で自動生成するため、あなたが書くと二重になり、かつリンクとして機能しません。

4. **本文構成**:
   - **導入**: 読者の抱える「無駄」を指摘し、利益を提示する。
   - **極限活用ハック (3〜5選)**: 具体的な応用例を書く。
   - **注意点**: 失敗しやすいポイントを教える。
   - **まとめ**: すぐやるべきアクションで締める。

5. **アフィリエイトリンク（表組み禁止）**:
   - 製品名が登場したら、その直後に検索リンクを置く。
   - **Markdownの表（テーブル）は使用禁止**。
   - リンク形式: `▷ [🛒 Amazonで「{product_name}」を検索](https://www.amazon.co.jp/s?k={product_name})`
   - 記事末尾にもリストとして再掲する。

6. **画像生成**:
   - 挿絵が必要な箇所に `[[IMG: 英語プロンプト]]` を2〜3回挿入。

## 必須フォーマット (厳守)
以下のFront Matter形式で開始すること。

---
layout: post
toc: true
read_time: true
show_date: true
title: "【極限活用】(ここに刺激的なタイトル)"
date: {datetime_str}
img: {correct_front_matter_img_path}
tags: [Productivity, LifeHack, Gadget, {product_name}]
category: tech
author: "Gemini Bot"
description: "(ここに80文字程度のSEOを意識した記事概要)"
---

(ここから本文)
<tweet>(パンチライン)</tweet>
"""

try:
    response = model.generate_content(prompt)
    content = response.text.replace("```markdown", "").replace("```", "").strip()

    # --- 強制修正ロジック ---
    # 日付と画像のパスをPython側の正確な値に置換
    content = re.sub(r'^date:\s*.*$', f'date: {datetime_str}', content, flags=re.MULTILINE)
    content = re.sub(r'^img:\s*.*$', f'img: {correct_front_matter_img_path}', content, flags=re.MULTILINE)
    
    # toc: true がない場合は追加
    if "toc: true" not in content:
        content = re.sub(r'layout: post', 'layout: post\ntoc: true', content)

    # --- 画像生成 ---
    print("--- Generating Cover Image ---")
    image_prompt = f"{product_name} technology minimal workspace professional 4k"
    if not download_ai_image(image_prompt, cover_physical_path):
        print("Warning: Cover image generation failed.")

    print("--- Processing Body Images ---")
    content = process_body_images(content, image_dir, unique_id)

    # --- ファイル保存 ---
    filename = f"{unique_id}-{product_name}.md" 
    filepath = os.path.join("_posts", filename)
    os.makedirs("_posts", exist_ok=True)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Successfully generated post: {filepath}")

except Exception as e:
    print(f"Error occurred: {e}")
    exit(1)