"""
統合LoggerクラスUnifiedLoggerの使用例とテストコード

シングルプロセスとマルチプロセスの両方に対応した
統合実装の使用方法を示します。
"""

import time
import multiprocessing
from logger_unified import UnifiedLogger, LoggerMode


def test_unified_single_process():
    """統合Logger（シングルプロセスモード）のテスト"""
    print("\n" + "="*60)
    print("UnifiedLogger（シングルプロセスモード）のテスト")
    print("="*60)
    
    # シングルプロセスモードで初期化
    logger_manager = UnifiedLogger('logging_config.yaml', use_multiprocessing=False)
    
    print(f"モード: {logger_manager.get_mode().value}")
    
    # ロガーの取得とログ出力
    logger = logger_manager.get_logger('unified_single')
    logger.info('シングルプロセスモードでログ出力')
    logger.warning('このモードではQueueを使用しません')
    logger.error('シンプルで効率的です')
    
    print("\nシングルプロセスモードのテスト完了")


def unified_worker_function(worker_id: int, log_queue: multiprocessing.Queue):
    """統合Logger用のワーカープロセス"""
    # ワーカープロセス用のLoggerを作成
    worker_logger = UnifiedLogger(
        'logging_config.yaml',
        use_multiprocessing=True,
        log_queue=log_queue
    )
    
    print(f"ワーカー {worker_id} のモード: {worker_logger.get_mode().value}")
    
    logger = worker_logger.get_logger(f'unified_worker_{worker_id}')
    
    # ログ出力
    logger.info(f'ワーカー {worker_id} が開始しました')
    
    for i in range(3):
        logger.info(f'ワーカー {worker_id}: タスク {i+1} を処理中')
        time.sleep(0.1)
    
    logger.info(f'ワーカー {worker_id} が完了しました')


def test_unified_multi_process():
    """統合Logger（マルチプロセスモード）のテスト"""
    print("\n" + "="*60)
    print("UnifiedLogger（マルチプロセスモード）のテスト")
    print("="*60)
    
    # マルチプロセスモードで初期化
    main_logger = UnifiedLogger('logging_config.yaml', use_multiprocessing=True)
    
    print(f"メインプロセスのモード: {main_logger.get_mode().value}")
    
    logger = main_logger.get_logger('unified_main')
    logger.info('マルチプロセスモードでテストを開始します')
    
    # 複数のワーカープロセスを起動
    processes = []
    num_workers = 3
    
    for i in range(num_workers):
        p = multiprocessing.Process(
            target=unified_worker_function,
            args=(i, main_logger.get_queue())
        )
        processes.append(p)
        p.start()
        logger.info(f'ワーカープロセス {i} を起動しました')
    
    # すべてのプロセスが完了するのを待つ
    for i, p in enumerate(processes):
        p.join()
        logger.info(f'ワーカープロセス {i} が終了しました')
    
    logger.info('すべてのワーカーが完了しました')
    
    # クリーンアップ
    main_logger.stop()
    print("\nマルチプロセスモードのテスト完了")


def test_mode_switching():
    """動作モードの切り替えテスト"""
    print("\n" + "="*60)
    print("UnifiedLogger モード切り替えのテスト")
    print("="*60)
    
    # シングルプロセスモード
    single_logger = UnifiedLogger('logging_config.yaml', use_multiprocessing=False)
    print(f"シングルプロセスモード: {single_logger.get_mode()}")
    logger1 = single_logger.get_logger('mode_test_single')
    logger1.info('シングルプロセスモードで動作中')
    
    # マルチプロセスモード（メイン）
    multi_main = UnifiedLogger('logging_config.yaml', use_multiprocessing=True)
    print(f"マルチプロセスモード（メイン）: {multi_main.get_mode()}")
    logger2 = multi_main.get_logger('mode_test_main')
    logger2.info('マルチプロセスモード（メイン）で動作中')
    
    # マルチプロセスモード（ワーカー）
    multi_worker = UnifiedLogger(
        'logging_config.yaml',
        use_multiprocessing=True,
        log_queue=multi_main.get_queue()
    )
    print(f"マルチプロセスモード（ワーカー）: {multi_worker.get_mode()}")
    logger3 = multi_worker.get_logger('mode_test_worker')
    logger3.info('マルチプロセスモード（ワーカー）で動作中')
    
    # クリーンアップ
    multi_main.stop()
    
    print("\nモード切り替えのテスト完了")


