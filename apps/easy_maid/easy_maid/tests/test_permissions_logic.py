import unittest

from easy_maid.easy_maid.permissions_logic import can_transition_visit_status


class TestPermissionsLogic(unittest.TestCase):
    def test_owner_can_complete_without_assignment(self):
        allowed = can_transition_visit_status(
            old_status="Scheduled",
            new_status="Completed",
            roles={"System Manager"},
            is_assigned_cleaner=False,
        )
        self.assertTrue(allowed)

    def test_assigned_cleaner_can_start(self):
        allowed = can_transition_visit_status(
            old_status="Scheduled",
            new_status="In Progress",
            roles={"Employee"},
            is_assigned_cleaner=True,
        )
        self.assertTrue(allowed)

    def test_unassigned_cleaner_cannot_complete(self):
        allowed = can_transition_visit_status(
            old_status="Scheduled",
            new_status="Completed",
            roles={"Employee"},
            is_assigned_cleaner=False,
        )
        self.assertFalse(allowed)


if __name__ == "__main__":
    unittest.main()
