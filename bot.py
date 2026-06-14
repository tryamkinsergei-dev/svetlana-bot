"""
Бот Светланы — Кармическая Звезда
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

BOT_TOKEN       = os.getenv('BOT_TOKEN', '')
YUKASSA_SHOP_ID = os.getenv('YUKASSA_SHOP_ID', '')
YUKASSA_SECRET  = os.getenv('YUKASSA_SECRET', '')
WEBAPP_URL      = 'https://svetlana-zvezda.netlify.app'
PORT            = int(os.getenv('PORT', 8080))
PRICE           = 990
PRODUCT_NAME    = 'Видео про Миссию Души'
ADMIN_IDS       = [275673546]

# ═══ ССЫЛКИ НА ВИДЕО ═══
# Как заполнить:
# 1. Отправь видео/PDF боту в личку
# 2. Бот пришлёт file_id
# 3. Вставь file_id сюда
MISSION_VIDEOS = {
    1:  ('', ''),
    2:  ('', ''),
    3:  ('BAACAgIAAxkBAAICkGouiczrE7E7vse_EFuB7bme9XguAAJVpwAC2RV5SYzfZ_CC5h9rPAQ', 'BQACAgIAAxkBAAICkmoujf94UdWBY-60v4czL5V7l-ttAAKBpwAC2RV5SQuyQx1CtqwRPAQ'),
    4:  ('BAACAgIAAxkBAAIClGoujwnnZoVYoiDmrAYESkIJTl_UAAKRpwAC2RV5SRj87uTu6388PAQ', 'BQACAgIAAxkBAAIClmoujx5A7EOXcZGKS4tn0fVRjbkSAAKSpwAC2RV5SUjg45FcJj9lPAQ'),
    5:  ('BQACAgIAAxkBAAICmGouj3EG1xlSHZym2ozexGeGhni4AAKXpwAC2RV5SZwKjg4WmAABOjwE', 'BQACAgIAAxkBAAICmmouj4P-k_XRfuhr6MWF-wnDA5QwAAKZpwAC2RV5STMZk3OxHoucPAQ'),
    6:  ('BAACAgIAAxkBAAICnGoukAijyl0Le2TD19PixOMbXh1wAAKcpwAC2RV5SRwsdwp__6nCPAQ', 'BQACAgIAAxkBAAICnmoukBktPcumZaNSg_qpWf5WeOVTAAKepwAC2RV5SeqQ2BFJ2ZsUPAQ'),
    7:  ('BAACAgIAAxkBAAICoGoukG7gmPpc9lSMknT3Juu_8GfpAAKjpwAC2RV5SVvrzjt8xFYaPAQ', 'BQACAgIAAxkBAAIComoukHYPfTFTLrxTYWRUDAKXWe_-AAKkpwAC2RV5Sa-NFdoGowWUPAQ'),
    8:  ('BAACAgIAAxkBAAICpGoukMe7x0qoU6N-ceJngiB1s2m8AAKmpwAC2RV5Scukn78dMKBsPAQ', 'BQACAgIAAxkBAAICpmoukOR3I5uLM7beSlDkAAEcm3c8nAACp6cAAtkVeUnjpu5lZCqgnzwE'),
    9:  ('BAACAgIAAxkBAAICqGoukSZQh7x3pyUVUql_4LZhea8JAAKqpwAC2RV5STrWNL3lB2TGPAQ', 'BQACAgIAAxkBAAICqmoukTza05jfttv01tou6BDF4xKbAAKspwAC2RV5SdYxh170reZMPAQ'),
    10: ('BAACAgIAAxkBAAICrGoukXySkLU8jmFEYeRM-0_Vh8RRAAKvpwAC2RV5SUrreD1rS8sjPAQ', 'BQACAgIAAxkBAAICrmoukZavtI0QfKk9V6D6AfiL7YQrAAKxpwAC2RV5SW1xqH8DvMFzPAQ'),
    11: ('BAACAgIAAxkBAAICsGoukbD8OU-1tRmjHola4JvfAAGmXAACs6cAAtkVeUntXclpbDvUkzwE', 'BQACAgIAAxkBAAICsmoukbye3COiRx6EdH5DE9tmR2BVAAK0pwAC2RV5SRVlNakrjSLsPAQ'),
    12: ('BAACAgIAAxkBAAICtGoukgFZgALoKCzKCdiXZ4r0TJBmAAK2pwAC2RV5Scv8rmTwLJ4mPAQ', 'BQACAgIAAxkBAAICtmoukgzwipf3_OgCYCHerkZRuvlYAAK4pwAC2RV5SU7Erst60_btPAQ'),
    13: ('BAACAgIAAxkBAAICuGouklQ6kFeT1pAC2b4FcOmKLHK_AAK8pwAC2RV5Se5duemkgt7sPAQ', 'BQACAgIAAxkBAAICumoukl2EzoAvXEEC_Uj_I0CynRAYAAK9pwAC2RV5SYncZgAB3sm-OjwE'),
    14: ('BAACAgIAAxkBAAICvGoukqeG0qeSo1dsFH5l-BpdQqvVAALBpwAC2RV5SbeaZJA440GXPAQ', 'BQACAgIAAxkBAAICvmoukrooB3o1GLvZC78mYs0pAy2tAALCpwAC2RV5SUKaVljgIWoiPAQ'),
    15: ('BAACAgIAAxkBAAICwmoukwZdWaFFEWN2za5c-vWWuMfoAALEpwAC2RV5SfpjSkzNzeY7PAQ', 'BQACAgIAAxkBAAICxGoukxNWuwg3pdYOZQPOe4ddV87QAALFpwAC2RV5SXpJpS3szqkaPAQ'),
    16: ('BAACAgIAAxkBAAICxmouk11C8Abge0yA-GN48GTlqGbvAALIpwAC2RV5SSkRUKEUwzsmPAQ', 'BQACAgIAAxkBAAICyGouk4d3zSLd8WpUX62gKZlhIZnhAALKpwAC2RV5SRIGyOLlowaSPAQ'),
    17: ('BAACAgIAAxkBAAICymouk9CsR0r_9Spa-ix8gTJ8YzWVAALRpwAC2RV5SUR6ya7TNo1wPAQ', 'BQACAgIAAxkBAAICzGouk-Khs7pAWFtl65ykab1xIGcsAALUpwAC2RV5SUdl6SuuxZ7APAQ'),
    18: ('BAACAgIAAxkBAAICzmoulFC92zFM2jnZppxD4wbXXg_nAALXpwAC2RV5Se8WPizJjtdKPAQ', 'BQACAgIAAxkBAAIC0GoulGA1w9okBxAQKp3fgxzAf4jvAALYpwAC2RV5SXHRAAGI-CqF8TwE'),
    19: ('BAACAgIAAxkBAAIC0moulMHt6qiBWvcQtNlDZA6A06okAALepwAC2RV5SXLDsOsxf7hiPAQ', 'BQACAgIAAxkBAAIC1GoulNAYoZXRAUZGgs_eDGpqkhEYAALfpwAC2RV5SSawd6IauKd0PAQ'),
    20: ('BAACAgIAAxkBAAIC1moulSTTaU38QQpulEbBiIMTXN4qAALipwAC2RV5SUO3-AaF_ObpPAQ', 'BQACAgIAAxkBAAIC2GoulTpq1PtD34x3B5WsdCv4a-kvAALjpwAC2RV5Sahql-mfl-ITPAQ'),
    21: ('BAACAgIAAxkBAAIC2moulZUDVw06NVTaxrhRaqf_HWLwAALppwAC2RV5SQL-35PZepzePAQ', 'BQACAgIAAxkBAAIC3GoulaE8CzjLI1uedd4KUi58P4y0AALqpwAC2RV5SRNDKAle2wABqTwE'),
    22: ('BAACAgIAAxkBAAIC3moulfZZPkNfjQEYugGqUJBeygS7AALvpwAC2RV5SVgnF7JwDVsdPAQ', 'BQACAgIAAxkBAAIC4GoulgPKtZrW4I2sWjJx73Apx0WfAALwpwAC2RV5SR_m-duVd5ZlPAQ'),
}

logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s', level=logging.INFO)
log = logging.getLogger(__name__)

DB = 'bot.db'

def init_db():
    with sqlite3.connect(DB) as c:
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY, arcane INTEGER,
            phone TEXT, payment_id TEXT, paid INTEGER DEFAULT 0)''')

def db_save_arcane(uid, arc):
    with sqlite3.connect(DB) as c:
        c.execute('INSERT OR REPLACE INTO users (user_id,arcane,paid) VALUES(?,?,0)', (uid,arc))

def db_save_phone(uid, ph):
    with sqlite3.connect(DB) as c:
        c.execute('UPDATE users SET phone=? WHERE user_id=?', (ph,uid))

def db_save_payment(uid, pid):
    with sqlite3.connect(DB) as c:
        c.execute('UPDATE users SET payment_id=? WHERE user_id=?', (pid,uid))

def db_get_user(uid):
    with sqlite3.connect(DB) as c:
        return c.execute('SELECT user_id,arcane,phone,payment_id,paid FROM users WHERE user_id=?',(uid,)).fetchone()

def db_find_by_payment(pid):
    with sqlite3.connect(DB) as c:
        return c.execute('SELECT user_id,arcane FROM users WHERE payment_id=?',(pid,)).fetchone()

def db_mark_paid(uid):
    with sqlite3.connect(DB) as c:
        c.execute('UPDATE users SET paid=1 WHERE user_id=?',(uid,))

def create_yukassa_payment(amount, description, phone, user_id):
    digits = ''.join(filter(str.isdigit, str(phone)))
    if digits.startswith('8'): digits = '7'+digits[1:]
    if not digits.startswith('7'): digits = '7'+digits
    payload = {
        "amount": {"value": f"{amount}.00", "currency": "RUB"},
        "capture": True,
        "confirmation": {"type": "redirect", "return_url": "https://t.me/numerolog_svetlana_bot"},
        "description": description,
        "receipt": {
            "customer": {"phone": f"+{digits}"},
            "tax_system_code": 2,
            "items": [{"description": description, "quantity": "1.00",
                "amount": {"value": f"{amount}.00", "currency": "RUB"},
                "vat_code": 1, "payment_mode": "full_payment", "payment_subject": "service"}]
        },
        "metadata": {"user_id": str(user_id)}
    }
    try:
        r = requests.post('https://api.yookassa.ru/v3/payments', json=payload,
            auth=(YUKASSA_SHOP_ID, YUKASSA_SECRET),
            headers={'Idempotence-Key': str(uuid.uuid4())}, timeout=10)
        if r.status_code == 200:
            d = r.json()
            return d['id'], d['confirmation']['confirmation_url']
        log.error(f"ЮKassa {r.status_code}: {r.text}")
    except Exception as e:
        log.error(f"ЮKassa exception: {e}")
    return None, None

def send_tg(method, data):
    requests.post(f'https://api.telegram.org/bot{BOT_TOKEN}/{method}', json=data, timeout=30)

def deliver_video(user_id, arcane):
    video_id, pdf_id = MISSION_VIDEOS.get(arcane, ('',''))
    send_tg('sendMessage', {'chat_id': user_id,
        'text': f"Оплата прошла ✦\n\nОтправляю твоё видео про Аркан {arcane}..."})
    if video_id:
        send_tg('sendVideo', {'chat_id': user_id, 'video': video_id,
            'caption': f'✦ Видео — Аркан {arcane}', 'supports_streaming': True})
    if pdf_id:
        send_tg('sendDocument', {'chat_id': user_id, 'document': pdf_id,
            'caption': '✦ PDF практика активации'})
    send_tg('sendMessage', {'chat_id': user_id,
        'text': "Посмотри сегодня — там есть то,\n"
                "что ты давно чувствовала, но не могла сформулировать.\n\n"
                "Если появятся вопросы — просто напиши сюда ✦"})
    log.info(f"Видео выдано: user={user_id}, arcane={arcane}")

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    name = update.effective_user.first_name or ''
    args = context.args
    if args and args[0].startswith('mission_'):
        try:
            arc = int(args[0].split('_')[1])
            if 1 <= arc <= 22:
                db_save_arcane(uid, arc)
                await send_offer(update, arc)
                return
        except: pass
    await update.message.reply_text(
        f"Привет{', '+name if name else ''}!\n\n"
        "Я — Светлана, нумеролог.\n\n"
        "Нажми кнопку ниже — я рассчитаю "
        "твою Кармическую Звезду по дате рождения.\n\n"
        "Бесплатно. Займёт 1 минуту ✦",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("Открыть калькулятор ✦", web_app=WebAppInfo(url=WEBAPP_URL))
        ]]))

async def send_offer(update, arcane):
    await update.message.reply_text(
        f"Я рассчитала твою Кармическую Звезду ✦\n\n"
        f"В центре — Миссия Души, Аркан {arcane}.\n\n"
        f"Я записала подробное видео именно про твой аркан — "
        f"12 минут + PDF с практикой активации.\n\n"
        f"Для оформления чека поделись номером телефона:",
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("Поделиться номером 📱", request_contact=True)]],
            resize_keyboard=True, one_time_keyboard=True))

async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid   = update.effective_user.id
    phone = update.message.contact.phone_number
    db_save_phone(uid, phone)
    user  = db_get_user(uid)
    if not user or not user[1]:
        await update.message.reply_text("Попробуй заново через калькулятор.", reply_markup=ReplyKeyboardRemove())
        return
    arcane = user[1]
    await update.message.reply_text("Создаю ссылку на оплату...", reply_markup=ReplyKeyboardRemove())
    pid, url = create_yukassa_payment(PRICE, PRODUCT_NAME, phone, uid)
    if not url:
        await update.message.reply_text("Ошибка при создании оплаты. Напиши нам — разберёмся! 🙏")
        return
    db_save_payment(uid, pid)
    await update.message.reply_text(
        f"Видео про Аркан {arcane} + PDF практика ✦\n\n"
        f"Стоимость: {PRICE} ₽\n\nПосле оплаты видео придёт сюда автоматически.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"Оплатить {PRICE} ₽ →", url=url)]]))

async def handle_webapp_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    try:
        data = json.loads(update.message.web_app_data.data)
        # Поддерживаем оба формата: {arcane: N} и {action: 'buy_mission', arcane: N}
        arc  = int(data.get('arcane', 0))
        if 1 <= arc <= 22:
            db_save_arcane(uid, arc)
            await send_offer(update, arc)
    except Exception as e:
        log.error(f"WebApp error: {e}")

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Для Светланы/Сергея — получить file_id отправленного файла."""
    uid = update.effective_user.id
    if uid not in ADMIN_IDS:
        return
    msg = update.message
    if msg.video:
        fid = msg.video.file_id
        await msg.reply_text(f"📹 VIDEO file\_id:\n`{fid}`", parse_mode='Markdown')
    elif msg.document:
        fid  = msg.document.file_id
        name = msg.document.file_name or 'файл'
        await msg.reply_text(f"📄 DOCUMENT file\_id \({name}\):\n`{fid}`", parse_mode='Markdown')

flask_app = Flask(__name__)

@flask_app.route('/yukassa/callback', methods=['POST'])
def yukassa_callback():
    try:
        data = request.json
        if data.get('event') == 'payment.succeeded':
            pid = data.get('object', {}).get('id')
            if pid:
                row = db_find_by_payment(pid)
                if row:
                    uid, arc = row
                    db_mark_paid(uid)
                    threading.Thread(target=deliver_video, args=(uid,arc), daemon=True).start()
        return jsonify({'status': 'ok'})
    except Exception as e:
        log.error(f"Webhook error: {e}")
        return jsonify({'status': 'error'}), 500

@flask_app.route('/health')
def health():
    return jsonify({'status': 'ok'})

def run_flask():
    flask_app.run(host='0.0.0.0', port=PORT, use_reloader=False)

def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN не задан!")
    init_db()
    threading.Thread(target=run_flask, daemon=True).start()
    log.info(f"Flask на порту {PORT}")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler('start', cmd_start))
    app.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp_data))
    app.add_handler(MessageHandler(filters.VIDEO | filters.Document.ALL, handle_file))
    log.info("Бот запускается... ✦")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
