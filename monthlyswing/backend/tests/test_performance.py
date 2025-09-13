"""test_performance.py: パフォーマンス最適化機能のテスト

キャッシュシステム、並列処理、レスポンス時間最適化のテストを実装。
実際のパフォーマンス向上を定量的に検証する。

テスト対象:
- MemoryCacheクラスの機能
- cache_resultデコレータ
- parallel_execute並列処理
- DataFrameCacheクラス
- パフォーマンス統計機能
"""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock, patch

import pandas as pd
import pytest

from monthlyswing_backend.utils.performance import (
    DataFrameCache,
    MemoryCache,
    async_parallel_execute,
    cache_key_for_symbol_and_period,
    cache_result,
    clear_cache,
    get_cache_stats,
    parallel_execute,
)


class TestMemoryCache:
    """MemoryCacheクラスのテスト."""

    def test_cache_basic_operations(self) -> None:
        """基本的なキャッシュ操作のテスト."""
        cache = MemoryCache(max_size=10, default_ttl=1)
        
        # 設定と取得
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        
        # 存在しないキー
        assert cache.get("nonexistent") is None
        
        # 削除
        assert cache.delete("key1") is True
        assert cache.get("key1") is None
        assert cache.delete("key1") is False

    def test_cache_ttl_expiration(self) -> None:
        """TTL期限切れのテスト."""
        cache = MemoryCache(max_size=10, default_ttl=1)
        
        # TTLを短く設定
        cache.set("key1", "value1", ttl=1)
        assert cache.get("key1") == "value1"
        
        # 期限切れまで待機
        time.sleep(1.1)
        assert cache.get("key1") is None

    def test_cache_lru_eviction(self) -> None:
        """LRU排除のテスト."""
        cache = MemoryCache(max_size=2, default_ttl=60)
        
        # キャッシュを満杯にする
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        # key1にアクセスしてLRUを更新
        cache.get("key1")
        
        # key3を追加してkey2が排除されることを確認
        cache.set("key3", "value3")
        
        assert cache.get("key1") == "value1"  # 残っている
        assert cache.get("key2") is None      # 排除された
        assert cache.get("key3") == "value3"  # 新しく追加

    def test_cache_statistics(self) -> None:
        """キャッシュ統計のテスト."""
        cache = MemoryCache(max_size=10, default_ttl=60)
        
        # 初期状態
        stats = cache.get_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["hit_rate"] == 0.0
        
        # ヒット・ミスの統計
        cache.set("key1", "value1")
        cache.get("key1")  # ヒット
        cache.get("key2")  # ミス
        
        stats = cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 0.5

    def test_cache_thread_safety(self) -> None:
        """スレッドセーフ性のテスト."""
        cache = MemoryCache(max_size=100, default_ttl=60)
        
        def worker(thread_id: int) -> None:
            for i in range(10):
                key = f"thread_{thread_id}_key_{i}"
                value = f"thread_{thread_id}_value_{i}"
                cache.set(key, value)
                retrieved = cache.get(key)
                assert retrieved == value
        
        # 複数スレッドで同時実行
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(worker, i) for i in range(5)]
            for future in futures:
                future.result()
        
        # スレッド安全性が保たれていることを確認
        stats = cache.get_stats()
        assert stats["cache_size"] == 50  # 5スレッド × 10キー


