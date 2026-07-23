from datetime import date
import unittest

from easy_maid.easy_maid.recurrence import RecurrenceRule, generate_dates


class TestRecurrenceLogic(unittest.TestCase):
    def test_weekly_recurrence_generates_expected_dates(self):
        rule = RecurrenceRule(
            frequency="Weekly",
            interval=1,
            start_date=date(2026, 7, 1),
            end_date=None,
            occurrences=4,
        )

        dates = generate_dates(rule, date(2026, 8, 31))
        self.assertEqual(
            dates,
            [
                date(2026, 7, 1),
                date(2026, 7, 8),
                date(2026, 7, 15),
                date(2026, 7, 22),
            ],
        )

    def test_recurrence_stops_at_end_date(self):
        rule = RecurrenceRule(
            frequency="Biweekly",
            interval=1,
            start_date=date(2026, 7, 1),
            end_date=date(2026, 7, 31),
            occurrences=None,
        )

        dates = generate_dates(rule, date(2026, 9, 1))
        self.assertEqual(
            dates,
            [
                date(2026, 7, 1),
                date(2026, 7, 15),
                date(2026, 7, 29),
            ],
        )


if __name__ == "__main__":
    unittest.main()
