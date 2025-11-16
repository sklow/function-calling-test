"""
メインオーケストレーションループ

LLM (Gemma 3) とツール呼び出しを連携させるメインループ。
JSON Schema 方式を使用してツール呼び出しを制御します。

主要機能:
- ユーザークエリからの反復的なツール呼び出し
- JSON Schema による構造化レスポンス
- エラーハンドリングとリトライ
- 最終回答の生成
- 詳細なログ出力
"""

import json
import logging
from typing import Any, Dict, List, Optional

from client.api.registry import fetch_tools
from client.api.tool_client import call_tool, ToolCallError
from client.llm.ollama_client import (
    ollama_chat,
    OllamaError,
    OllamaConnectionError,
    OllamaTimeoutError
)
from client.schemas.tool_call import (
    ToolCall,
    ToolResult,
    FinalAnswer,
    Clarification,
    parse_llm_response,
    ResponseType
)
# プロンプトビルダーのインポート（新しいモジュールを優先使用）
from client.prompts.prompt_builder import build_system_prompt as new_build_system_prompt


# ログ設定
logger = logging.getLogger(__name__)


# ============================================================================
# JSON Schema 定義
# ============================================================================

# ツール呼び出し / 最終回答 / 確認質問の統合 Schema
CALL_SCHEMA = {
    "type": "object",
    "properties": {
        "kind": {
            "type": "string",
            "enum": ["tool_call", "final_answer", "clarify"],
            "description": "レスポンスの種類"
        },
        "tool": {
            "type": "string",
            "description": "呼び出すツール名 (kind=tool_call の場合に必須)"
        },
        "arguments": {
            "type": "object",
            "description": "ツールに渡す引数 (kind=tool_call の場合に必須)"
        },
        "content": {
            "type": "string",
            "description": "最終回答の内容 (kind=final_answer の場合に必須) / 説明メッセージ (任意)"
        },
        "thought": {
            "type": "string",
            "description": "思考過程 (任意、デバッグ用)"
        },
        "question": {
            "type": "string",
            "description": "ユーザーへの質問 (kind=clarify の場合に必須)"
        },
        "missing_params": {
            "type": "array",
            "items": {"type": "string"},
            "description": "不足しているパラメータ (kind=clarify の場合)"
        }
    },
    "required": ["kind"],
    "allOf": [
        {
            "if": {
                "properties": {"kind": {"const": "tool_call"}}
            },
            "then": {
                "required": ["tool", "arguments"]
            }
        },
        {
            "if": {
                "properties": {"kind": {"const": "final_answer"}}
            },
            "then": {
                "required": ["content"]
            }
        },
        {
            "if": {
                "properties": {"kind": {"const": "clarify"}}
            },
            "then": {
                "required": ["question"]
            }
        }
    ]
}


# ============================================================================
# カスタム例外クラス
# ============================================================================

class OrchestratorError(Exception):
    """オーケストレーションの基本例外"""
    pass


class MaxIterationsReached(OrchestratorError):
    """最大反復回数に到達"""
    pass


class InvalidResponseFormat(OrchestratorError):
    """LLMからの無効なレスポンス形式"""
    pass


class ToolExecutionFailed(OrchestratorError):
    """ツール実行の失敗"""
    pass


# ============================================================================
# 主要関数
# ============================================================================

