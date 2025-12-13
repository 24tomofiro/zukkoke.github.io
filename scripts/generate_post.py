import os
import datetime
import requests
import google.generativeai as genai
import re
import urllib.parse
import json

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

# --- テーマの取得 ---
THEME_FILE = "themes.json" # ルートディレクトリにある前提
specific_theme = None

if os.path.exists(THEME_FILE):
    try:
        with open(THEME_FILE, "r", encoding="utf-8") as f:
            themes = json.load(f)
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
あなたは**「コストパフォーマンスの追及をこよなく愛し、製品やソフトウェアのポテンシャルを骨の髄までしゃぶり尽くすことに情熱を燃やす、辛口かつ情熱的なガジェット系テックブロガー」**です。
以下のテーマについて、読者が「ここまでやるか？」と驚くような、しかし実用的でコストパフォーマンスに優れた「極限活用術」の記事を書いてください。

## 執筆テーマ
{theme_instruction}

## 執筆方針 (Tone & Manner)
1. **ペルソナ**:
   - 建前だけのカタログスペック紹介は嫌い。「実際に現場でどう使えるか」を重視する。
   - 「脱Google」「脱サブスクリプション」「プライバシー保護」こそが至高という思想を持つ。
   - 読者に対して「自分が持っている製品を眠らせておくのは罪だ」と啓蒙するような熱い語り口。

2. **必須構成案**:
   - **導入**: 対象製品のスペックに触れつつ、一般的な「できない」という思い込みを否定する。（例：「Dockerが使えない？ だからどうした」）
   - **活用例 (3〜5選)**: 具体的なアプリ名を挙げ、それをどう「極限まで」使うかを紹介する。
     - 構成例: 「カテゴリ名」→「アプリ名」→「極限活用法（具体的なメリット）」
   - **現実的な注意点**: 褒めるだけでなく、製品の制約（メモリ不足など）によるデメリットと、それを回避する「使いこなしのコツ（運用回避策）」を正直に書く。
   - **まとめ**: 結局、この使い方は「何（月額費やプライバシー）」を取り戻せるのかを総括する。
   - **Next Step**: 読者が今日から始められる最初の一歩を提案する。

3. **文体**:
   - 「〜です、〜ます」調だが、断定的で自信に満ちた表現を使う。
   - 専門用語を使いつつも、初心者にもメリットが伝わる比喩を用いる（例：「自宅警備員」「自分だけのGoogle」）。

## 必須フォーマットルール (システム連携用・厳守)
1. **Front Matter**:
   - `title`, `description` は必ずダブルクォーテーション (") で囲む。
   - タイトルは「【極限活用】」や「【最適化】」などの引きのある言葉を入れる。
   - `date`: {date_str}
   - `img`: {correct_front_matter_img_path}
   
   例:
   ---
   layout: post
   read_time: true
   show_date: true
   title: "【極限活用】DS223jを骨の髄までしゃぶり尽くす脱サブスク術"
   date: {date_str}
   img: {correct_front_matter_img_path}
   tags: [Synology, NAS, Gadget, LifeHack]
   category: gadget
   author: Gemini Bot
   description: "メモリ1GBのNASでも諦めるな。GoogleフォトもDropboxも解約できる、DS223jの真の力を解放する方法を解説します。"
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