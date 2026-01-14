import datetime
from telegram import ReplyKeyboardMarkup, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# -------------------------------
#  Настройки
# -------------------------------
TOKEN = "8336389852:AAGuMNPiMxdUnCO8P4CsnXDBSGzgTK_Om-w"  # 🔴 Заменить на ваш токен
ADMINS = [973547064]  # 🔴 Заменить на ID админа

# -------------------------------
#  Главное меню
# -------------------------------
def main_menu():
    keyboard = [
        ["📅 Забронировать стол"],
        ["📖 Меню", "📍 О нас"],
        ["☎️ Контакты"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name
    text = (
        f"✨ Добро пожаловать, *{name}!* \n"
        "Я виртуальный ассистент вашего ресторана 'Карабах' 🍽️\n\n"
        "Выберите действие ниже 👇"
    )
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=main_menu())


# -------------------------------
#  Меню бронирования
# -------------------------------
def booking_menu():
    keyboard = [
        ["📆 Выбрать дату"],
        ["🕒 Выбрать время"],
        ["👥 Количество гостей"],
        ["⬅️ Назад"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


async def ask_booking(update, context):
    context.user_data.clear()
    await update.message.reply_text("✨ *Бронирование стола*\nВыберите действие:", parse_mode="Markdown",
                                    reply_markup=booking_menu())


# -------------------------------
#  Дата
# -------------------------------
async def ask_date(update, context):
    context.user_data["waiting_for_date"] = True
    await update.message.reply_text(
        "📆 Введите дату в формате *ДД.ММ.ГГГГ*:",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup([["⬅️ Назад"]], resize_keyboard=True)
    )


def validate_date(date_str):
    try:
        datetime.datetime.strptime(date_str, "%d.%m.%Y")
        return True
    except:
        return False


async def save_date(update, context):
    if not context.user_data.get("waiting_for_date"):
        return

    text = update.message.text
    if text == "⬅️ Назад":
        context.user_data.pop("waiting_for_date", None)
        await update.message.reply_text("↩️ Назад", reply_markup=booking_menu())
        return

    if not validate_date(text):
        await update.message.reply_text("❌ Неверный формат. Введите дату *ДД.ММ.ГГГГ*", parse_mode="Markdown")
        return

    context.user_data["date"] = text
    context.user_data.pop("waiting_for_date", None)
    await update.message.reply_text(f"✔ Дата выбрана: *{text}*", parse_mode="Markdown", reply_markup=booking_menu())


# -------------------------------
#  Время
# -------------------------------
TIME_SLOTS = ["17:00", "18:00", "19:00", "20:00", "21:00", "22:00"]

def time_menu():
    keyboard = [
        ["17:00", "18:00", "19:00"],
        ["20:00", "21:00", "22:00"],
        ["⌨️ Ввести своё время"],
        ["⬅️ Назад"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


async def ask_time(update, context):
    context.user_data["waiting_for_time"] = True
    await update.message.reply_text("🕒 Выберите время или введите вручную:", reply_markup=time_menu())


def validate_time(time_str):
    try:
        t = datetime.datetime.strptime(time_str, "%H:%M").time()

        open_time = datetime.time(10, 0)
        close_time = datetime.time(23, 59)

        # Проверка: время должно быть между 10:00 и 23:59
        return open_time <= t <= close_time

    except ValueError:
        return False

async def save_time(update, context):
    if not context.user_data.get("waiting_for_time"):
        return

    text = update.message.text

    if text == "⬅️ Назад":
        context.user_data.pop("waiting_for_time", None)
        await update.message.reply_text("↩️ Назад", reply_markup=booking_menu())
        return

    if text == "⌨️ Ввести своё время":
        await update.message.reply_text("✏️ Введите время в формате ЧЧ:ММ")
        return

    if not validate_time(text):
        await update.message.reply_text(
            "❌ Наш ресторан работает с 10:00 до 00:00.\n"
            "Пожалуйста, выберите корректное время."
        )
        return

    # ✅ Здесь все отступы одинаковые (4 пробела)
    context.user_data["time"] = text
    context.user_data.pop("waiting_for_time", None)
    await update.message.reply_text(
        f"✔ Время выбрано: *{text}*",
        parse_mode="Markdown",
        reply_markup=booking_menu()
    )


# -------------------------------
#  Количество гостей
# -------------------------------
async def ask_persons(update, context):
    keyboard = [
        ["1", "2", "3", "4"],
        ["5", "6", "7+"],
        ["⬅️ Назад"]
    ]
    context.user_data["waiting_for_persons"] = True
    await update.message.reply_text("👥 Выберите количество гостей:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))


async def save_persons(update, context):
    if not context.user_data.get("waiting_for_persons"):
        return

    text = update.message.text
    if text == "⬅️ Назад":
        context.user_data.pop("waiting_for_persons", None)
        await update.message.reply_text("↩️ Назад", reply_markup=booking_menu())
        return

    if text not in ["1","2","3","4","5","6","7+"]:
        await update.message.reply_text("❌ Выберите количество гостей кнопками.")
        return

    context.user_data["persons"] = text
    context.user_data.pop("waiting_for_persons", None)
    await confirm_booking(update, context)


# -------------------------------
#  Подтверждение брони
# -------------------------------
async def confirm_booking(update, context):
    data = context.user_data
    if not all(k in data for k in ("date", "time", "persons")):
        await update.message.reply_text("⚠️ Заполните все поля бронирования.", reply_markup=booking_menu())
        return

    text = (
        "✨ *Подтверждение брони:*\n\n"
        f"📆 Дата: *{data['date']}*\n"
        f"🕒 Время: *{data['time']}*\n"
        f"👥 Гостей: *{data['persons']}*\n\n"
        "Подтвердить бронь?"
    )
    keyboard = [["✅ Подтвердить", "❌ Отменить"]]
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))


# -------------------------------
#  Уведомление админа
# -------------------------------
async def notify_admin(update, context):
    data = context.user_data
    client_name = update.effective_user.first_name
    client_id = update.effective_user.id

    keyboard = [
        [
            InlineKeyboardButton("✅ Подтвердить", callback_data=f"confirm_{client_id}"),
            InlineKeyboardButton("❌ Отменить", callback_data=f"cancel_{client_id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    for admin in ADMINS:
        await context.bot.send_message(
            chat_id=admin,
            text=(
                f"🔔 *Новая бронь!*\n\n"
                f"📆 Дата: {data['date']}\n"
                f"🕒 Время: {data['time']}\n"
                f"👥 Гостей: {data['persons']}\n"
                f"👤 Клиент: {client_name}"
            ),
            parse_mode="Markdown",
            reply_markup=reply_markup
        )


# -------------------------------
#  Callback админа
# -------------------------------
async def admin_callback(update, context):
    query = update.callback_query
    await query.answer()

    data = query.data
    client_id = int(data.split("_")[1])

    if data.startswith("confirm_"):
        await query.edit_message_text(query.message.text + "\n\n✅ Бронь подтверждена!")
        await context.bot.send_message(client_id, "🎉 Ваша бронь подтверждена! Ждём вас 🍽️")
    elif data.startswith("cancel_"):
        await query.edit_message_text(query.message.text + "\n\n❌ Бронь отменена.")
        await context.bot.send_message(client_id, "⚠️ Ваша бронь отменена. Попробуйте другое время.")


# -------------------------------
#  Обработка текста
# -------------------------------
async def text_handler(update, context):
    text = update.message.text

    if text == "📅 Забронировать стол":
        await ask_booking(update, context)
    elif text == "📆 Выбрать дату":
        await ask_date(update, context)
    elif text == "🕒 Выбрать время":
        await ask_time(update, context)
    elif text == "👥 Количество гостей":
        await ask_persons(update, context)
    elif text in ["⬅️ Назад", "🏠 Главное меню"]:
        await update.message.reply_text("↩️ Возврат в меню:", reply_markup=main_menu())
    elif text in ["📖 Меню", "📍 О нас", "☎️ Контакты"]:
        await update.message.reply_text("Раздел в разработке 😊")
    elif text in ["1","2","3","4","5","6","7+"]:
        await save_persons(update, context)
    elif context.user_data.get("waiting_for_date"):
        await save_date(update, context)
    elif context.user_data.get("waiting_for_time") or text == "⌨️ Ввести своё время":
        await save_time(update, context)
    elif text in ["✅ Подтвердить", "❌ Отменить"]:
        await notify_admin(update, context)
        await confirm_booking(update, context)
    else:
        await update.message.reply_text("Выберите действие из меню 👇", reply_markup=main_menu())

# -------------------------------
#  Запуск бота
# -------------------------------
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
app.add_handler(CallbackQueryHandler(admin_callback))

print("Бот запущен!")
app.run_polling()
