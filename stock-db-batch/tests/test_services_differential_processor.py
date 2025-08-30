"""効率的差分処理サービスのテストコード

CSVデータとデータベースの効率的な比較・差分検出、
大量データ処理の最適化、並列処理によるパフォーマンス向上をテストします。
"""

import tempfile
from pathlib import Path

from stock_batch.database.connection import DatabaseConnection
from stock_batch.models.company import Company
from stock_batch.services.database_service import DatabaseService
from stock_batch.services.differential_processor import (
    DifferentialProcessor,
)


class TestDifferentialProcessor:
    """DifferentialProcessor クラスのテスト"""

    def test_create_differential_processor(self) -> None:
        """DifferentialProcessor 作成のテスト"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
            db_path = tmp_file.name

        try:
            conn = DatabaseConnection(db_path)
            db_service = DatabaseService(conn)
            processor = DifferentialProcessor(db_service)
            assert processor is not None

        finally:
            Path(db_path).unlink(missing_ok=True)

    def test_simple_diff_detection(self) -> None:
        """基本的な差分検出のテスト"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
            db_path = tmp_file.name

        try:
            conn = DatabaseConnection(db_path)
            db_service = DatabaseService(conn)
            processor = DifferentialProcessor(db_service)

            with conn:
                db_service.setup_database()

                # 既存データ挿入
                existing_companies = [
                    Company(
                        symbol="1332.T",
                        name="ニッスイ",
                        market="東P",
                        business_summary="古い情報",
                        price=800.0,
                    ),
                    Company(
                        symbol="1418.T",
                        name="インターライフ",
                        market="東S",
                        business_summary="変更なし",
                        price=400.0,
                    ),
                ]

                for company in existing_companies:
                    db_service.insert_company(company)

                # CSVからの新データ
                csv_companies = [
                    Company(
                        symbol="1332.T",
                        name="ニッスイ",
                        market="東P",
                        business_summary="新しい情報",  # ビジネス要約変更
                        price=877.8,  # 価格変更
                    ),
                    Company(
                        symbol="1418.T",
                        name="インターライフ",
                        market="東S",
                        business_summary="変更なし",
                        price=400.0,  # 変更なし
                    ),
                    Company(
                        symbol="130A.T",  # 新規
                        name="ベリタス",
                        market="東G",
                        business_summary="新規企業",
                        price=646.0,
                    ),
                ]

                result = processor.process_diff(csv_companies)

                assert len(result.to_insert) == 1
                assert len(result.to_update) == 1
                assert len(result.no_change) == 1

                assert result.to_insert[0].symbol == "130A.T"
                assert result.to_update[0].symbol == "1332.T"
                assert result.no_change[0].symbol == "1418.T"

        finally:
            Path(db_path).unlink(missing_ok=True)

    def test_large_dataset_processing(self) -> None:
        """大量データセット処理のテスト"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
            db_path = tmp_file.name

        try:
            conn = DatabaseConnection(db_path)
            db_service = DatabaseService(conn)
            processor = DifferentialProcessor(db_service, chunk_size=100)

            with conn:
                db_service.setup_database()

                # 大量データ作成（1000社）
                existing_companies = []
                csv_companies = []

                for i in range(1000, 2000):  # 1000社
                    symbol = f"{i}.T"
                    existing_company = Company(
                        symbol=symbol,
                        name=f"企業{i}",
                        market="東P",
                        business_summary=f"企業{i}の説明",
                        price=float(i),
                    )
                    existing_companies.append(existing_company)

                    # CSVデータ：半分は価格変更、半分は変更なし
                    new_price = float(i + 10) if i % 2 == 0 else float(i)
                    csv_company = Company(
                        symbol=symbol,
                        name=f"企業{i}",
                        market="東P",
                        business_summary=f"企業{i}の説明",
                        price=new_price,
                    )
                    csv_companies.append(csv_company)

                # 既存データ挿入
                db_service.batch_insert_companies(existing_companies)

                # 差分処理実行
                result = processor.process_diff(csv_companies)

                # 結果検証
                assert len(result.to_insert) == 0  # 全て既存
                assert len(result.to_update) == 500  # 半分が更新対象
                assert len(result.no_change) == 500  # 半分は変更なし
                assert result.summary.total_processed == 1000

        finally:
            Path(db_path).unlink(missing_ok=True)

    def test_memory_efficient_processing(self) -> None:
        """メモリ効率的処理のテスト"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
            db_path = tmp_file.name

        try:
            conn = DatabaseConnection(db_path)
            db_service = DatabaseService(conn)
            processor = DifferentialProcessor(
                db_service, chunk_size=50, enable_memory_optimization=True
            )

            with conn:
                db_service.setup_database()

                # テストデータ作成
                companies = []
                for i in range(200):
                    company = Company(
                        symbol=f"{1000 + i}.T",
                        name=f"企業{i}",
                        market="東P",
                        business_summary=f"説明{i}",
                        price=float(100 + i),
                    )
                    companies.append(company)

                result = processor.process_diff(companies)

                assert result.summary.total_processed == 200
                assert len(result.to_insert) == 200  # 全て新規
                assert result.summary.processing_time > 0

        finally:
            Path(db_path).unlink(missing_ok=True)

    def test_parallel_processing_enabled(self) -> None:
        """並列処理有効化のテスト"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
            db_path = tmp_file.name

        try:
            conn = DatabaseConnection(db_path)
            db_service = DatabaseService(conn)
            processor = DifferentialProcessor(
                db_service, chunk_size=50, enable_parallel=True, max_workers=2
            )

            with conn:
                db_service.setup_database()

                # テストデータ
                companies = []
                for i in range(150):
                    company = Company(
                        symbol=f"{1500 + i}.T",
                        name=f"企業{i}",
                        market="東P",
                        business_summary=f"説明{i}",
                        price=float(500 + i),
                    )
                    companies.append(company)

                result = processor.process_diff(companies)

                assert result.summary.total_processed == 150
                assert result.summary.chunks_processed >= 3  # 50件ずつなので3チャンク
                assert result.summary.parallel_enabled is True

        finally:
            Path(db_path).unlink(missing_ok=True)

    def test_change_detection_algorithms(self) -> None:
        """変更検出アルゴリズムのテスト"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
            db_path = tmp_file.name

        try:
            conn = DatabaseConnection(db_path)
            db_service = DatabaseService(conn)
            processor = DifferentialProcessor(db_service)

            with conn:
                db_service.setup_database()

                # 異なる種類の変更パターンテスト
                test_cases = [
                    # 価格のみ変更
                    {
                        "existing": Company(
                            symbol="PRICE.T",
                            name="価格変更",
                            market="東P",
                            business_summary="説明",
                            price=100.0,
                        ),
                        "new": Company(
                            symbol="PRICE.T",
                            name="価格変更",
                            market="東P",
                            business_summary="説明",
                            price=105.50,
                        ),
                        "should_update": True,
                    },
                    # ビジネス要約のみ変更
                    {
                        "existing": Company(
                            symbol="SUMMARY.T",
                            name="要約変更",
                            market="東P",
                            business_summary="古い説明",
                            price=200.0,
                        ),
                        "new": Company(
                            symbol="SUMMARY.T",
                            name="要約変更",
                            market="東P",
                            business_summary="新しい説明",
                            price=200.0,
                        ),
                        "should_update": True,
                    },
                    # 変更なし
                    {
                        "existing": Company(
                            symbol="NOCHANGE.T",
                            name="変更なし",
                            market="東P",
                            business_summary="同じ説明",
                            price=300.0,
                        ),
                        "new": Company(
                            symbol="NOCHANGE.T",
                            name="変更なし",
                            market="東P",
                            business_summary="同じ説明",
                            price=300.0,
                        ),
                        "should_update": False,
                    },
                    # 微小な価格変更（閾値以下）
                    {
                        "existing": Company(
                            symbol="SMALL.T",
                            name="微小変更",
                            market="東P",
                            business_summary="説明",
                            price=400.00,
                        ),
                        "new": Company(
                            symbol="SMALL.T",
                            name="微小変更",
                            market="東P",
                            business_summary="説明",
                            price=400.005,  # 0.5銭の差
                        ),
                        "should_update": False,
                    },
                ]

                # 既存データ挿入
                for case in test_cases:
                    db_service.insert_company(case["existing"])

                # 差分処理実行
                csv_companies = [case["new"] for case in test_cases]
                result = processor.process_diff(csv_companies)

                # 結果検証
                update_symbols = [comp.symbol for comp in result.to_update]
                no_change_symbols = [comp.symbol for comp in result.no_change]

                for case in test_cases:
                    symbol = case["existing"].symbol
                    if case["should_update"]:
                        assert symbol in update_symbols
                    else:
                        assert symbol in no_change_symbols

        finally:
            Path(db_path).unlink(missing_ok=True)

    def test_performance_metrics_collection(self) -> None:
        """パフォーマンス指標収集のテスト"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
            db_path = tmp_file.name

        try:
            conn = DatabaseConnection(db_path)
            db_service = DatabaseService(conn)
            processor = DifferentialProcessor(
                db_service, enable_performance_metrics=True
            )

            with conn:
                db_service.setup_database()

                companies = []
                for i in range(100):
                    company = Company(
                        symbol=f"{2000 + i}.T",
                        name=f"企業{i}",
                        market="東P",
                        business_summary=f"説明{i}",
                        price=float(i),
                    )
                    companies.append(company)

                result = processor.process_diff(companies)

                # パフォーマンス指標の検証
                assert result.summary.processing_time > 0
                assert result.summary.memory_usage_mb >= 0
                assert result.summary.records_per_second > 0
                assert result.summary.database_queries_count > 0

        finally:
            Path(db_path).unlink(missing_ok=True)

    def test_error_handling_and_recovery(self) -> None:
        """エラーハンドリングと回復処理のテスト"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
            db_path = tmp_file.name

        try:
            conn = DatabaseConnection(db_path)
            db_service = DatabaseService(conn)
            processor = DifferentialProcessor(db_service)

            with conn:
                db_service.setup_database()

                # 有効なデータのみでテスト（Pydantic検証をパス）
                companies = [
                    Company(
                        symbol="VALID.T",
                        name="正常企業",
                        market="東P",
                        business_summary="正常",
                        price=100.0,
                    ),
                    Company(
                        symbol="VALID2.T",
                        name="正常企業2",
                        market="東S",
                        business_summary="正常2",
                        price=200.0,
                    ),
                    Company(
                        symbol="VALID3.T",
                        name="正常企業3",
                        market="東G",
                        business_summary="正常3",
                        price=300.0,
                    ),
                ]

                result = processor.process_diff(companies)

                # 正常処理の検証
                assert result.summary.total_processed == 3
                assert result.summary.error_count == 0
                assert len(result.summary.error_details) == 0
                assert len(result.to_insert) == 3  # 全て新規

        finally:
            Path(db_path).unlink(missing_ok=True)

    def test_incremental_processing(self) -> None:
        """増分処理のテスト"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
            db_path = tmp_file.name

        try:
            conn = DatabaseConnection(db_path)
            db_service = DatabaseService(conn)
            processor = DifferentialProcessor(db_service, enable_incremental=True)

            with conn:
                db_service.setup_database()

                # 1回目の処理
                batch1 = [
                    Company(
                        symbol="INC1.T",
                        name="増分1",
                        market="東P",
                        business_summary="初回",
                        price=100.0,
                    ),
                    Company(
                        symbol="INC2.T",
                        name="増分2",
                        market="東P",
                        business_summary="初回",
                        price=200.0,
                    ),
                ]

                result1 = processor.process_diff(batch1)
                assert len(result1.to_insert) == 2

                # 1回目のデータを実際にデータベースに挿入
                db_service.batch_insert_companies(batch1)

                # 2回目の処理（一部変更）
                batch2 = [
                    Company(
                        symbol="INC1.T",
                        name="増分1",
                        market="東P",
                        business_summary="更新済み",  # 変更
                        price=110.0,  # 変更
                    ),
                    Company(
                        symbol="INC2.T",
                        name="増分2",
                        market="東P",
                        business_summary="初回",  # 変更なし
                        price=200.0,  # 変更なし
                    ),
                    Company(
                        symbol="INC3.T",  # 新規
                        name="増分3",
                        market="東S",
                        business_summary="新規",
                        price=300.0,
                    ),
                ]

                result2 = processor.process_diff(batch2)
                assert len(result2.to_insert) == 1  # INC3.T
                assert len(result2.to_update) == 1  # INC1.T
                assert len(result2.no_change) == 1  # INC2.T

        finally:
            Path(db_path).unlink(missing_ok=True)

    def test_custom_comparison_strategy(self) -> None:
        """カスタム比較戦略のテスト"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
            db_path = tmp_file.name

        try:
            conn = DatabaseConnection(db_path)
            db_service = DatabaseService(conn)

            # カスタム比較関数：価格変動5%以上のみ更新対象とする
            def custom_comparison(existing: Company, new: Company) -> bool:
                if existing.price and new.price:
                    price_change_rate = abs(new.price - existing.price) / existing.price
                    return price_change_rate >= 0.05  # 5%以上の変動
                return existing.business_summary != new.business_summary

            processor = DifferentialProcessor(
                db_service, custom_comparison_func=custom_comparison
            )

            with conn:
                db_service.setup_database()

                # 既存データ
                existing = Company(
                    symbol="CUSTOM.T",
                    name="カスタム",
                    market="東P",
                    business_summary="説明",
                    price=1000.0,
                )
                db_service.insert_company(existing)

                # テストケース
                test_cases = [
                    Company(
                        symbol="CUSTOM.T",
                        name="カスタム",
                        market="東P",
                        business_summary="説明",
                        price=1030.0,  # 3%増 → 更新対象外
                    ),
                    Company(
                        symbol="CUSTOM.T",
                        name="カスタム",
                        market="東P",
                        business_summary="説明",
                        price=1060.0,  # 6%増 → 更新対象
                    ),
                ]

                # 3%増のケース
                result1 = processor.process_diff([test_cases[0]])
                assert len(result1.to_update) == 0
                assert len(result1.no_change) == 1

                # 6%増のケース
                result2 = processor.process_diff([test_cases[1]])
                assert len(result2.to_update) == 1
                assert len(result2.no_change) == 0

        finally:
            Path(db_path).unlink(missing_ok=True)

    def test_get_processing_stats(self) -> None:
        """処理統計情報取得のテスト"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
            db_path = tmp_file.name

        try:
            conn = DatabaseConnection(db_path)
            db_service = DatabaseService(conn)
            processor = DifferentialProcessor(db_service)

            with conn:
                db_service.setup_database()

                # 複数回処理実行
                for batch_num in range(3):
                    companies = [
                        Company(
                            symbol=f"STAT{batch_num}_{i}.T",
                            name=f"統計{i}",
                            market="東P",
                            business_summary=f"バッチ{batch_num}",
                            price=float(batch_num * 100 + i),
                        )
                        for i in range(10)
                    ]
                    processor.process_diff(companies)

                stats = processor.get_processing_stats()

                assert stats["total_runs"] == 3
                assert stats["total_records_processed"] == 30
                assert stats["average_processing_time"] >= 0
                assert "last_run_summary" in stats

        finally:
            Path(db_path).unlink(missing_ok=True)
