# Logger実装パターン - 完全ガイド

このプロジェクトでは、シングルプロセスとマルチプロセスに対応した2つのLogger実装パターンを提供しています。

## 📁 ファイル構成

```
Logger/
├── logger_separate.py      # 別々の実装パターン
├── logger_unified.py        # 統合実装パターン
├── example_separate.py      # 別々実装の使用例
├── example_unified.py       # 統合実装の使用例
├── logging_config.yaml      # ログ設定ファイル
└── IMPLEMENTATION_GUIDE.md  # このファイル
```

---

## 🎯 実装パターンの選択

### パターン1: 別々の実装（`logger_separate.py`）

**特徴:**
- `SingleProcessLogger`: シングルプロセス専用
- `MultiProcessLogger`: マルチプロセス専用
- 各クラスが用途に特化してシンプル

**メリット:**
- ✅ コードが短く、理解しやすい
- ✅ デバッグが容易
- ✅ 不要な機能がなく、パフォーマンスが最適
- ✅ 保守性が高い

**推奨される場合:**
- 用途がはっきりしている（シングルorマルチが明確）
- シンプルさを重視
- チーム開発で役割分担が明確

### パターン2: 統合実装（`logger_unified.py`）

**特徴:**
- `UnifiedLogger`: 単一クラスで両モードに対応
- `use_multiprocessing`フラグでモードを切り替え
- 3つの動作モードを自動判定

**メリット:**
- ✅ 統一されたインターフェース
- ✅ モード切り替えが簡単（フラグ1つ）
- ✅ 環境に応じた動的切り替えが可能
- ✅ テストコードの共通化が容易

**推奨される場合:**
- 開発/本番で動作モードが異なる
- 環境変数で動作を制御したい
- 柔軟性と拡張性を重視

---

## 📖 使用例

### パターン1: 別々の実装

#### SingleProcessLogger

```python
from logger_separate import SingleProcessLogger

# シンプルな使用方法
logger_manager = SingleProcessLogger('logging_config.yaml')
logger = logger_manager.get_logger('my_app')
logger.info('Hello, World!')

# コンテキストマネージャー
with SingleProcessLogger('logging_config.yaml') as logger_manager:
    logger = logger_manager.get_logger('my_app')
    logger.info('クリーンな実装')
```

#### MultiProcessLogger

```python
from logger_separate import MultiProcessLogger
import multiprocessing

def worker(log_queue):
    # ワーカープロセス用のLoggerを作成
    worker_logger = MultiProcessLogger.from_queue('logging_config.yaml', log_queue)
    logger = worker_logger.get_logger('worker')
    logger.info('Hello from worker!')

# メインプロセス
main_logger = MultiProcessLogger('logging_config.yaml')

# ワーカープロセスを起動
p = multiprocessing.Process(target=worker, args=(main_logger.get_queue(),))
p.start()
p.join()

main_logger.stop()
```

### パターン2: 統合実装

#### シングルプロセスモード

```python
from logger_unified import UnifiedLogger

# シングルプロセスモード
logger_manager = UnifiedLogger('logging_config.yaml', use_multiprocessing=False)
logger = logger_manager.get_logger('my_app')
logger.info('シングルプロセスで動作')
```

#### マルチプロセスモード

```python
from logger_unified import UnifiedLogger
import multiprocessing

def worker(log_queue):
    # ワーカープロセス
    worker_logger = UnifiedLogger(
        'logging_config.yaml',
        use_multiprocessing=True,
        log_queue=log_queue
    )
    logger = worker_logger.get_logger('worker')
    logger.info('Hello from worker!')

# メインプロセス
main_logger = UnifiedLogger('logging_config.yaml', use_multiprocessing=True)

# ワーカープロセスを起動
p = multiprocessing.Process(target=worker, args=(main_logger.get_queue(),))
p.start()
p.join()

main_logger.stop()
```

---

## 🔍 詳細比較

### 別々の実装（logger_separate.py）

| 項目 | SingleProcessLogger | MultiProcessLogger |
|------|---------------------|-------------------|
| 用途 | シングルプロセス専用 | マルチプロセス専用 |
| 複雑さ | ⭐ シンプル | ⭐⭐ やや複雑 |
| パフォーマンス | ⭐⭐⭐ 最高 | ⭐⭐ 良好 |
| Queue使用 | ❌ なし | ✅ QueueHandler使用 |
| メソッド | `get_logger()` | `get_logger()`, `from_queue()`, `stop()` |

### 統合実装（logger_unified.py）

| 項目 | UnifiedLogger |
|------|---------------|
| 動作モード | シングル/マルチ両対応 |
| 複雑さ | ⭐⭐⭐ やや複雑 |
| 柔軟性 | ⭐⭐⭐ 最高 |
| モード判定 | LoggerMode列挙型で管理 |
| メソッド | `get_logger()`, `get_queue()`, `get_mode()`, `stop()` |

