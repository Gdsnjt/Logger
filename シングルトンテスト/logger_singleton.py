"""
シングルトンパターンで実装したLoggerクラス

マルチプロセスでQueueが共有されるかを検証するための実装
結論：マルチプロセスではシングルトンでも共有されない
"""

import logging
import logging.handlers
import multiprocessing
import yaml
import json
from pathlib import Path
from typing import Optional, Dict, Any, Union


class LoggerSingleton:
    """
    シングルトンパターンで実装したLoggerクラス
    
    理論上、1つのインスタンスしか存在しないため、
    すべてのプロセスで同じQueueを共有できるはず...ですが、
    マルチプロセスでは各プロセスが独立したメモリ空間を持つため、
    実際には共有されません。
    """
    
    _instance: Optional['LoggerSingleton'] = None
    _initialized: bool = False
    
    def __new__(cls, *args, **kwargs):
        """シングルトンパターンの実装"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(
        self, 
        config_path: Union[str, Path] = None,
        use_multiprocessing: bool = False,
        queue_size: int = -1
    ):
        """
        LoggerSingletonクラスの初期化
        
        注意: シングルトンなので、2回目以降の呼び出しでは初期化されません
        
        Args:
            config_path: ログ設定ファイルのパス（YAML or JSON）
            use_multiprocessing: マルチプロセスモードを使用するか
            queue_size: キューのサイズ（-1で無制限）
        """
        # 既に初期化済みの場合はスキップ
        if self._initialized:
            print(f"[PID={multiprocessing.current_process().pid}] 既に初期化済み - インスタンスID: {id(self)}")
            return
        
        print(f"[PID={multiprocessing.current_process().pid}] 新規初期化 - インスタンスID: {id(self)}")
        
        if config_path is None:
            raise ValueError("初回の初期化時にconfig_pathが必要です")
        
        self.config_path = Path(config_path)
        self.use_multiprocessing = use_multiprocessing
        self.log_queue: Optional[multiprocessing.Queue] = None
        self.listener: Optional[logging.handlers.QueueListener] = None
        self.handlers: list = []
        self.config: Dict[str, Any] = {}
        
        # 設定ファイルの読み込み
        self._load_config()
        
        # ハンドラーの設定
        self._setup_handlers()
        
        # マルチプロセスモードの場合、QueueListenerを起動
        if self.use_multiprocessing:
            self._setup_multiprocessing(queue_size)
        
        self._initialized = True
    
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
            max_bytes = handler_config.get('max_bytes', 10485760)
            backup_count = handler_config.get('backup_count', 5)
            encoding = handler_config.get('encoding', 'utf-8')
            handler = logging.handlers.RotatingFileHandler(
                filename, 
                maxBytes=max_bytes, 
                backupCount=backup_count,
                encoding=encoding
            )
        
        if handler:
            handler.setLevel(getattr(logging, level.upper()))
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
        if queue_size == -1:
            self.log_queue = multiprocessing.Queue()
        else:
            self.log_queue = multiprocessing.Queue(maxsize=queue_size)
        
        print(f"[PID={multiprocessing.current_process().pid}] Queue作成 - QueueID: {id(self.log_queue)}")
        
        self.listener = logging.handlers.QueueListener(
            self.log_queue,
            *self.handlers,
            respect_handler_level=True
        )
        self.listener.start()
        print(f"[PID={multiprocessing.current_process().pid}] QueueListener起動")
    
    def get_logger(self, name: str = None, level: str = 'INFO') -> logging.Logger:
        """
        ロガーを取得
        
        Args:
            name: ロガーの名前（Noneの場合はrootロガー）
            level: ログレベル
        
        Returns:
            設定されたロガーオブジェクト
        """
        logger = logging.getLogger(name)
        log_level = self.config.get('root', {}).get('level', level.upper())
        logger.setLevel(getattr(logging, log_level))
        logger.handlers.clear()
        
        if self.use_multiprocessing:
            if self.log_queue is None:
                raise RuntimeError("log_queueが初期化されていません")
            print(f"[PID={multiprocessing.current_process().pid}] get_logger: QueueID={id(self.log_queue)}")
            queue_handler = logging.handlers.QueueHandler(self.log_queue)
            logger.addHandler(queue_handler)
        else:
            for handler in self.handlers:
                logger.addHandler(handler)
        
        logger.propagate = self.config.get('root', {}).get('propagate', False)
        return logger
    
    def stop(self) -> None:
        """QueueListenerを停止"""
        if self.listener:
            print(f"[PID={multiprocessing.current_process().pid}] QueueListener停止")
            self.listener.stop()
            self.listener = None
    
    @classmethod
    def reset(cls):
        """シングルトンをリセット（主にテスト用）"""
        cls._instance = None
        cls._initialized = False
