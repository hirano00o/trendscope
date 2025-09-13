"""パフォーマンス最適化ユーティリティ

月次スイングトレードシステムのパフォーマンス向上を目的とした
最適化機能を提供する。

主要機能:
- メモリベースキャッシュシステム
- 並列処理フレームワーク
- 計算結果の中間キャッシュ
- データ前処理の最適化
- タイムベースキャッシュ無効化

設計原則:
- スレッドセーフな実装
- メモリ効率を考慮した設計
- 設定可能なキャッシュポリシー
- 透明性の高いキャッシュ操作
"""

import asyncio
import hashlib
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union

import pandas as pd
import structlog

logger = structlog.get_logger(__name__)

T = TypeVar("T")


class MemoryCache:
    """スレッドセーフなメモリベースキャッシュ.
    
    LRU (Least Recently Used) 方式とTTL (Time To Live) を組み合わせた
    高性能キャッシュシステム。金融データの特性を考慮した設計。
    
    特徴:
    - スレッドセーフな操作
    - 自動的な期限切れデータの削除
    - メモリ使用量の制限
    - 統計情報の収集
    
    Example:
        >>> cache = MemoryCache(max_size=100, default_ttl=300)
        >>> cache.set("AAPL_data", stock_data, ttl=600)
        >>> data = cache.get("AAPL_data")
    """
    
    def __init__(
        self, 
        max_size: int = 1000, 
        default_ttl: int = 300
    ) -> None:
        """初期化.
        
        Args:
            max_size: 最大キャッシュエントリ数
            default_ttl: デフォルトTTL（秒）
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._access_times: Dict[str, float] = {}
        self._lock = threading.RLock()
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "evictions": 0
        }
    
    def _is_expired(self, key: str) -> bool:
        """キーが期限切れかどうかを確認.
        
        Args:
            key: キャッシュキー
            
        Returns:
            bool: 期限切れの場合True
        """
        if key not in self._cache:
            return True
        
        entry = self._cache[key]
        if entry["expires_at"] < time.time():
            return True
        
        return False
    
    def _evict_expired(self) -> None:
        """期限切れエントリを削除."""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry["expires_at"] < current_time
        ]
        
        for key in expired_keys:
            del self._cache[key]
            del self._access_times[key]
            self._stats["evictions"] += 1
    
    def _evict_lru(self) -> None:
        """LRU方式で最も古いエントリを削除."""
        if not self._access_times:
            return
        
        lru_key = min(self._access_times.keys(), key=lambda k: self._access_times[k])
        del self._cache[lru_key]
        del self._access_times[lru_key]
        self._stats["evictions"] += 1
    
    def get(self, key: str) -> Optional[Any]:
        """キャッシュからデータを取得.
        
        Args:
            key: キャッシュキー
            
        Returns:
            Optional[Any]: キャッシュされたデータ、存在しない場合はNone
        """
        with self._lock:
            # 期限切れチェック
            if self._is_expired(key):
                if key in self._cache:
                    del self._cache[key]
                    del self._access_times[key]
                self._stats["misses"] += 1
                return None
            
            # アクセス時刻を更新
            self._access_times[key] = time.time()
            self._stats["hits"] += 1
            
            return self._cache[key]["value"]
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """キャッシュにデータを設定.
        
        Args:
            key: キャッシュキー
            value: キャッシュするデータ
            ttl: TTL（秒）、Noneの場合はdefault_ttlを使用
        """
        with self._lock:
            # 期限切れエントリを削除
            self._evict_expired()
            
            # キャッシュサイズ制限
            while len(self._cache) >= self.max_size:
                self._evict_lru()
            
            # TTL設定
            if ttl is None:
                ttl = self.default_ttl
            
            expires_at = time.time() + ttl
            
            # エントリを追加
            self._cache[key] = {
                "value": value,
                "expires_at": expires_at,
                "created_at": time.time()
            }
            self._access_times[key] = time.time()
            self._stats["sets"] += 1
    
    def delete(self, key: str) -> bool:
        """キャッシュからデータを削除.
        
        Args:
            key: キャッシュキー
            
        Returns:
            bool: 削除に成功した場合True
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                del self._access_times[key]
                return True
            return False
    
    def clear(self) -> None:
        """キャッシュを全削除."""
        with self._lock:
            self._cache.clear()
            self._access_times.clear()
            self._stats = {
                "hits": 0,
                "misses": 0,
                "sets": 0,
                "evictions": 0
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """キャッシュ統計情報を取得.
        
        Returns:
            Dict[str, Any]: 統計情報
        """
        with self._lock:
            total_requests = self._stats["hits"] + self._stats["misses"]
            hit_rate = (
                self._stats["hits"] / total_requests 
                if total_requests > 0 else 0.0
            )
            
            return {
                **self._stats,
                "total_requests": total_requests,
                "hit_rate": hit_rate,
                "cache_size": len(self._cache),
                "max_size": self.max_size
            }


# グローバルキャッシュインスタンス
_global_cache = MemoryCache(max_size=500, default_ttl=300)


def cache_result(
    ttl: int = 300,
    key_func: Optional[Callable[..., str]] = None,
    cache_instance: Optional[MemoryCache] = None
) -> Callable:
    """関数結果をキャッシュするデコレータ.
    
    関数の引数に基づいてキャッシュキーを生成し、
    結果をメモリにキャッシュする。
    
    Args:
        ttl: キャッシュの有効期限（秒）
        key_func: カスタムキー生成関数
        cache_instance: 使用するキャッシュインスタンス
        
    Returns:
        Callable: デコレータ関数
        
    Example:
        >>> @cache_result(ttl=600)
        ... async def fetch_data(symbol: str) -> pd.DataFrame:
        ...     return yf.download(symbol)
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        cache = cache_instance or _global_cache
        
        def generate_key(*args, **kwargs) -> str:
            """キャッシュキーを生成."""
            if key_func:
                return key_func(*args, **kwargs)
            
            # デフォルトキー生成
            key_data = f"{func.__module__}.{func.__name__}"
            if args:
                key_data += f":args:{str(args)}"
            if kwargs:
                key_data += f":kwargs:{str(sorted(kwargs.items()))}"
            
            return hashlib.md5(key_data.encode()).hexdigest()
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            key = generate_key(*args, **kwargs)
            
            # キャッシュから取得を試行
            cached_result = cache.get(key)
            if cached_result is not None:
                logger.debug(
                    f"キャッシュヒット: {func.__name__}",
                    cache_key=key,
                    function=func.__name__
                )
                return cached_result
            
            # 関数を実行
            start_time = time.time()
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            execution_time = time.time() - start_time
            
            # 結果をキャッシュ
            cache.set(key, result, ttl=ttl)
            
            logger.debug(
                f"関数実行完了: {func.__name__}",
                cache_key=key,
                execution_time=execution_time,
                function=func.__name__
            )
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            key = generate_key(*args, **kwargs)
            
            # キャッシュから取得を試行
            cached_result = cache.get(key)
            if cached_result is not None:
                logger.debug(
                    f"キャッシュヒット: {func.__name__}",
                    cache_key=key,
                    function=func.__name__
                )
                return cached_result
            
            # 関数を実行
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # 結果をキャッシュ
            cache.set(key, result, ttl=ttl)
            
            logger.debug(
                f"関数実行完了: {func.__name__}",
                cache_key=key,
                execution_time=execution_time,
                function=func.__name__
            )
            
            return result
        
        # 関数がasyncかどうかで適切なラッパーを返す
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def parallel_execute(
    tasks: List[Callable],
    max_workers: Optional[int] = None
) -> List[Any]:
    """関数のリストを並列実行.
    
    CPUバウンドなタスクに対してThreadPoolExecutorを使用した
    並列実行を提供する。
    
    Args:
        tasks: 実行する関数のリスト
        max_workers: 最大ワーカー数
        
    Returns:
        List[Any]: 実行結果のリスト
        
    Example:
        >>> tasks = [
        ...     lambda: calculate_sma(data, 20),
        ...     lambda: calculate_rsi(data, 14),
        ...     lambda: calculate_macd(data)
        ... ]
        >>> results = parallel_execute(tasks, max_workers=3)
    """
    if not tasks:
        return []
    
    if max_workers is None:
        max_workers = min(len(tasks), 4)  # 最大4並列
    
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(task) for task in tasks]
        results = [future.result() for future in futures]
    
    execution_time = time.time() - start_time
    
    logger.info(
        f"並列実行完了",
        task_count=len(tasks),
        max_workers=max_workers,
        execution_time=execution_time,
        avg_time_per_task=execution_time / len(tasks)
    )
    
    return results


async def async_parallel_execute(
    coroutines: List[Callable],
    semaphore_limit: int = 10
) -> List[Any]:
    """コルーチンのリストを並列実行.
    
    I/Oバウンドなタスクに対してasyncioを使用した
    並列実行を提供する。
    
    Args:
        coroutines: 実行するコルーチンのリスト
        semaphore_limit: 同時実行数制限
        
    Returns:
        List[Any]: 実行結果のリスト
        
    Example:
        >>> coroutines = [
        ...     fetch_data("AAPL"),
        ...     fetch_data("MSFT"),
        ...     fetch_data("GOOGL")
        ... ]
        >>> results = await async_parallel_execute(coroutines)
    """
    if not coroutines:
        return []
    
    semaphore = asyncio.Semaphore(semaphore_limit)
    
    async def limited_coroutine(coro):
        async with semaphore:
            return await coro
    
    start_time = time.time()
    
    tasks = [limited_coroutine(coro) for coro in coroutines]
    results = await asyncio.gather(*tasks)
    
    execution_time = time.time() - start_time
    
    logger.info(
        f"非同期並列実行完了",
        task_count=len(coroutines),
        semaphore_limit=semaphore_limit,
        execution_time=execution_time,
        avg_time_per_task=execution_time / len(coroutines)
    )
    
    return results


class DataFrameCache:
    """DataFrame専用の最適化キャッシュ.
    
    pandas DataFrameに特化したキャッシュシステム。
    メモリ効率とパフォーマンスを重視した設計。
    
    特徴:
    - DataFrame専用の最適化
    - カラムベースのアクセス
    - 計算結果の中間キャッシュ
    - メモリ使用量の監視
    
    Example:
        >>> df_cache = DataFrameCache()
        >>> df_cache.cache_dataframe("AAPL_data", stock_data)
        >>> sma_20 = df_cache.get_or_compute(
        ...     "AAPL_sma_20",
        ...     lambda: calculate_sma(stock_data, 20)
        ... )
    """
    
    def __init__(self, max_memory_mb: int = 100) -> None:
        """初期化.
        
        Args:
            max_memory_mb: 最大メモリ使用量（MB）
        """
        self.max_memory_mb = max_memory_mb
        self._cache: Dict[str, Any] = {}
        self._memory_usage: Dict[str, float] = {}
        self._lock = threading.RLock()
    
    def _estimate_memory_usage(self, obj: Any) -> float:
        """オブジェクトのメモリ使用量を推定（MB単位）.
        
        Args:
            obj: メモリ使用量を推定するオブジェクト
            
        Returns:
            float: 推定メモリ使用量（MB）
        """
        if isinstance(obj, pd.DataFrame):
            return obj.memory_usage(deep=True).sum() / 1024 / 1024
        else:
            # 簡易推定
            import sys
            return sys.getsizeof(obj) / 1024 / 1024
    
    def _evict_if_needed(self, required_memory: float) -> None:
        """メモリ不足の場合にエントリを削除.
        
        Args:
            required_memory: 必要なメモリ量（MB）
        """
        current_usage = sum(self._memory_usage.values())
        
        if current_usage + required_memory <= self.max_memory_mb:
            return
        
        # 使用量の多い順にソートして削除
        sorted_keys = sorted(
            self._memory_usage.keys(),
            key=lambda k: self._memory_usage[k],
            reverse=True
        )
        
        for key in sorted_keys:
            if current_usage + required_memory <= self.max_memory_mb:
                break
            
            current_usage -= self._memory_usage[key]
            del self._cache[key]
            del self._memory_usage[key]
            
            logger.debug(f"メモリ不足によりキャッシュエントリを削除: {key}")
    
    def cache_dataframe(
        self, 
        key: str, 
        df: pd.DataFrame, 
        ttl: Optional[int] = None
    ) -> None:
        """DataFrameをキャッシュ.
        
        Args:
            key: キャッシュキー
            df: キャッシュするDataFrame
            ttl: TTL（秒）
        """
        with self._lock:
            memory_usage = self._estimate_memory_usage(df)
            self._evict_if_needed(memory_usage)
            
            expires_at = time.time() + (ttl or 300)
            
            self._cache[key] = {
                "data": df.copy(),
                "expires_at": expires_at,
                "created_at": time.time()
            }
            self._memory_usage[key] = memory_usage
            
            logger.debug(
                f"DataFrameをキャッシュ: {key}",
                memory_mb=memory_usage,
                shape=df.shape
            )
    
    def get_dataframe(self, key: str) -> Optional[pd.DataFrame]:
        """キャッシュからDataFrameを取得.
        
        Args:
            key: キャッシュキー
            
        Returns:
            Optional[pd.DataFrame]: DataFrame、存在しない場合はNone
        """
        with self._lock:
            if key not in self._cache:
                return None
            
            entry = self._cache[key]
            if entry["expires_at"] < time.time():
                del self._cache[key]
                del self._memory_usage[key]
                return None
            
            return entry["data"].copy()
    
    def get_or_compute(
        self,
        key: str,
        compute_func: Callable[[], Any],
        ttl: Optional[int] = None
    ) -> Any:
        """キャッシュから取得、なければ計算して保存.
        
        Args:
            key: キャッシュキー
            compute_func: 計算関数
            ttl: TTL（秒）
            
        Returns:
            Any: 計算結果
        """
        with self._lock:
            # キャッシュから取得を試行
            if key in self._cache:
                entry = self._cache[key]
                if entry["expires_at"] >= time.time():
                    return entry["data"]
                else:
                    del self._cache[key]
                    del self._memory_usage[key]
            
            # 計算実行
            start_time = time.time()
            result = compute_func()
            execution_time = time.time() - start_time
            
            # 結果をキャッシュ
            memory_usage = self._estimate_memory_usage(result)
            self._evict_if_needed(memory_usage)
            
            expires_at = time.time() + (ttl or 300)
            
            self._cache[key] = {
                "data": result,
                "expires_at": expires_at,
                "created_at": time.time()
            }
            self._memory_usage[key] = memory_usage
            
            logger.debug(
                f"計算結果をキャッシュ: {key}",
                execution_time=execution_time,
                memory_mb=memory_usage
            )
            
            return result
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """メモリ使用統計を取得.
        
        Returns:
            Dict[str, Any]: メモリ統計情報
        """
        with self._lock:
            total_usage = sum(self._memory_usage.values())
            
            return {
                "total_memory_mb": total_usage,
                "max_memory_mb": self.max_memory_mb,
                "memory_usage_percent": (total_usage / self.max_memory_mb) * 100,
                "cached_items": len(self._cache),
                "average_item_size_mb": (
                    total_usage / len(self._cache) if self._cache else 0
                )
            }


def get_cache_stats() -> Dict[str, Any]:
    """グローバルキャッシュの統計情報を取得.
    
    Returns:
        Dict[str, Any]: 統計情報
    """
    return _global_cache.get_stats()


def clear_cache() -> None:
    """グローバルキャッシュをクリア."""
    _global_cache.clear()
    logger.info("グローバルキャッシュをクリアしました")


def cache_key_for_symbol_and_period(
    symbol: str, 
    period: str,
    analysis_type: str = "default"
) -> str:
    """シンボルと期間に基づくキャッシュキーを生成.
    
    Args:
        symbol: 株式シンボル
        period: 期間
        analysis_type: 分析タイプ
        
    Returns:
        str: キャッシュキー
    """
    return f"{analysis_type}:{symbol}:{period}:{datetime.now().strftime('%Y%m%d')}"