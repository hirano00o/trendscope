"""CSV読み取りサービスのテストコード

CSV形式のスクリーニング結果を読み取り、パース、変換する機能をテストします。
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from stock_batch.models.company import CSVCompanyData
from stock_batch.services.csv_reader import CSVReader


class TestCSVReader:
    """CSVReader クラスのテスト"""

    def test_create_csv_reader(self) -> None:
        """CSVReader 作成のテスト"""
        reader = CSVReader("/path/to/csv/file.csv")
        assert reader.csv_path == "/path/to/csv/file.csv"

    def test_read_csv_file_success(self) -> None:
        """CSVファイル読み取り成功のテスト"""
        # テスト用CSVファイル作成
        csv_content = '''﻿"コード","銘柄名","市場","現在値","前日比(%)"
"1332","ニッスイ","東P","877.8","+3.5(+0.40%)"
"1418","インターライフＨＬＤＧ","東S","405","-1.0(-0.25%)"
"130A","Ｖｅｒｉｔａｓ　Ｉｎ　Ｓｉｌｉ","東G","646","-33.0(-4.86%)"'''

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as tmp_file:
            tmp_file.write(csv_content)
            tmp_file_path = tmp_file.name

        try:
            reader = CSVReader(tmp_file_path)
            companies = reader.read_csv()

            assert len(companies) == 3

            # 1番目の企業データ検証
            first_company = companies[0]
            assert first_company.code == "1332"
            assert first_company.name == "ニッスイ"
            assert first_company.market == "東P"
            assert first_company.current_value == "877.8"
            assert first_company.change_percent == "+3.5(+0.40%)"

            # アルファベット含むコード検証
            third_company = companies[2]
            assert third_company.code == "130A"
            assert third_company.name == "Ｖｅｒｉｔａｓ　Ｉｎ　Ｓｉｌｉ"

        finally:
            Path(tmp_file_path).unlink(missing_ok=True)

    def test_read_csv_file_not_found(self) -> None:
        """存在しないCSVファイルのテスト"""
        reader = CSVReader("/nonexistent/path/file.csv")

        with pytest.raises(FileNotFoundError):
            reader.read_csv()

    def test_read_csv_with_bom(self) -> None:
        """BOM付きCSVファイル読み取りのテスト"""
        # BOM付きCSVコンテンツ（Excel保存時の形式）
        csv_content = '''﻿"コード","銘柄名","市場","現在値","前日比(%)"
"1332","ニッスイ","東P","877.8","+3.5(+0.40%)"'''

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8-sig"
        ) as tmp_file:
            tmp_file.write(csv_content)
            tmp_file_path = tmp_file.name

        try:
            reader = CSVReader(tmp_file_path)
            companies = reader.read_csv()

            assert len(companies) == 1
            assert companies[0].code == "1332"

        finally:
            Path(tmp_file_path).unlink(missing_ok=True)

    def test_read_csv_with_malformed_data(self) -> None:
        """不正な形式のCSVデータのテスト"""
        # 列数が不足しているデータ
        csv_content = '''﻿"コード","銘柄名","市場","現在値","前日比(%)"
"1332","ニッスイ","東P","877.8"
"1418","インターライフＨＬＤＧ","東S","405","-1.0(-0.25%)"'''

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as tmp_file:
            tmp_file.write(csv_content)
            tmp_file_path = tmp_file.name

        try:
            reader = CSVReader(tmp_file_path)
            companies = reader.read_csv()

            # 2行目はスキップされ、有効な1行のみ読み込まれる
            assert len(companies) == 1
            assert companies[0].code == "1418"

        finally:
            Path(tmp_file_path).unlink(missing_ok=True)

    def test_read_csv_empty_file(self) -> None:
        """空のCSVファイルのテスト"""
        csv_content = """﻿"コード","銘柄名","市場","現在値","前日比(%)"
