"""Convert generated Chinese text to the Traditional variant the user selected.

LLMs often answer in Simplified Chinese even when asked for zh-TW or zh-HK.
Running the text through OpenCC makes the script, TTS input, subtitles and
social captions consistently use the requested variant.
"""
from functools import lru_cache

from loguru import logger

# Language code (lower case) -> OpenCC conversion profile.
# s2twp also maps mainland vocabulary to Taiwan usage (e.g. 软件 -> 軟體).
_TRADITIONAL_PROFILES = {
    "zh-tw": "s2twp",
    "zh-hant-tw": "s2twp",
    "zh-hk": "s2hk",
    "zh-hant-hk": "s2hk",
    "zh-hant": "s2t",
}


def traditional_profile(language) -> str:
    """Return the OpenCC profile for a Traditional Chinese language code, or ""."""
    value = str(language or "").strip().lower().replace("_", "-")
    return _TRADITIONAL_PROFILES.get(value, "")


@lru_cache(maxsize=None)
def _converter(profile: str):
    from opencc import OpenCC

    return OpenCC(profile)


def to_language_variant(text, language):
    """Convert text to Traditional Chinese when language asks for it.

    Text for any other language is returned unchanged. A missing OpenCC
    install degrades to the unconverted text instead of failing the task.
    """
    profile = traditional_profile(language)
    if not profile or not isinstance(text, str) or not text:
        return text
    try:
        return _converter(profile).convert(text)
    except Exception as e:
        logger.warning(f"failed to convert text to {language}: {e}")
        return text
