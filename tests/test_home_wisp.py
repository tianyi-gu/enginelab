"""Tests for the Streamlit landing-page Wisp background integration."""

from __future__ import annotations

import ast
import re
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _home_template() -> str:
    module = ast.parse((ROOT / "ui" / "home.py").read_text())
    for node in module.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "_HOME_TEMPLATE":
                    return ast.literal_eval(node.value)
    raise AssertionError("_HOME_TEMPLATE assignment was not found")


def _module_string_assignment(path: Path, name: str) -> str:
    module = ast.parse(path.read_text())
    for node in module.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    return ast.literal_eval(node.value)
    raise AssertionError(f"{name} assignment was not found")


def _css_block(template: str, selector: str) -> str:
    match = re.search(rf"{re.escape(selector)}\s*\{{(?P<body>.*?)\}}", template, re.S)
    assert match is not None, f"{selector} CSS block was not found"
    return match.group("body")


def test_streamlit_config_enables_static_serving() -> None:
    config = tomllib.loads((ROOT / ".streamlit" / "config.toml").read_text())

    assert config["server"]["enableStaticServing"] is True


def test_static_wisp_assets_are_present() -> None:
    wisp_root = ROOT / "static" / "wisp"
    required_paths = [
        wisp_root / "index.html",
        wisp_root / "main.js",
        wisp_root / "wisp.js",
        wisp_root / "post.js",
        wisp_root / "shaders",
        wisp_root / "modules",
        wisp_root / "third_party",
    ]

    missing = [path.relative_to(ROOT).as_posix() for path in required_paths if not path.exists()]

    assert missing == []


def test_streamlit_app_static_path_points_to_root_static() -> None:
    app_static = ROOT / "ui" / "static"

    assert app_static.exists()
    assert app_static.resolve() == (ROOT / "static").resolve()


def test_wisp_iframe_is_first_body_element() -> None:
    template = _home_template()
    body = template.split("<body>", maxsplit=1)[1].lstrip()

    assert body.startswith("<iframe")
    assert 'id="wisp-bg"' in body
    assert 'src="/app/static/wisp/index.html"' in body
    assert 'frameborder="0"' in body


def test_wisp_iframe_css_keeps_background_noninteractive() -> None:
    template = _home_template()
    iframe_css = _css_block(template, "#wisp-bg")
    content_css = _css_block(template, ".content")

    assert "position: fixed;" in iframe_css
    assert "inset: 0;" in iframe_css
    assert "width: 100vw;" in iframe_css
    assert "height: 100vh;" in iframe_css
    assert "z-index: 0;" in iframe_css
    assert "pointer-events: none;" in iframe_css
    assert "filter: brightness(0.65) contrast(1.25) saturate(1.2);" in iframe_css
    assert "position: relative;" in content_css
    assert "z-index: 3;" in content_css


def test_main_app_wisp_background_markup_points_to_static_asset() -> None:
    markup = _module_string_assignment(ROOT / "ui" / "app.py", "_APP_WISP_BACKGROUND_HTML")

    assert '<iframe id="app-wisp-bg"' in markup
    assert 'src="/app/static/wisp/index.html"' in markup
    assert 'frameborder="0"' in markup


def test_main_app_wisp_css_keeps_streamlit_content_above_background() -> None:
    css = _module_string_assignment(ROOT / "ui" / "app.py", "_CSS")
    iframe_css = _css_block(css, "#app-wisp-bg")
    app_container_css = _css_block(css, 'div[data-testid="stAppViewContainer"]')

    assert "position: fixed;" in iframe_css
    assert "inset: 0;" in iframe_css
    assert "width: 100vw;" in iframe_css
    assert "height: 100vh;" in iframe_css
    assert "z-index: 0;" in iframe_css
    assert "pointer-events: none;" in iframe_css
    assert "filter: brightness(0.65) contrast(1.25) saturate(1.2);" in iframe_css
    assert "background: transparent !important;" in app_container_css
    assert "position: relative;" in app_container_css
    assert "z-index: 2;" in app_container_css


def test_main_app_renders_wisp_background_outside_home_view() -> None:
    source = (ROOT / "ui" / "app.py").read_text()

    assert "def _render_app_wisp_background() -> None:" in source
    assert "_render_app_wisp_background()" in source.split("if view == \"home\":", maxsplit=1)[1]


def test_legacy_background_layers_are_removed() -> None:
    template = _home_template()

    assert 'id="particles"' not in template
    assert 'id="dither"' not in template
    assert 'class="mini-boards"' not in template
