# オーケストレーションループ実装ドキュメント

## 概要

このモジュールは、Gemma 3 モデル用のメインオーケストレーションループを実装しています。LLMとC# APIサーバーのツールを連携させ、ユーザーの質問に対して反復的に回答を生成します。

## ファイル構成

```
client/orchestrator/
├── __init__.py           # モジュールのエントリポイント
├── loop.py               # メインのオーケストレーションループ実装
├── test_loop_unit.py     # ユニットテスト
├── demo_loop.py          # デモスクリプト
└── README.md             # このファイル
```

## 主要コンポーネント

### 1. メイン関数: `run_loop()`

オーケストレーションループのエントリポイントです。

```python
from client.orchestrator import run_loop

answer = run_loop(
    user_query="東京の天気は?",
    model="gemma3:4b",
    api_base="http://localhost:5000",
    ollama_host="http://localhost:11434",
    max_iterations=10,
    timeout=30
)

print(answer)
```

**パラメータ:**
- `user_query` (str): ユーザーの質問
- `model` (str): 使用するLLMモデル名（デフォルト: "gemma3:4b"）
- `api_base` (str): C# APIサーバーのベースURL（デフォルト: "http://localhost:5000"）
- `ollama_host` (str): OllamaサーバーのURL（デフォルト: "http://localhost:11434"）
- `max_iterations` (int): 最大反復回数（デフォルト: 10）
- `timeout` (int): タイムアウト秒数（デフォルト: 30）

**戻り値:**
- `str`: 最終的な回答文字列

**例外:**
- `OrchestratorError`: オーケストレーション全般のエラー
- `MaxIterationsReached`: 最大反復回数に到達
- `InvalidResponseFormat`: LLMからの無効なレスポンス形式
- `ToolExecutionFailed`: ツール実行の失敗

### 2. システムプロンプト構築: `build_system_prompt()`

利用可能なツール情報を含むシステムプロンプトを生成します。

```python
from client.orchestrator import build_system_prompt

tools = [
    {
        "name": "get_weather",
        "description": "天気情報を取得",
        "inputSchema": {...}
    }
]

prompt = build_system_prompt(tools)
```

### 3. ツール実行: `execute_tool()`

ツール呼び出しを実行し、結果を `ToolResult` で返します。

```python
from client.orchestrator import execute_tool
from client.schemas.tool_call import ToolCall

tool_call = ToolCall(
    tool="get_weather",
    arguments={"city": "Tokyo"}
)

result = execute_tool(tool_call, api_base="http://localhost:5000")

if result.ok:
    print("成功:", result.content)
else:
    print("失敗:", result.error)
```

### 4. JSON補完: `safe_parse_json()`

不完全なJSONを補完してパース可能にします。

```python
from client.orchestrator import safe_parse_json

# 括弧が不足しているJSON
incomplete_json = '{"kind": "final_answer", "content": "テスト"'

# 補完してパース
fixed_json = safe_parse_json(incomplete_json)
```

## オーケストレーションの流れ

```
1. 初期化
   ├─ ツールレジストリの取得
   ├─ システムプロンプトの構築
   └─ メッセージ履歴の初期化

2. メインループ（最大max_iterations回）
   ├─ フェーズ1: LLM呼び出し
   │   └─ JSON Schema制約付きで呼び出し
   │
   ├─ フェーズ2: レスポンスのパース
   │   ├─ ToolCall → ツール実行へ
   │   ├─ FinalAnswer → 終了
   │   └─ Clarification → エラー（将来対応）
   │
   └─ フェーズ3: アクション処理
       ├─ ツール呼び出しの実行
       ├─ 結果をメッセージ履歴に追加
       └─ 次の反復へ

3. 完了
   └─ 最終回答を返却
```

## JSON Schema 定義

LLMのレスポンスを制約するために使用される `CALL_SCHEMA`:

```json
{
  "type": "object",
  "properties": {
    "kind": {
      "type": "string",
      "enum": ["tool_call", "final_answer", "clarify"]
    },
    "tool": {"type": "string"},
    "arguments": {"type": "object"},
    "content": {"type": "string"},
    "thought": {"type": "string"},
    "question": {"type": "string"},
    "missing_params": {
      "type": "array",
      "items": {"type": "string"}
    }
  },
  "required": ["kind"],
  "allOf": [...]
}
```