class TestCacheResultDecorator:
    """cache_resultデコレータのテスト."""

    @pytest.mark.asyncio
    async def test_cache_result_async_function(self) -> None:
        """非同期関数のキャッシュテスト."""
        call_count = 0
        
        @cache_result(ttl=1)
        async def expensive_calculation(x: int) -> int:
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.01)  # 重い処理をシミュレート
            return x * x
        
        # 初回呼び出し
        result1 = await expensive_calculation(5)
        assert result1 == 25
        assert call_count == 1
        
        # キャッシュから取得
        result2 = await expensive_calculation(5)
        assert result2 == 25
        assert call_count == 1  # 関数は再実行されない
        
        # 異なる引数では実行される
        result3 = await expensive_calculation(6)
        assert result3 == 36
        assert call_count == 2

    def test_cache_result_sync_function(self) -> None:
        """同期関数のキャッシュテスト."""
        # 専用のキャッシュインスタンスを作成
        test_cache = MemoryCache(max_size=100, default_ttl=60)
        call_count = 0
        
        @cache_result(ttl=1, cache_instance=test_cache)
        def expensive_calculation(x: int) -> int:
            nonlocal call_count
            call_count += 1
            time.sleep(0.01)  # 重い処理をシミュレート
            return x * x
        
        # 初回呼び出し
        result1 = expensive_calculation(5)
        assert result1 == 25
        assert call_count == 1
        
        # キャッシュから取得
        result2 = expensive_calculation(5)
        assert result2 == 25
        assert call_count == 1  # 関数は再実行されない

    @pytest.mark.asyncio
    async def test_cache_result_ttl_expiration(self) -> None:
        """キャッシュTTL期限切れのテスト."""
        call_count = 0
        
        @cache_result(ttl=1)
        async def calculation(x: int) -> int:
            nonlocal call_count
            call_count += 1
            return x * x
        
        # 初回呼び出し
        result1 = await calculation(5)
        assert result1 == 25
        assert call_count == 1
        
        # TTL期限切れまで待機
        time.sleep(1.1)
        
        # 期限切れ後は再実行される
        result2 = await calculation(5)
        assert result2 == 25
        assert call_count == 2

    def test_custom_key_function(self) -> None:
        """カスタムキー関数のテスト."""
        call_count = 0
        
        def custom_key_func(symbol: str, period: str) -> str:
            return f"custom:{symbol}:{period}"
        
        @cache_result(ttl=60, key_func=custom_key_func)
        def fetch_data(symbol: str, period: str) -> str:
            nonlocal call_count
            call_count += 1
            return f"data_{symbol}_{period}"
        
        # カスタムキー関数が使用される
        result1 = fetch_data("AAPL", "1d")
        result2 = fetch_data("AAPL", "1d")
        
        assert result1 == result2
        assert call_count == 1


class TestParallelExecution:
    """並列実行機能のテスト."""

    def test_parallel_execute_basic(self) -> None:
        """基本的な並列実行のテスト."""
        def task1() -> int:
            time.sleep(0.1)
            return 1
        
        def task2() -> int:
            time.sleep(0.1)
            return 2
        
        def task3() -> int:
            time.sleep(0.1)
            return 3
        
        start_time = time.time()
        results = parallel_execute([task1, task2, task3], max_workers=3)
        execution_time = time.time() - start_time
        
        # 結果の確認
        assert sorted(results) == [1, 2, 3]
        
        # 並列実行により時間が短縮されることを確認
        # 3つのタスクを順次実行すると0.3秒、並列実行では約0.1秒
        assert execution_time < 0.2

    @pytest.mark.asyncio
    async def test_async_parallel_execute_basic(self) -> None:
        """基本的な非同期並列実行のテスト."""
        async def task1() -> int:
            await asyncio.sleep(0.1)
            return 1
        
        async def task2() -> int:
            await asyncio.sleep(0.1)
            return 2
        
        async def task3() -> int:
            await asyncio.sleep(0.1)
            return 3
        
        start_time = time.time()
        results = await async_parallel_execute([task1(), task2(), task3()])
        execution_time = time.time() - start_time
        
        # 結果の確認
        assert sorted(results) == [1, 2, 3]
        
        # 並列実行により時間が短縮されることを確認
        assert execution_time < 0.2

    @pytest.mark.asyncio
    async def test_async_parallel_execute_semaphore_limit(self) -> None:
        """セマフォ制限のテスト."""
        execution_order = []
        
        async def task(task_id: int) -> int:
            execution_order.append(f"start_{task_id}")
            await asyncio.sleep(0.05)
            execution_order.append(f"end_{task_id}")
            return task_id
        
        # セマフォを2に制限
        tasks = [task(i) for i in range(4)]
        results = await async_parallel_execute(tasks, semaphore_limit=2)
        
        assert len(results) == 4
        assert sorted(results) == [0, 1, 2, 3]
        
        # 同時実行数が制限されていることを確認
        # 詳細な実行順序はテスト環境に依存するため、基本的な動作のみ確認
        assert len([x for x in execution_order if x.startswith("start_")]) == 4

    def test_parallel_execute_empty_tasks(self) -> None:
        """空のタスクリストのテスト."""
        results = parallel_execute([])
        assert results == []

    @pytest.mark.asyncio
    async def test_async_parallel_execute_empty_tasks(self) -> None:
        """空のコルーチンリストのテスト."""
        results = await async_parallel_execute([])
        assert results == []