def test_context_manager_both_modes():
    """コンテキストマネージャーを使用した両モードのテスト"""
    print("\n" + "="*60)
    print("UnifiedLogger コンテキストマネージャーのテスト")
    print("="*60)
    
    # シングルプロセスモード
    print("\n【シングルプロセスモード】")
    with UnifiedLogger('logging_config.yaml') as logger_manager:
        logger = logger_manager.get_logger('context_single')
        logger.info('コンテキストマネージャー（シングル）でログ出力')
    
    # マルチプロセスモード
    print("\n【マルチプロセスモード】")
    with UnifiedLogger('logging_config.yaml', use_multiprocessing=True) as main_logger:
        logger = main_logger.get_logger('context_multi')
        logger.info('コンテキストマネージャー（マルチ）でログ出力')
        
        # ワーカープロセスを起動
        p = multiprocessing.Process(
            target=unified_worker_function,
            args=(100, main_logger.get_queue())
        )
        p.start()
        p.join()
    
    print("\nコンテキストマネージャーのテスト完了")


def compare_unified_features():
    """統合実装の特徴を説明"""
    print("\n" + "="*60)
    print("UnifiedLoggerの特徴")
    print("="*60)
    
    print("\n【統合実装のメリット】")
    print("  - 単一のクラスで両方のモードに対応")
    print("  - use_multiprocessingフラグで動作を切り替え")
    print("  - LoggerModeで現在のモードを明示的に管理")
    print("  - コードの一貫性が保たれる")
    
    print("\n【動作モード】")
    print("  1. SINGLE_PROCESS: シングルプロセス専用")
    print("  2. MULTI_PROCESS_MAIN: マルチプロセス（メイン）")
    print("  3. MULTI_PROCESS_WORKER: マルチプロセス（ワーカー）")
    
    print("\n【使用シーン】")
    print("  - 開発時はシングル、本番はマルチなど柔軟に切り替え")
    print("  - 環境変数で動作モードを制御できる")
    print("  - テストが容易（モックやスタブが不要）")


def compare_separate_vs_unified():
    """別々の実装と統合実装の比較"""
    print("\n" + "="*60)
    print("別々の実装 vs 統合実装の比較")
    print("="*60)
    
    print("\n【別々の実装（logger_separate.py）】")
    print("  ✓ シンプルで理解しやすい")
    print("  ✓ 各クラスが特定の用途に最適化")
    print("  ✓ コードが短く、デバッグが容易")
    print("  ✓ SingleProcessLoggerとMultiProcessLoggerを使い分け")
    print("  - 用途ごとにクラスを選択する必要がある")
    
    print("\n【統合実装（logger_unified.py）】")
    print("  ✓ 単一のインターフェースで両方のモードに対応")
    print("  ✓ モードの切り替えが簡単（フラグ1つ）")
    print("  ✓ コードの一貫性が保たれる")
    print("  ✓ 環境に応じた動的な切り替えが可能")
    print("  - 内部実装がやや複雑")
    
    print("\n【推奨される使い方】")
    print("  - 用途が明確な場合: 別々の実装（logger_separate.py）")
    print("  - 柔軟性が必要な場合: 統合実装（logger_unified.py）")
    print("  - チーム開発: 要件に応じて選択")


if __name__ == '__main__':
    # シングルプロセスモードのテスト
    test_unified_single_process()
    
    # マルチプロセスモードのテスト
    test_unified_multi_process()
    
    # モード切り替えのテスト
    test_mode_switching()
    
    # コンテキストマネージャーのテスト
    test_context_manager_both_modes()
    
    # 統合実装の特徴
    compare_unified_features()
    
    # 別々の実装との比較
    compare_separate_vs_unified()
    
    print("\n" + "="*60)
    print("すべてのテストが完了しました")
    print("="*60)
