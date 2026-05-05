from pyJianYingDraft.segment import BaseSegment
from pyJianYingDraft.time_util import Timerange


def test_base_segment_exports_visible_true_by_default():
    segment = BaseSegment("material-id", Timerange(0, 1_000_000))

    assert segment.export_json()["visible"] is True


def test_base_segment_exports_visible_false_when_set():
    segment = BaseSegment("material-id", Timerange(0, 1_000_000))
    segment.visible = False

    assert segment.export_json()["visible"] is False
