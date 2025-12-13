import os
import datetime
import requests
import google.generativeai as genai
import re
import urllib.parse
import json
import time # ★追加: 画像のシード値生成用

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
        # プロンプトをURLエンコード
        encoded_prompt = urllib.parse.quote(prompt_text)
        
        # Pollinations.aiを使用 (seedを時間で変えてバリエーションを出す)
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
    """
    本文中の [[IMG: プロンプト]] を検索し、画像を生成して置換する関数
    """
    # 正規表現で [[IMG: ... ]] を探す
    matches = re.findall(r'\[\[IMG:\s*(.*?)\]\]', content)
    
    new_content = content
    
    for i, prompt_text in enumerate(matches):
        # 画像ファイル名を決定 (body-1.jpg, body-2.jpg...)
        filename = f"body-{i+1}.jpg"
        save_path = os.path.join(save_dir, filename)
        web_path = f"{web_path_prefix}/{filename}" # Jekyll上のパス
        
        print(f"Found body image request: {prompt_text}")
        
        # 画像生成を実行
        # プロンプトに 'professional, 4k' などを付与して品質を上げる
        full_prompt = f"{prompt_text} professional tech illustration 4k"
        
        if download_ai_image(full_prompt, save_path):
            # 成功したらMarkdownの画像リンクに置換
            # [[IMG: ...]] -> ![prompt](path)
            markdown_image = f"![{prompt_text}](./assets/img/{web_path})"
            # スペースの有無両方に対応して置換
            new_content = new_content.replace(f"[[IMG:{prompt_text}]]", markdown_image)
            new_content = new_content.replace(f"[[IMG: {prompt_text}]]", markdown_image)
        else:
            # 失敗したらタグを消す（テキストに残らないように）
            new_content = new_content.replace(f"[[IMG:{prompt_text}]]", "")
            new_content = new_content.replace(f"[[IMG: {prompt_text}]]", "")
            
    return new_content

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
   - **導入**: 対象製品のスペックに触れつつ、一般的な「できない」という思い込みを否定する。
   - **活用例 (3〜5選)**: 具体的なアプリ名を挙げ、それをどう「極限まで」使うかを紹介する。
   - **現実的な注意点**: メモリ不足などのデメリットと、それを回避する「使いこなしのコツ」を正直に書く。
   - **まとめ**: 結局、この使い方は「何」を取り戻せるのかを総括する。

3. **商品リンク (Amazon & 楽天)**:
   - **記事内で具体的な製品名（型番など）が登場したら、必ずその直後かセクションの終わりにAmazonと楽天の検索リンクを並べて配置すること。**
   - リンク形式: `[🛒 Amazonで検索](https://www.amazon.co.jp/s?k={{製品名}}) | [🔴 楽天で検索](https://search.rakuten.co.jp/search/mall/{{製品名}})`
   - URL内の製品名はスペースを `+` に置換するなどして有効なリンクにすること。

4. **★重要：挿入画像について**:
   - 記事の途中（セクションの変わり目など）に、内容を補足する画像を挿入したい。
   - 画像を入れたい場所に **`[[IMG: 画像の英語プロンプト]]`** というタグを記述すること。
   - 例: `[[IMG: Synology NAS server room cyber punk style]]`
   - 全体で2〜3枚程度挿入すること。プロンプトは必ず**英語**で書くこと。

## 必須フォーマットルール (システム連携用・厳守)
1. **Front Matter**:
   - `title`, `description` は必ずダブルクォーテーション (") で囲む。
   - `date`: {date_str}
   - `img`: {correct_front_matter_img_path}

2. **本文**:
   - `<tweet>パンチライン</tweet>` を入れる。
   - 見出し（##, ###）を適切に使い、読みやすくする。

## 出力
Markdownの本文のみ出力。
"""

try:
    response = model.generate_content(prompt)
    content = response.text.replace("```markdown", "").replace("```", "").strip()

    # --- 強制修正ロジック ---
    content = re.sub(r'^date:\s*.*$', f'date: {date_str}', content, flags=re.MULTILINE)
    content = re.sub(r'^img:\s*.*$', f'img: {correct_front_matter_img_path}', content, flags=re.MULTILINE)

    # --- 2. 画像生成処理 ---
    
    # A. カバー画像の生成
    print("--- Generating Cover Image ---")
    image_prompt = f"{specific_theme if specific_theme else 'technology python ai'} professional header 4k"
    if not download_ai_image(image_prompt, cover_physical_path):
        print("Warning: Cover image generation failed.")

    # B. 本文内画像の生成・置換 (★ここが追加機能)
    print("--- Processing Body Images ---")
    # Jekyllでのパスプレフィックス: posts/20251213
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