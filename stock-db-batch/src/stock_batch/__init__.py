"""TrendScope Stock Database Batch Application

株価データベース更新バッチアプリケーション
- CSVから企業データを読み取り
- yfinanceで株価・企業情報を取得
- Google翻訳で企業概要を日本語化
- SQLiteデータベースを効率的に更新
"""

__version__ = "1.0.0"
