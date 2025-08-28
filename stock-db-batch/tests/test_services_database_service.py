"""データベースサービス（CRUD）のテストコード

企業データのCRUD操作、効率的な差分処理、バッチ更新機能をテストします。
"""

import tempfile
from pathlib import Path

from stock_batch.database.connection import DatabaseConnection
from stock_batch.models.company import Company
from stock_batch.services.database_service import DatabaseService


class TestDatabaseService:
    """DatabaseService クラスのテスト"""

    def test_create_database_service(self) -> None:
        """DatabaseService 作成のテスト"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
            db_path = tmp_file.name

        try:
            conn = DatabaseConnection(db_path)
            service = DatabaseService(conn)
            assert service is not None
        finally:
            Path(db_path).unlink(missing_ok=True)

    def test_setup_database_with_migration(self) -> None:
        """データベース初期化とマイグレーションのテスト"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
            db_path = tmp_file.name

        try:
            conn = DatabaseConnection(db_path)
            service = DatabaseService(conn)

            with conn:
                service.setup_database()

                # テーブルが作成されていることを確認
                cursor = conn.execute_query(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
                tables = [row[0] for row in cursor.fetchall()]
                assert "company" in tables
                assert "schema_version" in tables

        finally:
            Path(db_path).unlink(missing_ok=True)

    def test_insert_company_success(self) -> None:
        """企業データ挿入成功のテスト"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
            db_path = tmp_file.name

        try:
            conn = DatabaseConnection(db_path)
            service = DatabaseService(conn)

            with conn:
                service.setup_database()

                company = Company(
                    symbol="1332.T",
                    name="ニッスイ",
                    market="東P",
                    business_summary="日水株式会社は日本の水産会社です。",
                    price=877.8,
                )

                result = service.insert_company(company)
                assert result is True

                # データベースに挿入されたことを確認
                cursor = conn.execute_query(
                    "SELECT symbol, name, price FROM company WHERE symbol = ?",
                    ("1332.T",),
                )
                row = cursor.fetchone()
                assert row is not None
                assert row[0] == "1332.T"
                assert row[1] == "ニッスイ"
                assert row[2] == 877.8

        finally:
            Path(db_path).unlink(missing_ok=True)

    def test_insert_company_duplicate_symbol(self) -> None:
        """重複シンボル挿入エラーのテスト"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
            db_path = tmp_file.name

        try:
            conn = DatabaseConnection(db_path)
            service = DatabaseService(conn)

            with conn:
                service.setup_database()

                company = Company(
                    symbol="1332.T",
                    name="ニッスイ",
                    market="東P",
                    business_summary="日水株式会社",
                    price=877.8,
                )

                # 1回目は成功
                result1 = service.insert_company(company)
                assert result1 is True

                # 2回目は失敗（重複エラー）
                result2 = service.insert_company(company)
                assert result2 is False

        finally:
            Path(db_path).unlink(missing_ok=True)

    def test_get_company_by_symbol_found(self) -> None:
        """シンボルによる企業データ取得成功のテスト"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
            db_path = tmp_file.name

        try:
            conn = DatabaseConnection(db_path)
            service = DatabaseService(conn)

            with conn:
                service.setup_database()

                # テストデータ挿入
                company = Company(
                    symbol="1332.T",
                    name="ニッスイ",
                    market="東P",
                    business_summary="日水株式会社",
                    price=877.8,
                )
                service.insert_company(company)

                # データ取得
                result = service.get_company_by_symbol("1332.T")
                assert result is not None
                assert result.symbol == "1332.T"
                assert result.name == "ニッスイ"
                assert result.price == 877.8

        finally:
            Path(db_path).unlink(missing_ok=True)

    def test_get_company_by_symbol_not_found(self) -> None:
        """存在しないシンボルの企業データ取得テスト"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
            db_path = tmp_file.name

        try:
            conn = DatabaseConnection(db_path)
            service = DatabaseService(conn)

            with conn:
                service.setup_database()

                result = service.get_company_by_symbol("NONEXISTENT.T")
                assert result is None

        finally:
            Path(db_path).unlink(missing_ok=True)

    def test_update_company_success(self) -> None:
        """企業データ更新成功のテスト"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
            db_path = tmp_file.name

        try:
            conn = DatabaseConnection(db_path)
            service = DatabaseService(conn)

            with conn:
                service.setup_database()

                # 初期データ挿入
                original_company = Company(
                    symbol="1332.T",
                    name="ニッスイ",
                    market="東P",
                    business_summary="日水株式会社",
                    price=877.8,
                )
                service.insert_company(original_company)

                # データ更新
                updated_company = Company(
                    symbol="1332.T",
                    name="ニッスイ",
                    market="東P",
                    business_summary="日水株式会社は水産業界のリーダーです。",
                    price=890.5,
                )

                result = service.update_company(updated_company)
                assert result is True

                # 更新されたデータを確認
                retrieved = service.get_company_by_symbol("1332.T")
                assert retrieved is not None
                assert retrieved.price == 890.5
                assert "リーダー" in retrieved.business_summary

        finally:
            Path(db_path).unlink(missing_ok=True)

    def test_update_company_not_found(self) -> None:
        """存在しない企業データ更新テスト"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
            db_path = tmp_file.name

        try:
            conn = DatabaseConnection(db_path)
            service = DatabaseService(conn)

            with conn:
                service.setup_database()

                nonexistent_company = Company(
                    symbol="NONEXISTENT.T",
                    name="存在しない会社",
                    market="東P",
                    business_summary="存在しない",
                    price=100.0,
                )

                result = service.update_company(nonexistent_company)
                assert result is False

        finally:
            Path(db_path).unlink(missing_ok=True)

    def test_delete_company_success(self) -> None:
        """企業データ削除成功のテスト"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
            db_path = tmp_file.name

        try:
            conn = DatabaseConnection(db_path)
            service = DatabaseService(conn)

            with conn:
                service.setup_database()

                # テストデータ挿入
                company = Company(
                    symbol="1332.T",
                    name="ニッスイ",
                    market="東P",
                    business_summary="日水株式会社",
                    price=877.8,
                )
                service.insert_company(company)

                # 削除実行
                result = service.delete_company("1332.T")
                assert result is True

                # 削除されたことを確認
                retrieved = service.get_company_by_symbol("1332.T")
                assert retrieved is None

        finally:
            Path(db_path).unlink(missing_ok=True)

    def test_delete_company_not_found(self) -> None:
        """存在しない企業データ削除テスト"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
            db_path = tmp_file.name

        try:
            conn = DatabaseConnection(db_path)
            service = DatabaseService(conn)

            with conn:
                service.setup_database()

                result = service.delete_company("NONEXISTENT.T")
                assert result is False

        finally:
            Path(db_path).unlink(missing_ok=True)

    def test_get_all_companies(self) -> None:
        """全企業データ取得のテスト"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
            db_path = tmp_file.name

        try:
            conn = DatabaseConnection(db_path)
            service = DatabaseService(conn)

            with conn:
                service.setup_database()

                # 複数のテストデータ挿入
                companies = [
                    Company(
                        symbol="1332.T",
                        name="ニッスイ",
                        market="東P",
                        business_summary="日水株式会社",
                        price=877.8,
                    ),
                    Company(
                        symbol="1418.T",
                        name="インターライフ",
                        market="東S",
                        business_summary="インターライフ株式会社",
                        price=405.0,
                    ),
                ]

                for company in companies:
                    service.insert_company(company)

                # 全データ取得
                all_companies = service.get_all_companies()
                assert len(all_companies) == 2

                symbols = [comp.symbol for comp in all_companies]
                assert "1332.T" in symbols
                assert "1418.T" in symbols

        finally:
            Path(db_path).unlink(missing_ok=True)

    def test_get_companies_by_market(self) -> None:
        """市場別企業データ取得のテスト"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
            db_path = tmp_file.name

        try:
            conn = DatabaseConnection(db_path)
            service = DatabaseService(conn)

            with conn:
                service.setup_database()

                # 異なる市場のテストデータ挿入
                companies = [
                    Company(
                        symbol="1332.T",
                        name="ニッスイ",
                        market="東P",
                        business_summary="日水株式会社",
                        price=877.8,
                    ),
                    Company(
                        symbol="1418.T",
                        name="インターライフ",
                        market="東S",
                        business_summary="インターライフ株式会社",
                        price=405.0,
                    ),
                    Company(
                        symbol="130A.T",
                        name="ベリタス",
                        market="東G",
                        business_summary="ベリタス株式会社",
                        price=646.0,
                    ),
                ]

                for company in companies:
                    service.insert_company(company)

                # 東P市場の企業取得
                tokyop_companies = service.get_companies_by_market("東P")
                assert len(tokyop_companies) == 1
                assert tokyop_companies[0].symbol == "1332.T"

                # 東S市場の企業取得
                tokyos_companies = service.get_companies_by_market("東S")
                assert len(tokyos_companies) == 1
                assert tokyos_companies[0].symbol == "1418.T"

        finally:
            Path(db_path).unlink(missing_ok=True)

    def test_batch_insert_companies(self) -> None:
        """企業データバッチ挿入のテスト"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
            db_path = tmp_file.name

        try:
            conn = DatabaseConnection(db_path)
            service = DatabaseService(conn)

            with conn:
                service.setup_database()

                companies = [
                    Company(
                        symbol="1332.T",
                        name="ニッスイ",
                        market="東P",
                        business_summary="日水株式会社",
                        price=877.8,
                    ),
                    Company(
                        symbol="1418.T",
                        name="インターライフ",
                        market="東S",
                        business_summary="インターライフ株式会社",
                        price=405.0,
                    ),
                    Company(
                        symbol="130A.T",
                        name="ベリタス",
                        market="東G",
                        business_summary="ベリタス株式会社",
                        price=646.0,
                    ),
                ]

                result = service.batch_insert_companies(companies)
                assert result["successful"] == 3
                assert result["failed"] == 0
                assert len(result["failed_symbols"]) == 0

                # 全データが挿入されたことを確認
                all_companies = service.get_all_companies()
                assert len(all_companies) == 3

        finally:
            Path(db_path).unlink(missing_ok=True)

    def test_batch_insert_companies_with_duplicates(self) -> None:
        """重複を含むバッチ挿入のテスト"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
            db_path = tmp_file.name

        try:
            conn = DatabaseConnection(db_path)
            service = DatabaseService(conn)

            with conn:
                service.setup_database()

                # 事前に1件挿入
                existing_company = Company(
                    symbol="1332.T",
                    name="ニッスイ",
                    market="東P",
                    business_summary="既存企業",
                    price=800.0,
                )
                service.insert_company(existing_company)

                # 重複を含むバッチ挿入
                companies = [
                    Company(
                        symbol="1332.T",  # 重複
                        name="ニッスイ",
                        market="東P",
                        business_summary="日水株式会社",
                        price=877.8,
                    ),
                    Company(
                        symbol="1418.T",  # 新規
                        name="インターライフ",
                        market="東S",
                        business_summary="インターライフ株式会社",
                        price=405.0,
                    ),
                ]

                result = service.batch_insert_companies(companies)
                assert result["successful"] == 1  # 1418.T のみ成功
                assert result["failed"] == 1  # 1332.T は重複で失敗
                assert "1332.T" in result["failed_symbols"]

        finally:
            Path(db_path).unlink(missing_ok=True)

    def test_batch_update_companies(self) -> None:
        """企業データバッチ更新のテスト"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
            db_path = tmp_file.name

        try:
            conn = DatabaseConnection(db_path)
            service = DatabaseService(conn)

            with conn:
                service.setup_database()

                # 初期データ挿入
                initial_companies = [
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
                        business_summary="古い情報",
                        price=400.0,
                    ),
                ]

                for company in initial_companies:
                    service.insert_company(company)

                # バッチ更新
                updated_companies = [
                    Company(
                        symbol="1332.T",
                        name="ニッスイ",
                        market="東P",
                        business_summary="新しい情報",
                        price=877.8,
                    ),
                    Company(
                        symbol="1418.T",
                        name="インターライフ",
                        market="東S",
                        business_summary="新しい情報",
                        price=405.0,
                    ),
                ]

                result = service.batch_update_companies(updated_companies)
                assert result["successful"] == 2
                assert result["failed"] == 0

                # 更新されたことを確認
                updated = service.get_company_by_symbol("1332.T")
                assert updated.business_summary == "新しい情報"
                assert updated.price == 877.8

        finally:
            Path(db_path).unlink(missing_ok=True)

    def test_upsert_companies(self) -> None:
        """企業データupsert（挿入または更新）のテスト"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
            db_path = tmp_file.name

        try:
            conn = DatabaseConnection(db_path)
            service = DatabaseService(conn)

            with conn:
                service.setup_database()

                # 事前に1件挿入
                existing_company = Company(
                    symbol="1332.T",
                    name="ニッスイ",
                    market="東P",
                    business_summary="既存情報",
                    price=800.0,
                )
                service.insert_company(existing_company)

                # upsertデータ（既存1件 + 新規1件）
                upsert_companies = [
                    Company(
                        symbol="1332.T",  # 既存 → 更新
                        name="ニッスイ",
                        market="東P",
                        business_summary="更新された情報",
                        price=877.8,
                    ),
                    Company(
                        symbol="1418.T",  # 新規 → 挿入
                        name="インターライフ",
                        market="東S",
                        business_summary="新規企業",
                        price=405.0,
                    ),
                ]

                result = service.upsert_companies(upsert_companies)
                assert result["inserted"] == 1  # 1418.T 挿入
                assert result["updated"] == 1  # 1332.T 更新
                assert result["failed"] == 0

                # データを確認
                updated = service.get_company_by_symbol("1332.T")
                assert updated.business_summary == "更新された情報"

                new_company = service.get_company_by_symbol("1418.T")
                assert new_company is not None
                assert new_company.business_summary == "新規企業"

        finally:
            Path(db_path).unlink(missing_ok=True)

    def test_get_database_stats(self) -> None:
        """データベース統計情報取得のテスト"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
            db_path = tmp_file.name

        try:
            conn = DatabaseConnection(db_path)
            service = DatabaseService(conn)

            with conn:
                service.setup_database()

                # テストデータ挿入
                companies = [
                    Company(
                        symbol="1332.T",
                        name="ニッスイ",
                        market="東P",
                        business_summary="日水株式会社",
                        price=877.8,
                    ),
                    Company(
                        symbol="1418.T",
                        name="インターライフ",
                        market="東S",
                        business_summary="インターライフ株式会社",
                        price=405.0,
                    ),
                ]

                for company in companies:
                    service.insert_company(company)

                stats = service.get_database_stats()

                assert stats["total_companies"] == 2
                assert "東P" in stats["markets"]
                assert "東S" in stats["markets"]
                assert stats["markets"]["東P"] == 1
                assert stats["markets"]["東S"] == 1

        finally:
            Path(db_path).unlink(missing_ok=True)

    def test_find_companies_needing_update(self) -> None:
        """更新が必要な企業の検出テスト"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
            db_path = tmp_file.name

        try:
            conn = DatabaseConnection(db_path)
            service = DatabaseService(conn)

            with conn:
                service.setup_database()

                # 既存データ
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
                        business_summary="古い情報",
                        price=400.0,
                    ),
                ]

                for company in existing_companies:
                    service.insert_company(company)

                # CSVからの新データ
                csv_companies = [
                    Company(
                        symbol="1332.T",
                        name="ニッスイ",
                        market="東P",
                        business_summary="古い情報",  # 変更なし
                        price=877.8,  # 価格のみ変更
                    ),
                    Company(
                        symbol="1418.T",
                        name="インターライフ",
                        market="東S",
                        business_summary="古い情報",  # 変更なし
                        price=400.0,  # 価格も変更なし
                    ),
                    Company(
                        symbol="130A.T",  # 新規企業
                        name="ベリタス",
                        market="東G",
                        business_summary="新規企業",
                        price=646.0,
                    ),
                ]

                diff_result = service.find_companies_needing_update(csv_companies)

                assert len(diff_result["to_insert"]) == 1  # 130A.T
                assert len(diff_result["to_update"]) == 1  # 1332.T（価格変更）
                assert len(diff_result["no_change"]) == 1  # 1418.T

                assert diff_result["to_insert"][0].symbol == "130A.T"
                assert diff_result["to_update"][0].symbol == "1332.T"
                assert diff_result["no_change"][0].symbol == "1418.T"

        finally:
            Path(db_path).unlink(missing_ok=True)