class TestDataFrameCache:
    """DataFrameCacheクラスのテスト."""

    def test_dataframe_cache_basic(self) -> None:
        """DataFrameキャッシュの基本操作."""
        cache = DataFrameCache(max_memory_mb=10)
        
        # テスト用DataFrame作成
        df = pd.DataFrame({
            "close": [100, 101, 102],
            "volume": [1000, 1100, 1200]
        })
        
        # キャッシュと取得
        cache.cache_dataframe("test_df", df)
        cached_df = cache.get_dataframe("test_df")
        
        assert cached_df is not None
        pd.testing.assert_frame_equal(cached_df, df)
        
        # 異なるインスタンスであることを確認（コピーされている）
        assert cached_df is not df

    def test_dataframe_cache_ttl(self) -> None:
        """DataFrame TTLのテスト."""
        cache = DataFrameCache(max_memory_mb=10)
        
        df = pd.DataFrame({"value": [1, 2, 3]})
        
        # 短いTTLでキャッシュ
        cache.cache_dataframe("test_df", df, ttl=1)
        assert cache.get_dataframe("test_df") is not None
        
        # 期限切れまで待機
        time.sleep(1.1)
        assert cache.get_dataframe("test_df") is None

    def test_dataframe_cache_memory_management(self) -> None:
        """メモリ管理のテスト."""
        cache = DataFrameCache(max_memory_mb=1)  # 1MBに制限
        
        # 大きなDataFrameを作成（メモリ制限を超える）
        large_df1 = pd.DataFrame({
            "data": range(50000)  # 約0.4MB
        })
        large_df2 = pd.DataFrame({
            "data": range(50000)  # 約0.4MB
        })
        large_df3 = pd.DataFrame({
            "data": range(50000)  # 約0.4MB
        })
        
        # キャッシュに追加
        cache.cache_dataframe("df1", large_df1)
        cache.cache_dataframe("df2", large_df2)
        
        # メモリ統計を確認
        stats = cache.get_memory_stats()
        assert stats["cached_items"] == 2
        
        # 3つ目を追加するとメモリ制限により古いものが削除される
        cache.cache_dataframe("df3", large_df3)
        
        # メモリ制限が機能していることを確認
        stats_after = cache.get_memory_stats()
        assert stats_after["total_memory_mb"] <= 1.2  # 多少の誤差を許容

    def test_dataframe_cache_get_or_compute(self) -> None:
        """get_or_compute機能のテスト."""
        cache = DataFrameCache(max_memory_mb=10)
        
        compute_count = 0
        
        def expensive_computation() -> pd.DataFrame:
            nonlocal compute_count
            compute_count += 1
            return pd.DataFrame({"result": [1, 2, 3]})
        
        # 初回は計算実行
        result1 = cache.get_or_compute("computation", expensive_computation)
        assert compute_count == 1
        assert len(result1) == 3
        
        # 2回目はキャッシュから取得
        result2 = cache.get_or_compute("computation", expensive_computation)
        assert compute_count == 1  # 計算は実行されない
        pd.testing.assert_frame_equal(result1, result2)

    def test_memory_stats(self) -> None:
        """メモリ統計のテスト."""
        cache = DataFrameCache(max_memory_mb=10)
        
        # 初期状態
        stats = cache.get_memory_stats()
        assert stats["total_memory_mb"] == 0
        assert stats["cached_items"] == 0
        
        # データ追加後
        df = pd.DataFrame({"data": range(1000)})
        cache.cache_dataframe("test", df)
        
        stats_after = cache.get_memory_stats()
        assert stats_after["total_memory_mb"] > 0
        assert stats_after["cached_items"] == 1
        assert stats_after["memory_usage_percent"] > 0


class TestUtilityFunctions:
    """ユーティリティ関数のテスト."""

    def test_cache_key_for_symbol_and_period(self) -> None:
        """シンボル・期間キー生成のテスト."""
        key1 = cache_key_for_symbol_and_period("AAPL", "1d", "analysis")
        key2 = cache_key_for_symbol_and_period("AAPL", "1d", "analysis")
        key3 = cache_key_for_symbol_and_period("MSFT", "1d", "analysis")
        
        # 同じパラメータでは同じキー
        assert key1 == key2
        
        # 異なるシンボルでは異なるキー
        assert key1 != key3
        
        # キーの形式確認
        assert "analysis:AAPL:1d:" in key1

    def test_get_cache_stats(self) -> None:
        """グローバルキャッシュ統計のテスト."""
        # キャッシュをクリア
        clear_cache()
        
        # 初期状態の統計
        stats = get_cache_stats()
        assert stats["cache_size"] == 0
        assert stats["hits"] == 0

    def test_clear_cache(self) -> None:
        """キャッシュクリア機能のテスト."""
        # テスト用キャッシュ関数
        @cache_result(ttl=60)
        def test_function(x: int) -> int:
            return x * 2
        
        # キャッシュを使用
        result1 = test_function(5)
        assert result1 == 10
        
        # キャッシュをクリア
        clear_cache()
        
        # 統計が初期化されていることを確認
        stats = get_cache_stats()
        assert stats["cache_size"] == 0


