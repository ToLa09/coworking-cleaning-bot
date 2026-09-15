from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler

from cleaning import get_or_create_current_cleaning
from database import get_member, add_member, initialize_database, get_all_members, get_participants, add_participation

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

        await query.message.reply_text(text)

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


def main():
    initialize_database()
    application = (
        Application.builder()
           .token("8922753710:AAHXnDtc2-aqwDuSpAlNJTvlILL8ikj-qWo")
           .build()
    )
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('members', members))
    application.add_handler(CallbackQueryHandler(button_pressed))
    application.run_polling()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
