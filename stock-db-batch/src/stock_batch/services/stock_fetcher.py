"""yfinance株価取得サービス

yfinanceライブラリを使用した株価・企業情報の取得機能を提供
"""

from __future__ import annotations

import asyncio
import logging
import re
import time
from dataclasses import dataclass
from typing import Any

import yfinance as yf

logger = logging.getLogger(__name__)


@dataclass
class StockData:
    """株価データを表すデータクラス

    yfinanceから取得した株価・企業情報を保持する

    Attributes:
        symbol: 株式シンボル（例: 1332.T）
        current_price: 現在価格
        business_summary: 企業概要（英語）
        volume: 出来高
        day_high: 日中高値
        day_low: 日中安値
        sector: セクター
        industry: 業界

    Example:
        >>> data = StockData(
        ...     symbol="1332.T",
        ...     current_price=877.8,
        ...     business_summary="Nissui Corporation",
        ...     sector="Consumer Defensive"
        ... )
        >>> print(data.symbol)
        "1332.T"
    """

    symbol: str
    current_price: float
    business_summary: str
    volume: int | None = None
    day_high: float | None = None
    day_low: float | None = None
    sector: str | None = None
    industry: str | None = None


class StockFetcher:
    """yfinance株価取得サービスクラス

    yfinanceライブラリを使用して株価データと企業情報を取得する。
    エラーハンドリング、リトライ機能、レート制限対策を含む。

    Attributes:
        max_retries: 最大リトライ回数
        retry_delay: リトライ間隔（秒）
        _stats: 取得統計情報

    Example:
        >>> fetcher = StockFetcher()
        >>> stock_data = fetcher.fetch_stock_data("1332.T")
        >>> if stock_data:
        ...     print(f"{stock_data.symbol}: ¥{stock_data.current_price}")
    """

    # 日本株シンボルの正規表現パターン
    # 対応取引所: .T(東京), .S(札幌), .F(福岡), .N(名古屋), .OS(大阪)
    JAPAN_SYMBOL_PATTERN = re.compile(r"^[A-Z0-9]{3,4}\.(T|S|F|N|OS)$")

    def __init__(
        self,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        rate_limit_delay: float = 0.5,
    ) -> None:
        """StockFetcher を初期化する

        Args:
            max_retries: 最大リトライ回数（デフォルト: 3）
            retry_delay: リトライ間隔秒数（デフォルト: 1.0）
            rate_limit_delay: API呼び出し間の待機時間秒数（デフォルト: 0.5）

        Example:
            >>> fetcher = StockFetcher(
            ...     max_retries=5, retry_delay=2.0, rate_limit_delay=1.0
            ... )
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.rate_limit_delay = rate_limit_delay
        self._last_request_time = 0.0
        self._stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_response_time": 0.0,
        }

    def fetch_stock_data(self, symbol: str) -> StockData | None:
        """指定された株式シンボルの株価データを取得する

        yfinanceを使用して最新の株価と企業情報を取得する。
        ネットワークエラーやデータ不備の場合はリトライを実行。

        Args:
            symbol: 株式シンボル（例: 1332.T）

        Returns:
            StockDataオブジェクト、取得失敗時はNone

        Example:
            >>> fetcher = StockFetcher()
            >>> data = fetcher.fetch_stock_data("1332.T")
            >>> if data:
            ...     print(f"価格: ¥{data.current_price}")
        """
        if not self.is_valid_symbol(symbol):
            logger.warning("無効な株式シンボル: %s", symbol)
            self._record_failure()
            return None

        # レート制限対応
        self._apply_rate_limit()

        start_time = time.time()
        self._stats["total_requests"] += 1

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.debug(
                    "株価データ取得開始: %s (試行 %d/%d)",
                    symbol,
                    attempt,
                    self.max_retries,
                )

                # yfinance Ticker オブジェクト作成
                ticker = yf.Ticker(symbol)

                # 直近の株価データ取得（1日分）
                hist = ticker.history(period="1d")
                if hist.empty:
                    logger.warning("株価データが見つかりません: %s", symbol)
                    self._record_failure()
                    return None

                # 最新の価格データ取得
                latest_data = hist.iloc[-1]
                current_price = float(latest_data.get("Close", 0))

                if current_price <= 0:
                    logger.warning(
                        "無効な株価データ: %s - 価格: %s", symbol, current_price
                    )
                    self._record_failure()
                    return None

                # 企業情報取得
                info = ticker.info or {}

                # StockData オブジェクト作成
                stock_data = StockData(
                    symbol=symbol,
                    current_price=current_price,
                    business_summary=info.get("longBusinessSummary", ""),
                    volume=self._safe_int(latest_data.get("Volume")),
                    day_high=self._safe_float(latest_data.get("High")),
                    day_low=self._safe_float(latest_data.get("Low")),
                    sector=info.get("sector"),
                    industry=info.get("industry"),
                )

                # 統計情報更新
                response_time = time.time() - start_time
                self._record_success(response_time)

                logger.debug(
                    "株価データ取得成功: %s - 価格: ¥%.2f (%.2f秒)",
                    symbol,
                    current_price,
                    response_time,
                )
                return stock_data

            except Exception as e:
                logger.warning(
                    "株価データ取得エラー: %s (試行 %d/%d) - %s",
                    symbol,
                    attempt,
                    self.max_retries,
                    e,
                )

                if attempt < self.max_retries:
                    logger.debug("リトライまで %s秒待機", self.retry_delay)
                    time.sleep(self.retry_delay)
                else:
                    logger.error("株価データ取得失敗（リトライ上限到達）: %s", symbol)

        self._record_failure()
        return None

    def fetch_multiple_stocks(self, symbols: list[str]) -> list[StockData]:
        """複数の株式データを取得する

        並列処理は行わず、順次取得してレート制限を回避する。
        取得結果は価格の降順でソートして返す。

        Args:
            symbols: 株式シンボルのリスト

        Returns:
            StockDataオブジェクトのリスト（取得成功分のみ）

        Example:
            >>> fetcher = StockFetcher()
            >>> symbols = ["1332.T", "1418.T", "130A.T"]
            >>> stock_data_list = fetcher.fetch_multiple_stocks(symbols)
            >>> for data in stock_data_list:
            ...     print(f"{data.symbol}: ¥{data.current_price}")
        """
        if not symbols:
            return []

        logger.info("複数株価データ取得開始: %d件", len(symbols))
        start_time = time.time()

        stock_data_list = []
        successful_count = 0

        for i, symbol in enumerate(symbols, 1):
            logger.debug("進捗: %d/%d - %s", i, len(symbols), symbol)

            stock_data = self.fetch_stock_data(symbol)
            if stock_data:
                stock_data_list.append(stock_data)
                successful_count += 1

            # レート制限対策：短時間の待機
            if i < len(symbols):  # 最後以外
                time.sleep(0.1)  # 100ms 待機

        # 価格の降順でソート
        stock_data_list.sort(key=lambda x: x.current_price, reverse=True)

        elapsed_time = time.time() - start_time
        logger.info(
            "複数株価データ取得完了: %d/%d件成功 (%.2f秒)",
            successful_count,
            len(symbols),
            elapsed_time,
        )

        return stock_data_list

    def is_valid_symbol(self, symbol: str) -> bool:
        """株式シンボルの形式を検証する

        日本株の形式かチェックする。
        対応する取引所識別子: .T(東京), .S(札幌), .F(福岡), .N(名古屋), .OS(大阪)

        Args:
            symbol: 検証する株式シンボル

        Returns:
            有効な形式の場合True、そうでなければFalse

        Example:
            >>> fetcher = StockFetcher()
            >>> fetcher.is_valid_symbol("1332.T")
            True
            >>> fetcher.is_valid_symbol("3698.S")
            True
            >>> fetcher.is_valid_symbol("INVALID")
            False
        """
        if not symbol or not isinstance(symbol, str):
            return False

        return bool(self.JAPAN_SYMBOL_PATTERN.match(symbol.upper()))

    def get_stats(self) -> dict[str, Any]:
        """取得統計情報を返す

        デバッグやモニタリング用に統計情報を提供する。

        Returns:
            統計情報の辞書

        Example:
            >>> fetcher = StockFetcher()
            >>> # 何回か取得処理実行後
            >>> stats = fetcher.get_stats()
            >>> print(f"成功率: {stats['success_rate']:.2%}")
        """
        total = self._stats["total_requests"]
        successful = self._stats["successful_requests"]

        success_rate = (successful / total) if total > 0 else 0.0
        avg_response_time = (
            (self._stats["total_response_time"] / successful) if successful > 0 else 0.0
        )

        return {
            "total_requests": total,
            "successful_requests": successful,
            "failed_requests": self._stats["failed_requests"],
            "success_rate": success_rate,
            "average_response_time": avg_response_time,
        }

    def _record_success(self, response_time: float) -> None:
        """成功統計を記録する

        Args:
            response_time: レスポンス時間（秒）
        """
        self._stats["successful_requests"] += 1
        self._stats["total_response_time"] += response_time

    def _record_failure(self) -> None:
        """失敗統計を記録する"""
        self._stats["failed_requests"] += 1

    def _safe_int(self, value: Any) -> int | None:
        """値を安全にint変換する

        Args:
            value: 変換対象の値

        Returns:
            変換成功時はint、失敗時はNone
        """
        try:
            if value is not None and str(value).strip():
                return int(float(value))
        except (ValueError, TypeError):
            pass
        return None

    def _safe_float(self, value: Any) -> float | None:
        """値を安全にfloat変換する

        Args:
            value: 変換対象の値

        Returns:
            変換成功時はfloat、失敗時はNone
        """
        try:
            if value is not None and str(value).strip():
                return float(value)
        except (ValueError, TypeError):
            pass
        return None

    def _apply_rate_limit(self) -> None:
        """レート制限を適用する

        前回のAPI呼び出しからの経過時間をチェックし、
        必要に応じて待機してAPIレート制限を回避する
        """
        # 初回リクエストの場合はレート制限を適用しない
        if self._last_request_time == 0.0:
            self._last_request_time = time.time()
            return

        current_time = time.time()
        elapsed_time = current_time - self._last_request_time

        if elapsed_time < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - elapsed_time
            logger.debug("レート制限待機: %.2f秒", sleep_time)
            time.sleep(sleep_time)

        self._last_request_time = time.time()

    async def fetch_stock_data_async(self, symbol: str) -> StockData | None:
        """指定された株式シンボルの株価データを非同期で取得する

        yfinanceを使用して最新の株価と企業情報を非同期で取得する。
        ネットワークエラーやデータ不備の場合はリトライを実行。

        Args:
            symbol: 株式シンボル（例: 1332.T）

        Returns:
            StockDataオブジェクト、取得失敗時はNone

        Example:
            >>> fetcher = StockFetcher()
            >>> data = await fetcher.fetch_stock_data_async("1332.T")
            >>> if data:
            ...     print(f"価格: ¥{data.current_price}")
        """
        if not self.is_valid_symbol(symbol):
            logger.warning("無効な株式シンボル: %s", symbol)
            self._record_failure()
            return None

        # レート制限対応（非同期版）
        await self._apply_rate_limit_async()

        start_time = time.time()
        self._stats["total_requests"] += 1

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.debug(
                    "株価データ取得開始: %s (試行 %d/%d)",
                    symbol,
                    attempt,
                    self.max_retries,
                )

                # yfinance処理を非同期で実行
                def _sync_yfinance_call():
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(period="1d")
                    info = ticker.info or {}
                    return hist, info

                # CPU集約的なyfinance処理をスレッドプールで実行
                loop = asyncio.get_event_loop()
                hist, info = await loop.run_in_executor(None, _sync_yfinance_call)

                if hist.empty:
                    logger.warning("株価データが見つかりません: %s", symbol)
                    self._record_failure()
                    return None

                # 最新の価格データ取得
                latest_data = hist.iloc[-1]
                current_price = float(latest_data.get("Close", 0))

                if current_price <= 0:
                    logger.warning(
                        "無効な株価データ: %s - 価格: %s", symbol, current_price
                    )
                    self._record_failure()
                    return None

                # StockData オブジェクト作成
                stock_data = StockData(
                    symbol=symbol,
                    current_price=current_price,
                    business_summary=info.get("longBusinessSummary", ""),
                    volume=self._safe_int(latest_data.get("Volume")),
                    day_high=self._safe_float(latest_data.get("High")),
                    day_low=self._safe_float(latest_data.get("Low")),
                    sector=info.get("sector"),
                    industry=info.get("industry"),
                )

                # 統計情報更新
                response_time = time.time() - start_time
                self._record_success(response_time)

                logger.debug(
                    "株価データ取得成功: %s - 価格: ¥%.2f (%.2f秒)",
                    symbol,
                    current_price,
                    response_time,
                )
                return stock_data

            except Exception as e:
                logger.warning(
                    "株価データ取得エラー: %s (試行 %d/%d) - %s",
                    symbol,
                    attempt,
                    self.max_retries,
                    e,
                )

                if attempt < self.max_retries:
                    logger.debug("リトライまで %s秒待機", self.retry_delay)
                    await asyncio.sleep(self.retry_delay)
                else:
                    logger.error("株価データ取得失敗（リトライ上限到達）: %s", symbol)

        self._record_failure()
        return None

    async def fetch_multiple_stocks_async(
        self, symbols: list[str], max_concurrent: int = 5
    ) -> list[StockData]:
        """複数の株式データを非同期で取得する

        並行処理でスループットを向上させながら、レート制限を遵守する。
        取得結果は価格の降順でソートして返す。

        Args:
            symbols: 株式シンボルのリスト
            max_concurrent: 最大並行実行数（デフォルト: 5）

        Returns:
            StockDataオブジェクトのリスト（取得成功分のみ）

        Example:
            >>> fetcher = StockFetcher()
            >>> symbols = ["1332.T", "1418.T", "130A.T"]
            >>> stock_data_list = await fetcher.fetch_multiple_stocks_async(symbols)
            >>> for data in stock_data_list:
            ...     print(f"{data.symbol}: ¥{data.current_price}")
        """
        if not symbols:
            return []

        logger.info("複数株価データ非同期取得開始: %d件", len(symbols))
        start_time = time.time()

        # セマフォで並行数を制御
        semaphore = asyncio.Semaphore(max_concurrent)

        async def fetch_with_semaphore(symbol: str) -> StockData | None:
            """セマフォ制御付きの株価取得"""
            async with semaphore:
                return await self.fetch_stock_data_async(symbol)

        # 全ての株価取得を並行実行
        tasks = [fetch_with_semaphore(symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 結果をフィルタリング
        stock_data_list = []
        successful_count = 0

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error("株価取得で例外発生 %s: %s", symbols[i], result)
            elif result is not None:
                stock_data_list.append(result)
                successful_count += 1

        # 価格の降順でソート
        stock_data_list.sort(key=lambda x: x.current_price, reverse=True)

        elapsed_time = time.time() - start_time
        logger.info(
            "複数株価データ非同期取得完了: %d/%d件成功 (%.2f秒)",
            successful_count,
            len(symbols),
            elapsed_time,
        )

        return stock_data_list

    async def _apply_rate_limit_async(self) -> None:
        """レート制限を非同期で適用する

        前回のAPI呼び出しからの経過時間をチェックし、
        必要に応じて非同期で待機してAPIレート制限を回避する
        """
        # 初回リクエストの場合はレート制限を適用しない
        if self._last_request_time == 0.0:
            self._last_request_time = time.time()
            return

        current_time = time.time()
        elapsed_time = current_time - self._last_request_time

        if elapsed_time < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - elapsed_time
            logger.debug("レート制限待機（非同期）: %.2f秒", sleep_time)
            await asyncio.sleep(sleep_time)

        self._last_request_time = time.time()
