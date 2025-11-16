"""
オーケストレーションループのテストスクリプト

実際のOllamaとC# APIサーバーに接続してループの動作を確認します。
"""

import logging
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from client.orchestrator.loop import run_loop, OrchestratorError


# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def main():
    """メイン関数"""
    print("=" * 70)
    print("オーケストレーションループ テスト")
    print("=" * 70)
    print()

    # テストクエリ
    test_queries = [
        "こんにちは",
        "東京の天気は?",
        "2 + 2 は何ですか?",
    ]

    for idx, query in enumerate(test_queries, 1):
        print(f"\n{'=' * 70}")
        print(f"テスト {idx}/{len(test_queries)}: {query}")
        print("=" * 70)

        try:
            # オーケストレーションループの実行
            answer = run_loop(
                user_query=query,
                model="gemma3:4b",
                api_base="http://localhost:5000",
                ollama_host="http://localhost:11434",
                max_iterations=5,
                timeout=30
            )

            # 結果表示
            print()
            print("【最終回答】")
            print(answer)
            print()

        except OrchestratorError as e:
            print()
            print("【エラー】")
            print(f"オーケストレーションエラー: {e}")
            print()

        except KeyboardInterrupt:
            print()
            print("テストを中断しました")
            break

        except Exception as e:
            print()
            print("【予期しないエラー】")
            print(f"エラータイプ: {type(e).__name__}")
            print(f"エラーメッセージ: {str(e)}")
            print()

    print("=" * 70)
    print("テスト完了")
    print("=" * 70)


if __name__ == "__main__":
    main()
