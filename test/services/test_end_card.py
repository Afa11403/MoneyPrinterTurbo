"""片尾卡：在视频最后几秒叠加 logo 与下单引导文字。"""

import os
from unittest.mock import patch

from PIL import Image

from app.models.schema import VideoParams
from app.services import video
from app.utils import utils

FONT_PATH = os.path.join(utils.font_dir(), "STHeitiMedium.ttc")


def _logo(tmp_path, name="logo.png"):
    path = tmp_path / name
    Image.new("RGBA", (800, 400), (200, 60, 30, 255)).save(path)
    return path


def test_nothing_to_render_returns_none():
    assert video.render_end_card_image(1080, 1920, "", "", FONT_PATH) is None


def test_text_only_card_is_full_frame_and_translucent():
    image = video.render_end_card_image(1080, 1920, "蝦皮搜尋 越香", "", FONT_PATH)
    assert image.size == (1080, 1920)
    assert image.getpixel((5, 5))[3] == 170
    # 文字画在画面中部，白色填充。
    middle = image.crop((0, 900, 1080, 1020))
    assert (255, 255, 255, 255) in middle.getdata()


def test_logo_is_scaled_and_centered(tmp_path):
    image = video.render_end_card_image(1080, 1920, "", str(_logo(tmp_path)), FONT_PATH)
    # 宽 800 的 logo 会缩到短边的 40%（432px），并水平居中。
    assert image.getpixel((540, 960))[:3] == (200, 60, 30)
    assert image.getpixel((540 - 220, 960))[:3] == (0, 0, 0)


def test_broken_logo_falls_back_to_text(tmp_path):
    broken = tmp_path / "broken.png"
    broken.write_bytes(b"not an image")
    image = video.render_end_card_image(1080, 1920, "LINE", str(broken), FONT_PATH)
    assert image is not None


def test_logo_outside_logo_directory_is_rejected(tmp_path):
    assert video.resolve_end_card_logo(str(_logo(tmp_path))) == ""
    assert video.resolve_end_card_logo("../../config.toml") == ""
    assert video.resolve_end_card_logo("") == ""


def test_logo_inside_logo_directory_is_resolved(tmp_path):
    with patch.object(video.utils, "logo_dir", return_value=str(tmp_path)):
        _logo(tmp_path, "brand.png")
        assert video.resolve_end_card_logo("brand.png") == os.path.realpath(
            tmp_path / "brand.png"
        )


def test_end_card_clip_covers_the_last_seconds():
    params = VideoParams(video_subject="x", end_card_text="LINE", end_card_duration=3)
    clip = video._build_end_card_clip(params, 108, 192, 10.0, "")
    assert clip.start == 7.0
    assert clip.duration == 3.0


def test_end_card_is_clamped_to_short_videos():
    params = VideoParams(video_subject="x", end_card_text="LINE", end_card_duration=5)
    clip = video._build_end_card_clip(params, 108, 192, 2.0, "")
    assert clip.start == 0
    assert clip.duration == 2.0


def test_end_card_disabled_by_default():
    params = VideoParams(video_subject="x")
    assert video._build_end_card_clip(params, 108, 192, 10.0, "") is None
