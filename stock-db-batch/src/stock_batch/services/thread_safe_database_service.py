"""スレッドセーフなデータベースサービス（CRUD）

ThreadSafeDatabaseConnectionを使用してマルチスレッド環境で安全に動作する
企業データのCRUD操作、効率的な差分処理、バッチ更新機能を提供する
"""

from __future__ import annotations

import logging
import sqlite3
from typing import Any

from stock_batch.database.migration import DatabaseMigration
from stock_batch.database.thread_safe_connection import ThreadSafeDatabaseConnection
from stock_batch.models.company import Company

logger = logging.getLogger(__name__)


class ThreadSafeDatabaseService:
    """スレッドセーフなデータベースサービスクラス

    ThreadSafeDatabaseConnectionを使用して、マルチスレッド環境で安全な
    企業データのCRUD操作、バッチ処理、効率的な差分検出を提供する。

    Attributes:
        db_connection: スレッドセーフなデータベース接続管理オブジェクト

    Example:
        >>> conn = ThreadSafeDatabaseConnection("stocks.db")
        >>> service = ThreadSafeDatabaseService(conn)
        >>> service.setup_database()
        >>> 
        >>> # マルチスレッド環境での使用
        >>> def worker():
        ...     company = Company(symbol="1332.T", name="ニッスイ", ...)
        ...     service.insert_company(company)
        >>> 
        >>> with ThreadPoolExecutor(max_workers=4) as executor:
        ...     futures = [executor.submit(worker) for _ in range(4)]
        ...     results = [f.result() for f in futures]
    """

    def __init__(self, db_connection: ThreadSafeDatabaseConnection) -> None:
        """ThreadSafeDatabaseService を初期化する

        Args:
            db_connection: スレッドセーフなデータベース接続管理オブジェクト

        Example:
            >>> conn = ThreadSafeDatabaseConnection("/data/stocks.db")
            >>> service = ThreadSafeDatabaseService(conn)
        """
        self.db_connection = db_connection

    def setup_database(self) -> None:
        """データベースを初期化する

        マイグレーションを実行してテーブル作成や更新を行う。
        マルチスレッド環境で安全に実行可能。

        Example:
            >>> service = ThreadSafeDatabaseService(conn)
            >>> service.setup_database()
        """
        # 各スレッドで独立した接続を使用してマイグレーション実行
        connection = self.db_connection.get_connection()
        
        # マイグレーション用に一時的に従来のDatabaseConnection互換インターフェースを作成
        class CompatConnection:
            def __init__(self, sqlite_conn: sqlite3.Connection):
                self.connection = sqlite_conn
            
            def execute_query(self, query: str, parameters: tuple = ()) -> sqlite3.Cursor:
                cursor = self.connection.execute(query, parameters)
                self.connection.commit()
                return cursor
            
            def is_connected(self) -> bool:
                return self.connection is not None
        
        compat_conn = CompatConnection(connection)
        migration = DatabaseMigration(compat_conn)
        migration.run_migrations()
        logger.info("データベース初期化完了")

    def insert_company(self, company: Company) -> bool:
        """企業データを挿入する

        指定された企業データをデータベースに挿入する。
        シンボルの重複がある場合は失敗する。
        マルチスレッド環境で安全に実行可能。

        Args:
            company: 挿入する企業データ

        Returns:
            挿入成功時True、失敗時False

        Example:
            >>> company = Company(symbol="1332.T", name="ニッスイ", ...)
            >>> success = service.insert_company(company)
            >>> print(success)
            True
        """
        try:
            connection = self.db_connection.get_connection()
            sql = """
            INSERT INTO company (symbol, name, market, business_summary, price)
            VALUES (?, ?, ?, ?, ?)
            """
            connection.execute(
                sql,
                (
                    company.symbol,
                    company.name,
                    company.market,
                    company.business_summary,
                    company.price,
                ),
            )
            connection.commit()
            logger.debug("企業データ挿入成功: %s", company.symbol)
            return True

        except sqlite3.IntegrityError as e:
            logger.debug("企業データ挿入失敗（重複）: %s - %s", company.symbol, e)
            return False
        except Exception as e:
            logger.error("企業データ挿入エラー: %s - %s", company.symbol, e)
            return False

    def get_company_by_symbol(self, symbol: str) -> Company | None:
        """指定されたシンボルの企業データを取得する

        マルチスレッド環境で安全に実行可能。

        Args:
            symbol: 企業のシンボル（例: 1332.T）

        Returns:
            企業データ、見つからない場合はNone

        Example:
            >>> company = service.get_company_by_symbol("1332.T")
            >>> if company:
            ...     print(f"{company.name}: ¥{company.price}")
        """
        try:
            connection = self.db_connection.get_connection()
            sql = """
            SELECT symbol, name, market, business_summary, price,
                   last_updated, created_at
            FROM company
            WHERE symbol = ?
            """
            cursor = connection.execute(sql, (symbol,))
            row = cursor.fetchone()

            if row:
                return Company(
                    symbol=row[0],
                    name=row[1],
                    market=row[2],
                    business_summary=row[3],
                    price=row[4],
                )
            return None

        except Exception as e:
            logger.error("企業データ取得エラー: %s - %s", symbol, e)
            return None

    def update_company(self, company: Company) -> bool:
        """企業データを更新する

        指定されたシンボルの企業データを更新する。
        企業が存在しない場合は失敗する。
        マルチスレッド環境で安全に実行可能。

        Args:
            company: 更新する企業データ

        Returns:
            更新成功時True、失敗時False

        Example:
            >>> company.price = 900.0
            >>> success = service.update_company(company)
        """
        try:
            connection = self.db_connection.get_connection()
            sql = """
            UPDATE company
            SET name = ?, market = ?, business_summary = ?, price = ?,
                last_updated = CURRENT_TIMESTAMP
            WHERE symbol = ?
            """
            cursor = connection.execute(
                sql,
                (
                    company.name,
                    company.market,
                    company.business_summary,
                    company.price,
                    company.symbol,
                ),
            )
            connection.commit()

            if cursor.rowcount > 0:
                logger.debug("企業データ更新成功: %s", company.symbol)
                return True
            else:
                logger.debug("企業データ更新失敗（対象なし）: %s", company.symbol)
                return False

        except Exception as e:
            logger.error("企業データ更新エラー: %s - %s", company.symbol, e)
            return False

    def delete_company(self, symbol: str) -> bool:
        """指定されたシンボルの企業データを削除する

        マルチスレッド環境で安全に実行可能。

        Args:
            symbol: 削除する企業のシンボル

        Returns:
            削除成功時True、失敗時False

        Example:
            >>> success = service.delete_company("1332.T")
        """
        try:
            connection = self.db_connection.get_connection()
            sql = "DELETE FROM company WHERE symbol = ?"
            cursor = connection.execute(sql, (symbol,))
            connection.commit()

            if cursor.rowcount > 0:
                logger.debug("企業データ削除成功: %s", symbol)
                return True
            else:
                logger.debug("企業データ削除失敗（対象なし）: %s", symbol)
                return False

        except Exception as e:
            logger.error("企業データ削除エラー: %s - %s", symbol, e)
            return False

    def get_all_companies(self) -> list[Company]:
        """全ての企業データを取得する

        マルチスレッド環境で安全に実行可能。

        Returns:
            企業データのリスト

        Example:
            >>> companies = service.get_all_companies()
            >>> print(f"企業数: {len(companies)}")
        """
        try:
            connection = self.db_connection.get_connection()
            sql = """
            SELECT symbol, name, market, business_summary, price
            FROM company
            ORDER BY symbol
            """
            cursor = connection.execute(sql)
            rows = cursor.fetchall()

            companies = []
            for row in rows:
                company = Company(
                    symbol=row[0],
                    name=row[1],
                    market=row[2],
                    business_summary=row[3],
                    price=row[4],
                )
                companies.append(company)

            logger.debug("全企業データ取得完了: %d件", len(companies))
            return companies

        except Exception as e:
            logger.error("全企業データ取得エラー: %s", e)
            return []

    def get_companies_by_market(self, market: str) -> list[Company]:
        """指定された市場の企業データを取得する

        マルチスレッド環境で安全に実行可能。

        Args:
            market: 市場名（例: 東P、東S、東G）

        Returns:
            企業データのリスト

        Example:
            >>> prime_companies = service.get_companies_by_market("東P")
        """
        try:
            connection = self.db_connection.get_connection()
            sql = """
            SELECT symbol, name, market, business_summary, price
            FROM company
            WHERE market = ?
            ORDER BY symbol
            """
            cursor = connection.execute(sql, (market,))
            rows = cursor.fetchall()

            companies = []
            for row in rows:
                company = Company(
                    symbol=row[0],
                    name=row[1],
                    market=row[2],
                    business_summary=row[3],
                    price=row[4],
                )
                companies.append(company)

            logger.debug("市場別企業データ取得完了: %s - %d件", market, len(companies))
            return companies

        except Exception as e:
            logger.error("市場別企業データ取得エラー: %s - %s", market, e)
            return []

    def batch_insert_companies(self, companies: list[Company]) -> dict[str, Any]:
        """企業データを一括挿入する

        複数の企業データを効率的に挿入する。
        重複エラーが発生した場合はスキップして続行する。
        マルチスレッド環境で安全に実行可能。

        Args:
            companies: 挿入する企業データのリスト

        Returns:
            挿入結果の統計情報

        Example:
            >>> companies = [company1, company2, company3]
            >>> result = service.batch_insert_companies(companies)
            >>> print(f"成功: {result['successful']}件")
        """
        if not companies:
            return {"successful": 0, "failed": 0, "failed_symbols": []}

        successful = 0
        failed = 0
        failed_symbols = []

        logger.info("企業データ一括挿入開始: %d件", len(companies))

        for company in companies:
            if self.insert_company(company):
                successful += 1
            else:
                failed += 1
                failed_symbols.append(company.symbol)

        logger.info("企業データ一括挿入完了: 成功 %d件, 失敗 %d件", successful, failed)

        return {
            "successful": successful,
            "failed": failed,
            "failed_symbols": failed_symbols,
        }

    def batch_update_companies(self, companies: list[Company]) -> dict[str, Any]:
        """企業データを一括更新する

        複数の企業データを効率的に更新する。
        マルチスレッド環境で安全に実行可能。

        Args:
            companies: 更新する企業データのリスト

        Returns:
            更新結果の統計情報

        Example:
            >>> companies = [updated_company1, updated_company2]
            >>> result = service.batch_update_companies(companies)
        """
        if not companies:
            return {"successful": 0, "failed": 0, "failed_symbols": []}

        successful = 0
        failed = 0
        failed_symbols = []

        logger.info("企業データ一括更新開始: %d件", len(companies))

        for company in companies:
            if self.update_company(company):
                successful += 1
            else:
                failed += 1
                failed_symbols.append(company.symbol)

        logger.info("企業データ一括更新完了: 成功 %d件, 失敗 %d件", successful, failed)

        return {
            "successful": successful,
            "failed": failed,
            "failed_symbols": failed_symbols,
        }

    def upsert_companies(self, companies: list[Company]) -> dict[str, Any]:
        """企業データをupsert（挿入または更新）する

        企業が存在しない場合は挿入、存在する場合は更新を行う。
        効率的なバッチ処理でデータベース操作を最適化する。
        マルチスレッド環境で安全に実行可能。

        Args:
            companies: upsertする企業データのリスト

        Returns:
            upsert結果の統計情報

        Example:
            >>> companies = [company1, company2, company3]
            >>> result = service.upsert_companies(companies)
            >>> print(f"挿入: {result['inserted']}件, 更新: {result['updated']}件")
        """
        if not companies:
            return {"inserted": 0, "updated": 0, "failed": 0, "failed_symbols": []}

        inserted = 0
        updated = 0
        failed = 0
        failed_symbols = []

        logger.info("企業データupsert開始: %d件", len(companies))

        for company in companies:
            # 既存データの確認
            existing = self.get_company_by_symbol(company.symbol)

            if existing is None:
                # 新規挿入
                if self.insert_company(company):
                    inserted += 1
                else:
                    failed += 1
                    failed_symbols.append(company.symbol)
            else:
                # 既存データ更新
                if self.update_company(company):
                    updated += 1
                else:
                    failed += 1
                    failed_symbols.append(company.symbol)

        logger.info(
            "企業データupsert完了: 挿入 %d件, 更新 %d件, 失敗 %d件",
            inserted,
            updated,
            failed,
        )

        return {
            "inserted": inserted,
            "updated": updated,
            "failed": failed,
            "failed_symbols": failed_symbols,
        }

    def find_companies_needing_update(
        self, csv_companies: list[Company]
    ) -> dict[str, list[Company]]:
        """更新が必要な企業を効率的に検出する

        CSVデータと既存データベースデータを比較し、差分を検出する。
        新規挿入、更新、変更なしの企業を分類する。
        マルチスレッド環境で安全に実行可能。

        Args:
            csv_companies: CSVから読み取った企業データのリスト

        Returns:
            差分分析結果の辞書

        Example:
            >>> csv_companies = reader.read_and_convert()
            >>> diff = service.find_companies_needing_update(csv_companies)
            >>> print(f"新規: {len(diff['to_insert'])}件")
            >>> print(f"更新: {len(diff['to_update'])}件")
        """
        logger.info("差分分析開始: CSV %d件", len(csv_companies))

        # 既存の全企業データを取得
        existing_companies = self.get_all_companies()
        existing_dict = {comp.symbol: comp for comp in existing_companies}

        to_insert = []
        to_update = []
        no_change = []

        for csv_company in csv_companies:
            existing_company = existing_dict.get(csv_company.symbol)

            if existing_company is None:
                # 新規企業
                to_insert.append(csv_company)
            else:
                # 既存企業：変更があるかチェック
                if self._has_significant_changes(existing_company, csv_company):
                    to_update.append(csv_company)
                else:
                    no_change.append(csv_company)

        logger.info(
            "差分分析完了: 新規 %d件, 更新 %d件, 変更なし %d件",
            len(to_insert),
            len(to_update),
            len(no_change),
        )

        return {
            "to_insert": to_insert,
            "to_update": to_update,
            "no_change": no_change,
        }

    def get_database_stats(self) -> dict[str, Any]:
        """データベース統計情報を取得する

        企業数、市場別分布などの統計情報を返す。
        モニタリングやデバッグ用途に使用する。
        マルチスレッド環境で安全に実行可能。

        Returns:
            統計情報の辞書

        Example:
            >>> stats = service.get_database_stats()
            >>> print(f"総企業数: {stats['total_companies']}")
        """
        try:
            connection = self.db_connection.get_connection()
            
            # 総企業数
            cursor = connection.execute("SELECT COUNT(*) FROM company")
            total_companies = cursor.fetchone()[0]

            # 市場別分布
            cursor = connection.execute(
                "SELECT market, COUNT(*) FROM company GROUP BY market"
            )
            market_rows = cursor.fetchall()
            markets = {row[0]: row[1] for row in market_rows}

            # 最終更新日時
            cursor = connection.execute("SELECT MAX(last_updated) FROM company")
            last_update_row = cursor.fetchone()
            last_updated = last_update_row[0] if last_update_row[0] else None

            stats = {
                "total_companies": total_companies,
                "markets": markets,
                "last_updated": last_updated,
            }

            logger.debug("データベース統計情報取得完了: %d社", total_companies)
            return stats

        except Exception as e:
            logger.error("データベース統計情報取得エラー: %s", e)
            return {
                "total_companies": 0,
                "markets": {},
                "last_updated": None,
            }

    def _has_significant_changes(self, existing: Company, new: Company) -> bool:
        """企業データに重要な変更があるかチェックする

        価格やビジネス要約の変更を検出する。
        軽微な変更（空白の違いなど）は無視する。

        Args:
            existing: 既存の企業データ
            new: 新しい企業データ

        Returns:
            重要な変更がある場合True

        Example:
            >>> has_changes = service._has_significant_changes(old_data, new_data)
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