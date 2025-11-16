"""
C# ツールサーバー呼び出しクライアント

C# サーバの /tools/{tool_name} エンドポイントを呼び出して、
外部ツールを実行するためのクライアントライブラリ。

機能:
- ツール呼び出し（call_tool）
- リトライ機能付きツール呼び出し（call_tool_with_retry）
- APIサーバーヘルスチェック（check_api_health）
- 詳細なエラーハンドリングとログ出力
"""

import logging
from typing import Dict, Any, Optional, Union
from typing_extensions import TypedDict

import requests
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)


# ログ設定
logger = logging.getLogger(__name__)


# ============================================================================
# 型定義
# ============================================================================

class ToolResponse(TypedDict):
    """ツール実行結果の型定義"""
    success: bool
    data: Any
    error: Optional[str]


# ============================================================================
# カスタム例外クラス
# ============================================================================

class ToolClientError(Exception):
    """ツールクライアントのベース例外"""
    pass


class ToolCallError(ToolClientError):
    """ツール呼び出しの一般的なエラー"""
    pass


class ToolTimeoutError(ToolClientError):
    """ツール呼び出しのタイムアウト"""
    pass


class ToolNotFoundError(ToolClientError):
    """指定されたツールが存在しない（404エラー）"""
    pass


class ToolValidationError(ToolClientError):
    """ツール引数のバリデーションエラー（400エラー）"""
    pass


class ToolServerError(ToolClientError):
    """サーバー内部エラー（500エラー）"""
    pass


# ============================================================================
# 主要関数
# ============================================================================

