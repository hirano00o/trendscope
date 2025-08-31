"""Google翻訳サービスのテストコード

googletransライブラリを使用した英語から日本語への翻訳機能をテストします。
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from stock_batch.services.translation import TranslationService


class TestTranslationService:
    """TranslationService クラスのテスト"""

    def test_create_translation_service(self) -> None:
        """TranslationService 作成のテスト"""
        service = TranslationService()
        assert service is not None

    @pytest.mark.asyncio
    @patch("googletrans.Translator")
    async def test_translate_text_success(self, mock_translator_class: Mock) -> None:
        """英日翻訳成功のテスト"""
        # モックの設定 - 非同期コンテキストマネージャーとして使用
        mock_translator = AsyncMock()
        mock_translator_class.return_value.__aenter__ = AsyncMock(
            return_value=mock_translator
        )
        mock_translator_class.return_value.__aexit__ = AsyncMock(return_value=None)

        # 翻訳結果のモック
        mock_result = Mock()
        mock_result.text = "日水株式会社は日本の水産会社です。"
        mock_translator.translate.return_value = mock_result

        service = TranslationService()
        english_text = "Nissui Corporation is a Japanese fishery company."
        japanese_text = await service.translate_to_japanese(english_text)

        assert japanese_text is not None
        assert japanese_text == "日水株式会社は日本の水産会社です。"
        mock_translator.translate.assert_called_once_with(
            english_text, dest="ja", src="en"
        )

    @pytest.mark.asyncio
    @patch("googletrans.Translator")
    async def test_translate_text_empty_input(
        self, mock_translator_class: Mock
    ) -> None:
        """空文字列の翻訳テスト"""
        service = TranslationService()
        result = await service.translate_to_japanese("")

        assert result == ""
        # 空文字列の場合は翻訳APIを呼び出さない
        mock_translator_class.assert_not_called()

    @pytest.mark.asyncio
    @patch("googletrans.Translator")
    async def test_translate_text_none_input(self, mock_translator_class: Mock) -> None:
        """None入力の翻訳テスト"""
        service = TranslationService()
        result = await service.translate_to_japanese(None)

        assert result == ""
        # None入力の場合は翻訳APIを呼び出さない
        mock_translator_class.assert_not_called()

    @pytest.mark.asyncio
    @patch("googletrans.Translator")
    async def test_translate_text_network_error(
        self, mock_translator_class: Mock
    ) -> None:
        """ネットワークエラーのテスト"""
        # モックでネットワークエラーを発生させる
        mock_translator = AsyncMock()
        mock_translator_class.return_value.__aenter__ = AsyncMock(
            return_value=mock_translator
        )
        mock_translator_class.return_value.__aexit__ = AsyncMock(return_value=None)
        mock_translator.translate.side_effect = Exception("Network error")

        service = TranslationService()
        result = await service.translate_to_japanese("Test text")

        # エラーの場合は元の英語テキストを返す
        assert result == "Test text"

    @pytest.mark.asyncio
    @patch("googletrans.Translator")
    async def test_translate_multiple_texts_success(
        self, mock_translator_class: Mock
    ) -> None:
        """複数テキストの翻訳テスト"""
        # モックの設定 - 非同期コンテキストマネージャーとして使用
        mock_translator = AsyncMock()
        mock_translator_class.return_value.__aenter__ = AsyncMock(
            return_value=mock_translator
        )
        mock_translator_class.return_value.__aexit__ = AsyncMock(return_value=None)

        # 翻訳結果のモック
        def translate_side_effect(text, dest="ja", src="en"):
            mock_result = Mock()
            if "Nissui Corporation" in text:
                mock_result.text = "日水株式会社は日本の水産会社です。"
            elif "Sony Corporation" in text:
                mock_result.text = "ソニー株式会社は日本の電子機器会社です。"
            else:
                mock_result.text = f"翻訳結果: {text}"
            return mock_result

        mock_translator.translate.side_effect = translate_side_effect

        service = TranslationService()
        english_texts = [
            "Nissui Corporation is a Japanese fishery company.",
            "Sony Corporation is a Japanese electronics company.",
        ]
        japanese_texts = await service.translate_multiple_texts(english_texts)

        assert len(japanese_texts) == 2
        assert japanese_texts[0] == "日水株式会社は日本の水産会社です。"
        assert japanese_texts[1] == "ソニー株式会社は日本の電子機器会社です。"

    @pytest.mark.asyncio
    async def test_translate_multiple_texts_empty_list(self) -> None:
        """空リストの複数翻訳テスト"""
        service = TranslationService()
        result = await service.translate_multiple_texts([])

        assert result == []

    @patch("googletrans.Translator")
    def test_translate_multiple_texts_mixed_valid_invalid(
        self, mock_translator_class: Mock
    ) -> None:
        """有効/無効テキスト混合の複数翻訳テスト"""
        # モックの設定
        mock_translator = Mock()
        mock_translator_class.return_value = mock_translator

        def translate_side_effect(text, dest="ja", src="en"):
            if "error" in text.lower():
                raise Exception("Translation error")
            mock_result = Mock()
            mock_result.text = f"翻訳結果: {text}"
            return mock_result

        mock_translator.translate.side_effect = translate_side_effect

        service = TranslationService()
        english_texts = [
            "Valid text 1",
            "Error text",  # エラーが発生
            "Valid text 2",
        ]
        japanese_texts = await service.translate_multiple_texts(english_texts)

        assert len(japanese_texts) == 3
        assert japanese_texts[0] == "翻訳結果: Valid text 1"
        assert japanese_texts[1] == "Error text"  # エラー時は元テキスト
        assert japanese_texts[2] == "翻訳結果: Valid text 2"

    @patch("googletrans.Translator")
    def test_retry_mechanism(self, mock_translator_class: Mock) -> None:
        """リトライ機能のテスト"""
        # モックの設定
        mock_translator = Mock()
        mock_translator_class.return_value = mock_translator

        # 最初の2回は失敗、3回目で成功
        call_count = 0

        def translate_side_effect(text, dest="ja", src="en"):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise Exception("Temporary error")

            mock_result = Mock()
            mock_result.text = "翻訳成功"
            return mock_result

        mock_translator.translate.side_effect = translate_side_effect

        service = TranslationService(max_retries=3, retry_delay=0.1)
        result = service.translate_to_japanese("Test text")

        assert result == "翻訳成功"
        assert call_count == 3  # 3回目で成功

    @patch("googletrans.Translator")
    def test_retry_exhausted(self, mock_translator_class: Mock) -> None:
        """リトライ回数上限のテスト"""
        # モックの設定
        mock_translator = Mock()
        mock_translator_class.return_value = mock_translator
        mock_translator.translate.side_effect = Exception("Persistent error")

        service = TranslationService(max_retries=2, retry_delay=0.1)
        result = service.translate_to_japanese("Test text")

        # リトライ上限に達した場合は元のテキストを返す
        assert result == "Test text"

    def test_get_translation_stats(self) -> None:
        """翻訳統計情報取得のテスト"""
        service = TranslationService()

        stats = service.get_stats()

        assert "total_requests" in stats
        assert "successful_translations" in stats
        assert "failed_translations" in stats
        assert "average_response_time" in stats
        assert stats["total_requests"] == 0  # 初期値

    @patch("googletrans.Translator")
    def test_stats_tracking(self, mock_translator_class: Mock) -> None:
        """統計情報トラッキングのテスト"""
        # モックの設定
        mock_translator = Mock()
        mock_translator_class.return_value = mock_translator

        def translate_side_effect(text, dest="ja", src="en"):
            if "error" in text:
                raise Exception("Translation error")
            mock_result = Mock()
            mock_result.text = "翻訳成功"
            return mock_result

        mock_translator.translate.side_effect = translate_side_effect

        service = TranslationService()

        # 1回成功
        service.translate_to_japanese("Success text")

        # 1回失敗
        service.translate_to_japanese("error text")

        stats = service.get_stats()
        assert stats["total_requests"] == 2
        assert stats["successful_translations"] == 1
        assert stats["failed_translations"] == 1

    def test_validate_language_codes(self) -> None:
        """言語コード検証のテスト"""
        service = TranslationService()

        # 有効な言語コード
        assert service.is_valid_language_code("en") is True
        assert service.is_valid_language_code("ja") is True
        assert service.is_valid_language_code("zh") is True

        # 無効な言語コード
        assert service.is_valid_language_code("") is False
        assert service.is_valid_language_code("invalid") is False
        assert service.is_valid_language_code(None) is False

    @patch("googletrans.Translator")
    def test_long_text_handling(self, mock_translator_class: Mock) -> None:
        """長いテキストの処理テスト"""
        # モックの設定
        mock_translator = Mock()
        mock_translator_class.return_value = mock_translator

        mock_result = Mock()
        mock_result.text = "長いテキストの翻訳結果"
        mock_translator.translate.return_value = mock_result

        service = TranslationService()
        long_text = "A" * 5000  # 5000文字の長いテキスト

        result = service.translate_to_japanese(long_text)

        assert result == "長いテキストの翻訳結果"
        # APIが呼び出されたことを確認
        mock_translator.translate.assert_called_once()

    @patch("googletrans.Translator")
    def test_special_characters_handling(self, mock_translator_class: Mock) -> None:
        """特殊文字を含むテキストの処理テスト"""
        # モックの設定
        mock_translator = Mock()
        mock_translator_class.return_value = mock_translator

        mock_result = Mock()
        mock_result.text = "特殊文字の翻訳結果"
        mock_translator.translate.return_value = mock_result

        service = TranslationService()
        special_text = "Text with émojis 🚀 and spëcial châractèrs!"

        result = service.translate_to_japanese(special_text)

        assert result == "特殊文字の翻訳結果"
