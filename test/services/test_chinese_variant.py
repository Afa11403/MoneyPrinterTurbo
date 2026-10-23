"""选择繁体中文时，文案、自定义文案与发布文案都必须输出繁体。"""

import json
from unittest.mock import patch

import pytest

from app.models.schema import VideoParams
from app.services import llm
from app.services import task as tm
from app.utils.chinese_variant import to_language_variant, traditional_profile


@pytest.mark.parametrize(
    ("language", "profile"),
    [
        ("zh-TW", "s2twp"),
        ("zh_tw", "s2twp"),
        (" zh-HK ", "s2hk"),
        ("zh-Hant", "s2t"),
        ("zh-CN", ""),
        ("en-US", ""),
        ("", ""),
        (None, ""),
    ],
)
def test_traditional_profile(language, profile):
    assert traditional_profile(language) == profile


def test_taiwan_conversion_uses_taiwan_vocabulary():
    assert to_language_variant("软件里的信息", "zh-TW") == "軟體裡的資訊"


def test_other_languages_and_empty_text_are_unchanged():
    assert to_language_variant("胡椒来自富国岛", "zh-CN") == "胡椒来自富国岛"
    assert to_language_variant("Pepper", "en-US") == "Pepper"
    assert to_language_variant("", "zh-TW") == ""
    assert to_language_variant(None, "zh-TW") is None


def test_conversion_failure_returns_original_text():
    with patch("app.utils.chinese_variant._converter", side_effect=ImportError("x")):
        assert to_language_variant("胡椒", "zh-TW") == "胡椒"


def test_generated_script_is_converted_to_traditional():
    with patch.object(llm, "_generate_response", return_value="这款胡椒来自越南富国岛。") as provider:
        script = llm.generate_script("越南胡椒", language="zh-TW")
    assert script == "這款胡椒來自越南富國島。"
    assert "Traditional Chinese" in provider.call_args.kwargs["prompt"]


def test_simplified_script_language_is_not_converted():
    with patch.object(llm, "_generate_response", return_value="这款胡椒来自越南。") as provider:
        assert llm.generate_script("越南胡椒", language="zh-CN") == "这款胡椒来自越南。"
    assert "Traditional Chinese" not in provider.call_args.kwargs["prompt"]


def test_social_metadata_is_converted_to_traditional():
    response = json.dumps(
        {"title": "越南胡椒", "caption": "来自富国岛的胡椒", "hashtags": ["#胡椒", "#越南"]},
        ensure_ascii=False,
    )
    with patch.object(llm, "_generate_response", return_value=response):
        metadata = llm.generate_social_metadata("越南胡椒", language="zh-TW")
    assert metadata["caption"] == "來自富國島的胡椒"
    assert metadata["hashtags"] == ["#胡椒", "#越南"]


def test_social_metadata_fallback_is_converted_to_traditional():
    with patch.object(llm, "_generate_response", return_value="Error: offline"):
        metadata = llm.generate_social_metadata("越南胡椒", "来自富国岛", language="zh-TW")
    assert metadata["caption"] == "來自富國島"


def test_custom_task_script_is_converted_to_traditional():
    params = VideoParams(
        video_subject="越南胡椒", video_script="来自富国岛的胡椒", video_language="zh-TW"
    )
    with patch.object(tm.llm, "generate_script") as generate:
        assert tm.generate_script("task-id", params) == "來自富國島的胡椒"
    generate.assert_not_called()
