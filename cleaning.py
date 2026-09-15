from datetime import date, timedelta

from database import get_open_cleaning, create_cleaning, get_cleaning


def get_current_week():
    today = date.today()

    start = today - timedelta(days=today.weekday())
    end = start + timedelta(days=6)

    return start, end

def get_or_create_current_cleaning():
    cleaning = get_open_cleaning()

    if cleaning:
        return cleaning

    start, end = get_current_week()

    cleaning_id = create_cleaning(
        start.isoformat(),
        end.isoformat(),
    )

    return get_cleaning(cleaning_id)