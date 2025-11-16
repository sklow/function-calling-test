"""
プロンプトビルダーのテストスクリプト

prompt_builder モジュールの動作を確認するためのテストスクリプト
"""

import json
from client.prompts.prompt_builder import (
    PromptBuilder,
    build_system_prompt,
    extract_tool_schema_info,
    format_tools_list
)


# テスト用のツールデータ
TEST_TOOLS = [
    {
        "name": "get_weather",
        "description": "指定した都市の現在の天気情報を取得します",
        "inputSchema": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "都市名（例: Tokyo, New York）"
                },
                "unit": {
                    "type": "string",
                    "description": "温度単位（metric または imperial）",
                    "enum": ["metric", "imperial"]
                }
            },
            "required": ["city"]
        }
    },
    {
        "name": "calculate",
        "description": "数式を評価して計算結果を返します",
        "inputSchema": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "計算式（例: 2 + 2, sqrt(16)）"
                }
            },
            "required": ["expression"]
        }
    },
    {
        "name": "search_web",
        "description": "Web検索を実行してトップ結果を返します",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "検索クエリ"
                },
                "num_results": {
                    "type": "integer",
                    "description": "取得する結果の数（デフォルト: 5）"
                }
            },
            "required": ["query"]
        }
    }
]


def test_extract_tool_schema_info():
    """ツールスキーマ情報の抽出テスト"""
    print("=" * 60)
    print("テスト1: ツールスキーマ情報の抽出")
    print("=" * 60)

    tool = TEST_TOOLS[0]
    info = extract_tool_schema_info(tool)

    print(f"\nツール名: {info['name']}")
    print(f"説明: {info['description']}")
    print(f"必須パラメータ: {info['required_params']}")
    print(f"任意パラメータ: {info['optional_params']}")
    print("\nパラメータ詳細:")
    for param, desc in info['param_descriptions'].items():
        print(f"  - {param}: {desc}")
    print("\n使用例:")
    print(json.dumps(info['example_usage'], ensure_ascii=False, indent=2))


def test_format_tools_list():
    """ツール一覧のフォーマットテスト"""
    print("\n" + "=" * 60)
    print("テスト2: ツール一覧のフォーマット（詳細版）")
    print("=" * 60)

    formatted = format_tools_list(TEST_TOOLS, format_style='detailed', language='ja')
    print(formatted)

    print("\n" + "=" * 60)
    print("テスト3: ツール一覧のフォーマット（簡潔版）")
    print("=" * 60)

    formatted = format_tools_list(TEST_TOOLS, format_style='concise', language='ja')
    print(formatted)


def test_build_system_prompt_standard():
    """標準テンプレートでのプロンプト構築テスト"""
    print("\n" + "=" * 60)
    print("テスト4: システムプロンプト構築（標準テンプレート）")
    print("=" * 60)

    prompt = build_system_prompt(TEST_TOOLS)
    print(f"\nプロンプト長: {len(prompt)} 文字")
    print("\n--- プロンプト内容 ---")
    print(prompt[:500])  # 最初の500文字のみ表示
    print("...")
    print(prompt[-300:])  # 最後の300文字のみ表示


def test_prompt_builder_class():
    """PromptBuilder クラスのテスト"""
    print("\n" + "=" * 60)
    print("テスト5: PromptBuilder クラス（簡潔版テンプレート）")
    print("=" * 60)

    builder = PromptBuilder()
    prompt = builder.build_system_prompt(
        tools=TEST_TOOLS,
        language='ja',
        template_name='concise',
        format_style='concise'
    )

    print(f"\nプロンプト長: {len(prompt)} 文字")
    print("\n--- プロンプト内容 ---")
    print(prompt)


def test_custom_instructions():
    """カスタム指示の追加テスト"""
    print("\n" + "=" * 60)
    print("テスト6: カスタム指示の追加")
    print("=" * 60)

    builder = PromptBuilder()
    custom = "ユーザーには丁寧な敬語で回答してください。回答は箇条書きで簡潔にまとめてください。"

    prompt = builder.build_system_prompt(
        tools=TEST_TOOLS,
        language='ja',
        template_name='standard',
        custom_instructions=custom
    )

    print(f"\nプロンプト長: {len(prompt)} 文字")
    print("\n--- プロンプト末尾（カスタム指示部分） ---")
    print(prompt[-400:])


def test_detailed_template():
    """詳細版テンプレートのテスト"""
    print("\n" + "=" * 60)
    print("テスト7: 詳細版テンプレート")
    print("=" * 60)

    builder = PromptBuilder()
    prompt = builder.build_system_prompt(
        tools=TEST_TOOLS,
        language='ja',
        template_name='detailed',
        format_style='detailed'
    )

    print(f"\nプロンプト長: {len(prompt)} 文字")
    print("\n--- プロンプト構造 ---")
    # セクション見出しを抽出
    lines = prompt.split('\n')
    headers = [line for line in lines if line.startswith('#')]
    for header in headers[:10]:  # 最初の10個の見出し
        print(header)


def test_debug_template():
    """デバッグ版テンプレートのテスト"""
    print("\n" + "=" * 60)
    print("テスト8: デバッグ版テンプレート")
    print("=" * 60)

    builder = PromptBuilder()
    prompt = builder.build_system_prompt(
        tools=TEST_TOOLS,
        language='ja',
        template_name='debug',
        format_style='detailed'
    )

    print(f"\nプロンプト長: {len(prompt)} 文字")
    print("\n--- デバッグテンプレート内容（抜粋） ---")
    print(prompt[:600])


def main():
    """メインテスト実行"""
    print("\n")
    print("*" * 60)
    print("* プロンプトビルダーテスト")
    print("*" * 60)

    try:
        test_extract_tool_schema_info()
        test_format_tools_list()
        test_build_system_prompt_standard()
        test_prompt_builder_class()
        test_custom_instructions()
        test_detailed_template()
        test_debug_template()

        print("\n" + "=" * 60)
        print("全テスト完了")
        print("=" * 60)

    except Exception as e:
        print(f"\nエラーが発生しました: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
