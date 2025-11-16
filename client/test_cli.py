#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLIインターフェースの単体テスト

main.pyの各機能が正しく実装されているかを確認します。
"""

import sys
import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from client.main import (
    load_environment_config,
    parse_arguments,
    setup_logging,
    get_multiline_input,
    show_help,
    handle_command
)


class TestEnvironmentConfig(unittest.TestCase):
    """環境設定のテスト"""

    def test_load_environment_config_default(self):
        """デフォルト設定が正しく読み込まれることを確認"""
        config = load_environment_config()

        # デフォルト値の確認
        self.assertIn('ollama_host', config)
        self.assertIn('api_server_host', config)
        self.assertIn('model_name', config)
        self.assertIn('max_retries', config)
        self.assertIn('timeout_seconds', config)

        # 型の確認
        self.assertIsInstance(config['max_retries'], int)
        self.assertIsInstance(config['timeout_seconds'], int)


class TestArgumentParsing(unittest.TestCase):
    """コマンドライン引数解析のテスト"""

    def test_parse_arguments_default(self):
        """デフォルト引数のテスト"""
        with patch('sys.argv', ['main.py']):
            args = parse_arguments()

            self.assertIsNone(args.query)
            self.assertFalse(args.interactive)
            self.assertEqual(args.model, 'gemma3:4b')
            self.assertEqual(args.api_base, 'http://localhost:5000')
            self.assertEqual(args.ollama_host, 'http://localhost:11434')
            self.assertEqual(args.max_iterations, 10)
            self.assertEqual(args.timeout, 30)
            self.assertFalse(args.debug)
            self.assertFalse(args.verbose)

    def test_parse_arguments_with_query(self):
        """質問付き引数のテスト"""
        with patch('sys.argv', ['main.py', '東京の天気は?']):
            args = parse_arguments()

            self.assertEqual(args.query, '東京の天気は?')
            self.assertFalse(args.interactive)

    def test_parse_arguments_interactive(self):
        """対話モード引数のテスト"""
        with patch('sys.argv', ['main.py', '--interactive']):
            args = parse_arguments()

            self.assertTrue(args.interactive)

    def test_parse_arguments_with_options(self):
        """各種オプション引数のテスト"""
        with patch('sys.argv', [
            'main.py',
            '--model', 'gemma3:12b',
            '--max-iterations', '20',
            '--timeout', '60',
            '--debug',
            '--verbose'
        ]):
            args = parse_arguments()

            self.assertEqual(args.model, 'gemma3:12b')
            self.assertEqual(args.max_iterations, 20)
            self.assertEqual(args.timeout, 60)
            self.assertTrue(args.debug)
            self.assertTrue(args.verbose)


class TestLoggingSetup(unittest.TestCase):
    """ログ設定のテスト"""

    def test_setup_logging_debug(self):
        """デバッグモードのログ設定テスト"""
        mock_args = MagicMock()
        mock_args.debug = True
        mock_args.verbose = False
        mock_args.log_file = None

        # エラーが発生しないことを確認
        try:
            setup_logging(mock_args)
        except Exception as e:
            self.fail(f"setup_logging raised {e}")

    def test_setup_logging_verbose(self):
        """詳細モードのログ設定テスト"""
        mock_args = MagicMock()
        mock_args.debug = False
        mock_args.verbose = True
        mock_args.log_file = None

        # エラーが発生しないことを確認
        try:
            setup_logging(mock_args)
        except Exception as e:
            self.fail(f"setup_logging raised {e}")


class TestMultilineInput(unittest.TestCase):
    """複数行入力のテスト"""

    @patch('builtins.input', side_effect=['東京の天気は?', 'END'])
    def test_get_multiline_input_single_line(self, mock_input):
        """単一行入力のテスト"""
        result = get_multiline_input()
        self.assertEqual(result, '東京の天気は?')

    @patch('builtins.input', side_effect=['1行目', '2行目', 'END'])
    def test_get_multiline_input_multi_lines(self, mock_input):
        """複数行入力のテスト"""
        result = get_multiline_input()
        self.assertEqual(result, '1行目\n2行目')

    @patch('builtins.input', side_effect=EOFError)
    def test_get_multiline_input_eof(self, mock_input):
        """EOF入力のテスト"""
        result = get_multiline_input()
        self.assertEqual(result, '')


class TestCommandHandling(unittest.TestCase):
    """コマンド処理のテスト"""

    def test_show_help(self):
        """ヘルプ表示のテスト"""
        # エラーが発生しないことを確認
        try:
            show_help()
        except Exception as e:
            self.fail(f"show_help raised {e}")

    def test_handle_command_help(self):
        """ヘルプコマンドのテスト"""
        mock_args = MagicMock()
        result = handle_command('/help', mock_args)
        self.assertFalse(result)  # 終了しない

    def test_handle_command_quit(self):
        """終了コマンドのテスト"""
        mock_args = MagicMock()
        result = handle_command('/quit', mock_args)
        self.assertTrue(result)  # 終了する

    def test_handle_command_unknown(self):
        """不明なコマンドのテスト"""
        mock_args = MagicMock()
        result = handle_command('/unknown', mock_args)
        self.assertFalse(result)  # 終了しない


class TestIntegration(unittest.TestCase):
    """統合テスト"""

    def test_main_module_imports(self):
        """main.pyのインポートが成功することを確認"""
        try:
            import client.main
        except ImportError as e:
            self.fail(f"Failed to import client.main: {e}")

    def test_all_functions_defined(self):
        """必要な関数がすべて定義されていることを確認"""
        import client.main

        required_functions = [
            'load_environment_config',
            'parse_arguments',
            'setup_logging',
            'check_system_health',
            'process_query',
            'get_multiline_input',
            'show_help',
            'show_status',
            'show_available_tools',
            'handle_command',
            'interactive_mode',
            'single_query_mode',
            'main'
        ]

        for func_name in required_functions:
            self.assertTrue(
                hasattr(client.main, func_name),
                f"Function '{func_name}' is not defined in client.main"
            )


if __name__ == '__main__':
    # テスト実行
    print("=" * 60)
    print("CLIインターフェース単体テスト")
    print("=" * 60)
    print()

    # テストスイート作成
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 各テストクラスを追加
    suite.addTests(loader.loadTestsFromTestCase(TestEnvironmentConfig))
    suite.addTests(loader.loadTestsFromTestCase(TestArgumentParsing))
    suite.addTests(loader.loadTestsFromTestCase(TestLoggingSetup))
    suite.addTests(loader.loadTestsFromTestCase(TestMultilineInput))
    suite.addTests(loader.loadTestsFromTestCase(TestCommandHandling))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))

    # テスト実行
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 結果サマリー
    print()
    print("=" * 60)
    print("テスト結果サマリー")
    print("=" * 60)
    print(f"実行テスト数: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失敗: {len(result.failures)}")
    print(f"エラー: {len(result.errors)}")
    print()

    # 終了コード
    sys.exit(0 if result.wasSuccessful() else 1)
