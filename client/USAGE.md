# Gemma 3 Function Calling クライアント - 使用ガイド

## 概要

このCLIクライアントは、Gemma 3モデルとツール呼び出しを連携させたFunction Callingシステムのフロントエンドです。
ユーザーが自然言語で質問すると、LLMが適切なツールを呼び出して回答を生成します。

## インストール

### 前提条件

- Python 3.8 以上
- Ollama サーバーが起動していること（デフォルト: http://localhost:11434）
- C# APIサーバーが起動していること（デフォルト: http://localhost:5000）

### 依存パッケージ

```bash
pip install requests python-dotenv
```

## 使用方法

### 1. 基本的な使い方

#### 単発質問モード

質問を引数として渡すと、一度だけ質問に回答して終了します：

```bash
python client/main.py "東京の天気を教えて"
```

#### 対話モード

引数なしで実行、または `-i` オプションを指定すると対話モードになります：

```bash
# 引数なしで起動
python client/main.py

# または明示的に指定
python client/main.py --interactive
```

対話モードでは、複数の質問を連続して行うことができます。

### 2. コマンドラインオプション

#### 基本オプション

- `-i, --interactive`: 対話モードで起動
- `-m, --model MODEL`: 使用するLLMモデルを指定（デフォルト: gemma3:4b）
- `--api-base URL`: APIサーバーのURL（デフォルト: http://localhost:5000）
- `--ollama-host URL`: OllamaサーバーのURL（デフォルト: http://localhost:11434）

#### 詳細設定

- `--max-iterations N`: 最大反復回数（デフォルト: 10）
- `--timeout N`: タイムアウト秒数（デフォルト: 30）
- `--template TYPE`: プロンプトテンプレート（standard/concise/detailed/debug）

#### ログ・デバッグ

- `-d, --debug`: デバッグモードを有効化（詳細なログを出力）
- `-v, --verbose`: 詳細ログを有効化
- `--log-file PATH`: ログファイルのパスを指定

### 3. 使用例

#### 例1: デフォルト設定で単発質問

```bash
python client/main.py "1+1は?"
```

#### 例2: 特定のモデルで質問

```bash
python client/main.py --model gemma3:12b "複雑な数学の問題を解いて"
```

#### 例3: デバッグモードで詳細情報を確認

```bash
python client/main.py --debug --verbose "今日のニュースを教えて"
```

#### 例4: 反復回数を増やして複雑な質問

```bash
python client/main.py --max-iterations 20 "複数のステップが必要な質問"
```

#### 例5: ログファイルに保存

```bash
python client/main.py --log-file session.log --verbose "天気とニュースを教えて"
```

### 4. 対話モードの使い方

#### 起動

```bash
python client/main.py --interactive
```

#### 起動画面

```
============================================================
🤖 Gemma 3 Function Calling クライアント
============================================================
複数行入力: 'END' または Ctrl+D で入力終了
コマンド: /help でヘルプ、/quit で終了
------------------------------------------------------------
```

#### 質問の入力

単一行の質問：

```
💭 質問を入力してください (複数行可、'END' または Ctrl+D で終了):
>>> 東京の天気は?
```

複数行の質問：

```
💭 質問を入力してください (複数行可、'END' または Ctrl+D で終了):
>>> 以下の質問に答えてください:
... 1. 東京の天気
... 2. 今日のニュース
... END
```

#### 内蔵コマンド

対話モード中に以下のコマンドが使用できます：

- `/help` - ヘルプメッセージを表示
- `/quit` - プログラムを終了
- `/debug` - デバッグモードのオン/オフを切り替え
- `/status` - システムステータスを表示
- `/tools` - 利用可能なツール一覧を表示
- `/clear` - 画面をクリア

#### 使用例

```
>>> /help
利用可能なコマンド:
  /help       - このヘルプを表示
  /quit       - プログラムを終了
  ...

>>> /status
=== システムステータス ===
モデル: gemma3:4b
APIサーバー: http://localhost:5000
...

>>> /tools
=== 利用可能なツール ===
  1. weather_info
  2. news_feed
  3. calculator
  ...

>>> /quit
👋 終了します...
```

### 5. 環境変数の設定

`.env` ファイルを作成してデフォルト設定を変更できます：

```env
# .env ファイルの例
OLLAMA_HOST=http://localhost:11434
API_SERVER_HOST=http://localhost:5000
MODEL_NAME=gemma3:4b
MAX_RETRIES=3
TIMEOUT_SECONDS=30
```

環境変数よりもコマンドライン引数が優先されます。

### 6. システムヘルスチェック

デバッグモードまたは詳細モードで起動すると、自動的にシステムヘルスチェックが実行されます：

```bash
python client/main.py --verbose
```

出力例：

```
システムヘルスチェックを実行中...

✅ Ollama サーバー: OK
✅ モデル確認: gemma3:4b は利用可能です
✅ APIサーバー: OK (5個のツールが利用可能)
```

### 7. トラブルシューティング

#### Ollamaサーバーに接続できない

```
❌ Ollama サーバー: エラー - Ollama サーバーへの接続に失敗しました
```

→ Ollamaが起動していることを確認してください：

```bash
ollama serve
```

#### APIサーバーに接続できない

```
❌ APIサーバー: エラー - レジストリサーバーへの接続エラー
```

→ C# APIサーバーが起動していることを確認してください。

#### 指定したモデルが見つからない

```
❌ モデル確認: gemma3:12b が見つかりません
   利用可能なモデル: gemma3:4b, llama3.1:8b
```

→ 利用可能なモデルを確認して、正しいモデル名を指定してください：

```bash
ollama list
```

## 終了方法

### 対話モード

- `/quit` コマンドを入力
- `Ctrl+C` を押す

### 単発質問モード

- 質問が完了すると自動的に終了
- 処理中に `Ctrl+C` で中断可能

## 高度な使用例

### カスタムテンプレートでの実行

```bash
python client/main.py --template detailed "詳細な分析が必要な質問"
```

### 長時間のタスク用の設定

```bash
python client/main.py \
  --max-iterations 30 \
  --timeout 60 \
  --log-file long_task.log \
  "複雑で時間のかかるタスク"
```

### デバッグセッション

```bash
python client/main.py \
  --debug \
  --verbose \
  --log-file debug.log \
  --interactive
```

## まとめ

このCLIクライアントは柔軟性が高く、さまざまな使用シナリオに対応しています。
単純な質問から複雑な対話まで、状況に応じて適切なオプションを選択してください。
