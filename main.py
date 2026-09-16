from concurrent.interpreters import get_current
from datetime import date, time
from zoneinfo import ZoneInfo

from pyexpat.errors import messages
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, CallbackContext, \
    ConversationHandler, MessageHandler, filters

from cleaning import get_or_create_current_cleaning, shift_cleaning
from config import ADMIN_IDS, TELEGRAM_BOT_TOKEN, GROUP_CHAT_ID, SHIFT_CLEANING
from database import get_member, add_member, initialize_database, get_all_members, get_participants, add_participation, \
    is_participating, get_open_cleaning, complete_cleaning, get_cleaning_statistics, revoke_cleaning_participation, \
    get_user_participations
from reminder import cleaning_reminder


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

async def clean(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    member = get_member(user.id)
    if member is None:
        add_member(
            telegram_id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            username=user.username,
        )
    cleaning = get_or_create_current_cleaning()
    participants = get_participants(cleaning["id"])
    text = (
        f"Hallo {user.first_name}!\n\n"
    )
    if date.fromisoformat(cleaning['start_date']) > date.today():
        text += (
            "🧹 Nächste Reinigung\n\n"
        )
    else:
        text += (
            "🧹 Aktuelle Reinigung\n\n"
        )

    text += (
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
        keyboard.append(
            [
                InlineKeyboardButton(
                    "Doch nicht mithelfen",
                    callback_data="revoke_participation",
                )
            ]
        )
    else:
        keyboard.append(
        [
            InlineKeyboardButton(
                "🙋 Reinigung übernehmen",
                callback_data="take_cleaning"
            )
        ],
        )
    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None

    await update.message.reply_text(
        text,
        reply_markup=reply_markup,
    )

async def shift_cleaning_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    message = "Um wie viele Wochen soll die Reinigung verschoben werden?\nBitte eine Zahl eingeben."
    await update.message.reply_text(message)
    return SHIFT_CLEANING


async def shift_cleaning_value(update, context):
    weeks = int(update.message.text)
    cleaning = get_open_cleaning()
    shift_cleaning(cleaning['id'], weeks)
    await update.message.reply_text(
        f"✅ Reinigung um {weeks} Wochen verschoben."
    )
    return ConversationHandler.END

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

async def user_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    member = get_member(user.id)
    if not member:
        add_member(
            telegram_id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            username=user.username,
        )
    participations = get_user_participations(member['id'])
    if not participations:
        message = "Du hast bisher bei noch keiner Reinigung geholfen"
    else:
        message = f"Du hast bisher bei {len(participations)} Reinigungen mitgeholfen:\n"
        for participation in participations:
            message += (
                f"🧹 {participation['start_date']} – "
                f"{participation['end_date']}\n"
            )
            message += "   ✅ abgeschlossen\n"
            message += f"   Teilnehmer: {participation['first_name']}\n"
    await update.message.reply_text(message)

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

    elif query.data == "revoke_participation":
        user = update.effective_user
        member = get_member(user.id)
        cleaning = get_open_cleaning()
        revoke_cleaning_participation(cleaning["id"],member["id"])
        await query.message.reply_text(
            "Du nimmst nicht mehr an der Reinigung teil."
        )

def main():
    initialize_database()
    application = (
        Application.builder()
           .token(TELEGRAM_BOT_TOKEN)
           .build()
    )
    application.add_handler(ConversationHandler(
        entry_points=[
            CommandHandler(
                'shift',
                shift_cleaning_start
            )
        ],
        states={
            SHIFT_CLEANING: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    shift_cleaning_value
                )
            ]
        },
        fallbacks=[]
    ))
    application.job_queue.run_daily(cleaning_reminder, time=time(hour=21, minute=38, tzinfo=ZoneInfo("Europe/Berlin")))
    application.add_handler(CommandHandler('clean', clean))
    application.add_handler(CommandHandler('members', members))
    application.add_handler(CommandHandler('stats', statistics))
    application.add_handler(CommandHandler('mystats', user_statistics))
    application.add_handler(CallbackQueryHandler(button_pressed))
    application.run_polling()


if __name__ == '__main__':
    main()


