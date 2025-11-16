# プロンプトビルダーガイド

## 概要

`client/prompts` モジュールは、LLM（Gemma 3）に渡すシステムプロンプトの設計と管理を担当します。
このガイドでは、プロンプトビルダーの使用方法と実装の詳細を説明します。

## ディレクトリ構造

```
client/prompts/
├── __init__.py                      # モジュール公開インターフェース
├── prompt_builder.py                # プロンプト構築の主要ロジック
├── system_prompt.txt                # 標準テンプレート
├── system_prompt_concise.txt        # 簡潔版テンプレート
├── system_prompt_detailed.txt       # 詳細版テンプレート
└── system_prompt_debug.txt          # デバッグ版テンプレート
```

## 主要機能

### 1. プロンプトビルダークラス (`PromptBuilder`)

システムプロンプトを動的に構築するためのクラスです。

#### 基本的な使用方法

```python
from client.prompts import PromptBuilder

# ビルダーのインスタンス化
builder = PromptBuilder()

# システムプロンプトの構築
prompt = builder.build_system_prompt(
    tools=tools_list,              # ツールのリスト
    language='ja',                 # 言語（'ja' または 'en'）
    template_name='standard',      # テンプレート名
    format_style='detailed',       # フォーマットスタイル
    custom_instructions=None       # カスタム指示（任意）
)
```

#### パラメータ詳細

- **tools**: ツールレジストリから取得したツールのリスト
- **language**: 言語コード（'ja': 日本語、'en': 英語）
- **template_name**: 使用するテンプレート
  - `'standard'`: 標準テンプレート（バランス型）
  - `'concise'`: 簡潔版（トークン節約）
  - `'detailed'`: 詳細版（詳しい説明）
  - `'debug'`: デバッグ版（デバッグ情報を含む）
- **format_style**: ツール一覧のフォーマット
  - `'detailed'`: 詳細な情報（パラメータ説明、使用例）
  - `'concise'`: 簡潔な情報（必須パラメータのみ）
  - `'minimal'`: 最小限の情報（名前と説明のみ）
- **custom_instructions**: 追加の指示（任意）

### 2. 後方互換性関数 (`build_system_prompt`)

既存のコードとの互換性のために提供される関数です。

```python
from client.prompts import build_system_prompt

# シンプルな使用方法
prompt = build_system_prompt(tools)
```

この関数は内部的に `PromptBuilder` を使用し、デフォルト設定でプロンプトを構築します。

### 3. ツール情報の抽出 (`extract_tool_schema_info`)

ツールの JSON Schema から人間読みやすい情報を抽出します。

```python
from client.prompts import extract_tool_schema_info

tool_info = extract_tool_schema_info(tool_definition)

# 戻り値:
# {
#     'name': 'get_weather',
#     'description': '指定した都市の現在の天気情報を取得します',
#     'required_params': ['city'],
#     'optional_params': ['unit'],
#     'param_descriptions': {
#         'city': '(string): 都市名（例: Tokyo, New York）',
#         'unit': '(string): 温度単位（metric または imperial）'
#     },
#     'example_usage': {
#         'tool': 'get_weather',
#         'arguments': {'city': '<cityの値>'}
#     }
# }
```

### 4. ツール一覧のフォーマット (`format_tools_list`)

ツールのリストを見やすい形式でフォーマットします。

```python
from client.prompts import format_tools_list

formatted = format_tools_list(
    tools=tools_list,
    format_style='detailed',  # 'detailed', 'concise', 'minimal'
    language='ja'             # 'ja', 'en'
)
```

## テンプレートの種類

### 1. 標準テンプレート (`system_prompt.txt`)

バランスの取れたテンプレートです。通常はこれを使用します。

- **特徴**: 適度な詳しさ、明確な指示
- **トークン数**: 中程度
- **推奨用途**: 一般的なタスク

### 2. 簡潔版テンプレート (`system_prompt_concise.txt`)

トークン数を節約したいときに使用します。

- **特徴**: 最小限の説明、コンパクト
- **トークン数**: 少ない
- **推奨用途**: トークン制限が厳しい場合

### 3. 詳細版テンプレート (`system_prompt_detailed.txt`)

複雑なタスクや高精度が必要なときに使用します。

- **特徴**: 詳しい説明、多数の例、明確なガイドライン
- **トークン数**: 多い
- **推奨用途**: 複雑なタスク、高精度が必要な場合

### 4. デバッグ版テンプレート (`system_prompt_debug.txt`)

開発・デバッグ時に使用します。

- **特徴**: デバッグ情報の要求、思考過程の記録
- **トークン数**: 中程度
- **推奨用途**: 開発・デバッグ時

## カスタム指示の追加

プロンプトにカスタム指示を追加できます。

```python
builder = PromptBuilder()

custom = """
ユーザーには丁寧な敬語で回答してください。
回答は箇条書きで簡潔にまとめてください。
専門用語を使う場合は、わかりやすく説明してください。
"""

prompt = builder.build_system_prompt(
    tools=tools_list,
    custom_instructions=custom
)
```

カスタム指示は、テンプレートの `{custom_instructions}` プレースホルダーに挿入されます。

## プロンプト変数管理 (`PromptVariables`)

