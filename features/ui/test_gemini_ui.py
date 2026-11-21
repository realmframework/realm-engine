"""Permanent canvas boundaries complement rendered browser acceptance checks."""

import re

from fastapi.testclient import TestClient


def test_hero_has_no_controls_between_greeting_and_prompt(area_client: TestClient) -> None:
    html = area_client.get("/").text
    hero = html.index('id="hero-greeting-text"')
    greeting_end = html.index("</h1>", hero) + len("</h1>")
    pill = html.index('id="prompt-container"', greeting_end)
    between = html[greeting_end:pill]
    assert not re.search(r"<(?:select|button|input|nav|aside)\b", between)
    assert 'id="chat-scope"' not in html and 'id="clear-query-btn"' not in html


def test_optional_scope_chip_is_inside_pill_and_hidden_initially(area_client: TestClient) -> None:
    html = area_client.get("/").text
    pill = html[html.index('id="prompt-container"'):]
    form = pill[:pill.index("</form>")]
    assert re.search(r'<span id="scope-chip"\s+hidden\b', form)
    assert '#scope-chip[hidden] { display: none !important; }' in html
    assert 'id="scope-reset-btn"' in form and 'id="query"' in form
    assert 'id="model"' in form and 'id="mic-btn"' in form and 'id="prompt-submit-btn"' in form
    assert ".chat-dock { background: transparent !important; }" in html
    assert ".chat-scroll-mask {" in html
