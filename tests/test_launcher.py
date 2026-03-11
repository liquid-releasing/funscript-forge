# Copyright (c) 2026 Liquid Releasing. Licensed under the MIT License.
# Written by human and Claude AI (Claude Sonnet).

"""Tests for the local media HTTP server in launcher.py (_MediaHandler).

Starts a real HTTPServer on a loopback port for each test class so the
handler code runs as-is (no mocking of internals).  Each test creates
temporary media files in a tmpdir and makes real HTTP requests via
urllib.

Security scenarios
------------------
* Relative path in query string      → 400 Bad Request
* Empty path                         → 400 Bad Request
* Absolute path — file missing       → 404 Not Found
* Known extension but wrong content  → 200 (server is extension-only,
                                         magic-byte check is in the UI layer)
* Extension not in allowlist (.avi)  → 403 Forbidden
* Extension not in allowlist (.txt)  → 403 Forbidden
* Symlink whose *resolved* ext is
  outside the allowlist              → 403 Forbidden  (Windows: skipped if
                                         symlinks require elevation)

Range requests
--------------
* Range: bytes=0-3 on a small file   → 206 Partial Content
* Full file request                  → 200 OK with correct Content-Length
"""

import http.client
import http.server
import os
import sys
import tempfile
import threading
import unittest
from urllib.parse import quote

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Import the private handler class directly — it has no side effects on import.
from launcher import _MediaHandler


# ---------------------------------------------------------------------------
# Server fixture
# ---------------------------------------------------------------------------

