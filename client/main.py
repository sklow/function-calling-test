#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Function Calling Test - Client Side メインエントリーポイント

このスクリプトはクライアントサイドのCLIインターフェースを提供します。
ユーザーが対話的にLLMとツール呼び出しを実行できる機能を提供します。
"""

import argparse
import logging
import sys
import os
import time
import traceback
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# ロガー設定は後で setup_logging() で初期化
logger = logging.getLogger(__name__)


def load_environment_config() -> Dict[str, Any]:
    """
    環境変数と .env ファイルから設定を読み込み

    Returns:
        設定の辞書
    """
    # .env ファイルの読み込み
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        logger.debug(f"環境変数を読み込みました: {env_path}")
    else:
        logger.debug(".envファイルが見つかりません。デフォルト値または環境変数を使用します。")

    # デフォルト設定
    config = {
        'ollama_host': os.getenv('OLLAMA_HOST', 'http://localhost:11434'),
        'api_server_host': os.getenv('API_SERVER_HOST', 'http://localhost:5000'),
        'model_name': os.getenv('MODEL_NAME', 'gemma3:4b'),
        'max_retries': int(os.getenv('MAX_RETRIES', '3')),
        'timeout_seconds': int(os.getenv('TIMEOUT_SECONDS', '30')),
    }

    return config


def parse_arguments():
    """
    コマンドライン引数を解析する

    Returns:
        argparse.Namespace: 解析された引数
    """
    parser = argparse.ArgumentParser(
        description='Gemma 3 Function Calling クライアント',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python main.py "東京の天気を教えて"
  python main.py --interactive
  python main.py --model gemma3:12b "複雑な質問"
  python main.py --debug --max-iterations 15 "詳細な分析が必要な質問"
"""
    )

    # 位置引数
    parser.add_argument(
        'query',
        nargs='?',
        help='ユーザーの質問（省略時は対話モード）'
    )

    # オプション引数
    parser.add_argument(
        '-i', '--interactive',
        action='store_true',
        help='対話モード'
    )

    parser.add_argument(
        '-m', '--model',
        default='gemma3:4b',
        help='使用するLLMモデル（デフォルト: gemma3:4b）'
    )

    parser.add_argument(
        '--api-base',
        default='http://localhost:5000',
        help='APIサーバーのURL（デフォルト: http://localhost:5000）'
    )

    parser.add_argument(
        '--ollama-host',
        default='http://localhost:11434',
        help='OllamaサーバーのURL（デフォルト: http://localhost:11434）'
    )

    parser.add_argument(
        '--max-iterations',
        type=int,
        default=10,
        help='最大反復回数（デフォルト: 10）'
    )

    parser.add_argument(
        '--timeout',
        type=int,
        default=30,
        help='タイムアウト秒数（デフォルト: 30）'
    )

    parser.add_argument(
        '--template',
        default='standard',
        choices=['standard', 'concise', 'detailed', 'debug'],
        help='プロンプトテンプレート（デフォルト: standard）'
    )

    parser.add_argument(
        '-d', '--debug',
        action='store_true',
        help='デバッグモード'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='詳細ログ'
    )

    parser.add_argument(
        '--log-file',
        help='ログファイルのパス'
    )

    return parser.parse_args()


def setup_logging(args: argparse.Namespace) -> None:
    """
    ログ設定の初期化

    Args:
        args: コマンドライン引数
    """
    # ログレベルの決定
    if args.debug:
        log_level = logging.DEBUG
    elif args.verbose:
        log_level = logging.INFO
    else:
        log_level = logging.WARNING

    # フォーマッターの設定
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # コンソールハンドラー
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)

    # ファイルハンドラー（指定時）
    handlers = [console_handler]

    if args.log_file:
        file_handler = logging.FileHandler(args.log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)
        handlers.append(file_handler)

    # ルートロガーの設定
    logging.basicConfig(
        level=log_level,
        handlers=handlers,
        force=True  # 既存の設定を上書き
    )


