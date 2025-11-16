"""
ツールレジストリ管理モジュール

C# サーバから /tools エンドポイントを通じてツール一覧を取得し、
ローカルキャッシュで管理する機能を提供します。

主要機能:
- ツールレジストリの取得とキャッシュ
- 特定ツールのスキーマ情報取得
- キャッシュ管理（TTL、クリア）
- エラーハンドリングとロギング
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List
from typing_extensions import TypedDict

import requests


# ログ設定
logger = logging.getLogger(__name__)


# ============================================================================
# 定数定義
# ============================================================================

# キャッシュディレクトリとファイル
CACHE_DIR = Path(__file__).parent.parent / ".cache"
CACHE_FILE = CACHE_DIR / "tools_cache.json"

# デフォルト設定
DEFAULT_API_BASE = "http://localhost:5000"
DEFAULT_TIMEOUT = 10
DEFAULT_CACHE_TTL = 300  # 5分


# ============================================================================
# 型定義
# ============================================================================

class ToolMetadata(TypedDict):
    """ツールメタデータの型定義"""
    name: str
    description: str
    httpMethod: str
    path: str
    inputSchema: Dict[str, Any]
    outputSchema: Dict[str, Any]
    requiresAuth: bool


# ============================================================================
# カスタム例外クラス
# ============================================================================

class RegistryError(Exception):
    """ツールレジストリのベース例外"""
    pass


class RegistryTimeoutError(RegistryError):
    """レジストリ取得のタイムアウト"""
    pass


class RegistryConnectionError(RegistryError):
    """レジストリサーバーへの接続エラー"""
    pass


class RegistryParseError(RegistryError):
    """レジストリレスポンスのパースエラー"""
    pass


# ============================================================================
# キャッシュ管理クラス
# ============================================================================

class ToolsCache:
    """ツールレジストリのローカルキャッシュ管理"""

    def __init__(self, cache_file: Path = CACHE_FILE):
        """
        キャッシュマネージャーの初期化

        Args:
            cache_file: キャッシュファイルのパス
        """
        self.cache_file = cache_file
        self.cache_dir = cache_file.parent

    def save(self, data: Dict[str, Any]) -> None:
        """
        キャッシュにデータを保存

        Args:
            data: 保存するデータ
        """
        try:
            # キャッシュディレクトリが存在しない場合は作成
            self.cache_dir.mkdir(parents=True, exist_ok=True)

            # 現在のタイムスタンプを追加
            cache_data = {
                **data,
                "cached_at": datetime.now(timezone.utc).isoformat()
            }

            # JSONファイルに書き込み
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)

            logger.debug(f"キャッシュ保存完了: {self.cache_file}")

        except IOError as e:
            logger.error(f"キャッシュ保存エラー: {e}")
            # キャッシュ保存失敗は致命的エラーではないため例外は再送出しない

    def load(self) -> Optional[Dict[str, Any]]:
        """
        キャッシュからデータを読み込み

        Returns:
            キャッシュされたデータ、またはNone（キャッシュが存在しない場合）
        """
        try:
            if not self.cache_file.exists():
                logger.debug("キャッシュファイルが存在しません")
                return None

            with open(self.cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            logger.debug(f"キャッシュ読み込み完了: {self.cache_file}")
            return data

        except (IOError, json.JSONDecodeError) as e:
            logger.warning(f"キャッシュ読み込みエラー: {e}")
            return None

    def is_expired(self, ttl: int = DEFAULT_CACHE_TTL) -> bool:
        """
        キャッシュが期限切れかチェック

        Args:
            ttl: キャッシュの有効期限（秒）

        Returns:
            期限切れの場合はTrue、有効な場合はFalse
        """
        data = self.load()
        if data is None:
            return True

        cached_at_str = data.get("cached_at")
        if not cached_at_str:
            logger.warning("キャッシュにタイムスタンプがありません")
            return True

        try:
            cached_at = datetime.fromisoformat(cached_at_str)
            now = datetime.now(timezone.utc)
            elapsed_seconds = (now - cached_at).total_seconds()

            is_expired = elapsed_seconds > ttl
            logger.debug(
                f"キャッシュ期限チェック: 経過時間={elapsed_seconds:.1f}秒, "
                f"TTL={ttl}秒, 期限切れ={is_expired}"
            )
            return is_expired

        except ValueError as e:
            logger.warning(f"タイムスタンプ解析エラー: {e}")
            return True

    def clear(self) -> None:
        """キャッシュファイルを削除"""
        try:
            if self.cache_file.exists():
                self.cache_file.unlink()
                logger.info(f"キャッシュクリア完了: {self.cache_file}")
            else:
                logger.debug("削除するキャッシュファイルが存在しません")

        except IOError as e:
            logger.error(f"キャッシュクリアエラー: {e}")


# ============================================================================
# 主要関数
# ============================================================================

def fetch_tools(
    api_base: str = DEFAULT_API_BASE,
    timeout: int = DEFAULT_TIMEOUT,
    use_cache: bool = True,
    cache_ttl: int = DEFAULT_CACHE_TTL
) -> Dict[str, Any]:
    """
    C# サーバから利用可能なツール一覧を取得

    Args:
        api_base: APIサーバーのベースURL
        timeout: タイムアウト秒数
        use_cache: キャッシュを使用するかどうか
        cache_ttl: キャッシュの有効期限（秒）

    Returns:
        ツール一覧の辞書
        {
            "tools": [ToolMetadata, ...],
            "count": int,
            "fetched_at": datetime,
            "api_base": str
        }

    Raises:
        RegistryError: レジストリ取得エラー
        RegistryTimeoutError: タイムアウト
        RegistryConnectionError: 接続エラー
        RegistryParseError: パースエラー
    """
    cache = ToolsCache()

    # キャッシュ使用時の処理
    if use_cache:
        cached_data = cache.load()
        if cached_data and not cache.is_expired(cache_ttl):
            # 同じAPIベースの場合のみキャッシュを使用
            if cached_data.get("api_base") == api_base:
                logger.info(
                    f"キャッシュヒット: {cached_data['count']}個のツールを取得"
                )
                return cached_data
            else:
                logger.debug(
                    f"APIベースが異なるためキャッシュを使用しません: "
                    f"キャッシュ={cached_data.get('api_base')}, 要求={api_base}"
                )
        else:
            logger.debug("キャッシュミスまたは期限切れ")

    # レジストリ取得開始
    url = f"{api_base}/tools"
    logger.info(f"ツールレジストリ取得開始: {url}")

    try:
        # HTTP GETリクエスト送信
        response = requests.get(url, timeout=timeout)

        # レスポンス受信ログ
        logger.debug(f"レスポンス受信: ステータスコード={response.status_code}")

        # ステータスコードチェック
        if response.status_code != 200:
            error_msg = f"レジストリ取得失敗: HTTPステータス {response.status_code}"
            logger.error(error_msg)
            raise RegistryError(error_msg)

        # JSONパース
        try:
            registry_data = response.json()
        except json.JSONDecodeError as e:
            logger.error(f"JSONパースエラー: {e}")
            raise RegistryParseError(
                f"レジストリレスポンスのJSON解析に失敗しました: {e}"
            ) from e

        # レスポンス構造の検証
        if not validate_tool_registry(registry_data):
            raise RegistryParseError("レジストリデータの形式が不正です")

        # 取得成功
        tools_count = registry_data.get("count", 0)
        logger.info(f"ツールレジストリ取得成功: {tools_count}個のツール")

        # 結果データ構築
        result = {
            "tools": registry_data.get("tools", []),
            "count": tools_count,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "api_base": api_base
        }

        # キャッシュに保存
        if use_cache:
            cache.save(result)

        return result

    except requests.Timeout as e:
        error_msg = f"レジストリ取得タイムアウト: {timeout}秒"
        logger.error(error_msg)
        raise RegistryTimeoutError(error_msg) from e

    except requests.ConnectionError as e:
        error_msg = f"レジストリサーバーへの接続エラー: {api_base}"
        logger.error(error_msg)
        raise RegistryConnectionError(error_msg) from e

    except requests.RequestException as e:
        error_msg = f"レジストリ取得リクエストエラー: {str(e)}"
        logger.error(error_msg)
        raise RegistryError(error_msg) from e


def get_tool_schema(
    tool_name: str,
    api_base: str = DEFAULT_API_BASE
) -> Optional[Dict[str, Any]]:
    """
    指定されたツールのスキーマ情報を取得

    Args:
        tool_name: ツール名
        api_base: APIサーバーのベースURL

    Returns:
        ツールのスキーマ情報またはNone（見つからない場合）
    """
    try:
        # ツールレジストリを取得（キャッシュ使用）
        registry = fetch_tools(api_base=api_base, use_cache=True)
        tools = registry.get("tools", [])

        # 指定されたツールを検索
        for tool in tools:
            if tool.get("name") == tool_name:
                logger.info(f"ツールスキーマ取得成功: {tool_name}")
                return tool

        logger.warning(f"ツールが見つかりません: {tool_name}")
        return None

    except RegistryError as e:
        logger.error(f"ツールスキーマ取得エラー: {e}")
        return None


def clear_tools_cache() -> None:
    """ツールキャッシュをクリア"""
    cache = ToolsCache()
    cache.clear()


# ============================================================================
# 補助関数
# ============================================================================

def list_available_tools(api_base: str = DEFAULT_API_BASE) -> List[str]:
    """
    利用可能なツール名の一覧を取得

    Args:
        api_base: APIサーバーのベースURL

    Returns:
        ツール名のリスト

    Raises:
        RegistryError: レジストリ取得エラー
    """
    try:
        registry = fetch_tools(api_base=api_base, use_cache=True)
        tools = registry.get("tools", [])
        tool_names = [tool.get("name") for tool in tools if tool.get("name")]

        logger.info(f"利用可能なツール数: {len(tool_names)}")
        return tool_names

    except RegistryError as e:
        logger.error(f"ツール一覧取得エラー: {e}")
        raise


def validate_tool_registry(registry_data: Dict[str, Any]) -> bool:
    """
    レジストリデータの妥当性をチェック

    Args:
        registry_data: 検証対象のレジストリデータ

    Returns:
        妥当な場合はTrue、不正な場合はFalse
    """
    # 必須フィールドのチェック
    if not isinstance(registry_data, dict):
        logger.error("レジストリデータがdictではありません")
        return False

    if "tools" not in registry_data:
        logger.error("レジストリデータに 'tools' フィールドがありません")
        return False

    if not isinstance(registry_data["tools"], list):
        logger.error("'tools' フィールドがリストではありません")
        return False

    # 各ツールの基本構造チェック
    tools = registry_data["tools"]
    for idx, tool in enumerate(tools):
        if not isinstance(tool, dict):
            logger.error(f"ツール[{idx}]がdictではありません")
            return False

        required_fields = ["name", "description", "httpMethod", "path"]
        for field in required_fields:
            if field not in tool:
                logger.error(
                    f"ツール[{idx}]に必須フィールド '{field}' がありません"
                )
                return False

    logger.debug(f"レジストリデータ検証成功: {len(tools)}個のツール")
    return True


# ============================================================================
# 使用例（モジュール直接実行時）
# ============================================================================

if __name__ == "__main__":
    # ログ設定
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    print("=== ツールレジストリ取得テスト ===\n")

    try:
        # ツールレジストリ取得
        print("1. ツールレジストリ取得")
        tools = fetch_tools()
        print(f"   利用可能なツール数: {tools['count']}")
        print(f"   取得時刻: {tools['fetched_at']}")
        print()

        # ツール一覧表示
        print("2. ツール一覧")
        tool_names = list_available_tools()
        for idx, name in enumerate(tool_names, 1):
            print(f"   {idx}. {name}")
        print()

        # 特定ツールのスキーマ取得
        if tool_names:
            first_tool = tool_names[0]
            print(f"3. '{first_tool}' のスキーマ取得")
            schema = get_tool_schema(first_tool)
            if schema:
                print(f"   説明: {schema.get('description')}")
                print(f"   HTTPメソッド: {schema.get('httpMethod')}")
                print(f"   パス: {schema.get('path')}")
                print(f"   認証必要: {schema.get('requiresAuth')}")
                print()

        # キャッシュテスト
        print("4. キャッシュテスト")
        print("   キャッシュから再取得...")
        tools_cached = fetch_tools(use_cache=True)
        print(f"   キャッシュ時刻: {tools_cached.get('cached_at')}")
        print()

        # キャッシュクリア
        print("5. キャッシュクリア")
        clear_tools_cache()
        print("   キャッシュをクリアしました")
        print()

    except RegistryError as e:
        print(f"エラー: {e}")
        print("\n注意: C# サーバーが起動していることを確認してください")
