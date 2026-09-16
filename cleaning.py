from datetime import date, timedelta

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from database import get_open_cleaning, create_cleaning, get_cleaning, update_cleaning_dates, get_participants, \
    is_participating


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

def build_cleaning_message(cleaning):
    participants = get_participants(cleaning["id"])

    if date.fromisoformat(cleaning["start_date"]) > date.today():
        title = "🧹 Nächste Reinigung"
    else:
        title = "🧹 Aktuelle Reinigung"

    text = (
        f"{title}\n\n"
        f"{cleaning['start_date']} – {cleaning['end_date']}\n\n"
        "👥 Teilnehmer:\n"
    )

    if participants:
        for member in participants:
            text += f"• {member['first_name']}\n"
    else:
        text += "Noch niemand.\n"

    return text

def build_cleaning_keyboard(cleaning, member_id):
    keyboard = []

    if is_participating(cleaning["id"], member_id):
        keyboard.append([
            InlineKeyboardButton(
                "✅ Reinigung abschließen",
                callback_data="complete_cleaning",
            )
        ])
        keyboard.append([
            InlineKeyboardButton(
                "❌ Doch nicht mithelfen",
                callback_data="revoke_participation",
            )
        ])
    else:
        keyboard.append([
            InlineKeyboardButton(
                "🙋 Mithelfen",
                callback_data="take_cleaning",
            )
        ])

    return InlineKeyboardMarkup(keyboard)
