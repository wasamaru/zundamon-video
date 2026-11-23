import zipfile

import pytest

import zvideo.characters as ch


class _RawNameInfo(zipfile.ZipInfo):
    # zipfile は非 ASCII 名に自動で UTF-8 フラグを付けるので、生バイトをフラグ無しで書かせる
    def _encodeFilenameFlags(self):
        return self.raw, self.flag_bits


def _make_zip(path, entries):
    """entries: [(name_bytes_or_str, data, utf8_flag)]"""
    with zipfile.ZipFile(path, "w") as zf:
        for name, data, utf8 in entries:
            if isinstance(name, bytes):
                # cp932 バイト列を cp437 として解釈した文字列で名前を持たせる（flag なし）
                info = _RawNameInfo(name.decode("cp437"))
                info.raw = name
            else:
                info = zipfile.ZipInfo(name)
                if utf8:
                    info.flag_bits |= 0x800
            zf.writestr(info, data)


def test_extract_utf8_names(tmp_path):
    z = tmp_path / "a.zip"
    _make_zip(z, [("ずんだもん立ち絵素材V3.2/x.psd", b"psd", True)])
    out = tmp_path / "out"
    ch.extract_zip(z, out)
    assert (out / "ずんだもん立ち絵素材V3.2" / "x.psd").read_bytes() == b"psd"


def test_extract_cp932_names(tmp_path):
    z = tmp_path / "a.zip"
    _make_zip(z, [("ずんだもん立ち絵素材V3.2/x.psd".encode("cp932"), b"psd", False)])
    out = tmp_path / "out"
    ch.extract_zip(z, out)
    assert (out / "ずんだもん立ち絵素材V3.2" / "x.psd").read_bytes() == b"psd"


def test_copies_from_sozai_home(tmp_path, monkeypatch):
    home = tmp_path / "home" / "ahiru"
    home.mkdir(parents=True)
    ahiru = tmp_path / "rt" / "ahiru"
    psd = ahiru / "metan_2.1" / "d" / "m.psd"
    _make_zip(home / "metan_2.1.zip", [("d/m.psd", b"psd", True)])
    monkeypatch.setenv("ZVIDEO_SOZAI_HOME", str(tmp_path / "home"))
    monkeypatch.setattr(ch, "AHIRU", ahiru)
    monkeypatch.setattr(ch, "METAN_AHIRU", {**ch.METAN_AHIRU, "psd": psd})
    ch.ensure_ahiru_psd("metan")
    assert (ahiru / "metan_2.1.zip").exists()
    assert psd.read_bytes() == b"psd"


def test_structure_mismatch_lists_psds(tmp_path, monkeypatch):
    home = tmp_path / "home" / "ahiru"
    home.mkdir(parents=True)
    ahiru = tmp_path / "rt" / "ahiru"
    _make_zip(home / "metan_2.1.zip", [("other/found.psd", b"psd", True)])
    monkeypatch.setenv("ZVIDEO_SOZAI_HOME", str(tmp_path / "home"))
    monkeypatch.setattr(ch, "AHIRU", ahiru)
    monkeypatch.setattr(ch, "METAN_AHIRU", {**ch.METAN_AHIRU, "psd": ahiru / "metan_2.1" / "no" / "m.psd"})
    with pytest.raises(FileNotFoundError) as e:
        ch.ensure_ahiru_psd("metan")
    assert "found.psd" in str(e.value)
    assert "MD5" not in str(e.value)
