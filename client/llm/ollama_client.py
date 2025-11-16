"""
Ollama API クライアントラッパー

Ollama Chat API (/api/chat) を呼び出す低レベル関数を提供する。
requests ライブラリを使用した直接的なHTTP通信を行う。
"""

import json
import logging
from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict

import requests


# ログ設定
logger = logging.getLogger(__name__)


# ========================================
# カスタム例外クラス
# ========================================

class OllamaError(Exception):
    """Ollama API のベース例外"""
    pass


class OllamaConnectionError(OllamaError):
    """Ollama サーバーへの接続エラー"""
    pass


class OllamaTimeoutError(OllamaError):
    """Ollama API のタイムアウト"""
    pass


class OllamaAPIError(OllamaError):
    """Ollama API のエラーレスポンス"""
    pass


# ========================================
# 型定義（TypedDict）
# ========================================

class OllamaMessage(TypedDict):
    """Ollama メッセージ型"""
    role: str  # "user", "assistant", "system"
    content: str


class OllamaOptions(TypedDict, total=False):
    """Ollama オプション型"""
    temperature: float
    num_ctx: int
    top_k: int
    top_p: float
    repeat_penalty: float


class OllamaFormatSchema(TypedDict):
    """Ollama フォーマットスキーマ型"""
    type: str  # "json"
    schema: Dict[str, Any]


class OllamaChatRequest(TypedDict, total=False):
    """Ollama Chat API リクエスト型"""
    model: str
    messages: List[OllamaMessage]
    stream: bool
    format: OllamaFormatSchema
    options: OllamaOptions
    tools: List[Dict[str, Any]]


class OllamaChatResponse(TypedDict):
    """Ollama Chat API レスポンス型"""
    model: str
    created_at: str
    message: OllamaMessage
    done: bool
    total_duration: int
    load_duration: int
    prompt_eval_count: int
    prompt_eval_duration: int
    eval_count: int
    eval_duration: int


class OllamaModelInfo(TypedDict):
    """Ollama モデル情報型"""
    name: str
    modified_at: str
    size: int
    digest: str


# ========================================
# 主要関数
# ========================================

def ollama_chat(
    messages: List[Dict[str, Any]],
    model: str = "gemma3:4b",
    tools: Optional[List[Dict[str, Any]]] = None,
    format_schema: Optional[Dict[str, Any]] = None,
    host: str = "http://localhost:11434",
    temperature: float = 0.7,
    timeout: int = 30
) -> Dict[str, Any]:
    """
    Ollama Chat API を呼び出す

    Args:
        messages: 会話履歴（{"role": str, "content": str}のリスト）
        model: 使用するモデル名（例: "gemma3:4b", "llama3.1:8b"）
        tools: ツール定義（ネイティブサポート用、将来対応）
        format_schema: JSON Schema による出力制約
        host: Ollama ホストURL
        temperature: 温度パラメータ（0.0-1.0、高いほどランダム）
        timeout: タイムアウト秒数

    Returns:
        Ollama APIのレスポンス（OllamaChatResponse型）

    Raises:
        OllamaConnectionError: 接続エラー
        OllamaTimeoutError: タイムアウト
        OllamaAPIError: API エラー

    Example:
        >>> messages = [{"role": "user", "content": "こんにちは"}]
        >>> response = ollama_chat(messages, model="gemma3:4b")
        >>> print(response["message"]["content"])
    """
    # エンドポイントURL構築
    endpoint = f"{host.rstrip('/')}/api/chat"

    # リクエストボディ構築
    request_body: OllamaChatRequest = {
        "model": model,
        "messages": messages,  # type: ignore
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_ctx": 4096  # コンテキストウィンドウサイズ
        }
    }

    # format_schema が指定されている場合、format フィールドを追加
    if format_schema is not None:
        request_body["format"] = {
            "type": "json",
            "schema": format_schema
        }

    # tools が指定されている場合、tools フィールドを追加（将来対応）
    if tools is not None:
        request_body["tools"] = tools
        logger.debug("ツール定義が指定されましたが、現在は実験的サポートです")

    # デバッグログ: リクエスト送信
    logger.debug(
        f"Ollama Chat API リクエスト送信: endpoint={endpoint}, "
        f"model={model}, messages_count={len(messages)}, "
        f"temperature={temperature}, timeout={timeout}s"
    )
    logger.debug(f"リクエストボディ: {json.dumps(request_body, ensure_ascii=False, indent=2)}")

    try:
        # HTTP POSTリクエスト送信
        response = requests.post(
            endpoint,
            json=request_body,
            timeout=timeout,
            headers={"Content-Type": "application/json"}
        )

        # HTTPステータスコードチェック
        response.raise_for_status()

    except requests.exceptions.ConnectionError as e:
        error_msg = f"Ollama サーバーへの接続に失敗しました: {host}"
        logger.error(f"{error_msg} - {str(e)}")
        raise OllamaConnectionError(error_msg) from e

    except requests.exceptions.Timeout as e:
        error_msg = f"Ollama API がタイムアウトしました（{timeout}秒）"
        logger.error(f"{error_msg} - {str(e)}")
        raise OllamaTimeoutError(error_msg) from e

    except requests.exceptions.HTTPError as e:
        error_msg = (
            f"Ollama API がエラーを返しました: "
            f"status={response.status_code}, reason={response.reason}"
        )
        logger.error(f"{error_msg} - レスポンス: {response.text}")
        raise OllamaAPIError(error_msg) from e

    except requests.exceptions.RequestException as e:
        error_msg = f"Ollama API リクエスト中に予期しないエラーが発生しました"
        logger.error(f"{error_msg} - {str(e)}")
        raise OllamaAPIError(error_msg) from e

    # JSONレスポンスのパース
    try:
        response_data: Dict[str, Any] = response.json()

    except json.JSONDecodeError as e:
        error_msg = "Ollama API のレスポンスをJSONとしてパースできませんでした"
        logger.error(f"{error_msg} - レスポンス: {response.text}")
        raise OllamaAPIError(error_msg) from e

    # デバッグログ: レスポンス受信
    logger.debug(
        f"Ollama Chat API レスポンス受信: model={response_data.get('model')}, "
        f"done={response_data.get('done')}, "
        f"eval_count={response_data.get('eval_count')}"
    )
    logger.debug(f"レスポンスボディ: {json.dumps(response_data, ensure_ascii=False, indent=2)}")

    return response_data


