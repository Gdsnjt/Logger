"""
Logger クラスのテストコード

単体テストとマルチプロセスのテストを含みます。
"""

import unittest
import tempfile
import shutil
import multiprocessing
from pathlib import Path
from logger import Logger


class TestLogger(unittest.TestCase):
    """Loggerクラスのテスト"""
    
    def setUp(self):
        """テストの前処理"""
        # 一時ディレクトリを作成
        self.temp_dir = Path(tempfile.mkdtemp())
        self.logs_dir = self.temp_dir / 'logs'
        self.logs_dir.mkdir(exist_ok=True)
        
        # テスト用の設定ファイルを作成
        self.config_file = self.temp_dir / 'test_config.yaml'
        config_content = f"""
root:
  level: DEBUG
  propagate: false

handlers:
  console:
    type: stream
    level: DEBUG
    formatter:
      format: '%(asctime)s - %(name)s - [%(levelname)s] - %(message)s'
      datefmt: '%Y-%m-%d %H:%M:%S'
  
  file:
    type: file
    level: DEBUG
    filename: '{str(self.logs_dir / "test.log").replace(chr(92), '/')}'
    mode: 'a'
    encoding: 'utf-8'
    formatter:
      format: '%(asctime)s - %(name)s - [%(levelname)s] - %(message)s'
      datefmt: '%Y-%m-%d %H:%M:%S'
"""
        self.config_file.write_text(config_content, encoding='utf-8')
    
    def tearDown(self):
        """テストの後処理"""
        # 一時ディレクトリを削除
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_single_process_mode(self):
        """シングルプロセスモードのテスト"""
        logger_manager = Logger(self.config_file, use_multiprocessing=False)
        logger = logger_manager.get_logger('test_single')
        
        # ログを出力
        logger.info('Test log message')
        
        # ログファイルが作成されたことを確認
        log_file = self.logs_dir / 'test.log'
        self.assertTrue(log_file.exists())
        
        # ログファイルの内容を確認
        log_content = log_file.read_text(encoding='utf-8')
        self.assertIn('Test log message', log_content)
        self.assertIn('test_single', log_content)
    
    def test_multiprocessing_mode(self):
        """マルチプロセスモードのテスト"""
        logger_manager = Logger(self.config_file, use_multiprocessing=True)
        logger = logger_manager.get_logger('test_multi')
        
        # ログを出力
        logger.info('Test multiprocessing log')
        
        # クリーンアップ
        logger_manager.stop()
        
        # ログファイルが作成されたことを確認
        log_file = self.logs_dir / 'test.log'
        self.assertTrue(log_file.exists())
    
    def test_context_manager(self):
        """コンテキストマネージャーのテスト"""
        with Logger(self.config_file, use_multiprocessing=False) as logger_manager:
            logger = logger_manager.get_logger('test_context')
            logger.info('Context manager test')
        
        # コンテキストを抜けた後もログが記録されていることを確認
        log_file = self.logs_dir / 'test.log'
        log_content = log_file.read_text(encoding='utf-8')
        self.assertIn('Context manager test', log_content)
    
    def test_multiple_loggers(self):
        """複数のロガーのテスト"""
        logger_manager = Logger(self.config_file, use_multiprocessing=False)
        
        logger1 = logger_manager.get_logger('logger1')
        logger2 = logger_manager.get_logger('logger2')
        
        logger1.info('Message from logger1')
        logger2.info('Message from logger2')
        
        log_file = self.logs_dir / 'test.log'
        log_content = log_file.read_text(encoding='utf-8')
        
        self.assertIn('logger1', log_content)
        self.assertIn('logger2', log_content)
    
    def test_log_levels(self):
        """ログレベルのテスト"""
        logger_manager = Logger(self.config_file, use_multiprocessing=False)
        logger = logger_manager.get_logger('test_levels')
        
        # 各レベルのログを出力
        logger.debug('DEBUG message')
        logger.info('INFO message')
        logger.warning('WARNING message')
        logger.error('ERROR message')
        logger.critical('CRITICAL message')
        
        log_file = self.logs_dir / 'test.log'
        log_content = log_file.read_text(encoding='utf-8')
        
        # すべてのレベルが記録されていることを確認
        self.assertIn('DEBUG message', log_content)
        self.assertIn('INFO message', log_content)
        self.assertIn('WARNING message', log_content)
        self.assertIn('ERROR message', log_content)
        self.assertIn('CRITICAL message', log_content)


def worker_for_test(config_path: str, log_queue: multiprocessing.Queue, process_id: int, result_queue: multiprocessing.Queue):
    """マルチプロセステスト用のワーカー関数"""
    try:
        # 共通のQueueを使ってLoggerインスタンスを作成
        logger_manager = Logger(config_path, use_multiprocessing=True, log_queue=log_queue)
        logger = logger_manager.get_logger(f'worker_{process_id}')
        logger.info(f'Process {process_id} message')
        # ワーカープロセスではstopを呼ばない
        result_queue.put((process_id, True))
    except Exception as e:
        result_queue.put((process_id, False))


class TestLoggerMultiprocessing(unittest.TestCase):
    """マルチプロセス環境でのテスト"""
    
    def setUp(self):
        """テストの前処理"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.logs_dir = self.temp_dir / 'logs'
        self.logs_dir.mkdir(exist_ok=True)
        
        self.config_file = self.temp_dir / 'test_config.yaml'
        config_content = f"""
root:
  level: INFO
  propagate: false

handlers:
  file:
    type: file
    level: INFO
    filename: '{str(self.logs_dir / "multi_test.log").replace(chr(92), '/')}'
    mode: 'a'
    encoding: 'utf-8'
    formatter:
      format: '%(asctime)s - %(name)s - [%(levelname)s] - %(message)s'
      datefmt: '%Y-%m-%d %H:%M:%S'
"""
        self.config_file.write_text(config_content, encoding='utf-8')
    
    def tearDown(self):
        """テストの後処理"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_multiple_processes(self):
        """複数プロセスでのログ出力テスト（正しいパターン）"""
        num_processes = 3
        result_queue = multiprocessing.Queue()
        
        # メインプロセスでLoggerインスタンスを作成
        main_logger_manager = Logger(str(self.config_file), use_multiprocessing=True)
        
        processes = []
        
        # 共通のQueueを渡してワーカープロセスを起動
        for i in range(num_processes):
            p = multiprocessing.Process(
                target=worker_for_test,
                args=(str(self.config_file), main_logger_manager.log_queue, i, result_queue)
            )
            p.start()
            processes.append(p)
        
        # プロセスの完了を待つ
        for p in processes:
            p.join()
        
        # メインプロセスでListenerを停止
        main_logger_manager.stop()
        
        # 結果を確認
        results = []
        while not result_queue.empty():
            results.append(result_queue.get())
        
        # すべてのプロセスが成功したことを確認
        self.assertEqual(len(results), num_processes)
        for process_id, success in results:
            self.assertTrue(success, f"Process {process_id} failed")


def run_tests():
    """テストを実行"""
    # テストスイートを作成
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # テストを追加
    suite.addTests(loader.loadTestsFromTestCase(TestLogger))
    suite.addTests(loader.loadTestsFromTestCase(TestLoggerMultiprocessing))
    
    # テストを実行
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == '__main__':
    multiprocessing.freeze_support()
    run_tests()
