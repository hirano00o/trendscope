"""非同期翻訳機能のテスト

TranslationServiceの非同期機能をテストする
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from stock_batch.services.translation import TranslationService


class TestAsyncTranslation:
    """非同期翻訳機能のテストクラス"""

    @pytest.fixture
    def translation_service(self):
        """テスト用TranslationService"""
        return TranslationService(max_retries=2, retry_delay=0.1)

    @pytest.fixture
    def mock_company(self):
        """テスト用企業データ"""
        company = MagicMock()
        company.symbol = "1332.T"
        company.business_summary = "Test business summary in English"
        return company

    @pytest.fixture
    def mock_companies(self):
        """テスト用企業データリスト"""
        companies = []
        summaries = [
            "Technology company specializing in software",
            "Manufacturing company with global presence", 
            "Financial services provider",
            "Retail chain with multiple locations",
            "Healthcare solutions company",
        ]
        for i, summary in enumerate(summaries):
            company = MagicMock()
            company.symbol = f"{1332 + i}.T"
            company.business_summary = summary
            companies.append(company)
        return companies

    @pytest.mark.asyncio
    async def test_translate_to_japanese_async_success(
        self, translation_service, mock_company
    ):
        """非同期翻訳成功テスト"""
        # googletransのモック
        mock_translator = AsyncMock()
        mock_result = MagicMock()
        mock_result.text = "テスト用ビジネス要約"
        mock_translator.translate.return_value = mock_result

        with patch("stock_batch.services.translation.Translator") as mock_translator_class:
            mock_translator_class.return_value.__aenter__.return_value = mock_translator

            translated_text = await translation_service.translate_to_japanese_async(
                mock_company.business_summary
            )

        # 結果検証
        assert translated_text == "テスト用ビジネス要約"

    @pytest.mark.asyncio
    async def test_translate_to_japanese_async_error_handling(
        self, translation_service, mock_company
    ):
        """非同期翻訳エラーハンドリングテスト"""
        # googletransでエラーが発生するモック
        mock_translator = AsyncMock()
        mock_translator.translate.side_effect = Exception("Translation error")

        with patch("stock_batch.services.translation.Translator") as mock_translator_class:
            mock_translator_class.return_value.__aenter__.return_value = mock_translator

            # エラー時は元のテキストが返されること
            translated_text = await translation_service.translate_to_japanese_async(
                mock_company.business_summary
            )
            assert translated_text == mock_company.business_summary

    @pytest.mark.asyncio
    async def test_translate_to_japanese_async_retry_mechanism(
        self, translation_service, mock_company
    ):
        """非同期翻訳リトライメカニズムテスト"""
        call_count = 0

        async def mock_translate_with_retry(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("Temporary translation error")
            
            # 2回目は成功
            mock_result = MagicMock()
            mock_result.text = "リトライ後の翻訳結果"
            return mock_result

        mock_translator = AsyncMock()
        mock_translator.translate.side_effect = mock_translate_with_retry

        with patch("stock_batch.services.translation.Translator") as mock_translator_class:
            mock_translator_class.return_value.__aenter__.return_value = mock_translator

            translated_text = await translation_service.translate_to_japanese_async(
                mock_company.business_summary
            )

        # リトライ後に成功すること
        assert translated_text == "リトライ後の翻訳結果"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_translate_multiple_texts_async_success(
        self, translation_service, mock_companies
    ):
        """複数テキスト非同期翻訳成功テスト"""
        # googletransのモック
        def create_mock_translate(text, **kwargs):
            # 英語テキストから日本語に翻訳するモック
            translations = {
                "Technology company specializing in software": "ソフトウェア専門技術会社",
                "Manufacturing company with global presence": "グローバル展開製造会社",
                "Financial services provider": "金融サービス提供会社",
                "Retail chain with multiple locations": "多店舗展開小売チェーン",
                "Healthcare solutions company": "ヘルスケアソリューション会社",
            }
            mock_result = MagicMock()
            mock_result.text = translations.get(text, f"翻訳済み: {text}")
            return mock_result

        mock_translator = AsyncMock()
        mock_translator.translate.side_effect = create_mock_translate

        with patch("stock_batch.services.translation.Translator") as mock_translator_class:
            mock_translator_class.return_value.__aenter__.return_value = mock_translator

            texts = [company.business_summary for company in mock_companies]
            translated_texts = await translation_service.translate_multiple_texts_async(texts)

        # 結果検証
        assert len(translated_texts) == 5
        assert translated_texts[0] == "ソフトウェア専門技術会社"
        assert translated_texts[1] == "グローバル展開製造会社"

    @pytest.mark.asyncio
    async def test_translate_multiple_texts_async_with_errors(self, translation_service):
        """複数テキスト非同期翻訳（一部エラー）テスト"""
        def create_mock_translate_with_errors(text, **kwargs):
            if "error" in text.lower():
                raise Exception("Translation error")
            
            mock_result = MagicMock()
            mock_result.text = f"翻訳済み: {text}"
            return mock_result

        mock_translator = AsyncMock()
        mock_translator.translate.side_effect = create_mock_translate_with_errors

        texts = ["Good text", "Error text", "Another good text"]
        
        with patch("stock_batch.services.translation.Translator") as mock_translator_class:
            mock_translator_class.return_value.__aenter__.return_value = mock_translator

            translated_texts = await translation_service.translate_multiple_texts_async(texts)

        # エラーのテキストは元のまま、成功分は翻訳されること
        assert len(translated_texts) == 3
        assert translated_texts[0] == "翻訳済み: Good text"
        assert translated_texts[1] == "Error text"  # エラー時は元のテキスト
        assert translated_texts[2] == "翻訳済み: Another good text"

    @pytest.mark.asyncio
    async def test_translate_with_rate_limit_async(self, translation_service, mock_companies):
        """レート制限付き翻訳テスト"""
        # モック設定
        def create_mock_translate(text, **kwargs):
            mock_result = MagicMock()
            mock_result.text = f"翻訳済み: {text}"
            return mock_result

        mock_translator = AsyncMock()
        mock_translator.translate.side_effect = create_mock_translate

        with patch("stock_batch.services.translation.Translator") as mock_translator_class:
            mock_translator_class.return_value.__aenter__.return_value = mock_translator

            texts = [company.business_summary for company in mock_companies[:3]]
            translated_texts = await translation_service.translate_multiple_texts_async(
                texts, max_concurrent=2  # 並行数制限
            )

        # 結果検証
        assert len(translated_texts) == 3
        assert all(text.startswith("翻訳済み:") for text in translated_texts)

    @pytest.mark.asyncio
    async def test_concurrent_translation(self, translation_service):
        """並行翻訳テスト"""
        texts = ["Text 1", "Text 2", "Text 3"]
        
        # モック設定
        def create_mock_translate(text, **kwargs):
            mock_result = MagicMock()
            mock_result.text = f"翻訳済み: {text}"
            return mock_result

        mock_translator = AsyncMock()
        mock_translator.translate.side_effect = create_mock_translate

        with patch("stock_batch.services.translation.Translator") as mock_translator_class:
            mock_translator_class.return_value.__aenter__.return_value = mock_translator

            # 並行実行
            tasks = [
                translation_service.translate_to_japanese_async(text)
                for text in texts
            ]
            results = await asyncio.gather(*tasks)

        # 結果検証
        assert len(results) == 3
        assert all(result.startswith("翻訳済み:") for result in results)

    def test_validate_async_methods_exist(self, translation_service):
        """非同期メソッドの存在確認テスト"""
        # 非同期メソッドが定義されていることを確認
        assert hasattr(translation_service, "translate_to_japanese_async")
        assert hasattr(translation_service, "translate_multiple_texts_async")
        
        # メソッドがコルーチン関数であることを確認
        import inspect
        assert inspect.iscoroutinefunction(translation_service.translate_to_japanese_async)
        assert inspect.iscoroutinefunction(translation_service.translate_multiple_texts_async)

    @pytest.mark.asyncio
    async def test_async_stats_tracking(self, translation_service, mock_company):
        """非同期処理の統計追跡テスト"""
        # 初期状態の統計確認
        initial_stats = translation_service.get_stats()
        assert initial_stats["total_requests"] == 0

        # モック設定
        mock_translator = AsyncMock()
        mock_result = MagicMock()
        mock_result.text = "翻訳済みテキスト"
        mock_translator.translate.return_value = mock_result

        with patch("stock_batch.services.translation.Translator") as mock_translator_class:
            mock_translator_class.return_value.__aenter__.return_value = mock_translator

            await translation_service.translate_to_japanese_async(
                mock_company.business_summary
            )

        # 統計が更新されていることを確認
        final_stats = translation_service.get_stats()
        assert final_stats["total_requests"] > initial_stats["total_requests"]
        assert final_stats["successful_translations"] > 0

    @pytest.mark.asyncio
    async def test_empty_text_handling_async(self, translation_service):
        """空テキスト処理テスト"""
        # 空文字列の場合
        result = await translation_service.translate_to_japanese_async("")
        assert result == ""

        # Noneの場合
        result = await translation_service.translate_to_japanese_async(None)
        assert result == ""

        # 空白のみの場合
        result = await translation_service.translate_to_japanese_async("   ")
        assert result == ""

    @pytest.mark.asyncio
    async def test_translate_companies_async(self, translation_service, mock_companies):
        """企業リスト翻訳テスト"""
        # モック設定
        def create_mock_translate(text, **kwargs):
            mock_result = MagicMock()
            mock_result.text = f"翻訳済み企業: {text[:20]}..."
            return mock_result

        mock_translator = AsyncMock()
        mock_translator.translate.side_effect = create_mock_translate

        with patch("stock_batch.services.translation.Translator") as mock_translator_class:
            mock_translator_class.return_value.__aenter__.return_value = mock_translator

            # 企業リストの翻訳
            translated_companies = await translation_service.translate_companies_async(
                mock_companies
            )

        # 結果検証
        assert len(translated_companies) == 5
        for company in translated_companies:
            assert company.business_summary.startswith("翻訳済み企業:")