def check_system_health(args: argparse.Namespace) -> bool:
    """
    システムの動作確認

    Args:
        args: コマンドライン引数

    Returns:
        すべてのチェックが成功した場合はTrue、それ以外はFalse
    """
    from client.llm.ollama_client import check_ollama_health, list_models
    from client.api.registry import fetch_tools, RegistryError

    checks = []
    all_ok = True

    # 1. Ollama サーバーの接続チェック
    try:
        ollama_ok = check_ollama_health(args.ollama_host)
        status = "✅" if ollama_ok else "❌"
        print(f"{status} Ollama サーバー: {'OK' if ollama_ok else 'NG'}")
        if not ollama_ok:
            all_ok = False
    except Exception as e:
        print(f"❌ Ollama サーバー: エラー - {e}")
        all_ok = False

    # 2. モデル確認
    try:
        models = list_models(args.ollama_host)
        if args.model in models:
            print(f"✅ モデル確認: {args.model} は利用可能です")
        else:
            print(f"❌ モデル確認: {args.model} が見つかりません")
            print(f"   利用可能なモデル: {', '.join(models)}")
            all_ok = False
    except Exception as e:
        print(f"❌ モデル確認: エラー - {e}")
        all_ok = False

    # 3. APIサーバーの接続チェック
    try:
        tools_data = fetch_tools(api_base=args.api_base, use_cache=False, timeout=5)
        tools_count = tools_data.get('count', 0)
        print(f"✅ APIサーバー: OK ({tools_count}個のツールが利用可能)")
    except RegistryError as e:
        print(f"❌ APIサーバー: エラー - {e}")
        all_ok = False
    except Exception as e:
        print(f"❌ APIサーバー: 予期しないエラー - {e}")
        all_ok = False

    return all_ok


def process_query(query: str, args: argparse.Namespace) -> str:
    """
    質問を処理し、回答を取得

    Args:
        query: ユーザーの質問
        args: コマンドライン引数

    Returns:
        回答文字列

    Raises:
        Exception: 処理中のエラー
    """
    from client.orchestrator.loop import run_loop

    # 開始時刻の記録
    start_time = time.time()

    # デバッグ情報の表示
    if args.debug or args.verbose:
        print(f"🔧 使用モデル: {args.model}")
        print(f"🔧 APIサーバー: {args.api_base}")
        print(f"🔧 Ollamaサーバー: {args.ollama_host}")
        print(f"🔧 最大反復回数: {args.max_iterations}")
        print(f"🔧 プロンプトテンプレート: {args.template}")
        print()

    try:
        # オーケストレーションループの実行
        answer = run_loop(
            user_query=query,
            model=args.model,
            api_base=args.api_base,
            ollama_host=args.ollama_host,
            max_iterations=args.max_iterations,
            timeout=args.timeout
        )

        # 実行時間の表示
        elapsed_time = time.time() - start_time
        if args.verbose:
            print(f"\n⏱️ 実行時間: {elapsed_time:.2f}秒")

        return answer

    except Exception as e:
        logger.error(f"クエリ処理中にエラーが発生: {str(e)}")
        raise


def get_multiline_input() -> str:
    """
    複数行入力を取得

    Returns:
        入力されたテキスト
    """
    print("💭 質問を入力してください (複数行可、'END' または Ctrl+D で終了):")
    lines = []

    try:
        while True:
            if not lines:
                line = input(">>> ")
            else:
                line = input("... ")

            if line.strip().upper() == 'END':
                break

            lines.append(line)

    except EOFError:
        # Ctrl+D が押された
        pass

    return '\n'.join(lines).strip()


def show_help():
    """ヘルプメッセージを表示"""
    print("""
利用可能なコマンド:
  /help       - このヘルプを表示
  /quit       - プログラムを終了
  /debug      - デバッグモードの切り替え
  /status     - システムステータスを表示
  /tools      - 利用可能なツール一覧を表示
  /clear      - 画面をクリア
""")


def show_status(args: argparse.Namespace):
    """システムステータスを表示"""
    print("\n=== システムステータス ===")
    print(f"モデル: {args.model}")
    print(f"APIサーバー: {args.api_base}")
    print(f"Ollamaサーバー: {args.ollama_host}")
    print(f"最大反復回数: {args.max_iterations}")
    print(f"タイムアウト: {args.timeout}秒")
    print(f"デバッグモード: {'有効' if args.debug else '無効'}")
    print()


def show_available_tools(args: argparse.Namespace):
    """利用可能なツール一覧を表示"""
    from client.api.registry import list_available_tools, RegistryError

    try:
        print("\n=== 利用可能なツール ===")
        tool_names = list_available_tools(api_base=args.api_base)
        for idx, name in enumerate(tool_names, 1):
            print(f"  {idx}. {name}")
        print()
    except RegistryError as e:
        print(f"❌ ツール一覧の取得に失敗しました: {e}\n")


