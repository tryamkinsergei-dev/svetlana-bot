"""
╔══════════════════════════════════════════════════════╗
║     БОТ СВЕТЛАНЫ — Кармическая Звезда               ║
║     Полная воронка: калькулятор → оплата → видео    ║
╚══════════════════════════════════════════════════════╝

Перед запуском заполни переменные в файле .env:
  BOT_TOKEN, YUKASSA_SHOP_ID, YUKASSA_SECRET, PUBLIC_URL
"""

import os, logging, threading, sqlite3, requests, json, uuid
from flask import Flask, request, jsonify
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    WebAppInfo, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes
)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ═══════════════════════════════════════════
# КОНФИГУРАЦИЯ
# ═══════════════════════════════════════════
BOT_TOKEN        = os.getenv('BOT_TOKEN', '')
YUKASSA_SHOP_ID  = os.getenv('YUKASSA_SHOP_ID', '')
YUKASSA_SECRET   = os.getenv('YUKASSA_SECRET', '')
PUBLIC_URL       = os.getenv('PUBLIC_URL', '')   # https://ваш-проект.railway.app
WEBAPP_URL       = 'https://svetlana-zvezda.netlify.app'
PORT             = int(os.getenv('PORT', 8080))
PRICE            = 990
PRODUCT_NAME     = 'Видео про Миссию Души'

# ═══════════════════════════════════════════
# ССЫЛКИ НА ВИДЕО — заполни ссылки Google Drive
# Формат: аркан: ('ссылка_видео', 'ссылка_pdf')
# ═══════════════════════════════════════════
MISSION_VIDEOS = {
    1:  ('ССЫЛКА_ВИДЕО_1',  'ССЫЛКА_PDF_1'),
    2:  ('ССЫЛКА_ВИДЕО_2',  'ССЫЛКА_PDF_2'),
    3:  ('https://disk.yandex.ru/i/lYLnlOvOmcEyWQ',  'https://disk.yandex.ru/i/MCpa3mJm7ogX8w'),
    4:  ('https://disk.yandex.ru/i/oWzECllPgp5ONw',  'https://disk.yandex.ru/i/G1WEv68-MghnsA'),
    5:  ('https://disk.yandex.ru/i/TmZbVPtKP6XW6g',  'https://disk.yandex.ru/i/4zDSE6FkXopi2Q'),
    6:  ('https://disk.yandex.ru/i/VBXa-ZDyKVdEcg',  'https://disk.yandex.ru/i/c68MgE80N6veuA'),
    7:  ('https://disk.yandex.ru/i/4WB-aY53DU9ntQ',  'https://disk.yandex.ru/i/pwZKL5FTSmuU3Q'),
    8:  ('https://disk.yandex.ru/i/2L9r9JyC-ImeHg',  'https://disk.yandex.ru/i/yvCAlCpHqiNtjg'),
    9:  ('https://disk.yandex.ru/i/gpPxWHiElhD3rQ',  'https://disk.yandex.ru/i/IRuBk9qJQS8HAA'),
    10: ('https://disk.yandex.ru/i/cl0WXnkriJG7TA', 'https://disk.yandex.ru/i/BZGs0VDrczXCOQ'),
    11: ('https://disk.yandex.ru/i/f46FHu7GFvzFPw', 'https://disk.yandex.ru/i/iVW6Di7rj2wjQA'),
    12: ('https://disk.yandex.ru/i/dLKMoVf6iG9AyA', 'https://disk.yandex.ru/i/muZ9IoJbq84W1A'),
    13: ('https://disk.yandex.ru/i/Ig8iuTPHvB5nHQ', 'https://disk.yandex.ru/i/T3_UAWb-cZQbbw'),
    14: ('https://disk.yandex.ru/i/zLAAuQkKGgsfEA', 'https://disk.yandex.ru/i/iqiBue3nMTKBcA'),
    15: ('https://disk.yandex.ru/i/iQqeswSZDl0WWw', 'https://disk.yandex.ru/i/L5HPcwKCzY1o4w'),
    16: ('https://disk.yandex.ru/i/ChBSD8gwYVIbQQ', 'https://disk.yandex.ru/i/CuDpLZ8gQh2YDA'),
    17: ('https://disk.yandex.ru/i/b1HsViFYVAo0Gw', 'https://disk.yandex.ru/i/nXvuFMnsWkyHZw'),
    18: ('https://disk.yandex.ru/i/tanIvQ8-BpqrCg', 'https://disk.yandex.ru/i/ARAoMgEDWGH3Iw'),
    19: ('https://disk.yandex.ru/i/0Dd7PKAX1RWCGQ', 'https://disk.yandex.ru/i/6u3SSquvLfq4SA'),
    20: ('https://disk.yandex.ru/i/g6p-iTg7sCCwrQ', 'https://disk.yandex.ru/i/lVYMLDgUqyxntQ'),
    21: ('https://disk.yandex.ru/i/7gZe3qb9VNw7xw', 'https://disk.yandex.ru/i/vkE-pufJPYACeQ'),
    22: ('https://disk.yandex.ru/i/ZOv_AioR5nEkwA', 'https://disk.yandex.ru/i/Mpk0fsRRVkFDIw'),
}

