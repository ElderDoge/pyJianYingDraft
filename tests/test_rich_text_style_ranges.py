import json

import pytest

from pyJianYingDraft import (
    ClipSettings,
    FontType,
    ScriptFile,
    TextBorder,
    TextSegment,
    TextShadow,
    TextStyle,
    TextStyleRange,
    Timerange,
    TrackType,
)
from pyJianYingDraft.text_segment import TextBubble


def _content(segment: TextSegment):
    return json.loads(segment.export_material()["content"])


def _script_text_content(script: ScriptFile, index: int = 0):
    return json.loads(script.materials.texts[index]["content"])


def test_exports_single_style_range_with_default_fill():
    segment = TextSegment(
        "重点普通",
        Timerange(0, 1000000),
        style=TextStyle(size=8.0, color=(1.0, 1.0, 1.0)),
    )
    segment.add_style_range(0, 2, style=TextStyle(size=12.0, color=(1.0, 0.0, 0.0), bold=True))

    styles = _content(segment)["styles"]

    assert [style["range"] for style in styles] == [[0, 2], [2, 4]]
    assert styles[0]["size"] == 12.0
    assert styles[0]["bold"] is True
    assert styles[0]["fill"]["content"]["solid"]["color"] == [1.0, 0.0, 0.0]
    assert styles[1]["size"] == 8.0
    assert styles[1]["fill"]["content"]["solid"]["color"] == [1.0, 1.0, 1.0]


def test_exports_multiple_style_ranges_and_default_gaps():
    segment = TextSegment("A重点B结尾", Timerange(0, 1000000), style=TextStyle(size=6.0))
    segment.add_style_range(1, 3, style=TextStyle(size=9.0, italic=True))
    segment.add_style_range(4, 6, style=TextStyle(size=11.0, underline=True))

    styles = _content(segment)["styles"]

    assert [style["range"] for style in styles] == [[0, 1], [1, 3], [3, 4], [4, 6]]
    assert styles[1]["italic"] is True
    assert styles[3]["underline"] is True
    assert styles[0]["size"] == 6.0
    assert styles[2]["size"] == 6.0


@pytest.mark.parametrize(
    "start,end",
    [
        (1, 1),
        (2, 1),
    ],
)
def test_rejects_empty_style_range(start, end):
    segment = TextSegment("测试", Timerange(0, 1000000))

    with pytest.raises(ValueError):
        segment.add_style_range(start, end, style=TextStyle(color=(1.0, 0.0, 0.0)))


@pytest.mark.parametrize(
    "start,end",
    [
        (-1, 1),
        (0, 3),
    ],
)
def test_rejects_out_of_bounds_style_range(start, end):
    segment = TextSegment("测试", Timerange(0, 1000000))

    with pytest.raises(ValueError):
        segment.add_style_range(start, end, style=TextStyle(color=(1.0, 0.0, 0.0)))


def test_rejects_overlapping_style_ranges():
    segment = TextSegment("重点普通", Timerange(0, 1000000))
    segment.add_style_range(0, 2, style=TextStyle(color=(1.0, 0.0, 0.0)))

    with pytest.raises(ValueError):
        segment.add_style_range(1, 3, style=TextStyle(color=(0.0, 1.0, 0.0)))


def test_exports_local_font_border_shadow_and_effect():
    segment = TextSegment("局部样式", Timerange(0, 1000000))
    segment.add_style_range(
        0,
        2,
        style=TextStyle(size=18.0, color=(0.2, 0.3, 0.4)),
        font=FontType.文轩体,
        border=TextBorder(alpha=0.8, color=(1.0, 0.0, 0.0), width=50.0),
        shadow=TextShadow(alpha=0.6, color=(0.0, 0.0, 1.0), diffuse=30.0, distance=6.0, angle=30.0),
        effect_id="effect-local-1",
    )

    styles = _content(segment)["styles"]

    assert styles[0]["font"]["id"] == FontType.文轩体.value.resource_id
    assert styles[0]["fill"]["content"]["solid"]["color"] == [0.2, 0.3, 0.4]
    assert styles[0]["size"] == 18.0
    assert styles[0]["strokes"][0]["content"]["solid"]["alpha"] == 0.8
    assert styles[0]["shadows"][0]["alpha"] == 0.6
    assert styles[0]["effectStyle"]["id"] == "effect-local-1"
    assert segment.style_ranges[0].effect.global_id in segment.extra_material_refs


def test_registers_local_effect_material_when_segment_is_added():
    script = ScriptFile(1080, 1920, 30, False)
    segment = TextSegment("局部花字", Timerange(0, 1000000))
    segment.add_style_range(0, 2, effect_id="effect-local-2")

    script.add_track(TrackType.text, "text")
    script.add_segment(segment, "text")

    assert [material.effect_id for material in script.materials.filters] == ["effect-local-2"]


def test_rejects_local_text_bubble():
    segment = TextSegment("气泡", Timerange(0, 1000000))

    with pytest.raises(ValueError):
        segment.add_style_range(0, 1, bubble=TextBubble("bubble-effect", "bubble-resource"))


def test_import_srt_applies_style_range_resolver(tmp_path):
    srt_path = tmp_path / "subtitle.srt"
    srt_path.write_text(
        "1\n00:00:00,000 --> 00:00:01,000\n重点字幕\n\n"
        "2\n00:00:01,000 --> 00:00:02,000\n普通字幕\n",
        encoding="utf-8",
    )
    script = ScriptFile(1080, 1920, 30, False)

    def resolver(text, index):
        if index == 0:
            return [TextStyleRange(0, 2, style=TextStyle(color=(1.0, 0.0, 0.0), bold=True))]
        return []

    script.import_srt(str(srt_path), "subtitle", style_ranges_resolver=resolver)

    first_styles = _script_text_content(script, 0)["styles"]
    second_styles = _script_text_content(script, 1)["styles"]

    assert [style["range"] for style in first_styles] == [[0, 2], [2, 4]]
    assert first_styles[0]["bold"] is True
    assert [style["range"] for style in second_styles] == [[0, 4]]


def test_import_srt_without_resolver_keeps_single_default_style(tmp_path):
    srt_path = tmp_path / "subtitle.srt"
    srt_path.write_text("1\n00:00:00,000 --> 00:00:01,000\n普通字幕\n", encoding="utf-8")
    script = ScriptFile(1080, 1920, 30, False)

    script.import_srt(str(srt_path), "subtitle", clip_settings=ClipSettings(transform_y=-0.8))

    styles = _script_text_content(script)["styles"]

    assert [style["range"] for style in styles] == [[0, 4]]


def test_exports_style_ranges_with_utf16_boundaries_for_emoji_positions():
    segment = TextSegment("A😋中🌈尾", Timerange(0, 1000000), style=TextStyle(size=6.0))
    segment.add_style_range(0, 2, style=TextStyle(size=9.0))
    segment.add_style_range(2, 4, style=TextStyle(size=11.0))

    styles = _content(segment)["styles"]

    assert [style["range"] for style in styles] == [[0, 3], [3, 6], [6, 7]]
    assert [style["size"] for style in styles] == [9.0, 11.0, 6.0]


def test_exports_full_emoji_grapheme_range_with_utf16_boundaries():
    segment = TextSegment("烦躁无聊😮‍💨", Timerange(0, 1000000), style=TextStyle(size=6.0))
    segment.add_style_range(0, len(segment.text), style=TextStyle(size=12.0, bold=True))

    styles = _content(segment)["styles"]

    assert [style["range"] for style in styles] == [[0, 9]]
    assert styles[0]["size"] == 12.0
    assert styles[0]["bold"] is True
