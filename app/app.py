import logging
import math
import typing as t
from dataclasses import dataclass
from pathlib import Path
from typing import Union

import sqlalchemy as sa
from flask import Flask, redirect, render_template, request, url_for

try:
    from app.trade import CONST_VALUE, NameOperation, Trade
except ImportError:  # pragma: no cover
    from trade import CONST_VALUE, NameOperation, Trade  # type: ignore

if t.TYPE_CHECKING:
    from werkzeug.wrappers.response import Response


logger = logging.getLogger(__name__)


@dataclass
class Application:
    app: Flask
    trade: Trade
    now_user_login: str


logger.info('Запускаем сервер')
application = Application(Flask(__name__), None, '')  # type: ignore


def init_trade_operation() -> None:  # pragma: no cover -- Функции ниже тестируются отдельно
    application.trade.base_drop_all()
    application.trade.base_create_all()

    application.trade.create_cryptocurrency('crypto_1', '123.43')
    application.trade.create_cryptocurrency('crypto_2', '3.3')
    application.trade.create_cryptocurrency('crypto_3', '17.67')
    application.trade.create_cryptocurrency('crypto_4', '65')
    application.trade.create_cryptocurrency('crypto_5', '143.8')

    application.trade.create_operation(NameOperation.Buy.value)
    application.trade.create_operation(NameOperation.Sell.value)


def init_trade() -> None:
    logger.info('Идет подключение к базе данных')

    name_base = 'main.db'
    path_base = f'sqlite:///{name_base}'
    if Path(name_base).exists():
        logger.info('Подключимся к существующей базе данных')
        engine = sa.create_engine(path_base)
        application.trade = Trade(engine)
    else:
        logger.info('Создадим новую базу данных')
        engine = sa.create_engine(path_base)
        application.trade = Trade(engine)
        init_trade_operation()
    application.trade.regular_update_cost()


def init_application() -> None:
    init_trade()


@application.app.route('/index')
@application.app.route('/list_cryptocurrency')
def list_cryptocurrency() -> str:
    user_balance = ''

    if application.now_user_login != '':
        user_balance = application.trade.get_user_balance(application.now_user_login)

    cryptocurrency_list = application.trade.get_all_crypto()

    return render_template(
        'index.html',
        user_login=application.now_user_login,
        cryptocurrency_list=cryptocurrency_list,
        user_balance=user_balance,
    )


@application.app.route('/authorization_user', methods=['POST'])
def authorization_user() -> 'Response':
    application.now_user_login = str(request.form.get('user_login_in'))

    if not application.trade.is_user_exist(application.now_user_login):
        application.trade.create_user(application.now_user_login)

    logger.info('Пользователь %s авторизовался', application.now_user_login)

    return redirect(url_for('list_cryptocurrency'))


@application.app.route('/exit_user', methods=['POST'])
def exit_user() -> 'Response':
    logger.info('Пользователь %s вышел', application.now_user_login)
    application.now_user_login = ''
    return redirect(url_for('list_cryptocurrency'))


@application.app.route('/user_buy_cryptocurrency', methods=['POST'])
def user_buy_cryptocurrency() -> Union[str, 'Response']:
    count_str = str(request.form.get('count_buy_crypto'))
    crypto_name = str(request.args.get('crypto_name'))
    crypto_cost = str(request.args.get('crypto_cost'))

    logger.info(
        'Пользователь %s хочет купить %s %s по цене %s',
        application.now_user_login,
        count_str,
        crypto_name,
        crypto_cost,
    )

    is_error = False
    text_error = None

    try:
        count_int = int(count_str)
    except ValueError:
        is_error = True
        text_error = 'Введено некорректное значение в поле количества'

    if not is_error:
        # Проверим, что цена не изменилась
        new_cost = str(application.trade.get_cryptocurrency_cost(crypto_name))
        if new_cost != crypto_cost:
            is_error = True
            text_error = 'Цена криптовалюты изменилась. Пожалуйста, обновите страницу'

    if not is_error:
        try:
            application.trade.user_buy_cryptocurrency(
                application.now_user_login, crypto_name, count_int
            )
        except ValueError as error:
            is_error = True
            text_error = str(error)

    if is_error:
        user_balance = application.trade.get_user_balance(application.now_user_login)
        cryptocurrency_list = application.trade.get_all_crypto()
        return render_template(
            'index_error.html',
            user_login=application.now_user_login,
            cryptocurrency_list=cryptocurrency_list,
            user_balance=user_balance,
            text_error=text_error,
        )

    return redirect(url_for('list_cryptocurrency'))


@application.app.route('/user_sell_cryptocurrency', methods=['POST'])
def user_sell_cryptocurrency() -> Union[str, 'Response']:
    count_str = str(request.form.get('count_sell_crypto'))
    crypto_name = str(request.args.get('crypto_name'))

    logger.info(
        'Пользователь %s хочет продать %s %s',
        application.now_user_login,
        count_str,
        crypto_name,
    )

    is_error = False
    text_error = None

    try:
        count_int = int(count_str)
    except ValueError:
        is_error = True
        text_error = 'Введено некорректное значение в поле количества'

    if not is_error:
        try:
            application.trade.user_sell_cryptocurrency(
                application.now_user_login, crypto_name, count_int
            )
        except ValueError as error:
            is_error = True
            text_error = str(error)
    if is_error:
        user_balance = application.trade.get_user_balance(application.now_user_login)
        cryptocurrency_list = application.trade.get_all_crypto()
        return render_template(
            'index_error.html',
            user_login=application.now_user_login,
            cryptocurrency_list=cryptocurrency_list,
            user_balance=user_balance,
            text_error=text_error,
        )
    return redirect(url_for('list_cryptocurrency'))


