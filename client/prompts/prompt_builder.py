"""
プロンプトビルダー

システムプロンプトの動的構築とテンプレート管理を提供します。
ツール情報を含むプロンプトの生成、多言語対応、トークン最適化などの機能を実装します。

主要機能:
- プロンプトテンプレートの読み込みと管理
- ツール情報の動的挿入
- 多言語対応（日本語/英語）
- トークン数の制御と最適化
- カスタム指示の追加
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


# ログ設定
logger = logging.getLogger(__name__)


# ============================================================================
# テンプレート定義
# ============================================================================

# プロンプトテンプレートの定義
PROMPT_TEMPLATES = {
    'standard': 'system_prompt.txt',
    'concise': 'system_prompt_concise.txt',
    'detailed': 'system_prompt_detailed.txt',
    'debug': 'system_prompt_debug.txt'
}


# 言語別設定
LANGUAGE_CONFIGS = {
    'ja': {
        'role_description': 'あなたは有能なAIアシスタントです。',
        'rules_header': '# 重要な指示',
        'tools_header': '# 利用可能なツール',
        'examples_header': '# レスポンス例',
        'response_format_header': '# レスポンス形式',
        'tool_call_label': 'ツール呼び出し',
        'final_answer_label': '最終回答',
        'clarify_label': '確認質問',
        'parameters_label': 'パラメータ',
        'required_label': '必須',
        'optional_label': '任意',
        'no_params_label': '(パラメータなし)',
    },
    'en': {
        'role_description': 'You are a capable AI assistant.',
        'rules_header': '# Important Instructions',
        'tools_header': '# Available Tools',
        'examples_header': '# Response Examples',
        'response_format_header': '# Response Format',
        'tool_call_label': 'Tool Call',
        'final_answer_label': 'Final Answer',
        'clarify_label': 'Clarification',
        'parameters_label': 'Parameters',
        'required_label': 'Required',
        'optional_label': 'Optional',
        'no_params_label': '(No parameters)',
    }
}


# ============================================================================
# プロンプト変数管理
# ============================================================================

class PromptVariables:
    """
    プロンプトテンプレートで使用する変数の管理

    プロンプトテンプレート内の変数を一元管理し、
    テンプレートへの変数置換を提供します。
    """

    def __init__(self):
        """変数ストアの初期化"""
        self.variables: Dict[str, str] = {
            'tools_list': '',
            'language': 'ja',
            'response_format': 'json',
            'max_iterations': '10',
            'custom_instructions': '',
            'examples': ''
        }

    def set_variable(self, key: str, value: Any) -> None:
        """
        変数を設定

        Args:
            key: 変数名
            value: 変数の値
        """
        self.variables[key] = str(value)
        logger.debug(f"変数を設定: {key} = {value}")

    def get_variable(self, key: str, default: Any = None) -> Any:
        """
        変数を取得

        Args:
            key: 変数名
            default: デフォルト値

        Returns:
            変数の値（存在しない場合はデフォルト値）
        """
        return self.variables.get(key, default)

    def format_template(self, template: str) -> str:
        """
        テンプレート内の変数を置換

        Args:
            template: プロンプトテンプレート文字列

        Returns:
            変数が置換されたテンプレート
        """
        result = template
        for key, value in self.variables.items():
            placeholder = f"{{{key}}}"
            result = result.replace(placeholder, value)

        logger.debug(f"テンプレート変数を置換: {len(self.variables)}個")
        return result


# ============================================================================
# ツール情報の抽出と整形
# ============================================================================

def extract_tool_schema_info(tool: Dict[str, Any]) -> Dict[str, Any]:
    """
    ツールの JSON Schema から人間読みやすい情報を抽出

    Args:
        tool: ツール定義（JSON Schema形式）

    Returns:
        整理されたツール情報
        {
            'name': str,
            'description': str,
            'required_params': List[str],
            'optional_params': List[str],
            'param_descriptions': Dict[str, str],
            'example_usage': Dict[str, Any]
        }
    """
    name = tool.get('name', 'unknown')
    description = tool.get('description', '説明なし')

    # inputSchema から情報を抽出
    input_schema = tool.get('inputSchema', {})
    properties = input_schema.get('properties', {})
    required = input_schema.get('required', [])

    # パラメータ情報の整理
    param_descriptions = {}
    for param_name, param_info in properties.items():
        param_type = param_info.get('type', 'any')
        param_desc = param_info.get('description', '')
        param_descriptions[param_name] = f"({param_type}): {param_desc}"

    # 必須・任意パラメータの分類
    required_params = [p for p in required if p in properties]
    optional_params = [p for p in properties.keys() if p not in required]

    # 使用例の生成
    example_usage = {
        'tool': name,
        'arguments': {
            param: f"<{param}の値>"
            for param in required_params
        }
    }

    return {
        'name': name,
        'description': description,
        'required_params': required_params,
        'optional_params': optional_params,
        'param_descriptions': param_descriptions,
        'example_usage': example_usage
    }


def format_tools_list(
    tools: List[Dict[str, Any]],
    format_style: str = 'detailed',
    language: str = 'ja'
) -> str:
    """
    ツール一覧を見やすい形式でフォーマット

    Args:
        tools: ツールのリスト
        format_style: フォーマットスタイル（'detailed', 'concise', 'minimal'）
        language: 言語コード（'ja', 'en'）

    Returns:
        フォーマットされたツール一覧テキスト
    """
    if not tools:
        return "(利用可能なツールはありません)" if language == 'ja' else "(No tools available)"

    lang_config = LANGUAGE_CONFIGS.get(language, LANGUAGE_CONFIGS['ja'])
    tools_description = []

    for tool in tools:
        tool_info = extract_tool_schema_info(tool)

        if format_style == 'minimal':
            # 最小限の情報のみ
            tool_text = f"## {tool_info['name']}\n{tool_info['description']}"

        elif format_style == 'concise':
            # 簡潔な情報
            params_list = ', '.join(tool_info['required_params']) if tool_info['required_params'] else lang_config['no_params_label']
            tool_text = f"""## {tool_info['name']}
{tool_info['description']}
{lang_config['parameters_label']}: {params_list}"""

        else:  # 'detailed'
            # 詳細な情報
            params_lines = []

            # 必須パラメータ
            for param in tool_info['required_params']:
                desc = tool_info['param_descriptions'].get(param, '')
                params_lines.append(f"  - {param} ({lang_config['required_label']}): {desc}")

            # 任意パラメータ
            for param in tool_info['optional_params']:
                desc = tool_info['param_descriptions'].get(param, '')
                params_lines.append(f"  - {param} ({lang_config['optional_label']}): {desc}")

            params_text = "\n".join(params_lines) if params_lines else f"  {lang_config['no_params_label']}"

            # 使用例
            example_json = json.dumps(tool_info['example_usage'], ensure_ascii=False, indent=2)

            tool_text = f"""## {tool_info['name']}
{tool_info['description']}

