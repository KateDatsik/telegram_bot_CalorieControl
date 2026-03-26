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

### Обновление данных (e-dostavka.by)

`main.py` парсит `edostavka.by` (aiohttp + BeautifulSoup) и пишет данные в формат, совместимый с ботом:

- `data/*.json`
- `data/*.csv`

Пример запуска:

```bash
python3 main.py
```

Быстрый тест:

```bash
MAX_CATEGORIES=1 MAX_PAGES_PER_CATEGORY=1 MAX_PRODUCTS_PER_CATEGORY=5 python3 main.py
```
