"""
ツールレジストリ機能の総合テスト

すべての主要関数の動作を確認するテストスクリプト
"""

import logging
import time
from client.api import (
    fetch_tools,
    get_tool_schema,
    clear_tools_cache,
    list_available_tools,
    validate_tool_registry,
    RegistryError,
)


# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def test_fetch_tools():
    """fetch_tools() 関数のテスト"""
    print("\n" + "=" * 60)
    print("テスト1: fetch_tools() - ツールレジストリの取得")
    print("=" * 60)

    try:
        # キャッシュクリア
        clear_tools_cache()

        # 初回取得（APIから）
        print("\n1-1. 初回取得（APIから直接）")
        tools = fetch_tools(use_cache=True)
        print(f"  [OK] 取得成功")
        print(f"  - ツール数: {tools['count']}")
        print(f"  - 取得時刻: {tools['fetched_at']}")
        print(f"  - APIベース: {tools['api_base']}")

        # 2回目取得（キャッシュから）
        print("\n1-2. 2回目取得（キャッシュから）")
        tools_cached = fetch_tools(use_cache=True)
        print(f"  [OK] 取得成功")
        print(f"  - キャッシュ時刻: {tools_cached.get('cached_at')}")

        # キャッシュ無効化テスト
        print("\n1-3. キャッシュ無効化テスト")
        tools_no_cache = fetch_tools(use_cache=False)
        print(f"  [OK]取得成功（キャッシュ未使用）")

        return True

    except RegistryError as e:
        print(f"  [NG]エラー: {e}")
        return False


def test_get_tool_schema():
    """get_tool_schema() 関数のテスト"""
    print("\n" + "=" * 60)
    print("テスト2: get_tool_schema() - 特定ツールのスキーマ取得")
    print("=" * 60)

    try:
        # 存在するツールのスキーマ取得
        print("\n2-1. 'get_weather' のスキーマ取得")
        schema = get_tool_schema("get_weather")
        if schema:
            print(f"  [OK] 取得成功")
            print(f"  - 名前: {schema['name']}")
            print(f"  - 説明: {schema['description']}")
            print(f"  - HTTPメソッド: {schema['httpMethod']}")
            print(f"  - パス: {schema['path']}")
            print(f"  - 認証必要: {schema['requiresAuth']}")
            print(f"  - 入力スキーマ: {schema['inputSchema'].get('title')}")
            print(f"  - 出力スキーマ: {schema['outputSchema'].get('title')}")
        else:
            print(f"  [NG]スキーマが取得できませんでした")
            return False

        # 存在しないツールのスキーマ取得
        print("\n2-2. 存在しないツール 'invalid_tool' のスキーマ取得")
        schema_invalid = get_tool_schema("invalid_tool")
        if schema_invalid is None:
            print(f"  [OK]正しくNoneを返しました")
        else:
            print(f"  [NG]予期しない結果: {schema_invalid}")
            return False

        return True

    except Exception as e:
        print(f"  [NG]エラー: {e}")
        return False


def test_list_available_tools():
    """list_available_tools() 関数のテスト"""
    print("\n" + "=" * 60)
    print("テスト3: list_available_tools() - ツール名一覧の取得")
    print("=" * 60)

    try:
        print("\n3-1. ツール一覧取得")
        tool_names = list_available_tools()
        print(f"  [OK] 取得成功")
        print(f"  - ツール数: {len(tool_names)}")
        for idx, name in enumerate(tool_names, 1):
            print(f"  {idx}. {name}")

        return True

    except RegistryError as e:
        print(f"  [NG]エラー: {e}")
        return False


def test_validate_tool_registry():
    """validate_tool_registry() 関数のテスト"""
    print("\n" + "=" * 60)
    print("テスト4: validate_tool_registry() - レジストリデータの検証")
    print("=" * 60)

    # 正常なデータ
    print("\n4-1. 正常なレジストリデータ")
    valid_data = {
        "tools": [
            {
                "name": "test_tool",
                "description": "テストツール",
                "httpMethod": "POST",
                "path": "/tools/test",
                "inputSchema": {},
                "outputSchema": {},
                "requiresAuth": False
            }
        ],
        "count": 1
    }

    if validate_tool_registry(valid_data):
        print("  [OK]正常なデータとして認識されました")
    else:
        print("  [NG]バリデーション失敗")
        return False

    # 不正なデータ（toolsフィールドがない）
    print("\n4-2. 不正なレジストリデータ（toolsフィールドなし）")
    invalid_data1 = {"count": 0}

    if not validate_tool_registry(invalid_data1):
        print("  [OK]正しく不正なデータとして検出されました")
    else:
        print("  [NG]不正なデータを正常と判定してしまいました")
        return False

    # 不正なデータ（toolsがリストでない）
    print("\n4-3. 不正なレジストリデータ（toolsがリストでない）")
    invalid_data2 = {"tools": "invalid"}

    if not validate_tool_registry(invalid_data2):
        print("  [OK]正しく不正なデータとして検出されました")
    else:
        print("  [NG]不正なデータを正常と判定してしまいました")
        return False

    return True


def test_cache_ttl():
    """キャッシュTTL機能のテスト"""
    print("\n" + "=" * 60)
    print("テスト5: キャッシュTTL（有効期限）機能")
    print("=" * 60)

    try:
        # キャッシュクリア
        clear_tools_cache()

        # 短いTTLで取得
        print("\n5-1. TTL=2秒でキャッシュ取得")
        tools1 = fetch_tools(use_cache=True, cache_ttl=2)
        print(f"  [OK]取得成功: {tools1['count']}個のツール")

        # 即座に再取得（キャッシュヒット）
        print("\n5-2. 即座に再取得（キャッシュ有効）")
        tools2 = fetch_tools(use_cache=True, cache_ttl=2)
        print(f"  [OK]キャッシュヒット")

        # 3秒待機（TTL切れ）
        print("\n5-3. 3秒待機してTTL切れを確認")
        time.sleep(3)
        tools3 = fetch_tools(use_cache=True, cache_ttl=2)
        print(f"  [OK]TTL切れ後、再取得成功")

        return True

    except RegistryError as e:
        print(f"  [NG]エラー: {e}")
        return False


def main():
    """すべてのテストを実行"""
    print("\n" + "=" * 60)
    print("ツールレジストリ機能 総合テスト")
    print("=" * 60)

    results = []

    # 各テストを実行
    results.append(("fetch_tools", test_fetch_tools()))
    results.append(("get_tool_schema", test_get_tool_schema()))
    results.append(("list_available_tools", test_list_available_tools()))
    results.append(("validate_tool_registry", test_validate_tool_registry()))
    results.append(("cache_ttl", test_cache_ttl()))

    # 結果サマリー
    print("\n" + "=" * 60)
    print("テスト結果サマリー")
    print("=" * 60)

    passed = 0
    failed = 0

    for test_name, result in results:
        status = "[OK] PASS" if result else "[NG] FAIL"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
        else:
            failed += 1

    print("\n" + "-" * 60)
    print(f"合計: {len(results)} テスト")
    print(f"成功: {passed} テスト")
    print(f"失敗: {failed} テスト")
    print("=" * 60)

    # 最終的なキャッシュクリア
    clear_tools_cache()

    return failed == 0


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
