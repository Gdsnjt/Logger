"""
シングルプロセスとマルチプロセスを別々に実装したLoggerクラス

それぞれの用途に特化したシンプルで明確な実装。
SingleProcessLoggerとMultiProcessLoggerを提供します。
"""

import logging
import logging.handlers
import multiprocessing
import yaml
import json
from pathlib import Path
from typing import Optional, Dict, Any, Union
from abc import ABC, abstractmethod


class BaseLogger(ABC):
    """Loggerの基底クラス"""
    
    def __init__(self, config_path: Union[str, Path]):
        """
        基底Loggerの初期化
        
        Args:
            config_path: ログ設定ファイルのパス（YAML or JSON）
        """
        self.config_path = Path(config_path)
        self.handlers: list = []
        self.config: Dict[str, Any] = {}
        
        # 設定ファイルの読み込み
        self._load_config()
        
        # ハンドラーの設定
        self._setup_handlers()
    
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
    
    @abstractmethod
    def get_logger(self, name: str = None, level: str = 'INFO') -> logging.Logger:
        """
        ロガーを取得（各サブクラスで実装）
        
        Args:
            name: ロガーの名前
            level: ログレベル
        
        Returns:
            設定されたロガーオブジェクト
        """
        pass


class SingleProcessLogger(BaseLogger):
    """
    シングルプロセス専用のLoggerクラス
    
    シンプルで軽量な実装。マルチプロセスの複雑さがないため、
    デバッグが容易で、オーバーヘッドも最小限。
    
    使用例:
        logger_manager = SingleProcessLogger('logging_config.yaml')
        logger = logger_manager.get_logger('my_app')
        logger.info('Hello, World!')
    """
    
    def __init__(self, config_path: Union[str, Path]):
        """
        SingleProcessLoggerの初期化
        
        Args:
            config_path: ログ設定ファイルのパス（YAML or JSON）
        """
        super().__init__(config_path)
    
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
        
        # ハンドラーを直接追加
        for handler in self.handlers:
            logger.addHandler(handler)
        
        # 親ロガーへの伝播を防ぐ
        logger.propagate = self.config.get('root', {}).get('propagate', False)
        
        return logger
    
    def __enter__(self):
        """コンテキストマネージャーのサポート"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャーのサポート"""
        pass


class MultiProcessLogger(BaseLogger):
    """
    マルチプロセス専用のLoggerクラス
    
    QueueHandlerとQueueListenerを使用して、複数のプロセスから
    安全にログを出力できます。
    
    使用例:
        # メインプロセス
        main_logger = MultiProcessLogger('logging_config.yaml')
        
        # ワーカープロセス
        def worker(log_queue):
            worker_logger = MultiProcessLogger.from_queue(
                'logging_config.yaml', 
                log_queue
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
        queue_size: int = -1
    ):
        """
        MultiProcessLogger（メインプロセス用）の初期化
        
        Args:
            config_path: ログ設定ファイルのパス（YAML or JSON）
            queue_size: キューのサイズ（-1で無制限）
        """
        super().__init__(config_path)
        
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
        self.is_owner = True  # このインスタンスがListenerの所有者
    
    @classmethod
    def from_queue(
        cls, 
        config_path: Union[str, Path],
        log_queue: multiprocessing.Queue
    ) -> 'MultiProcessLogger':
        """
        既存のQueueを使用してワーカープロセス用のLoggerを作成
        
        Args:
            config_path: ログ設定ファイルのパス
            log_queue: メインプロセスから渡されたQueue
        
        Returns:
            ワーカープロセス用のMultiProcessLogger
        """
        instance = cls.__new__(cls)
        BaseLogger.__init__(instance, config_path)
        instance.log_queue = log_queue
        instance.listener = None
        instance.is_owner = False  # ワーカーはListenerの所有者ではない
        return instance
    
    def get_logger(self, name: str = None, level: str = 'INFO') -> logging.Logger:
        """
        ロガーを取得
        
        Args:
            name: ロガーの名前（Noneの場合はrootロガー）
            level: ログレベル
        
        Returns:
            設定されたロガーオブジェクト
        """
        # ロガーの取得
        logger = logging.getLogger(name)
        
        # レベルの設定
        log_level = self.config.get('root', {}).get('level', level.upper())
        logger.setLevel(getattr(logging, log_level))
        
        # 既存のハンドラーをクリア
        logger.handlers.clear()
        
        # QueueHandlerを使用
        queue_handler = logging.handlers.QueueHandler(self.log_queue)
        logger.addHandler(queue_handler)
        
        # 親ロガーへの伝播を防ぐ
        logger.propagate = self.config.get('root', {}).get('propagate', False)
        
        return logger
    
    def get_queue(self) -> multiprocessing.Queue:
        """
        ログキューを取得（ワーカープロセスに渡すため）
        
        Returns:
            マルチプロセス用のQueue
        """
        return self.log_queue
    
    def stop(self) -> None:
        """
        QueueListenerを停止
        注意: メインプロセス（所有者）のみが呼び出すこと
        """
        if self.listener and self.is_owner:
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
