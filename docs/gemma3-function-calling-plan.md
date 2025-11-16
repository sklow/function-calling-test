## Gemma 3 × Ollama Structured Output 計画（Function Calling 風）

### 目的
- Gemma 3（`gemma3:4b`）を Ollama で実行し、Ollama の Structured Output（JSON/JSON Schema）と Tool Calling を活用して、LLM が「どのツール（C# API）をどの引数で呼ぶか」を安全・一貫して指示する。
- サーバは C#（ASP.NET Core）でツールを HTTP で公開、クライアントは Python で LLM 対話・スキーマ検証・API 呼び出しを仲介。

### 最新リリース情報（2025-11 時点）
- Gemma 3 は 2025-03-12 に正式リリースされ、1B / 4B / 12B / 27B の 4 サイズと 270M系の軽量派生が存在。4B 以上はテキスト＋画像のマルチモーダル入力と 128K トークンのコンテキストをサポート。
- Ollama ライブラリの `gemma3` には `gemma3:1b`（テキストのみ）と `gemma3:4b/12b/27b`（Vision タグ付き）が公開済み。量子化済みの `gemma3:4b` がデフォルト pull 対象、性能要求に応じて 12B / 27B を選択する。

### 全体像
```
┌──────────────┐       prompt/JSON        ┌────────────┐
│  Python Client│  <────────────────────> │  Gemma 3   │
│ (orchestrator)│      (structured)       │ (inference)│
└─────┬──────────┘                         └────────────┘
      │  HTTP(S)
      ▼
┌──────────────┐    tools (REST)    ┌────────────────────┐
│  C# Server   │ <────────────────> │  External Services │
│ (ASP.NET API)│                    │  (DB/Weather/etc.) │
└──────────────┘                    └────────────────────┘
```

### コアアイデア（Ollama 版）
- Ollama の `format` 機能で JSON/JSON Schema に拘束できる（JSON モード or スキーマ）。
- Ollama `/api/chat` の Tool Calling（`tools`、応答の `message.tool_calls`）で関数呼び出しの指示を安全に取得。
- Python クライアントは Tool 対応モデルなら `tool_calls` を実行し、標準モデルなら JSON Schema で自己申告された `call_tool` オブジェクトを解釈して結果を `role: tool` で返し→最終ターンで `format` により構造化最終回答を取得。

> **注意 (Gemma 3 の Tool 対応)**
> - 2025年11月時点で Ollama 公式の `gemma3` ライブラリは `tools` フラグが無効なため、`tools` パラメータを渡すと 400 `does not support tools` が返る（`tool_calls` は生成されない）。
> - Gemma 3 自体は function calling がサポートされているので、標準モデルでは JSON Schema に沿った `call_tool`/`final_answer` オブジェクトを自発的に出力させる構成を基本とする。
> - ネイティブな Tool Calling が必要であれば `PetrosStav/gemma3-tools` など、`tools` タグ付きのコミュニティモデルを pull して使う。
> - いずれの経路でも `format` に JSON Schema を渡し、Python 側で検証する（標準モデルでは常時 Schema、Tool 対応モデルでは最終回答のみ Schema）。

---

## Ollama の Structured Output 活用

### 基本
- Ollama は `format` で出力を拘束可能（`"json"` か JSON Schema オブジェクトを指定）。
  - `"format": "json"` で JSON を強制。
  - `"format": { ...JSON Schema... }` でスキーマ準拠を強制（直接スキーマを渡す）。
- チャットは `/api/chat` を利用。Tool Calling は `tools` で宣言し、応答の `message.tool_calls` を解釈。
- スキーマ拘束時は `stream: false` を推奨（完全 JSON を一括取得）。

注意: 本仕様は Ollama 公式 API ドキュメント（/api/generate と /api/chat）に基づく。`format` は `"json"` または「JSON Schema オブジェクト」を直接指定する。

