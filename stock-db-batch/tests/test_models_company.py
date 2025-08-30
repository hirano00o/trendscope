"""Company モデルのテストコード

Companyモデルの検証、バリデーション、変換機能をテストします。
"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from stock_batch.models.company import Company, CSVCompanyData


class TestCompany:
    """Company データクラスのテスト"""

    def test_create_company_with_all_fields(self) -> None:
        """全フィールドを指定したCompany作成のテスト"""
        company = Company(
            symbol="1332.T",
            name="ニッスイ",
            market="東P",
            business_summary="水産物の製造・販売を行う企業",
            price=877.8,
        )

        assert company.symbol == "1332.T"
        assert company.name == "ニッスイ"
        assert company.market == "東P"
        assert company.business_summary == "水産物の製造・販売を行う企業"
        assert company.price == 877.8
        assert company.id is None  # デフォルト値
        assert company.last_updated is None  # デフォルト値
        assert company.created_at is None  # デフォルト値

    def test_create_company_with_required_fields_only(self) -> None:
        """必須フィールドのみでのCompany作成のテスト"""
        company = Company(
            symbol="1418.T",
            name="インターライフＨＬＤＧ",
        )

        assert company.symbol == "1418.T"
        assert company.name == "インターライフＨＬＤＧ"
        assert company.market is None
        assert company.business_summary is None
        assert company.price is None

    def test_company_validation_empty_symbol(self) -> None:
        """空のsymbolでのバリデーションエラーのテスト"""
        with pytest.raises(ValidationError) as exc_info:
            Company(symbol="", name="テスト企業")

        errors = exc_info.value.errors()
        assert any(error["type"] == "string_too_short" for error in errors)

    def test_company_validation_empty_name(self) -> None:
        """空のnameでのバリデーションエラーのテスト"""
        with pytest.raises(ValidationError) as exc_info:
            Company(symbol="1234.T", name="")

        errors = exc_info.value.errors()
        assert any(error["type"] == "string_too_short" for error in errors)

    def test_company_validation_negative_price(self) -> None:
        """負の価格でのバリデーションエラーのテスト"""
        with pytest.raises(ValidationError) as exc_info:
            Company(symbol="1234.T", name="テスト企業", price=-100.0)

        errors = exc_info.value.errors()
        assert any(error["type"] == "greater_than_equal" for error in errors)

    def test_company_set_timestamps(self) -> None:
        """タイムスタンプ設定のテスト"""
        company = Company(symbol="1234.T", name="テスト企業")
        now = datetime.now()

        company.set_timestamps(created_at=now, last_updated=now)

        assert company.created_at == now
        assert company.last_updated == now


class TestCSVCompanyData:
    """CSVCompanyData データクラスのテスト"""

    def test_create_csv_company_data(self) -> None:
        """CSVCompanyData作成のテスト"""
        csv_data = CSVCompanyData(
            code="1332",
            name="ニッスイ",
            market="東P",
            current_value="877.8",
            change_percent="+3.5(+0.40%)",
        )

        assert csv_data.code == "1332"
        assert csv_data.name == "ニッスイ"
        assert csv_data.market == "東P"
        assert csv_data.current_value == "877.8"
        assert csv_data.change_percent == "+3.5(+0.40%)"

    def test_csv_to_symbol_conversion_japanese_stock(self) -> None:
        """日本株式のシンボル変換テスト（XXXX → XXXX.T）"""
        csv_data = CSVCompanyData(
            code="1332",
            name="ニッスイ",
            market="東P",
            current_value="877.8",
            change_percent="+3.5(+0.40%)",
        )

        symbol = csv_data.to_yfinance_symbol()
        assert symbol == "1332.T"

    def test_csv_to_symbol_conversion_with_alphabet_code(self) -> None:
        """アルファベット含む株式コードのシンボル変換テスト（130A → 130A.T）"""
        csv_data = CSVCompanyData(
            code="130A",
            name="Ｖｅｒｉｔａｓ　Ｉｎ　Ｓｉｌｉ",
            market="東G",
            current_value="646",
            change_percent="-33.0(-4.86%)",
        )

        symbol = csv_data.to_yfinance_symbol()
        assert symbol == "130A.T"

    def test_csv_parse_current_price_float(self) -> None:
        """現在値の浮動小数点変換テスト"""
        csv_data = CSVCompanyData(
            code="1332",
            name="ニッスイ",
            market="東P",
            current_value="877.8",
            change_percent="+3.5(+0.40%)",
        )

        price = csv_data.parse_current_price()
        assert price == 877.8

    def test_csv_parse_current_price_integer(self) -> None:
        """整数価格の変換テスト"""
        csv_data = CSVCompanyData(
            code="130A",
            name="Ｖｅｒｉｔａｓ　Ｉｎ　Ｓｉｌｉ",
            market="東G",
            current_value="646",
            change_percent="-33.0(-4.86%)",
        )

        price = csv_data.parse_current_price()
        assert price == 646.0

    def test_csv_parse_current_price_invalid(self) -> None:
        """無効な価格文字列での変換エラーテスト"""
        csv_data = CSVCompanyData(
            code="1234",
            name="テスト企業",
            market="東P",
            current_value="invalid",
            change_percent="0",
        )

        with pytest.raises(ValueError):
            csv_data.parse_current_price()

    def test_csv_to_company_conversion(self) -> None:
        """CSVDataからCompanyへの変換テスト"""
        csv_data = CSVCompanyData(
            code="1332",
            name="ニッスイ",
            market="東P",
            current_value="877.8",
            change_percent="+3.5(+0.40%)",
        )

        company = csv_data.to_company()

        assert company.symbol == "1332.T"
        assert company.name == "ニッスイ"
        assert company.market == "東P"
        assert company.price == 877.8
        assert company.business_summary is None  # CSV段階では未取得

    def test_csv_validation_required_fields(self) -> None:
        """CSVCompanyDataの必須フィールドバリデーションテスト"""
        with pytest.raises(ValueError):
            CSVCompanyData(
                code="",  # 空のコード
                name="テスト企業",
                market="東P",
                current_value="100",
                change_percent="0",
            )