def run_loop(
    user_query: str,
    model: str = "gemma3:4b",
    api_base: str = "http://localhost:5000",
    ollama_host: str = "http://localhost:11434",
    max_iterations: int = 10,
    timeout: int = 30
) -> str:
    """
    メインのオーケストレーションループ

    ユーザーのクエリを受け取り、LLMとツール呼び出しを反復的に実行して
    最終的な回答を生成します。

    Args:
        user_query: ユーザーの質問
        model: 使用するLLMモデル名
        api_base: C# APIサーバーのベースURL
        ollama_host: OllamaサーバーのURL
        max_iterations: 最大反復回数
        timeout: タイムアウト秒数

    Returns:
        最終回答の文字列

    Raises:
        OrchestratorError: オーケストレーションエラー
        MaxIterationsReached: 最大反復回数に到達
        InvalidResponseFormat: 無効なレスポンス形式
        ToolExecutionFailed: ツール実行の失敗

    Example:
        >>> answer = run_loop("東京の天気は?")
        >>> print(answer)
        東京の今日の天気は晴れで、気温は25度です。
    """
    logger.info("=" * 60)
    logger.info("オーケストレーションループを開始します")
    logger.info(f"ユーザークエリ: {user_query}")
    logger.info(f"モデル: {model}")
    logger.info(f"最大反復回数: {max_iterations}")
    logger.info("=" * 60)

    # ステップ1: 初期化
    try:
        # ツールレジストリの取得
        logger.info("ステップ1: ツールレジストリを取得中...")
        tools_registry = fetch_tools(api_base=api_base, use_cache=True)
        tools = tools_registry.get("tools", [])
        logger.info(f"利用可能なツール数: {len(tools)}")

        # システムプロンプトの構築（新しいプロンプトビルダーを使用）
        logger.info("ステップ2: システムプロンプトを構築中...")
        system_prompt = new_build_system_prompt(tools)
        logger.debug(f"システムプロンプト長: {len(system_prompt)} 文字")

        # メッセージ履歴の初期化
        messages: List[Dict[str, str]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ]
        logger.info(f"メッセージ履歴を初期化しました (メッセージ数: {len(messages)})")

    except Exception as e:
        error_msg = f"初期化エラー: {str(e)}"
        logger.error(error_msg)
        raise OrchestratorError(error_msg) from e

    # ステップ2: メインループ
    for iteration in range(max_iterations):
        logger.info("")
        logger.info("=" * 60)
        logger.info(f"オーケストレーション反復 {iteration + 1}/{max_iterations} を開始")
        logger.info("=" * 60)

        try:
            # フェーズ1: LLM呼び出し（ツール呼び出し判断）
            logger.info(f"フェーズ1: LLMに問い合わせ中... (メッセージ数: {len(messages)})")
            logger.debug(f"送信メッセージ: {json.dumps(messages, ensure_ascii=False, indent=2)}")

            try:
                call_response = ollama_chat(
                    messages=messages,
                    model=model,
                    format_schema=CALL_SCHEMA,
                    host=ollama_host,
                    timeout=timeout
                )
            except OllamaConnectionError as e:
                error_msg = (
                    f"Ollama サーバーへの接続に失敗しました: {ollama_host}\n"
                    f"サーバーが起動していることを確認してください。\n"
                    f"詳細: {str(e)}"
                )
                logger.error(error_msg)
                raise OrchestratorError(error_msg) from e
            except OllamaTimeoutError as e:
                error_msg = f"LLM呼び出しがタイムアウトしました ({timeout}秒)"
                logger.error(error_msg)
                raise OrchestratorError(error_msg) from e
            except OllamaError as e:
                error_msg = f"LLM呼び出しエラー: {str(e)}"
                logger.error(error_msg)
                raise OrchestratorError(error_msg) from e

            # レスポンスの取得
            llm_response_text = call_response.get("message", {}).get("content", "")
            logger.info(f"LLMレスポンス受信: {len(llm_response_text)} 文字")
            logger.debug(f"LLMレスポンス内容:\n{llm_response_text}")

            # フェーズ2: レスポンスのパース
            logger.info("フェーズ2: レスポンスをパース中...")
            try:
                action = parse_llm_response(llm_response_text)
                logger.info(f"パース結果: {type(action).__name__}")
            except ValueError as e:
                # JSONパースエラーの場合、補完を試行
                logger.warning(f"レスポンスのパースに失敗: {str(e)}")
                logger.info("JSONの補完を試行中...")

                try:
                    # 基本的なJSON補完（中括弧の補完など）
                    fixed_json = safe_parse_json(llm_response_text)
                    action = parse_llm_response(fixed_json)
                    logger.info(f"補完後のパース成功: {type(action).__name__}")
                except Exception as e2:
                    error_msg = f"レスポンスの補完にも失敗しました: {str(e2)}"
                    logger.error(error_msg)
                    logger.error(f"元のレスポンス: {llm_response_text}")
                    raise InvalidResponseFormat(error_msg) from e2

            # フェーズ3: アクションの処理
            logger.info("フェーズ3: アクションを処理中...")

            if isinstance(action, FinalAnswer):
                # 最終回答の場合は終了
                logger.info("=" * 60)
                logger.info("最終回答を受信しました")
                logger.info("=" * 60)
                logger.info(f"回答内容: {action.content}")
                logger.info(f"総反復回数: {iteration + 1}")
                return action.content

            elif isinstance(action, ToolCall):
                # ツール呼び出しの実行
                logger.info(f"ツール呼び出し: {action.tool}")
                logger.debug(f"ツール引数: {json.dumps(action.arguments, ensure_ascii=False, indent=2)}")

                # ツール実行
                tool_result = execute_tool(action, api_base, timeout)

                # 結果のログ出力
                if tool_result.ok:
                    logger.info(f"ツール実行成功: {action.tool}")
                    logger.debug(f"実行結果: {tool_result.content}")
                else:
                    logger.warning(f"ツール実行失敗: {action.tool}")
                    logger.warning(f"エラー: {tool_result.error}")

                # メッセージ履歴に追加
                messages.append({
                    "role": "assistant",
                    "content": json.dumps(action.model_dump(), ensure_ascii=False)
                })
                messages.append({
                    "role": "user",
                    "content": json.dumps(tool_result.model_dump(), ensure_ascii=False)
                })

                logger.info(f"メッセージ履歴を更新しました (メッセージ数: {len(messages)})")

                # 次の反復へ継続
                continue

            elif isinstance(action, Clarification):
                # 確認質問の処理（将来の拡張用）
                logger.info(f"確認質問: {action.question}")
                logger.info(f"不足パラメータ: {action.missing_params}")

                # 現在は確認質問をエラーとして扱う（将来的にユーザー入力対応予定）
                error_msg = (
                    f"LLMが追加情報を要求しています: {action.question}\n"
                    f"不足パラメータ: {action.missing_params}\n"
                    f"※現在のバージョンでは対話的な確認に対応していません。"
                )
                logger.error(error_msg)
                raise OrchestratorError(error_msg)

            else:
                # 未知のレスポンスタイプ
                error_msg = f"未知のレスポンスタイプ: {type(action).__name__}"
                logger.error(error_msg)
                raise InvalidResponseFormat(error_msg)

        except (OrchestratorError, InvalidResponseFormat, ToolExecutionFailed):
            # 既知のエラーはそのまま再送出
            raise

        except Exception as e:
            # その他の予期しないエラー
            error_msg = f"反復 {iteration + 1} で予期しないエラーが発生しました: {str(e)}"
            logger.error(error_msg)
            logger.exception("詳細なスタックトレース:")
            raise OrchestratorError(error_msg) from e

    # 最大反復回数に到達
    error_msg = (
        f"最大反復回数 ({max_iterations}) に到達しました。\n"
        f"タスクを完了できませんでした。"
    )
    logger.error(error_msg)
    raise MaxIterationsReached(error_msg)


