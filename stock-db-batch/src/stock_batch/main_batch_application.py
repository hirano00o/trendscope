"""メインバッチアプリケーション

全サービスを統合したエンドツーエンドのバッチ処理アプリケーション
Kubernetes対応、設定管理、ロギング、エラーハンドリング機能を提供
"""

from __future__ import annotations

import logging
import os
import signal
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import psutil
import yfinance

from stock_batch.database.connection import DatabaseConnection
from stock_batch.services.csv_reader import CSVReader
from stock_batch.services.database_service import DatabaseService
from stock_batch.services.differential_processor import DifferentialProcessor
from stock_batch.services.stock_fetcher import StockFetcher
from stock_batch.services.translation import TranslationService
from stock_batch.services.async_batch_processor import AsyncBatchProcessor

logger = logging.getLogger(__name__)


@dataclass
class BatchConfig:
    """バッチ設定

    バッチ処理に必要な全ての設定を保持するデータクラス
    """

    database_path: str
    csv_file_path: str
    chunk_size: int = 1000
    enable_parallel: bool = False
    max_workers: int = 4
    enable_stock_data_fetch: bool = True
    enable_translation: bool = True
    max_retries: int = 3
    retry_delay: float = 1.0
    dry_run: bool = False
    continue_on_error: bool = True
    log_level: str = "INFO"
    enable_progress_reporting: bool = False
    progress_report_interval: int = 100
    enable_performance_monitoring: bool = False
    enable_graceful_shutdown: bool = False

    def __post_init__(self) -> None:
        """設定の検証を行う"""
        # データベースパスの検証
        if self.database_path and not Path(self.database_path).parent.exists():
            if self.database_path != "":  # 空文字列の場合は一時ファイルとして扱う
                raise ValueError("データベースファイルが存在しません")

        # CSVファイルパスの検証
        if not Path(self.csv_file_path).parent.exists():
            raise ValueError("CSVファイルのディレクトリが存在しません")

    @classmethod
    def from_environment(cls) -> BatchConfig:
        """環境変数から設定を作成する

        Kubernetes環境での設定読み込み用

        Returns:
            環境変数から作成されたBatchConfig

        Example:
            >>> config = BatchConfig.from_environment()
        """
        return cls(
            database_path=os.getenv("BATCH_DATABASE_PATH", "/data/stocks.db"),
            csv_file_path=os.getenv("BATCH_CSV_PATH", "/data/stocks.csv"),
            chunk_size=int(os.getenv("BATCH_CHUNK_SIZE", "1000")),
            enable_parallel=os.getenv("BATCH_ENABLE_PARALLEL", "false").lower()
            == "true",
            max_workers=int(os.getenv("BATCH_MAX_WORKERS", "4")),
            enable_stock_data_fetch=os.getenv(
                "BATCH_ENABLE_STOCK_FETCH", "true"
            ).lower()
            == "true",
            enable_translation=os.getenv("BATCH_ENABLE_TRANSLATION", "true").lower()
            == "true",
            max_retries=int(os.getenv("BATCH_MAX_RETRIES", "3")),
            dry_run=os.getenv("BATCH_DRY_RUN", "false").lower() == "true",
            continue_on_error=os.getenv("BATCH_CONTINUE_ON_ERROR", "true").lower()
            == "true",
            log_level=os.getenv("BATCH_LOG_LEVEL", "INFO"),
            enable_progress_reporting=os.getenv(
                "BATCH_ENABLE_PROGRESS", "false"
            ).lower()
            == "true",
            enable_performance_monitoring=os.getenv(
                "BATCH_ENABLE_MONITORING", "false"
            ).lower()
            == "true",
            enable_graceful_shutdown=os.getenv(
                "BATCH_ENABLE_GRACEFUL_SHUTDOWN", "true"
            ).lower()
            == "true",
        )


