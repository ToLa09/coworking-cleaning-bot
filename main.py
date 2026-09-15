from datetime import date, time
from zoneinfo import ZoneInfo

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler

from cleaning import get_or_create_current_cleaning
from database import get_member, add_member, initialize_database, get_all_members, get_participants, add_participation, \
    is_participating, get_open_cleaning, complete_cleaning, get_cleaning_statistics

ADMIN_IDS = {
    502322401
}

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS



async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    member = get_member(user.id)

    if member is None:
        add_member(
            telegram_id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            username=user.username,
        )

        message = (
            f"Hallo {user.first_name}! 👋\n\n"
            "Du bist jetzt registriert."
        )
    else:
        message = (
            f"Schön dich wiederzusehen, {user.first_name}! 👋"
        )

    keyboard = [
        [
            InlineKeyboardButton(
                "🙋 Reinigung übernehmen",
                callback_data="take_cleaning"
            )
        ],
        [
            InlineKeyboardButton(
                "📅 Aktuelle Reinigung",
                callback_data="current_cleaning"
            )
        ],
    ]

    await update.message.reply_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

async def button_pressed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user

    if query.data == "take_cleaning":
        user = update.effective_user
        member = get_member(user.id)
        if not member:
            await query.message.reply_text(
                "Fehler: Du bist noch nicht als Mitglied registriert"
            )
            return

        cleaning = get_or_create_current_cleaning()
        add_participation(
            cleaning["id"],
            member["id"],
        )
        await query.message.reply_text(
            "🧹 Du bist bei der aktuellen Reinigung dabei! 👍"
        )

    elif query.data == "current_cleaning":
        cleaning = get_or_create_current_cleaning()
        participants = get_participants(cleaning["id"])
        text = (
            "🧹 Aktuelle Reinigung\n\n"
            f"{cleaning['start_date']} – "
            f"{cleaning['end_date']}\n\n"
            "👥 Teilnehmer:\n"
        )
        if participants:
            for member in participants:
                text += f"• {member['first_name']}\n"
        else:
            text += "Noch niemand.\n"

        user = update.effective_user
        member = get_member(user.id)
        keyboard = []
        if is_participating(cleaning["id"], member["id"]):
            keyboard.append(
                [
                    InlineKeyboardButton(
                        "🧹 Reinigung abschließen",
                        callback_data="complete_cleaning",
                    )
                ]
            )
        reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None

        await query.message.reply_text(
            text,
            reply_markup=reply_markup,
        )

    elif query.data == "complete_cleaning":
        user = update.effective_user
        member = get_member(user.id)
        if not member:
            await query.message.reply_text(
                "Du bist nicht als Mitglied registriert."
            )
            return
        cleaning = get_open_cleaning()
        if not cleaning:
            await query.message.reply_text(
                "Es gibt aktuell keine offene Reinigung."
            )
            return
        if not is_participating(
                cleaning["id"],
                member["id"],
        ):
            await query.message.reply_text(
                "⛔ Du bist für diese Reinigung nicht registriert."
            )
            return
        if date.fromisoformat(cleaning["start_date"]) > date.today():
            await query.message.reply_text(
                "Die Reinigung kann nicht abgeschlossen werden weil sie in der Zukunft liegt."
            )
            return
        new_cleaning_id = complete_cleaning(
            cleaning["id"]
        )
        if new_cleaning_id is None:
            await query.message.reply_text(
                "Die Reinigung konnte nicht abgeschlossen werden."
            )
            return
        await query.message.reply_text(
            "✅ Reinigung abgeschlossen!\n\n"
            "🧹 Die nächste Reinigung wurde automatisch erstellt."
        )

async def members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text(
            "⛔ Dieser Befehl ist nur für Admins verfügbar."
        )
        return

    members = get_all_members()

    if not members:
        await update.message.reply_text(
            "Noch keine Mitglieder registriert."
        )
        return

    text = "👥 Mitglieder\n\n"
    for member in members:
        text += f"• {member['first_name']}"
        if member["last_name"]:
            text += f" {member['last_name']}"
        text += f" — ID: {member['telegram_id']}\n"

    await update.message.reply_text(text)

async def statistics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = get_cleaning_statistics()
    if not rows:
        await update.message.reply_text(
            "Noch keine Reinigungen vorhanden."
        )
        return

    text = "📊 Reinigungsstatistik\n\n"
    current_cleaning_id = None

    for row in rows:
        if row["id"] != current_cleaning_id:
            current_cleaning_id = row["id"]
            text += (
                f"🧹 {row['start_date']} – "
                f"{row['end_date']}\n"
            )
            if row["status"] == "COMPLETED":
                text += "   ✅ abgeschlossen\n"
            else:
                text += "   🟢 offen\n"

            text += "   Teilnehmer:"
        if row["first_name"]:
            text += f" {row['first_name']}"
        text += "\n"

    await update.message.reply_text(text)

async def cleaning_reminder(context: ContextTypes.DEFAULT_TYPE):
    cleaning = get_open_cleaning()
    if not cleaning:
        return
    today = date.today()
    end_date = date.fromisoformat(cleaning["end_date"])
    days_until_end = (end_date - today).days

    if days_until_end == 1:
        message = (
            "🧹 Erinnerung\n\n"
            "Die aktuelle Reinigung endet morgen."
            "Bitte denkt daran, sie noch zu erledigen."
        )
    elif days_until_end == 0:
        message = (
            "🧹 Erinnerung\n\n"
            "Heute ist der letzte Tag der aktuellen Reinigung. "
            "Bitte denkt daran, sie heute abzuschließen."
        )
    elif days_until_end < 0:
        message = (
            "⚠️ Reinigung überfällig\n\n"
            f"Die aktuelle Reinigung ist seit "
            f"{abs(days_until_end)} Tagen überfällig.\n"
            "Bitte holt sie möglichst bald nach."
        )
    else:
        return

    participants = get_participants(cleaning["id"])
    if not participants:
        return
    for member in participants:
        try:
            await context.bot.send_message(
                chat_id=member["telegram_id"],
                text=message,
            )
        except Exception as error:
            print(
                f"Reminder konnte nicht an "
                f"{member['telegram_id']} gesendet werden: {error}"
            )


def main():
    initialize_database()
    application = (
        Application.builder()
           .token("8922753710:AAHXnDtc2-aqwDuSpAlNJTvlILL8ikj-qWo")
           .build()
    )
    application.job_queue.run_daily(cleaning_reminder, time=time(hour=9, minute=0, tzinfo=ZoneInfo("Europe/Berlin")))
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('members', members))
    application.add_handler(CommandHandler('stats', statistics))
    application.add_handler(CallbackQueryHandler(button_pressed))
    application.run_polling()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