{lang_config['parameters_label']}:
{params_text}

使用例:
```json
{example_json}
```"""

        tools_description.append(tool_text.strip())

    result = "\n\n".join(tools_description)
    logger.info(f"ツール一覧をフォーマット: {len(tools)}個のツール、スタイル={format_style}")
    return result


def generate_tools_section(
    tools: List[Dict[str, Any]],
    format_style: str = 'detailed',
    language: str = 'ja'
) -> str:
    """
    ツールレジストリからプロンプト用のツール説明を生成

    Args:
        tools: ツールのリスト
        format_style: フォーマットスタイル
        language: 言語コード

    Returns:
        ツールセクションのテキスト
    """
    return format_tools_list(tools, format_style, language)


# ============================================================================
# プロンプトビルダークラス
# ============================================================================

class PromptBuilder:
    """
    システムプロンプトの動的構築とテンプレート管理

    テンプレートファイルからプロンプトを読み込み、
    ツール情報やカスタム指示を動的に挿入してシステムプロンプトを構築します。
    """

    def __init__(self, template_path: Optional[str] = None):
        """
        初期化

        Args:
            template_path: プロンプトテンプレートファイルのパス
                          指定しない場合はデフォルトテンプレートを使用
        """
        self.template_path = template_path
        self.variables = PromptVariables()

        # デフォルトテンプレートディレクトリ
        self.templates_dir = Path(__file__).parent

        logger.info(f"PromptBuilder初期化: テンプレートディレクトリ={self.templates_dir}")

    def load_template(self, template_name: str = 'standard') -> str:
        """
        指定されたテンプレートを読み込み

        Args:
            template_name: テンプレート名（'standard', 'concise', 'detailed', 'debug'）

        Returns:
            テンプレート文字列

        Raises:
            FileNotFoundError: テンプレートファイルが見つからない場合
        """
        # テンプレートファイル名を取得
        template_file = PROMPT_TEMPLATES.get(template_name, PROMPT_TEMPLATES['standard'])
        template_path = self.templates_dir / template_file

        logger.info(f"テンプレート読み込み: {template_name} ({template_path})")

        if not template_path.exists():
            # フォールバック: デフォルトテンプレートを使用
            logger.warning(f"テンプレートファイルが見つかりません: {template_path}")
            logger.warning("デフォルトテンプレートを使用します")
            return self._get_default_template()

        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template = f.read()
            logger.debug(f"テンプレート読み込み成功: {len(template)}文字")
            return template
        except Exception as e:
            logger.error(f"テンプレート読み込みエラー: {str(e)}")
            logger.warning("デフォルトテンプレートを使用します")
            return self._get_default_template()

    def build_system_prompt(
        self,
        tools: List[Dict[str, Any]],
        language: str = 'ja',
        include_examples: bool = True,
        custom_instructions: Optional[str] = None,
        template_name: str = 'standard',
        format_style: str = 'detailed'
    ) -> str:
        """
        ツール情報を含むシステムプロンプトを構築

        Args:
            tools: ツールのリスト
            language: 言語コード（'ja', 'en'）
            include_examples: 使用例を含めるかどうか
            custom_instructions: カスタム指示（任意）
            template_name: 使用するテンプレート名
            format_style: ツール一覧のフォーマットスタイル

        Returns:
            構築されたシステムプロンプト
        """
        logger.info("=" * 60)
        logger.info("システムプロンプトを構築中...")
        logger.info(f"言語: {language}, テンプレート: {template_name}, スタイル: {format_style}")
        logger.info(f"ツール数: {len(tools)}")
        logger.info("=" * 60)

        # テンプレートの読み込み
        template = self.load_template(template_name)

        # ツール一覧の生成
        tools_list = generate_tools_section(tools, format_style, language)

        # 変数の設定
        self.variables.set_variable('tools_list', tools_list)
        self.variables.set_variable('language', language)

        # カスタム指示の追加
        if custom_instructions:
            custom_section = f"\n\n# 追加の指示\n\n{custom_instructions}"
            self.variables.set_variable('custom_instructions', custom_section)
        else:
            self.variables.set_variable('custom_instructions', '')

        # テンプレートの変数置換
        prompt = self.variables.format_template(template)

        logger.info(f"システムプロンプト構築完了: {len(prompt)}文字")
        return prompt.strip()

    def add_custom_instructions(
        self,
        base_prompt: str,
        instructions: str
    ) -> str:
        """
        カスタム指示をプロンプトに追加

        Args:
            base_prompt: ベースとなるプロンプト
            instructions: 追加する指示

        Returns:
            カスタム指示が追加されたプロンプト
        """
        custom_section = f"\n\n# 追加の指示\n\n{instructions}"
        result = base_prompt + custom_section

        logger.info(f"カスタム指示を追加: {len(instructions)}文字")
        return result

    def _get_default_template(self) -> str:
        """
        デフォルトテンプレートを返す（フォールバック用）

        Returns:
            デフォルトのシステムプロンプトテンプレート
        """
        return """あなたは有能なAIアシスタントです。
