import json
import uuid

from pyJianYingDraft import (
    CropSettings,
    FilterType,
    ScriptFile,
    SmartColorAdjust,
    Timerange,
    TrackType,
    VideoMaterial,
    VideoSceneEffectType,
    VideoSegment,
)


def _fake_video_material(name: str = "video.mp4", *, duration: int = 20_000_000) -> VideoMaterial:
    material = VideoMaterial.__new__(VideoMaterial)
    material.material_id = uuid.uuid4().hex
    material.local_material_id = ""
    material.material_name = name
    material.path = f"/tmp/{name}"
    material.duration = duration
    material.height = 1080
    material.width = 1920
    material.crop_settings = CropSettings()
    material.material_type = "video"
    return material


def _dump(script: ScriptFile):
    return json.loads(script.dumps())


def _segment_by_type(draft_json: dict, track_type: str):
    return next(track["segments"][0] for track in draft_json["tracks"] if track["type"] == track_type)


def test_segment_level_smart_color_adjust_exports_effect_and_segment_refs():
    script = ScriptFile(1920, 1080, 30, True)
    script.add_track(TrackType.video)

    segment = VideoSegment(_fake_video_material(), Timerange(0, 8_133_333))
    segment.add_smart_color_adjust(80)
    script.add_segment(segment)

    draft_json = _dump(script)
    smart_effect = next(effect for effect in draft_json["materials"]["effects"] if effect["type"] == "smart_color_adjust")
    video_segment = _segment_by_type(draft_json, "video")

    assert smart_effect["name"] == SmartColorAdjust.DEFAULT_NAME
    assert smart_effect["effect_id"] == SmartColorAdjust.DEFAULT_EFFECT_ID
    assert smart_effect["resource_id"] == SmartColorAdjust.DEFAULT_RESOURCE_ID
    assert smart_effect["value"] == 0.8
    assert video_segment["enable_smart_color_adjust"] is True
    assert smart_effect["id"] in video_segment["extra_material_refs"]


def test_plain_video_segment_keeps_default_smart_color_adjust_behavior():
    script = ScriptFile(1920, 1080, 30, True)
    script.add_track(TrackType.video)

    segment = VideoSegment(_fake_video_material(), Timerange(0, 8_133_333))
    script.add_segment(segment)

    draft_json = _dump(script)
    video_segment = _segment_by_type(draft_json, "video")

    assert not any(effect["type"] == "smart_color_adjust" for effect in draft_json["materials"]["effects"])
    assert video_segment["enable_smart_color_adjust"] is False
    assert len(video_segment["extra_material_refs"]) == 1


def test_segment_level_smart_color_adjust_coexists_with_filter_and_video_effect():
    script = ScriptFile(1920, 1080, 30, True)
    script.add_track(TrackType.video)

    segment = VideoSegment(_fake_video_material(), Timerange(0, 8_133_333))
    segment.add_smart_color_adjust(37.64523237179487)
    segment.add_filter(FilterType.原生肤, 10)
    segment.add_effect(VideoSceneEffectType.胶片闪切, [50, None, 80])
    script.add_segment(segment)

    draft_json = _dump(script)
    effect_types = [effect["type"] for effect in draft_json["materials"]["effects"]]
    video_effect_types = [effect["type"] for effect in draft_json["materials"]["video_effects"]]

    assert "smart_color_adjust" in effect_types
    assert "filter" in effect_types
    assert "video_effect" in video_effect_types


def test_track_level_smart_color_adjust_exports_placeholder_adjust_track_and_refs():
    script = ScriptFile(1920, 1080, 30, True)
    script.add_track(TrackType.video)

    normal_segment = VideoSegment(_fake_video_material("plain.mp4"), Timerange(0, 5_000_000))
    script.add_segment(normal_segment)
    script.add_smart_color_adjust(28.35536858974359, Timerange(0, 16_066_666))

    draft_json = _dump(script)

    placeholder = draft_json["materials"]["placeholders"][0]
    smart_effect = next(effect for effect in draft_json["materials"]["effects"] if effect["type"] == "smart_color_adjust")
    adjust_track = next(track for track in draft_json["tracks"] if track["type"] == "adjust")
    adjust_segment = adjust_track["segments"][0]
    video_track = next(track for track in draft_json["tracks"] if track["type"] == "video")
    video_segment = video_track["segments"][0]

    assert placeholder["type"] == "adjust"
    assert placeholder["name"] == "调节1"
    assert adjust_segment["material_id"] == placeholder["id"]
    assert adjust_segment["enable_smart_color_adjust"] is True
    assert adjust_segment["extra_material_refs"] == [smart_effect["id"]]
    assert adjust_segment["target_timerange"] == {"duration": 16_066_666, "start": 0}
    assert adjust_segment["clip"] is None
    assert adjust_segment["uniform_scale"] is None
    assert adjust_segment["hdr_settings"] is None
    assert video_track["type"] == "video"
    assert video_segment["material_id"] == normal_segment.material_id
    assert len(video_segment["extra_material_refs"]) == 1
