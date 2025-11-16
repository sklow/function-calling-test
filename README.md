# Gemma 3 Function Calling システム

Gemma 3とOllamaを使用したFunction Callingシステムです。C# APIサーバーがツールを提供し、Python クライアントがLLMとの対話を管理します。

## 📋 概要

このシステムは、Gemma 3 LLMが外部ツールを呼び出して複雑なタスクを実行できるようにします。

### 主な特徴

- 🤖 **Gemma 3 統合**: Ollama経由でGemma 3を使用
- 🔧 **拡張可能なツールシステム**: C# APIサーバーでツールを管理
- 🎯 **JSON Schema方式**: 標準Gemmaモデルでの構造化出力
- 💬 **ユーザーフレンドリーなCLI**: 単発質問と対話モード
- 📝 **柔軟なプロンプト管理**: 4種類のテンプレートから選択可能
- 🔄 **自動リトライ**: ネットワークエラーやパースエラーに対応

## 🏗️ システム構成

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│                 │    │                 │    │                 │
│  Python Client  │◄──►│   C# Server     │    │     Ollama      │
│                 │    │                 │    │                 │
│ オーケストレーション │    │   ツール提供      │    │   Gemma 3      │
│ ユーザーインターフェース │    │   API エンドポイント │    │   LLM実行       │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
       localhost          localhost:5000        localhost:11434
```

### C# サーバー（ツール提供層）
- **GET /tools**: 利用可能なツールの一覧を取得
- **POST /tools/get_weather**: 天気情報取得ツール
- JSON Schema自動生成、CORS、Swagger UI対応

### Python クライアント（オーケストレーション層）
- Ollama API統合
- ツール呼び出し管理（キャッシュ・リトライ付き）
- システムプロンプト管理
- CLI インターフェース

## 🚀 クイックスタート

### 1. 必要要件

- **.NET 8 SDK**: C# サーバー用
- **Python 3.8+**: クライアント用
- **Ollama**: LLM実行環境

### 2. Ollamaのセットアップ

```bash
# Ollamaをインストール（公式サイトから）
# https://ollama.ai/

# Ollamaサーバー起動
ollama serve

# 別ターミナルでGemma 3モデルを取得
ollama pull gemma3:4b
```

詳細は [docs/ollama-setup.md](docs/ollama-setup.md) を参照してください。

### 3. C# サーバーの起動

```bash
cd server
dotnet restore
dotnet run --urls "http://localhost:5000"
```

### 4. Python クライアントのセットアップ

```bash
cd client
pip install -r requirements.txt

# 環境変数の設定（任意）
cp .env.example .env
# .envファイルを編集して設定をカスタマイズ
```

### 5. システムの動作確認

```bash
cd client
python main.py "東京の天気を教えて"
```

## 💻 使用方法

### 単発質問モード

```bash
# 基本的な使用
python main.py "質問内容"

# 例: 天気の質問
python main.py "大阪の天気を教えて"

# モデルを指定
python main.py --model gemma3:12b "複雑な質問"

# デバッグモード
python main.py --debug --verbose "質問内容"
```

### 対話モード

```bash
# 対話モードで開始
python main.py --interactive

# または引数なしで起動
python main.py
```

対話モードでの操作：
- 複数行入力: `END` またはCtrl+Dで入力終了
- 内蔵コマンド:
  - `/help`: ヘルプ表示
  - `/tools`: 利用可能なツール一覧
  - `/status`: システム状態確認
  - `/debug`: デバッグモード切り替え
  - `/quit`: 終了

### コマンドライン引数

```bash
python main.py [質問] [オプション]

位置引数:
  query                 ユーザーの質問（省略時は対話モード）

