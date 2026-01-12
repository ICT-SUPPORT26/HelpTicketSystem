import unittest
from unittest.mock import patch, Mock
import requests

from sms_service import _normalize_phone, send_sms


class TestSMSService(unittest.TestCase):
    def test_normalize_phone_various(self):
        self.assertEqual(_normalize_phone('+254712345678'), '254712345678')
        self.assertEqual(_normalize_phone('254712345678'), '254712345678')
        self.assertEqual(_normalize_phone('0712345678'), '254712345678')
        self.assertEqual(_normalize_phone('712345678'), '254712345678')
        self.assertIsNone(_normalize_phone('12345'))
        self.assertIsNone(_normalize_phone(None))

    @patch('sms_service.requests.post')
    def test_send_sms_success(self, mock_post):
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.text = 'OK'
        mock_post.return_value = mock_resp

        ok = send_sms('0712345678', 'hello', timeout=1, max_retries=1)
        self.assertTrue(ok)
        mock_post.assert_called_once()

    @patch('sms_service.requests.post')
    def test_send_sms_invalid_phone(self, mock_post):
        ok = send_sms('555', 'hello', max_retries=1)
        self.assertFalse(ok)
        mock_post.assert_not_called()

    @patch('sms_service.requests.post')
    def test_send_sms_retries_on_exception_then_success(self, mock_post):
        # First two calls raise, third succeeds
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.text = 'OK'

        def side_effect(*args, **kwargs):
            side_effect.counter += 1
            if side_effect.counter < 3:
                raise requests.exceptions.RequestException('net')
            return mock_resp

        mock_post.side_effect = side_effect
        side_effect.counter = 0

        ok = send_sms('0712345678', 'hello', timeout=1, max_retries=3, backoff_factor=0)
        self.assertTrue(ok)
        self.assertEqual(mock_post.call_count, 3)


if __name__ == '__main__':
    unittest.main()
