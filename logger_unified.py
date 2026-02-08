"""
統合されたLoggerクラスの改善版

シングルプロセスとマルチプロセスの両方に対応した柔軟なロガー実装。
use_multiprocessingフラグで動作モードを切り替えることができます。
"""

import logging
import logging.handlers
import multiprocessing
import yaml
import json
from pathlib import Path
from typing import Optional, Dict, Any, Union
from enum import Enum


class LoggerMode(Enum):
    """ロガーの動作モード"""
    SINGLE_PROCESS = "single_process"
    MULTI_PROCESS_MAIN = "multi_process_main"
    MULTI_PROCESS_WORKER = "multi_process_worker"


class UnifiedLogger:
    """
    シングルプロセス・マルチプロセス統合対応のLoggerクラス
    
    use_multiprocessingフラグで動作モードを切り替え、
    適切なログ処理方法を自動的に選択します。
    
    使用例:
        # シングルプロセスモード
        with UnifiedLogger('logging_config.yaml') as logger_manager:
            logger = logger_manager.get_logger('my_app')
            logger.info('Hello, World!')
        
        # マルチプロセスモード
        # メインプロセス
        main_logger = UnifiedLogger('logging_config.yaml', use_multiprocessing=True)
        
        # ワーカープロセス
        def worker(log_queue):
            worker_logger = UnifiedLogger(
                'logging_config.yaml',
                use_multiprocessing=True,
                log_queue=log_queue
            )
            logger = worker_logger.get_logger('worker')
            logger.info('Hello from worker!')
        
        p = multiprocessing.Process(target=worker, args=(main_logger.get_queue(),))
        p.start()
        p.join()
        
        main_logger.stop()
    """
    
    def __init__(
        self, 
        config_path: Union[str, Path],
        use_multiprocessing: bool = False,
        queue_size: int = -1,
        log_queue: Optional[multiprocessing.Queue] = None
    ):
        """
        UnifiedLoggerの初期化
        
        Args:
            config_path: ログ設定ファイルのパス（YAML or JSON）
            use_multiprocessing: マルチプロセスモードを使用するか
            queue_size: キューのサイズ（-1で無制限）
            log_queue: 既存のQueueを使用する場合に指定（ワーカープロセス用）
        """
        self.config_path = Path(config_path)
        self.use_multiprocessing = use_multiprocessing
        self.log_queue: Optional[multiprocessing.Queue] = log_queue
        self.listener: Optional[logging.handlers.QueueListener] = None
        self.handlers: list = []
        self.config: Dict[str, Any] = {}
        
        # 動作モードの判定
        self._determine_mode(log_queue)
        
        # 設定ファイルの読み込み
        self._load_config()
        
        # ハンドラーの設定
        self._setup_handlers()
        
        # マルチプロセスモードの初期化
        if self.mode == LoggerMode.MULTI_PROCESS_MAIN:
            self._setup_multiprocessing(queue_size)
    
    def _determine_mode(self, log_queue: Optional[multiprocessing.Queue]) -> None:
        """動作モードを判定"""
        if not self.use_multiprocessing:
            self.mode = LoggerMode.SINGLE_PROCESS
        elif log_queue is None:
            self.mode = LoggerMode.MULTI_PROCESS_MAIN
        else:
            self.mode = LoggerMode.MULTI_PROCESS_WORKER
    
    def _load_config(self) -> None:
        """設定ファイルを読み込む"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"設定ファイルが見つかりません: {self.config_path}")
        
        suffix = self.config_path.suffix.lower()
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            if suffix in ['.yaml', '.yml']:
                self.config = yaml.safe_load(f)
            elif suffix == '.json':
                self.config = json.load(f)
            else:
                raise ValueError(f"サポートされていないファイル形式: {suffix}")
    
    def _setup_handlers(self) -> None:
        """設定ファイルに基づいてハンドラーを作成"""
        # ワーカープロセスではハンドラーは不要（Queueを使用）
        if self.mode == LoggerMode.MULTI_PROCESS_WORKER:
            return
        
        handlers_config = self.config.get('handlers', {})
        
        for handler_name, handler_config in handlers_config.items():
            handler = self._create_handler(handler_name, handler_config)
            if handler:
                self.handlers.append(handler)
    
    def _create_handler(
        self, 
        handler_name: str, 
        handler_config: Dict[str, Any]
    ) -> Optional[logging.Handler]:
        """個別のハンドラーを作成"""
        handler_type = handler_config.get('type', 'stream')
        level = handler_config.get('level', 'INFO')
        formatter_config = handler_config.get('formatter', {})
        
        handler = None
        
        if handler_type == 'stream':
            handler = logging.StreamHandler()
        elif handler_type == 'file':
            filename = handler_config.get('filename', 'app.log')
            mode = handler_config.get('mode', 'a')
            encoding = handler_config.get('encoding', 'utf-8')
            handler = logging.FileHandler(filename, mode=mode, encoding=encoding)
        elif handler_type == 'rotating_file':
            filename = handler_config.get('filename', 'app.log')
            max_bytes = handler_config.get('max_bytes', 10485760)  # 10MB
            backup_count = handler_config.get('backup_count', 5)
            encoding = handler_config.get('encoding', 'utf-8')
            handler = logging.handlers.RotatingFileHandler(
                filename, 
                maxBytes=max_bytes, 
                backupCount=backup_count,
                encoding=encoding
            )
        elif handler_type == 'timed_rotating_file':
            filename = handler_config.get('filename', 'app.log')
            when = handler_config.get('when', 'midnight')
            interval = handler_config.get('interval', 1)
            backup_count = handler_config.get('backup_count', 7)
            encoding = handler_config.get('encoding', 'utf-8')
            handler = logging.handlers.TimedRotatingFileHandler(
                filename,
                when=when,
                interval=interval,
                backupCount=backup_count,
                encoding=encoding
            )
        
        if handler:
            # レベルの設定
            handler.setLevel(getattr(logging, level.upper()))
            
            # フォーマッターの設定
            format_string = formatter_config.get(
                'format', 
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            date_format = formatter_config.get('datefmt', '%Y-%m-%d %H:%M:%S')
            formatter = logging.Formatter(format_string, datefmt=date_format)
            handler.setFormatter(formatter)
        
        return handler
    
    def _setup_multiprocessing(self, queue_size: int) -> None:
        """マルチプロセス用のQueueとListenerを設定"""
        # マルチプロセス対応のキューを作成
        if queue_size == -1:
            self.log_queue = multiprocessing.Queue()
        else:
            self.log_queue = multiprocessing.Queue(maxsize=queue_size)
        
        # QueueListenerを作成して起動
        self.listener = logging.handlers.QueueListener(
            self.log_queue,
            *self.handlers,
            respect_handler_level=True
        )
        self.listener.start()
    
    def get_logger(self, name: str = None, level: str = 'INFO') -> logging.Logger:
        """
        ロガーを取得
        
        Args:
            name: ロガーの名前（Noneの場合はrootロガー）
            level: ログレベル（'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'）
        
        Returns:
            設定されたロガーオブジェクト
        """
        # ロガーの取得
        logger = logging.getLogger(name)
        
        # レベルの設定
        log_level = self.config.get('root', {}).get('level', level.upper())
        logger.setLevel(getattr(logging, log_level))
        
        # 既存のハンドラーをクリア（重複を避けるため）
        logger.handlers.clear()
        
        # モードに応じたハンドラーの設定
        if self.mode == LoggerMode.SINGLE_PROCESS:
            # シングルプロセスモード: 直接ハンドラーを追加
            for handler in self.handlers:
                logger.addHandler(handler)
        else:
            # マルチプロセスモード: QueueHandlerを使用
            queue_handler = logging.handlers.QueueHandler(self.log_queue)
            logger.addHandler(queue_handler)
        
        # 親ロガーへの伝播を防ぐ
        logger.propagate = self.config.get('root', {}).get('propagate', False)
        
        return logger
    
    def get_queue(self) -> Optional[multiprocessing.Queue]:
        """
        ログキューを取得（ワーカープロセスに渡すため）
        
        Returns:
            マルチプロセス用のQueue（シングルプロセスモードの場合はNone）
        """
        return self.log_queue if self.use_multiprocessing else None
    
    def get_mode(self) -> LoggerMode:
        """
        現在の動作モードを取得
        
        Returns:
            LoggerMode
        """
        return self.mode
    
    def stop(self) -> None:
        """
        QueueListenerを停止（マルチプロセスモードの場合）
        注意: メインプロセスのみが呼び出すこと
        """
        if self.listener and self.mode == LoggerMode.MULTI_PROCESS_MAIN:
            self.listener.stop()
            self.listener = None
    
    def __enter__(self):
        """コンテキストマネージャーのサポート"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャーのサポート"""
        self.stop()
    
    def __del__(self):
        """デストラクタでリスナーを停止"""
        self.stop()
    
    def __repr__(self) -> str:
        """オブジェクトの文字列表現"""
        return f"UnifiedLogger(mode={self.mode.value}, config={self.config_path.name})"
