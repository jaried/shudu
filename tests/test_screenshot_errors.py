"""公开入口报告首错位置，并保留其他阶段的错误契约。"""

import numpy as np
import pytest
from test_screenshot_foreground import board_image, unreadable_image, write_image

from shudu.sudoku_screenshot import load_screenshot_game


def test_first_unreadable_cell_reports_one_based_location_and_original_cause(tmp_path, monkeypatch):
    import shudu.sudoku_screenshot as screenshot

    path = unreadable_image(tmp_path / "无法识别.png")
    cell = screenshot._read_cell
    seen = []

    def read_cell(image):
        seen.append(image)
        return cell(image)

    monkeypatch.setattr(screenshot, "_read_cell", read_cell)
    with pytest.raises(ValueError, match=r"^第3行第5列：正式大数字识别置信度不足：0\.\d+。请使用清晰截图重试。$") as raised:
        load_screenshot_game(path)
    assert isinstance(raised.value.__cause__, ValueError)
    assert str(raised.value.__cause__).startswith("正式大数字识别置信度不足：")
    assert len(seen) == 23


@pytest.mark.parametrize(
    "kind,reason", (("missing", "截图文件不存在"), ("corrupt", "无法读取截图"), ("no_board", "没有找到"), ("no_digits", "没有识别到正式大数字"))
)
def test_non_cell_errors_keep_their_original_owner(tmp_path, kind, reason):
    path = tmp_path / "输入.png"
    if kind == "corrupt":
        path.write_bytes(b"invalid image")
    elif kind == "no_board":
        write_image(path, np.full((1000, 1000, 3), 248, dtype=np.uint8))
    elif kind == "no_digits":
        write_image(path, board_image())
    with pytest.raises(ValueError, match=reason) as raised:
        load_screenshot_game(path)
    assert not str(raised.value).startswith("第")
    assert raised.value.__cause__ is None
