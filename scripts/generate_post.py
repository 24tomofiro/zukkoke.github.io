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
#  変更点1: 日付だけでなく「現在時刻」を取得して固有IDを作る
# ==========================================
now = datetime.datetime.now()
date_str = now.strftime('%Y-%m-%d')            # 2025-12-14 (Front Matter用)
datetime_str = now.strftime('%Y-%m-%d %H:%M:%S') # 2025-12-14 09:30:00 (Front Matter詳細用)
unique_id = now.strftime('%Y%m%d_%H%M%S')     # 20251214_093000 (フォルダ・ファイル名識別用)

# 画像保存用設定（実行ごとにユニークなフォルダを作る）
# 例: assets/img/posts/20251214_093000/
image_dir = os.path.join("assets", "img", "posts", unique_id)
os.makedirs(image_dir, exist_ok=True)

cover_filename = "cover.jpg"
cover_physical_path = os.path.join(image_dir, cover_filename)
# Web用のパス (Jekyll/Hugo等で参照するパス)
correct_front_matter_img_path = f"/assets/img/posts/{unique_id}/{cover_filename}"

# モデル設定
model = genai.GenerativeModel('gemini-2.5-flash')

# --- CSV管理ロジック ---
IDEAS_FILE = "ideas.csv"

def get_next_idea_and_update_csv(file_path):
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
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
            # 記事化日に時間まで入れる（ログとして便利）
            row['記事化日'] = datetime_str 
            print(f"★ Found new idea: {row.get('製品名')}")
            break
    
    if not target_row:
        print("No new ideas found in CSV (All done).")
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
    product_name = idea_data.get('製品名', 'ガジェット').replace("/", " ") # ファイル名用にスラッシュ等は置換
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
        # seedに時間を使い、かつ固有IDも混ぜて完全にランダム化
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
        # Webパスにも unique_id を含める
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
   - 記事内で紹介した具体的な製品名やサービス名が登場したら、その直後（または段落の終わり）に必ず検索リンクを置くこと。
   - **Markdownの表（テーブル）は使用禁止**。
   - リンク形式: `▷ [🛒 Amazonで「{product_name}」を検索](https://www.amazon.co.jp/s?k={product_name})`
   - 記事の最後にも「今回紹介したアイテムリスト」としてリンクを再掲すること。

4. **画像生成プロンプトの挿入**:
   - 記事の理解を助ける挿絵が必要な箇所に、以下の形式で2〜3回挿入すること。
   - 形式: `[[IMG: 英語の画像生成プロンプト]]`

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
    # 日付(date)フィールドに、時間を含めた正確なdatetime_strを入れる
    content = re.sub(r'^date:\s*.*$', f'date: {datetime_str}', content, flags=re.MULTILINE)
    content = re.sub(r'^img:\s*.*$', f'img: {correct_front_matter_img_path}', content, flags=re.MULTILINE)
    if "toc: true" not in content:
        content = re.sub(r'layout: post', 'layout: post\ntoc: true', content)

    # --- 画像生成 ---
    print("--- Generating Cover Image ---")
    image_prompt = f"{product_name} technology minimal workspace professional 4k"
    if not download_ai_image(image_prompt, cover_physical_path):
        print("Warning: Cover image generation failed.")

    print("--- Processing Body Images ---")
    # ここで unique_id を渡すのが重要
    content = process_body_images(content, image_dir, unique_id)

    # --- ファイル保存 ---
    # ファイル名にも unique_id (YYYYMMDD_HHMMSS) を使用して重複回避
    filename = f"{unique_id}-{product_name}.md" 
    filepath = os.path.join("_posts", filename)
    os.makedirs("_posts", exist_ok=True)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Successfully generated post: {filepath}")

except Exception as e:
    print(f"Error occurred: {e}")
    exit(1)