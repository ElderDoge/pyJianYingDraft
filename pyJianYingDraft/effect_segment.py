"""定义特效/滤镜/调节片段类"""

import uuid

from typing import Dict, Any
from typing import Union, Optional, List

from .time_util import Timerange
from .segment import BaseSegment
from .video_segment import VideoEffect, Filter, SmartColorAdjust

from .metadata import VideoSceneEffectType, VideoCharacterEffectType, FilterType

class EffectSegment(BaseSegment):
    """放置在独立特效轨道上的特效片段"""

    effect_inst: VideoEffect
    """相应的特效素材

    在放入轨道时自动添加到素材列表中
    """

    def __init__(self, effect_type: Union[VideoSceneEffectType, VideoCharacterEffectType],
                 target_timerange: Timerange, params: Optional[List[Optional[float]]] = None):
        self.effect_inst = VideoEffect(effect_type, params, apply_target_type=2)  # 作用域为全局
        super().__init__(self.effect_inst.global_id, target_timerange)

class FilterSegment(BaseSegment):
    """放置在独立滤镜轨道上的滤镜片段"""

    material: Filter
    """相应的滤镜素材

    在放入轨道时自动添加到素材列表中
    """

    def __init__(self, meta: FilterType, target_timerange: Timerange, intensity: float):
        self.material = Filter(meta.value, intensity)
        super().__init__(self.material.global_id, target_timerange)

class AdjustPlaceholder:
    """调节轨占位素材"""

    placeholder_id: str
    name: str

    def __init__(self, name: str):
        self.placeholder_id = uuid.uuid4().hex
        self.name = name

    def export_json(self) -> Dict[str, Any]:
        return {
            "id": self.placeholder_id,
            "material_resource_id": "",
            "name": self.name,
            "type": "adjust",
        }

class AdjustSegment(BaseSegment):
    """放置在调节轨上的智能调色片段"""

    placeholder: AdjustPlaceholder
    smart_color_adjust: SmartColorAdjust
    extra_material_refs: List[str]

    def __init__(self, placeholder: AdjustPlaceholder, smart_color_adjust: SmartColorAdjust, target_timerange: Timerange):
        self.placeholder = placeholder
        self.smart_color_adjust = smart_color_adjust
        self.extra_material_refs = [smart_color_adjust.global_id]
        super().__init__(placeholder.placeholder_id, target_timerange)

    def export_json(self) -> Dict[str, Any]:
        json_dict = super().export_json()
        json_dict.update({
            "caption_info": None,
            "cartoon": False,
            "clip": None,
            "enable_smart_color_adjust": True,
            "extra_material_refs": self.extra_material_refs,
            "group_id": "",
            "hdr_settings": None,
            "intensifies_audio": False,
            "is_placeholder": False,
            "is_tone_modify": False,
            "responsive_layout": {
                "enable": False,
                "horizontal_pos_layout": 0,
                "size_layout": 0,
                "target_follow": "",
                "vertical_pos_layout": 0,
            },
            "source_timerange": None,
            "speed": 1.0,
            "template_id": "",
            "template_scene": "default",
            "track_render_index": 1,
            "uniform_scale": None,
            "volume": 1.0,
        })
        return json_dict