### Pydantic 連携と `format` 指定
- `pydantic.BaseModel` を定義し、`model_json_schema()` を `format` に渡すと Llma.cpp 側で GBNF に変換される（手書き JSON Schema より安全）。
- 返却は `model_validate_json()`（v2系）や `model_validate()` でバリデーション可能。例:
```python
from typing import Any, Literal
from ollama import chat
from pydantic import BaseModel

class ToolCall(BaseModel):
    kind: Literal["call_tool", "final_answer", "clarify"]
    tool: str | None = None
    arguments: dict[str, Any] | None = None
    content: str | None = None

resp = chat(
    model="gemma3:4b",
    messages=messages,
    format=ToolCall.model_json_schema(),
    options={"temperature": 0, "seed": 42}
)
tool_call = ToolCall.model_validate_json(resp["message"]["content"])
```
- 温度は `0`（float 0.0 ではなく int 0 で deterministic モード）＋ `seed` 指定で再現性を高める。

### マルチモーダル入力（Vision）
- `gemma3:4b` 以上は `messages[i]["images"]` に base64 あるいはファイルパスを指定可能。
- ツール呼び出し判断を画像＋テキストで行うときは、Vision 対応モデルに限定する。
```python
resp = chat(
    model="gemma3:12b",
    messages=[{
        "role": "user",
        "content": "画像を解析して必要な API を選んで",
        "images": ["/path/to/panel.jpg"]
    }],
    format=ToolCall.model_json_schema()
)
```

### Schema → GBNF 制約
- Ollama は受け取った JSON Schema を Greibach BNF に変換して llama.cpp の grammar API に渡すため、100% 構文的に正しい JSON になる（途中打ち切り時を除く）。
- grammar 変換に時間がかかる大型スキーマは最小限に保ち、可能ならツール単位の小さなモデルを複数定義する。

---

## ツール呼び出しプロトコル（JSON Schema）

LLM → クライアント（要求）
```json
{
  "kind": "call_tool",      // call_tool | final_answer | clarify
  "tool": "get_weather",    // ツール名（C# 側の公開名）
  "arguments": {             // ツールへの引数（スキーマ準拠）
    "city": "Tokyo",
    "unit": "metric"
  },
  "thought": "...optional..."
}
```

クライアント → LLM（ツール実行結果）
```json
{
  "kind": "tool_result",
  "tool": "get_weather",
  "ok": true,
  "content": {"temp": 25.2, "desc": "Clear"},
  "error": null
}
```

最終応答
```json
{
  "kind": "final_answer",
  "content": "東京の現在の気温は25.2℃、快晴です。"
}
```

最小 JSON Schema（MVP）
```json
{
  "type": "object",
  "properties": {
    "kind": {"enum": ["call_tool", "final_answer", "clarify", "tool_result"]},
    "tool": {"type": "string"},
    "arguments": {"type": "object"},
    "content": {},
    "ok": {"type": "boolean"},
    "error": {"type": ["string", "null"]},
    "thought": {"type": ["string", "null"]}
  },
  "required": ["kind"]
}
```

Ollama への `format` 指定例（/api/chat、JSON Schema 直接指定）
```json
{
  "model": "gemma3:4b",
  "messages": [
    {"role": "system", "content": "あなたはツール呼び出しを行う補助エージェントです...（省略）"},
    {"role": "user", "content": "東京の天気を教えて"}
  ],
  "format": { /* 上記スキーマをそのまま指定 */ },
  "options": {"temperature": 0.0},
  "stream": false
}
```

Tool Calling の宣言例（/api/chat の `tools`）
（`tools` タグ付きモデルを使う場合のサンプル。標準 `gemma3` ではエラーになるため JSON Schema 経路を利用する。）
```json
{
  "model": "gemma3:4b",
  "messages": [{"role":"user","content":"東京の天気"}],
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "get_weather",
        "description": "Get the weather in a given city",
        "parameters": {
          "type": "object",
          "properties": {
            "city": {"type":"string"},
            "unit": {"type":"string","enum":["metric","imperial"],"default":"metric"}
          },
          "required": ["city"]
        }
      }
    }
  ],
  "stream": false
}
```
- ツール実行結果を LLM に戻す際は、Ollama の Tool Calling 仕様に沿って `{"role":"tool","content":...,"tool_name":...}` を `messages` に追加する。`role:"tool"` は公式に許可されたロールであり、`message.tool_calls[x].id` が返るモデルでは合わせて `tool_call_id` を含める。

