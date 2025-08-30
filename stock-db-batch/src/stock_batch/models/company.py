"""Company データモデル

株式企業情報を表すデータクラスとCSVデータ変換機能を提供
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from pydantic import BaseModel, Field


class Company(BaseModel):
    """株式企業情報を表すデータクラス

    データベースのcompanyテーブルに対応するデータ構造

    Attributes:
        id: データベース内の一意識別子
        symbol: yfinance用の株式シンボル（例: 1332.T）
        name: 企業名
        market: 市場区分（東P、東G、東S等）
        business_summary: 企業概要（日本語）
        price: 株価（更新時点での価格）
        last_updated: 最終更新日時
        created_at: 作成日時

    Example:
        >>> company = Company(
        ...     symbol="1332.T",
        ...     name="ニッスイ",
        ...     market="東P",
        ...     price=877.8
        ... )
        >>> print(company.symbol)
        "1332.T"
    """

    id: int | None = None
    symbol: str = Field(min_length=1, description="yfinance用の株式シンボル")
    name: str = Field(min_length=1, description="企業名")
    market: str | None = Field(default=None, description="市場区分")
    business_summary: str | None = Field(default=None, description="企業概要（日本語）")
    price: float | None = Field(default=None, ge=0.0, description="株価")
    last_updated: datetime | None = Field(default=None, description="最終更新日時")
    created_at: datetime | None = Field(default=None, description="作成日時")

    def set_timestamps(
        self,
        created_at: datetime | None = None,
        last_updated: datetime | None = None,
    ) -> None:
        """タイムスタンプを設定する

        Args:
            created_at: 作成日時（Noneの場合は変更しない）
            last_updated: 最終更新日時（Noneの場合は変更しない）

        Example:
            >>> company = Company(symbol="1332.T", name="ニッスイ")
            >>> now = datetime.now()
            >>> company.set_timestamps(created_at=now, last_updated=now)
        """
        if created_at is not None:
            self.created_at = created_at
        if last_updated is not None:
            self.last_updated = last_updated


@dataclass
class CSVCompanyData:
    """CSV形式の企業データを表すデータクラス

    SBI証券スクリーニング結果CSVから読み取った生データを保持

    Attributes:
        code: 株式コード（例: 1332, 130A）
        name: 企業名
        market: 市場区分（東P、東G、東S、札P、名P、大P、福P等）
        current_value: 現在値（文字列）
        change_percent: 前日比（%）（文字列）

    Example:
        >>> csv_data = CSVCompanyData(
        ...     code="1332",
        ...     name="ニッスイ",
        ...     market="東P",
        ...     current_value="877.8",
        ...     change_percent="+3.5(+0.40%)"
        ... )
        >>> symbol = csv_data.to_yfinance_symbol()
        >>> print(symbol)
        "1332.T"
    """

    # 市場区分から取引所識別子へのマッピング
    EXCHANGE_MAPPING = {
        "札": ".S",  # 札幌証券取引所
        "東": ".T",  # 東京証券取引所
        "福": ".F",  # 福岡証券取引所
        "名": ".N",  # 名古屋証券取引所
        "大": ".OS", # 大阪証券取引所
    }

    code: str
    name: str
    market: str
    current_value: str
    change_percent: str

    def __post_init__(self) -> None:
        """初期化後の検証処理"""
        if not self.code.strip():
            raise ValueError("株式コードは空にできません")
        if not self.name.strip():
            raise ValueError("企業名は空にできません")

    def to_yfinance_symbol(self) -> str:
        """CSV株式コードをyfinanceシンボルに変換する

        市場区分の1文字目に基づいて適切な取引所識別子を付加してyfinance対応シンボルにする
        
        識別子マッピング:
        - 札 → .S（札幌証券取引所）
        - 東 → .T（東京証券取引所）
        - 福 → .F（福岡証券取引所）  
        - 名 → .N（名古屋証券取引所）
        - 大 → .OS（大阪証券取引所）
        - その他 → .T（デフォルト：東京証券取引所）

        Returns:
            yfinance対応の株式シンボル

        Example:
            >>> csv_data = CSVCompanyData("1332", "ニッスイ", "東P", "877.8", "+0.40%")
            >>> symbol = csv_data.to_yfinance_symbol()
            >>> print(symbol)
            "1332.T"
            
            >>> csv_data = CSVCompanyData("3698", "CRI・ミドルウェア", "札P", "1220.0", "-0.49%")
            >>> symbol = csv_data.to_yfinance_symbol()
            >>> print(symbol)
            "3698.S"
        """
        if not self.market:
            # 市場区分が空の場合は東京証券取引所をデフォルトとする
            return f"{self.code}.T"
        
        # 市場区分の1文字目を取得
        market_prefix = self.market[0]
        
        # マッピングから対応する識別子を取得（見つからない場合は.Tをデフォルト）
        exchange_suffix = self.EXCHANGE_MAPPING.get(market_prefix, ".T")
        
        return f"{self.code}{exchange_suffix}"

    def parse_current_price(self) -> float:
        """現在値文字列を浮動小数点数に変換する

        Returns:
            株価の浮動小数点値

        Raises:
            ValueError: 無効な価格文字列の場合

        Example:
            >>> csv_data = CSVCompanyData("1332", "ニッスイ", "東P", "877.8", "+0.40%")
            >>> price = csv_data.parse_current_price()
            >>> print(price)
            877.8
        """
        try:
            return float(self.current_value)
        except ValueError as e:
            raise ValueError(f"無効な価格文字列: {self.current_value}") from e

    def to_company(self) -> Company:
        """CSVCompanyDataからCompanyオブジェクトに変換する

        CSV読み取り段階では企業概要（business_summary）は未取得のため
        Noneに設定される

        Returns:
            変換されたCompanyオブジェクト

        Example:
            >>> csv_data = CSVCompanyData("1332", "ニッスイ", "東P", "877.8", "+0.40%")
            >>> company = csv_data.to_company()
            >>> print(company.symbol, company.name)
            "1332.T" "ニッスイ"
        """
        return Company(
            symbol=self.to_yfinance_symbol(),
            name=self.name,
            market=self.market,
            price=self.parse_current_price(),
            business_summary=None,  # CSV段階では企業概要は未取得
        )
