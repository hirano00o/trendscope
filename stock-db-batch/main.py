"""
TrendScope 株式データバッチ処理アプリケーション

エントリーポイント
"""

import logging
import sys

from stock_batch.main_batch_application import BatchConfig, MainBatchApplication


def main() -> int:
    """メイン実行関数

    Returns:
        終了コード (0: 成功, 1: 失敗)
    """
    try:
        # Kubernetes環境からの設定読み込み
        config = BatchConfig.from_environment()

        # アプリケーション実行
        app = MainBatchApplication(config)
        result = app.run_batch()

        if result.success:
            print(f"バッチ処理成功: {result.total_processed}件処理")
            return 0
        else:
            print(f"バッチ処理失敗: {result.error_details}")
            return 1

    except Exception as e:
        logging.error(f"アプリケーション実行エラー: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
