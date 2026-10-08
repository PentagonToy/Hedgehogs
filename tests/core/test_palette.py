import json

import pytest

import hedgehogs as hdg


def test_build_color_map_preserves_first_unique_label_order():
    mapping = hdg.build_color_map(["alpha", "alpha", "beta"])
    palette = hdg.get_palette()
    assert mapping == {"alpha": palette[0], "beta": palette[1]}


def test_build_style_map_uses_more_than_colour():
    mapping = hdg.build_style_map([f"case-{index}" for index in range(10)])
    assert mapping["case-0"]["linestyle"] != mapping["case-1"]["linestyle"]
    assert mapping["case-0"]["marker"] != mapping["case-1"]["marker"]
    assert mapping["case-0"]["color"] == mapping["case-8"]["color"]
    assert mapping["case-0"] != mapping["case-8"]
    assert set(mapping["case-0"]) == {"color", "linestyle", "marker"}


@pytest.mark.parametrize("value", [0, -1, 1.5, True])
def test_palette_size_must_be_a_positive_integer(value):
    with pytest.raises(ValueError, match="positive integer"):
        hdg.get_palette(n=value)


def test_custom_palette_round_trip(tmp_path):
    hdg.register_palette(
        "laboratory",
        {"cold": "#123456", "hot": "#abcdef"},
        overwrite=True,
    )
    path = hdg.save_palette("laboratory", tmp_path / "palette.json")
    assert json.loads(path.read_text())["name"] == "laboratory"

    restored = hdg.load_palette(
        path,
        name="laboratory-copy",
        overwrite=True,
    )
    assert restored["cold"] == "#123456"
    assert restored["hot"] == "#abcdef"
