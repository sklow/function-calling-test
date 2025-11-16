"""
API モジュール

APIサーバーとの通信を担当するモジュール
- APIエンドポイントへのリクエスト送信
- レスポンスのハンドリング
- エラー処理
- 接続管理
- ツールレジストリ管理
"""

from .tool_client import (
    # 主要関数
    call_tool,
    call_tool_with_retry,
    check_api_health,
    validate_tool_arguments,

    # 例外クラス
    ToolClientError,
    ToolCallError,
    ToolTimeoutError,
    ToolNotFoundError,
    ToolValidationError,
    ToolServerError,

    # 型定義
    ToolResponse,
)

from .registry import (
    # 主要関数
    fetch_tools,
    get_tool_schema,
    clear_tools_cache,
    list_available_tools,
    validate_tool_registry,

    # 例外クラス
    RegistryError,
    RegistryTimeoutError,
    RegistryConnectionError,
    RegistryParseError,

    # 型定義
    ToolMetadata,

    # キャッシュ管理
    ToolsCache,
)

__all__ = [
    # tool_client 関数
    "call_tool",
    "call_tool_with_retry",
    "check_api_health",
    "validate_tool_arguments",

    # tool_client 例外
    "ToolClientError",
    "ToolCallError",
    "ToolTimeoutError",
    "ToolNotFoundError",
    "ToolValidationError",
    "ToolServerError",

    # tool_client 型定義
    "ToolResponse",

    # registry 関数
    "fetch_tools",
    "get_tool_schema",
    "clear_tools_cache",
    "list_available_tools",
    "validate_tool_registry",

    # registry 例外
    "RegistryError",
    "RegistryTimeoutError",
    "RegistryConnectionError",
    "RegistryParseError",

    # registry 型定義
    "ToolMetadata",

    # registry キャッシュ管理
    "ToolsCache",
]