# ═══════════════════════════════════════════
# ЛОГИРОВАНИЕ
# ═══════════════════════════════════════════
logging.basicConfig(
    format='%(asctime)s [%(levelname)s] %(message)s',
    level=logging.INFO
)
log = logging.getLogger(__name__)

# ═══════════════════════════════════════════
# БАЗА ДАННЫХ (SQLite)
# ═══════════════════════════════════════════
DB = 'bot.db'

def init_db():
    with sqlite3.connect(DB) as c:
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id    INTEGER PRIMARY KEY,
                arcane     INTEGER,
                phone      TEXT,
                payment_id TEXT,
                paid       INTEGER DEFAULT 0
            )
        ''')

def db_save_arcane(user_id, arcane):
    with sqlite3.connect(DB) as c:
        c.execute(
            'INSERT OR REPLACE INTO users (user_id, arcane, paid) VALUES (?,?,0)',
            (user_id, arcane)
        )

def db_save_phone(user_id, phone):
    with sqlite3.connect(DB) as c:
        c.execute('UPDATE users SET phone=? WHERE user_id=?', (phone, user_id))

def db_save_payment(user_id, payment_id):
    with sqlite3.connect(DB) as c:
        c.execute('UPDATE users SET payment_id=? WHERE user_id=?', (payment_id, user_id))

def db_get_user(user_id):
    with sqlite3.connect(DB) as c:
        return c.execute(
            'SELECT user_id, arcane, phone, payment_id, paid FROM users WHERE user_id=?',
            (user_id,)
        ).fetchone()

def db_find_by_payment(payment_id):
    with sqlite3.connect(DB) as c:
        return c.execute(
            'SELECT user_id, arcane FROM users WHERE payment_id=?',
            (payment_id,)
        ).fetchone()

def db_mark_paid(user_id):
    with sqlite3.connect(DB) as c:
        c.execute('UPDATE users SET paid=1 WHERE user_id=?', (user_id,))

# ═══════════════════════════════════════════
# ЮKASSA — создание платежа
# ═══════════════════════════════════════════
def create_yukassa_payment(amount, description, phone, user_id):
    """
    Создаём платёж в ЮKassa с полным чеком.
    Возвращает (payment_id, payment_url) или (None, None) при ошибке.
    """
    # Нормализуем телефон → +7XXXXXXXXXX
    digits = ''.join(filter(str.isdigit, str(phone)))
    if digits.startswith('8'):
        digits = '7' + digits[1:]
    if not digits.startswith('7'):
        digits = '7' + digits
    formatted_phone = f'+{digits}'

    idempotence_key = str(uuid.uuid4())

    payload = {
        "amount": {
            "value": f"{amount}.00",
            "currency": "RUB"
        },
        "capture": True,
        "confirmation": {
            "type": "redirect",
            "return_url": f"https://t.me/numerolog_svetlana_bot"
        },
        "description": description,
        "receipt": {
            "customer": {
                "phone": formatted_phone
            },
            "items": [
                {
                    "description": description,
                    "quantity": "1.00",
                    "amount": {
                        "value": f"{amount}.00",
                        "currency": "RUB"
                    },
                    "vat_code": 1,
                    "payment_mode": "full_payment",
                    "payment_subject": "service"
                }
            ]
        },
        "metadata": {
            "user_id": str(user_id)
        }
    }

    try:
        resp = requests.post(
            'https://api.yookassa.ru/v3/payments',
            json=payload,
            auth=(YUKASSA_SHOP_ID, YUKASSA_SECRET),
            headers={'Idempotence-Key': idempotence_key},
            timeout=10
        )
        if resp.status_code == 200:
            data = resp.json()
            return data['id'], data['confirmation']['confirmation_url']
        else:
            log.error(f"ЮKassa error {resp.status_code}: {resp.text}")
            return None, None
    except Exception as e:
        log.error(f"ЮKassa exception: {e}")
        return None, None

# ═══════════════════════════════════════════
# ОТПРАВКА ВИДЕО (через Bot API напрямую)
# ═══════════════════════════════════════════
def deliver_video(user_id: int, arcane: int):
    """Отправляем видео и PDF пользователю после оплаты."""
    video_url, pdf_url = MISSION_VIDEOS.get(arcane, ('', ''))

    text = (
        f"Оплата прошла ✦\n\n"
        f"Вот твоё видео про Аркан {arcane}:\n"
        f"{video_url}\n\n"
        f"PDF практика:\n"
        f"{pdf_url}\n\n"
        f"Посмотри сегодня — там есть то,\n"
        f"что ты давно чувствовала, но не могла сформулировать.\n\n"
        f"Если появятся вопросы — просто напиши сюда."
    )

    try:
        requests.post(
            f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage',
            json={'chat_id': user_id, 'text': text},
            timeout=10
        )
        log.info(f"Видео отправлено: user={user_id}, arcane={arcane}")
    except Exception as e:
        log.error(f"Ошибка отправки видео: {e}")

# ═══════════════════════════════════════════
# ОБРАБОТЧИКИ TELEGRAM БОТА
# ═══════════════════════════════════════════
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатываем /start — обычный и с параметром mission_N"""
    user_id   = update.effective_user.id
    user_name = update.effective_user.first_name or ''
    args      = context.args  # параметры после /start

    # Пришёл из Mini App: /start mission_5
    if args and args[0].startswith('mission_'):
        try:
            arcane = int(args[0].split('_')[1])
            if 1 <= arcane <= 22:
                db_save_arcane(user_id, arcane)
                await send_mission_offer(update, arcane)
                return
        except (ValueError, IndexError):
            pass

    # Обычный старт — показываем кнопку калькулятора
    greeting = f"Привет, {user_name}!\n\n" if user_name else "Привет!\n\n"

    await update.message.reply_text(
        f"{greeting}"
        "Я — Светлана, нумеролог.\n\n"
        "Нажми кнопку ниже — я рассчитаю "
        "твою Кармическую Звезду по дате рождения.\n\n"
        "Бесплатно. Займёт 1 минуту ✦",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton(
                "Открыть калькулятор ✦",
                web_app=WebAppInfo(url=WEBAPP_URL)
            )
        ]])
    )

async def send_mission_offer(update: Update, arcane: int):
    """Показываем оффер после расчёта миссии."""
    keyboard = ReplyKeyboardMarkup(
        [[KeyboardButton("Поделиться номером 📱", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await update.message.reply_text(
        f"Я рассчитала твою Кармическую Звезду ✦\n\n"
        f"В центре — Миссия Души, Аркан {arcane}.\n\n"
        f"Я записала подробное видео именно про твой аркан — "
        f"12 минут + PDF с практикой активации.\n\n"
        f"Для оформления чека поделись номером телефона:",
        reply_markup=keyboard
    )

async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получили телефон — создаём ссылку на оплату."""
    user_id = update.effective_user.id
    phone   = update.message.contact.phone_number

    db_save_phone(user_id, phone)

    user = db_get_user(user_id)
    if not user or not user[1]:
        await update.message.reply_text(
            "Что-то пошло не так. Попробуй заново через калькулятор.",
            reply_markup=ReplyKeyboardRemove()
        )
        return

    arcane = user[1]

    await update.message.reply_text(
        "Создаю ссылку на оплату...",
        reply_markup=ReplyKeyboardRemove()
    )

    payment_id, payment_url = create_yukassa_payment(PRICE, PRODUCT_NAME, phone, user_id)

    if not payment_url:
        await update.message.reply_text(
            "Ошибка при создании оплаты. Напиши нам — разберёмся! 🙏"
        )
        return

    db_save_payment(user_id, payment_id)

    await update.message.reply_text(
        f"Видео про Аркан {arcane} + PDF практика ✦\n\n"
        f"Стоимость: {PRICE} ₽\n\n"
        f"После оплаты видео придёт сюда автоматически.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton(f"Оплатить {PRICE} ₽ →", url=payment_url)
        ]])
    )

async def handle_webapp_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Данные из Mini App через sendData (запасной путь)."""
    user_id = update.effective_user.id
    try:
        data   = json.loads(update.message.web_app_data.data)
        arcane = int(data.get('arcane', 0))
        if 1 <= arcane <= 22:
            db_save_arcane(user_id, arcane)
            await send_mission_offer(update, arcane)
    except Exception as e:
        log.error(f"WebApp data error: {e}")

# ═══════════════════════════════════════════
# FLASK — WEBHOOK ОТ ЮKASSA
# ═══════════════════════════════════════════
flask_app = Flask(__name__)

@flask_app.route('/yukassa/callback', methods=['POST'])
def yukassa_callback():
    """Принимаем уведомление об успешной оплате."""
    try:
        data = request.json
        log.info(f"ЮKassa webhook: event={data.get('event')}")

        if data.get('event') == 'payment.succeeded':
            payment    = data.get('object', {})
            payment_id = payment.get('id')

            if payment_id:
                row = db_find_by_payment(payment_id)
                if row:
                    user_id, arcane = row
                    db_mark_paid(user_id)
                    # Отправляем видео в отдельном потоке
                    threading.Thread(
                        target=deliver_video,
                        args=(user_id, arcane),
                        daemon=True
                    ).start()

        return jsonify({'status': 'ok'})
    except Exception as e:
        log.error(f"Webhook error: {e}")
        return jsonify({'status': 'error'}), 500

@flask_app.route('/health')
def health():
    return jsonify({'status': 'ok', 'bot': 'svetlana_numerolog'})

# ═══════════════════════════════════════════
# ЗАПУСК
# ═══════════════════════════════════════════
def run_flask():
    flask_app.run(host='0.0.0.0', port=PORT, use_reloader=False)

def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN не задан! Заполни файл .env")
    if not YUKASSA_SHOP_ID or not YUKASSA_SECRET:
        raise RuntimeError("YUKASSA_SHOP_ID / YUKASSA_SECRET не заданы!")

    init_db()
    log.info("База данных инициализирована")

    # Flask в отдельном потоке
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    log.info(f"Flask запущен на порту {PORT}")

    # Telegram бот
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler('start', cmd_start))
    app.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp_data))

    log.info("Бот Светланы запускается... ✦")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
