import random
from typing import Any

import pandas as pd


# Рандомизация по экспоненциальному распределению
def randomize(value: int | float):
    return random.expovariate(1 / value)


# Замена значения границами отрезка (луча),
# если оно не принадлежит таковому
def fit_limit(
    value: float,
    lower: float | None = None,
    upper: float | None = None,
) -> float:
    value = value if lower is None else max(value, lower)
    value = value if upper is None else min(value, upper)
    return value


# Получение элемента из словаря с вероятностями
def dict_weighted_choice(probas: dict[Any, float]):
    return random.choices(list(probas.keys()), weights=list(probas.values()))[0]


# Вспомогательная функция для отладки
def config_debug():
    pd.set_option("display.max_rows", 1000)
    pd.set_option("display.max_columns", 1000)
    pd.set_option("display.width", 1000)
