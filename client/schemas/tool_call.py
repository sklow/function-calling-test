"""
ツール呼び出しスキーマ

LLM とのやり取りで使用するデータスキーマを定義
- ツール呼び出しリクエスト/レスポンス
- 最終回答
- 確認・質問
- JSON Schema 生成
"""

from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field, field_validator, model_validator
import json


class ToolCall(BaseModel):
    """
    LLM がツールを呼び出す際のリクエスト

    LLM がユーザーのリクエストを満たすために外部ツールを呼び出す必要がある場合、
    この形式でツール呼び出しを指示します。

    使用例:
        tool_call = ToolCall(
            tool="get_weather",
            arguments={"city": "Tokyo"},
            content="東京の天気を確認します",
            thought="ユーザーは東京の天気を知りたいようだ"
        )
    """
    kind: Literal["tool_call"] = Field(
        default="tool_call",
        description="レスポンスタイプ識別子"
    )
    tool: str = Field(
        ...,
        description="呼び出すツール名（例: get_weather, search_web）",
        min_length=1
    )
    arguments: Dict[str, Any] = Field(
        ...,
        description="ツールに渡す引数の辞書"
    )
    content: Optional[str] = Field(
        None,
        description="ユーザーへの説明メッセージ（任意）"
    )
    thought: Optional[str] = Field(
        None,
        description="LLM の思考過程・推論内容（デバッグ用、任意）"
    )

    @field_validator('tool')
    @classmethod
    def validate_tool_name(cls, v: str) -> str:
        """
        ツール名の妥当性をチェック

        Args:
            v: ツール名

        Returns:
            検証済みのツール名

        Raises:
            ValueError: ツール名が空文字列の場合
        """
        if not v.strip():
            raise ValueError("ツール名は空にできません")
        return v.strip()

    @field_validator('arguments')
    @classmethod
    def validate_arguments(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """
        arguments の妥当性をチェック

        Args:
            v: 引数の辞書

        Returns:
            検証済みの引数辞書
        """
        # arguments は辞書である必要がある（Pydantic が保証）
        # 追加のカスタムバリデーションがあればここに記述
        return v

    def to_message(self) -> Dict[str, str]:
        """
        Ollama のメッセージ形式に変換

        Returns:
            Ollama API で使用可能なメッセージ辞書
        """
        message = {
            "role": "assistant",
            "content": json.dumps(self.model_dump(), ensure_ascii=False)
        }
        return message

    @classmethod
    def get_json_schema(cls) -> Dict[str, Any]:
        """
        このモデルの JSON Schema を取得

        Returns:
            JSON Schema 辞書
        """
        return cls.model_json_schema()


class ToolResult(BaseModel):
    """
    ツール実行結果を LLM に返す際のレスポンス

    クライアント側でツールを実行した後、その結果を LLM にフィードバックする際に使用。
    成功時は ok=True、失敗時は ok=False と error 情報を含めます。

    使用例:
        # 成功時
        result = ToolResult(
            tool="get_weather",
            ok=True,
            content="東京の天気: 晴れ、気温25度"
        )

        # 失敗時
        result = ToolResult(
            tool="get_weather",
            ok=False,
            content="天気情報の取得に失敗しました",
            error="API接続エラー: タイムアウト"
        )
    """
    kind: Literal["tool_result"] = Field(
        default="tool_result",
        description="レスポンスタイプ識別子"
    )
    tool: str = Field(
        ...,
        description="実行されたツール名",
        min_length=1
    )
    ok: bool = Field(
        ...,
        description="実行成功フラグ（True: 成功, False: 失敗）"
    )
    content: Optional[str] = Field(
        None,
        description="結果の内容またはエラーメッセージ"
    )
    error: Optional[str] = Field(
        None,
        description="詳細なエラー情報（失敗時のスタックトレースなど）"
    )

    @model_validator(mode='after')
    def validate_tool_result(self) -> 'ToolResult':
        """
        tool_result の一貫性をチェック

        ok=False の場合は error フィールドの設定を推奨

        Returns:
            検証済みの ToolResult インスタンス
        """
        if not self.ok and not self.error:
            # 警告: 失敗時は error フィールドを設定することを推奨
            # ただし、厳密にエラーとはしない（柔軟性のため）
            pass
        return self

    def to_message(self) -> Dict[str, str]:
        """
        Ollama のメッセージ形式に変換

        Returns:
            Ollama API で使用可能なメッセージ辞書
        """
        message = {
            "role": "user",
            "content": json.dumps(self.model_dump(), ensure_ascii=False)
        }
        return message

    @classmethod
    def get_json_schema(cls) -> Dict[str, Any]:
        """
        このモデルの JSON Schema を取得

        Returns:
            JSON Schema 辞書
        """
        return cls.model_json_schema()


class FinalAnswer(BaseModel):
    """
    LLM からの最終回答

    すべてのツール呼び出しが完了し、ユーザーのリクエストに対する
    最終的な回答を返す際に使用します。

    使用例:
        answer = FinalAnswer(
            content="東京の今日の天気は晴れで、気温は25度です。過ごしやすい一日になりそうですね。"
        )
    """
    kind: Literal["final_answer"] = Field(
        default="final_answer",
        description="レスポンスタイプ識別子"
    )
    content: str = Field(
        ...,
        description="ユーザーへの回答内容",
        min_length=1
    )

    @field_validator('content')
    @classmethod
    def validate_content(cls, v: str) -> str:
        """
        content の妥当性をチェック

        Args:
            v: 回答内容

        Returns:
            検証済みの回答内容

        Raises:
            ValueError: 回答内容が空の場合
        """
        if not v.strip():
            raise ValueError("回答内容は空にできません")
        return v.strip()

    def to_message(self) -> Dict[str, str]:
        """
        Ollama のメッセージ形式に変換

        Returns:
            Ollama API で使用可能なメッセージ辞書
        """
        message = {
            "role": "assistant",
            "content": json.dumps(self.model_dump(), ensure_ascii=False)
        }
        return message

    @classmethod
    def get_json_schema(cls) -> Dict[str, Any]:
        """
        このモデルの JSON Schema を取得

        Returns:
            JSON Schema 辞書
        """
        return cls.model_json_schema()


class Clarification(BaseModel):
    """
    LLM が追加情報を求める場合

    ユーザーのリクエストが不明確だったり、必要なパラメータが不足している場合に
    LLM が追加情報を求める際に使用します。

    使用例:
        clarify = Clarification(
            question="どの都市の天気を調べますか？",
            missing_params=["city"]
        )
    """
    kind: Literal["clarify"] = Field(
        default="clarify",
        description="レスポンスタイプ識別子"
    )
    question: str = Field(
        ...,
        description="ユーザーへの質問内容",
        min_length=1
    )
    missing_params: List[str] = Field(
        default_factory=list,
        description="不足しているパラメータのリスト"
    )

    @field_validator('question')
    @classmethod
    def validate_question(cls, v: str) -> str:
        """
        question の妥当性をチェック

        Args:
            v: 質問内容

        Returns:
            検証済みの質問内容

        Raises:
            ValueError: 質問内容が空の場合
        """
        if not v.strip():
            raise ValueError("質問内容は空にできません")
        return v.strip()

    def to_message(self) -> Dict[str, str]:
        """
        Ollama のメッセージ形式に変換

        Returns:
            Ollama API で使用可能なメッセージ辞書
        """
        message = {
            "role": "assistant",
            "content": json.dumps(self.model_dump(), ensure_ascii=False)
        }
        return message

    @classmethod
    def get_json_schema(cls) -> Dict[str, Any]:
        """
        このモデルの JSON Schema を取得

        Returns:
            JSON Schema 辞書
        """
        return cls.model_json_schema()


# レスポンスタイプの Union 型
ResponseType = Union[ToolCall, ToolResult, FinalAnswer, Clarification]


def parse_llm_response(response_text: str) -> ResponseType:
    """
    LLM のレスポンステキストからモデルをパース

    LLM から返された JSON 文字列を適切な Pydantic モデルにパースします。
    kind フィールドを見て適切なモデルクラスを選択します。

    Args:
        response_text: LLM からの JSON レスポンステキスト

    Returns:
        パースされた ResponseType モデル

    Raises:
        ValueError: JSON のパースに失敗した場合
        ValueError: 未知の kind 値の場合

    使用例:
        response = parse_llm_response('{"kind": "tool_call", "tool": "get_weather", "arguments": {"city": "Tokyo"}}')
        if isinstance(response, ToolCall):
            print(f"ツール {response.tool} を呼び出します")
    """
    try:
        data = json.loads(response_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON のパースに失敗しました: {e}")

    kind = data.get("kind")

    if kind == "tool_call":
        return ToolCall.model_validate(data)
    elif kind == "tool_result":
        return ToolResult.model_validate(data)
    elif kind == "final_answer":
        return FinalAnswer.model_validate(data)
    elif kind == "clarify":
        return Clarification.model_validate(data)
    else:
        raise ValueError(f"未知の kind 値です: {kind}")


def get_all_schemas() -> Dict[str, Dict[str, Any]]:
    """
    すべてのレスポンスタイプの JSON Schema を取得

    LLM にツール呼び出しの形式を教える際に使用します。

    Returns:
        各レスポンスタイプの JSON Schema を含む辞書

    使用例:
        schemas = get_all_schemas()
        print(json.dumps(schemas, indent=2, ensure_ascii=False))
    """
    return {
        "ToolCall": ToolCall.get_json_schema(),
        "ToolResult": ToolResult.get_json_schema(),
        "FinalAnswer": FinalAnswer.get_json_schema(),
        "Clarification": Clarification.get_json_schema(),
    }


def create_response_schema_description() -> str:
    """
    LLM 向けのレスポンススキーマ説明を生成

    システムプロンプトに含めるための、レスポンス形式の説明文を生成します。

    Returns:
        レスポンススキーマの説明テキスト
    """
    description = """
# レスポンス形式

あなたのレスポンスは必ず以下のいずれかの JSON 形式で返してください：

## 1. ツール呼び出し (tool_call)
ツールを使用する必要がある場合:
```json
{
  "kind": "tool_call",
  "tool": "ツール名",
  "arguments": {"パラメータ名": "値"},
  "content": "ユーザーへの説明（任意）",
  "thought": "思考過程（任意）"
}
```

## 2. 最終回答 (final_answer)
ユーザーへの最終的な回答:
```json
{
  "kind": "final_answer",
  "content": "回答内容"
}
```

## 3. 確認質問 (clarify)
追加情報が必要な場合:
```json
{
  "kind": "clarify",
  "question": "質問内容",
  "missing_params": ["不足しているパラメータ"]
}
```

## 4. ツール結果 (tool_result)
※これはシステムが返す形式です。あなたが使用する必要はありません。
```json
{
  "kind": "tool_result",
  "tool": "ツール名",
  "ok": true/false,
  "content": "結果内容",
  "error": "エラー情報（任意）"
}
```
"""
    return description.strip()


# モジュールの公開インターフェース
__all__ = [
    "ToolCall",
    "ToolResult",
    "FinalAnswer",
    "Clarification",
    "ResponseType",
    "parse_llm_response",
    "get_all_schemas",
    "create_response_schema_description",
]
