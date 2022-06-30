import logging
import random
import threading
import time
from contextlib import contextmanager
from enum import Enum
from typing import Any, Generator, Optional

from sqlalchemy.orm import Session, sessionmaker

try:
    from app.models import (
        Base,
        Cryptocurrency,
        HistoryOperation,
        Operation,
        User,
        UserCryptocurrency,
    )
except ImportError:  # pragma: no cover
    from models import (  # type: ignore
        Base,
        Cryptocurrency,
        HistoryOperation,
        Operation,
        User,
        UserCryptocurrency,
    )


class NameOperation(Enum):
    Buy = 'Buy'
    Sell = 'Sell'


class CONST_VALUE(Enum):
    COUNT_OPERATION_ON_PAGE = 5
    TIME_UPDATE = 10


logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.DEBUG,
    filename='app.log',
    filemode='w',
    format='%(name)s - %(levelname)s - %(message)s',
    encoding='utf-8',
)


class Trade:
    def __init__(self, engine_db: int) -> None:
        self.engine = engine_db
        self.Session = sessionmaker(bind=self.engine)

    def update_cost(self, seed: Optional[int] = None) -> None:
        logger.info('Обновим курс каждой валюты')
        with self._create_session() as session:
            list_cryptocurrency = session.query(Cryptocurrency).all()
            for crypto in list_cryptocurrency:
                old_cost = crypto.cost
                if seed is not None:
                    random.seed(seed)
                crypto.cost = round(
                    random.randint(-10, 10) * crypto.cost / 100 + crypto.cost, 2
                )
                logger.info(
                    'Криптовалюта %s: %s --> %s', crypto.name, old_cost, crypto.cost
                )

    def _loop_for_update_cost(self) -> None:
        while True:
            self.update_cost()
            time.sleep(CONST_VALUE.TIME_UPDATE.value)

    def regular_update_cost(self) -> None:
        thread = threading.Thread(target=self._loop_for_update_cost)
        thread.start()

    @contextmanager
    def _create_session(
        self, **kwargs: dict[Any, Any]
    ) -> Generator[Session, Session, None]:
        new_session = self.Session(**kwargs)
        try:
            yield new_session
            new_session.commit()
        except Exception:
            new_session.rollback()
            raise
        finally:
            new_session.close()

    def base_drop_all(self) -> None:
        Base.metadata.drop_all(self.engine)

    def base_create_all(self) -> None:
        Base.metadata.create_all(self.engine)

    def create_user(self, login: str) -> None:
        with self._create_session() as session:
            user = User(login=login, balance='1000')
            session.add(user)
        logger.info('Добавили пользователя: %s', login)

    def create_cryptocurrency(self, name: str, cost: str) -> None:
        with self._create_session() as session:
            crypto = (
                session.query(Cryptocurrency).where(Cryptocurrency.name == name).first()
            )
            if crypto is not None:
                logger.error('Криптовалюта с именем %s уже существует', name)
                raise ValueError(f'Криптовалюта с именем {name} уже существует')

            cryptocurrency = Cryptocurrency(name=name, cost=cost)
            session.add(cryptocurrency)

        logger.info('Добавили криптовалюту: %s со стоимостью %s', name, cost)

    def create_operation(self, name: str) -> None:
        with self._create_session() as session:
            operation = Operation(name=name)
            session.add(operation)
        logger.info('Добавили операцию: %s', name)

    def user_buy_cryptocurrency(
        self, user_login: str, cryptocurrency_name: str, count: int
    ) -> None:
        logger.info(
            'Пользователю %s хочет купить %d %s',
            user_login,
            count,
            cryptocurrency_name,
        )
        with self._create_session() as session:
            user = session.query(User).where(User.login == user_login).first()
            if user is None:
                logger.error('Пользователя %s не существует', user_login)
                raise ValueError('Такого пользователя не существует')

            cryptocurrency = (
                session.query(Cryptocurrency)
                .where(Cryptocurrency.name == cryptocurrency_name)
                .first()
            )
            if cryptocurrency is None:
                logger.error('Криптовалюты %s не существует', cryptocurrency_name)
                raise ValueError('Такой криптовалюты не существует')

            # Получим запись Пользователь - Криптовалюта
            notes_user_crypto = (
                session.query(UserCryptocurrency)
                .where(UserCryptocurrency.users == user)
                .where(UserCryptocurrency.cryptocurrencies == cryptocurrency)
                .first()
            )

            # Проверим, что у пользователя хватает средств для покупки
            if user.balance >= cryptocurrency.cost * count:
                user.balance -= cryptocurrency.cost * count
            else:
                logger.error(
                    'У пользователя %s на счету %s, а для покупки надо %s',
                    user_login,
                    user.balance,
                    cryptocurrency.cost * count,
                )
                raise ValueError('Недостаточно средств')

            # У пользователя нет такой валюты ещё
            if notes_user_crypto is None:
                new_notes = UserCryptocurrency(count=count)
                new_notes.users = user
                new_notes.cryptocurrencies = cryptocurrency
            else:
                notes_user_crypto.count += count

            # Запишем операцию в историю
            operation = (
                session.query(Operation)
                .where(Operation.name == NameOperation.Buy.value)
                .first()
            )

            new_operations = HistoryOperation(count=count)
            new_operations.user = user
            new_operations.operation = operation
            new_operations.cryptocurrency = cryptocurrency
            new_operations.price = cryptocurrency.cost

            logger.info(
                'Пользователь %s купил %d %s по цене %s и заплатил %s',
                user_login,
                count,
                cryptocurrency_name,
                cryptocurrency.cost,
                cryptocurrency.cost * count,
            )

    def user_sell_cryptocurrency(
        self, user_login: str, cryptocurrency_name: str, count: int
    ) -> None:
        logger.info(
            'Пользователь %s хочет продать %d %s',
            user_login,
            count,
            cryptocurrency_name,
        )
        with self._create_session() as session:
            user = session.query(User).where(User.login == user_login).first()
            if user is None:
                logger.error('Пользователя %s не существует', user_login)
                raise ValueError(f'Пользователя {user_login} не существует')

            cryptocurrency = (
                session.query(Cryptocurrency)
                .where(Cryptocurrency.name == cryptocurrency_name)
                .first()
            )
            if cryptocurrency is None:
                logger.error('Криптовалюты %s не существует', cryptocurrency_name)
                raise ValueError('Криптовалюты не существует')

            # Получим запись Пользователь - Криптовалюта
            notes_user_crypto = (
                session.query(UserCryptocurrency)
                .where(UserCryptocurrency.users == user)
                .where(UserCryptocurrency.cryptocurrencies == cryptocurrency)
                .first()
            )

            if notes_user_crypto is None or notes_user_crypto.count == 0:
                # У пользователя нет такой валюты
                logger.error(
                    'У пользователя %s нет криптовалюты %s',
                    user_login,
                    cryptocurrency_name,
                )
                raise ValueError(
                    f'У пользователя {user_login} нет криптовалюты {cryptocurrency_name}'
                )

            # Проверим, что у пользователя хватает криптовалюты на счету
            if notes_user_crypto.count >= count:
                user.balance += cryptocurrency.cost * count
                notes_user_crypto.count -= count
            else:
                logger.error(
                    'У пользователя %s есть %d %s, а для продажи надо %d',
                    user_login,
                    notes_user_crypto.count,
                    cryptocurrency_name,
                    count,
                )
                raise ValueError(
                    f'У пользователя {user_login} есть {notes_user_crypto.count} {cryptocurrency_name}, а для продажи надо {count}'  # pylint: disable=line-too-long
                )

            # Запишем операцию в историю
            operation = (
                session.query(Operation)
                .where(Operation.name == NameOperation.Sell.value)
                .first()
            )

            new_operations = HistoryOperation(count=count)
            new_operations.user = user
            new_operations.operation = operation
            new_operations.cryptocurrency = cryptocurrency
            new_operations.price = cryptocurrency.cost

            logger.info(
                'Пользователь %s продал %d %s по цене %s и получил %s',
                user_login,
                count,
                cryptocurrency_name,
                cryptocurrency.cost,
                cryptocurrency.cost * count,
            )

    def get_all_users(self) -> list[tuple[Any, Any, list[tuple[Any, Any]]]]:
        with self._create_session() as session:
            users = session.query(User).all()

            res = []

            for user in users:
                user_crypto = []
                for crypto in user.portfolio:
                    cryptocurrency_name = crypto.cryptocurrencies.name
                    crypto_count = crypto.count
                    user_crypto.append((cryptocurrency_name, crypto_count))
                res.append((user.login, user.balance, user_crypto))

            return res

    def get_all_crypto(self) -> list[tuple[str, str]]:
        with self._create_session() as session:
            cryptocurrencies = session.query(Cryptocurrency).all()
            return [(crypto.name, crypto.cost) for crypto in cryptocurrencies]

    def get_all_operations(self) -> list[str]:
        with self._create_session() as session:
            operations = session.query(Operation).all()
            return [op.name for op in operations]

    def get_all_history(self) -> list[tuple[str, str, str, str, str]]:
        with self._create_session() as session:
            history = session.query(HistoryOperation).all()

            return [
                (
                    i.user.login,
                    i.operation.name,
                    i.count,
                    i.cryptocurrency.name,
                    i.price,
                )
                for i in history
            ]

    def get_user_balance(self, user_login: str) -> str:
        logger.info('Получим баланс пользователя %s', user_login)
        with self._create_session() as session:
            user = session.query(User).where(User.login == user_login).first()

            if user is None:
                logger.error('Пользователя %s не существует', user_login)
                raise ValueError(f'Пользователя {user_login} не существует')

            logger.info('Баланс пользователя %s равен %s', user_login, user.balance)

            return user.balance

    def get_user_portfolio(self, user_login: str) -> list[tuple[str, str]]:
        logger.info('Получим портфель пользователя %s', user_login)
        with self._create_session() as session:
            user = session.query(User).where(User.login == user_login).first()

            if user is None:
                logger.error('Пользователя %s не существует', user_login)
                raise ValueError(f'Пользователя {user_login} не существует')

            res = []
            for portfolio in user.portfolio:
                if portfolio.count == 0:
                    continue
                res.append((portfolio.count, portfolio.cryptocurrencies.name))

            logger.info('Баланс пользователя %s состоит из %s', user_login, res)
            return res

    def is_user_exist(self, user_login: str) -> bool:
        logger.info('Узнаем, существует ли пользователь %s', user_login)
        with self._create_session() as session:
            user = session.query(User).where(User.login == user_login).first()
            return user is not None

    def get_cryptocurrency_cost(self, cryptocurrency_name: str) -> str:
        logger.info('Получим стоимость %s', cryptocurrency_name)
        with self._create_session() as session:
            cryptocurrency = (
                session.query(Cryptocurrency)
                .where(Cryptocurrency.name == cryptocurrency_name)
                .first()
            )
            return cryptocurrency.cost

    def get_user_history_operation(self, user_login: str) -> list[tuple[str, str, str]]:
        logger.info('Получим историю операций пользователя %s', user_login)
        with self._create_session() as session:
            user = session.query(User).where(User.login == user_login).first()
            list_operation = user.history_operations
            res = [
                (op.operation.name, op.cryptocurrency.name, op.count)
                for op in list_operation
            ]
            return res
