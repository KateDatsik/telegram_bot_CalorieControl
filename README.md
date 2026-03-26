## Telegram бот калорийности (Docker)

Бот принимает запрос (продукт/блюдо), ищет совпадения в `data/*.json` и возвращает калорийность и КБЖУ.

### Запуск бота

1. Подготовьте `.env`:

```bash
cp .env.example .env
```

2. Укажите токен:

```env
TELEGRAM_BOT_TOKEN=123456:ABC...
```

3. Запустите контейнер:

```bash
docker compose up --build
```

### Обновление данных (health-diet.ru)

`main.py` парсит `health-diet.ru` (BeautifulSoup) и пишет данные в формат, совместимый с ботом:

- `data/*.json`
- `data/*.csv`
