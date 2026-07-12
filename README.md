# ♥️ LOVER — Telegram-бот Lavrelin

Бот на aiogram 3 с меню на инлайн-кнопках, разделом предложений с модерацией,
розыгрышами и рассылками. Все ссылки, ID и токен берутся из переменных
окружения — ничего не захардкожено в коде.

## Структура проекта

```
config.py                     # загрузка настроек из .env
main.py                       # точка входа, сборка бота
database/
  models.py                   # таблицы: User, Suggestion, Raffle, RaffleParticipant, ActualInfo, BroadcastLog
  engine.py                   # async engine + сессии, SQLite по умолчанию
  requests.py                 # все запросы к БД в одном месте
handlers/
  user/                       # /start, Контент, Предложить, Розыгрыш, Актуальное, Уведомления
  admin/                      # /write /ban /unban /baninfo /mute /unmute /stats
                               # /givestart /giveinfo /editactual /notsend
  moderation/                 # кнопки Одобрить/Отклонить в модер-группе
keyboards/                    # все инлайн-клавиатуры
utils/
  texts.py                    # весь текст бота, включая 99 приветствий
  states.py                   # FSM-состояния
  scheduler.py                # автозавершение розыгрышей по таймеру (APScheduler)
middlewares/
  access.py                   # только личные сообщения + бан/мьют
```

## Как добавлять новый функционал

Проект специально разложен по маленьким файлам, чтобы новый раздел не задевал
остальные:
1. Новый текст → `utils/texts.py`.
2. Новая клавиатура → отдельный файл в `keyboards/`.
3. Новый обработчик → отдельный файл в `handlers/user/` или `handlers/admin/`,
   затем одна строка `dp.include_router(...)` в `main.py`.
4. Новая таблица → `database/models.py` + функции в `database/requests.py`.

## Запуск локально

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # впиши свои значения, если нужно поменять
python main.py
```

## Деплой на Railway

1. Залей проект в GitHub-репозиторий.
2. Создай новый проект на Railway → Deploy from GitHub repo.
3. В Variables добавь все переменные из `.env.example` (токен уже указан
   в примере — при желании смени на новый через @BotFather).
4. Railway подхватит `railway.json` / `Procfile` и запустит `python main.py`
   как воркер (long polling, вебхук не нужен).
5. По умолчанию используется SQLite-файл `bot.db` — он живет только пока жив
   контейнер. Если нужно постоянное хранилище, подключи Railway Postgres
   плагин и пропиши его `DATABASE_URL` (формат
   `postgresql+asyncpg://user:pass@host:5432/db`) — код это уже поддерживает.

## Админ-команды

| Команда | Действие |
|---|---|
| `/write <id\|@username> текст` | Отправить сообщение пользователю от бота |
| `/ban <id\|@username>` | Забанить (бот попросит указать причину) |
| `/unban <id\|@username>` | Разбанить |
| `/baninfo <id\|@username>` | Показать причину бана |
| `/mute <id\|@username> [минуты]` | Замьютить (по умолчанию 60 мин) |
| `/unmute <id\|@username>` | Снять мьют |
| `/stats` | Статистика бота, канала, группы, розыгрышей, уведомлений |
| `/givestart` | Пошаговое создание розыгрыша |
| `/giveinfo` | Показать / отредактировать текущий розыгрыш |
| `/editactual` | Изменить текст раздела «Актуальное» |
| `/notsend` | Разослать сообщение всем, у кого включены уведомления |

Админы определяются переменной `ADMIN_IDS` в `.env` (через запятую).

## Важно про токен

В `.env.example` уже вписан токен из твоего сообщения — для безопасности
советую после первого теста перевыпустить токен через @BotFather
(`/revoke`), если он уже где-то "засветился".
