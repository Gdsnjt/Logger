"""
シングルトンLoggerのテストコード

マルチプロセスでシングルトンのQueueが共有されるかを検証します。

予想結果：
- メインプロセスと各ワーカープロセスで異なるインスタンスが作成される
- 各プロセスで異なるQueueが作成される
- したがって、ログが正しく集約されない可能性が高い
"""

import time
import multiprocessing
from pathlib import Path
from logger_singleton import LoggerSingleton


def worker_process(process_id: int):
    """
    ワーカープロセス
    
    シングルトンなので、引数でQueueを渡さずに
    直接LoggerSingletonのインスタンスを取得
    """
    print(f"\n=== Worker {process_id} 開始 ===")
    
    # シングルトンインスタンスを取得（理論上、メインと同じインスタンスのはず...）
    logger_manager = LoggerSingleton('logging_config.yaml', use_multiprocessing=True)
    logger = logger_manager.get_logger(f'worker_{process_id}')
    
    # ログ出力
    logger.info(f'ワーカー {process_id} が開始しました')
    
    for i in range(3):
        logger.info(f'ワーカー {process_id} - 処理 {i+1}/3')
        time.sleep(0.1)
    
    logger.info(f'ワーカー {process_id} が完了しました')
    print(f"=== Worker {process_id} 終了 ===\n")


def test_singleton_multiprocessing():
    """シングルトンパターンでのマルチプロセステスト"""
    print("=" * 60)
    print("シングルトンパターン マルチプロセステスト")
    print("=" * 60)
    
    # logsディレクトリを作成
    Path('logs').mkdir(exist_ok=True)
    
    print("\n--- メインプロセスでLoggerSingletonを初期化 ---")
    # メインプロセスでシングルトンを初期化
    main_logger_manager = LoggerSingleton('logging_config.yaml', use_multiprocessing=True)
    main_logger = main_logger_manager.get_logger('main_process')
    
    main_logger.info('メインプロセス: テストを開始します')
    main_logger.info(f'メインプロセスのインスタンスID: {id(main_logger_manager)}')
    main_logger.info(f'メインプロセスのQueueID: {id(main_logger_manager.log_queue)}')
    
    print("\n--- ワーカープロセスを起動（Queueを渡さない） ---")
    num_processes = 3
    processes = []
    
    # ワーカープロセスを起動（引数でQueueを渡さない）
    for i in range(num_processes):
        p = multiprocessing.Process(target=worker_process, args=(i,))
        p.start()
        processes.append(p)
    
    # プロセスの完了を待つ
    for p in processes:
        p.join()
    
    print("\n--- すべてのワーカープロセスが完了 ---")
    main_logger.info('メインプロセス: すべてのワーカーが完了しました')
    
    # リスナーを停止
    time.sleep(0.5)  # ログ出力の完了を待つ
    main_logger_manager.stop()
    
    print("\n" + "=" * 60)
    print("テスト完了")
    print("=" * 60)
    
    print("\n【検証結果】")
    print("上記の出力で、各ワーカープロセスの「新規初期化」と「QueueID」を確認してください。")
    print("メインプロセスと異なるIDが表示されていれば、")
    print("シングルトンでもプロセス間ではインスタンスが共有されないことが証明されます。")
    print("\nログファイル（logs/singleton_test.log）も確認してください。")
    print("ワーカープロセスのログが記録されていない、または")
    print("各プロセスが独自のログファイルを持っている可能性があります。")


def test_singleton_basic():
    """シングルトンが同一プロセス内で正しく動作するかの基本テスト"""
    print("\n" + "=" * 60)
    print("シングルトンパターン 基本テスト（単一プロセス）")
    print("=" * 60)
    
    # logsディレクトリを作成
    Path('logs').mkdir(exist_ok=True)
    
    print("\n1回目のインスタンス作成:")
    logger1 = LoggerSingleton('logging_config.yaml', use_multiprocessing=False)
    print(f"インスタンスID: {id(logger1)}")
    
    print("\n2回目のインスタンス作成:")
    logger2 = LoggerSingleton()  # 既に初期化済みなのでconfig_pathは不要
    print(f"インスタンスID: {id(logger2)}")
    
    print(f"\n同じインスタンス？ {logger1 is logger2}")
    print("=" * 60)


if __name__ == '__main__':
    multiprocessing.freeze_support()
    
    # 基本テスト
    test_singleton_basic()
    
    # シングルトンをリセット
    LoggerSingleton.reset()
    
    # マルチプロセステスト
    test_singleton_multiprocessing()