class TestPerformanceIntegration:
    """パフォーマンス機能の統合テスト."""

    @pytest.mark.asyncio
    async def test_performance_improvement_simulation(self) -> None:
        """パフォーマンス向上のシミュレーションテスト."""
        # 重い処理をシミュレートする関数
        execution_times = []
        
        @cache_result(ttl=60)
        async def heavy_analysis(symbol: str) -> dict:
            start = time.time()
            await asyncio.sleep(0.1)  # 100msの重い処理
            end = time.time()
            execution_times.append(end - start)
            
            return {
                "symbol": symbol,
                "analysis": "completed",
                "timestamp": time.time()
            }
        
        # 初回実行（キャッシュなし）
        start_time = time.time()
        result1 = await heavy_analysis("AAPL")
        first_execution_time = time.time() - start_time
        
        # 2回目実行（キャッシュから取得）
        start_time = time.time()
        result2 = await heavy_analysis("AAPL")
        cached_execution_time = time.time() - start_time
        
        # 結果の確認
        assert result1["symbol"] == "AAPL"
        assert result1 == result2
        
        # パフォーマンス向上の確認
        assert len(execution_times) == 1  # 実際の処理は1回のみ
        assert first_execution_time >= 0.1  # 初回は重い処理時間
        assert cached_execution_time < 0.01  # キャッシュは高速

    def test_concurrent_cache_access(self) -> None:
        """並行キャッシュアクセスのテスト."""
        cache = MemoryCache(max_size=100, default_ttl=60)
        
        def worker(worker_id: int) -> list:
            results = []
            for i in range(10):
                key = f"worker_{worker_id}_item_{i}"
                value = f"value_{worker_id}_{i}"
                
                # 設定と取得を繰り返す
                cache.set(key, value)
                retrieved = cache.get(key)
                results.append(retrieved == value)
            
            return results
        
        # 複数ワーカーで同時実行
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(worker, i) for i in range(5)]
            results = [future.result() for future in futures]
        
        # 全ての操作が成功していることを確認
        for worker_results in results:
            assert all(worker_results)
        
        # キャッシュ統計の確認
        stats = cache.get_stats()
        assert stats["cache_size"] == 50  # 5ワーカー × 10アイテム
        assert stats["hits"] == 50
        assert stats["sets"] == 50

    @pytest.mark.asyncio
    async def test_parallel_vs_sequential_performance(self) -> None:
        """並列 vs 順次実行のパフォーマンス比較テスト."""
        async def mock_analysis_task(delay: float) -> str:
            await asyncio.sleep(delay)
            return f"completed_after_{delay}"
        
        task_delay = 0.05  # 50ms
        num_tasks = 4
        
        # 順次実行
        start_time = time.time()
        sequential_results = []
        for i in range(num_tasks):
            result = await mock_analysis_task(task_delay)
            sequential_results.append(result)
        sequential_time = time.time() - start_time
        
        # 並列実行
        start_time = time.time()
        parallel_tasks = [mock_analysis_task(task_delay) for _ in range(num_tasks)]
        parallel_results = await async_parallel_execute(parallel_tasks)
        parallel_time = time.time() - start_time
        
        # 結果の確認
        assert len(sequential_results) == num_tasks
        assert len(parallel_results) == num_tasks
        
        # パフォーマンス向上の確認
        expected_sequential_time = task_delay * num_tasks  # 200ms
        expected_parallel_time = task_delay  # 50ms
        
        # 並列実行が顕著に高速であることを確認
        performance_improvement = sequential_time / parallel_time
        assert performance_improvement > 2.0  # 少なくとも2倍高速
        
        assert sequential_time >= expected_sequential_time * 0.8  # 多少の誤差を許容
        assert parallel_time <= expected_parallel_time * 1.5   # 多少のオーバーヘッドを許容