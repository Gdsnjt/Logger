# Logger - マルチプロセス対応Pythonロガー

シングルプロセスとマルチプロセスの両方に対応した柔軟なロガー実装です。

## 特徴

- ✅ シングルプロセス・マルチプロセス両対応
- ✅ YAML/JSON形式の設定ファイル
- ✅ QueueHandlerによる安全なマルチプロセスログ処理
- ✅ 複数のハンドラータイプをサポート
  - コンソール出力
  - ファイル出力
  - ローテーションファイル（サイズベース）
  - ローテーションファイル（時間ベース）
- ✅ コンテキストマネージャーサポート
- ✅ 柔軟なフォーマット設定

## インストール

必要なパッケージをインストールします：

```bash
pip install pyyaml
```

## 使用方法

### シングルプロセスモード

```python
from logger import Logger

# Loggerインスタンスの作成
logger_manager = Logger('logging_config.yaml', use_multiprocessing=False)

# ロガーの取得
logger = logger_manager.get_logger('my_app')

# ログ出力
logger.info('Hello, World!')
logger.debug('デバッグメッセージ')
logger.warning('警告メッセージ')
```

### マルチプロセスモード

```python
from logger import Logger
import multiprocessing

def worker_process(config_path, process_id):
    logger_manager = Logger(config_path, use_multiprocessing=True)
    logger = logger_manager.get_logger(f'worker_{process_id}')
    
    logger.info(f'プロセス {process_id} が開始しました')
    # 処理...
    logger.info(f'プロセス {process_id} が完了しました')
    
    logger_manager.stop()

if __name__ == '__main__':
    processes = []
    for i in range(4):
        p = multiprocessing.Process(target=worker_process, args=('logging_config.yaml', i))
        p.start()
        processes.append(p)
    
    for p in processes:
        p.join()
```

### コンテキストマネージャー

```python
from logger import Logger

with Logger('logging_config.yaml', use_multiprocessing=False) as logger_manager:
    logger = logger_manager.get_logger('my_app')
    logger.info('自動的にクリーンアップされます')
```

## 設定ファイル

### YAML形式（logging_config.yaml）

```yaml
root:
  level: INFO
  propagate: false

handlers:
  console:
    type: stream
    level: INFO
    formatter:
      format: '%(asctime)s - %(name)s - [%(levelname)s] - %(message)s'
      datefmt: '%Y-%m-%d %H:%M:%S'
  
  file:
    type: file
    level: DEBUG
    filename: 'logs/app.log'
    mode: 'a'
    encoding: 'utf-8'
    formatter:
      format: '%(asctime)s - %(name)s - [%(levelname)s] - %(filename)s:%(lineno)d - %(message)s'
      datefmt: '%Y-%m-%d %H:%M:%S'
  
  rotating_file:
    type: rotating_file
    level: INFO
    filename: 'logs/app_rotating.log'
    max_bytes: 10485760  # 10MB
    backup_count: 5
    encoding: 'utf-8'
    formatter:
      format: '%(asctime)s - %(name)s - [%(levelname)s] - %(message)s'
      datefmt: '%Y-%m-%d %H:%M:%S'
```

### JSON形式（logging_config.json）

```json
{
  "root": {
    "level": "INFO",
    "propagate": false
  },
  "handlers": {
    "console": {
      "type": "stream",
      "level": "INFO",
      "formatter": {
        "format": "%(asctime)s - %(name)s - [%(levelname)s] - %(message)s",
        "datefmt": "%Y-%m-%d %H:%M:%S"
      }
    }
  }
}
```

## ハンドラータイプ

- `stream`: コンソール出力
- `file`: ファイル出力
- `rotating_file`: サイズベースのローテーション
- `timed_rotating_file`: 時間ベースのローテーション

## サンプルコード

- `example.py`: 使用例のデモンストレーション
- `test_logger.py`: 単体テストとマルチプロセステスト

実行方法：

```bash
# サンプルの実行
python example.py

# テストの実行
python test_logger.py
```

## API リファレンス

### Logger クラス

#### `__init__(config_path, use_multiprocessing=False, queue_size=-1)`

- `config_path`: 設定ファイルのパス（YAML or JSON）
- `use_multiprocessing`: マルチプロセスモードを使用するか（デフォルト: False）
- `queue_size`: キューのサイズ（デフォルト: -1で無制限）

#### `get_logger(name=None, level='INFO')`

ロガーを取得します。

- `name`: ロガーの名前（Noneの場合はrootロガー）
- `level`: ログレベル（'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'）
- 戻り値: `logging.Logger` オブジェクト

#### `stop()`

QueueListenerを停止します（マルチプロセスモードの場合）。プログラム終了時に呼び出してください。

## 注意事項

- マルチプロセスモードを使用する場合は、プログラム終了時に `stop()` メソッドを呼び出すか、コンテキストマネージャーを使用してください
- Windowsでマルチプロセスを使用する場合は、`if __name__ == '__main__':` ガード内でコードを実行してください
- ログファイルを出力するディレクトリは事前に作成しておく必要があります

## ライセンス

MIT License
