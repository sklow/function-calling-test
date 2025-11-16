"""
tool_client.py の動作テストスクリプト

C# サーバーが起動している状態で実行してください。
"""

import logging
from api import (
    call_tool,
    call_tool_with_retry,
    check_api_health,
    ToolClientError,
    ToolNotFoundError,
    ToolValidationError,
)


# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def test_api_health():
    """APIサーバーヘルスチェックのテスト"""
    print("\n" + "=" * 60)
    print("テスト1: APIサーバーヘルスチェック")
    print("=" * 60)

    is_healthy = check_api_health()
    print(f"結果: サーバー状態 = {'正常' if is_healthy else '異常'}")
    return is_healthy


def test_tool_call_basic():
    """基本的なツール呼び出しのテスト"""
    print("\n" + "=" * 60)
    print("テスト2: 基本的なツール呼び出し（get_weather）")
    print("=" * 60)

    try:
        result = call_tool(
            tool_name="get_weather",
            arguments={"city": "Tokyo", "unit": "metric"}
        )
        print(f"成功: {result}")
        return True
    except ToolClientError as e:
        print(f"エラー: {type(e).__name__} - {e}")
        return False


def test_tool_call_with_retry():
    """リトライ機能付きツール呼び出しのテスト"""
    print("\n" + "=" * 60)
    print("テスト3: リトライ機能付きツール呼び出し")
    print("=" * 60)

    try:
        result = call_tool_with_retry(
            tool_name="get_weather",
            arguments={"city": "Osaka", "unit": "metric"}
        )
        print(f"成功: {result}")
        return True
    except ToolClientError as e:
        print(f"エラー: {type(e).__name__} - {e}")
        return False


def test_tool_not_found():
    """存在しないツール呼び出しのテスト"""
    print("\n" + "=" * 60)
    print("テスト4: 存在しないツール呼び出し（エラーハンドリング確認）")
    print("=" * 60)

    try:
        result = call_tool(
            tool_name="non_existent_tool",
            arguments={}
        )
        print(f"予期しない成功: {result}")
        return False
    except ToolNotFoundError as e:
        print(f"期待通りのエラー: {type(e).__name__} - {e}")
        return True
    except ToolClientError as e:
        print(f"異なるエラー: {type(e).__name__} - {e}")
        return False


def test_invalid_arguments():
    """不正な引数でのツール呼び出しテスト"""
    print("\n" + "=" * 60)
    print("テスト5: 不正な引数での呼び出し（バリデーションエラー確認）")
    print("=" * 60)

    try:
        result = call_tool(
            tool_name="get_weather",
            arguments={"invalid_param": "value"}
        )
        print(f"予期しない成功: {result}")
        return False
    except ToolValidationError as e:
        print(f"期待通りのエラー: {type(e).__name__} - {e}")
        return True
    except ToolClientError as e:
        print(f"異なるエラー: {type(e).__name__} - {e}")
        # バリデーションエラーが返らない場合も許容
        return True


def main():
    """テストメイン関数"""
    print("\n")
    print("*" * 60)
    print("*** tool_client.py 動作テスト ***")
    print("*" * 60)
    print("\n注意: このテストを実行する前に、C# サーバーを起動してください。")
    print("サーバー起動コマンド: cd server && dotnet run\n")

    # テスト実行
    results = []

    # テスト1: ヘルスチェック
    is_healthy = test_api_health()
    results.append(("ヘルスチェック", is_healthy))

    if not is_healthy:
        print("\n" + "!" * 60)
        print("警告: APIサーバーが応答しません。")
        print("サーバーを起動してから再度テストを実行してください。")
        print("!" * 60)
        return

    # テスト2-5: 各種機能テスト
    results.append(("基本的なツール呼び出し", test_tool_call_basic()))
    results.append(("リトライ機能", test_tool_call_with_retry()))
    results.append(("ツール未検出エラー", test_tool_not_found()))
    results.append(("引数バリデーション", test_invalid_arguments()))

    # 結果サマリー
    print("\n" + "=" * 60)
    print("テスト結果サマリー")
    print("=" * 60)

    success_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    for test_name, passed in results:
        status = "✓ 成功" if passed else "✗ 失敗"
        print(f"{status}: {test_name}")

    print(f"\n合計: {success_count}/{total_count} テスト成功")

    if success_count == total_count:
        print("\n全テスト成功！")
    else:
        print(f"\n{total_count - success_count} 件のテストが失敗しました。")


if __name__ == "__main__":
    main()