---

## C# サーバ（ASP.NET Core）設計

### 役割
- ビジネスロジックを「ツール」として HTTP(S) で提供。
- 各ツールの入出力スキーマを公開（ツールレジストリ）。
- OpenAPI（Swagger）を自動公開。CORS/認証/制限を実装。

### エンドポイント例
- `GET /tools` ツール一覧（`name/description/input_schema/output_schema/http_method/path/auth`）。
- `GET /tools/schemas` もしくは `/tools` の中に各ツールの JSON Schema を含めて返却（LLM に渡すため）。
- `POST /tools/get_weather` 入力: `{city, unit}` → 出力: `{temp, desc}`。
- `POST /tools/search_products` 入力: `{q, limit}` → 出力: `[{id, title, price}]`。

### 技術スタック
- ASP.NET Core 8 Minimal APIs
- Swashbuckle (OpenAPI/Swagger)
- NJsonSchema/NSwag: DTO → JSON Schema 生成（LLM 提示用）
- FluentValidation または DataAnnotations（DTO 入力検証）
- 監視: Serilog + OpenTelemetry（任意）

### 非機能
- 認証: API Key または OAuth2（要件次第）。
- レート制限: `AspNetCoreRateLimit` など。
- CORS: Python クライアント許可。

---

## Python クライアント設計（Ollama）

### 役割
- LLM との対話ループのオーケストレーション。
- 構造化出力の検証、C# ツール呼び出し、結果の再プロンプト。

### 実装ポイント
- LLM 呼び出し: Ollama `/api/chat` を使用。Tool Calling を優先し、最終回答のみ `format` で JSON/Schema を強制。
- ツール呼び出し経路: 標準 `gemma3` では JSON Schema で `call_tool` を自己申告させる（`use_native_tool_calls=False`）、tool 対応モデルを使うときだけ `tools` パラメータと `message.tool_calls` を利用。
- JSON 検証: `format` 指定時はスキーマ準拠が期待できるが、`pydantic` または `jsonschema` で最終チェックし、失敗時は再プロンプト。
- 失敗復旧: 例外時の再試行（最大 N 回）。
- ループ終端: ツール呼び出しがなく `message.content` が返った段階で終了。必要ならそのターンのみ `format` を指定して再取得。
- 出力打ち切りやエンコードエラーに備えて、`json.loads` 失敗時は括弧補完や再生成を行う（完全保証ではない）。

