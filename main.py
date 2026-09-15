from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🧹 Coworking Reinigung\n\n"
        "Was möchtest du tun?",
        reply_markup=reply_markup,
    )

async def button_pressed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "take_cleaning":
        await query.message.reply_text(
            "🙋 Du möchtest die Reinigung übernehmen."
        )

    elif query.data == "current_cleaning":
        await query.message.reply_text(
            "📅 Hier zeigen wir später die aktuelle Reinigung."
        )

def main():
    application = (
        Application.builder()
           .token("8922753710:AAHXnDtc2-aqwDuSpAlNJTvlILL8ikj-qWo")
           .build()
    )
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(button_pressed))
    application.run_polling()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
