# Бот Светланы — Кармическая Звезда

## Быстрый запуск на Railway

### Шаг 1 — Подготовь файлы
1. Скачай все файлы из этой папки
2. Скопируй `.env.example` в `.env`
3. Заполни `.env` своими данными

### Шаг 2 — Зарегистрируйся на Railway
1. Зайди на railway.app
2. Создай аккаунт через GitHub

### Шаг 3 — Задеплой бота
1. Нажми "New Project" → "Deploy from GitHub"
2. Или: "New Project" → "Empty Project" → "Add Service" → "GitHub Repo"
3. Загрузи файлы проекта

### Шаг 4 — Добавь переменные окружения
В Railway: Settings → Variables → добавь:
- BOT_TOKEN
- YUKASSA_SHOP_ID  
- YUKASSA_SECRET
- PUBLIC_URL (после деплоя Railway даст URL)

### Шаг 5 — Настрой webhook ЮKassa
В личном кабинете ЮKassa → Интеграция → HTTP-уведомления:
```
https://твой-проект.railway.app/yukassa/callback
```

### Шаг 6 — Заполни ссылки на видео
В файле bot.py найди раздел MISSION_VIDEOS
и замени 'ССЫЛКА_ВИДЕО_N' на реальные ссылки Google Drive

## Структура файлов
```
bot.py           — основной файл бота
requirements.txt — зависимости Python
Procfile         — команда запуска для Railway
.env             — твои секретные ключи (не публикуй!)
.env.example     — пример файла .env
```

## Поток пользователя
```
Instagram → t.me/numerolog_svetlana_bot
  ↓
/start → кнопка "Открыть калькулятор"
  ↓
Mini App (svetlana-zvezda.netlify.app)
  ↓
Пользователь вводит дату → видит звезду → нажимает на Миссию
  ↓
"Получить видео про Аркан N — 990₽"
  ↓
Бот просит телефон → создаёт платёж ЮKassa
  ↓
Пользователь платит
  ↓
ЮKassa webhook → бот отправляет видео
```
