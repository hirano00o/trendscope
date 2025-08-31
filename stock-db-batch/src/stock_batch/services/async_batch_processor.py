"""非同期バッチプロセッサ

プロデューサー・コンシューマーパターンによる非同期株価取得・翻訳処理
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ProcessingStats:
    """処理統計情報

    非同期処理の統計情報を保持するデータクラス
    """

    total_companies: int = 0
    stock_fetch_completed: int = 0
    translation_completed: int = 0
    stock_fetch_errors: int = 0
    translation_errors: int = 0
    processing_start_time: float = 0.0
    stock_fetch_time: float = 0.0
    translation_time: float = 0.0


class AsyncBatchProcessor:
    """非同期バッチプロセッサクラス

    株価取得と翻訳処理を非同期パイプラインで実行する。
    プロデューサー・コンシューマーパターンを使用してスループットを最大化。

    Attributes:
        stock_workers: 株価取得ワーカー数
        translation_workers: 翻訳ワーカー数
        queue_max_size: キューの最大サイズ
        stock_rate_limit: 株価取得レート制限（秒）
        translation_rate_limit: 翻訳レート制限（秒）

    Example:
        >>> processor = AsyncBatchProcessor(
        ...     stock_workers=5,
        ...     translation_workers=3,
        ...     queue_max_size=100
        ... )
        >>> await processor.start_pipeline()
        >>> # 処理実行
        >>> await processor.stop_pipeline()
    """

    def __init__(
        self,
        stock_workers: int = 5,
        translation_workers: int = 3,
        queue_max_size: int = 100,
        stock_rate_limit: float = 0.2,
        translation_rate_limit: float = 0.5,
        stock_fetcher: Any | None = None,
        translation_service: Any | None = None,
    ) -> None:
        """AsyncBatchProcessor を初期化する

        Args:
            stock_workers: 株価取得の並行ワーカー数（デフォルト: 5）
            translation_workers: 翻訳の並行ワーカー数（デフォルト: 3）
            queue_max_size: キューの最大サイズ（デフォルト: 100）
            stock_rate_limit: 株価取得のレート制限秒数（デフォルト: 0.2）
            translation_rate_limit: 翻訳のレート制限秒数（デフォルト: 0.5）
            stock_fetcher: StockFetcherのインスタンス
            translation_service: TranslationServiceのインスタンス

        Example:
            >>> processor = AsyncBatchProcessor(
            ...     stock_workers=3, translation_workers=2,
            ...     stock_fetcher=stock_fetcher, translation_service=translation_service
            ... )
        """
        self.stock_workers = stock_workers
        self.translation_workers = translation_workers
        self.queue_max_size = queue_max_size
        self.stock_rate_limit = stock_rate_limit
        self.translation_rate_limit = translation_rate_limit

        # キューの初期化
        self.stock_queue: asyncio.Queue = asyncio.Queue(maxsize=queue_max_size)
        self.translation_queue: asyncio.Queue = asyncio.Queue(maxsize=queue_max_size)
        self.result_queue: asyncio.Queue = asyncio.Queue(maxsize=queue_max_size)

        # セマフォの初期化
        self.stock_semaphore = asyncio.Semaphore(stock_workers)
        self.translation_semaphore = asyncio.Semaphore(translation_workers)

        # 実行状態
        self.is_running = False
        self._tasks: list[asyncio.Task] = []

        # 統計情報
        self.stats = ProcessingStats()
        self.errors: list[Exception] = []
        self.progress_reports: list[dict[str, Any]] = []

        # 設定
        self.enable_progress_reporting = False
        self.progress_report_interval = 10

        # 停止制御
        self._translation_shutdown_sent = False

        # 実際のサービスクラス
        self.stock_fetcher = stock_fetcher
        self.translation_service = translation_service

        # コールバック関数（外部から設定）
        self.stock_fetcher_func: Callable[[Any], Awaitable[Any]] | None = None
        self.translator_func: Callable[[Any], Awaitable[Any]] | None = None

        logger.info(
            "AsyncBatchProcessor初期化完了: "
            "stock_workers=%d, translation_workers=%d, queue_max_size=%d",
            stock_workers,
            translation_workers,
            queue_max_size,
        )

    async def start_pipeline(self) -> None:
        """非同期パイプラインを開始する

        株価取得ワーカーと翻訳ワーカーのタスクを開始する。

        Example:
            >>> await processor.start_pipeline()
        """
        if self.is_running:
            logger.warning("パイプラインは既に実行中です")
            return

        logger.info("非同期パイプライン開始")
        self.is_running = True
        self.stats.processing_start_time = time.time()

        # 株価取得ワーカー開始
        for i in range(self.stock_workers):
            task = asyncio.create_task(self._stock_fetch_worker(f"stock_worker_{i}"))
            self._tasks.append(task)

        # 翻訳ワーカー開始
        for i in range(self.translation_workers):
            task = asyncio.create_task(
                self._translation_worker(f"translation_worker_{i}")
            )
            self._tasks.append(task)

        logger.info(
            "ワーカー開始完了: stock=%d, translation=%d",
            self.stock_workers,
            self.translation_workers,
        )

    async def stop_pipeline(self) -> None:
        """非同期パイプラインを停止する

        全てのワーカータスクを停止し、リソースをクリーンアップする。

        Example:
            >>> await processor.stop_pipeline()
        """
        if not self.is_running:
            logger.warning("パイプラインは既に停止しています")
            return

        logger.info("非同期パイプライン停止開始")
        self.is_running = False

        # 全タスクのキャンセル
        for task in self._tasks:
            task.cancel()

        # タスク完了待機
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)

        self._tasks.clear()

        # 統計情報更新
        total_time = time.time() - self.stats.processing_start_time

        logger.info(
            "非同期パイプライン停止完了: 処理時間=%.2f秒, "
            "株価取得=%d件, 翻訳=%d件, エラー=%d件",
            total_time,
            self.stats.stock_fetch_completed,
            self.stats.translation_completed,
            len(self.errors),
        )

    async def process_companies(self, companies: list[Any]) -> list[Any]:
        """企業リストを非同期パイプラインで処理する

        株価取得と翻訳を並行実行し、処理済み企業リストを返す。

        Args:
            companies: 処理対象の企業リスト

        Returns:
            処理完了した企業リスト

        Example:
            >>> companies = [company1, company2, company3]
            >>> processed = await processor.process_companies(companies)
        """
        if not self.is_running:
            raise RuntimeError("パイプラインが開始されていません")

        self.stats.total_companies = len(companies)
        logger.info("企業処理開始: %d件", len(companies))

        # 企業データをキューに投入
        for company in companies:
            await self.stock_queue.put(company)

        # 終了シグナル投入（単一シグナルで全ワーカー連携停止）
        await self.stock_queue.put(None)

        # 処理完了まで待機
        processed_companies = []
        companies_received = 0

        while companies_received < len(companies):
            try:
                company = await asyncio.wait_for(self.result_queue.get(), timeout=10.0)
                if company is not None:
                    processed_companies.append(company)
                    companies_received += 1
            except TimeoutError:
                logger.warning(
                    "処理待機タイムアウト: %d/%d件完了",
                    companies_received,
                    len(companies),
                )
                break

        logger.info("企業処理完了: %d/%d件", companies_received, len(companies))
        return processed_companies

    async def _stock_fetch_worker(self, worker_name: str) -> None:
        """株価取得ワーカー

        キューから企業データを取得し、株価データを取得して翻訳キューに渡す。

        Args:
            worker_name: ワーカー名（ログ用）
        """
        logger.debug("株価取得ワーカー開始: %s", worker_name)

        last_request_time = 0.0

        try:
            while self.is_running:
                try:
                    # キューから企業データ取得
                    company = await self.stock_queue.get()

                    # 終了シグナル処理
                    if company is None:
                        # 最初のワーカーのみが翻訳ワーカーに停止シグナルを送信
                        if not self._translation_shutdown_sent:
                            self._translation_shutdown_sent = True
                            for _ in range(self.translation_workers):
                                await self.translation_queue.put(None)
                        break

                    # セマフォ取得（並行数制御）
                    async with self.stock_semaphore:
                        # レート制限適用
                        await self._apply_rate_limit(
                            last_request_time, self.stock_rate_limit
                        )
                        last_request_time = time.time()

                        # 株価取得処理
                        if self.stock_fetcher_func:
                            try:
                                start_time = time.time()
                                processed_company = await self.stock_fetcher_func(
                                    company
                                )
                                processing_time = time.time() - start_time

                                self.stats.stock_fetch_completed += 1
                                self.stats.stock_fetch_time += processing_time

                                # 翻訳キューに送信
                                await self.translation_queue.put(processed_company)

                                logger.debug(
                                    "%s: 株価取得完了 %s (%.3f秒)",
                                    worker_name,
                                    getattr(company, "symbol", "UNKNOWN"),
                                    processing_time,
                                )

                            except Exception as e:
                                self.stats.stock_fetch_errors += 1
                                self.errors.append(e)
                                logger.error(
                                    "%s: 株価取得エラー %s - %s",
                                    worker_name,
                                    getattr(company, "symbol", "UNKNOWN"),
                                    e,
                                )
                                # エラー時も翻訳キューに送信（処理継続）
                                await self.translation_queue.put(company)
                        else:
                            # 株価取得関数が未設定の場合はそのまま送信
                            await self.translation_queue.put(company)

                    # 進捗報告
                    if (
                        self.enable_progress_reporting
                        and self.stats.stock_fetch_completed
                        % self.progress_report_interval
                        == 0
                    ):
                        await self._report_progress("stock_fetch")

                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error("%s: 予期しないエラー - %s", worker_name, e)
                    self.errors.append(e)

        except asyncio.CancelledError:
            pass

        logger.debug("株価取得ワーカー終了: %s", worker_name)

    async def _translation_worker(self, worker_name: str) -> None:
        """翻訳ワーカー

        翻訳キューから企業データを取得し、翻訳処理を実行。

        Args:
            worker_name: ワーカー名（ログ用）
        """
        logger.debug("翻訳ワーカー開始: %s", worker_name)

        last_request_time = 0.0

        try:
            while self.is_running:
                try:
                    # キューから企業データ取得
                    company = await self.translation_queue.get()

                    # 終了シグナル処理
                    if company is None:
                        break

                    # セマフォ取得（並行数制御）
                    async with self.translation_semaphore:
                        # レート制限適用
                        await self._apply_rate_limit(
                            last_request_time, self.translation_rate_limit
                        )
                        last_request_time = time.time()

                        # 翻訳処理
                        if self.translator_func:
                            try:
                                start_time = time.time()
                                processed_company = await self.translator_func(company)
                                processing_time = time.time() - start_time

                                self.stats.translation_completed += 1
                                self.stats.translation_time += processing_time

                                # 結果キューに送信
                                await self.result_queue.put(processed_company)

                                logger.debug(
                                    "%s: 翻訳完了 %s (%.3f秒)",
                                    worker_name,
                                    getattr(company, "symbol", "UNKNOWN"),
                                    processing_time,
                                )

                            except Exception as e:
                                self.stats.translation_errors += 1
                                self.errors.append(e)
                                logger.error(
                                    "%s: 翻訳エラー %s - %s",
                                    worker_name,
                                    getattr(company, "symbol", "UNKNOWN"),
                                    e,
                                )
                                # エラー時も結果キューに送信（処理継続）
                                await self.result_queue.put(company)
                        else:
                            # 翻訳関数が未設定の場合はそのまま結果キューに送信
                            await self.result_queue.put(company)

                        # 進捗報告
                        if (
                            self.enable_progress_reporting
                            and self.stats.translation_completed
                            % self.progress_report_interval
                            == 0
                        ):
                            await self._report_progress("translation")

                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error("%s: 予期しないエラー - %s", worker_name, e)
                    self.errors.append(e)

        except asyncio.CancelledError:
            pass

        logger.debug("翻訳ワーカー終了: %s", worker_name)

    async def _apply_rate_limit(
        self, last_request_time: float, rate_limit: float
    ) -> None:
        """レート制限を適用する

        前回のリクエストからの経過時間をチェックし、必要に応じて待機。

        Args:
            last_request_time: 前回のリクエスト時刻
            rate_limit: レート制限間隔（秒）
        """
        if last_request_time == 0.0:
            return

        current_time = time.time()
        elapsed_time = current_time - last_request_time

        if elapsed_time < rate_limit:
            sleep_time = rate_limit - elapsed_time
            await asyncio.sleep(sleep_time)

    async def _report_progress(self, stage: str) -> None:
        """進捗報告を行う

        処理の進捗状況をログに出力し、統計情報を記録。

        Args:
            stage: 処理段階（"stock_fetch" または "translation"）
        """
        current_time = time.time()
        elapsed_time = current_time - self.stats.processing_start_time

        if stage == "stock_fetch":
            completed = self.stats.stock_fetch_completed
            errors = self.stats.stock_fetch_errors
        else:
            completed = self.stats.translation_completed
            errors = self.stats.translation_errors

        progress = {
            "stage": stage,
            "completed": completed,
            "errors": errors,
            "total": self.stats.total_companies,
            "percentage": (completed / self.stats.total_companies * 100)
            if self.stats.total_companies > 0
            else 0,
            "elapsed_time": elapsed_time,
            "processing_rate": completed / elapsed_time if elapsed_time > 0 else 0,
        }

        self.progress_reports.append(progress)

        logger.info(
            "進捗報告 [%s]: %d/%d件完了 (%.1f%%), エラー=%d件, 処理速度=%.1f件/秒",
            stage,
            completed,
            self.stats.total_companies,
            progress["percentage"],
            errors,
            progress["processing_rate"],
        )

    def get_stats(self) -> dict[str, Any]:
        """処理統計情報を取得する

        Returns:
            統計情報の辞書

        Example:
            >>> stats = processor.get_stats()
            >>> print(f"処理完了: {stats['stock_fetch_completed']}件")
        """
        total_time = time.time() - self.stats.processing_start_time

        return {
            "total_companies": self.stats.total_companies,
            "stock_fetch_completed": self.stats.stock_fetch_completed,
            "translation_completed": self.stats.translation_completed,
            "stock_fetch_errors": self.stats.stock_fetch_errors,
            "translation_errors": self.stats.translation_errors,
            "total_processing_time": total_time,
            "stock_fetch_avg_time": (
                self.stats.stock_fetch_time / self.stats.stock_fetch_completed
                if self.stats.stock_fetch_completed > 0
                else 0
            ),
            "translation_avg_time": (
                self.stats.translation_time / self.stats.translation_completed
                if self.stats.translation_completed > 0
                else 0
            ),
            "overall_rate": (
                self.stats.translation_completed / total_time if total_time > 0 else 0
            ),
            "error_rate": (
                (self.stats.stock_fetch_errors + self.stats.translation_errors)
                / (self.stats.total_companies * 2)
                * 100
                if self.stats.total_companies > 0
                else 0
            ),
        }

    async def process_pipeline(self, companies: list[Any]) -> list[Any]:
        """企業データのエンドツーエンド非同期パイプライン処理

        株価取得と翻訳を統合したパイプライン処理を実行する。
        実際のStockFetcherとTranslationServiceを使用してデータを処理する。

        Args:
            companies: 処理対象の企業リスト

        Returns:
            株価データと翻訳済みビジネス要約を含む企業リスト

        Example:
            >>> companies = [company1, company2, company3]
            >>> results = await processor.process_pipeline(companies)
            >>> for result in results:
            ...     print(f"{result.symbol}: {result.business_summary_ja}")
        """
        if not companies:
            return []

        if not self.stock_fetcher or not self.translation_service:
            raise RuntimeError("StockFetcherとTranslationServiceが必要です")

        logger.info("パイプライン処理開始: %d社", len(companies))
        start_time = time.time()

        # 結果格納用リスト
        results = []
        
        # 各企業に対して並行処理を実行
        semaphore = asyncio.Semaphore(min(self.stock_workers, self.translation_workers))
        
        async def process_company(company: Any) -> Any:
            """単一企業の処理"""
            async with semaphore:
                processed_company = company
                
                # 株価データ取得
                try:
                    if hasattr(self.stock_fetcher, 'fetch_stock_data_async'):
                        stock_data = await self.stock_fetcher.fetch_stock_data_async(company.symbol)
                        processed_company.stock_data = stock_data
                        logger.debug("株価取得成功: %s", company.symbol)
                    else:
                        logger.warning("株価取得メソッドが見つかりません: %s", company.symbol)
                        processed_company.stock_data = None
                except Exception as e:
                    logger.error("株価取得エラー %s: %s", company.symbol, e)
                    processed_company.stock_data = None
                
                # 翻訳処理
                try:
                    if hasattr(self.translation_service, 'translate_to_japanese_async'):
                        business_summary = getattr(company, 'business_summary', '') or ''
                        if business_summary:
                            translated_text = await self.translation_service.translate_to_japanese_async(business_summary)
                            processed_company.business_summary_ja = translated_text
                            logger.debug("翻訳成功: %s", company.symbol)
                        else:
                            processed_company.business_summary_ja = ''
                    else:
                        logger.warning("翻訳メソッドが見つかりません: %s", company.symbol)
                        processed_company.business_summary_ja = getattr(company, 'business_summary', '') or ''
                except Exception as e:
                    logger.error("翻訳エラー %s: %s", company.symbol, e)
                    processed_company.business_summary_ja = getattr(company, 'business_summary', '') or ''
                
                # 小さな遅延でレート制限を適用
                await asyncio.sleep(0.1)
                return processed_company

        # 並行処理実行
        tasks = [process_company(company) for company in companies]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 例外処理とクリーンアップ
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error("企業処理エラー %s: %s", companies[i].symbol, result)
                # エラー時も元の企業データを含める
                company = companies[i]
                company.stock_data = None
                company.business_summary_ja = getattr(company, 'business_summary', '') or ''
                final_results.append(company)
            else:
                final_results.append(result)

        processing_time = time.time() - start_time
        logger.info(
            "パイプライン処理完了: %d社処理 (%.2f秒)",
            len(final_results),
            processing_time,
        )

        return final_results
