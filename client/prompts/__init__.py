"""
Prompts モジュール

プロンプト管理を担当するモジュール
- システムプロンプトの定義
- プロンプトテンプレート
- Function Calling用のプロンプト設計
- プロンプトの動的生成
"""

from client.prompts.prompt_builder import (
    # クラス
    PromptBuilder,
    PromptVariables,

    # 関数
    build_system_prompt,
    extract_tool_schema_info,
    format_tools_list,
    generate_tools_section,
    optimize_prompt_length,
    measure_prompt_effectiveness,

    # 定数
    PROMPT_TEMPLATES,
    LANGUAGE_CONFIGS,
)


__all__ = [
    # クラス
    'PromptBuilder',
    'PromptVariables',

    # 関数
    'build_system_prompt',
    'extract_tool_schema_info',
    'format_tools_list',
    'generate_tools_section',
    'optimize_prompt_length',
    'measure_prompt_effectiveness',

    # 定数
    'PROMPT_TEMPLATES',
    'LANGUAGE_CONFIGS',
]
