"""
Logger クラスの使用例

シングルプロセスとマルチプロセスの両方の使用例を示します。
"""

import time
import multiprocessing
from pathlib import Path
from logger import Logger


def worker_process(logger_config_path: str, log_queue: multiprocessing.Queue, process_id: int):
    """
    マルチプロセスで実行されるワーカー関数
    
    Args:
        logger_config_path: ログ設定ファイルのパス
        log_queue: メインプロセスから渡された共通のQueue
        process_id: プロセスID
    """
    # 共通のQueueを使ってLoggerインスタンスを作成
    logger_manager = Logger(logger_config_path, use_multiprocessing=True, log_queue=log_queue)
    logger = logger_manager.get_logger(f'worker_{process_id}')
    
    # ログ出力
    logger.info(f'プロセス {process_id} が開始しました')
    
    for i in range(5):
        logger.debug(f'プロセス {process_id} - 処理 {i+1}/5')
        time.sleep(0.1)
    
    logger.warning(f'プロセス {process_id} で警告が発生しました')
    logger.info(f'プロセス {process_id} が完了しました')
    
    # ワーカープロセスではstopを呼ばない（Listenerの所有者ではないため）


def example_single_process():
    """シングルプロセスでの使用例"""
    print("=== シングルプロセス例 ===")
    
    # Loggerインスタンスの作成
    logger_manager = Logger('logging_config.yaml', use_multiprocessing=False)
    
    # ロガーの取得
    logger = logger_manager.get_logger('single_process_app')
    
    # ログ出力
    logger.debug('これはDEBUGレベルのログです')
    logger.info('これはINFOレベルのログです')
    logger.warning('これはWARNINGレベルのログです')
    logger.error('これはERRORレベルのログです')
    logger.critical('これはCRITICALレベルのログです')
    
    # 処理の例
    logger.info('処理を開始します')
    for i in range(3):
        logger.info(f'ステップ {i+1}/3 を実行中')
        time.sleep(0.5)
    logger.info('処理が完了しました')
    
    print("シングルプロセス例が完了しました\n")


def example_multiprocessing():
    """マルチプロセスでの使用例（正しいパターン）"""
    print("=== マルチプロセス例 ===")
    
    config_path = 'logging_config.yaml'
    num_processes = 4
    
    # メインプロセスでLoggerインスタンスを作成（QueueとListenerを起動）
    main_logger_manager = Logger(config_path, use_multiprocessing=True)
    
    # メインプロセスからもログ出力可能
    main_logger = main_logger_manager.get_logger('main_process')
    main_logger.info(f'{num_processes}個のワーカープロセスを起動します')
    
    # プロセスのリスト
    processes = []
    
    # 複数のプロセスを起動（共通のQueueを渡す）
    for i in range(num_processes):
        p = multiprocessing.Process(
            target=worker_process,
            args=(config_path, main_logger_manager.log_queue, i)
        )
        p.start()
        processes.append(p)
    
    # すべてのプロセスの完了を待つ
    for p in processes:
        p.join()
    
    main_logger.info('すべてのワーカープロセスが完了しました')
    
    # メインプロセスでListenerを停止
    main_logger_manager.stop()
    
    print("マルチプロセス例が完了しました\n")


def example_context_manager():
    """コンテキストマネージャーでの使用例"""
    print("=== コンテキストマネージャー例 ===")
    
    # with文を使用して自動的にクリーンアップ
    with Logger('logging_config.yaml', use_multiprocessing=False) as logger_manager:
        logger = logger_manager.get_logger('context_manager_app')
        logger.info('コンテキストマネージャーを使用したログ出力')
        logger.info('ブロックを抜けると自動的にクリーンアップされます')
    
    print("コンテキストマネージャー例が完了しました\n")


def example_json_config():
    """JSON設定ファイルでの使用例"""
    print("=== JSON設定ファイル例 ===")
    
    logger_manager = Logger('logging_config.json', use_multiprocessing=False)
    logger = logger_manager.get_logger('json_config_app')
    
    logger.info('JSON形式の設定ファイルを使用しています')
    logger.debug('DEBUGログも出力されます')
    
    print("JSON設定ファイル例が完了しました\n")


def main():
    """メイン関数"""
    # logsディレクトリを作成
    Path('logs').mkdir(exist_ok=True)
    
    # 各例を実行
    example_single_process()
    example_context_manager()
    example_json_config()
    
    # マルチプロセス例
    # 注意: Windowsでは __main__ ガード内で実行する必要があります
    if __name__ == '__main__':
        example_multiprocessing()


if __name__ == '__main__':
    # Windowsでのマルチプロセス実行に必要
    multiprocessing.freeze_support()
    main()