## エラーハンドリング

### カスタム例外クラス

- **OrchestratorError**: すべてのオーケストレーションエラーの基底クラス
- **MaxIterationsReached**: 最大反復回数に到達した場合
- **InvalidResponseFormat**: LLMが無効な形式のレスポンスを返した場合
- **ToolExecutionFailed**: ツールの実行に失敗した場合

### エラー復旧

- **JSONパースエラー**: `safe_parse_json()` で自動補完を試行
- **ツール実行エラー**: `ToolResult(ok=False)` で継続、LLMに通知
- **接続エラー**: 適切なエラーメッセージとともに終了

## ログ出力

詳細なログを出力して、オーケストレーションの各ステップを追跡できます。

```python
import logging

# ログレベルを設定
logging.basicConfig(
    level=logging.DEBUG,  # または INFO, WARNING, ERROR
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# オーケストレーションを実行
answer = run_loop("東京の天気は?")
```

**ログ出力例:**
```
2025-11-16 22:55:00 - client.orchestrator.loop - INFO - ========== オーケストレーションループを開始します ==========
2025-11-16 22:55:00 - client.orchestrator.loop - INFO - ユーザークエリ: 東京の天気は?
2025-11-16 22:55:00 - client.orchestrator.loop - INFO - ステップ1: ツールレジストリを取得中...
2025-11-16 22:55:01 - client.orchestrator.loop - INFO - 利用可能なツール数: 3
2025-11-16 22:55:01 - client.orchestrator.loop - INFO - オーケストレーション反復 1/10 を開始
2025-11-16 22:55:01 - client.orchestrator.loop - INFO - フェーズ1: LLMに問い合わせ中...
...
```

## テスト

### ユニットテスト

```bash
cd D:\_dev\FunctionCallingTest
python client/orchestrator/test_loop_unit.py
```

**テスト内容:**
- システムプロンプト生成（空のツール、ツール有）
- ツール実行（成功、失敗）
- JSON補完（正常、コードブロック、括弧不足、無効）

### デモスクリプト

```bash
cd D:\_dev\FunctionCallingTest
python client/orchestrator/demo_loop.py
```

サーバー接続なしで基本機能をデモします。

### 統合テスト

実際のサーバーを使用したテスト:

```bash
# 前提条件:
# 1. Ollama サーバーが起動している
# 2. C# API サーバーが起動している
# 3. Gemma 3 モデルがインストールされている

cd D:\_dev\FunctionCallingTest
python client/test_loop.py
```

## 使用例

### 基本的な使用

```python
from client.orchestrator import run_loop

# シンプルな質問
answer = run_loop("こんにちは")
print(answer)
# 出力: こんにちは!何かお手伝いできることはありますか?

# ツールを使用する質問
answer = run_loop("東京の天気を教えて")
print(answer)
# 出力: 東京の今日の天気は晴れで、気温は25度です。
```

### カスタム設定

```python
from client.orchestrator import run_loop, OrchestratorError
import logging

# ログを詳細に設定
logging.basicConfig(level=logging.DEBUG)

try:
    answer = run_loop(
        user_query="複雑な質問",
        model="gemma3:4b",
        max_iterations=15,  # 反復回数を増やす
        timeout=60          # タイムアウトを長く
    )
    print(answer)

except OrchestratorError as e:
    print(f"エラー: {e}")
```

## 将来の拡張

- **Clarification対応**: ユーザーへの確認質問の処理
- **マルチツール並列実行**: 複数のツールを並列で呼び出し
- **Vision対応**: 画像入力のサポート
- **ストリーミングレスポンス**: リアルタイムでレスポンスを返却
- **会話履歴管理**: 複数ターンの会話をサポート

## 依存関係

- `client.api.registry`: ツールレジストリの取得
- `client.api.tool_client`: ツール呼び出し
- `client.llm.ollama_client`: Ollama Chat API
- `client.schemas.tool_call`: Pydanticモデル

## ライセンス

このプロジェクトの一部として、同じライセンスが適用されます。

## サポート

問題や質問がある場合は、プロジェクトのissueトラッカーに報告してください。
