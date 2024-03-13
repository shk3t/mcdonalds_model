from __future__ import annotations

import random
from dataclasses import dataclass
from enum import Enum
from typing import Self

from utils import dict_weighted_choice, randomize


@dataclass
class MenuItem:
    name: str
    cooking_time: float
    popularity: int

    def __str__(self) -> str:
        return self.name


class MenuItemTypeError(TypeError):
    def __init__(self, *_):
        super().__init__("You can use only `MenuItem` instances as class attributes")


class MenuMeta(type):
    items: list[MenuItem]

    def __new__(cls, name, bases, attrs, **_):
        for k, v in attrs.items():
            if (
                not k.startswith("__")
                and not (callable(v) or callable(getattr(v, "__func__", None)))
                and not isinstance(v, MenuItem)
            ):
                raise MenuItemTypeError

            MenuClass = super().__new__(cls, name, bases, attrs)
            MenuClass.items = [
                x for x in MenuClass.__dict__.values() if isinstance(x, MenuItem)
            ]
        return MenuClass


class Menu(metaclass=MenuMeta):
    def __setattr__(self, name: str, value: MenuItem):
        if not isinstance(value, MenuItem):
            raise MenuItemTypeError
        self.__dict__[name] = value

    @classmethod
    def generate_items(cls, amount: int = 1) -> list[MenuItem]:
        return random.choices(
            cls.items, weights=[x.popularity for x in cls.items], k=amount
        )


class DefaultMenu(Menu):
    cheeseburger = MenuItem("Чизбургер", 20.0, 50)
    big_mac = MenuItem("Биг Мак", 40.0, 60)
    big_tasty = MenuItem("Биг Тейсти", 60.0, 40)
    shrimp_roll = MenuItem("Шримп Ролл", 80.0, 10)
    french_fries = MenuItem("Картофель Фри", 10.0, 100)
    coca_cola = MenuItem("Кока-Кола", 8.0, 130)


@dataclass
class Order:
    class Type(str, Enum):
        terminal = "terminal"
        cashier = "cashier"
        online = "online"

    type: Type
    need_bring: bool
    items: list[MenuItem]

    @classmethod
    def generate(
        cls,
        type_probas: dict[Order.Type, float],
        need_bring_proba: float,
        avg_size: float,
        menu: Menu,
    ) -> Self:
        return cls(
            type=dict_weighted_choice(type_probas),
            need_bring=need_bring_proba < random.random(),
            items=menu.generate_items(amount=round(randomize(avg_size))),
        )
