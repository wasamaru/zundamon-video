import pytest


def _patch_setup(monkeypatch):
    import zvideo.setup_env as s
    called = []
    monkeypatch.setattr(s, "ensure_voicevox", lambda: called.append(1) or "ok")
    monkeypatch.setattr(s, "download", lambda *a, **k: "skip")
    monkeypatch.setattr(s, "ensure_playwright_browser", lambda: None)
    monkeypatch.setattr(s, "DOWNLOADS", [])
    return s, called


def test_no_voicevox_flag_skips_download(monkeypatch):
    monkeypatch.delenv("ZVIDEO_NO_VOICEVOX", raising=False)
    s, called = _patch_setup(monkeypatch)
    s.main(["--no-voicevox"])
    assert called == []


def test_env_var_skips_download(monkeypatch):
    monkeypatch.setenv("ZVIDEO_NO_VOICEVOX", "1")
    s, called = _patch_setup(monkeypatch)
    s.main([])
    assert called == []


def test_default_still_ensures_voicevox(monkeypatch):
    monkeypatch.delenv("ZVIDEO_NO_VOICEVOX", raising=False)
    s, called = _patch_setup(monkeypatch)
    s.main([])
    assert called == [1]


def test_linux_missing_engine_message(monkeypatch):
    import zvideo.voicevox as v
    monkeypatch.setattr(v, "engine_version", lambda: None)
    monkeypatch.setattr(v.sys, "platform", "linux")
    with pytest.raises(RuntimeError, match="voicevox/voicevox_engine:cpu-latest"):
        v.ensure_engine()
