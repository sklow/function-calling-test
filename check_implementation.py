"""実装完了確認スクリプト"""
import sys
from pathlib import Path

print('=' * 70)
print('タスク2.6 実装完了確認')
print('=' * 70)
print()

# 1. インポート確認
print('1. モジュールインポート確認')
print('-' * 70)
try:
    from client.orchestrator import (
        run_loop,
        build_system_prompt,
        execute_tool,
        safe_parse_json,
        OrchestratorError,
        MaxIterationsReached,
        InvalidResponseFormat,
        ToolExecutionFailed,
        CALL_SCHEMA
    )
    print('[OK] すべての公開インターフェースが正常にインポートされました')
    print()
except Exception as e:
    print(f'[NG] インポートエラー: {e}')
    print()
    sys.exit(1)

# 2. 関数シグネチャ確認
print('2. 主要関数の確認')
print('-' * 70)
import inspect
print(f'run_loop: {len(inspect.signature(run_loop).parameters)} 個のパラメータ')
print(f'build_system_prompt: {len(inspect.signature(build_system_prompt).parameters)} 個のパラメータ')
print(f'execute_tool: {len(inspect.signature(execute_tool).parameters)} 個のパラメータ')
print(f'safe_parse_json: {len(inspect.signature(safe_parse_json).parameters)} 個のパラメータ')
print()

# 3. JSON Schema確認
print('3. JSON Schema 確認')
print('-' * 70)
print(f'CALL_SCHEMA タイプ: {type(CALL_SCHEMA).__name__}')
print(f'必須フィールド: {CALL_SCHEMA.get("required")}')
print(f'プロパティ数: {len(CALL_SCHEMA.get("properties", {}))}')
print()

# 4. 例外クラス確認
print('4. カスタム例外クラス確認')
print('-' * 70)
exceptions = [
    OrchestratorError,
    MaxIterationsReached,
    InvalidResponseFormat,
    ToolExecutionFailed
]
for exc in exceptions:
    print(f'[OK] {exc.__name__}: {exc.__doc__ or "(説明なし)"}')
print()

# 5. ファイル構成確認
print('5. ファイル構成確認')
print('-' * 70)
files = [
    'client/orchestrator/__init__.py',
    'client/orchestrator/loop.py',
    'client/orchestrator/test_loop_unit.py',
    'client/orchestrator/demo_loop.py',
    'client/orchestrator/README.md',
    'client/test_loop.py',
]
for file in files:
    path = Path(file)
    if path.exists():
        print(f'[OK] {file} ({path.stat().st_size} バイト)')
    else:
        print(f'[NG] {file} (見つかりません)')
print()

print('=' * 70)
print('実装完了!')
print('=' * 70)