@application.app.route('/user_portfolio')
def get_user_portfolio() -> str:
    if application.now_user_login != '':
        logger.info(
            'Пользователь %s хочет получить свой портфель криптовалют',
            application.now_user_login,
        )
    else:
        logger.info(
            'Выведем сообщение, что нужно авторизоваться для просмотра портфеля криптовалют'
        )

    user_portfolio = None
    user_balance = None

    if application.now_user_login != '':
        user_portfolio = application.trade.get_user_portfolio(
            application.now_user_login
        )
        user_balance = application.trade.get_user_balance(application.now_user_login)

    return render_template(
        'user_portfolio.html',
        user_login=application.now_user_login,
        user_portfolio=user_portfolio,
        user_balance=user_balance,
    )


@application.app.route('/history_operations')
def get_history_operation() -> Union['Response', str]:
    if application.now_user_login != '':
        logger.info(
            'Получим историю операций пользователя %s', application.now_user_login
        )
    else:
        logger.info(
            'Выведем сообщение, что нужно авторизоваться для просмотра истории операций'
        )
        render_template('user_history_operations.html')

    page_str = str(request.args.get('page'))

    if page_str == 'None':
        number_page = 1
    else:
        try:
            number_page = int(page_str)
        except ValueError:
            logger.error(
                'Передан некорректный номер страницы для получения истории пользователя: %s',
                page_str,
            )
            return render_template('error_404.html')

    if not number_page > 0:
        render_template('error_404.html')
        logger.error('Передано неверной число для получения страницы: %d', number_page)
        return render_template('error_404.html')

    user_history_operations = None
    user_balance = None
    url_next = None
    url_prev = None

    if application.now_user_login != '':
        logger.info(
            'Для пользователя %s получим %d страницу последних операций',
            application.now_user_login,
            number_page,
        )

        user_history_operations = application.trade.get_user_history_operation(
            application.now_user_login
        )
        user_balance = application.trade.get_user_balance(application.now_user_login)

        # Реализуем пагинацию
        all_count_operation = len(user_history_operations)
        count_operation_on_page = CONST_VALUE.COUNT_OPERATION_ON_PAGE.value

        min_number_page = 1
        # Максимум нужен, чтобы пустой список отрабатывался корректно
        max_number_page = max(
            math.ceil(all_count_operation / count_operation_on_page), 1
        )

        if not min_number_page <= number_page <= max_number_page:
            logger.info(
                'У пользователя %s нет страницы с номером %d',
                application.now_user_login,
                number_page,
            )
            return render_template('error_404.html')

        start_page = count_operation_on_page * (number_page - 1)
        end_page = count_operation_on_page * (number_page - 1) + count_operation_on_page

        user_history_operations = user_history_operations[start_page:end_page]

        # Ссылка на предыдущую страницу (если такой нет, то оставим None)
        prev_page = number_page - 1
        if min_number_page <= prev_page <= max_number_page:
            url_prev = f'history_operations?page={prev_page}'

        # Ссылку на следующую страницу (если такой нет, то оставим None)
        next_page = number_page + 1
        if min_number_page <= next_page <= max_number_page:
            url_next = f'history_operations?page={next_page}'

    return render_template(
        'user_history_operations.html',
        user_login=application.now_user_login,
        user_history_operations=user_history_operations,
        user_balance=user_balance,
        url_next=url_next,
        url_prev=url_prev,
    )


# Доступ к ней только когда пользователь авторизован
@application.app.route('/add_cryptocurrency', methods=['POST'])
def add_cryptocurrency() -> Union[str, 'Response']:

    crypto_name = str(request.form.get('crypto_name'))
    crypto_cost = str(request.form.get('crypto_cost'))

    logger.info(
        'Пользователь %s хочет добавить новую криптовалюту %s со стоимостью %s',
        application.now_user_login,
        crypto_name,
        crypto_cost,
    )

    is_error = None
    text_error = None

    try:
        float(crypto_cost)
    except ValueError as e:
        is_error = True
        text_error = e

    if not is_error:
        try:
            application.trade.create_cryptocurrency(crypto_name, crypto_cost)
        except ValueError as e:
            is_error = True
            text_error = e

    if is_error:
        user_balance = application.trade.get_user_balance(application.now_user_login)
        cryptocurrency_list = application.trade.get_all_crypto()
        return render_template(
            'index_error.html',
            user_login=application.now_user_login,
            cryptocurrency_list=cryptocurrency_list,
            user_balance=user_balance,
            text_error=text_error,
        )

    return redirect(url_for('list_cryptocurrency'))


if __name__ == '__main__':  # pragma: no cover
    init_application()
    logger.info('Сервер запущен')
    application.app.run()
