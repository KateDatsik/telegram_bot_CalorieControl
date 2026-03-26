from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

_SPACE_RE = re.compile(r"\s+")
_NON_ALNUM_RE = re.compile(r"[^0-9a-zа-яё]+", re.IGNORECASE)


def _norm(text: str) -> str:
    text = text.strip().lower()
    text = _NON_ALNUM_RE.sub(" ", text)
    text = _SPACE_RE.sub(" ", text).strip()
    return text


@dataclass(frozen=True)
class FoodItem:
    title: str
    calories: str
    proteins: str
    fats: str
    carbohydrates: str
    category: str | None = None
    source_file: str | None = None

    @property
    def title_norm(self) -> str:
        return _norm(self.title)


class CalorieDB:
    def __init__(self, items: list[FoodItem]) -> None:
        self._items = items

    @staticmethod
    def load_from_dir(data_dir: str | os.PathLike) -> "CalorieDB":
        base = Path(data_dir)
        if not base.exists() or not base.is_dir():
            raise FileNotFoundError(f"Data dir not found: {base}")

        items: list[FoodItem] = []
        for p in sorted(base.glob("*.json")):
            category = _guess_category_from_filename(p.name)
            items.extend(_load_items_from_json(p, category=category))

        return CalorieDB(items)

    def search(self, query: str, limit: int = 8) -> list[FoodItem]:
        q = _norm(query)
        if not q:
            return []

        scored: list[tuple[int, FoodItem]] = []
        for it in self._items:
            t = it.title_norm
            if q == t:
                score = 0
            elif t.startswith(q):
                score = 1
            elif q in t:
                score = 2
            else:
                continue
            scored.append((score, it))

        scored.sort(key=lambda x: (x[0], len(x[1].title)))
        return [it for _, it in scored[:limit]]


def _guess_category_from_filename(filename: str) -> str | None:
    name = filename
    if name.lower().endswith(".json"):
        name = name[:-5]
    if "_" in name:
        _, rest = name.split("_", 1)
        rest = rest.strip()
        return rest or None
    return None


def _load_items_from_json(path: Path, category: str | None) -> Iterable[FoodItem]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []

    if not isinstance(raw, list):
        return []

    for obj in raw:
        if not isinstance(obj, dict):
            continue
        title = str(obj.get("Title", "")).strip()
        calories = str(obj.get("Calories", "")).strip()
        proteins = str(obj.get("Proteins", "")).strip()
        fats = str(obj.get("Fats", "")).strip()
        carbohydrates = str(obj.get("Carbohydrates", "")).strip()
        if not title:
            continue
        yield FoodItem(
            title=title,
            calories=calories,
            proteins=proteins,
            fats=fats,
            carbohydrates=carbohydrates,
            category=category,
            source_file=path.name,
        )