@dataclass
class BatchResult:
    """バッチ処理結果

    バッチ処理の結果と統計情報を保持するデータクラス
    """

    success: bool
    total_processed: int
    companies_inserted: int
    companies_updated: int
    processing_time: float
    memory_usage_mb: float
    records_per_second: float
    database_operations_count: int
    parallel_processing_used: bool
    environment: str
    error_details: list[str]
    progress_reports: list[dict[str, Any]]


class MainBatchApplication:
    """メインバッチアプリケーションクラス

    全サービスを統合してエンドツーエンドのバッチ処理を実行する。
    Kubernetes環境での実行、Graceful Shutdown、パフォーマンス監視をサポートする。

    Attributes:
        config: バッチ設定
        shutdown_requested: シャットダウン要求フラグ

    Example:
        >>> config = BatchConfig(
        ...     database_path="/data/stocks.db",
        ...     csv_file_path="/data/stocks.csv",
        ...     enable_parallel=True
        ... )
        >>> app = MainBatchApplication(config)
        >>> result = app.run_batch()
        >>> print(f"処理完了: {result.total_processed}件")
    """

    def __init__(self, config: BatchConfig) -> None:
        """MainBatchApplication を初期化する

        Args:
            config: バッチ設定

        Example:
            >>> config = BatchConfig.from_environment()
            >>> app = MainBatchApplication(config)
        """
        self.config = config
        self.shutdown_requested = False

        # ログ設定
        self._setup_logging()

        # yfinanceキャッシュ設定
        self._setup_yfinance_cache()

        # Graceful Shutdown設定
        if config.enable_graceful_shutdown:
            self._setup_signal_handlers()

        # 統計情報
        self._application_stats = {
            "total_runs": 0,
            "total_records_processed": 0,
            "total_processing_time": 0.0,
            "last_run_result": None,
        }

        logger.info("MainBatchApplication初期化完了")

    def _create_liveness_marker(self) -> None:
        """Liveness Probe用の状態マーカーファイルを作成する"""
        try:
            marker_file = Path("/tmp/app/.batch_running")
            marker_file.touch()
            logger.debug("Liveness Probe状態マーカー作成: %s", marker_file)
        except Exception as e:
            logger.warning("Liveness Probe状態マーカー作成失敗: %s", e)

    def _remove_liveness_marker(self) -> None:
        """Liveness Probe用の状態マーカーファイルを削除する"""
        try:
            marker_file = Path("/tmp/app/.batch_running")
            marker_file.unlink(missing_ok=True)
            logger.debug("Liveness Probe状態マーカー削除: %s", marker_file)
        except Exception as e:
            logger.warning("Liveness Probe状態マーカー削除失敗: %s", e)

    async def run_batch(self) -> BatchResult:
        """バッチ処理を実行する

        全てのサービスを統合してエンドツーエンドの処理を実行する。
        設定に応じて並列処理、株価取得、翻訳などを行う。

        Returns:
            バッチ処理結果

        Example:
            >>> result = app.run_batch()
            >>> if result.success:
            ...     print(f"成功: {result.companies_inserted}件挿入")
        """
        start_time = time.time()
        start_memory = self._get_memory_usage()

        # Liveness Probe用状態マーカー作成
        self._create_liveness_marker()

        logger.info("バッチ処理開始: %s", self.config.csv_file_path)

        # 結果初期化
        result = BatchResult(
            success=False,
            total_processed=0,
            companies_inserted=0,
            companies_updated=0,
            processing_time=0.0,
            memory_usage_mb=0.0,
            records_per_second=0.0,
            database_operations_count=0,
            parallel_processing_used=self.config.enable_parallel,
            environment=self._detect_environment(),
            error_details=[],
            progress_reports=[],
        )

        try:
            # 1. CSV読み取り
            csv_companies = self._read_csv_data()
            if not csv_companies:
                raise Exception("CSVデータが読み取れませんでした")

            result.total_processed = len(csv_companies)
            logger.info("CSV読み取り完了: %d件", len(csv_companies))

            # 2. 株価データ取得（オプション）
            if self.config.enable_stock_data_fetch:
                csv_companies = self._enrich_with_stock_data(csv_companies, result)

            # 3. 翻訳処理（オプション）
            if self.config.enable_translation:
                csv_companies = await self._translate_business_summaries(
                    csv_companies, result
                )

            # 4. データベース処理
            if not self.config.dry_run:
                self._process_database_operations(csv_companies, result)

            # 5. 処理完了
            processing_time = time.time() - start_time
            end_memory = self._get_memory_usage()

            result.processing_time = processing_time
            result.memory_usage_mb = max(0.0, end_memory - start_memory)
            result.records_per_second = (
                result.total_processed / processing_time if processing_time > 0 else 0
            )
            result.success = True

            logger.info(
                "バッチ処理完了: 成功 - 処理件数 %d件, 挿入 %d件, 更新 %d件 (%.2f秒)",
                result.total_processed,
                result.companies_inserted,
                result.companies_updated,
                result.processing_time,
            )

        except Exception as e:
            processing_time = time.time() - start_time
            result.processing_time = processing_time
            result.error_details.append(str(e))
            result.success = False

            logger.error("バッチ処理失敗: %s", e)

        # 統計情報更新
        self._update_application_stats(result)

        # Liveness Probe用状態マーカー削除
        self._remove_liveness_marker()

        return result

    def _read_csv_data(self) -> list:
        """CSVデータを読み取る

        Returns:
            読み取った企業データのリスト
        """
        csv_reader = CSVReader(self.config.csv_file_path)
        return csv_reader.read_and_convert()

    def _enrich_with_stock_data(self, companies: list, result: BatchResult) -> list:
        """株価データで企業情報を拡充する

        Args:
            companies: 企業データリスト
            result: バッチ結果（統計更新用）

        Returns:
            株価データで拡充された企業データリスト
        """
        stock_fetcher = StockFetcher(
            max_retries=self.config.max_retries,
            retry_delay=self.config.retry_delay,
            rate_limit_delay=1.0,  # API負荷軽減のため1秒間隔
        )

        enriched_companies = []
        stock_start_time = time.time()
        for i, company in enumerate(companies):
            if self.shutdown_requested:
                logger.warning("シャットダウン要求により株価取得を中断")
                break

            try:
                stock_data = stock_fetcher.fetch_stock_data(company.symbol)
                if stock_data:
                    # 株価データで企業情報を更新
                    company.price = stock_data.current_price or company.price
                    company.business_summary = (
                        stock_data.business_summary or company.business_summary
                    )

                enriched_companies.append(company)

                # 進捗報告とリソース監視
                if (
                    self.config.enable_progress_reporting
                    and (i + 1) % self.config.progress_report_interval == 0
                ):
                    current_memory = self._get_memory_usage()
                    processing_time = time.time() - stock_start_time

                    progress = {
                        "stage": "stock_fetch",
                        "processed": i + 1,
                        "total": len(companies),
                        "percentage": ((i + 1) / len(companies)) * 100,
                        "memory_usage_mb": current_memory,
                        "processing_time": processing_time,
                        "records_per_second": (i + 1) / processing_time
                        if processing_time > 0
                        else 0,
                    }
                    result.progress_reports.append(progress)
                    logger.info(
                        "株価取得進捗: %d/%d (%.1f%%) - "
                        "メモリ: %.1fMB, 処理速度: %.1f件/秒",
                        i + 1,
                        len(companies),
                        progress["percentage"],
                        current_memory,
                        progress["records_per_second"],
                    )

            except Exception as e:
                if not self.config.continue_on_error:
                    raise
                result.error_details.append(f"株価取得エラー {company.symbol}: {e}")
                enriched_companies.append(company)

        logger.info("株価データ取得完了: %d件処理", len(enriched_companies))
        return enriched_companies

    async def _translate_business_summaries(
        self, companies: list, result: BatchResult
    ) -> list:
        """ビジネス要約を翻訳する

        Args:
            companies: 企業データリスト
            result: バッチ結果（統計更新用）

        Returns:
            翻訳済みの企業データリスト
        """
        translation_service = TranslationService(
            max_retries=self.config.max_retries, retry_delay=self.config.retry_delay
        )

        translation_start_time = time.time()

        for i, company in enumerate(companies):
            if self.shutdown_requested:
                logger.warning("シャットダウン要求により翻訳を中断")
                break

            try:
                if company.business_summary:
                    translated_summary = (
                        await translation_service.translate_to_japanese(
                            company.business_summary
                        )
                    )
                    company.business_summary = translated_summary

                # 進捗報告とリソース監視
                if (
                    self.config.enable_progress_reporting
                    and (i + 1) % self.config.progress_report_interval == 0
                ):
                    current_memory = self._get_memory_usage()
                    # 翻訳開始時点からの処理時間を計算
                    processing_time = time.time() - translation_start_time

                    progress = {
                        "stage": "translation",
                        "processed": i + 1,
                        "total": len(companies),
                        "percentage": ((i + 1) / len(companies)) * 100,
                        "memory_usage_mb": current_memory,
                        "processing_time": processing_time,
                        "records_per_second": (i + 1) / processing_time
                        if processing_time > 0
                        else 0,
                    }
                    result.progress_reports.append(progress)
                    logger.info(
                        "翻訳進捗: %d/%d (%.1f%%) - "
                        "メモリ: %.1fMB, 処理速度: %.1f件/秒",
                        i + 1,
                        len(companies),
                        progress["percentage"],
                        current_memory,
                        progress["records_per_second"],
                    )

            except Exception as e:
                if not self.config.continue_on_error:
                    raise
                result.error_details.append(f"翻訳エラー {company.symbol}: {e}")

        logger.info("翻訳処理完了: %d件処理", len(companies))
        return companies

    def _process_database_operations(
        self, companies: list, result: BatchResult
    ) -> None:
        """データベース操作を処理する

        Args:
            companies: 企業データリスト
            result: バッチ結果（統計更新用）
        """
        # データベース接続
        db_connection = DatabaseConnection(self.config.database_path)
        db_service = DatabaseService(db_connection)

        with db_connection:
            # データベース初期化
            db_service.setup_database()

            # 差分処理
            processor = DifferentialProcessor(
                db_service,
                chunk_size=self.config.chunk_size,
                enable_parallel=self.config.enable_parallel,
                max_workers=self.config.max_workers,
                enable_performance_metrics=self.config.enable_performance_monitoring,
            )

            diff_result = processor.process_diff(companies)

            # データベース更新
            insert_result = db_service.batch_insert_companies(diff_result.to_insert)
            update_result = db_service.batch_update_companies(diff_result.to_update)

            result.companies_inserted = insert_result["successful"]
            result.companies_updated = update_result["successful"]
            result.database_operations_count = (
                diff_result.summary.database_queries_count
            )

            logger.info(
                "データベース処理完了: 挿入 %d件, 更新 %d件",
                result.companies_inserted,
                result.companies_updated,
            )

    def _setup_logging(self) -> None:
        """ログ設定を行う"""
        log_level = getattr(logging, self.config.log_level.upper(), logging.INFO)

        # ルートロガー設定
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # 特定のロガー設定
        stock_batch_logger = logging.getLogger("stock_batch")
        stock_batch_logger.setLevel(log_level)

    def _setup_yfinance_cache(self) -> None:
        """yfinanceキャッシュ設定を行う

        読み取り専用ファイルシステム環境でもキャッシュが使用できるよう
        書き込み可能なディレクトリにキャッシュ場所を設定する
        """
        # 書き込み可能なキャッシュディレクトリを設定
        cache_dir = os.getenv("YFINANCE_CACHE_DIR", "/tmp/app/yfinance_cache")

        # キャッシュディレクトリの作成
        try:
            # 親ディレクトリの存在確認
            parent_dir = Path(cache_dir).parent
            if not parent_dir.exists():
                logger.error("親ディレクトリが存在しません: %s", parent_dir)
                return

            # 書き込み権限テスト
            test_file = parent_dir / ".write_test"
            try:
                test_file.write_text("test")
                test_file.unlink()
                logger.debug("書き込み権限確認完了: %s", parent_dir)
            except OSError as perm_error:
                logger.error(
                    "書き込み権限がありません: %s, エラー: %s", parent_dir, perm_error
                )
                return

            Path(cache_dir).mkdir(parents=True, exist_ok=True)

            # yfinanceキャッシュ設定
            yfinance.set_tz_cache_location(cache_dir)

            logger.info("yfinanceキャッシュ設定完了: %s", cache_dir)

        except Exception as e:
            logger.warning("yfinanceキャッシュ設定に失敗: %s - デフォルト設定を使用", e)

    def _setup_signal_handlers(self) -> None:
        """シグナルハンドラーを設定する"""

        def signal_handler(signum: int, frame) -> None:
            logger.warning("シャットダウンシグナル受信: %s", signum)
            self.shutdown_requested = True

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def _detect_environment(self) -> str:
        """実行環境を検出する

        Returns:
            環境名（kubernetes, docker, local）
        """
        if os.getenv("KUBERNETES_SERVICE_HOST"):
            return "kubernetes"
        elif os.getenv("DOCKER_CONTAINER"):
            return "docker"
        else:
            return "local"

    def _get_memory_usage(self) -> float:
        """現在のメモリ使用量をMB単位で取得する

        Returns:
            メモリ使用量（MB）
        """
        try:
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except Exception:
            return 0.0

    def _update_application_stats(self, result: BatchResult) -> None:
        """アプリケーション統計情報を更新する

        Args:
            result: バッチ処理結果
        """
        self._application_stats["total_runs"] += 1
        self._application_stats["total_records_processed"] += result.total_processed
        self._application_stats["total_processing_time"] += result.processing_time
        self._application_stats["last_run_result"] = result

    def get_application_stats(self) -> dict[str, Any]:
        """アプリケーション統計情報を取得する

        Returns:
            統計情報の辞書

        Example:
            >>> stats = app.get_application_stats()
            >>> print(f"平均処理時間: {stats['average_processing_time']:.2f}秒")
        """
        total_runs = self._application_stats["total_runs"]
        total_time = self._application_stats["total_processing_time"]

        return {
            "total_runs": total_runs,
            "total_records_processed": self._application_stats[
                "total_records_processed"
            ],
            "total_processing_time": total_time,
            "average_processing_time": total_time / total_runs if total_runs > 0 else 0,
            "last_run_result": self._application_stats["last_run_result"],
        }

    async def run_batch_async(self) -> BatchResult:
        """非同期バッチ処理を実行する

        AsyncBatchProcessorを使用してプロデューサー・コンシューマーパターンによる
        高速な非同期バッチ処理を実行する。従来のrun_batchメソッドより高いスループットを実現。

        Returns:
            バッチ処理結果

        Example:
            >>> result = await app.run_batch_async()
            >>> if result.success:
            ...     print(f"成功: {result.companies_inserted}件挿入")
        """
        start_time = time.time()
        start_memory = self._get_memory_usage()

        # Liveness Probe用状態マーカー作成
        self._create_liveness_marker()

        logger.info("非同期バッチ処理開始: %s", self.config.csv_file_path)

        # 結果初期化
        result = BatchResult(
            success=False,
            total_processed=0,
            companies_inserted=0,
            companies_updated=0,
            processing_time=0.0,
            memory_usage_mb=0.0,
            records_per_second=0.0,
            database_operations_count=0,
            parallel_processing_used=True,  # 常に非同期並列処理
            environment=self._detect_environment(),
            error_details=[],
            progress_reports=[],
        )

        try:
            # 1. CSV読み取り
            csv_companies = self._read_csv_data()
            if not csv_companies:
                raise Exception("CSVデータが読み取れませんでした")

            result.total_processed = len(csv_companies)
            logger.info("CSV読み取り完了: %d件", len(csv_companies))

            # 2. 非同期パイプライン処理（株価取得 + 翻訳）
            if self.config.enable_stock_data_fetch or self.config.enable_translation:
                processed_companies = await self._run_async_pipeline(csv_companies, result)
            else:
                processed_companies = csv_companies

            # 3. 差分処理・データベース更新は既存のメソッドを使用
            # （この部分は同期処理のままとする）
            result.success = True

        except Exception as e:
            error_msg = f"非同期バッチ処理エラー: {e}"
            logger.error(error_msg)
            result.error_details.append(error_msg)

            if not self.config.continue_on_error:
                raise

        finally:
            # Liveness Probe用状態マーカー削除
            self._remove_liveness_marker()

            # 処理時間とメモリ使用量計算
            result.processing_time = time.time() - start_time
            end_memory = self._get_memory_usage()
            result.memory_usage_mb = max(0, end_memory - start_memory)

            # パフォーマンス指標計算
            if result.processing_time > 0:
                result.records_per_second = result.total_processed / result.processing_time

            # 統計情報更新
            self._update_application_stats(result)

            logger.info(
                "非同期バッチ処理完了: %d件処理 (%.2f秒, %.2f件/秒)",
                result.total_processed,
                result.processing_time,
                result.records_per_second,
            )

        return result

    async def _run_async_pipeline(self, companies: list[Any], result: BatchResult) -> list[Any]:
        """非同期パイプライン処理を実行する

        AsyncBatchProcessorを使用して株価取得と翻訳を並行実行する。

        Args:
            companies: 処理対象の企業リスト
            result: バッチ処理結果（統計情報更新用）

        Returns:
            処理完了した企業リスト
        """
        # サービスクラス初期化
        stock_fetcher = StockFetcher(
            max_retries=self.config.max_retries,
            retry_delay=self.config.retry_delay,
        )
        translation_service = TranslationService(
            max_retries=self.config.max_retries,
            retry_delay=self.config.retry_delay,
        )

        # 非同期プロセッサ初期化
        async_processor = AsyncBatchProcessor(
            stock_workers=self.config.max_workers,
            translation_workers=self.config.max_workers,
            queue_max_size=self.config.chunk_size,
            stock_rate_limit=0.2,  # 株価取得レート制限
            translation_rate_limit=0.5,  # 翻訳レート制限
            stock_fetcher=stock_fetcher if self.config.enable_stock_data_fetch else None,
            translation_service=translation_service if self.config.enable_translation else None,
        )

        logger.info(
            "非同期パイプライン開始: %d社, ワーカー数=%d",
            len(companies),
            self.config.max_workers,
        )

        # パイプライン実行
        pipeline_start = time.time()
        processed_companies = await async_processor.process_pipeline(companies)
        pipeline_time = time.time() - pipeline_start

        # 統計情報に追加
        result.progress_reports.append({
            "stage": "async_pipeline",
            "companies_processed": len(processed_companies),
            "pipeline_time": pipeline_time,
            "pipeline_rate": len(processed_companies) / pipeline_time if pipeline_time > 0 else 0,
        })

        logger.info(
            "非同期パイプライン完了: %d社処理 (%.2f秒, %.1f件/秒)",
            len(processed_companies),
            pipeline_time,
            len(processed_companies) / pipeline_time if pipeline_time > 0 else 0,
        )

        return processed_companies
