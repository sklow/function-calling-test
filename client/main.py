#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Function Calling Test - Client Side メインエントリーポイント

このスクリプトはクライアントサイドのCLIインターフェースを提供します。
"""

import argparse
import logging
import sys
from pathlib import Path
from dotenv import load_dotenv
import os

# ロガーの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('client.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


def load_environment():
    """
    環境変数を読み込む

    .envファイルが存在する場合は読み込み、
    必要な環境変数が設定されているか確認する
    """
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        logger.info(f"環境変数を読み込みました: {env_path}")
    else:
        logger.warning(".envファイルが見つかりません。デフォルト値または環境変数を使用します。")

    # 環境変数の確認
    required_vars = ['OLLAMA_HOST', 'API_SERVER_HOST', 'MODEL_NAME']
    for var in required_vars:
        value = os.getenv(var)
        if value:
            logger.info(f"{var}: {value}")
        else:
            logger.warning(f"{var} が設定されていません")


def parse_arguments():
    """
    コマンドライン引数を解析する

    Returns:
        argparse.Namespace: 解析された引数
    """
    parser = argparse.ArgumentParser(
        description='Function Calling Test - Client CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='デバッグモードを有効化'
    )

    parser.add_argument(
        '--model',
        type=str,
        help='使用するモデル名（環境変数を上書き）'
    )

    parser.add_argument(
        '--prompt',
        type=str,
        help='実行するプロンプト'
    )

    parser.add_argument(
        '--mode',
        choices=['interactive', 'single'],
        default='interactive',
        help='実行モード: interactive（対話型）またはsingle（単発実行）'
    )

    return parser.parse_args()


def main():
    """
    メイン処理

    コマンドライン引数を解析し、環境変数を読み込み、
    オーケストレータを呼び出す（将来実装予定）
    """
    # 引数解析
    args = parse_arguments()

    # デバッグモードの設定
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("デバッグモードが有効化されました")

    # 環境変数の読み込み
    load_environment()

    # モデル名の上書き
    if args.model:
        os.environ['MODEL_NAME'] = args.model
        logger.info(f"モデル名を上書き: {args.model}")

    logger.info("=" * 60)
    logger.info("Function Calling Test - Client 起動")
    logger.info("=" * 60)

    # TODO: ここでオーケストレータを呼び出す
    # from orchestrator.main import Orchestrator
    # orchestrator = Orchestrator()
    #
    # if args.mode == 'interactive':
    #     orchestrator.run_interactive()
    # elif args.mode == 'single' and args.prompt:
    #     result = orchestrator.run_single(args.prompt)
    #     print(result)

    logger.info("将来的にオーケストレータがここで実行されます")
    logger.info("現在はスケルトン実装です")

    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        logger.info("\n中断されました")
        sys.exit(1)
    except Exception as e:
        logger.error(f"エラーが発生しました: {e}", exc_info=True)
        sys.exit(1)