# ============================================================================
# 補助関数
# ============================================================================

def build_system_prompt(tools: List[Dict[str, Any]]) -> str:
    """
    ツール情報を含むシステムプロンプトを構築（非推奨）

    この関数は後方互換性のために残されています。
    新しいコードでは client.prompts.prompt_builder.build_system_prompt を使用してください。

    Args:
        tools: ツールレジストリから取得したツール一覧

    Returns:
        システムプロンプト文字列

    Deprecated:
        バージョン 0.2.0 で非推奨となりました。
        代わりに client.prompts.prompt_builder.build_system_prompt を使用してください。
    """
    logger.warning(
        "loop.build_system_prompt() は非推奨です。"
        "client.prompts.prompt_builder.build_system_prompt を使用してください。"
    )
    # 新しいプロンプトビルダーに委譲
    return new_build_system_prompt(tools)


def execute_tool(
    tool_call: ToolCall,
    api_base: str,
    timeout: int = 30
) -> ToolResult:
    """
    ツール呼び出しを実行し、結果を ToolResult で返す

    Args:
        tool_call: ツール呼び出し情報
        api_base: APIサーバーのベースURL
        timeout: タイムアウト秒数

    Returns:
        ツール実行結果 (ToolResult)
    """
    try:
        logger.info(f"ツール '{tool_call.tool}' を呼び出し中...")
        logger.debug(f"引数: {json.dumps(tool_call.arguments, ensure_ascii=False, indent=2)}")

        # ツール呼び出し実行
        result = call_tool(
            tool_name=tool_call.tool,
            arguments=tool_call.arguments,
            api_base=api_base,
            timeout=timeout
        )

        # 成功時の ToolResult を生成
        logger.info(f"ツール実行成功: {tool_call.tool}")
        return ToolResult(
            tool=tool_call.tool,
            ok=True,
            content=json.dumps(result, ensure_ascii=False)
        )

    except ToolCallError as e:
        # ツール呼び出しエラー
        error_msg = f"ツール実行エラー: {str(e)}"
        logger.error(error_msg)

        return ToolResult(
            tool=tool_call.tool,
            ok=False,
            content="ツールの実行に失敗しました",
            error=str(e)
        )

    except Exception as e:
        # 予期しないエラー
        error_msg = f"予期しないツール実行エラー: {str(e)}"
        logger.error(error_msg)
        logger.exception("詳細なスタックトレース:")

        return ToolResult(
            tool=tool_call.tool,
            ok=False,
            content="予期しないエラーが発生しました",
            error=str(e)
        )


