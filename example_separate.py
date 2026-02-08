"""
別々に実装したLoggerクラスの使用例とテストコード

SingleProcessLoggerとMultiProcessLoggerの両方の使用方法を示します。
"""

import time
import multiprocessing
from logger_separate import SingleProcessLogger, MultiProcessLogger


def test_single_process_logger():
    """シングルプロセスLoggerのテスト"""
    print("\n" + "="*60)
    print("SingleProcessLoggerのテスト")
    print("="*60)
    
    # ロガーの初期化
    logger_manager = SingleProcessLogger('logging_config.yaml')
    
    # 異なる名前のロガーを取得
    logger1 = logger_manager.get_logger('app')
    logger2 = logger_manager.get_logger('database')
    
    # ログ出力のテスト
    logger1.debug('デバッグメッセージ')
    logger1.info('情報メッセージ')
    logger1.warning('警告メッセージ')
    logger1.error('エラーメッセージ')
    logger1.critical('致命的なエラー')
    
    logger2.info('データベース接続を確立しました')
    logger2.warning('データベースの応答が遅いです')
    
    print("\nシングルプロセスLoggerのテスト完了")


def test_single_process_logger_with_context():
    """コンテキストマネージャーを使用したシングルプロセスLoggerのテスト"""
    print("\n" + "="*60)
    print("SingleProcessLogger（コンテキストマネージャー使用）のテスト")
    print("="*60)
    
    with SingleProcessLogger('logging_config.yaml') as logger_manager:
        logger = logger_manager.get_logger('context_test')
        logger.info('コンテキストマネージャー内でのログ出力')
        logger.info('これはクリーンな実装です')
    
    print("\nコンテキストマネージャーのテスト完了")


def worker_function(worker_id: int, log_queue: multiprocessing.Queue):
    """ワーカープロセスの処理"""
    # ワーカープロセス用のLoggerを作成
    worker_logger = MultiProcessLogger.from_queue('logging_config.yaml', log_queue)
    logger = worker_logger.get_logger(f'worker_{worker_id}')
    
    # ログ出力
    logger.info(f'ワーカー {worker_id} が開始しました')
    
    # 簡単な処理
    for i in range(3):
        logger.info(f'ワーカー {worker_id}: タスク {i+1} を処理中')
        time.sleep(0.1)
    
    logger.info(f'ワーカー {worker_id} が完了しました')


def test_multi_process_logger():
    """マルチプロセスLoggerのテスト"""
    print("\n" + "="*60)
    print("MultiProcessLoggerのテスト")
    print("="*60)
    
    # メインプロセス用のLoggerを作成
    main_logger = MultiProcessLogger('logging_config.yaml')
    logger = main_logger.get_logger('main')
    
    logger.info('マルチプロセスLoggerのテストを開始します')
    
    # 複数のワーカープロセスを起動
    processes = []
    num_workers = 3
    
    for i in range(num_workers):
        p = multiprocessing.Process(
            target=worker_function,
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
    print("\nマルチプロセスLoggerのテスト完了")


def test_multi_process_logger_with_context():
    """コンテキストマネージャーを使用したマルチプロセスLoggerのテスト"""
    print("\n" + "="*60)
    print("MultiProcessLogger（コンテキストマネージャー使用）のテスト")
    print("="*60)
    
    with MultiProcessLogger('logging_config.yaml') as main_logger:
        logger = main_logger.get_logger('main_context')
        logger.info('コンテキストマネージャーでマルチプロセスLoggerを使用')
        
        # ワーカープロセスを起動
        process = multiprocessing.Process(
            target=worker_function,
            args=(99, main_logger.get_queue())
        )
        process.start()
        process.join()
        
        logger.info('テスト完了')
    
    print("\nコンテキストマネージャー（マルチプロセス）のテスト完了")


def compare_implementations():
    """2つの実装の特徴を比較"""
    print("\n" + "="*60)
    print("実装パターンの比較")
    print("="*60)
    
    print("\n【SingleProcessLogger】")
    print("  - シンプルで軽量")
    print("  - デバッグが容易")
    print("  - オーバーヘッドが最小限")
    print("  - シングルプロセスアプリケーションに最適")
    
    print("\n【MultiProcessLogger】")
    print("  - マルチプロセス環境で安全")
    print("  - QueueHandlerとQueueListenerを使用")
    print("  - from_queue()メソッドでワーカーを作成")
    print("  - 並列処理アプリケーションに最適")
    
    print("\n【使い分けの指針】")
    print("  - シングルプロセスの場合: SingleProcessLoggerを使用")
    print("  - マルチプロセスの場合: MultiProcessLoggerを使用")
    print("  - 用途が明確なため、コードが読みやすく保守しやすい")


if __name__ == '__main__':
    # シングルプロセスのテスト
    test_single_process_logger()
    test_single_process_logger_with_context()
    
    # マルチプロセスのテスト
    test_multi_process_logger()
    test_multi_process_logger_with_context()
    
    # 実装パターンの比較
    compare_implementations()
    
    print("\n" + "="*60)
    print("すべてのテストが完了しました")
    print("="*60)
