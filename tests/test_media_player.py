# Copyright (c) 2026 Liquid Releasing. Licensed under the MIT License.
# Written by human and Claude AI (Claude Sonnet).

"""Tests for ui.streamlit.panels.media_player (pure-Python helpers only).

Does NOT import Streamlit — only the functions that have no UI dependency:
  * validate_media_file()   — magic-byte checker
  * find_matching_media()   — stem-match file finder
  * MEDIA_EXTS              — allowlist set

Scenarios covered
-----------------
Magic-byte validation:
  * Each supported container type with correct magic bytes → None
  * Each container with corrupt / wrong bytes → error string
  * File not found, empty file, file < 12 bytes
  * .avi → helpful ffmpeg conversion hint (not None, not generic error)
  * Unknown extension → unsupported message listing allowed types

Allowlist:
  * .avi absent from MEDIA_EXTS / VIDEO_EXTS

find_matching_media:
  * Matching file found (mp4, mp3 etc.)
  * No match → None
  * Missing uploads directory → None
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Import only the pure-Python symbols — avoids pulling in Streamlit.
from ui.streamlit.panels.media_player import (
    AUDIO_EXTS,
    MEDIA_EXTS,
    VIDEO_EXTS,
    find_matching_media,
    validate_media_file,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write(tmp: str, name: str, content: bytes) -> str:
    path = os.path.join(tmp, name)
    with open(path, "wb") as fh:
        fh.write(content)
    return path


# Minimal valid magic-byte headers (padded to 12 bytes)
_MP3_ID3   = b"ID3" + b"\x00" * 9
_MP3_ADTS  = bytes([0xFF, 0xE0]) + b"\x00" * 10
_MP4       = b"\x00\x00\x00\x20" + b"ftyp" + b"isom" + b"\x00\x00"
_WAV       = b"RIFF" + b"\x00\x00\x00\x00" + b"WAVE"
_OGG       = b"OggS" + b"\x00" * 8
_WEBM      = b"\x1a\x45\xdf\xa3" + b"\x00" * 8
_AAC_MPEG4 = bytes([0xFF, 0xF1]) + b"\x00" * 10
_AVI       = b"RIFF" + b"\x00\x00\x00\x00" + b"AVI "
_GARBAGE   = b"\x00" * 12


# ---------------------------------------------------------------------------
# validate_media_file — happy path
# ---------------------------------------------------------------------------

class TestValidateMediaFileHappyPath(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def _ok(self, name: str, content: bytes) -> None:
        path = _write(self.tmp, name, content)
        self.assertIsNone(validate_media_file(path), f"Expected None for {name}")

    def test_mp3_id3(self):       self._ok("a.mp3",  _MP3_ID3)
    def test_mp3_adts(self):      self._ok("b.mp3",  _MP3_ADTS)
    def test_mp4(self):           self._ok("a.mp4",  _MP4)
    def test_m4a(self):           self._ok("a.m4a",  _MP4)
    def test_mov(self):           self._ok("a.mov",  _MP4)
    def test_wav(self):           self._ok("a.wav",  _WAV)
    def test_ogg(self):           self._ok("a.ogg",  _OGG)
    def test_webm(self):          self._ok("a.webm", _WEBM)
    def test_mkv(self):           self._ok("a.mkv",  _WEBM)
    def test_aac_mpeg4(self):     self._ok("a.aac",  _AAC_MPEG4)
    def test_aac_mpeg2(self):
        aac2 = bytes([0xFF, 0xF9]) + b"\x00" * 10
        self._ok("b.aac", aac2)


# ---------------------------------------------------------------------------
# validate_media_file — corrupt files
# ---------------------------------------------------------------------------

class TestValidateMediaFileCorrupt(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def _err(self, name: str, content: bytes) -> str:
        path = _write(self.tmp, name, content)
        result = validate_media_file(path)
        self.assertIsNotNone(result, f"Expected error for {name}")
        return result

    def test_corrupt_mp3(self):   self._err("bad.mp3",  _GARBAGE)
    def test_corrupt_mp4(self):   self._err("bad.mp4",  _GARBAGE)
    def test_corrupt_wav(self):   self._err("bad.wav",  _GARBAGE)
    def test_corrupt_ogg(self):   self._err("bad.ogg",  _GARBAGE)
    def test_corrupt_webm(self):  self._err("bad.webm", _GARBAGE)
    def test_corrupt_mkv(self):   self._err("bad.mkv",  _GARBAGE)
    def test_corrupt_aac(self):   self._err("bad.aac",  _GARBAGE)


# ---------------------------------------------------------------------------
# validate_media_file — edge cases
# ---------------------------------------------------------------------------

class TestValidateMediaFileEdgeCases(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def test_file_not_found(self):
        result = validate_media_file(os.path.join(self.tmp, "ghost.mp4"))
        self.assertIsNotNone(result)
        self.assertIn("not found", result.lower())

    def test_empty_file(self):
        path = _write(self.tmp, "empty.mp4", b"")
        result = validate_media_file(path)
        self.assertIsNotNone(result)
        self.assertIn("empty", result.lower())

    def test_truncated_file(self):
        path = _write(self.tmp, "short.mp4", b"\x00" * 8)
        result = validate_media_file(path)
        self.assertIsNotNone(result)
        self.assertIn("small", result.lower())

    def test_unknown_extension(self):
        path = _write(self.tmp, "video.xyz", _GARBAGE)
        result = validate_media_file(path)
        self.assertIsNotNone(result)
        self.assertIn("Unsupported", result)
        # Should list allowed types but NOT mention avi
        self.assertNotIn("avi", result.lower())

    def test_avi_returns_helpful_error(self):
        """AVI files get a clear rejection with the ffmpeg conversion command."""
        path = _write(self.tmp, "clip.avi", _AVI)
        result = validate_media_file(path)
        self.assertIsNotNone(result)
        self.assertIn("ffmpeg", result.lower())
        self.assertIn("mp4", result.lower())

    def test_avi_wrong_header_still_returns_avi_error(self):
        """Even a corrupt AVI gets the AVI-specific message, not a generic one."""
        path = _write(self.tmp, "bad.avi", _GARBAGE)
        result = validate_media_file(path)
        self.assertIsNotNone(result)
        self.assertIn("ffmpeg", result.lower())


# ---------------------------------------------------------------------------
# Allowlist constants
# ---------------------------------------------------------------------------

class TestMediaExtsAllowlist(unittest.TestCase):
    def test_avi_not_in_video_exts(self):
        self.assertNotIn(".avi", VIDEO_EXTS)

    def test_avi_not_in_media_exts(self):
        self.assertNotIn(".avi", MEDIA_EXTS)

    def test_avi_not_in_audio_exts(self):
        self.assertNotIn(".avi", AUDIO_EXTS)

    def test_supported_video_exts_present(self):
        for ext in (".mp4", ".mkv", ".mov", ".webm"):
            self.assertIn(ext, VIDEO_EXTS)

    def test_supported_audio_exts_present(self):
        for ext in (".mp3", ".m4a", ".wav", ".ogg", ".aac"):
            self.assertIn(ext, AUDIO_EXTS)


# ---------------------------------------------------------------------------
# find_matching_media
# ---------------------------------------------------------------------------

class TestFindMatchingMedia(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def test_finds_mp4(self):
        open(os.path.join(self.tmp, "MyVideo.mp4"), "w").close()
        result = find_matching_media(
            os.path.join(self.tmp, "MyVideo.funscript"), self.tmp
        )
        self.assertIsNotNone(result)
        self.assertTrue(result.endswith("MyVideo.mp4"))

    def test_finds_mp3(self):
        open(os.path.join(self.tmp, "Track.mp3"), "w").close()
        result = find_matching_media(
            os.path.join(self.tmp, "Track.funscript"), self.tmp
        )
        self.assertIsNotNone(result)
        self.assertTrue(result.endswith("Track.mp3"))

    def test_no_match_returns_none(self):
        result = find_matching_media(
            os.path.join(self.tmp, "Ghost.funscript"), self.tmp
        )
        self.assertIsNone(result)

    def test_missing_uploads_dir_returns_none(self):
        result = find_matching_media(
            os.path.join(self.tmp, "Video.funscript"),
            os.path.join(self.tmp, "nonexistent_dir"),
        )
        self.assertIsNone(result)

    def test_prefers_mp4_over_mp3(self):
        """mp4 is listed first in the search order — it should win."""
        open(os.path.join(self.tmp, "Clip.mp4"), "w").close()
        open(os.path.join(self.tmp, "Clip.mp3"), "w").close()
        result = find_matching_media(
            os.path.join(self.tmp, "Clip.funscript"), self.tmp
        )
        self.assertIsNotNone(result)
        self.assertTrue(result.endswith("Clip.mp4"))


if __name__ == "__main__":
    unittest.main()
