"""
オーケストレーションループのデモスクリプト

実際のサーバーなしでループの基本動作を確認するためのデモです。
"""

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from client.orchestrator.loop import (
    build_system_prompt,
    safe_parse_json,
    CALL_SCHEMA
)


def main():
    """メイン関数"""
    print("=" * 70)
    print("オーケストレーションループ デモ")
    print("=" * 70)
    print()

    # テスト1: システムプロンプトの生成
    print("=" * 70)
    print("テスト1: システムプロンプトの生成")
    print("=" * 70)
    print()

    mock_tools = [
        {
            "name": "get_weather",
            "description": "指定された都市の天気情報を取得します",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "都市名（例: Tokyo, New York）"
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
            "description": "数式を計算して結果を返します",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "計算式（例: 2 + 2, 10 * 5）"
                    }
                },
                "required": ["expression"]
            }
        }
    ]

    system_prompt = build_system_prompt(mock_tools)

    print("システムプロンプトの一部:")
    print("-" * 70)
    print(system_prompt[:500] + "...")
    print("-" * 70)
    print(f"システムプロンプト長: {len(system_prompt)} 文字")
    print()

    # テスト2: JSON Schema の確認
    print("=" * 70)
    print("テスト2: JSON Schema の確認")
    print("=" * 70)
    print()

    import json
    print("CALL_SCHEMA:")
    print("-" * 70)
    print(json.dumps(CALL_SCHEMA, indent=2, ensure_ascii=False))
    print("-" * 70)
    print()

    # テスト3: JSON補完機能のテスト
    print("=" * 70)
    print("テスト3: JSON補完機能のテスト")
    print("=" * 70)
    print()

    test_cases = [
        ('正常なJSON', '{"kind": "final_answer", "content": "テスト"}'),
        ('コードブロック付き', '```json\n{"kind": "final_answer", "content": "テスト"}\n```'),
        ('括弧不足', '{"kind": "final_answer", "content": "テスト"'),
    ]

    for name, test_json in test_cases:
        print(f"ケース: {name}")
        print(f"入力: {test_json[:50]}...")
        try:
            result = safe_parse_json(test_json)
            parsed = json.loads(result)
            print(f"結果: 成功 - {parsed}")
        except Exception as e:
            print(f"結果: 失敗 - {str(e)}")
        print()

    # 完了メッセージ
    print("=" * 70)
    print("デモ完了")
    print("=" * 70)
    print()
    print("注意:")
    print("- 実際のオーケストレーションループを実行するには、以下が必要です:")
    print("  1. Ollama サーバーの起動 (http://localhost:11434)")
    print("  2. C# API サーバーの起動 (http://localhost:5000)")
    print("  3. Gemma 3 モデルのインストール (ollama pull gemma3:4b)")
    print()


if __name__ == "__main__":
    main()
