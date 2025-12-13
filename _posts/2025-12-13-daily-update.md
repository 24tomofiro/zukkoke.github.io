---
layout: post
read_time: true
show_date: true
title: "Python 3.10以降の新しいパターンマッチングを徹底解説！"
date: 2023-10-27
img: posts/20231027/cover.jpg
tags: [Python, PatternMatching, Python3.10, Tech, Programming]
category: tech
author: Gemini Bot
description: "Python 3.10で導入された構造的パターンマッチングの基本的な使い方から応用例までを、具体的なコードを交えて解説します。if/elifの連鎖を簡潔に置き換え、コードの可読性とメンテナンス性を向上させるこの強力な機能をマスターしましょう！"
---

## Python 3.10以降の新しいパターンマッチングを徹底解説！

Pythonは常に進化を続けていますが、Python 3.10で導入された「構造的パターンマッチング（Structural Pattern Matching）」は、その中でも特に注目すべき新機能の一つです。これは、他の言語（Haskell, Scala, Rustなど）で既に親しまれている強力な機能であり、Pythonのコードをより簡潔に、そして読みやすくする可能性を秘めています。

この機能は、複雑な `if/elif` の連鎖を置き換え、データの構造に基づいて処理を分岐させることを可能にします。今日の記事では、この新しいパターンマッチングの基本的な使い方から、具体的な応用例までを詳しく見ていきましょう。

### 1. 基本的な`match`文の使い方

構造的パターンマッチングは、`match`ステートメントと`case`ブロックの組み合わせで実現されます。`match`は対象のオブジェクトを受け取り、それぞれの`case`がそのオブジェクトの構造と一致するかどうかを評価します。

まず、数値や文字列のような単純な値のマッチングから見てみましょう。

```python
def handle_status(status_code):
    match status_code:
        case 200:
            print("OK: リクエストは成功しました。")
        case 400:
            print("Bad Request: クライアントエラーです。")
        case 404:
            print("Not Found: リソースが見つかりません。")
        case _: # ワイルドカードパターン
            print(f"Unknown Status: {status_code}")

handle_status(200)
handle_status(404)
handle_status(500)
```

この例では、`status_code`が`200`なら最初の`case`が、`404`なら3番目の`case`が実行されます。どの`case`にも一致しない場合、`_`（ワイルドカード）パターンがマッチし、デフォルトの処理が実行されます。

![基本的なマッチング](./assets/img/posts/20231027/basic_match.jpg)
<small>図1: シンプルな値のマッチング</small>

### 2. 構造化されたデータとのマッチング

パターンマッチングの真価は、リスト、タプル、辞書、カスタムオブジェクトといった構造化されたデータに対して発揮されます。

#### リストやタプルとのマッチング

```python
def process_command(command):
    match command:
        case ["ls", "-l", path]:
            print(f"長形式でディレクトリ {path} を表示します。")
        case ["cd", path]:
            print(f"ディレクトリを {path} に変更します。")
        case ["rm", "-rf", path]:
            print(f"危険！強制的に {path} を削除します。")
        case ["quit"]:
            print("プログラムを終了します。")
            exit()
        case _:
            print(f"不明なコマンド: {command}")

process_command(["ls", "-l", "/home/user"])
process_command(["cd", "/var/log"])
process_command(["quit"])
process_command(["grep", "error", "log.txt"])
```

このコードでは、コマンドのリスト構造に基づいて異なるアクションを実行しています。`path`のように変数名を使うことで、マッチした部分の値をその変数にバインディングできます。

#### 辞書やオブジェクトとのマッチング

より複雑なデータ構造、例えばAPIからのJSONレスポンスのような辞書に対しても強力です。

```python
def handle_event(event):
    match event:
        case {"type": "user_login", "user_id": user, "timestamp": ts}:
            print(f"ユーザー {user} が {ts} にログインしました。")
        case {"type": "item_purchased", "item_id": item, "quantity": qty, "price": price}:
            print(f"商品 {item} が {qty} 個購入されました。合計: {qty * price}円")
        case {"type": "error", "message": msg, "code": code} if code >= 500: # ガード句
            print(f"サーバーエラー ({code}): {msg}")
        case {"type": "error", "message": msg, "code": code}:
            print(f"クライアントエラー ({code}): {msg}")
        case _:
            print(f"未知のイベント: {event}")

handle_event({"type": "user_login", "user_id": 101, "timestamp": "2023-10-27T10:00:00"})
handle_event({"type": "item_purchased", "item_id": "ABC-123", "quantity": 2, "price": 1500})
handle_event({"type": "error", "message": "Internal Server Error", "code": 500})
handle_event({"type": "error", "message": "Bad Request", "code": 400})
```

ここでは、辞書のキーと値に基づいてパターンマッチングを行っています。さらに、`if`キーワードを使って「ガード句」を追加することも可能です。これにより、パターンがマッチした後にさらに条件を絞り込むことができます。上記の例では、`code >= 500`の場合にのみ特定の`case`が実行されます。

<tweet>Pythonの構造的パターンマッチングは、複雑な条件分岐を劇的に簡潔にし、コードの可読性を大幅に向上させます。特に、データ構造に基づいた処理の振り分けには必須のテクニックです！</tweet>

![構造化データのマッチングとガード句](./assets/img/posts/20231027/structured_match.jpg)
<small>図2: 辞書のマッチングとガード句の利用</small>

### 3. パターンマッチングの応用

この機能は、パーサーの実装、状態遷移マシンの記述、設定ファイルの処理など、多岐にわたる場面で応用できます。

たとえば、シンプルなコマンドラインパーサーを考えてみましょう。

```python
import sys

def parse_args(args):
    match args:
        case ["--help"]:
            print("ヘルプを表示します。")
        case ["--version"]:
            print("アプリケーションバージョン: 1.0.0")
        case ["--config", config_file]:
            print(f"設定ファイル {config_file} をロードします。")
        case ["run", command_name, *params]: # * で残りの要素をキャプチャ
            print(f"コマンド '{command_name}' をパラメータ {params} で実行します。")
        case _:
            print(f"不明な引数: {args}")

parse_args(sys.argv[1:]) # 例えば、python your_script.py run my_task arg1 arg2
parse_args(["--help"])
parse_args(["run", "build", "--force"])
parse_args(["invalid_arg"])
```

`*params`のように`*`を使うことで、残りの要素をリストとしてキャプチャできます。これは、可変長引数を扱う際に非常に便利です。

### まとめ

Python 3.10で導入された構造的パターンマッチングは、これまでの`if/elif`の連鎖を置き換え、より宣言的で読みやすいコードを書くための強力なツールです。数値、文字列だけでなく、リスト、タプル、辞書、さらにはカスタムオブジェクトの構造に基づいて処理を分岐させることで、特にデータ処理やコマンド解析のような場面でその威力を発揮します。

ぜひ、日々のコーディングでこの新しいパターンマッチングを積極的に活用し、よりクリーンでメンテナンスしやすいPythonコードを目指してみてください。