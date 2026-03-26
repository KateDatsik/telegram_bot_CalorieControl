from __future__ import annotations

import asyncio
import os
import secrets
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from dotenv import load_dotenv

from app.calorie_db import CalorieDB, FoodItem

_PENDING_QUERIES: dict[str, dict[str, list[FoodItem]]] = {}


def _resolve_data_dir(raw_path: str) -> str:
    p = Path(raw_path)
    if p.is_absolute() and p.exists():
        return str(p)

    cwd_candidate = Path.cwd() / p
    if cwd_candidate.exists():
        return str(cwd_candidate)

    project_candidate = Path(__file__).resolve().parent.parent / p
    if project_candidate.exists():
        return str(project_candidate)

    return raw_path


def _env(name: str) -> str:
    load_dotenv()
    v = os.getenv(name)
    if not v:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return v


def _format_item(it: FoodItem) -> str:
    parts = [f"<b>{it.title}</b>"]
    if it.category:
        parts.append(f"<i>{it.category}</i>")
    if it.calories:
        parts.append(f"Калорийность: <b>{it.calories}</b>")
    macros = []
    if it.proteins:
        macros.append(f"Б: {it.proteins}")
    if it.fats:
        macros.append(f"Ж: {it.fats}")
    if it.carbohydrates:
        macros.append(f"У: {it.carbohydrates}")
    if macros:
        parts.append(" / ".join(macros))
    return "\n".join(parts)


def _group_by_category(items: list[FoodItem]) -> dict[str, list[FoodItem]]:
    grouped: dict[str, list[FoodItem]] = {}
    for it in items:
        key = it.category or "Без категории"
        grouped.setdefault(key, []).append(it)
    return grouped


def _build_category_keyboard(query_id: str, grouped: dict[str, list[FoodItem]]) -> InlineKeyboardMarkup:
    buttons: list[list[InlineKeyboardButton]] = []
    for idx, (category, cat_items) in enumerate(grouped.items()):
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"{category} ({len(cat_items)})",
                    callback_data=f"cat:{query_id}:{idx}",
                )
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def main() -> None:
    token = _env("TELEGRAM_BOT_TOKEN")
    data_dir_raw = os.getenv("DATA_DIR") or os.getenv("DARA_DIR") or "data"
    data_dir = _resolve_data_dir(data_dir_raw)
    limit = int(os.getenv("SEARCH_LIMIT", "6"))

    db = CalorieDB.load_from_dir(data_dir)

    bot = Bot(
        token=token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    @dp.message(Command("start"))
    async def start(m: Message) -> None:
        await m.answer(
            "Напиши название продукта или блюда, и я найду калорийность.\n\n"
            "Пример: <code>бургер кинг гамбургер</code>\n"
            "Команда: /help",
        )

    @dp.message(Command("help"))
    async def help_(m: Message) -> None:
        await m.answer(
            "Отправь текстом запрос (часть названия).\n"
            "Если есть несколько категорий, я дам выбрать одну.\n\n"
            "Пример: <code>пицца пепперони</code>",
        )

    @dp.message(F.text)
    async def query(m: Message) -> None:
        text = (m.text or "").strip()
        if not text or text.startswith("/"):
            return

        items = db.search(text, limit=max(limit, 20))
        if not items:
            await m.answer("Ничего не нашёл. Попробуй другое название (или короче).")
            return

        grouped = _group_by_category(items)
        if len(grouped) == 1:
            msg = "\n\n".join(_format_item(it) for it in items[:limit])
            await m.answer(msg)
            return

        query_id = secrets.token_hex(4)
        _PENDING_QUERIES[query_id] = grouped
        keyboard = _build_category_keyboard(query_id, grouped)
        await m.answer("Нашёл в нескольких категориях. Выбери одну:", reply_markup=keyboard)

    @dp.callback_query(F.data.startswith("cat:"))
    async def choose_category(c: CallbackQuery) -> None:
        data = (c.data or "").split(":")
        if len(data) != 3:
            await c.answer("Некорректные данные кнопки", show_alert=True)
            return

        _, query_id, idx_raw = data
        grouped = _PENDING_QUERIES.get(query_id)
        if not grouped:
            await c.answer("Выбор устарел. Введи запрос снова.", show_alert=True)
            return

        try:
            idx = int(idx_raw)
        except ValueError:
            await c.answer("Некорректная категория", show_alert=True)
            return

        categories = list(grouped.items())
        if idx < 0 or idx >= len(categories):
            await c.answer("Категория не найдена", show_alert=True)
            return

        category, cat_items = categories[idx]
        msg = f"<b>Категория:</b> {category}\n\n" + "\n\n".join(
            _format_item(it) for it in cat_items[:limit]
        )
        if c.message:
            await c.message.answer(msg)
        await c.answer()

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

