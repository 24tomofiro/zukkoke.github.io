import os
import datetime
import requests
import google.generativeai as genai
import re
import urllib.parse
import json
import time
import csv  # 追加

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

# ==========================================
#  ここから: CSV管理ロジックへの変更部分
# ==========================================
IDEAS_FILE = "ideas.csv"
current_idea = None

def get_next_idea_and_update_csv(file_path):
    """
    CSVを読み込み、ステータスが未完了の最初の行を取得。
    取得と同時にメモリ上でステータスを更新し、ファイルを上書き保存する。
    """
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        return None

    target_row = None
    all_rows = []
    
    # 1. 読み込み
    try:
        with open(file_path, mode='r', encoding='utf-8-sig') as f: # Excel互換のためutf-8-sig推奨
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            all_rows = list(reader)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return None

    # 2. 未処理データの検索と更新
    for row in all_rows:
        # ステータス列が空、または '未' の場合を対象とする
        status = row.get('ステータス', '').strip()
        if status not in ['済', 'Done', 'Complete']:
            target_row = row
            
            # メモリ上で更新 (ステータスと日付)
            row['ステータス'] = '済'
            row['記事化日'] = date_str
            
            print(f"★ Found new idea: {row.get('製品名')}")
            break
    
    if not target_row:
        print("No new ideas found in CSV (All done).")
        return None

    # 3. CSVへの書き戻し（ロック用）
    try:
        with open(file_path, mode='w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_rows)
            print("CSV updated: Status set to '済'")
    except Exception as e:
        print(f"Error updating CSV: {e}")
        # 書き込み失敗時はNoneを返して処理を中断させるべき
        return None

    return target_row

# 実行してテーマを取得
idea_data = get_next_idea_and_update_csv(IDEAS_FILE)

if idea_data:
    product_name = idea_data.get('製品名', 'ガジェット')
    details = idea_data.get('活用詳細', '') # カラム名はCSVに合わせて調整してください
    price = idea_data.get('推定価格', '')
    
    theme_instruction = f"""
    今回の執筆対象製品: 「{product_name}」 (推定価格: {price})
    
    この製品の「極限活用法」として、以下のアイデアを核にして記事を膨らませてください：
    {details}
    """
else:
    # CSVにネタがない、またはエラー時のフォールバック
    print("Fallback to default theme.")
    theme_instruction = "テーマ: 「最新の低価格ガジェット活用術」について書いてください。"
    product_name = "ガジェット" # 仮置き

# ==========================================
#  ここまで: CSV管理ロジックへの変更部分
# ==========================================

def download_ai_image(prompt_text, save_path):
    """画像生成・保存関数"""
    try:
        encoded_prompt = urllib.parse.quote(prompt_text)
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
            markdown_image = f"![{prompt_text}](/assets/img/{web_path})" # パス修正: /assets... から始まる絶対パス推奨
            new_content = new_content.replace(f"[[IMG:{prompt_text}]]", markdown_image)
            new_content = new_content.replace(f"[[IMG: {prompt_text}]]", markdown_image)
        else:
            new_content = new_content.replace(f"[[IMG:{prompt_text}]]", "")
            new_content = new_content.replace(f"[[IMG: {prompt_text}]]", "")
            
    return new_content

# --- 1. 記事生成 ---
# プロンプト内の変数を product_name を使うように微調整
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
date: {date_str}
img: {correct_front_matter_img_path}
tags: [Productivity, LifeHack, Gadget, {product_name}]
category: tech
author: "Gemini Bot"
description: "(ここに80文字程度のSEOを意識した記事概要)"
---

(ここから本文を開始)
<tweet>(ここに記事のハイライトとなる「パンチライン」を1つ書く)</tweet>
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
    # プロンプトに製品名を含める
    image_prompt = f"{product_name} technology minimal workspace professional 4k"
    if not download_ai_image(image_prompt, cover_physical_path):
        print("Warning: Cover image generation failed.")

    print("--- Processing Body Images ---")
    web_path_prefix = f"posts/{date_compact}"
    content = process_body_images(content, image_dir, web_path_prefix)

    # --- 3. ファイル保存 ---
    filename = f"{date_str}-{product_name}.md" # ファイル名に製品名を入れると管理しやすい
    filepath = os.path.join("_posts", filename)
    os.makedirs("_posts", exist_ok=True)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Successfully generated post: {filepath}")

except Exception as e:
    print(f"Error occurred: {e}")
    exit(1)