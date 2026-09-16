from datetime import date

from telegram.ext import ContextTypes

from config import GROUP_CHAT_ID
from database import get_open_cleaning, get_participants


async def cleaning_reminder(context: ContextTypes.DEFAULT_TYPE):
    cleaning = get_open_cleaning()
    if not cleaning:
        return
    today = date.today()
    start_date = date.fromisoformat(cleaning["start_date"])
    end_date = date.fromisoformat(cleaning["end_date"])
    days_until_end = (end_date - today).days
    participants = get_participants(cleaning["id"])
    private_message = ""

    if today == start_date:
        if not participants:
            group_message = (
                "Juhu! Diese Woche ist Reinigungswoche.\n"
                "Da noch niemand teilnimmt: Klickt bitte unter /clean auf \"teilnehmen\" wenn ihr diese Woche bei der Büroreinigung mithelft."
            )
        else:
            group_message = (
                "Juhu! Diese Woche ist Reinigungswoche.\n"
                "Wer mithilft klickt bitte unter /clean auf \"teilnehmen\". Wenn ihr fertig seid bitte \"Reinigung abschließen\"."
                "Aktuell nimmt teil:\n"
            )
            for member in participants:
                group_message += f"• {member['first_name']}\n"

            private_message = (
                "Kurze Erinnerung: Diese Woche ist Reinigungswoche im Coworking-Space und du hast dich dazu angemeldet.\n"
            )
    elif days_until_end == 2:
        group_message = (
            "🧹 Erinnerung\n\n"
            "Die Reinigung diese Woche ist noch nicht erledigt."
        )
        private_message = (
            "Kurze Erinnerung: Die Reinigung im Coworking-Space diese Woche ist noch nicht erledigt und du hast dich dazu angemeldet.\n"
        )
    elif days_until_end == 0:
        group_message = (
            "🧹 Erinnerung\n\n"
            "Heute ist der letzte Tag der aktuellen Reinigung. "
            "Bitte denkt daran, sie heute abzuschließen."
        )
        private_message = (
            "Kurze Erinnerung: Heute endet die Reinigungswoche im Coworking-Space und du hast dich dazu angemeldet.\n"
        )
    elif days_until_end < 0:
        group_message = (
            "⚠️ Reinigung überfällig\n\n"
            f"Die aktuelle Reinigung ist seit "
            f"{abs(days_until_end)} Tagen überfällig.\n"
            "Bitte holt sie möglichst bald nach."
        )
        private_message = (
            "Kurze Erinnerung: Die Reinigungswoche im Coworking-Space ist überfällig und du hast dich dazu angemeldet.\n"
        )
    else:
        return

    await context.bot.send_message(
        chat_id=GROUP_CHAT_ID,
        text=group_message,
    )

    if not participants:
        return
    for member in participants:
        try:
            await context.bot.send_message(
                chat_id=member["telegram_id"],
                text=private_message,
            )
        except Exception as error:
            print(
                f"Reminder konnte nicht an "
                f"{member['telegram_id']} gesendet werden: {error}"
            )