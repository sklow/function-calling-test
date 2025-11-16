"""
LLM モジュール

Ollamaとの通信を担当するモジュール
- LLMへのリクエスト送信
- レスポンスの解析
- Function Callingの処理
- リトライロジック
"""

from .ollama_client import (
    # 主要関数
    ollama_chat,
    check_ollama_health,
    list_models,
    # カスタム例外
    OllamaError,
    OllamaConnectionError,
    OllamaTimeoutError,
    OllamaAPIError,
    # 型定義
    OllamaMessage,
    OllamaOptions,
    OllamaFormatSchema,
    OllamaChatRequest,
    OllamaChatResponse,
    OllamaModelInfo,
)

__all__ = [
    # 主要関数
    "ollama_chat",
    "check_ollama_health",
    "list_models",
    # カスタム例外
    "OllamaError",
    "OllamaConnectionError",
    "OllamaTimeoutError",
    "OllamaAPIError",
    # 型定義
    "OllamaMessage",
    "OllamaOptions",
    "OllamaFormatSchema",
    "OllamaChatRequest",
    "OllamaChatResponse",
    "OllamaModelInfo",
]
