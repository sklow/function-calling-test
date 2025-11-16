"""
オーケストレーションループのユニットテスト

モック環境でループの各コンポーネントをテストします。
"""

import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from client.orchestrator.loop import (
    build_system_prompt,
    execute_tool,
    safe_parse_json,
    OrchestratorError,
    InvalidResponseFormat,
)
from client.schemas.tool_call import ToolCall, ToolResult


# ============================================================================
# テスト用データ
# ============================================================================

MOCK_TOOLS = [
    {
        "name": "get_weather",
        "description": "指定された都市の天気を取得します",
        "inputSchema": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "都市名"
                },
                "unit": {
                    "type": "string",
                    "description": "温度単位 (metric/imperial)"
                }
            },
            "required": ["city"]
        }
    },
    {
        "name": "calculate",
        "description": "数式を計算します",
        "inputSchema": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "計算式"
                }
            },
            "required": ["expression"]
        }
    }
]


# ============================================================================
# build_system_prompt のテスト
# ============================================================================

def test_build_system_prompt_empty_tools():
    """ツールが空の場合のシステムプロンプト生成"""
    prompt = build_system_prompt([])

    assert "AIアシスタント" in prompt
    assert "レスポンス形式" in prompt
    assert "tool_call" in prompt
    assert "final_answer" in prompt


def test_build_system_prompt_with_tools():
    """ツールが存在する場合のシステムプロンプト生成"""
    prompt = build_system_prompt(MOCK_TOOLS)

    # ツール情報が含まれているか
    assert "get_weather" in prompt
    assert "calculate" in prompt
    assert "指定された都市の天気を取得します" in prompt
    assert "数式を計算します" in prompt

    # パラメータ情報が含まれているか
    assert "city" in prompt
    assert "expression" in prompt


# ============================================================================
# execute_tool のテスト
# ============================================================================

@patch('client.orchestrator.loop.call_tool')
def test_execute_tool_success(mock_call_tool):
    """ツール実行成功のテスト"""
    # モック設定
    mock_call_tool.return_value = {
        "temperature": 25,
        "condition": "晴れ"
    }

    # ツール呼び出し
    tool_call = ToolCall(
        tool="get_weather",
        arguments={"city": "Tokyo"}
    )

    result = execute_tool(tool_call, api_base="http://localhost:5000")

    # 検証
    assert result.ok is True
    assert result.tool == "get_weather"
    assert "temperature" in result.content
    assert mock_call_tool.called


@patch('client.orchestrator.loop.call_tool')
def test_execute_tool_failure(mock_call_tool):
    """ツール実行失敗のテスト"""
    from client.api.tool_client import ToolCallError

    # モック設定（エラーを発生させる）
    mock_call_tool.side_effect = ToolCallError("接続エラー")

    # ツール呼び出し
    tool_call = ToolCall(
        tool="get_weather",
        arguments={"city": "Tokyo"}
    )

    result = execute_tool(tool_call, api_base="http://localhost:5000")

    # 検証（エラー時は ok=False で返る）
    assert result.ok is False
    assert result.tool == "get_weather"
    assert result.error is not None
    assert "接続エラー" in result.error


# ============================================================================
# safe_parse_json のテスト
# ============================================================================

def test_safe_parse_json_valid():
    """正常なJSONのパース"""
    text = '{"kind": "final_answer", "content": "テスト"}'
    result = safe_parse_json(text)

    # パース可能であることを確認
    data = json.loads(result)
    assert data["kind"] == "final_answer"
    assert data["content"] == "テスト"


def test_safe_parse_json_with_code_block():
    """コードブロックマーカー付きJSONのパース"""
    text = '''```json
{
  "kind": "final_answer",
  "content": "テスト"
}
```'''

    result = safe_parse_json(text)
    data = json.loads(result)
    assert data["kind"] == "final_answer"


def test_safe_parse_json_incomplete_braces():
    """閉じ括弧が不足しているJSONの補完"""
    text = '{"kind": "final_answer", "content": "テスト"'

    result = safe_parse_json(text)
    data = json.loads(result)
    assert data["kind"] == "final_answer"
    assert data["content"] == "テスト"


def test_safe_parse_json_invalid():
    """修復不可能なJSONの処理"""
    text = 'this is not json at all'

    try:
        safe_parse_json(text)
        raise AssertionError("ValueErrorが発生すべきでした")
    except ValueError:
        # 期待通りの動作
        pass


# ============================================================================
# メイン実行（pytestなしでも実行可能）
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("オーケストレーションループ ユニットテスト")
    print("=" * 70)
    print()

    # 各テスト関数を手動実行
    tests = [
        ("システムプロンプト生成（空）", test_build_system_prompt_empty_tools),
        ("システムプロンプト生成（ツール有）", test_build_system_prompt_with_tools),
        ("JSON補完（正常）", test_safe_parse_json_valid),
        ("JSON補完（コードブロック）", test_safe_parse_json_with_code_block),
        ("JSON補完（括弧不足）", test_safe_parse_json_incomplete_braces),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            test_func()
            print(f"[OK] {name}")
            passed += 1
        except Exception as e:
            print(f"[NG] {name}: {str(e)}")
            failed += 1

    print()
    print("=" * 70)
    print(f"結果: {passed} 成功, {failed} 失敗")
    print("=" * 70)

    if failed == 0:
        print("すべてのテストが成功しました!")
    else:
        print("一部のテストが失敗しました")
