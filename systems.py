from __future__ import annotations

import statistics
from dataclasses import dataclass, field

import simpy
from simpy import Environment, Event, Resource

from models import DefaultMenu, Menu, MenuItem, Order
from utils import fit_limit, randomize

# Базовый класс для создания систем массового обслуживания
class QueuingSystem:
    @dataclass
    class Statistics:
        use_time: float = 0.0  # Время использования системы
        wait_times: list[float] = field(
            default_factory=list
        )  # Время обслуживания заявок
        request_counts: list[float] = field(
            default_factory=list
        )  # Число требований в разное время
        active_time: float = 0.0

    # Ресурсы системы
    @dataclass
    class Resources:
        pass

    # Параметры системы
    @dataclass
    class Parameters:
        request_timeout: float = 0.0

    def __init__(self):
        self.env = simpy.Environment()  # Задание среды
        self.stats = self.Statistics()  # Статистические данные

    # Метод для рассчета коэффицицента использования системы
    @property
    def avg_load(self):
        return round(self.stats.use_time / self.stats.active_time, 4)

    # Метод для рассчета среднего времени ожидания
    @property
    def avg_wait_time(self):
        average_wait = round(statistics.mean(self.stats.wait_times))
        return divmod(average_wait, 60)

    # Метод для рассчета среднего числа требований в системе
    @property
    def avg_requests(self):
        return round(statistics.mean(self.stats.request_counts), 4)

    def _run(self):
        yield Event(self.env)

    def run(self, until):
        self.env.process(self._run())
        self.env.run(until=until)
        self.stats.active_time = int(self.env.now)


# Класс исследуемой системы массового обслуживания
class McDonalds(QueuingSystem):
    @dataclass
    class Resources:
        def __init__(self, env: Environment, terminals: int, services: int, chefs: int):
            self.terminals: Resource = Resource(env, int(fit_limit(terminals, 1)))
            self.services: Resource = Resource(env, int(fit_limit(services, 1)))
            self.chefs: Resource = Resource(env, int(fit_limit(chefs, 1)))

    @dataclass
    class Parameters:
        def __init__(
            self,
            request_timeout: float = 60.0,
            terminal_order_time: float = 90.0,
            cashier_order_time: float = 60.0,
            collect_order_time_per_item: float = 5.0,
            bring_order_time: float = 30.0,
            terminal_order_proba: float = 0.5,
            cashier_order_proba: float = 0.3,
            online_order_proba: float = 0.2,
            need_bring_proba: float = 0.5,
            order_size: float = 3.5,
            menu: Menu | None = None,
        ):
            self.request_timeout: float = fit_limit(request_timeout, 0.0001)
            self.terminal_order_time: float = fit_limit(terminal_order_time, 0)
            self.cashier_order_time: float = fit_limit(cashier_order_time, 0)
            self.collect_order_time_per_item: float = fit_limit(
                collect_order_time_per_item, 0
            )
            self.bring_order_time: float = fit_limit(bring_order_time, 0)

            terminal_order_proba = fit_limit(terminal_order_proba, 0, 1)
            cashier_order_proba = fit_limit(cashier_order_proba, 0, 1)
            online_order_proba = fit_limit(online_order_proba, 0, 1)
            sum_order_type_proba = (
                terminal_order_proba + cashier_order_proba + online_order_proba
            )
            self.terminal_order_proba: float = (
                terminal_order_proba / sum_order_type_proba
            )
            self.cashier_order_proba: float = cashier_order_proba / sum_order_type_proba
            self.online_order_proba: float = online_order_proba / sum_order_type_proba
            self.need_bring_proba: float = fit_limit(need_bring_proba, 0, 1)

            self.order_size: float = fit_limit(order_size, 1)
            self.menu: Menu = menu or DefaultMenu()

    def __init__(
        self,
        terminals: int,
        services: int,
        chefs: int,
        params: McDonalds.Parameters | None = None,
    ):
        super().__init__()
        self.res = self.Resources(
            self.env, terminals=terminals, services=services, chefs=chefs
        )
        self.params = params or self.Parameters()

    # Сгенерировать случайный вероятный заказ, соответствующий параметрам системы
    def generate_order(self) -> Order:
        params = self.params
        return Order.generate(
            type_probas={
                Order.Type.terminal: params.terminal_order_proba,
                Order.Type.cashier: params.cashier_order_proba,
                Order.Type.online: params.online_order_proba,
            },
            need_bring_proba=params.need_bring_proba,
            avg_size=params.order_size,
            menu=params.menu,
        )

    # Заказать через терминал
    def order_via_terminal(self):
        yield self.env.timeout(randomize(self.params.terminal_order_time))

    # Заказать через кассу
    def order_via_cashier(self):
        yield self.env.timeout(randomize(self.params.cashier_order_time))

    # Заказть онлайн
    def order_online(self):
        yield self.env.timeout(0)

    # Приготовить пункт меню
    def cook_menu_item(self, item: MenuItem):
        yield self.env.timeout(randomize(item.cooking_time))

    # Собрать заказ
    def collect_order(self, order_size: int):
        yield self.env.timeout(
            randomize(order_size * self.params.collect_order_time_per_item)
        )

    # Принести заказ
    def bring_order(self):
        yield self.env.timeout(randomize(self.params.bring_order_time))

    # Процесс заказа
    def order_food(self):
        # Используется для подсчета времени, сколько ожидал клиент
        enter_time = self.env.now

        order = self.generate_order()

        # Клиент передумал заказывать
        if len(order.items) == 0:
            return

        # Заказ через терминал
        if order.type == Order.Type.terminal:
            with self.res.terminals.request() as request:
                yield request  # Встать в очередь к терминалу
                # Не учитываем время, затраченное клиентом на совершение заказа
                enter_time -= self.env.now
                # Подойти к терминалу и совершить заказ
                yield self.env.process(self.order_via_terminal())
                enter_time += self.env.now
        # Заказ через кассу
        elif order.type == Order.Type.cashier:
            with self.res.services.request() as request:
                yield request
                enter_time -= self.env.now
                yield self.env.process(self.order_via_cashier())
                enter_time += self.env.now

        # Готовка
        for item in order.items:
            with self.res.chefs.request() as request:
                yield request
                yield self.env.process(self.cook_menu_item(item=item))

        # Сборка заказа
        with self.res.services.request() as request:
            yield request
            yield self.env.process(self.collect_order(order_size=len(order.items)))

        # Заказ несут
        if order.need_bring:
            with self.res.services.request() as request:
                yield request
                yield self.env.process(self.bring_order())

        # рассчитываем, сколько времени составило ожидание клиента, и сохраняем его
        self.stats.wait_times.append(self.env.now - enter_time)

    # Метод run() отвечает за создание экземпляра ресторана и генерацию клиентов,
    # пока симуляция не прекратится
    def _run(self):
        while True:
            # Задержка, с которой в среднем клиенты приходят в ресторан
            yield self.env.timeout(randomize(self.params.request_timeout))
            # Делаем на это время задержку, прежде чем создавать нового пользователя
            self.env.process(self.order_food())
