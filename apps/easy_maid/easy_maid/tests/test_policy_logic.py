from datetime import datetime, timedelta
import unittest

from easy_maid.easy_maid.policy_logic import can_client_modify_visit


class TestPolicyLogic(unittest.TestCase):
    def test_client_can_modify_when_more_than_24h(self):
        now = datetime(2026, 7, 23, 9, 0, 0)
        scheduled = now + timedelta(hours=30)
        self.assertTrue(can_client_modify_visit(scheduled, now))


    def test_client_cannot_modify_when_less_than_24h(self):
        now = datetime(2026, 7, 23, 9, 0, 0)
        scheduled = now + timedelta(hours=10)
        self.assertFalse(can_client_modify_visit(scheduled, now))


    def test_client_exactly_24h_is_allowed(self):
        now = datetime(2026, 7, 23, 9, 0, 0)
        scheduled = now + timedelta(hours=24)
        self.assertTrue(can_client_modify_visit(scheduled, now))


if __name__ == "__main__":
    unittest.main()
