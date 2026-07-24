import re
from dataclasses import dataclass
from datetime import date, datetime, time


class IssueExtractionError(ValueError):
    pass


@dataclass(frozen=True)
class ExtractedIssue:
    issue_date: date
    issue_time: time
    sender: str
    issue: str


_DATE_PATTERNS = (
    re.compile(r"\b(?P<year>\d{4})-(?P<month>\d{1,2})-(?P<day>\d{1,2})\b"),
    re.compile(r"\b(?P<month>\d{1,2})/(?P<day>\d{1,2})/(?P<year>\d{4})\b"),
)
_TIME_PATTERN = re.compile(
    r"\b(?P<hour>\d{1,2}):(?P<minute>\d{2})"
    r"(?::(?P<second>\d{2})(?:\.(?P<fraction>\d{1,6}))?)?"
    r"(?:\s*(?P<period>am|pm|AM|PM))?\b"
)


def extract_issue(content: str, author: object, message_timestamp: datetime) -> ExtractedIssue:
    issue = (content or "").strip()
    if not issue:
        raise IssueExtractionError("Message content is empty")

    return ExtractedIssue(
        issue_date=_extract_date(issue, message_timestamp),
        issue_time=_extract_time(issue, message_timestamp),
        sender=_extract_sender(author),
        issue=issue,
    )


def _extract_sender(author: object) -> str:
    display_name = getattr(author, "display_name", None)
    if display_name:
        return str(display_name)

    name = getattr(author, "name", None)
    if name:
        return str(name)

    return str(author)


def _extract_date(content: str, fallback: datetime) -> date:
    for pattern in _DATE_PATTERNS:
        match = pattern.search(content)
        if not match:
            continue

        try:
            return date(
                int(match.group("year")),
                int(match.group("month")),
                int(match.group("day")),
            )
        except ValueError:
            continue

    return fallback.date()


def _extract_time(content: str, fallback: datetime) -> time:
    match = _TIME_PATTERN.search(content)
    if not match:
        return fallback.timetz().replace(tzinfo=None)

    hour = int(match.group("hour"))
    minute = int(match.group("minute"))
    second = int(match.group("second") or 0)
    fraction = match.group("fraction") or ""
    microsecond = int(fraction.ljust(6, "0")) if fraction else 0
    period = match.group("period")

    if period:
        if not 1 <= hour <= 12:
            return fallback.timetz().replace(tzinfo=None)
        if period.lower() == "pm" and hour != 12:
            hour += 12
        elif period.lower() == "am" and hour == 12:
            hour = 0

    try:
        return time(
            hour=hour,
            minute=minute,
            second=second,
            microsecond=microsecond,
        )
    except ValueError:
        return fallback.timetz().replace(tzinfo=None)