オプション:
  -i, --interactive     対話モード
  -m, --model MODEL     使用するLLMモデル (デフォルト: gemma3:4b)
  --api-base URL        APIサーバーのURL (デフォルト: http://localhost:5000)
  --ollama-host URL     OllamaサーバーのURL (デフォルト: http://localhost:11434)
  --max-iterations N    最大反復回数 (デフォルト: 10)
  --timeout N           タイムアウト秒数 (デフォルト: 30)
  --template TYPE       プロンプトテンプレート (standard/concise/detailed/debug)
  -d, --debug           デバッグモード
  -v, --verbose         詳細ログ
  --log-file FILE       ログファイルのパス
```

## 📁 ディレクトリ構造

```
FunctionCallingTest/
├── README.md                     # このファイル
├── docs/                         # ドキュメント
│   ├── ollama-setup.md          # Ollama セットアップガイド
│   ├── prompt_builder_guide.md   # プロンプト管理ガイド
│   └── gemma3-function-calling-plan.md  # 設計計画書
├── server/                       # C# APIサーバー
│   ├── Program.cs               # エントリーポイント
│   ├── FunctionCallingServer.csproj
│   ├── Models/                  # データモデル
│   │   ├── ToolMetadata.cs
│   │   └── DTOs/
│   │       ├── WeatherRequest.cs
│   │       └── WeatherResponse.cs
│   ├── Services/                # ビジネスロジック
│   │   └── ToolRegistry.cs
│   ├── Tools/                   # ツール実装
│   │   └── WeatherTool.cs
│   └── Utils/                   # ユーティリティ
│       └── SchemaGenerator.cs
├── client/                       # Python クライアント
│   ├── main.py                  # CLI エントリーポイント
│   ├── requirements.txt         # Python 依存関係
│   ├── .env.example            # 環境変数テンプレート
│   ├── USAGE.md                # 詳細な使用ガイド
│   ├── llm/                    # LLM通信
│   │   └── ollama_client.py
│   ├── api/                    # API通信
│   │   ├── tool_client.py
│   │   └── registry.py
│   ├── schemas/                # データスキーマ
│   │   └── tool_call.py
│   ├── orchestrator/           # オーケストレーション
│   │   └── loop.py
│   ├── prompts/                # プロンプト管理
│   │   ├── prompt_builder.py
│   │   └── system_prompt*.txt
│   └── utils/                  # ユーティリティ
└── .vscode/                     # VS Code 設定
    └── settings.json
```

## 🛠️ 開発情報

### 利用可能なツール

現在実装されているツール：
- **get_weather**: 指定した都市の天気情報を取得

### カスタムツールの追加

1. C# サーバー側でツールを実装：
   ```csharp
   // server/Tools/YourTool.cs
   public class YourTool : IYourTool { ... }
   ```

2. DTO クラスを定義：
   ```csharp
   // server/Models/DTOs/YourRequest.cs
   public record YourRequest(string Param);
   ```

3. Program.cs でサービスとエンドポイントを登録

### プロンプトテンプレート

4種類のテンプレートが利用可能：
- **standard**: バランスの取れたデフォルト
- **concise**: トークン節約重視
- **detailed**: 詳細な説明付き
- **debug**: デバッグ情報出力

## 🔧 トラブルシューティング

### よくある問題

**1. "Ollama サーバーに接続できない"**
```bash
# Ollama が起動しているか確認
ollama serve

# モデルがインストールされているか確認
ollama list
```

**2. "API サーバーに接続できない"**
```bash
# C# サーバーが起動しているか確認
cd server
dotnet run --urls "http://localhost:5000"
```

**3. "JSON パースエラーが頻発する"**
- デバッグモードで詳細を確認: `--debug --verbose`
- プロンプトテンプレートを変更: `--template debug`

**4. "応答が遅い"**
- タイムアウトを延長: `--timeout 60`
- より軽量なモデルを使用: `--model gemma3:1b`

### ログの確認

```bash
# 詳細ログ付きで実行
python main.py --verbose --log-file session.log "質問"

# ログファイルを確認
cat session.log
```

## 📚 関連ドキュメント

- [Ollama セットアップガイド](docs/ollama-setup.md)
- [プロンプトビルダーガイド](docs/prompt_builder_guide.md)
- [詳細な使用方法](client/USAGE.md)
- [設計計画書](docs/gemma3-function-calling-plan.md)

## 🤝 コントリビューション

1. フォークしてください
2. フィーチャーブランチを作成: `git checkout -b feature/amazing-feature`
3. 変更をコミット: `git commit -m 'Add amazing feature'`
4. ブランチにプッシュ: `git push origin feature/amazing-feature`
5. プルリクエストを作成してください

## 📄 ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 🙏 謝辞

- [Ollama](https://ollama.ai/) - ローカルLLM実行環境
- [Google Gemma](https://ai.google.dev/gemma) - LLMモデル
- [ASP.NET Core](https://docs.microsoft.com/aspnet/core/) - Web API フレームワーク
- [Pydantic](https://pydantic-docs.helpmanual.io/) - Python データバリデーション