# ========================================
# 補助関数
# ========================================

def check_ollama_health(host: str = "http://localhost:11434") -> bool:
    """
    Ollama サーバーの死活監視

    Ollama サーバーが起動しているか、APIが応答可能かをチェックする。

    Args:
        host: Ollama ホストURL

    Returns:
        サーバーが正常に応答する場合はTrue、それ以外はFalse

    Example:
        >>> if check_ollama_health():
        ...     print("Ollama サーバーは正常です")
    """
    endpoint = f"{host.rstrip('/')}/api/tags"

    try:
        response = requests.get(endpoint, timeout=5)
        response.raise_for_status()

        logger.debug(f"Ollama サーバー死活監視: OK (host={host})")
        return True

    except requests.exceptions.RequestException as e:
        logger.warning(f"Ollama サーバー死活監視: NG (host={host}) - {str(e)}")
        return False


def list_models(host: str = "http://localhost:11434") -> List[str]:
    """
    利用可能なモデル一覧を取得

    Ollama サーバーにインストールされているモデル名のリストを返す。

    Args:
        host: Ollama ホストURL

    Returns:
        モデル名のリスト（例: ["gemma3:4b", "llama3.1:8b"]）

    Raises:
        OllamaConnectionError: 接続エラー
        OllamaAPIError: API エラー

    Example:
        >>> models = list_models()
        >>> print(f"利用可能なモデル: {', '.join(models)}")
    """
    endpoint = f"{host.rstrip('/')}/api/tags"

    try:
        response = requests.get(endpoint, timeout=10)
        response.raise_for_status()

    except requests.exceptions.ConnectionError as e:
        error_msg = f"Ollama サーバーへの接続に失敗しました: {host}"
        logger.error(f"{error_msg} - {str(e)}")
        raise OllamaConnectionError(error_msg) from e

    except requests.exceptions.HTTPError as e:
        error_msg = (
            f"Ollama API がエラーを返しました: "
            f"status={response.status_code}, reason={response.reason}"
        )
        logger.error(f"{error_msg} - レスポンス: {response.text}")
        raise OllamaAPIError(error_msg) from e

    except requests.exceptions.RequestException as e:
        error_msg = f"Ollama API リクエスト中に予期しないエラーが発生しました"
        logger.error(f"{error_msg} - {str(e)}")
        raise OllamaAPIError(error_msg) from e

    try:
        data = response.json()
        models_info: List[OllamaModelInfo] = data.get("models", [])
        model_names = [model["name"] for model in models_info]

        logger.debug(f"利用可能なモデル一覧を取得: {len(model_names)}個 - {model_names}")
        return model_names

    except (json.JSONDecodeError, KeyError) as e:
        error_msg = "Ollama API のレスポンスをパースできませんでした"
        logger.error(f"{error_msg} - レスポンス: {response.text}")
        raise OllamaAPIError(error_msg) from e
