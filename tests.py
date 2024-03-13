import numpy as np
import pandas as pd
from pandas import DataFrame

from models import DefaultMenu, MenuItem
from systems import McDonalds


def test_system_wait_time(
    terminals: int | float,
    services: int | float,
    chefs: int | float,
    params: McDonalds.Parameters | None = None,
) -> int:
    parameters = dict(
        terminals=terminals,
        services=services,
        chefs=chefs,
        # params=params,
    )
    # Настройка среды
    # random.seed(42)

    # Настройка ресторана
    mcdonalds = McDonalds(**parameters)  # type: ignore

    # Запуск моделирования
    mcdonalds.run(until=24 * 60 * 60)

    # Просмотр результатов
    avg_wait_mins, avg_wait_secs = mcdonalds.avg_wait_time
    print(
        f"Для параметров {parameters} имеем:",
        f"    Среднее время ожидания: {avg_wait_mins}:{avg_wait_secs:02}",
        sep="\n",
        end="\n\n",
    )

    return avg_wait_mins * 60 + avg_wait_secs


def make_some_factor_plan_dataset(filename_for_save: str | None = None):
    factors = [
        dict(
            terminals=terminals,
            services=services,
            chefs=chefs,
            terminal_order_proba=terminal_order_proba,
            order_size=order_size,
            big_tasty_popularity=big_tasty_popularity,
        )
        for terminals in (2, 8)
        for services in (2, 8)
        for chefs in (2, 8)
        for terminal_order_proba in (0.25, 1.0)
        for order_size in (2, 8)
        for big_tasty_popularity in (20, 80)
    ]

    my_menu = DefaultMenu()

    for factor in factors:
        my_menu.big_tasty = MenuItem(
            "Биг Тейсти", 60.0, popularity=int(factor["big_tasty_popularity"])
        )

        factor["wait_time"] = test_system_wait_time(
            terminals=factor["terminals"],
            services=factor["services"],
            chefs=factor["chefs"],
            params=McDonalds.Parameters(
                request_timeout=30.0,
                terminal_order_proba=factor["terminal_order_proba"],
                order_size=factor["order_size"],
                menu=my_menu,
            ),
        )

    factor_plan = DataFrame(factors)

    if filename_for_save:
        factor_plan.to_csv("./output/" + filename_for_save, index=False)

    return factor_plan


def dataset_to_factor_plan(dataset: DataFrame) -> DataFrame:
    factors, response = dataset.iloc[:, :-1], dataset.iloc[:, -1:]
    factors[factors == factors.min()] *= -1
    factors /= np.abs(factors)
    return pd.concat([factors, response], axis=1)


def do_factor_analysis(factor_plan: DataFrame) -> tuple[dict, dict]:
    main_effects: dict[str, float] = {}
    interaction_effects: dict[tuple[str, str], float] = {}

    for factor in factor_plan.iloc[:, :-1]:
        main_effects[factor] = (
            factor_plan[factor] * factor_plan.iloc[:, -1] / (factor_plan.shape[0] / 2)
        ).sum()

    for i, factor_i in enumerate(factor_plan.columns[:-1]):
        for factor_j in factor_plan.columns[(i + 1) : -1]:
            interaction_effects[(factor_i, factor_j)] = (
                factor_plan[factor_i]
                * factor_plan[factor_j]
                * factor_plan.iloc[:, -1]
                / (factor_plan.shape[0] / 2)
            ).sum()

    return main_effects, interaction_effects