def _start_server() -> tuple[http.server.HTTPServer, int]:
    """Start a _MediaHandler server on a random loopback port."""
    server = http.server.HTTPServer(("127.0.0.1", 0), _MediaHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, port


def _get(port: int, path_param: str, range_header: str | None = None):
    """Make a GET /media?path=<encoded> request and return the response."""
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    headers = {}
    if range_header:
        headers["Range"] = range_header
    encoded = quote(path_param, safe="/:\\")
    conn.request("GET", f"/media?path={encoded}", headers=headers)
    return conn.getresponse()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write(tmp: str, name: str, content: bytes = b"\x00" * 64) -> str:
    path = os.path.join(tmp, name)
    with open(path, "wb") as fh:
        fh.write(content)
    return path


# ---------------------------------------------------------------------------
# Bad request / not found
# ---------------------------------------------------------------------------

class TestMediaHandlerBadRequests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.server, cls.port = _start_server()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def test_empty_path_returns_400(self):
        resp = _get(self.port, "")
        self.assertEqual(resp.status, 400)

    def test_relative_path_returns_400(self):
        resp = _get(self.port, "relative/path/file.mp4")
        self.assertEqual(resp.status, 400)

    def test_missing_file_returns_404(self):
        # Use an absolute path rooted in a real tmpdir — just don't create the file.
        ghost = os.path.join(self.tmp, "ghost_video.mp4")
        resp = _get(self.port, ghost)
        self.assertEqual(resp.status, 404)


# ---------------------------------------------------------------------------
# Extension allowlist
# ---------------------------------------------------------------------------

class TestMediaHandlerAllowlist(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.server, cls.port = _start_server()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def test_avi_returns_403(self):
        path = _write(self.tmp, "clip.avi")
        resp = _get(self.port, path)
        self.assertEqual(resp.status, 403)

    def test_txt_returns_403(self):
        path = _write(self.tmp, "notes.txt")
        resp = _get(self.port, path)
        self.assertEqual(resp.status, 403)

    def test_exe_returns_403(self):
        path = _write(self.tmp, "evil.exe")
        resp = _get(self.port, path)
        self.assertEqual(resp.status, 403)

    def test_mp4_returns_200(self):
        path = _write(self.tmp, "video.mp4")
        resp = _get(self.port, path)
        self.assertEqual(resp.status, 200)

    def test_mp3_returns_200(self):
        path = _write(self.tmp, "audio.mp3")
        resp = _get(self.port, path)
        self.assertEqual(resp.status, 200)

    def test_webm_returns_200(self):
        path = _write(self.tmp, "video.webm")
        resp = _get(self.port, path)
        self.assertEqual(resp.status, 200)

    def test_mkv_returns_200(self):
        path = _write(self.tmp, "video.mkv")
        resp = _get(self.port, path)
        self.assertEqual(resp.status, 200)

    def test_wav_returns_200(self):
        path = _write(self.tmp, "audio.wav")
        resp = _get(self.port, path)
        self.assertEqual(resp.status, 200)

    def test_ogg_returns_200(self):
        path = _write(self.tmp, "audio.ogg")
        resp = _get(self.port, path)
        self.assertEqual(resp.status, 200)

    def test_aac_returns_200(self):
        path = _write(self.tmp, "audio.aac")
        resp = _get(self.port, path)
        self.assertEqual(resp.status, 200)

    def test_m4a_returns_200(self):
        path = _write(self.tmp, "audio.m4a")
        resp = _get(self.port, path)
        self.assertEqual(resp.status, 200)

    def test_mov_returns_200(self):
        path = _write(self.tmp, "video.mov")
        resp = _get(self.port, path)
        self.assertEqual(resp.status, 200)


# ---------------------------------------------------------------------------
# Content-Type header
# ---------------------------------------------------------------------------

class TestMediaHandlerContentType(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.server, cls.port = _start_server()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def _ct(self, name: str) -> str:
        path = _write(self.tmp, name)
        resp = _get(self.port, path)
        return resp.getheader("Content-Type", "")

    def test_mp4_content_type(self):
        self.assertIn("video/mp4", self._ct("a.mp4"))

    def test_mp3_content_type(self):
        self.assertIn("audio/mpeg", self._ct("a.mp3"))

    def test_webm_content_type(self):
        self.assertIn("video/webm", self._ct("a.webm"))


# ---------------------------------------------------------------------------
# Range requests
# ---------------------------------------------------------------------------

class TestMediaHandlerRangeRequests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.server, cls.port = _start_server()
        cls.mp4 = _write(cls.tmp, "range_test.mp4", b"A" * 100)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def test_range_returns_206(self):
        resp = _get(self.port, self.mp4, range_header="bytes=0-9")
        self.assertEqual(resp.status, 206)

    def test_range_body_length(self):
        resp = _get(self.port, self.mp4, range_header="bytes=0-9")
        body = resp.read()
        self.assertEqual(len(body), 10)

    def test_range_content_range_header(self):
        resp = _get(self.port, self.mp4, range_header="bytes=10-19")
        cr = resp.getheader("Content-Range", "")
        self.assertTrue(cr.startswith("bytes 10-19/"))

    def test_range_partial_body_correct(self):
        resp = _get(self.port, self.mp4, range_header="bytes=5-14")
        body = resp.read()
        self.assertEqual(body, b"A" * 10)

    def test_full_request_returns_200(self):
        resp = _get(self.port, self.mp4)
        self.assertEqual(resp.status, 200)

    def test_full_request_content_length(self):
        resp = _get(self.port, self.mp4)
        self.assertEqual(int(resp.getheader("Content-Length", 0)), 100)

    def test_accept_ranges_header_present(self):
        resp = _get(self.port, self.mp4)
        self.assertEqual(resp.getheader("Accept-Ranges", ""), "bytes")


# ---------------------------------------------------------------------------
# Symlink security
# ---------------------------------------------------------------------------

class TestMediaHandlerSymlinkSecurity(unittest.TestCase):
    """Symlinks named *.mp4 that resolve to a non-media file must be blocked.

    Skipped on platforms where symlink creation requires elevated privileges.
    """

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.server, cls.port = _start_server()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def test_symlink_to_text_file_blocked(self):
        txt = _write(self.tmp, "secret.txt", b"sensitive data")
        link = os.path.join(self.tmp, "trick.mp4")
        try:
            os.symlink(txt, link)
        except (OSError, NotImplementedError):
            self.skipTest("Symlink creation not available on this platform/user")

        resp = _get(self.port, link)
        # The resolved path ends in .txt — must be refused (403), not served.
        self.assertEqual(resp.status, 403)

    def test_symlink_to_mp4_allowed(self):
        real = _write(self.tmp, "real_video.mp4", b"\x00" * 32)
        link = os.path.join(self.tmp, "linked_video.mp4")
        try:
            os.symlink(real, link)
        except (OSError, NotImplementedError):
            self.skipTest("Symlink creation not available on this platform/user")

        resp = _get(self.port, link)
        self.assertEqual(resp.status, 200)


if __name__ == "__main__":
    unittest.main()
