"""効率的差分処理サービス

大量データの効率的な比較・差分検出、並列処理によるパフォーマンス向上、
メモリ最適化機能を提供
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any

import psutil

from stock_batch.models.company import Company
from stock_batch.services.thread_safe_database_service import ThreadSafeDatabaseService

logger = logging.getLogger(__name__)


@dataclass
class ProcessingResult:
    """差分処理結果

    処理結果と統計情報を保持するデータクラス
    """

    to_insert: list[Company]
    to_update: list[Company]
    no_change: list[Company]
    summary: DiffSummary


@dataclass
class DiffSummary:
    """差分処理サマリー

    処理統計情報とメタデータを保持するデータクラス
    """

    total_processed: int
    processing_time: float
    memory_usage_mb: float
    records_per_second: float
    database_queries_count: int
    chunks_processed: int
    parallel_enabled: bool
    error_count: int
    error_details: list[str]


class DifferentialProcessor:
    """効率的差分処理サービスクラス

    大量の企業データを効率的に処理し、データベースとCSVデータの差分を検出する。
    メモリ最適化、並列処理、カスタム比較戦略をサポートする。

    Attributes:
        db_service: スレッドセーフデータベースサービス
        chunk_size: チャンク処理サイズ
        enable_parallel: 並列処理有効フラグ
        max_workers: 最大ワーカー数
        enable_memory_optimization: メモリ最適化有効フラグ
        enable_performance_metrics: パフォーマンス指標収集有効フラグ
        enable_incremental: 増分処理有効フラグ
        custom_comparison_func: カスタム比較関数

    Example:
        >>> db_service = ThreadSafeDatabaseService(thread_safe_conn)
        >>> processor = DifferentialProcessor(
        ...     db_service, chunk_size=1000, enable_parallel=True
        ... )
        >>> result = processor.process_diff(csv_companies)
        >>> print(f"挿入: {len(result.to_insert)}件")
    """

    def __init__(
        self,
        db_service: ThreadSafeDatabaseService,
        chunk_size: int = 1000,
        enable_parallel: bool = False,
        max_workers: int = 4,
        enable_memory_optimization: bool = False,
        enable_performance_metrics: bool = False,
        enable_incremental: bool = False,
        custom_comparison_func: Callable[[Company, Company], bool] | None = None,
    ) -> None:
        """DifferentialProcessor を初期化する

        Args:
            db_service: スレッドセーフデータベースサービス
            chunk_size: チャンク処理サイズ（デフォルト: 1000）
            enable_parallel: 並列処理有効（デフォルト: False）
            max_workers: 最大ワーカー数（デフォルト: 4）
            enable_memory_optimization: メモリ最適化有効（デフォルト: False）
            enable_performance_metrics: パフォーマンス指標収集有効（デフォルト: False）
            enable_incremental: 増分処理有効（デフォルト: False）
            custom_comparison_func: カスタム比較関数

        Example:
            >>> processor = DifferentialProcessor(
            ...     db_service,
            ...     chunk_size=500,
            ...     enable_parallel=True,
            ...     enable_memory_optimization=True
            ... )
        """
        self.db_service = db_service
        self.chunk_size = chunk_size
        self.enable_parallel = enable_parallel
        self.max_workers = max_workers
        self.enable_memory_optimization = enable_memory_optimization
        self.enable_performance_metrics = enable_performance_metrics
        self.enable_incremental = enable_incremental
        self.custom_comparison_func = custom_comparison_func

        # 統計情報
        self._processing_stats = {
            "total_runs": 0,
            "total_records_processed": 0,
            "total_processing_time": 0.0,
            "last_run_summary": None,
        }

    def process_diff(self, csv_companies: list[Company]) -> ProcessingResult:
        """CSVデータとデータベースの差分を効率的に処理する

        大量データを効率的に処理し、挿入・更新・変更なしの分類を行う。
        並列処理やメモリ最適化により高速化を図る。

        Args:
            csv_companies: CSVから読み取った企業データのリスト

        Returns:
            差分処理結果

        Example:
            >>> csv_data = csv_reader.read_and_convert()
            >>> result = processor.process_diff(csv_data)
            >>> print(f"処理時間: {result.summary.processing_time:.2f}秒")
        """
        start_time = time.time()
        start_memory = (
            self._get_memory_usage() if self.enable_performance_metrics else 0
        )

        logger.info(
            "差分処理開始: %d件, チャンクサイズ: %d, 並列処理: %s",
            len(csv_companies),
            self.chunk_size,
            self.enable_parallel,
        )

        # 結果格納
        to_insert = []
        to_update = []
        no_change = []
        error_count = 0
        error_details = []
        database_queries = 0

        try:
            if self.enable_parallel and len(csv_companies) > self.chunk_size:
                # 並列処理
                result = self._process_parallel(csv_companies)
                to_insert = result["to_insert"]
                to_update = result["to_update"]
                no_change = result["no_change"]
                database_queries = result["database_queries"]
                chunks_processed = result["chunks_processed"]
            else:
                # シーケンシャル処理
                result = self._process_sequential(csv_companies)
                to_insert = result["to_insert"]
                to_update = result["to_update"]
                no_change = result["no_change"]
                database_queries = result["database_queries"]
                chunks_processed = 1

        except Exception as e:
            error_count += 1
            error_details.append(str(e))
            logger.error("差分処理エラー: %s", e)

        # 処理時間とメモリ使用量計算
        processing_time = time.time() - start_time
        end_memory = self._get_memory_usage() if self.enable_performance_metrics else 0
        memory_usage = max(0, end_memory - start_memory)

        # 統計情報作成
        summary = DiffSummary(
            total_processed=len(csv_companies),
            processing_time=processing_time,
            memory_usage_mb=memory_usage,
            records_per_second=(
                len(csv_companies) / processing_time if processing_time > 0 else 0
            ),
            database_queries_count=database_queries,
            chunks_processed=chunks_processed,
            parallel_enabled=self.enable_parallel,
            error_count=error_count,
            error_details=error_details,
        )

        # 処理統計更新
        self._update_processing_stats(summary)

        logger.info(
            "差分処理完了: 挿入 %d件, 更新 %d件, 変更なし %d件 (%.2f秒)",
            len(to_insert),
            len(to_update),
            len(no_change),
            processing_time,
        )

        return ProcessingResult(
            to_insert=to_insert,
            to_update=to_update,
            no_change=no_change,
            summary=summary,
        )

    def _process_sequential(self, companies: list[Company]) -> dict[str, Any]:
        """シーケンシャル処理

        Args:
            companies: 処理する企業データのリスト

        Returns:
            処理結果の辞書
        """
        to_insert = []
        to_update = []
        no_change = []
        database_queries = 0

        if self.enable_memory_optimization:
            # メモリ効率的な処理（チャンク単位）
            chunks = self._create_chunks(companies, self.chunk_size)
            for chunk in chunks:
                chunk_result = self._process_chunk(chunk)
                to_insert.extend(chunk_result["to_insert"])
                to_update.extend(chunk_result["to_update"])
                no_change.extend(chunk_result["no_change"])
                database_queries += chunk_result["database_queries"]
        else:
            # 一括処理
            chunk_result = self._process_chunk(companies)
            to_insert = chunk_result["to_insert"]
            to_update = chunk_result["to_update"]
            no_change = chunk_result["no_change"]
            database_queries = chunk_result["database_queries"]

        return {
            "to_insert": to_insert,
            "to_update": to_update,
            "no_change": no_change,
            "database_queries": database_queries,
            "chunks_processed": 1,
        }

    def _process_parallel(self, companies: list[Company]) -> dict[str, Any]:
        """並列処理

        Args:
            companies: 処理する企業データのリスト

        Returns:
            処理結果の辞書
        """
        to_insert = []
        to_update = []
        no_change = []
        database_queries = 0
        chunks_processed = 0

        # チャンクに分割
        chunks = self._create_chunks(companies, self.chunk_size)
        logger.debug("並列処理開始: %d チャンク", len(chunks))

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 各チャンクを並列処理
            future_to_chunk = {
                executor.submit(self._process_chunk, chunk): chunk for chunk in chunks
            }

            for future in as_completed(future_to_chunk):
                try:
                    chunk_result = future.result()
                    to_insert.extend(chunk_result["to_insert"])
                    to_update.extend(chunk_result["to_update"])
                    no_change.extend(chunk_result["no_change"])
                    database_queries += chunk_result["database_queries"]
                    chunks_processed += 1

                except Exception as e:
                    logger.error("チャンク処理エラー: %s", e)

        return {
            "to_insert": to_insert,
            "to_update": to_update,
            "no_change": no_change,
            "database_queries": database_queries,
            "chunks_processed": chunks_processed,
        }

    def _process_chunk(self, chunk: list[Company]) -> dict[str, Any]:
        """チャンク処理

        Args:
            chunk: 処理するチャンクデータ

        Returns:
            チャンク処理結果
        """
        to_insert = []
        to_update = []
        no_change = []
        database_queries = 0

        # チャンク内のシンボルリストを取得
        symbols = [company.symbol for company in chunk]

        # 既存データを一括取得（効率化）
        existing_companies = {}
        for symbol in symbols:
            existing = self.db_service.get_company_by_symbol(symbol)
            if existing:
                existing_companies[symbol] = existing
            database_queries += 1

        # 差分判定
        for company in chunk:
            try:
                existing = existing_companies.get(company.symbol)

                if existing is None:
                    # 新規企業
                    to_insert.append(company)
                else:
                    # 既存企業：変更判定
                    if self._has_changes(existing, company):
                        to_update.append(company)
                    else:
                        no_change.append(company)

            except Exception as e:
                logger.warning("企業データ処理エラー: %s - %s", company.symbol, e)

        return {
            "to_insert": to_insert,
            "to_update": to_update,
            "no_change": no_change,
            "database_queries": database_queries,
        }

    def _has_changes(self, existing: Company, new: Company) -> bool:
        """企業データの変更を検出する

        カスタム比較関数が指定されている場合はそれを使用し、
        そうでなければデフォルトの比較を行う。

        Args:
            existing: 既存の企業データ
            new: 新しい企業データ

        Returns:
            変更がある場合True
        """
        if self.custom_comparison_func:
            return self.custom_comparison_func(existing, new)

        return self._default_has_changes(existing, new)

    def _default_has_changes(self, existing: Company, new: Company) -> bool:
        """デフォルトの変更検出ロジック

        Args:
            existing: 既存の企業データ
            new: 新しい企業データ

        Returns:
            重要な変更がある場合True
        """
        # 価格の変更チェック（小数点以下の誤差を考慮）
        if existing.price is not None and new.price is not None:
            price_diff = abs(existing.price - new.price)
            if price_diff > 0.01:  # 1銭以上の差
                return True

        # ビジネス要約の変更チェック
        existing_summary = (existing.business_summary or "").strip()
        new_summary = (new.business_summary or "").strip()
        if existing_summary != new_summary:
            return True

        # 企業名の変更チェック
        if existing.name.strip() != new.name.strip():
            return True

        # 市場の変更チェック
        if (existing.market or "").strip() != (new.market or "").strip():
            return True

        return False

    def _create_chunks(
        self, companies: list[Company], chunk_size: int
    ) -> list[list[Company]]:
        """企業データをチャンクに分割する

        Args:
            companies: 企業データのリスト
            chunk_size: チャンクサイズ

        Returns:
            チャンクのリスト
        """
        chunks = []
        for i in range(0, len(companies), chunk_size):
            chunk = companies[i : i + chunk_size]
            chunks.append(chunk)
        return chunks

    def _get_memory_usage(self) -> float:
        """現在のメモリ使用量をMB単位で取得する

        Returns:
            メモリ使用量（MB）
        """
        try:
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024  # MB
        except Exception:
            return 0.0

    def _update_processing_stats(self, summary: DiffSummary) -> None:
        """処理統計情報を更新する

        Args:
            summary: 処理サマリー
        """
        self._processing_stats["total_runs"] += 1
        self._processing_stats["total_records_processed"] += summary.total_processed
        self._processing_stats["total_processing_time"] += summary.processing_time
        self._processing_stats["last_run_summary"] = summary

    def get_processing_stats(self) -> dict[str, Any]:
        """処理統計情報を取得する

        Returns:
            処理統計情報の辞書

        Example:
            >>> stats = processor.get_processing_stats()
            >>> print(f"平均処理時間: {stats['average_processing_time']:.2f}秒")
        """
        total_runs = self._processing_stats["total_runs"]
        total_time = self._processing_stats["total_processing_time"]

        return {
            "total_runs": total_runs,
            "total_records_processed": self._processing_stats[
                "total_records_processed"
            ],
            "total_processing_time": total_time,
            "average_processing_time": total_time / total_runs if total_runs > 0 else 0,
            "last_run_summary": self._processing_stats["last_run_summary"],
        }

    def reset_stats(self) -> None:
        """統計情報をリセットする

        Example:
            >>> processor.reset_stats()
        """
        self._processing_stats = {
            "total_runs": 0,
            "total_records_processed": 0,
            "total_processing_time": 0.0,
            "last_run_summary": None,
        }
        logger.debug("処理統計情報をリセットしました")
