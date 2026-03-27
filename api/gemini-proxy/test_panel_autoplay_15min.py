#!/usr/bin/env python3
"""
Verify panel autoplay can consume a full 15-minute (900 s) budget.

Default (no network): mocks Vertex GenerativeModel and advances a virtual monotonic
clock each turn so ~900s elapses in sub-second wall time.

Optional live mode: POST /chat to a running service with a small autoplay value
for a quick smoke test (full 15 minutes is opt-in via --live-minutes 15).

Run from this directory (needs FastAPI/Pydantic from requirements.txt):
  cd api/gemini-proxy
  python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
  .venv/bin/python test_panel_autoplay_15min.py

Live smoke (real Vertex calls, small budget by default):
  CHAT_API_URL=https://YOUR-SERVICE.run.app .venv/bin/python test_panel_autoplay_15min.py
  # Full wall-clock ~15 min (expensive): add --live-minutes 15 --live-timeout 970
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import unittest.mock as mock
from typing import Any, List
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def _ensure_import_path() -> None:
    here = os.path.dirname(os.path.abspath(__file__))
    if here not in sys.path:
        sys.path.insert(0, here)


def test_chat_request_autoplay_cap() -> None:
    _ensure_import_path()
    from pydantic import ValidationError

    from main_fastapi import ChatRequest

    r = ChatRequest(message="hi", autoplay_panel_minutes=15.0)
    assert r.autoplay_panel_minutes == 15.0

    try:
        ChatRequest(message="hi", autoplay_panel_minutes=15.01)
    except ValidationError:
        pass
    else:
        raise AssertionError("autoplay_panel_minutes above 15 should be rejected")


class _FakeResp:
    text = "Autoplay stub line — one beat only."


class _VirtualClock:
    def __init__(self) -> None:
        self.t = 0.0

    def monotonic(self) -> float:
        return self.t

    def advance(self, seconds: float) -> None:
        self.t += seconds


class _FakeGenerativeModel:
    """Minimal stand-in for vertexai GenerativeModel used inside run_panel_autoplay."""

    clk: _VirtualClock
    per_turn_seconds: float

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass

    def start_chat(self, history: List[Any]):
        return self

    def send_message(self, msg: str):
        self.clk.advance(self.per_turn_seconds)
        return _FakeResp()

    def generate_content(self, msg: str):
        self.clk.advance(self.per_turn_seconds)
        return _FakeResp()


def test_run_panel_autoplay_full_15_minute_budget() -> None:
    """
    With max_turns=240 and 15*60s budget, each turn advances time by 3.75s so
    240 turns land exactly at 900s and the loop exits on time (not max_turns early).
    """
    _ensure_import_path()
    import main_fastapi as mf

    clk = _VirtualClock()
    per_turn = 900.0 / 240.0  # 3.75 — fills budget exactly in 240 turns

    guests = ["terpenequeen", "pinene"]
    history: List[dict] = [{"role": "user", "content": "Quick panel kickoff — autoplay test."}]
    responses: List[dict] = []

    class FM(_FakeGenerativeModel):
        per_turn_seconds = per_turn

    FM.clk = clk

    # Avoid importing vertexai Content types in this unit test.
    with mock.patch.object(mf.time, "monotonic", clk.monotonic):
        with mock.patch.object(mf, "build_vertex_chat_history", return_value=[]):
            mf.run_panel_autoplay(
                FM,
                guests,
                history,
                responses,
                autoplay_minutes=15.0,
            )

    assert len(responses) == 240, f"expected 240 autoplay turns, got {len(responses)}"
    assert clk.t >= 900.0, f"virtual elapsed {clk.t}s should reach 900s budget"
    assert clk.t < 901.0, f"virtual elapsed {clk.t}s should not overshoot meaningfully"

    # Alternation: after user, first speaker is a guest
    assert responses[0]["terpene_id"] == "pinene"
    assert responses[1]["terpene_id"] == "terpenequeen"


def live_smoke_post(
    base_url: str,
    minutes: float,
    timeout_sec: float,
) -> None:
    """POST /chat with autoplay_panel_minutes (real Vertex calls — costs $ / time)."""
    url = base_url.rstrip("/") + "/chat"
    body = json.dumps(
        {
            "message": "Say one short sentence about terpenes, then the panel may continue.",
            "active_terpenes": ["terpenequeen", "pinene"],
            "conversation_history": [],
            "autoplay_panel_minutes": minutes,
        }
    ).encode("utf-8")
    req = Request(
        url,
        data=body,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    t0 = time.monotonic()
    try:
        with urlopen(req, timeout=timeout_sec) as resp:
            raw = resp.read().decode("utf-8")
    except HTTPError as e:
        raise SystemExit(f"HTTP {e.code}: {e.read().decode('utf-8', errors='replace')}") from e
    except URLError as e:
        raise SystemExit(f"Request failed: {e}") from e
    wall = time.monotonic() - t0
    data = json.loads(raw)
    n = len(data.get("responses") or [])
    print(f"Live smoke OK: {n} assistant segments in {wall:.1f}s wall time (autoplay={minutes} min).")
    if n < 2:
        raise SystemExit(f"Expected at least 2 responses for autoplay>0, got {n}")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--live-url",
        default=os.environ.get("CHAT_API_URL", ""),
        help="If set, POST /chat here (e.g. https://....run.app)",
    )
    p.add_argument(
        "--live-minutes",
        type=float,
        default=0.1,
        help="Autoplay minutes for live smoke (default 0.1 ≈ 6s budget). Use 15 only if you mean it.",
    )
    p.add_argument(
        "--live-timeout",
        type=float,
        default=970.0,
        help="urllib timeout seconds (must exceed autoplay wall time + margin).",
    )
    args = p.parse_args()

    test_chat_request_autoplay_cap()
    print("ok: ChatRequest accepts 15.0 and rejects >15")

    test_run_panel_autoplay_full_15_minute_budget()
    print("ok: run_panel_autoplay fills full 15-minute virtual budget (240 turns @ 3.75s)")

    if args.live_url:
        live_smoke_post(args.live_url, args.live_minutes, args.live_timeout)
    else:
        print("skip: live smoke (pass --live-url or set CHAT_API_URL)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
