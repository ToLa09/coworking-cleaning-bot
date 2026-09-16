from datetime import date, timedelta

from database import get_open_cleaning, create_cleaning, get_cleaning, update_cleaning_dates


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


def shift_cleaning(cleaning_id: int, weeks: int):
    cleaning = get_cleaning(cleaning_id)
    if not cleaning:
        return
    current_start = date.fromisoformat(cleaning['start_date'])
    current_end = date.fromisoformat(cleaning['end_date'])
    new_start = current_start + timedelta(weeks=weeks)
    new_end = current_end + timedelta(weeks=weeks)
    update_cleaning_dates(cleaning_id, new_start, new_end)
    return