def clear_screen():
    """画面をクリア"""
    os.system('cls' if os.name == 'nt' else 'clear')


def toggle_debug_mode(args: argparse.Namespace):
    """デバッグモードを切り替え"""
    args.debug = not args.debug
    new_level = logging.DEBUG if args.debug else logging.WARNING
    logging.getLogger().setLevel(new_level)
    print(f"デバッグモード: {'有効' if args.debug else '無効'}\n")


def handle_command(command: str, args: argparse.Namespace) -> bool:
    """
    内蔵コマンドの処理

    Args:
        command: コマンド文字列
        args: コマンドライン引数

    Returns:
        プログラムを終了する場合はTrue、継続する場合はFalse
    """
    cmd = command.strip().lower()

    if cmd == '/help':
        show_help()
    elif cmd == '/quit':
        print("👋 終了します...")
        return True
    elif cmd == '/debug':
        toggle_debug_mode(args)
    elif cmd == '/status':
        show_status(args)
    elif cmd == '/tools':
        show_available_tools(args)
    elif cmd == '/clear':
        clear_screen()
    else:
        print(f"❓ 不明なコマンド: {command}")
        print("使用可能なコマンド: /help, /quit, /debug, /status, /tools, /clear")

    return False


def interactive_mode(args: argparse.Namespace) -> None:
    """
    対話モードでの連続的な質問応答

    Args:
        args: コマンドライン引数
    """
    print("=" * 60)
    print("🤖 Gemma 3 Function Calling クライアント")
    print("=" * 60)
    print("複数行入力: 'END' または Ctrl+D で入力終了")
    print("コマンド: /help でヘルプ、/quit で終了")
    print("-" * 60)
    print()

    session_count = 0

    while True:
        try:
            # 複数行入力の処理
            query = get_multiline_input()

            if query.strip() == '':
                continue

            # 特別なコマンドの処理
            if query.startswith('/'):
                should_quit = handle_command(query, args)
                if should_quit:
                    break
                continue

            # 通常の質問の処理
            session_count += 1
            print(f"\n[セッション {session_count}]")

            answer = process_query(query, args)
            print(f"\n🤖 回答: {answer}\n")
            print("-" * 60)

        except KeyboardInterrupt:
            print("\n\n👋 終了します...")
            break
        except Exception as e:
            print(f"\n❌ エラーが発生しました: {e}\n")
            if args.debug:
                traceback.print_exc()


def single_query_mode(query: str, args: argparse.Namespace) -> None:
    """
    単発の質問を処理

    Args:
        query: ユーザーの質問
        args: コマンドライン引数
    """
    print(f"💭 質問: {query}\n")

    try:
        answer = process_query(query, args)
        print(f"\n🤖 回答: {answer}\n")

    except KeyboardInterrupt:
        print("\n⏸️ 処理を中断しました")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}\n")
        if args.debug:
            traceback.print_exc()
        sys.exit(1)


def main():
    """
    メイン処理

    コマンドライン引数を解析し、環境変数を読み込み、
    オーケストレーションループを実行します。
    """
    # 引数解析
    args = parse_arguments()

    # ログ設定
    setup_logging(args)

    # 環境設定の読み込み
    config = load_environment_config()

    # コマンドライン引数で環境変数を上書き
    if not args.api_base or args.api_base == 'http://localhost:5000':
        args.api_base = config['api_server_host']
    if not args.ollama_host or args.ollama_host == 'http://localhost:11434':
        args.ollama_host = config['ollama_host']
    if args.model == 'gemma3:4b':  # デフォルト値の場合のみ上書き
        args.model = config['model_name']

    # ウェルカムメッセージ
    if args.verbose or args.debug:
        print("=" * 60)
        print("Gemma 3 Function Calling クライアント - 起動")
        print("=" * 60)
        print()

    # システムヘルスチェック（デバッグモードまたは詳細モード時のみ）
    if args.debug or args.verbose:
        print("システムヘルスチェックを実行中...\n")
        health_ok = check_system_health(args)
        print()

        if not health_ok:
            print("⚠️ 一部のシステムチェックが失敗しました。")
            print("   継続する場合はEnterキーを押してください。")
            input()

    # モード判定と実行
    if args.interactive or not args.query:
        # 対話モード
        interactive_mode(args)
    else:
        # 単発質問モード
        single_query_mode(args.query, args)

    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n👋 中断されました")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 致命的なエラーが発生しました: {e}")
        traceback.print_exc()
        sys.exit(1)
