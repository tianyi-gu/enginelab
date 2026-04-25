"""Tests for the drag-and-drop chess board Streamlit component."""

from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_dnd_component_uses_streamlit_component_value_channel() -> None:
    component = ROOT / "ui" / "components" / "chess_dnd" / "index.html"
    source = component.read_text()

    assert 'type: "streamlit:componentReady"' in source
    assert 'type: "streamlit:setComponentValue"' in source
    assert 'type !== "streamlit:render"' in source
    assert "window.parent.location" not in source
    assert "window.top.location" not in source


def test_chess_play_dnd_returns_component_move_value() -> None:
    module = ast.parse((ROOT / "ui" / "chess_viewer.py").read_text())
    functions = {
        node.name: node
        for node in module.body
        if isinstance(node, ast.FunctionDef)
    }
    function = functions["chess_play_dnd"]

    assert ast.unparse(function.returns) == "str | None"
    source = ast.get_source_segment(
        (ROOT / "ui" / "chess_viewer.py").read_text(),
        function,
    )
    assert "_chess_dnd_component(" in source
    assert "return move if isinstance(move, str) else None" in source


def test_play_board_handles_returned_drop_before_fallback_query_params() -> None:
    source = (ROOT / "ui" / "app.py").read_text()

    assert "dropped_move = chess_play_dnd(" in source
    assert "if dropped_move:" in source
    assert "_handle_player_move(dropped_move, variant, depth)" in source