テンプレート内の変数を管理するクラスです。

```python
from client.prompts import PromptVariables

variables = PromptVariables()

# 変数の設定
variables.set_variable('tools_list', formatted_tools)
variables.set_variable('language', 'ja')
variables.set_variable('custom_instructions', custom_text)

# テンプレートの変数置換
template = "利用可能なツール:\n{tools_list}"
result = variables.format_template(template)
```

### 利用可能な変数

- `{tools_list}`: ツール一覧
- `{language}`: 言語コード
- `{response_format}`: レスポンス形式
- `{max_iterations}`: 最大反復回数
- `{custom_instructions}`: カスタム指示
- `{examples}`: 使用例

## 多言語対応

日本語と英語に対応しています。

```python
# 日本語プロンプト
prompt_ja = builder.build_system_prompt(
    tools=tools_list,
    language='ja'
)

# 英語プロンプト
prompt_en = builder.build_system_prompt(
    tools=tools_list,
    language='en'
)
```

言語設定は `LANGUAGE_CONFIGS` 定数で管理されています。

## 既存コードとの統合

`client/orchestrator/loop.py` では、以下のように統合されています：

```python
# 新しいプロンプトビルダーのインポート
from client.prompts.prompt_builder import build_system_prompt as new_build_system_prompt

# プロンプトの構築
system_prompt = new_build_system_prompt(tools)
```

既存の `loop.py` 内の `build_system_prompt()` 関数は非推奨となり、
新しいモジュールの関数に委譲されています。

## 実装の詳細

### ツールスキーマの抽出ロジック

1. `inputSchema` から `properties` と `required` を取得
2. 各パラメータの型と説明を抽出
3. 必須パラメータと任意パラメータを分類
4. 使用例を自動生成

### フォーマットスタイルの違い

#### Detailed（詳細版）
```
## get_weather
指定した都市の現在の天気情報を取得します

パラメータ:
  - city (必須): (string): 都市名（例: Tokyo, New York）
  - unit (任意): (string): 温度単位（metric または imperial）

使用例:
{
  "tool": "get_weather",
  "arguments": {
    "city": "<cityの値>"
  }
}
```

#### Concise（簡潔版）
```
## get_weather
指定した都市の現在の天気情報を取得します
パラメータ: city
```

#### Minimal（最小版）
```
## get_weather
指定した都市の現在の天気情報を取得します
```

## テスト

テストスクリプトが用意されています：

```bash
python test_prompt_builder.py
```

このスクリプトは以下をテストします：

1. ツールスキーマ情報の抽出
2. ツール一覧のフォーマット（詳細版・簡潔版）
3. システムプロンプト構築（標準テンプレート）
4. PromptBuilder クラス（簡潔版テンプレート）
5. カスタム指示の追加
6. 詳細版テンプレート
7. デバッグ版テンプレート

## ベストプラクティス

### 1. 適切なテンプレートの選択

- **通常のタスク**: `standard`
- **トークン節約**: `concise`
- **複雑なタスク**: `detailed`
- **開発中**: `debug`

### 2. フォーマットスタイルの選択

- **初回実装**: `detailed` で動作確認
- **本番運用**: `concise` でトークン節約
- **ツールが少ない**: `detailed` で詳細情報提供
- **ツールが多い**: `minimal` で簡潔に

### 3. カスタム指示の活用

ドメイン固有の指示を追加することで、より精度の高い回答を得られます：

```python
custom = """
医療情報を扱う場合は、必ず情報源を明記してください。
診断や治療の推奨は行わず、医療従事者への相談を促してください。
"""
```

### 4. パフォーマンスの考慮

- トークン数が多いと処理時間が増加します
- 必要最小限のツール情報を含める
- `concise` または `minimal` スタイルを検討

## トラブルシューティング

### テンプレートファイルが見つからない

```
WARNING: テンプレートファイルが見つかりません
WARNING: デフォルトテンプレートを使用します
```

→ `client/prompts/` ディレクトリにテンプレートファイルがあるか確認してください。

### カスタム変数が置換されない

テンプレート内に対応するプレースホルダー（`{変数名}`）があるか確認してください。

### LLMの応答が不正確

1. より詳細なテンプレート（`detailed`）を試す
2. カスタム指示を追加して具体的な指示を与える
3. ツール説明をより詳しく記述する

## 今後の拡張

### 予定されている機能

1. **トークン最適化**
   - トークナイザーを使用した正確なトークン数測定
   - 自動的なプロンプト最適化

2. **プロンプト効果測定**
   - テストクエリでの評価
   - A/B テスト機能

3. **テンプレートのカスタマイズ**
   - ユーザー定義テンプレートのサポート
   - テンプレート継承機能

4. **動的プロンプト調整**
   - LLMの応答に基づく動的な調整
   - 文脈に応じたプロンプト変更

## まとめ

プロンプトビルダーモジュールは以下を提供します：

- **柔軟なプロンプト構築**: 複数のテンプレートとスタイル
- **ツール情報の自動挿入**: JSON Schema からの自動生成
- **多言語対応**: 日本語・英語のサポート
- **カスタマイズ性**: カスタム指示の追加
- **後方互換性**: 既存コードとの統合

これにより、LLM とのやり取りをより効果的に制御できます。
