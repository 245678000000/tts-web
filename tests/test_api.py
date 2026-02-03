import unittest
from unittest.mock import patch

from web_app import app


class TestAPI(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_synthesize_missing_text(self):
        response = self.client.post("/api/synthesize", json={"voice_name": "x"})
        self.assertEqual(response.status_code, 400)
        body = response.get_json()
        self.assertEqual(body["error_code"], "invalid_request")

    @patch("web_app.synthesize_text")
    def test_synthesize_success(self, mock_synthesize):
        mock_synthesize.return_value = b"FAKE_MP3_DATA"
        response = self.client.post(
            "/api/synthesize",
            json={
                "text": "你好，世界。",
                "voice_name": "zh-CN-XiaoxiaoNeural",
                "style": "narration-relaxed",
                "rate": "0",
                "pitch": "0",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "audio/mpeg")
        self.assertEqual(response.data, b"FAKE_MP3_DATA")
        self.assertIn("attachment; filename=", response.headers.get("Content-Disposition", ""))

    @patch("web_app.synthesize_text")
    def test_synthesize_service_error(self, mock_synthesize):
        mock_synthesize.side_effect = RuntimeError("boom")
        response = self.client.post("/api/synthesize", json={"text": "hello"})
        self.assertEqual(response.status_code, 500)
        body = response.get_json()
        self.assertEqual(body["error_code"], "synthesis_failed")

    @patch("web_app.get_available_voices")
    def test_voices_success(self, mock_voices):
        mock_voices.return_value = [
            {
                "short_name": "zh-CN-XiaoxiaoNeural",
                "locale": "zh-CN",
                "gender": "Female",
                "display_name": "晓晓",
            }
        ]
        response = self.client.get("/api/voices")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("voices", data)
        self.assertEqual(len(data["voices"]), 1)


if __name__ == "__main__":
    unittest.main()