def handle_clarification(
    clarification: Clarification,
    messages: List[Dict[str, str]]
) -> str:
    """
    確認質問を処理（将来の拡張用）

    現在のバージョンでは確認質問に対応していないため、
    エラーメッセージを返します。

    Args:
        clarification: 確認質問情報
        messages: メッセージ履歴

    Returns:
        ユーザーへの説明メッセージ

    Note:
        将来的にはユーザー入力を受け付ける機能を追加予定
    """
    logger.warning(f"確認質問を受信しました: {clarification.question}")
    logger.warning("現在のバージョンでは確認質問に対応していません")

    return (
        f"追加情報が必要です: {clarification.question}\n"
        f"不足パラメータ: {clarification.missing_params}"
    )


def safe_parse_json(text: str) -> str:
    """
    JSONテキストの補完を試行

    不完全なJSONを可能な限り修復します。

    Args:
        text: パース対象のテキスト

    Returns:
        補完されたJSON文字列

    Raises:
        ValueError: 補完に失敗した場合
    """
    # 前後の空白を除去
    text = text.strip()

    # コードブロックマーカーを除去（```json ... ``` など）
    if text.startswith("```"):
        lines = text.split("\n")
        # 最初と最後の```行を除去
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    # 基本的なJSON補完
    try:
        # まずそのままパースを試行
        json.loads(text)
        return text
    except json.JSONDecodeError:
        pass

    # 閉じ括弧が不足している場合の補完
    open_braces = text.count("{")
    close_braces = text.count("}")
    if open_braces > close_braces:
        text += "}" * (open_braces - close_braces)
        logger.debug(f"閉じ括弧を補完しました: {open_braces - close_braces}個")

    # 再度パースを試行
    try:
        json.loads(text)
        return text
    except json.JSONDecodeError as e:
        logger.error(f"JSON補完に失敗: {str(e)}")
        raise ValueError(f"JSONの補完に失敗しました: {str(e)}") from e


# ============================================================================
# モジュールの公開インターフェース
# ============================================================================

__all__ = [
    "run_loop",
    "build_system_prompt",
    "execute_tool",
    "handle_clarification",
    "safe_parse_json",
    "OrchestratorError",
    "MaxIterationsReached",
    "InvalidResponseFormat",
    "ToolExecutionFailed",
    "CALL_SCHEMA",
]
