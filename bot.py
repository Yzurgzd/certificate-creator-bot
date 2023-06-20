import os
from telegram import Update, ParseMode, ReplyKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
    ConversationHandler
)
from service import (
    create_folder,
    create_sertificate,
    get_publish,
    update_templates,
    get_folders,
    put_publish
)

TOKEN = ""

USERS_ID = ["1691246843", "895060026"]

DATA = {
    "template": '',
    "subtitle": '',
    "date": '',
    "names": [],
    "folder": ''
}

TEMPLATE, SUBTITLE, DATE, NAMES, NEW_FOLDER, FOLDER = range(6)


def get_templates_reply_keyboard():
    """Return template keyboard"""
    keyboard = []

    dir_path = os.path.dirname(os.path.realpath(__file__))
    templates_dir = os.path.join(dir_path, 'templates/layout')
    for root, dirs, files in os.walk(templates_dir):
        for file in files:
            if file.endswith('.html'):
                keyboard.append([str(file)])

    reply_markup = ReplyKeyboardMarkup(
        keyboard, one_time_keyboard=True, resize_keyboard=True)
    return reply_markup


def get_folders_reply_keyboard():
    """Return folders Keyboard"""
    keyboard = []

    folders = get_folders()
    if folders:
        for folder in folders:
            keyboard.append([str(folder["name"])])
    reply_markup = ReplyKeyboardMarkup(
        keyboard, one_time_keyboard=True, resize_keyboard=True)
    return reply_markup


def update(update: Update, context: CallbackContext) -> None:
    """Update templates"""
    chat_id = update.message.chat_id
    update.message.bot.send_message(
        chat_id=chat_id,
        text="📍 Обновляем...",
        parse_mode=ParseMode.HTML
    )

    message = ''
    if update_templates():
        message = "✅ Шаблоны успешно обновлены."
    else:
        message = "💢 Произошла ошибка при обновлении шаблонов."
    update.message.bot.send_message(
        chat_id=chat_id,
        text=message,
        parse_mode=ParseMode.HTML
    )


def help(update: Update, context: CallbackContext) -> None:
    """Command /help"""
    chat_id = update.message.chat_id
    update.message.bot.send_message(
        chat_id=chat_id,
        text="✨ При возникновении ошибок и вопросов, обращаться ко мне.",
        parse_mode=ParseMode.HTML
    )


def start(update: Update, context: CallbackContext) -> int:
    """Сommand /start"""
    chat_id = update.message.chat_id
    update.message.bot.send_message(
        chat_id=chat_id,
        text="📄 Выберите один из доступных шаблонов.\nEсли не отображаются все шаблоны, обновите файлы /update.\n\nОтмена создания /cancel",
        parse_mode=ParseMode.HTML,
        reply_markup=get_templates_reply_keyboard())
    return TEMPLATE


def get_template(update: Update, context: CallbackContext) -> int:
    """Get template"""
    DATA["template"] = update.message.text
    update.message.reply_text(
        text="✉ Введите наименование мероприятия.",
        parse_mode=ParseMode.HTML)
    return SUBTITLE


def get_subtitle(update: Update, context: CallbackContext) -> int:
    """Get subtitle"""
    DATA["subtitle"] = update.message.text
    update.message.reply_text(
        text="📅 Введите дату проведения мероприятия.",
        parse_mode=ParseMode.HTML)
    return DATE


def get_date(update: Update, context: CallbackContext) -> int:
    """Get date"""
    DATA["date"] = update.message.text
    update.message.reply_text(
        text="🎓 Введите участников данного мероприятия.",
        parse_mode=ParseMode.HTML)
    return NAMES


def get_names(update: Update, context: CallbackContext) -> int:
    """Get names"""
    DATA["names"] = update.message.text.split('\n')
    update.message.reply_text(
        text="📁 Введите название новой папки для загрузки сертификатов, " +
        "или /skip если выберите имеющуюся.",
        parse_mode=ParseMode.HTML)
    return NEW_FOLDER


def get_new_folder(update: Update, context: CallbackContext):
    """Get new folder"""
    name_folder = update.message.text
    if create_folder(name_folder):
        DATA["folder"] = name_folder
        update.message.reply_text(
            text="✅ Папка создана", parse_mode=ParseMode.HTML)
        update.message.reply_text(
            text=f"⏳ Создание сертификатов может занять некоторое время", parse_mode=ParseMode.HTML)
        create_sertificate(
            DATA["template"],
            DATA["subtitle"],
            DATA["date"],
            DATA["names"],
            DATA["folder"]
        )

        update.message.reply_text(
            text=f"✅ Сертификаты успешно загружены", parse_mode=ParseMode.HTML)

        href_publish = put_publish(f"certificates/{DATA['folder']}")
        public_url = get_publish(href_publish)

        update.message.reply_text(
            text=f"Сертификаты {DATA['subtitle']}\n\n{public_url}", parse_mode=ParseMode.HTML)
    else:
        update.message.reply_text(
            text=f"💢 Произошла ошибка при создании папки", parse_mode=ParseMode.HTML)

    return ConversationHandler.END


def skip_new_folder(update: Update, context: CallbackContext) -> int:
    """Skip creatind new folder"""
    update.message.reply_text(
        text="📁 Выберите папку для загрузки сертификатов",
        parse_mode=ParseMode.HTML,
        reply_markup=get_folders_reply_keyboard())

    return FOLDER


def get_folder(update: Update, context: CallbackContext) -> int:
    """Get folder"""
    DATA["folder"] = update.message.text

    update.message.reply_text(
        text=f"⏳ Создание сертификатов может занять некоторое время", parse_mode=ParseMode.HTML)

    create_sertificate(
        DATA["template"],
        DATA["subtitle"],
        DATA["date"],
        DATA["names"],
        DATA["folder"]
    )

    href_publish = put_publish(f"certificates/{DATA['folder']}")
    public_url = get_publish(href_publish)

    update.message.reply_text(
        text=f"Сертификаты {DATA['subtitle']}\n\n{public_url}", parse_mode=ParseMode.HTML)

    return ConversationHandler.END


def cancel(update: Update, context: CallbackContext) -> int:
    """Cancels and ends the conversation"""
    update.message.reply_text(
        '🌑 Пока! Я надеюсь, что смогу пригодиться в следующий раз'
    )
    return ConversationHandler.END


def main():
    """Starts the bot"""
    # Create the Updater and pass it your bot's token.
    updater = Updater(TOKEN)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
    conv_handler = ConversationHandler(  # здесь строится логика разговора
        entry_points=[CommandHandler(
            'start', start)],
        states={
            TEMPLATE: [MessageHandler(Filters.text & ~Filters.command, get_template)],
            SUBTITLE: [MessageHandler(Filters.text & ~Filters.command, get_subtitle)],
            DATE: [MessageHandler(Filters.text & ~Filters.command, get_date)],
            NAMES: [
                MessageHandler(Filters.text & ~Filters.command, get_names)
            ],
            NEW_FOLDER: [
                MessageHandler(Filters.text & ~Filters.command,
                               get_new_folder),
                CommandHandler('skip', skip_new_folder)
            ],
            FOLDER: [
                MessageHandler(Filters.text & ~Filters.command, get_folder)
            ]
        },
        # точка выхода из разговора
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    dispatcher.add_handler(conv_handler)

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler(
        "start", start, Filters.user(user_id=USERS_ID)))
    dispatcher.add_handler(CommandHandler("update", update))
    dispatcher.add_handler(CommandHandler("help", help))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
