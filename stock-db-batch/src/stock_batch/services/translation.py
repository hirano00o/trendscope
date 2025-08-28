"""Google翻訳サービス

googletransライブラリを使用した英語から日本語への翻訳機能を提供
"""

from __future__ import annotations

import logging
import time
from typing import Any

import googletrans

logger = logging.getLogger(__name__)


class TranslationService:
    """Google翻訳サービスクラス

    googletransライブラリを使用して英語テキストを日本語に翻訳する。
    エラーハンドリング、リトライ機能、統計情報収集を含む。

    Attributes:
        max_retries: 最大リトライ回数
        retry_delay: リトライ間隔（秒）
        _stats: 翻訳統計情報

    Example:
        >>> service = TranslationService()
        >>> japanese_text = service.translate_to_japanese("Hello, world!")
        >>> print(japanese_text)
        "こんにちは世界！"
    """

    # サポートされる言語コード
    SUPPORTED_LANGUAGES = {
        "en": "English",
        "ja": "Japanese",
        "zh": "Chinese",
        "ko": "Korean",
        "es": "Spanish",
        "fr": "French",
        "de": "German",
        "it": "Italian",
        "pt": "Portuguese",
        "ru": "Russian",
    }

    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0) -> None:
        """TranslationService を初期化する

        Args:
            max_retries: 最大リトライ回数（デフォルト: 3）
            retry_delay: リトライ間隔秒数（デフォルト: 1.0）

        Example:
            >>> service = TranslationService(max_retries=5, retry_delay=2.0)
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._stats = {
            "total_requests": 0,
            "successful_translations": 0,
            "failed_translations": 0,
            "total_response_time": 0.0,
        }

    def translate_to_japanese(self, text: str | None) -> str:
        """英語テキストを日本語に翻訳する

        googletrans を使用してテキストを英語から日本語に翻訳する。
        ネットワークエラーや翻訳失敗の場合はリトライを実行。

        Args:
            text: 翻訳する英語テキスト

        Returns:
            日本語翻訳テキスト。翻訳失敗時は元のテキストを返す。

        Example:
            >>> service = TranslationService()
            >>> result = service.translate_to_japanese("Hello, world!")
            >>> print(result)
            "こんにちは世界！"
        """
        if not text or not text.strip():
            return ""

        start_time = time.time()
        self._stats["total_requests"] += 1

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.debug(
                    "翻訳開始: %s文字 (試行 %d/%d)",
                    len(text),
                    attempt,
                    self.max_retries,
                )

                # Google翻訳API呼び出し
                translator = googletrans.Translator()
                result = translator.translate(text, dest="ja", src="en")

                # 翻訳結果取得
                translated_text = result.text or text

                # 統計情報更新
                response_time = time.time() - start_time
                self._record_success(response_time)

                logger.debug(
                    "翻訳成功: %s → %s (%.2f秒)",
                    text[:50] + "..." if len(text) > 50 else text,
                    (
                        translated_text[:50] + "..."
                        if len(translated_text) > 50
                        else translated_text
                    ),
                    response_time,
                )
                return translated_text

            except Exception as e:
                logger.warning(
                    "翻訳エラー: %s... (試行 %d/%d) - %s",
                    text[:30] + "..." if len(text) > 30 else text,
                    attempt,
                    self.max_retries,
                    e,
                )

                if attempt < self.max_retries:
                    logger.debug("リトライまで %s秒待機", self.retry_delay)
                    time.sleep(self.retry_delay)
                else:
                    logger.error(
                        "翻訳失敗（リトライ上限到達）: %s...",
                        text[:30] + "..." if len(text) > 30 else text,
                    )

        # 翻訳失敗時は元のテキストを返す
        self._record_failure()
        return text

    def translate_multiple_texts(self, texts: list[str]) -> list[str]:
        """複数のテキストを日本語に翻訳する

        並列処理は行わず、順次翻訳してレート制限を回避する。

        Args:
            texts: 翻訳する英語テキストのリスト

        Returns:
            日本語翻訳テキストのリスト

        Example:
            >>> service = TranslationService()
            >>> texts = ["Hello", "World", "Python"]
            >>> results = service.translate_multiple_texts(texts)
            >>> print(results)
            ["こんにちは", "世界", "パイソン"]
        """
        if not texts:
            return []

        logger.info("複数テキスト翻訳開始: %d件", len(texts))
        start_time = time.time()

        translated_texts = []
        successful_count = 0

        for i, text in enumerate(texts, 1):
            logger.debug("進捗: %d/%d", i, len(texts))

            translated_text = self.translate_to_japanese(text)
            translated_texts.append(translated_text)

            # 翻訳に成功した場合（元のテキストと異なる場合）
            if translated_text != text:
                successful_count += 1

            # レート制限対策：短時間の待機
            if i < len(texts):  # 最後以外
                time.sleep(0.1)  # 100ms 待機

        elapsed_time = time.time() - start_time
        logger.info(
            "複数テキスト翻訳完了: %d/%d件成功 (%.2f秒)",
            successful_count,
            len(texts),
            elapsed_time,
        )

        return translated_texts

    def is_valid_language_code(self, code: str | None) -> bool:
        """言語コードの有効性を検証する

        Args:
            code: 検証する言語コード

        Returns:
            有効な言語コードの場合True、そうでなければFalse

        Example:
            >>> service = TranslationService()
            >>> service.is_valid_language_code("ja")
            True
            >>> service.is_valid_language_code("invalid")
            False
        """
        if not code or not isinstance(code, str):
            return False

        return code.lower() in self.SUPPORTED_LANGUAGES

    def get_stats(self) -> dict[str, Any]:
        """翻訳統計情報を返す

        デバッグやモニタリング用に統計情報を提供する。

        Returns:
            統計情報の辞書

        Example:
            >>> service = TranslationService()
            >>> # 何回か翻訳処理実行後
            >>> stats = service.get_stats()
            >>> print(f"成功率: {stats['success_rate']:.2%}")
        """
        total = self._stats["total_requests"]
        successful = self._stats["successful_translations"]

        success_rate = (successful / total) if total > 0 else 0.0
        avg_response_time = (
            (self._stats["total_response_time"] / successful) if successful > 0 else 0.0
        )

        return {
            "total_requests": total,
            "successful_translations": successful,
            "failed_translations": self._stats["failed_translations"],
            "success_rate": success_rate,
            "average_response_time": avg_response_time,
        }

    def _record_success(self, response_time: float) -> None:
        """成功統計を記録する

        Args:
            response_time: レスポンス時間（秒）
        """
        self._stats["successful_translations"] += 1
        self._stats["total_response_time"] += response_time

    def _record_failure(self) -> None:
        """失敗統計を記録する"""
        self._stats["failed_translations"] += 1