ユーザーの質問に答えるために、必要に応じて以下のツールを呼び出すことができます。

# 利用可能なツール

{tools_list}

# レスポンス形式

あなたのレスポンスは必ず以下のいずれかのJSON形式で返してください:

## 1. ツール呼び出し (tool_call)
```json
{{
  "kind": "tool_call",
  "tool": "ツール名",
  "arguments": {{"パラメータ名": "値"}}
}}
```

## 2. 最終回答 (final_answer)
```json
{{
  "kind": "final_answer",
  "content": "回答内容"
}}
```

# 重要な指示

1. レスポンスは必ずJSON形式で返してください
2. ツールを呼び出す場合は、正確なツール名とパラメータを指定してください
3. ツールの実行結果を受け取ったら、それを元に最終回答を生成してください
{custom_instructions}"""


# ============================================================================
# プロンプト最適化
# ============================================================================

def optimize_prompt_length(
    prompt: str,
    max_tokens: int = 4000,
    preserve_sections: Optional[List[str]] = None
) -> str:
    """
    プロンプトの長さを最適化

    プロンプトが長すぎる場合に、重要でない部分を短縮します。

    Args:
        prompt: 元のプロンプト
        max_tokens: 最大トークン数の目安
        preserve_sections: 保持するセクション名のリスト

    Returns:
        最適化されたプロンプト

    Note:
        現在は簡易的な文字数ベースの最適化を実装。
        将来的にはトークナイザーを使用した正確な最適化を検討。
    """
    if preserve_sections is None:
        preserve_sections = ['rules', 'format']

    # 簡易的に文字数で判定（1トークン ≒ 2文字と仮定）
    estimated_tokens = len(prompt) / 2

    if estimated_tokens <= max_tokens:
        logger.debug(f"プロンプト最適化不要: 推定トークン数={estimated_tokens:.0f}")
        return prompt

    logger.warning(f"プロンプトが長すぎます: 推定トークン数={estimated_tokens:.0f} > {max_tokens}")
    logger.warning("プロンプト最適化機能は未実装です")

    # TODO: 実際の最適化ロジックを実装
    # - 使用例の削減
    # - ツール説明の簡略化
    # - 重要でないセクションの削除

    return prompt


def measure_prompt_effectiveness(
    prompt: str,
    test_queries: List[str],
    expected_responses: List[str]
) -> Dict[str, float]:
    """
    プロンプトの効果測定（将来実装）

    Args:
        prompt: 評価対象のプロンプト
        test_queries: テストクエリのリスト
        expected_responses: 期待されるレスポンスのリスト

    Returns:
        評価メトリクス
        {
            'accuracy': float,  # 正確性
            'efficiency': float,  # 効率性
            'token_usage': float  # トークン使用量
        }

    Note:
        将来的な実装予定の機能です。
    """
    logger.warning("measure_prompt_effectiveness は未実装です")
    return {
        'accuracy': 0.0,
        'efficiency': 0.0,
        'token_usage': 0.0
    }


# ============================================================================
# 後方互換性のためのユーティリティ関数
# ============================================================================

def build_system_prompt(tools: List[Dict[str, Any]]) -> str:
    """
    ツール情報を含むシステムプロンプトを構築（後方互換性用）

    既存の loop.py の build_system_prompt() と同じインターフェースを提供します。

    Args:
        tools: ツールレジストリから取得したツール一覧

    Returns:
        システムプロンプト文字列
    """
    builder = PromptBuilder()
    return builder.build_system_prompt(
        tools=tools,
        language='ja',
        template_name='standard',
        format_style='detailed'
    )


# ============================================================================
# モジュールの公開インターフェース
# ============================================================================

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
