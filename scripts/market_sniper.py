import os
import datetime
import requests # 画像ダウンロード用に追加
import google.generativeai as genai
import yfinance as yf

# --- 設定エリア ---
# 監視対象: VOO (S&P500), NVDA (NVIDIA), BTC-USD (Bitcoin) など自由に変更可
TICKER = "VOO" 
# 記事にする閾値(%): この数値以上動いたら記事作成 (絶対値)
THRESHOLD_PERCENT = 1.0 

# APIキー設定
API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("GEMINI_API_KEY is not set")
genai.configure(api_key=API_KEY)

def get_market_data():
    """株価データを取得し、直近の変化率を計算する"""
    try:
        ticker = yf.Ticker(TICKER)
        # 5日分取得して、確実にデータがある日同士を比較
        hist = ticker.history(period="5d")
        
        if len(hist) < 2:
            return None

        # 最新の終値と、その一つ前の終値を比較
        current_price = hist['Close'].iloc[-1]
        prev_price = hist['Close'].iloc[-2]
        
        change_percent = ((current_price - prev_price) / prev_price) * 100
        
        return {
            "ticker": TICKER,
            "price": current_price,
            "change_percent": change_percent,
            "date": datetime.date.today().strftime('%Y-%m-%d')
        }
    except Exception as e:
        print(f"Data fetch error: {e}")
        return None

def download_chart_image(trend, ticker, save_path):
    """トレンドに合わせた画像を生成して保存する"""
    # トレンドに合わせて色や雰囲気を指定
    color = "green" if trend == "up" else "red"
    # プロンプト: 株価チャート、上昇/下降、色、プロフェッショナル、4K
    prompt_text = f"stock market chart {ticker} trend going {trend} color {color} professional finance 4k"
    
    url = f"https://image.pollinations.ai/prompt/{prompt_text}?width=1200&height=630&nologo=true"
    
    try:
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

def generate_sniper_article(data, front_matter_img_path):
    """Geminiで速報記事を生成する"""
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    trend = "急騰" if data["change_percent"] > 0 else "急落"
    sign = "+" if data["change_percent"] > 0 else ""
    
    prompt = f"""
    あなたは金融特化のAIブロガーです。以下の市場データを元に、投資家向けの「緊急速報ブログ記事」を書いてください。

    # 市場データ
    * 銘柄: {data['ticker']}
    * 現在値: {data['price']:.2f} USD
    * 変動率: {sign}{data['change_percent']:.2f}% ({trend})

    # 必須フォーマットルール (Jekyll互換性のために厳守)
    1. **Front Matterの `title` と `description` は必ずダブルクォーテーション (") で囲むこと。**
       例: title: "【緊急】S&P500が動いた！..."
    2. **Front Matterの `img` には "{front_matter_img_path}" を指定すること。**
    3. タイトルはクリックしたくなるような煽りを含める。
    4. 本文中に `<tweet>{data['ticker']}が前日比{data['change_percent']:.2f}%の変動。市場はどう動く？</tweet>` を含める。
    5. 変動の要因として考えられる一般的な理由（金利、決算、地政学リスクなど）を推測で良いので挙げて解説する。
    6. 出力はMarkdownの本文のみ。
    """
    
    response = model.generate_content(prompt)
    content = response.text
    
    # 掃除処理
    content = content.replace("```markdown", "").replace("```", "").strip()
    return content

# --- メイン実行部 ---
data = get_market_data()

if data:
    print(f"Check {TICKER}: {data['change_percent']:.2f}% (Threshold: {THRESHOLD_PERCENT}%)")
    
    # 絶対値で比較（プラスでもマイナスでも、大きく動けば反応する）
    if abs(data["change_percent"]) >= THRESHOLD_PERCENT:
        print(">>> THRESHOLD EXCEEDED! Generating article...")
        
        # --- 画像保存の準備 ---
        now = datetime.datetime.now()
        date_compact = now.strftime('%Y%m%d')
        time_str = now.strftime('%H%M')
        
        # 保存先ディレクトリ: assets/img/posts/YYYYMMDD
        image_dir = os.path.join("assets", "img", "posts", date_compact)
        os.makedirs(image_dir, exist_ok=True)
        
        # 画像ファイル名
        image_filename = f"sniper-{time_str}.jpg"
        image_physical_path = os.path.join(image_dir, image_filename)
        
        # 記事内で指定するパス (Jekyll用)
        front_matter_path = f"posts/{date_compact}/{image_filename}"
        
        # --- 画像生成・ダウンロード実行 ---
        trend_str = "up" if data["change_percent"] > 0 else "down"
        download_chart_image(trend_str, data["ticker"], image_physical_path)
        
        # --- 記事生成実行 (画像パスを渡す) ---
        content = generate_sniper_article(data, front_matter_path)
        
        # --- 記事ファイル保存 ---
        filename = f"{now.strftime('%Y-%m-%d-%H%M')}-market-alert.md"
        filepath = os.path.join("_posts", filename)
        
        os.makedirs("_posts", exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
            
        print(f"Successfully generated: {filepath}")
    else:
        print("Changes are within normal range. No article generated.")
else:
    print("Failed to fetch market data.")