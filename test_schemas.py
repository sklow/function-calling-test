"""
Pydantic スキーマモデルの動作確認テストスクリプト

作成した各スキーマモデルが正しく動作することを確認します。
"""

import json
import sys
import os
from pathlib import Path

# UTF-8 出力を有効化（Windows対応）
if sys.platform == "win32":
    os.system("chcp 65001 >nul 2>&1")
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# client モジュールをインポートできるようにパスを追加
sys.path.insert(0, str(Path(__file__).parent / "client"))

from schemas import (
    ToolCall,
    ToolResult,
    FinalAnswer,
    Clarification,
    parse_llm_response,
    get_all_schemas,
    create_response_schema_description,
)


def test_tool_call():
    """ToolCall モデルのテスト"""
    print("=" * 60)
    print("ToolCall モデルのテスト")
    print("=" * 60)

    # 正常なケース
    tool_call = ToolCall(
        tool="get_weather",
        arguments={"city": "Tokyo"},
        content="東京の天気を確認します",
        thought="ユーザーは東京の天気を知りたいようだ"
    )
    print("\n✓ ToolCall インスタンス作成成功:")
    print(json.dumps(tool_call.model_dump(), indent=2, ensure_ascii=False))

    # JSON Schema 取得
    print("\n✓ JSON Schema:")
    schema = tool_call.get_json_schema()
    print(json.dumps(schema, indent=2, ensure_ascii=False))

    # メッセージ形式に変換
    print("\n✓ Ollama メッセージ形式:")
    message = tool_call.to_message()
    print(json.dumps(message, indent=2, ensure_ascii=False))

    print("\n" + "=" * 60)


def test_tool_result():
    """ToolResult モデルのテスト"""
    print("\nToolResult モデルのテスト")
    print("=" * 60)

    # 成功ケース
    result_success = ToolResult(
        tool="get_weather",
        ok=True,
        content="東京の天気: 晴れ、気温25度"
    )
    print("\n✓ ToolResult (成功) インスタンス作成成功:")
    print(json.dumps(result_success.model_dump(), indent=2, ensure_ascii=False))

    # 失敗ケース
    result_failure = ToolResult(
        tool="get_weather",
        ok=False,
        content="天気情報の取得に失敗しました",
        error="API接続エラー: タイムアウト"
    )
    print("\n✓ ToolResult (失敗) インスタンス作成成功:")
    print(json.dumps(result_failure.model_dump(), indent=2, ensure_ascii=False))

    print("\n" + "=" * 60)


def test_final_answer():
    """FinalAnswer モデルのテスト"""
    print("\nFinalAnswer モデルのテスト")
    print("=" * 60)

    answer = FinalAnswer(
        content="東京の今日の天気は晴れで、気温は25度です。過ごしやすい一日になりそうですね。"
    )
    print("\n✓ FinalAnswer インスタンス作成成功:")
    print(json.dumps(answer.model_dump(), indent=2, ensure_ascii=False))

    print("\n" + "=" * 60)


def test_clarification():
    """Clarification モデルのテスト"""
    print("\nClarification モデルのテスト")
    print("=" * 60)

    clarify = Clarification(
        question="どの都市の天気を調べますか?",
        missing_params=["city"]
    )
    print("\n✓ Clarification インスタンス作成成功:")
    print(json.dumps(clarify.model_dump(), indent=2, ensure_ascii=False))

    print("\n" + "=" * 60)


def test_parse_llm_response():
    """parse_llm_response 関数のテスト"""
    print("\nparse_llm_response 関数のテスト")
    print("=" * 60)

    # ToolCall のパース
    json_str = json.dumps({
        "kind": "tool_call",
        "tool": "get_weather",
        "arguments": {"city": "Tokyo"}
    })

    parsed = parse_llm_response(json_str)
    print(f"\n✓ ToolCall パース成功: {type(parsed).__name__}")
    print(json.dumps(parsed.model_dump(), indent=2, ensure_ascii=False))

    # FinalAnswer のパース
    json_str = json.dumps({
        "kind": "final_answer",
        "content": "これが最終回答です"
    })

    parsed = parse_llm_response(json_str)
    print(f"\n✓ FinalAnswer パース成功: {type(parsed).__name__}")
    print(json.dumps(parsed.model_dump(), indent=2, ensure_ascii=False))

    print("\n" + "=" * 60)


def test_get_all_schemas():
    """get_all_schemas 関数のテスト"""
    print("\nget_all_schemas 関数のテスト")
    print("=" * 60)

    schemas = get_all_schemas()
    print(f"\n✓ 取得したスキーマ数: {len(schemas)}")
    for name in schemas.keys():
        print(f"  - {name}")

    print("\n" + "=" * 60)


def test_create_response_schema_description():
    """create_response_schema_description 関数のテスト"""
    print("\ncreate_response_schema_description 関数のテスト")
    print("=" * 60)

    description = create_response_schema_description()
    print("\n✓ レスポンススキーマ説明:")
    print(description)

    print("\n" + "=" * 60)


def test_validation_errors():
    """バリデーションエラーのテスト"""
    print("\nバリデーションエラーのテスト")
    print("=" * 60)

    # ToolCall: 空のツール名
    try:
        ToolCall(tool="", arguments={})
        print("✗ 空のツール名が許可されてしまいました")
    except Exception as e:
        print(f"✓ 空のツール名を正しく拒否: {type(e).__name__}")

    # FinalAnswer: 空のコンテンツ
    try:
        FinalAnswer(content="")
        print("✗ 空のコンテンツが許可されてしまいました")
    except Exception as e:
        print(f"✓ 空のコンテンツを正しく拒否: {type(e).__name__}")

    # 不正な JSON
    try:
        parse_llm_response("invalid json")
        print("✗ 不正な JSON がパースされてしまいました")
    except Exception as e:
        print(f"✓ 不正な JSON を正しく拒否: {type(e).__name__}")

    # 未知の kind
    try:
        parse_llm_response('{"kind": "unknown"}')
        print("✗ 未知の kind が許可されてしまいました")
    except Exception as e:
        print(f"✓ 未知の kind を正しく拒否: {type(e).__name__}")

    print("\n" + "=" * 60)


def main():
    """メインテスト実行"""
    print("\n" + "=" * 60)
    print("Pydantic スキーマモデル 動作確認テスト")
    print("=" * 60)

    try:
        test_tool_call()
        test_tool_result()
        test_final_answer()
        test_clarification()
        test_parse_llm_response()
        test_get_all_schemas()
        test_create_response_schema_description()
        test_validation_errors()

        print("\n" + "=" * 60)
        print("すべてのテストが正常に完了しました!")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ テスト中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
