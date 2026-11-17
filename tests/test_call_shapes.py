"""Offline tests for the platform call shapes (no network, no tokens).

Run:  python3 -m unittest discover -s tests -v
Mocks `requests` and asserts each platform calls the exact endpoints,
methods and parameters documented in the official API docs. These tests
prove the request shapes; live behaviour still needs real tokens
(see docs/SETUP.md).
"""
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from platforms import dailymotion as dm  # noqa: E402
from platforms import threads as th  # noqa: E402
from platforms import youtube as yt  # noqa: E402


def _resp(json_data=None, status=200, headers=None):
    m = MagicMock()
    m.ok = 200 <= status < 300
    m.status_code = status
    m.json.return_value = json_data or {}
    m.headers = headers or {}
    m.text = str(json_data)
    return m


class ThreadsTest(unittest.TestCase):
    @patch("platforms.threads.requests")
    def test_video_post_flow(self, req):
        req.post.side_effect = [
            _resp({"id": "111"}),  # container
            _resp({"id": "222"}),  # publish
        ]
        req.get.side_effect = [
            _resp({"status": "FINISHED"}),  # container status
            _resp({"permalink": "https://www.threads.com/@aiwo.rldclips/post/abc"}),
        ]
        with patch("platforms.threads.time.sleep"):
            url = th.post_threads(
                "https://example.com/clip.mp4", "hook\nfooter", "999", "tok"
            )
        self.assertEqual(url, "https://www.threads.com/@aiwo.rldclips/post/abc")
        create = req.post.call_args_list[0]
        self.assertTrue(create[0][0].endswith("/999/threads"))
        self.assertEqual(create[1]["data"]["media_type"], "VIDEO")
        self.assertEqual(create[1]["data"]["video_url"], "https://example.com/clip.mp4")
        publish = req.post.call_args_list[1]
        self.assertTrue(publish[0][0].endswith("/999/threads_publish"))
        self.assertEqual(publish[1]["data"]["creation_id"], "111")


class DailymotionTest(unittest.TestCase):
    @patch("platforms.dailymotion.requests")
    def test_upload_flow(self, req):
        req.post.side_effect = [
            _resp({"access_token": "at"}),  # token refresh
            _resp({"upload_url": "https://upload.dm/upload?uuid=u&extra=prof1",
                   "progress_url": "https://upload.dm/progress?uuid=u"}),
            _resp({"url": "https://upload.dm/files/f1"}),  # file upload
            _resp({"video_id": "xabc"}, status=201),  # video creation
        ]
        req.get.return_value = _resp({"id": "prof1"})
        with open("/tmp/dm-test.mp4", "wb") as f:
            f.write(b"\x00" * 1024)
        url = dm.post_dailymotion("/tmp/dm-test.mp4", "Title", "Desc", ["viral"],
                                  "funny", "cid", "csec", "rtok")
        self.assertEqual(url, "https://www.dailymotion.com/video/xabc")
        create = req.post.call_args_list[3]
        self.assertTrue(create[0][0].endswith("/v2/profiles/prof1/videos"))
        import json as _json
        body = _json.loads(create[1]["data"])
        self.assertEqual(body["category"], "funny")
        self.assertEqual(body["visibility"], "public")
        self.assertIs(body["is_for_kids"], False)
        self.assertEqual(body["source"]["file_url"], "https://upload.dm/files/f1")


class YouTubeTest(unittest.TestCase):
    @patch("platforms.youtube.requests")
    def test_resumable_upload_with_resume(self, req):
        # 9 MB file -> two chunks; first PUT answers 308, second 200.
        path = "/tmp/yt-test.mp4"
        with open(path, "wb") as f:
            f.write(b"\x00" * (9 * 1024 * 1024))
        req.post.side_effect = [
            _resp({"access_token": "at"}),  # token refresh
            _resp({}, headers={"Location": "https://upload/session/xyz"}),  # session
        ]
        first_put = _resp({}, status=308, headers={"Range": "bytes=0-8388607"})
        second_put = _resp({"id": "yt123"})
        req.put.side_effect = [first_put, second_put]
        video_id, privacy = yt.post_youtube(
            path, "Title", "Desc", ["viral"], "24", "cid", "csec", "rtok"
        )
        self.assertEqual((video_id, privacy), ("yt123", "public"))
        session = req.post.call_args_list[1]
        self.assertIn("uploadType=resumable", session[0][0])
        self.assertIn("part=snippet,status", session[0][0])
        self.assertEqual(req.put.call_args_list[0][1]["headers"]["Content-Range"],
                         "bytes 0-8388607/9437184")
        self.assertEqual(req.put.call_args_list[1][1]["headers"]["Content-Range"],
                         "bytes 8388608-9437183/9437184")


if __name__ == "__main__":
    unittest.main()
