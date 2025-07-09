#!/usr/bin/env python3
"""バッチ株式分析スクリプト

複数の株式シンボルに対して包括的分析を実行し、
結果をCSV形式で出力するバッチ処理スクリプト。

使用例:
    python scripts/batch_analysis.py AAPL GOOGL MSFT TSLA 7203.T
    python scripts/batch_analysis.py --output results.csv --verbose AAPL GOOGL

必要条件:
    - バックエンドサーバーが起動していること (http://localhost:8000)
    - 有効な株式シンボルが指定されていること
"""

import argparse
import asyncio
import csv
import sys
import time
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin

import httpx


class StockAnalysisBatch:
    """バッチ株式分析クラス
    
    複数の株式シンボルに対して並列で包括的分析を実行し、
    結果をCSV形式で出力する機能を提供。
    
    Args:
        base_url: バックエンドAPIのベースURL
        timeout: HTTPリクエストのタイムアウト（秒）
        max_retries: 最大リトライ回数
        concurrent_limit: 同時リクエスト数の制限
        
    Example:
        >>> batch = StockAnalysisBatch()
        >>> results = await batch.analyze_symbols(["AAPL", "GOOGL"])
        >>> batch.output_csv(results)
    """
    
    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        timeout: float = 60.0,
        max_retries: int = 3,
        concurrent_limit: int = 10
    ):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        self.concurrent_limit = concurrent_limit
        self.semaphore = asyncio.Semaphore(concurrent_limit)
        
    async def analyze_symbol(
        self, 
        client: httpx.AsyncClient, 
        symbol: str,
        verbose: bool = False
    ) -> Dict[str, Any]:
        """単一シンボルの包括的分析を実行
        
        Args:
            client: HTTPクライアント
            symbol: 株式シンボル
            verbose: 詳細ログ出力フラグ
            
        Returns:
            分析結果辞書（symbol, confidence, overall_score, error等）
            
        Raises:
            Exception: API呼び出しが全てのリトライで失敗した場合
        """
        async with self.semaphore:
            url = f"{self.base_url}/api/v1/comprehensive/{symbol}"
            
            if verbose:
                print(f"🔍 分析開始: {symbol}")
            
            for attempt in range(self.max_retries + 1):
                try:
                    response = await client.get(url, timeout=self.timeout)
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        if data.get("success") and "data" in data:
                            analysis_data = data["data"]
                            integrated_score = analysis_data.get("integrated_score", {})
                            
                            result = {
                                "symbol": symbol,
                                "confidence": float(integrated_score.get("confidence_level", 0.0)),
                                "overall_score": float(integrated_score.get("overall_score", 0.0)),
                                "error": None,
                                "status": "success"
                            }
                            
                            if verbose:
                                print(f"✅ 完了: {symbol} (スコア: {result['overall_score']:.3f}, 信頼度: {result['confidence']:.3f})")
                            
                            return result
                        else:
                            error_msg = "APIレスポンスが無効な形式です"
                            if verbose:
                                print(f"⚠️  {symbol}: {error_msg}")
                            return self._create_error_result(symbol, error_msg)
                    
                    elif response.status_code == 404:
                        error_msg = f"シンボル '{symbol}' のデータが見つかりません"
                        if verbose:
                            print(f"❌ {symbol}: {error_msg}")
                        return self._create_error_result(symbol, error_msg)
                    
                    elif response.status_code == 400:
                        error_msg = f"無効なシンボル形式: '{symbol}'"
                        if verbose:
                            print(f"❌ {symbol}: {error_msg}")
                        return self._create_error_result(symbol, error_msg)
                    
                    else:
                        error_msg = f"HTTPエラー {response.status_code}"
                        if verbose and attempt < self.max_retries:
                            print(f"⚠️  {symbol}: {error_msg} - リトライ中 ({attempt + 1}/{self.max_retries})")
                        elif verbose:
                            print(f"❌ {symbol}: {error_msg} - リトライ回数上限")
                        
                        if attempt == self.max_retries:
                            return self._create_error_result(symbol, error_msg)
                
                except httpx.TimeoutException:
                    error_msg = "リクエストタイムアウト"
                    if verbose and attempt < self.max_retries:
                        print(f"⏱️  {symbol}: {error_msg} - リトライ中 ({attempt + 1}/{self.max_retries})")
                    elif verbose:
                        print(f"❌ {symbol}: {error_msg} - リトライ回数上限")
                    
                    if attempt == self.max_retries:
                        return self._create_error_result(symbol, error_msg)
                
                except httpx.ConnectError:
                    error_msg = "サーバーに接続できません"
                    if verbose and attempt < self.max_retries:
                        print(f"🔌 {symbol}: {error_msg} - リトライ中 ({attempt + 1}/{self.max_retries})")
                    elif verbose:
                        print(f"❌ {symbol}: {error_msg} - リトライ回数上限")
                    
                    if attempt == self.max_retries:
                        return self._create_error_result(symbol, error_msg)
                
                except Exception as e:
                    error_msg = f"予期しないエラー: {str(e)}"
                    if verbose:
                        print(f"❌ {symbol}: {error_msg}")
                    return self._create_error_result(symbol, error_msg)
                
                # リトライ前の待機
                if attempt < self.max_retries:
                    await asyncio.sleep(2 ** attempt)  # 指数バックオフ
    
    def _create_error_result(self, symbol: str, error: str) -> Dict[str, Any]:
        """エラー結果辞書を作成
        
        Args:
            symbol: 株式シンボル
            error: エラーメッセージ
            
        Returns:
            エラー結果辞書
        """
        return {
            "symbol": symbol,
            "confidence": 0.0,
            "overall_score": 0.0,
            "error": error,
            "status": "error"
        }
    
    async def analyze_symbols(
        self, 
        symbols: List[str], 
        verbose: bool = False
    ) -> List[Dict[str, Any]]:
        """複数シンボルの並列分析実行
        
        Args:
            symbols: 分析対象の株式シンボルリスト
            verbose: 詳細ログ出力フラグ
            
        Returns:
            全シンボルの分析結果リスト
            
        Example:
            >>> results = await batch.analyze_symbols(["AAPL", "GOOGL"], verbose=True)
            >>> len(results)
            2
        """
        if verbose:
            print(f"🚀 バッチ分析開始: {len(symbols)} シンボル")
            print(f"   同時接続数制限: {self.concurrent_limit}")
            print(f"   タイムアウト: {self.timeout}秒")
            print(f"   最大リトライ: {self.max_retries}回")
            print()
        
        start_time = time.time()
        
        async with httpx.AsyncClient() as client:
            # 全シンボルに対して並列でリクエスト実行
            tasks = [
                self.analyze_symbol(client, symbol.strip().upper(), verbose)
                for symbol in symbols
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 例外が発生した場合の処理
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    processed_results.append(
                        self._create_error_result(symbols[i], f"処理エラー: {str(result)}")
                    )
                else:
                    processed_results.append(result)
        
        end_time = time.time()
        duration = end_time - start_time
        
        if verbose:
            successful = sum(1 for r in processed_results if r["status"] == "success")
            failed = len(processed_results) - successful
            print()
            print(f"📊 分析完了:")
            print(f"   成功: {successful}件")
            print(f"   失敗: {failed}件")
            print(f"   実行時間: {duration:.2f}秒")
            print()
        
        return processed_results
    
    def output_csv(
        self, 
        results: List[Dict[str, Any]], 
        output_file: Optional[str] = None,
        include_errors: bool = False,
        verbose: bool = False
    ) -> None:
        """分析結果をCSV形式で出力
        
        Args:
            results: 分析結果リスト
            output_file: 出力ファイルパス（None の場合は標準出力）
            include_errors: エラー結果も含めて出力するか
            verbose: 詳細ログ出力フラグ
            
        Example:
            >>> batch.output_csv(results, "analysis_results.csv")
            >>> batch.output_csv(results)  # 標準出力
        """
        # 出力対象データのフィルタリング
        output_data = []
        for result in results:
            if result["status"] == "success":
                output_data.append(result)
            elif include_errors:
                # エラーの場合は confidence と overall_score を 0.0 として出力
                output_data.append(result)
        
        if verbose:
            if output_file:
                print(f"📝 CSV出力: {output_file}")
            else:
                print("📝 CSV出力: 標準出力")
            print(f"   出力レコード数: {len(output_data)}件")
        
        # CSV出力
        if output_file:
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                self._write_csv_data(csvfile, output_data, include_errors)
        else:
            self._write_csv_data(sys.stdout, output_data, include_errors)
    
    def _write_csv_data(
        self, 
        file_obj, 
        data: List[Dict[str, Any]], 
        include_errors: bool = False
    ) -> None:
        """CSV データの実際の書き込み処理
        
        Args:
            file_obj: 出力先ファイルオブジェクト
            data: 出力データ
            include_errors: エラー情報も含めるか
        """
        if include_errors:
            fieldnames = ['symbol', 'confidence', 'overall_score', 'error']
        else:
            fieldnames = ['symbol', 'confidence', 'overall_score']
        
        writer = csv.DictWriter(file_obj, fieldnames=fieldnames)
        writer.writeheader()
        
        for row in data:
            output_row = {
                'symbol': row['symbol'],
                'confidence': f"{row['confidence']:.6f}",
                'overall_score': f"{row['overall_score']:.6f}"
            }
            
            if include_errors:
                output_row['error'] = row.get('error', '')
            
            writer.writerow(output_row)


async def main():
    """メイン実行関数
    
    コマンドライン引数を解析してバッチ分析を実行する。
    
    Example:
        >>> python scripts/batch_analysis.py AAPL GOOGL MSFT
        symbol,confidence,overall_score
        AAPL,0.850000,0.720000
        GOOGL,0.780000,0.650000
        MSFT,0.820000,0.690000
    """
    parser = argparse.ArgumentParser(
        description="複数の株式シンボルに対してバッチ分析を実行し、CSV形式で結果を出力します",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  %(prog)s AAPL GOOGL MSFT TSLA
  %(prog)s --output results.csv --verbose AAPL GOOGL 7203.T
  %(prog)s --include-errors --verbose INVALID_SYMBOL AAPL

注意事項:
  - バックエンドサーバーが http://localhost:8000 で起動している必要があります
  - 起動方法: cd backend && ./start-dev.sh
        """
    )
    
    parser.add_argument(
        'symbols',
        nargs='+',
        help='分析対象の株式シンボル（例: AAPL GOOGL MSFT 7203.T）'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        help='出力CSVファイルパス（指定しない場合は標準出力）'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='詳細な実行ログを表示'
    )
    
    parser.add_argument(
        '--include-errors',
        action='store_true',
        help='エラーが発生したシンボルもCSVに含める'
    )
    
    parser.add_argument(
        '--timeout',
        type=float,
        default=60.0,
        help='HTTPリクエストのタイムアウト（秒、デフォルト: 60）'
    )
    
    parser.add_argument(
        '--max-retries',
        type=int,
        default=3,
        help='最大リトライ回数（デフォルト: 3）'
    )
    
    parser.add_argument(
        '--concurrent-limit',
        type=int,
        default=10,
        help='同時リクエスト数の制限（デフォルト: 10）'
    )
    
    parser.add_argument(
        '--base-url',
        type=str,
        default='http://localhost:8000',
        help='バックエンドAPIのベースURL（デフォルト: http://localhost:8000）'
    )
    
    args = parser.parse_args()
    
    # 重複シンボルの除去と正規化
    unique_symbols = list(dict.fromkeys([s.strip().upper() for s in args.symbols]))
    
    if args.verbose:
        print("=" * 60)
        print("🔬 TrendScope バッチ株式分析スクリプト")
        print("=" * 60)
        print(f"対象シンボル: {', '.join(unique_symbols)}")
        print(f"バックエンドURL: {args.base_url}")
        print("=" * 60)
        print()
    
    try:
        # バッチ分析インスタンス作成
        batch = StockAnalysisBatch(
            base_url=args.base_url,
            timeout=args.timeout,
            max_retries=args.max_retries,
            concurrent_limit=args.concurrent_limit
        )
        
        # 分析実行
        results = await batch.analyze_symbols(unique_symbols, verbose=args.verbose)
        
        # CSV出力
        batch.output_csv(
            results,
            output_file=args.output,
            include_errors=args.include_errors,
            verbose=args.verbose
        )
        
        # 成功/失敗の統計をエラー出力に表示（標準出力がCSVの場合の配慮）
        if not args.output and args.verbose:
            successful = sum(1 for r in results if r["status"] == "success")
            failed = len(results) - successful
            print(f"\n処理完了: 成功 {successful}件, 失敗 {failed}件", file=sys.stderr)
    
    except KeyboardInterrupt:
        if args.verbose:
            print("\n⏹️  処理が中断されました", file=sys.stderr)
        sys.exit(1)
    
    except Exception as e:
        print(f"❌ 予期しないエラー: {str(e)}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # Python 3.7+ のasyncio.run()を使用
    asyncio.run(main())