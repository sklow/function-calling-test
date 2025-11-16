# Ollama セットアップ手順書

このドキュメントでは、Ollama のインストールから Gemma 3 モデルのセットアップ、本プロジェクトとの統合までの完全な手順を説明します。

## 目次

1. [システム要件](#システム要件)
2. [インストール手順](#インストール手順)
3. [初期設定](#初期設定)
4. [Gemma 3 モデルの取得](#gemma-3-モデルの取得)
5. [動作確認](#動作確認)
6. [本プロジェクトとの統合](#本プロジェクトとの統合)
7. [パフォーマンス最適化](#パフォーマンス最適化)
8. [トラブルシューティング](#トラブルシューティング)

---

## システム要件

### 最小要件

- **CPU**: 2コア以上
- **RAM**: 8GB以上（gemma3:4b の場合）
- **ストレージ**: 10GB 以上の空き容量
- **ネットワーク**: インターネット接続（モデルダウンロード時）

### 推奨要件

- **CPU**: 4コア以上
- **RAM**: 16GB以上
- **GPU**: NVIDIA GPU（CUDA 11.8以上）または Apple M1/M2/M3
- **ストレージ**: SSD 推奨、20GB 以上の空き容量

### 対応OS

- **Windows**: Windows 10/11 (64bit)
- **macOS**: 10.15 (Catalina) 以降
- **Linux**: Ubuntu 18.04以降、CentOS 7以降、Debian 10以降

### モデル別メモリ要件

| モデル | モデルサイズ | 最小RAM | 推奨RAM | GPU VRAM |
|--------|------------|---------|---------|----------|
| gemma3:1b | 約1GB | 4GB | 8GB | 2GB |
| gemma3:4b | 約4GB | 8GB | 16GB | 6GB |
| gemma3:12b | 約12GB | 16GB | 32GB | 12GB |

---

## インストール手順

### Windows

#### 方法1: 公式インストーラー（推奨）

1. **ダウンロード**
   - [Ollama 公式サイト](https://ollama.ai/) にアクセス
   - 「Download for Windows」ボタンをクリック
   - `OllamaSetup.exe` をダウンロード

2. **インストール**
   ```
   1. ダウンロードした OllamaSetup.exe をダブルクリック
   2. インストールウィザードの指示に従う
   3. インストール先: デフォルトは C:\Users\<ユーザー名>\AppData\Local\Programs\Ollama
   4. 「完了」をクリック
   ```

3. **確認**
   ```powershell
   # PowerShell または コマンドプロンプトを開く
   ollama --version
   ```
   バージョン情報が表示されればインストール成功です。

#### 方法2: Winget

```powershell
# PowerShell を管理者権限で開く
winget install Ollama.Ollama
```

#### 方法3: Docker

```powershell
# Docker Desktop がインストールされている前提
docker pull ollama/ollama

# コンテナを起動
docker run -d -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama
```

### macOS

#### 方法1: 公式インストーラー（推奨）

1. **ダウンロード**
   - [Ollama 公式サイト](https://ollama.ai/) にアクセス
   - 「Download for Mac」ボタンをクリック
   - `Ollama.dmg` をダウンロード

2. **インストール**
   ```
   1. ダウンロードした Ollama.dmg を開く
   2. Ollama アイコンを Applications フォルダにドラッグ
   3. Applications から Ollama を起動
   ```

3. **確認**
   ```bash
   # ターミナルを開く
   ollama --version
   ```

#### 方法2: Homebrew

```bash
# Homebrew がインストールされている前提
brew install ollama

# サービスとして起動
brew services start ollama
```

#### 方法3: Docker

```bash
# Docker Desktop がインストールされている前提
docker pull ollama/ollama

# コンテナを起動（Apple Silicon の場合）
docker run -d -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama
```

### Linux

#### 方法1: インストールスクリプト（推奨）

```bash
# 公式インストールスクリプトを実行
curl -fsSL https://ollama.ai/install.sh | sh
```

#### 方法2: Ubuntu/Debian（APT）

```bash
# リポジトリを追加
curl -fsSL https://ollama.ai/install.sh | sudo sh

# または手動でインストール
sudo apt-get update
sudo apt-get install ollama
```

#### 方法3: CentOS/RHEL（YUM/DNF）

```bash
# YUM の場合
sudo yum install ollama

# DNF の場合
sudo dnf install ollama
```

#### 方法4: Docker

```bash
# Docker がインストールされている前提
docker pull ollama/ollama

# コンテナを起動
docker run -d \
  -v ollama:/root/.ollama \
  -p 11434:11434 \
  --name ollama \
  ollama/ollama

# GPU を使用する場合（NVIDIA GPU）
docker run -d \
  --gpus=all \
  -v ollama:/root/.ollama \
  -p 11434:11434 \
  --name ollama \
  ollama/ollama
```

#### 方法5: 手動インストール

```bash
# バイナリをダウンロード
curl -L https://ollama.ai/download/ollama-linux-amd64 -o ollama

# 実行権限を付与
chmod +x ollama

# 適切な場所に移動
sudo mv ollama /usr/local/bin/

# 動作確認
ollama --version
```

---

## 初期設定

### 環境変数の設定

Ollama の動作をカスタマイズするための環境変数を設定します。

#### 主要な環境変数

| 環境変数 | 説明 | デフォルト値 |
|---------|------|------------|
| `OLLAMA_HOST` | バインドするホストとポート | `127.0.0.1:11434` |
| `OLLAMA_ORIGINS` | CORS で許可するオリジン | `*` |
| `OLLAMA_MODELS` | モデル保存先ディレクトリ | OS依存 |
| `OLLAMA_KEEP_ALIVE` | モデルをメモリに保持する時間 | `5m` |
| `OLLAMA_NUM_PARALLEL` | 並列リクエスト数 | `1` |
| `OLLAMA_MAX_LOADED_MODELS` | 同時ロード可能なモデル数 | `1` |
| `OLLAMA_DEBUG` | デバッグモード | `false` |

### Windows での設定

#### PowerShell（一時的）

```powershell
# 現在のセッションのみ有効
$env:OLLAMA_HOST = "0.0.0.0:11434"
$env:OLLAMA_ORIGINS = "*"
$env:OLLAMA_MODELS = "D:\ollama-models"
```

#### システム環境変数（永続的）

```powershell
# PowerShell を管理者権限で開く
[System.Environment]::SetEnvironmentVariable('OLLAMA_HOST', '0.0.0.0:11434', 'User')
[System.Environment]::SetEnvironmentVariable('OLLAMA_MODELS', 'D:\ollama-models', 'User')
```

または、GUI で設定：
```
1. 「Windowsキー + R」で「sysdm.cpl」を実行
2. 「詳細設定」タブ → 「環境変数」ボタン
3. 「ユーザー環境変数」または「システム環境変数」で「新規」
4. 変数名と値を入力
5. 「OK」で保存
```

### macOS/Linux での設定

#### Bash の場合

```bash
# ~/.bashrc に追加
echo 'export OLLAMA_HOST=0.0.0.0:11434' >> ~/.bashrc
echo 'export OLLAMA_ORIGINS=*' >> ~/.bashrc
echo 'export OLLAMA_MODELS=$HOME/ollama-models' >> ~/.bashrc

# 設定を反映
source ~/.bashrc
```

#### Zsh の場合

```bash
# ~/.zshrc に追加
echo 'export OLLAMA_HOST=0.0.0.0:11434' >> ~/.zshrc
echo 'export OLLAMA_ORIGINS=*' >> ~/.zshrc
echo 'export OLLAMA_MODELS=$HOME/ollama-models' >> ~/.zshrc

# 設定を反映
source ~/.zshrc
```

#### システムワイド設定（Linux）

```bash
# /etc/environment に追加（管理者権限が必要）
sudo bash -c 'cat >> /etc/environment << EOF
OLLAMA_HOST=0.0.0.0:11434
OLLAMA_ORIGINS=*
OLLAMA_MODELS=/var/lib/ollama/models
EOF'
```

### Docker での設定

```bash
# 環境変数を指定してコンテナを起動
docker run -d \
  -v ollama:/root/.ollama \
  -p 11434:11434 \
  -e OLLAMA_ORIGINS=* \
  -e OLLAMA_KEEP_ALIVE=10m \
  --name ollama \
  ollama/ollama
```

### ポート設定の変更

デフォルトのポート 11434 が使用されている場合、別のポートに変更できます。

```bash
# Windows（PowerShell）
$env:OLLAMA_HOST = "0.0.0.0:8080"

# macOS/Linux
export OLLAMA_HOST=0.0.0.0:8080

# Docker
docker run -d \
  -v ollama:/root/.ollama \
  -p 8080:11434 \
  -e OLLAMA_HOST=0.0.0.0:11434 \
  --name ollama \
  ollama/ollama
```

---

## Gemma 3 モデルの取得

### Ollama サーバの起動

モデルを取得する前に、Ollama サーバを起動します。

#### Windows/macOS（GUI インストールの場合）

```
アプリケーションから Ollama を起動すると、バックグラウンドでサーバが自動起動します。
システムトレイに Ollama のアイコンが表示されます。
```

#### コマンドラインでの起動

```bash
# すべてのOS共通
ollama serve
```

別のターミナル/コマンドプロンプトを開いて、以降のコマンドを実行してください。

#### Docker の場合

```bash
# コンテナが起動していれば、サーバも起動済み
docker ps | grep ollama

# コンテナ内でコマンドを実行
docker exec -it ollama ollama list
```

### モデルのダウンロード

#### gemma3:4b（推奨）

バランスの取れたパフォーマンスと品質を提供します。

```bash
ollama pull gemma3:4b
```

**ダウンロード容量**: 約 4GB
**推奨環境**: RAM 8GB以上、GPU VRAM 6GB以上（オプション）

#### gemma3:1b（軽量版）

リソースが限られている環境向けです。

```bash
ollama pull gemma3:1b
```

**ダウンロード容量**: 約 1GB
**推奨環境**: RAM 4GB以上、GPU VRAM 2GB以上（オプション）

#### gemma3:12b（高性能版）

最高品質の出力が必要な場合に使用します。

```bash
ollama pull gemma3:12b
```

**ダウンロード容量**: 約 12GB
**推奨環境**: RAM 16GB以上、GPU VRAM 12GB以上（強く推奨）

### Docker での取得

```bash
# コンテナ内でモデルを取得
docker exec -it ollama ollama pull gemma3:4b
```

### ダウンロード進行状況の確認

ダウンロード中は進行状況が表示されます：

```
pulling manifest
pulling 8934d96d3f08... 100% ▕████████████████▏ 4.7 GB
pulling 8c17c2ebb0ea... 100% ▕████████████████▏ 7.0 KB
pulling 7c23fb36d801... 100% ▕████████████████▏ 4.8 KB
pulling 2e0493f67d0c... 100% ▕████████████████▏   59 B
pulling fa304d675061... 100% ▕████████████████▏   91 B
pulling 42ba7f8a01dd... 100% ▕████████████████▏  557 B
verifying sha256 digest
writing manifest
removing any unused layers
success
```

### モデル一覧の確認

インストールされているモデルを確認します。

```bash
ollama list
```

出力例：
```
NAME              ID              SIZE      MODIFIED
gemma3:4b         a1b2c3d4e5f6    4.7 GB    2 minutes ago
```

---

## 動作確認

### 基本的な動作テスト

#### 対話型モードでのテスト

```bash
# gemma3:4b モデルで対話を開始
ollama run gemma3:4b

# プロンプトが表示されたら、質問を入力
>>> こんにちは、自己紹介してください

# 終了するには /bye を入力
>>> /bye
```

#### ワンショット実行

```bash
# コマンドラインから直接質問
ollama run gemma3:4b "日本の首都はどこですか？"
```

### API エンドポイントのテスト

#### モデル一覧の取得

```bash
# Windows（PowerShell）
Invoke-WebRequest -Uri http://localhost:11434/api/tags | Select-Object -Expand Content

# macOS/Linux
curl http://localhost:11434/api/tags
```

#### チャット API のテスト

```bash
# Windows（PowerShell）
$body = @{
    model = "gemma3:4b"
    messages = @(
        @{
            role = "user"
            content = "こんにちは"
        }
    )
    stream = $false
} | ConvertTo-Json

Invoke-WebRequest -Uri http://localhost:11434/api/chat `
    -Method POST `
    -ContentType "application/json" `
    -Body $body | Select-Object -Expand Content

# macOS/Linux
curl -X POST http://localhost:11434/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:4b",
    "messages": [
      {
        "role": "user",
        "content": "こんにちは"
      }
    ],
    "stream": false
  }'
```

#### Function Calling のテスト

```bash
# Windows（PowerShell）
$body = @{
    model = "gemma3:4b"
    messages = @(
        @{
            role = "user"
            content = "東京の天気を教えて"
        }
    )
    tools = @(
        @{
            type = "function"
            function = @{
                name = "get_weather"
                description = "指定された都市の天気情報を取得します"
                parameters = @{
                    type = "object"
                    properties = @{
                        city = @{
                            type = "string"
                            description = "都市名"
                        }
                    }
                    required = @("city")
                }
            }
        }
    )
    stream = $false
} | ConvertTo-Json -Depth 10

Invoke-WebRequest -Uri http://localhost:11434/api/chat `
    -Method POST `
    -ContentType "application/json" `
    -Body $body | Select-Object -Expand Content

# macOS/Linux
curl -X POST http://localhost:11434/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:4b",
    "messages": [
      {
        "role": "user",
        "content": "東京の天気を教えて"
      }
    ],
    "tools": [
      {
        "type": "function",
        "function": {
          "name": "get_weather",
          "description": "指定された都市の天気情報を取得します",
          "parameters": {
            "type": "object",
            "properties": {
              "city": {
                "type": "string",
                "description": "都市名"
              }
            },
            "required": ["city"]
          }
        }
      }
    ],
    "stream": false
  }'
```

### ストリーミング API のテスト

```bash
# macOS/Linux
curl -X POST http://localhost:11434/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:4b",
    "messages": [
      {
        "role": "user",
        "content": "100文字程度で日本の歴史について説明してください"
      }
    ],
    "stream": true
  }'
```

### サーバ状態の確認

```bash
# ヘルスチェック
curl http://localhost:11434/

# 期待される出力: "Ollama is running"
```

---

## 本プロジェクトとの統合

### プロジェクト構成の確認

```
FunctionCallingTest/
├── server/              # C# API サーバ（ASP.NET Core）
│   ├── Program.cs
│   └── ...
├── client/              # Python クライアント
│   ├── main.py
│   ├── requirements.txt
│   └── .env.example
└── docs/
    └── ollama-setup.md  # このファイル
```

### 環境変数の設定

#### client/.env の作成

`.env.example` を `.env` にコピーして編集します。

```bash
# Windows（PowerShell）
cd D:\_dev\FunctionCallingTest\client
Copy-Item .env.example .env

# macOS/Linux
cd /path/to/FunctionCallingTest/client
cp .env.example .env
```

#### .env ファイルの編集

```bash
# Ollama サーバのエンドポイント
OLLAMA_HOST=http://localhost:11434

# C# API サーバのエンドポイント
API_SERVER_HOST=http://localhost:5000

# 使用する Gemma 3 モデル
MODEL_NAME=gemma3:4b

# リトライ設定
MAX_RETRIES=3
TIMEOUT_SECONDS=30

# ストリーミング設定
ENABLE_STREAMING=true

# ログレベル（DEBUG, INFO, WARNING, ERROR）
LOG_LEVEL=INFO
```

### C# サーバの起動

```bash
# サーバディレクトリに移動
cd D:\_dev\FunctionCallingTest\server

# 依存関係の復元
dotnet restore

# サーバの起動
dotnet run
```

サーバが起動すると以下のように表示されます：
```
info: Microsoft.Hosting.Lifetime[14]
      Now listening on: http://localhost:5000
info: Microsoft.Hosting.Lifetime[0]
      Application started. Press Ctrl+C to shut down.
```

### Python クライアントからの接続テスト

```bash
# クライアントディレクトリに移動
cd D:\_dev\FunctionCallingTest\client

# 仮想環境の作成（初回のみ）
python -m venv venv

# 仮想環境の有効化
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 依存関係のインストール
pip install -r requirements.txt

# クライアントの実行
python main.py
```

### 統合テストの実行

#### テスト1: Ollama との接続確認

```bash
# Python インタラクティブシェルを起動
python

# 以下のコードを実行
>>> import requests
>>> response = requests.get('http://localhost:11434/api/tags')
>>> print(response.json())
{'models': [{'name': 'gemma3:4b', 'modified_at': '...', 'size': 4700000000}]}
>>> exit()
```

#### テスト2: C# サーバとの連携確認

```bash
# クライアントから天気取得をテスト
python main.py
# プロンプト: 「東京の天気を教えて」
```

期待される動作：
1. Python クライアントが Ollama に質問を送信
2. Gemma 3 が `get_weather` 関数の呼び出しを生成
3. Python が C# サーバの `/api/weather` エンドポイントを呼び出し
4. C# サーバが天気情報を返す
5. Gemma 3 が結果を自然言語で返答

#### テスト3: JSON Schema 形式での出力テスト

```python
# test_json_output.py
import requests
import json

url = "http://localhost:11434/api/chat"

payload = {
    "model": "gemma3:4b",
    "messages": [
        {
            "role": "user",
            "content": "ユーザー情報を JSON で返してください。名前: 田中太郎、年齢: 30、職業: エンジニア"
        }
    ],
    "format": "json",
    "stream": False
}

response = requests.post(url, json=payload)
result = response.json()
print(json.dumps(result, indent=2, ensure_ascii=False))
```

実行：
```bash
python test_json_output.py
```

### トラブルシューティング（統合時）

#### 問題: C# サーバに接続できない

```bash
# サーバが起動しているか確認
# Windows
netstat -ano | findstr :5000

# macOS/Linux
lsof -i :5000
```

解決策：
- サーバが起動していない → `dotnet run` で起動
- ファイアウォールでブロックされている → ファイアウォール設定を確認
- ポートが使用中 → .env でポート番号を変更

#### 問題: Ollama に接続できない

```bash
# Ollama サーバが起動しているか確認
curl http://localhost:11434/

# モデルが利用可能か確認
ollama list
```

解決策：
- サーバが起動していない → `ollama serve` で起動
- ポートが異なる → .env の `OLLAMA_HOST` を確認
- モデルが未インストール → `ollama pull gemma3:4b` を実行

---

## パフォーマンス最適化

### GPU 活用

#### NVIDIA GPU（CUDA）

##### 1. CUDA のインストール確認

```bash
# CUDA バージョンの確認
nvidia-smi

# 期待される出力:
# +-----------------------------------------------------------------------------+
# | NVIDIA-SMI 525.xx.xx    Driver Version: 525.xx.xx    CUDA Version: 12.x   |
# +-----------------------------------------------------------------------------+
```

##### 2. Ollama での GPU 利用確認

```bash
# Ollama を起動してログを確認
ollama serve

# 出力に以下のようなメッセージがあれば GPU が認識されています:
# "GPU 0: NVIDIA GeForce RTX 3080"
```

##### 3. GPU メモリ使用量の確認

```bash
# モデル実行中に別のターミナルで実行
nvidia-smi

# GPU メモリ使用量を確認
watch -n 1 nvidia-smi
```

##### 4. GPU を使用しない場合（CPU のみ）

```bash
# 環境変数で CPU のみに制限
export OLLAMA_NUM_GPU=0
ollama serve
```

#### Apple Silicon（M1/M2/M3）

Apple Silicon では、Metal Performance Shaders（MPS）が自動的に使用されます。

##### 1. GPU 活用の確認

```bash
# アクティビティモニタで GPU 使用率を確認
# またはコマンドラインで:
sudo powermetrics --samplers gpu_power -i1000 -n1
```

##### 2. メモリ統合アーキテクチャの利用

Apple Silicon は CPU と GPU がメモリを共有するため、システム RAM が GPU メモリとしても機能します。

```bash
# メモリ使用量の確認
vm_stat
```

##### 3. パフォーマンス設定

```bash
# より多くのメモリを Ollama に割り当て
export OLLAMA_MAX_LOADED_MODELS=1
export OLLAMA_KEEP_ALIVE=30m
```

### メモリ使用量の最適化

#### 1. モデルのメモリ保持時間を調整

```bash
# 5分でメモリから解放（デフォルト）
export OLLAMA_KEEP_ALIVE=5m

# すぐに解放（メモリ節約重視）
export OLLAMA_KEEP_ALIVE=0

# 30分保持（レスポンス速度重視）
export OLLAMA_KEEP_ALIVE=30m
```

#### 2. コンテキストサイズの調整

```bash
# API リクエスト時に num_ctx を指定
curl -X POST http://localhost:11434/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:4b",
    "messages": [{"role": "user", "content": "こんにちは"}],
    "options": {
      "num_ctx": 2048
    },
    "stream": false
  }'
```

| num_ctx | メモリ使用量 | 用途 |
|---------|------------|------|
| 2048 | 低 | 短い会話、シンプルなタスク |
| 4096 | 中（デフォルト） | 通常の会話 |
| 8192 | 高 | 長い文脈が必要なタスク |

#### 3. 同時実行数の調整

```bash
# 並列リクエスト数を制限
export OLLAMA_NUM_PARALLEL=1

# 複数モデルの同時ロードを制限
export OLLAMA_MAX_LOADED_MODELS=1
```

### モデル選択指針

#### 用途別のモデル選択

| 用途 | 推奨モデル | 理由 |
|------|----------|------|
| 本番環境（バランス重視） | gemma3:4b | パフォーマンスと品質のバランスが良い |
| 開発・テスト環境 | gemma3:1b | 高速、リソース消費が少ない |
| 高品質な出力が必要 | gemma3:12b | 最高品質の出力 |
| メモリ制約が厳しい | gemma3:1b | 最小メモリで動作 |
| リアルタイム処理 | gemma3:1b | レスポンス速度が速い |

#### パフォーマンス vs 品質のトレードオフ

```
品質         ：  低 ←――――――――――――――――→ 高
               1b        4b           12b
レスポンス速度：  速 ←――――――――――――――――→ 遅
メモリ使用量  ：  少 ←――――――――――――――――→ 多
```

#### 複数モデルの使い分け

プロジェクトで複数モデルを使い分ける例：

```python
# Python クライアント例
import os

# タスクの複雑度に応じてモデルを選択
def get_model_for_task(task_type):
    if task_type == "simple":
        return "gemma3:1b"  # シンプルな質問応答
    elif task_type == "normal":
        return "gemma3:4b"  # Function Calling
    elif task_type == "complex":
        return "gemma3:12b"  # 複雑な推論
    else:
        return os.getenv("MODEL_NAME", "gemma3:4b")

# 使用例
model = get_model_for_task("normal")
print(f"使用モデル: {model}")
```

### バッチ処理の最適化

複数のリクエストを効率的に処理する方法：

```python
# バッチ処理の例
import requests
import asyncio
import aiohttp

async def process_batch(prompts, model="gemma3:4b"):
    """複数のプロンプトを並列処理"""
    async with aiohttp.ClientSession() as session:
        tasks = []
        for prompt in prompts:
            task = send_request(session, model, prompt)
            tasks.append(task)

        results = await asyncio.gather(*tasks)
        return results

async def send_request(session, model, prompt):
    """単一リクエストの送信"""
    url = "http://localhost:11434/api/chat"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False
    }

    async with session.post(url, json=payload) as response:
        return await response.json()

# 実行例
prompts = [
    "東京の天気を教えて",
    "大阪の天気を教えて",
    "札幌の天気を教えて"
]

results = asyncio.run(process_batch(prompts))
```

### キャッシュ戦略

頻繁に使用するプロンプトの結果をキャッシュして、レスポンス速度を向上させます。

```python
# シンプルなキャッシュ実装
from functools import lru_cache
import hashlib
import json

class OllamaCache:
    def __init__(self, max_size=100):
        self.cache = {}
        self.max_size = max_size

    def get_cache_key(self, model, messages):
        """メッセージからキャッシュキーを生成"""
        content = json.dumps({"model": model, "messages": messages}, sort_keys=True)
        return hashlib.md5(content.encode()).hexdigest()

    def get(self, model, messages):
        """キャッシュから取得"""
        key = self.get_cache_key(model, messages)
        return self.cache.get(key)

    def set(self, model, messages, response):
        """キャッシュに保存"""
        if len(self.cache) >= self.max_size:
            # 最も古いエントリを削除
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]

        key = self.get_cache_key(model, messages)
        self.cache[key] = response

# 使用例
cache = OllamaCache()

# キャッシュからの取得を試行
cached_response = cache.get("gemma3:4b", [{"role": "user", "content": "こんにちは"}])
if cached_response:
    print("キャッシュヒット")
else:
    print("キャッシュミス - API を呼び出し")
```

---

## トラブルシューティング

### よくある問題と解決策

#### 問題1: インストールエラー

**症状**: インストールスクリプトやインストーラーが失敗する

**解決策**:

1. **管理者権限で実行**
   ```powershell
   # Windows: PowerShell を管理者権限で開く
   # macOS/Linux: sudo を使用
   sudo curl -fsSL https://ollama.ai/install.sh | sh
   ```

2. **ファイアウォール/アンチウイルスを一時的に無効化**
   - インストール中のみ無効化し、完了後に再度有効化

3. **手動インストールを試す**
   - Docker を使用する
   - バイナリを直接ダウンロード

#### 問題2: ポート競合

**症状**: `address already in use` エラー

**解決策**:

1. **使用中のプロセスを確認**
   ```bash
   # Windows
   netstat -ano | findstr :11434

   # macOS/Linux
   lsof -i :11434
   ```

2. **プロセスを終了**
   ```bash
   # Windows
   taskkill /PID <プロセスID> /F

   # macOS/Linux
   kill -9 <プロセスID>
   ```

3. **別のポートを使用**
   ```bash
   export OLLAMA_HOST=0.0.0.0:8080
   ollama serve
   ```

#### 問題3: メモリ不足

**症状**: `out of memory` エラー、システムが遅くなる

**解決策**:

1. **より軽量なモデルに変更**
   ```bash
   # gemma3:12b → gemma3:4b
   # gemma3:4b → gemma3:1b
   ollama pull gemma3:1b
   ```

2. **モデルを即座にアンロード**
   ```bash
   export OLLAMA_KEEP_ALIVE=0
   ```

3. **不要なアプリケーションを終了**
   - ブラウザのタブを閉じる
   - 他の重いアプリケーションを終了

4. **スワップ領域を増やす（Linux）**
   ```bash
   # 既存のスワップを確認
   swapon --show

   # スワップファイルを作成（4GB の例）
   sudo fallocate -l 4G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   ```

#### 問題4: モデル取得の失敗

**症状**: `failed to download model` エラー

**解決策**:

1. **ネットワーク接続を確認**
   ```bash
   # インターネット接続のテスト
   ping ollama.ai
   ```

2. **プロキシ設定が必要な場合**
   ```bash
   # Windows
   $env:HTTP_PROXY = "http://proxy.example.com:8080"
   $env:HTTPS_PROXY = "http://proxy.example.com:8080"

   # macOS/Linux
   export HTTP_PROXY=http://proxy.example.com:8080
   export HTTPS_PROXY=http://proxy.example.com:8080
   ```

3. **ダウンロードをリトライ**
   ```bash
   # モデルを削除して再取得
   ollama rm gemma3:4b
   ollama pull gemma3:4b
   ```

4. **ディスク容量を確認**
   ```bash
   # Windows
   Get-PSDrive C

   # macOS/Linux
   df -h
   ```

#### 問題5: API 接続エラー

**症状**: `connection refused` または `timeout` エラー

**解決策**:

1. **Ollama サーバが起動しているか確認**
   ```bash
   # ヘルスチェック
   curl http://localhost:11434/

   # 期待される出力: "Ollama is running"
   ```

2. **ファイアウォール設定を確認**
   ```bash
   # Windows: Windows Defender ファイアウォールで 11434 ポートを許可
   # macOS: システム環境設定 → セキュリティとプライバシー → ファイアウォール
   # Linux: ufw または iptables で許可
   sudo ufw allow 11434
   ```

3. **OLLAMA_HOST を確認**
   ```bash
   # 現在の設定を表示
   # Windows
   echo $env:OLLAMA_HOST

   # macOS/Linux
   echo $OLLAMA_HOST
   ```

4. **ローカルホスト以外からアクセスする場合**
   ```bash
   # すべてのインターフェースでリッスン
   export OLLAMA_HOST=0.0.0.0:11434
   ollama serve
   ```

#### 問題6: パフォーマンス問題（遅い）

**症状**: レスポンスが非常に遅い、タイムアウトする

**解決策**:

1. **GPU が使用されているか確認**
   ```bash
   # NVIDIA GPU
   nvidia-smi

   # Apple Silicon
   sudo powermetrics --samplers gpu_power -i1000 -n1
   ```

2. **より軽量なモデルを使用**
   ```bash
   ollama pull gemma3:1b
   ```

3. **コンテキストサイズを削減**
   ```json
   {
     "model": "gemma3:4b",
     "messages": [...],
     "options": {
       "num_ctx": 2048
     }
   }
   ```

4. **バックグラウンドプロセスを確認**
   ```bash
   # CPU 使用率の高いプロセスを確認
   # Windows
   tasklist /v

   # macOS/Linux
   top
   htop
   ```

#### 問題7: JSON Schema 出力が不正

**症状**: 期待した JSON 形式で出力されない

**解決策**:

1. **format パラメータを明示的に指定**
   ```json
   {
     "model": "gemma3:4b",
     "messages": [...],
     "format": "json",
     "stream": false
   }
   ```

2. **プロンプトで JSON 形式を明示**
   ```python
   messages = [
       {
           "role": "system",
           "content": "必ず有効な JSON 形式で応答してください。"
       },
       {
           "role": "user",
           "content": "ユーザー情報を返してください"
       }
   ]
   ```

3. **レスポンスのバリデーション**
   ```python
   import json

   try:
       response_json = json.loads(response_text)
   except json.JSONDecodeError as e:
       print(f"JSON パースエラー: {e}")
       # リトライまたはエラーハンドリング
   ```

### ログの確認方法

#### Ollama のログ場所

**Windows**:
```
C:\Users\<ユーザー名>\AppData\Local\Ollama\logs\
```

**macOS**:
```
~/Library/Logs/Ollama/
```

**Linux**:
```
~/.ollama/logs/
または
/var/log/ollama/
```

#### ログの表示

```bash
# 最新のログを表示
# Windows
Get-Content "$env:LOCALAPPDATA\Ollama\logs\server.log" -Tail 50

# macOS
tail -f ~/Library/Logs/Ollama/server.log

# Linux
tail -f ~/.ollama/logs/server.log

# Docker
docker logs ollama
docker logs -f ollama  # リアルタイム
```

#### デバッグモードの有効化

```bash
# デバッグログを有効化
export OLLAMA_DEBUG=1
ollama serve

# より詳細なログ
export OLLAMA_DEBUG=1
export OLLAMA_LOG_LEVEL=debug
ollama serve
```

### エラーメッセージの解釈

#### エラー: `model not found`

**意味**: 指定されたモデルがインストールされていない

**解決**:
```bash
ollama list  # インストール済みモデルを確認
ollama pull gemma3:4b  # モデルをインストール
```

#### エラー: `context length exceeded`

**意味**: 会話が長すぎてコンテキスト制限を超えた

**解決**:
```json
{
  "options": {
    "num_ctx": 8192  # コンテキストサイズを増やす
  }
}
```
または会話履歴をトリミング

#### エラー: `CUDA out of memory`

**意味**: GPU メモリ不足

**解決**:
```bash
# CPU のみで実行
export OLLAMA_NUM_GPU=0

# または軽量モデルに変更
ollama pull gemma3:1b
```

#### エラー: `rate limit exceeded`

**意味**: リクエスト数が多すぎる

**解決**:
```python
import time

# リクエスト間に遅延を追加
for prompt in prompts:
    response = send_request(prompt)
    time.sleep(1)  # 1秒待機
```

### サポートとコミュニティ

問題が解決しない場合は、以下のリソースを活用してください：

- **公式ドキュメント**: https://github.com/ollama/ollama/blob/main/docs/
- **GitHub Issues**: https://github.com/ollama/ollama/issues
- **Discord コミュニティ**: https://discord.gg/ollama
- **Reddit**: r/ollama

---

## まとめ

このセットアップ手順書では、以下の内容をカバーしました：

1. **システム要件**: 各モデルに必要な最小・推奨スペック
2. **インストール**: Windows/macOS/Linux での複数のインストール方法
3. **初期設定**: 環境変数の設定とカスタマイズ
4. **モデル取得**: Gemma 3 の各バージョンのダウンロードと選択指針
5. **動作確認**: API テストと Function Calling の確認
6. **プロジェクト統合**: C# サーバと Python クライアントとの連携
7. **パフォーマンス最適化**: GPU 活用、メモリ管理、モデル選択
8. **トラブルシューティング**: よくある問題と解決策、ログ確認方法

これで Ollama と Gemma 3 を使用した Function Calling システムの構築準備が整いました。

次のステップ：
- `docs/gemma3-function-calling-plan.md` で実装計画を確認
- C# サーバと Python クライアントの実装を開始
- 実際の Function Calling を試して動作を確認

質問や問題が発生した場合は、このドキュメントのトラブルシューティングセクションを参照してください。
