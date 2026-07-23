from __future__ import annotations

from dataclasses import dataclass
import calendar
from datetime import date, timedelta


@dataclass(frozen=True)
class RecurrenceRule:
    frequency: str
    interval: int
    start_date: date
    end_date: date | None
    occurrences: int | None


def next_occurrence(current: date, frequency: str, interval: int) -> date:
    if frequency == "Weekly":
        return current + timedelta(days=7 * interval)
    if frequency == "Biweekly":
        return current + timedelta(days=14 * interval)
    if frequency == "Monthly":
        month = current.month - 1 + interval
        year = current.year + month // 12
        month = month % 12 + 1
        day = min(current.day, calendar.monthrange(year, month)[1])
        return date(year, month, day)
    raise ValueError(f"Unsupported recurrence frequency: {frequency}")


def generate_dates(rule: RecurrenceRule, horizon_end: date) -> list[date]:
    out: list[date] = []
    current = rule.start_date
    count = 0

    while current <= horizon_end:
        if rule.end_date and current > rule.end_date:
            break
        if rule.occurrences and count >= rule.occurrences:
            break

        out.append(current)
        count += 1
        current = next_occurrence(current, rule.frequency, max(1, rule.interval))

    return out