"""

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as tmp_file:
            tmp_file.write(csv_content)
            tmp_file_path = tmp_file.name

        try:
            reader = CSVReader(tmp_file_path)
            companies = reader.read_csv()

            # ヘッダーのみで企業データは0件
            assert len(companies) == 0

        finally:
            Path(tmp_file_path).unlink(missing_ok=True)

    def test_validate_csv_headers(self) -> None:
        """CSVヘッダー検証のテスト"""
        # 正しいヘッダー
        correct_headers = ["コード", "銘柄名", "市場", "現在値", "前日比(%)"]
        reader = CSVReader("/dummy/path")

        result = reader.validate_headers(correct_headers)
        assert result is True

    def test_validate_csv_headers_incorrect(self) -> None:
        """不正なCSVヘッダーのテスト"""
        # 間違ったヘッダー
        incorrect_headers = ["Code", "Name", "Market", "Price", "Change"]
        reader = CSVReader("/dummy/path")

        result = reader.validate_headers(incorrect_headers)
        assert result is False

    def test_filter_valid_companies(self) -> None:
        """有効企業データのフィルタリングテスト"""
        reader = CSVReader("/dummy/path")

        # テスト用データ（一部に不正データ含む）
        # NOTE: CSVCompanyDataは__post_init__でバリデーションするため、
        # 有効なデータのみでテストし、無効データは別途テストする
        test_data = [
            CSVCompanyData("1332", "ニッスイ", "東P", "877.8", "+3.5(+0.40%)"),
            CSVCompanyData("130A", "正常企業", "東G", "invalid", "0"),  # 不正：価格形式
            CSVCompanyData("1420", "正常企業2", "東S", "680", "-1.0(-0.15%)"),
        ]

        valid_companies = reader.filter_valid_companies(test_data)

        # 有効な企業データのみ残る（1332.T, 1420.T）- invalidな価格は除外
        assert len(valid_companies) == 2
        assert valid_companies[0].code == "1332"
        assert valid_companies[1].code == "1420"

    def test_read_csv_with_encoding_detection(self) -> None:
        """文字エンコーディング自動検出のテスト"""
        # Shift_JISエンコーディングのテストファイル
        csv_content = '''"コード","銘柄名","市場","現在値","前日比(%)"
"1332","ニッスイ","東P","877.8","+3.5(+0.40%)"'''

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="shift_jis"
        ) as tmp_file:
            tmp_file.write(csv_content)
            tmp_file_path = tmp_file.name

        try:
            reader = CSVReader(tmp_file_path)
            companies = reader.read_csv()

            assert len(companies) == 1
            assert companies[0].name == "ニッスイ"

        finally:
            Path(tmp_file_path).unlink(missing_ok=True)

    def test_get_csv_stats(self) -> None:
        """CSV統計情報取得のテスト"""
        csv_content = '''﻿"コード","銘柄名","市場","現在値","前日比(%)"
"1332","ニッスイ","東P","877.8","+3.5(+0.40%)"
"1418","インターライフＨＬＤＧ","東S","405","-1.0(-0.25%)"
"130A","Ｖｅｒｉｔａｓ　Ｉｎ　Ｓｉｌｉ","東G","646","-33.0(-4.86%)"'''

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as tmp_file:
            tmp_file.write(csv_content)
            tmp_file_path = tmp_file.name

        try:
            reader = CSVReader(tmp_file_path)
            companies = reader.read_csv()
            stats = reader.get_csv_stats(companies)

            assert stats["total_companies"] == 3
            assert stats["valid_companies"] == 3
            assert stats["invalid_companies"] == 0
            assert "markets" in stats
            assert "東P" in stats["markets"]
            assert "東S" in stats["markets"]
            assert "東G" in stats["markets"]

        finally:
            Path(tmp_file_path).unlink(missing_ok=True)

    @patch("builtins.open")
    def test_read_csv_io_error(self, mock_open: Mock) -> None:
        """CSV読み取り時のIOエラーのテスト"""
        mock_open.side_effect = OSError("ファイル読み取りエラー")

        reader = CSVReader("/path/to/file.csv")

        with pytest.raises(IOError):
            reader.read_csv()

    def test_convert_to_companies(self) -> None:
        """CSVCompanyDataからCompanyオブジェクトへの変換テスト"""
        reader = CSVReader("/dummy/path")

        csv_data = [
            CSVCompanyData("1332", "ニッスイ", "東P", "877.8", "+3.5(+0.40%)"),
            CSVCompanyData(
                "1418", "インターライフＨＬＤＧ", "東S", "405", "-1.0(-0.25%)"
            ),
        ]

        companies = reader.convert_to_companies(csv_data)

        assert len(companies) == 2

        # yfinanceシンボル変換確認
        assert companies[0].symbol == "1332.T"
        assert companies[0].name == "ニッスイ"
        assert companies[0].price == 877.8

        assert companies[1].symbol == "1418.T"
        assert companies[1].name == "インターライフＨＬＤＧ"
        assert companies[1].price == 405.0

    def test_read_and_convert_full_workflow(self) -> None:
        """CSV読み取りから変換までのフルワークフローテスト"""
        csv_content = '''﻿"コード","銘柄名","市場","現在値","前日比(%)"
"1332","ニッスイ","東P","877.8","+3.5(+0.40%)"
"1418","インターライフＨＬＤＧ","東S","405","-1.0(-0.25%)"'''

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as tmp_file:
            tmp_file.write(csv_content)
            tmp_file_path = tmp_file.name

        try:
            reader = CSVReader(tmp_file_path)
            companies = reader.read_and_convert()

            assert len(companies) == 2
            assert companies[0].symbol == "1332.T"
            assert companies[1].symbol == "1418.T"
            # business_summaryはCSV段階では未設定
            assert companies[0].business_summary is None

        finally:
            Path(tmp_file_path).unlink(missing_ok=True)