---

## 🏗️ アーキテクチャ

### 別々の実装

```
BaseLogger (ABC)
├── SingleProcessLogger
│   └── 直接Handlerを使用
│
└── MultiProcessLogger
    └── QueueHandler + QueueListener
```

### 統合実装

```
UnifiedLogger
├── モード判定ロジック
├── SINGLE_PROCESS       → 直接Handler
├── MULTI_PROCESS_MAIN   → Queue作成 + Listener起動
└── MULTI_PROCESS_WORKER → 既存Queueを使用
```

---

## 🚀 実行方法

### 別々の実装のテスト

```bash
python example_separate.py
```

**出力内容:**
- SingleProcessLoggerのテスト
- コンテキストマネージャーのテスト
- MultiProcessLoggerのテスト
- 実装パターンの比較

### 統合実装のテスト

```bash
python example_unified.py
```

**出力内容:**
- シングルプロセスモードのテスト
- マルチプロセスモードのテスト
- モード切り替えのテスト
- 両パターンの比較

---

## 📊 パフォーマンス比較

| シナリオ | 別々の実装 | 統合実装 | 備考 |
|---------|-----------|---------|------|
| シングルプロセス | ⭐⭐⭐ | ⭐⭐ | 別々の実装がわずかに高速 |
| マルチプロセス | ⭐⭐⭐ | ⭐⭐⭐ | ほぼ同等 |
| コードサイズ | ⭐⭐ | ⭐⭐⭐ | 統合実装は1ファイル |
| 保守性 | ⭐⭐⭐ | ⭐⭐ | 別々の実装がシンプル |

---

## 💡 使い分けのガイドライン

### 別々の実装を選ぶべき場合

1. **用途が明確**
   - シングルプロセスアプリケーション
   - マルチプロセスアプリケーション
   - どちらか一方しか使わない

2. **シンプルさを重視**
   - コードレビューが容易
   - 新人でも理解しやすい
   - バグが発生しにくい

3. **最適なパフォーマンス**
   - 不要なオーバーヘッドを排除
   - メモリ効率が重要

### 統合実装を選ぶべき場合

1. **動的な切り替えが必要**
   - 開発環境ではシングル、本番ではマルチ
   - 環境変数で制御したい
   - テスト時にモックが不要

2. **統一されたコードベース**
   - インターフェースを統一したい
   - ラッパークラスを作りやすい
   - プラグインシステムに組み込む

3. **将来の拡張性**
   - 新しいモードを追加する可能性
   - 設定ファイルで動作を制御
   - フレームワークとして提供

---

## 🔧 カスタマイズ

### 新しいHandlerの追加

両実装とも、`_create_handler`メソッドを拡張することで、
カスタムハンドラーを追加できます。

```python
def _create_handler(self, handler_name: str, handler_config: Dict[str, Any]):
    handler_type = handler_config.get('type', 'stream')
    
    # 既存のハンドラー...
    
    elif handler_type == 'custom':
        # カスタムハンドラーの実装
        handler = MyCustomHandler()
    
    return handler
```

### 設定ファイルの拡張

`logging_config.yaml`でハンドラーの詳細を設定できます。

```yaml
handlers:
  file:
    type: file
    filename: logs/app.log
    level: INFO
    formatter:
      format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
      datefmt: '%Y-%m-%d %H:%M:%S'
```

---

## 🎓 学習リソース

### 別々の実装のポイント

- `SingleProcessLogger`: 基本的なlogging.Handlerの使用方法
- `MultiProcessLogger`: QueueHandlerとQueueListenerのパターン
- `from_queue()`: クラスメソッドの活用

### 統合実装のポイント

- `LoggerMode`: Enumを使った状態管理
- `_determine_mode()`: 動的なモード判定
- `get_mode()`: 現在の状態の取得

---

## 📝 まとめ

| 要素 | 別々の実装 | 統合実装 |
|------|-----------|---------|
| **シンプルさ** | ⭐⭐⭐ | ⭐⭐ |
| **柔軟性** | ⭐⭐ | ⭐⭐⭐ |
| **パフォーマンス** | ⭐⭐⭐ | ⭐⭐⭐ |
| **保守性** | ⭐⭐⭐ | ⭐⭐ |
| **学習コスト** | ⭐⭐ | ⭐⭐⭐ |

### 最終推奨

- **小〜中規模プロジェクト**: 別々の実装（logger_separate.py）
- **大規模プロジェクト**: 統合実装（logger_unified.py）
- **初学者**: 別々の実装から始める
- **経験者**: 要件に応じて選択

---

## 🤝 貢献

バグ報告や機能要望は、GitHubのIssueでお願いします。

## 📄 ライセンス

MIT License

---

**作成日**: 2026年2月8日
**最終更新**: 2026年2月8日
