"""CSV読み取りサービス

SBI証券スクリーニング結果CSVファイルの読み取り、パース、変換機能を提供
"""

from __future__ import annotations

import csv
import logging
from typing import Any

from stock_batch.models.company import Company, CSVCompanyData

logger = logging.getLogger(__name__)


class CSVReader:
    """CSV読み取りサービスクラス

    SBI証券のスクリーニング結果CSVファイルを読み取り、
    CSVCompanyData および Company オブジェクトに変換する。

    Attributes:
        csv_path: CSVファイルのパス

    Example:
        >>> reader = CSVReader("/data/screener_result.csv")
        >>> companies = reader.read_and_convert()
        >>> for company in companies:
        ...     print(f"{company.symbol}: {company.name}")
    """

    # 期待するCSVヘッダー（SBI証券スクリーニング結果の形式）
    EXPECTED_HEADERS = ["コード", "銘柄名", "市場", "現在値", "前日比(%)"]

    def __init__(self, csv_path: str) -> None:
        """CSVReader を初期化する

        Args:
            csv_path: CSVファイルのパス

        Example:
            >>> reader = CSVReader("/data/screener_result.csv")
            >>> reader.csv_path
            "/data/screener_result.csv"
        """
        self.csv_path = csv_path

    def read_csv(self) -> list[CSVCompanyData]:
        """CSVファイルを読み取り、CSVCompanyDataのリストを返す

        BOM付きUTF-8、Shift_JIS、UTF-8の順で文字エンコーディングを試行する。
        不正なデータ行はスキップし、有効なデータのみを返す。

        Returns:
            CSVCompanyDataオブジェクトのリスト

        Raises:
            FileNotFoundError: CSVファイルが存在しない場合
            IOError: ファイル読み取りエラーの場合

        Example:
            >>> reader = CSVReader("/data/screener_result.csv")
            >>> companies = reader.read_csv()
            >>> len(companies)
            1500
        """
        encodings_to_try = ["utf-8-sig", "shift_jis", "utf-8"]
        companies = []

        for encoding in encodings_to_try:
            try:
                with open(self.csv_path, encoding=encoding, newline="") as file:
                    csv_reader = csv.reader(file)

                    # ヘッダー読み取り
                    headers = next(csv_reader, None)
                    if headers is None:
                        logger.warning("CSVファイルが空です: %s", self.csv_path)
                        return []

                    # BOM除去（必要に応じて）
                    if headers[0].startswith("\ufeff"):
                        headers[0] = headers[0][1:]

                    # ヘッダー検証
                    if not self.validate_headers(headers):
                        logger.warning(
                            "CSVヘッダーが期待する形式と異なります。"
                            "期待値: %s, 実際: %s",
                            self.EXPECTED_HEADERS,
                            headers,
                        )

                    # データ行読み取り
                    line_number = 1
                    for row in csv_reader:
                        line_number += 1
                        try:
                            if len(row) >= 5:  # 必要な列数をチェック
                                company_data = CSVCompanyData(
                                    code=row[0].strip().strip('"'),
                                    name=row[1].strip().strip('"'),
                                    market=row[2].strip().strip('"'),
                                    current_value=row[3].strip().strip('"'),
                                    change_percent=row[4].strip().strip('"'),
                                )
                                companies.append(company_data)
                            else:
                                logger.warning(
                                    "行 %d: 列数が不足しています（%d列）: %s",
                                    line_number,
                                    len(row),
                                    row,
                                )
                        except ValueError as e:
                            logger.warning(
                                "行 %d: データ形式エラー: %s - %s", line_number, e, row
                            )
                            continue

                logger.info(
                    "CSV読み取り完了: %s (%s) - %d件の企業データ",
                    self.csv_path,
                    encoding,
                    len(companies),
                )
                return self.filter_valid_companies(companies)

            except UnicodeDecodeError:
                logger.debug("エンコーディング %s で読み取り失敗、次を試行", encoding)
                continue
            except FileNotFoundError:
                logger.error("CSVファイルが見つかりません: %s", self.csv_path)
                raise
            except OSError as e:
                logger.error("CSVファイル読み取りエラー: %s - %s", self.csv_path, e)
                raise

        # すべてのエンコーディングで失敗した場合
        logger.error(
            "すべてのエンコーディングで読み取りに失敗しました: %s", self.csv_path
        )
        raise OSError(f"CSVファイル読み取りに失敗しました: {self.csv_path}")

    def validate_headers(self, headers: list[str]) -> bool:
        """CSVヘッダーが期待する形式かチェックする

        Args:
            headers: CSVファイルのヘッダー行

        Returns:
            期待する形式の場合True、そうでなければFalse

        Example:
            >>> reader = CSVReader("/dummy/path")
            >>> headers = ["コード", "銘柄名", "市場", "現在値", "前日比(%)"]
            >>> reader.validate_headers(headers)
            True
        """
        if len(headers) < len(self.EXPECTED_HEADERS):
            return False

        for i, expected_header in enumerate(self.EXPECTED_HEADERS):
            if i >= len(headers) or headers[i].strip().strip('"') != expected_header:
                return False

        return True

    def filter_valid_companies(
        self, companies: list[CSVCompanyData]
    ) -> list[CSVCompanyData]:
        """有効な企業データのみをフィルタリングする

        以下の条件をチェックし、無効なデータを除外する:
        - 株式コードが空でない
        - 企業名が空でない
        - 現在値が数値として解析可能

        Args:
            companies: フィルタリング前の企業データリスト

        Returns:
            有効な企業データのリスト

        Example:
            >>> reader = CSVReader("/dummy/path")
            >>> data = CSVCompanyData("1332", "ニッスイ", "東P", "877.8", "+0.40%")
            >>> valid_data = [data]
            >>> invalid_data = [CSVCompanyData("", "空コード", "東P", "100", "0")]
            >>> all_data = valid_data + invalid_data
            >>> filtered = reader.filter_valid_companies(all_data)
            >>> len(filtered)
            1
        """
        valid_companies = []
        invalid_count = 0

        for company in companies:
            try:
                # 基本的な検証
                if not company.code.strip():
                    logger.debug("無効なデータ: 株式コードが空 - %s", company.name)
                    invalid_count += 1
                    continue

                if not company.name.strip():
                    logger.debug("無効なデータ: 企業名が空 - %s", company.code)
                    invalid_count += 1
                    continue

                # 価格の数値変換テスト
                float(company.current_value)

                valid_companies.append(company)

            except (ValueError, AttributeError) as e:
                logger.debug(
                    "無効なデータ: %s - %s (%s)", company.code, company.name, e
                )
                invalid_count += 1

        if invalid_count > 0:
            logger.info(
                "データフィルタリング完了: 有効 %d件, 無効 %d件",
                len(valid_companies),
                invalid_count,
            )

        return valid_companies

    def convert_to_companies(
        self, csv_companies: list[CSVCompanyData]
    ) -> list[Company]:
        """CSVCompanyDataをCompanyオブジェクトに変換する

        株式コードをyfinance形式のシンボルに変換し、
        現在値を浮動小数点数に変換して Company オブジェクトを作成する。

        Args:
            csv_companies: 変換元のCSVCompanyDataリスト

        Returns:
            Companyオブジェクトのリスト

        Example:
            >>> reader = CSVReader("/dummy/path")
            >>> data = CSVCompanyData("1332", "ニッスイ", "東P", "877.8", "+0.40%")
            >>> csv_data = [data]
            >>> companies = reader.convert_to_companies(csv_data)
            >>> companies[0].symbol
            "1332.T"
        """
        companies = []

        for csv_company in csv_companies:
            try:
                company = csv_company.to_company()
                companies.append(company)
            except Exception as e:
                logger.warning(
                    "企業データ変換エラー: %s (%s) - %s",
                    csv_company.code,
                    csv_company.name,
                    e,
                )

        logger.info(
            "企業データ変換完了: %d件 → %d件", len(csv_companies), len(companies)
        )
        return companies

    def read_and_convert(self) -> list[Company]:
        """CSV読み取りから Company オブジェクト変換までを一括実行

        読み取り → フィルタリング → 変換の全ワークフローを実行する。

        Returns:
            Companyオブジェクトのリスト

        Raises:
            FileNotFoundError: CSVファイルが存在しない場合
            IOError: ファイル読み取りエラーの場合

        Example:
            >>> reader = CSVReader("/data/screener_result.csv")
            >>> companies = reader.read_and_convert()
            >>> for company in companies:
            ...     print(f"{company.symbol}: {company.name} - ¥{company.price}")
        """
        logger.info("CSV読み取り・変換処理を開始: %s", self.csv_path)

        # CSV読み取り
        csv_companies = self.read_csv()

        # Company オブジェクトに変換
        companies = self.convert_to_companies(csv_companies)

        logger.info(
            "CSV読み取り・変換処理完了: %s - %d件の企業データ",
            self.csv_path,
            len(companies),
        )
        return companies

    def get_csv_stats(self, csv_companies: list[CSVCompanyData]) -> dict[str, Any]:
        """CSV読み取り統計情報を取得する

        デバッグやモニタリング用に統計情報を提供する。

        Args:
            csv_companies: 統計対象のCSVCompanyDataリスト

        Returns:
            統計情報の辞書

        Example:
            >>> reader = CSVReader("/data/screener_result.csv")
            >>> csv_companies = reader.read_csv()
            >>> stats = reader.get_csv_stats(csv_companies)
            >>> stats["total_companies"]
            1500
        """
        if not csv_companies:
            return {
                "total_companies": 0,
                "valid_companies": 0,
                "invalid_companies": 0,
                "markets": {},
            }

        # フィルタリング前後の件数
        valid_companies = self.filter_valid_companies(csv_companies)

        # 市場別統計
        market_stats: dict[str, int] = {}
        for company in valid_companies:
            market = company.market
            market_stats[market] = market_stats.get(market, 0) + 1

        return {
            "total_companies": len(csv_companies),
            "valid_companies": len(valid_companies),
            "invalid_companies": len(csv_companies) - len(valid_companies),
            "markets": market_stats,
        }
