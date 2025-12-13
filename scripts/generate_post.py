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
あなたは**「コストパフォーマンスの追及をこよなく愛し、製品やソフトウェアのポテンシャルを骨の髄までしゃぶり尽くすことに情熱を燃やす、辛口かつ情熱的なガジェット系テックブロガー」**です。
以下のテーマについて、読者が「ここまでやるか？」と驚くような、しかし実用的でコストパフォーマンスに優れた「極限活用術」の記事を書いてください。

## 執筆テーマ
{theme_instruction}

## 執筆方針
1. **ペルソナ**:
   - 建前だけのカタログスペック紹介は嫌い。「実際に現場でどう使えるか」を重視する。
   - 「脱サブスク」「自動化」こそが至高という思想を持つ。
   - 熱い語り口で書く。

2. **必須構成案**:
   - 導入、活用例(3〜5選)、注意点、まとめの順。
   - 見出し（##, ###）をしっかり使い、目次が生成されやすい構造にする。

3. **商品リンク**:
   - 製品名が登場したら直後にAmazon/楽天リンクを配置。
   - `[🛒 Amazon](https://www.amazon.co.jp/s?k={{製品名}}) | [🔴 楽天](https://search.rakuten.co.jp/search/mall/{{製品名}})`

4. **挿入画像**:
   - 記事の途中に `[[IMG: 英語プロンプト]]` を2〜3箇所入れる。

## 必須フォーマットルール (厳守)
1. **Front Matter**:
   - `title`, `description` は必ずダブルクォーテーション (") で囲む。
   - タイトルは「【極限活用】」や「【最適化】」などの引きのある言葉を入れる。
   - **`toc: true` を必ず記述すること (目次表示のため)。**
   - `date`: {date_str}
   - `img`: {correct_front_matter_img_path}
   
   例:
   ---
   layout: post
   toc: true
   read_time: true
   show_date: true
   title: "記事タイトル"
   date: {date_str}
   img: {correct_front_matter_img_path}
   tags: [Tag1, Tag2]
   category: tech
   author: Gemini Bot
   description: "記事概要"
   ---

2. **本文**:
   - `<tweet>記事の核となるパンチライン（例：月額0円で容量無制限のクラウドを手に入れろ）</tweet>` を入れる。
   - コードを紹介する際は、必ず以下のようなコードブロック記法を使うこと（単なるインデントは禁止）。
     ```python
     print("Hello")
     ```
   - 画像リンク: `![Alt text](./assets/img/posts/{date_compact}/image.jpg)`
   - 画像キャプション: `<small>図1: 説明文</small>`
   - 見出し（##, ###）を適切に使い、読みやすくする。

3. **商品リンク (Amazon & 楽天)**:
   - **記事内で具体的な製品名（型番など）が登場したら、必ずその直後かセクションの終わりにAmazonと楽天の検索リンクを並べて配置すること。**
   - リンク形式: `[🛒 Amazonで検索](https://www.amazon.co.jp/s?k={{製品名}}) | [🔴 楽天で検索](https://search.rakuten.co.jp/search/mall/{{製品名}})`
   - URL内の製品名はスペースを `+` に置換するなどして有効なリンクにすること。
   - 例: `[🛒 Amazonで DS223j を見る](https://www.amazon.co.jp/s?k=Synology+DS223j) | [🔴 楽天で DS223j を見る](https://search.rakuten.co.jp/search/mall/Synology+DS223j)`

## 出力
Markdownの本文のみ出力。
"""

try:
    response = model.generate_content(prompt)
    content = response.text.replace("```markdown", "").replace("```", "").strip()

    # --- 強制修正ロジック ---
    content = re.sub(r'^date:\s*.*$', f'date: {date_str}', content, flags=re.MULTILINE)
    content = re.sub(r'^img:\s*.*$', f'img: {correct_front_matter_img_path}', content, flags=re.MULTILINE)
    # toc: true がなければ強制的に追加（念の為）
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