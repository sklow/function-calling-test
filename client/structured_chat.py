#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ollama + Gemma3 + LangChain の Structured Output + ツール呼び出し + メモリ保持
Function Callingが使えないGemma3でも、Structured Outputを使ってツールを呼び出せます
"""

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
import json

# ============================================================
# 1. ツール呼び出しリクエストの構造定義（Pydanticモデル）
# ============================================================

class ToolCall(BaseModel):
    """ツール呼び出しのリクエスト"""
    should_use_tool: bool = Field(description="ツールを使用する必要があるか（True/False）")
    tool_name: Optional[Literal["get_current_time", "calculate", "get_weather", "get_word_count"]] = Field(
        default=None,
        description="使用するツールの名前。使わない場合はNone"
    )
    tool_argument: Optional[str] = Field(
        default=None,
        description="ツールに渡す引数。calculateの場合は数式、get_weatherの場合は場所、get_word_countの場合はテキスト"
    )
    response: str = Field(description="ユーザーへの応答メッセージ")

# ============================================================
# 2. ツール関数の実装
# ============================================================

def get_current_time() -> str:
    """現在の日時を取得します"""
    now = datetime.now()
    return now.strftime("%Y年%m月%d日 %H時%M分%S秒")

def calculate(expression: str) -> str:
    """
    数式を計算します

    Args:
        expression: 計算する数式（例: "2 + 3 * 4"）
    """
    try:
        # 安全な計算のため、eval()を制限的に使用
        result = eval(expression, {"__builtins__": {}}, {})
        return f"{expression} = {result}"
    except Exception as e:
        return f"計算エラー: {str(e)}"

def get_weather(location: str) -> str:
    """
    指定された場所の天気情報を取得します（シミュレーション）

    Args:
        location: 場所の名前（例: "東京"）
    """
    import random
    weather_conditions = ["晴れ", "曇り", "雨", "雪"]
    temp = random.randint(-5, 35)
    condition = random.choice(weather_conditions)

    return f"{location}の天気: {condition}、気温: {temp}°C"

def get_word_count(text: str) -> str:
    """
    テキストの文字数と単語数をカウントします

    Args:
        text: カウントするテキスト
    """
    char_count = len(text)
    word_count = len(text.split())

    return f"文字数: {char_count}、単語数: {word_count}"

# ツールのマッピング
TOOLS = {
    "get_current_time": get_current_time,
    "calculate": calculate,
    "get_weather": get_weather,
    "get_word_count": get_word_count,
}

# ============================================================
# 3. メイン処理
# ============================================================

def execute_tool(tool_name: str, argument: Optional[str]) -> str:
    """ツールを実行して結果を返す"""
    tool_func = TOOLS.get(tool_name)

    if not tool_func:
        return f"エラー: ツール '{tool_name}' が見つかりません"

    try:
        # get_current_timeは引数不要
        if tool_name == "get_current_time":
            return tool_func()
        else:
            return tool_func(argument)
    except Exception as e:
        return f"ツール実行エラー: {str(e)}"

def main():
    # LLMの初期化（temperature=0で安定性向上）
    llm = ChatOllama(
        model="gemma3:4b",
        temperature=0,
    )

    # Structured Outputを使用
    structured_llm = llm.with_structured_output(ToolCall)

    # システムプロンプト
    system_prompt = """あなたは親切で知識豊富なAIアシスタントです。
ユーザーの質問に答えるために、必要に応じて以下のツールを使用してください。

利用可能なツール:
1. get_current_time: 現在の日時を取得（引数不要）
2. calculate: 数式を計算（引数: 数式の文字列、例: "123 + 456"）
3. get_weather: 天気情報を取得（引数: 場所の名前、例: "東京"）
4. get_word_count: 文字数をカウント（引数: カウントするテキスト）

ツールを使う必要がある場合：
- should_use_tool を true に設定
- tool_name に使用するツール名を設定
- tool_argument にツールに渡す引数を設定
- response にツールを使用することを説明

ツールを使う必要がない場合：
- should_use_tool を false に設定
- tool_name と tool_argument は null
- response に直接回答を記述

必ず JSON 形式で応答してください。"""

    # 会話履歴を保持するリスト
    chat_history = []

    print("=" * 60)
    print("Gemma3 Structured Output + ツール呼び出し + メモリ保持")
    print("=" * 60)
    print("ツールを使って様々な機能を実行できます（会話履歴も保持）")
    print("\n利用可能なツール:")
    print("  - 現在時刻の取得")
    print("  - 計算機能")
    print("  - 天気情報（シミュレーション）")
    print("  - 文字数カウント")
    print("\n例: '今何時?', '123 + 456を計算して', '東京の天気は?'")
    print("終了するには 'quit' または 'exit' と入力してください\n")

    # 対話ループ
    while True:
        user_input = input("あなた: ").strip()

        if user_input.lower() in ['quit', 'exit', '終了']:
            print("\nチャットを終了します。")
            break

        if not user_input:
            continue

        try:
            # メッセージの構築
            messages = [
                SystemMessage(content=system_prompt),
                *chat_history,
                HumanMessage(content=user_input)
            ]

            # Structured Outputで応答を取得
            result: ToolCall = structured_llm.invoke(messages)

            # デバッグ情報
            print(f"\n[判断] ツール使用: {result.should_use_tool}")
            if result.should_use_tool:
                print(f"[ツール] {result.tool_name}")
                print(f"[引数] {result.tool_argument}")

            # ツールを使用する場合
            if result.should_use_tool and result.tool_name:
                # ツールを実行
                tool_result = execute_tool(result.tool_name, result.tool_argument)
                print(f"[結果] {tool_result}")

                # 会話履歴に追加（ユーザー入力 + ツール使用の記録）
                chat_history.append(HumanMessage(content=user_input))
                chat_history.append(AIMessage(
                    content=f"ツール '{result.tool_name}' を使用しました。結果: {tool_result}"
                ))

                # ユーザーに表示
                print(f"\nGemma3: {tool_result}\n")
            else:
                # ツールを使わない通常の応答
                chat_history.append(HumanMessage(content=user_input))
                chat_history.append(AIMessage(content=result.response))

                print(f"\nGemma3: {result.response}\n")

            # メモリ管理: 会話履歴が長すぎる場合は古いものから削除
            if len(chat_history) > 20:
                chat_history = chat_history[-20:]

        except Exception as e:
            print(f"\nエラーが発生しました: {e}\n")
            print("エラーの詳細:")
            import traceback
            traceback.print_exc()
            print("\nOllamaが起動していることを確認してください。")
            print("コマンド: ollama run gemma3:4b\n")

if __name__ == "__main__":
    main()