### 疑似コード
```python
from typing import Dict, Any, List, Optional
import json, requests
from jsonschema import validate, ValidationError

CALL_SCHEMA = {
    "type": "object",
    "properties": {
        "kind": {"enum": ["call_tool", "final_answer", "clarify"]},
        "tool": {"type": "string"},
        "arguments": {"type": "object"},
        "content": {}
    },
    "required": ["kind"]
}

FINAL_SCHEMA = {
    "type": "object",
    "properties": {
        "kind": {"const": "final_answer"},
        "content": {"type": "string"}
    },
    "required": ["kind", "content"],
}

def call_tool(api_base: str, tool: str, args: Dict[str, Any]) -> Dict[str, Any]:
    resp = requests.post(f"{api_base}/tools/{tool}", json=args, timeout=30)
    resp.raise_for_status()
    return resp.json()

def ollama_chat(model: str,
                messages: List[Dict[str, Any]],
                tools: Optional[List[Dict[str, Any]]] = None,
                format_schema: Optional[Dict[str, Any]] = None,
                temperature: float = 0.0) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "options": {"temperature": temperature},
        "stream": False,
    }
    if tools:
        payload["tools"] = tools
    if format_schema:
        payload["format"] = format_schema  # JSON Schema を直接指定
    r = requests.post("http://localhost:11434/api/chat", json=payload, timeout=120)
    r.raise_for_status()
    return r.json()  # { model, message: { role, content, tool_calls? }, ... }

def run_loop(tool_api_base: str,
             system_prompt: str,
             user_input: str,
             tools: List[Dict[str, Any]],
             model: str = "gemma3:4b",
             use_native_tool_calls: bool = False) -> Dict[str, Any]:
    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input},
    ]
    # 1) ツール呼び出しフェーズ（Tool 対応モデル=tools / 標準モデル=CALL_SCHEMA）
    for _ in range(8):
        data = ollama_chat(
            model,
            messages,
            tools=tools if use_native_tool_calls else None,
            format_schema=None if use_native_tool_calls else CALL_SCHEMA,
        )
        msg = data.get("message", {})
        raw_content = (msg.get("content") or "").strip()
        structured: Optional[Dict[str, Any]] = None
        if not use_native_tool_calls and raw_content:
            try:
                structured = json.loads(raw_content)
            except json.JSONDecodeError:
                structured = None

        tool_calls = msg.get("tool_calls") or [] if use_native_tool_calls else []
        if not use_native_tool_calls and structured and structured.get("kind") == "call_tool":
            tool_calls = [{
                "function": {
                    "name": structured.get("tool"),
                    "arguments": structured.get("arguments", {}),
                }
            }]
        if tool_calls:
            # 最初の tool call のみ順次処理（複数のときはループ可）
            for call in tool_calls:
                fn = call.get("function", {})
                name = fn.get("name")
                args = fn.get("arguments", {})
                try:
                    result = call_tool(tool_api_base, name, args)
                    tool_content = json.dumps(result, ensure_ascii=False)
                except Exception as e:
                    tool_content = json.dumps({"error": str(e)}, ensure_ascii=False)
                # Ollama 仕様: ツールの実行結果は role: tool, tool_name で返信
                messages.append({
                    "role": "tool",
                    "content": tool_content,
                    "tool_name": name,
                })
            continue
        # tool_calls がない → 最終応答がある可能性
        if not use_native_tool_calls and structured:
            if structured.get("kind") == "final_answer":
                content = structured.get("content", "")
            elif structured.get("kind") == "clarify":
                return structured
            else:
                content = raw_content
        else:
            content = raw_content
        if content:
            # 2) 最終回答を JSON で厳格取得（同履歴に対して再度 format 指定）
            data2 = ollama_chat(model, messages + [{"role": "assistant", "content": content}],
                                 format_schema=FINAL_SCHEMA)
            raw = data2.get("message", {}).get("content", "")
            try:
                obj = json.loads(raw)
                validate(obj, FINAL_SCHEMA)
                return obj  # { kind: final_answer, content: ... }
            except (json.JSONDecodeError, ValidationError) as e:
                # スキーマ化に失敗した場合は素のテキストを包んで返す
                return {"kind": "final_answer", "content": content, "note": f"schema_error: {e}"}
    return {"kind": "final_answer", "content": "対話回数上限に達しました。"}
```

### JSON 安全パース補助
```python
def safe_parse_json(raw: str) -> dict[str, Any]:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        trimmed = raw.rstrip()
        if not trimmed.endswith("}"):
            open_braces = trimmed.count("{") - trimmed.count("}")
            trimmed += "}" * max(open_braces, 0)
        return json.loads(trimmed)
```
- grammar 拘束でも出力が途中停止する際に備えた簡易補正。補正後も失敗する場合は LLM へ再生成を依頼する。

### プロンプト雛形（MVP）
```
あなたはツールを使ってユーザー要求を解決するアシスタントです。
必要に応じて提供された tools を呼び出し、その結果を踏まえて回答します。
最終的な回答は JSON で返してください（スキーマは別途システム側で指定します）。
回答は日本語で簡潔にまとめてください。
```

---

## モデル実行（Ollama）
- ローカル: `ollama serve` を起動し、用途ごとに `ollama pull gemma3:1b/4b/12b/27b` を取得（4B 以上は Vision）。
- 推奨 `options`（構造化出力用）:
  - `temperature: 0`（整数 0 で deterministic）、`seed: 42`（任意の固定値）、`stream: false`。
  - `num_ctx`: 4096〜32768（Gemma 3 最大全 128K だが VRAM 要件に合わせて増減）。
  - `num_predict`: 512 前後（必要最大出力）、`top_p: 0.95`、`repeat_penalty: 1.1`。