def call_tool(
    tool_name: str,
    arguments: Dict[str, Any],
    api_base: str = "http://localhost:5000",
    timeout: int = 30,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    C# サーバのツールを呼び出す

    Args:
        tool_name: ツール名（例: "get_weather"）
        arguments: ツールの引数
        api_base: APIサーバーのベースURL
        timeout: タイムアウト秒数
        api_key: API認証キー（将来の認証対応）

    Returns:
        ツール実行結果の辞書

    Raises:
        ToolCallError: ツール呼び出しエラー
        ToolTimeoutError: タイムアウト
        ToolNotFoundError: ツールが存在しない
        ToolValidationError: 引数バリデーションエラー
        ToolServerError: サーバー内部エラー
    """
    # エンドポイントURL構築
    url = f"{api_base}/tools/{tool_name}"

    # HTTPヘッダー準備
    headers = {
        "Content-Type": "application/json"
    }

    # 将来のAPI Key認証対応
    if api_key:
        headers["X-API-Key"] = api_key

    # リクエスト送信ログ
    logger.debug(f"ツール呼び出しリクエスト送信: {tool_name}")
    logger.debug(f"エンドポイント: {url}")
    logger.debug(f"引数: {arguments}")

    try:
        # HTTP POSTリクエスト送信
        response = requests.post(
            url,
            json=arguments,
            headers=headers,
            timeout=timeout
        )

        # レスポンス受信ログ
        logger.debug(f"レスポンス受信: ステータスコード={response.status_code}")
        logger.debug(f"レスポンスボディ: {response.text}")

        # ステータスコード別エラーハンドリング
        if response.status_code == 200:
            # 正常な結果を返す
            result = response.json()
            logger.info(f"ツール呼び出し成功: {tool_name}")
            return result

        elif response.status_code == 400:
            # 引数バリデーションエラー
            error_detail = _extract_error_message(response)
            logger.error(f"引数バリデーションエラー: {error_detail}")
            raise ToolValidationError(
                f"ツール '{tool_name}' の引数が不正です: {error_detail}"
            )

        elif response.status_code == 404:
            # ツールが存在しない
            error_detail = _extract_error_message(response)
            logger.error(f"ツール未検出: {tool_name}")
            raise ToolNotFoundError(
                f"ツール '{tool_name}' が見つかりません: {error_detail}"
            )

        elif response.status_code == 500:
            # サーバー内部エラー
            error_detail = _extract_error_message(response)
            logger.error(f"サーバー内部エラー: {error_detail}")
            raise ToolServerError(
                f"サーバー内部エラーが発生しました: {error_detail}"
            )

        else:
            # その他のHTTPエラー
            error_detail = _extract_error_message(response)
            logger.error(f"予期しないHTTPエラー: {response.status_code}")
            raise ToolCallError(
                f"予期しないHTTPエラー（{response.status_code}）: {error_detail}"
            )

    except requests.Timeout as e:
        # タイムアウトエラー
        logger.error(f"ツール呼び出しタイムアウト: {tool_name} (timeout={timeout}s)")
        raise ToolTimeoutError(
            f"ツール '{tool_name}' の呼び出しがタイムアウトしました（{timeout}秒）"
        ) from e

    except requests.ConnectionError as e:
        # 接続エラー
        logger.error(f"APIサーバーへの接続エラー: {api_base}")
        raise ToolCallError(
            f"APIサーバー '{api_base}' への接続に失敗しました"
        ) from e

    except requests.RequestException as e:
        # その他のリクエストエラー
        logger.error(f"リクエストエラー: {str(e)}")
        raise ToolCallError(
            f"ツール呼び出し中にエラーが発生しました: {str(e)}"
        ) from e


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((ToolCallError, ToolTimeoutError))
)
def call_tool_with_retry(
    tool_name: str,
    arguments: Dict[str, Any],
    **kwargs
) -> Dict[str, Any]:
    """
    リトライ機能付きのツール呼び出し

    最大3回までリトライを実行します。
    指数バックオフ（1秒、2秒、4秒...最大10秒）で待機します。

    Args:
        tool_name: ツール名
        arguments: ツールの引数
        **kwargs: call_tool()に渡す追加パラメータ

    Returns:
        ツール実行結果の辞書

    Raises:
        ToolNotFoundError: ツールが存在しない（リトライしない）
        ToolValidationError: 引数バリデーションエラー（リトライしない）
        ToolCallError: リトライ後も失敗
        ToolTimeoutError: リトライ後もタイムアウト
        ToolServerError: サーバー内部エラー

    Note:
        ToolNotFoundError と ToolValidationError はリトライしません。
    """
    logger.info(f"リトライ機能付きツール呼び出し開始: {tool_name}")

    try:
        result = call_tool(tool_name, arguments, **kwargs)
        return result
    except (ToolCallError, ToolTimeoutError) as e:
        # リトライ対象のエラー - tenacityが自動的にリトライ
        logger.warning(f"リトライ対象エラー発生: {str(e)}")
        raise
    except (ToolNotFoundError, ToolValidationError, ToolServerError) as e:
        # リトライ対象外のエラー - 即座に失敗
        logger.error(f"リトライ不可能なエラー発生: {str(e)}")
        raise


# ============================================================================
# 補助関数
# ============================================================================

def check_api_health(api_base: str = "http://localhost:5000") -> bool:
    """
    C# APIサーバーの死活監視

    GET / エンドポイントでヘルスチェックを実行します。

    Args:
        api_base: APIサーバーのベースURL

    Returns:
        サーバーが正常に動作している場合はTrue、それ以外はFalse
    """
    try:
        logger.debug(f"APIサーバーヘルスチェック: {api_base}")
        response = requests.get(api_base, timeout=5)

        if response.status_code == 200:
            logger.info(f"APIサーバー正常動作確認: {api_base}")
            return True
        else:
            logger.warning(
                f"APIサーバー異常レスポンス: {api_base} "
                f"(ステータスコード={response.status_code})"
            )
            return False

    except requests.RequestException as e:
        logger.error(f"APIサーバーヘルスチェック失敗: {api_base} - {str(e)}")
        return False


def validate_tool_arguments(
    tool_name: str,
    arguments: Dict[str, Any],
    tool_schemas: Dict[str, Any]
) -> bool:
    """
    ツール引数をスキーマに対してバリデーション

    将来的にツールスキーマ取得後に実装予定。
    現在はプレースホルダー実装。

    Args:
        tool_name: ツール名
        arguments: 検証対象の引数
        tool_schemas: ツールスキーマ定義

    Returns:
        バリデーション成功の場合はTrue

    Raises:
        ToolValidationError: バリデーション失敗

    Note:
        現在は常にTrueを返します。
        将来的にjsonschemaライブラリを使用して実装予定。
    """
    # TODO: ツールスキーマ取得機能実装後に完全実装
    logger.debug(
        f"引数バリデーション（未実装）: {tool_name} - {arguments}"
    )
    return True


def _extract_error_message(response: requests.Response) -> str:
    """
    HTTPレスポンスからエラーメッセージを抽出

    Args:
        response: HTTPレスポンスオブジェクト

    Returns:
        抽出されたエラーメッセージ
    """
    try:
        # JSONレスポンスからエラーメッセージ取得を試行
        error_data = response.json()

        # 一般的なエラーメッセージフィールドを検索
        if isinstance(error_data, dict):
            return (
                error_data.get("error") or
                error_data.get("message") or
                error_data.get("detail") or
                str(error_data)
            )
        else:
            return str(error_data)

    except ValueError:
        # JSONパース失敗 - テキストレスポンスを返す
        return response.text or f"HTTPエラー {response.status_code}"


# ============================================================================
# 使用例（モジュール直接実行時）
# ============================================================================

if __name__ == "__main__":
    # ログ設定
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # サーバーヘルスチェック
    print("=== APIサーバーヘルスチェック ===")
    is_healthy = check_api_health()
    print(f"サーバー状態: {'正常' if is_healthy else '異常'}\n")

    if is_healthy:
        # ツール呼び出し例
        print("=== ツール呼び出し例 ===")
        try:
            result = call_tool(
                tool_name="get_weather",
                arguments={"city": "Tokyo", "unit": "metric"}
            )
            print(f"結果: {result}\n")
        except ToolClientError as e:
            print(f"エラー: {e}\n")

        # リトライ付き呼び出し例
        print("=== リトライ付きツール呼び出し例 ===")
        try:
            result = call_tool_with_retry(
                tool_name="get_weather",
                arguments={"city": "Tokyo", "unit": "metric"}
            )
            print(f"結果: {result}\n")
        except ToolClientError as e:
            print(f"エラー: {e}\n")
