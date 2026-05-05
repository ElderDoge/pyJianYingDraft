from pyJianYingDraft import TextSegment, TextStyle, Timerange


def _material(style: TextStyle):
    segment = TextSegment("固定文字框", Timerange(0, 1000000), style=style)
    return segment.export_material()


def test_default_text_style_exports_fixed_box_and_line_fields():
    material = _material(TextStyle())

    assert material["fixed_width"] == -1.0
    assert material["fixed_height"] == -1.0
    assert material["line_feed"] == 1
    assert material["line_max_width"] == 0.82
    assert material["force_apply_line_max_width"] is False


def test_horizontal_text_exports_fixed_width():
    material = _material(TextStyle(vertical=False, align=1, fixed_width=669.3977451324463))

    assert material["typesetting"] == 0
    assert material["alignment"] == 1
    assert material["fixed_width"] == 669.3977451324463
    assert material["fixed_height"] == -1.0


def test_vertical_text_exports_fixed_height_and_raw_alignment():
    material = _material(TextStyle(vertical=True, align=4, fixed_height=619.6528823997663))

    assert material["typesetting"] == 1
    assert material["alignment"] == 4
    assert material["fixed_width"] == -1.0
    assert material["fixed_height"] == 619.6528823997663


def test_exports_custom_line_fields():
    material = _material(
        TextStyle(
            line_feed=2,
            max_line_width=0.5,
            force_apply_line_max_width=True,
        )
    )

    assert material["line_feed"] == 2
    assert material["line_max_width"] == 0.5
    assert material["force_apply_line_max_width"] is True