- API: `http://localhost:11434/api/chat` を Python から呼び出し、Tool 対応モデルでは `tools` をそのまま渡し、標準モデルでは JSON Schema フローで `call_tool` を解釈する。

## Docker / ランタイム設定
- Compose 例: `ollama/ollama:latest` を使い、`./models:/root/.ollama/models` をマウント。
- `environment` に `OLLAMA_MODELS=/root/.ollama/models`、`OLLAMA_KEEP_ALIVE=5m`（未使用モデルの破棄までの時間）などを設定。
- GPU を使う場合は `deploy.resources.reservations.devices` で NVIDIA runtime を指定し、`ollama serve` 側は自動で GPU を利用する。

## モデル取得コマンド
```bash
ollama pull gemma3:4b   # Q4_0 量子化（Vision 対応）
ollama pull gemma3:1b   # テキスト専用、ツール自己申告用
ollama pull gemma3:27b  # 最高精度（要 32GB VRAM）
```
- 初回 pull 時に 4B がデフォルトで選択されるため、他サイズを使うときは明示的に指定。

---

## セキュリティと堅牢化
- 入力検証: C# 側 DTO 検証＋Python 側 `jsonschema` 検証。
- 権限分離: ツールごとにスコープ・API Key。LLM から許可されていないツールは呼ばない。
- プロンプトインジェクション対策: 許可ツールのホワイトリストと引数スキーマの強制。LLM 出力は常に検証。
- タイムアウト/リトライ: ツール呼び出しの外側で統一管理。
- 監査ログ: すべてのツール呼び出しと LLM 出力を追跡（個人情報には注意）。

---

## 実装ステップ（MVP → 強化）
1) 要件確定
   - 必要ツールの一覧と入出力、認証方針、SLA を整理。

2) C# サーバ雛形
   - ASP.NET Core 最小構成、`/tools`（レジストリ）とダミーの `get_weather` を追加。
   - CORS, API Key, OpenAPI を設定。

3) Python クライアント MVP（Ollama）
   - Ollama `/api/chat` で Tool 対応モデルなら `message.tool_calls` を解釈し、標準モデルなら `CALL_SCHEMA` に従う `call_tool` オブジェクトを読んで C# API を呼び出す。
   - 最終回答のみ `format` に JSON Schema（`FINAL_SCHEMA`）を指定して構造化出力を取得。

4) スキーマの厳格化
   - 各ツールの input/output を JSON Schema で公開し、クライアント側でも検証。
   - LLM へのプロンプトにツールごとの schema 抜粋を提示。

5) ツールスキーマの自動化
   - C# DTO から JSON Schema を自動生成（NSwag 等）。`/tools` で配布し、クライアントが取得して LLM に提示。

6) 監視・運用
   - ロギング、メトリクス、レート制限、リトライ戦略の最適化。

---

## リスクと対策
- LLM 出力の JSON 逸脱: 再試行＋生成制御で軽減。
- ツールの引数不足/曖昧さ: `clarify` 分岐とユーザ確認を導入。
- 外部 API 失敗: エラーを `tool_result` として返し、代替案を LLM に促す。
- スキーマの肥大化: ツール毎の最小必須項目に限定、要約版をプロンプト提示。

---

## 次アクション（提案）
- [ ] C#: Minimal API で `/tools` と `get_weather` を作成し、DTO → JSON Schema を公開。
- [ ] Python: Ollama `/api/chat` の Tool Calling を用いたオーケストレーターを実装（上記コード）し、E2E 検証。
- [ ] JSON Schema: ツール input/output のスキーマをレジストリで配布。最終回答の `FINAL_SCHEMA` を要件に合わせ拡張。
- [ ] モデル実行: `ollama pull gemma3:4b`。環境に応じて 12b/27b へスケール。
- [ ] 運用: ログ/メトリクス、リトライ/レート制限、API Key 認証を適用。
