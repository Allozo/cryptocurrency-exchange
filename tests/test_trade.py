import pytest
import sqlalchemy as sa

from app.trade import NameOperation, Trade

engine = sa.create_engine('sqlite:///test.db')
trade = Trade(engine)


@pytest.fixture(autouse=True)
def clear_trade_base():
    trade.base_create_all()
    yield
    trade.base_drop_all()


def test_add_user():
    trade.create_user('name_1')
    trade.create_user('name_2')

    assert (
        str(trade.get_all_users())
        == "[('name_1', Decimal('1000.00'), []), ('name_2', Decimal('1000.00'), [])]"
    )


def test_add_cryptocurrency():
    trade.create_cryptocurrency('crypto_1', '123.23')
    trade.create_cryptocurrency('crypto_2', '12.3')

    assert (
        str(trade.get_all_crypto())
        == "[('crypto_1', Decimal('123.23')), ('crypto_2', Decimal('12.30'))]"
    )


def test_add_cryptocurrency_with_eq_name():
    trade.create_cryptocurrency('crypto_1', '123.23')

    with pytest.raises(ValueError):
        trade.create_cryptocurrency('crypto_1', '123.23')


def test_add_operation():
    trade.create_operation(NameOperation.Buy.value)
    trade.create_operation(NameOperation.Sell.value)

    assert str(trade.get_all_operations()) == "['Buy', 'Sell']"


def test_user_buy_cryptocurrency():
    trade.create_user('name_1')
    trade.create_user('name_2')
    trade.create_cryptocurrency('crypto_1', '123.23')
    trade.create_cryptocurrency('crypto_2', '12.3')

    trade.create_operation(NameOperation.Buy.value)

    trade.user_buy_cryptocurrency('name_1', 'crypto_1', 5)
    trade.user_buy_cryptocurrency('name_2', 'crypto_1', 5)
    trade.user_buy_cryptocurrency('name_2', 'crypto_2', 10)
    trade.user_buy_cryptocurrency('name_2', 'crypto_2', 15)

    assert (
        str(trade.get_all_users())
        == "[('name_1', Decimal('383.85'), [('crypto_1', 5)]), ('name_2', Decimal('76.35'), [('crypto_1', 5), ('crypto_2', 25)])]"  # pylint: disable=line-too-long
    )

    assert (
        str(trade.get_all_history())
        == "[('name_1', 'Buy', 5, 'crypto_1', Decimal('123.23')), ('name_2', 'Buy', 5, 'crypto_1', Decimal('123.23')), ('name_2', 'Buy', 10, 'crypto_2', Decimal('12.30')), ('name_2', 'Buy', 15, 'crypto_2', Decimal('12.30'))]"  # pylint: disable=line-too-long
    )


def test_user_buy_cryptocurrency_error_insufficient_funds():
    trade.create_user('name_1')
    trade.create_cryptocurrency('crypto_1', '123.23')

    trade.create_operation(NameOperation.Buy.value)

    with pytest.raises(ValueError):
        trade.user_buy_cryptocurrency('name_1', 'crypto_1', 50)


def test_user_buy_cryptocurrency_error_no_user():
    trade.create_user('name_1')
    trade.create_cryptocurrency('crypto_1', '123.23')

    trade.create_operation(NameOperation.Buy.value)

    with pytest.raises(ValueError):
        trade.user_buy_cryptocurrency('name_2', 'crypto_1', 5)


def test_user_buy_cryptocurrency_error_no_crypto():
    trade.create_user('name_1')
    trade.create_cryptocurrency('crypto_1', '123.23')

    trade.create_operation(NameOperation.Buy.value)

    with pytest.raises(ValueError):
        trade.user_buy_cryptocurrency('name_1', 'crypto_2', 5)


def test_user_sell_cryptocurrency():
    trade.create_user('name_1')
    trade.create_user('name_2')
    trade.create_cryptocurrency('crypto_1', '123.23')
    trade.create_cryptocurrency('crypto_2', '12.3')
    trade.create_operation(NameOperation.Buy.value)
    trade.create_operation(NameOperation.Sell.value)

    trade.user_buy_cryptocurrency('name_1', 'crypto_1', 5)
    trade.user_buy_cryptocurrency('name_2', 'crypto_1', 5)
    trade.user_buy_cryptocurrency('name_2', 'crypto_2', 10)

    trade.user_sell_cryptocurrency('name_1', 'crypto_1', 5)
    trade.user_sell_cryptocurrency('name_2', 'crypto_2', 9)

    assert (
        str(trade.get_all_users())
        == "[('name_1', Decimal('1000.00'), [('crypto_1', 0)]), ('name_2', Decimal('371.55'), [('crypto_1', 5), ('crypto_2', 1)])]"  # pylint: disable=line-too-long
    )

    assert (
        str(trade.get_all_history())
        == "[('name_1', 'Buy', 5, 'crypto_1', Decimal('123.23')), ('name_2', 'Buy', 5, 'crypto_1', Decimal('123.23')), ('name_2', 'Buy', 10, 'crypto_2', Decimal('12.30')), ('name_1', 'Sell', 5, 'crypto_1', Decimal('123.23')), ('name_2', 'Sell', 9, 'crypto_2', Decimal('12.30'))]"  # pylint: disable=line-too-long
    )


def test_user_sell_cryptocurrency_error_count_cryptocurrency():
    trade.create_user('name_1')
    trade.create_cryptocurrency('crypto_1', '123.23')
    trade.create_operation(NameOperation.Buy.value)
    trade.create_operation(NameOperation.Sell.value)

    trade.user_buy_cryptocurrency('name_1', 'crypto_1', 5)

    with pytest.raises(ValueError):
        trade.user_sell_cryptocurrency('name_1', 'crypto_1', 50)


def test_user_sell_cryptocurrency_error_no_user():
    trade.create_user('name_1')
    trade.create_cryptocurrency('crypto_1', '123.23')
    trade.create_operation(NameOperation.Buy.value)
    trade.create_operation(NameOperation.Sell.value)

    trade.user_buy_cryptocurrency('name_1', 'crypto_1', 5)

    with pytest.raises(ValueError):
        trade.user_sell_cryptocurrency('name_2', 'crypto_1', 5)


def test_user_sell_cryptocurrency_error_no_crypto():
    trade.create_user('name_1')
    trade.create_cryptocurrency('crypto_1', '123.23')
    trade.create_cryptocurrency('crypto_2', '123.23')
    trade.create_cryptocurrency('crypto_3', '123.23')
    trade.create_operation(NameOperation.Buy.value)
    trade.create_operation(NameOperation.Sell.value)

    trade.user_buy_cryptocurrency('name_1', 'crypto_1', 5)

    with pytest.raises(ValueError):
        trade.user_sell_cryptocurrency('name_1', 'crypto_1', 10)
    with pytest.raises(ValueError):
        trade.user_sell_cryptocurrency('name_1', 'crypto_3', 5)
    with pytest.raises(ValueError):
        trade.user_sell_cryptocurrency('name_1', 'crypto_4', 5)


def test_get_user_balance():
    trade.create_user('name_1')
    trade.create_cryptocurrency('crypto_1', '123.23')
    trade.create_operation(NameOperation.Buy.value)
    trade.create_operation(NameOperation.Sell.value)

    trade.user_buy_cryptocurrency('name_1', 'crypto_1', 5)
    trade.user_sell_cryptocurrency('name_1', 'crypto_1', 3)

    assert str(trade.get_user_balance('name_1')) == '753.54'


def test_get_user_balance_error_no_user():
    with pytest.raises(ValueError):
        trade.get_user_balance('name_1')


def test_get_user_portfolio():
    trade.create_user('name_1')
    trade.create_cryptocurrency('crypto_1', '123.23')
    trade.create_cryptocurrency('crypto_2', '13.3')
    trade.create_operation(NameOperation.Buy.value)
    trade.create_operation(NameOperation.Sell.value)

    trade.user_buy_cryptocurrency('name_1', 'crypto_1', 5)
    trade.user_buy_cryptocurrency('name_1', 'crypto_2', 9)
    trade.user_sell_cryptocurrency('name_1', 'crypto_1', 5)
    trade.user_sell_cryptocurrency('name_1', 'crypto_2', 5)

    assert str(trade.get_user_portfolio('name_1')) == "[(4, 'crypto_2')]"


def test_get_user_portfolio_error_no_user():
    with pytest.raises(ValueError):
        trade.get_user_portfolio('name_1')


def test_is_user_exist():
    trade.create_user('name_1')
    assert trade.is_user_exist('name_1') is True


def test_get_cryptocurrency_cost():
    trade.create_cryptocurrency('crypto_1', '123.23')
    cost = trade.get_cryptocurrency_cost('crypto_1')
    assert str(cost) == '123.23'


def test_get_user_history_operation():
    trade.create_user('name_1')
    trade.create_cryptocurrency('crypto_1', '123.23')
    trade.create_cryptocurrency('crypto_2', '13.3')
    trade.create_operation(NameOperation.Buy.value)
    trade.create_operation(NameOperation.Sell.value)

    trade.user_buy_cryptocurrency('name_1', 'crypto_1', 5)
    trade.user_buy_cryptocurrency('name_1', 'crypto_2', 9)
    trade.user_sell_cryptocurrency('name_1', 'crypto_1', 5)
    trade.user_sell_cryptocurrency('name_1', 'crypto_2', 5)

    history_operation = trade.get_user_history_operation('name_1')

    assert (
        str(history_operation)
        == "[('Buy', 'crypto_1', 5), ('Buy', 'crypto_2', 9), ('Sell', 'crypto_1', 5), ('Sell', 'crypto_2', 5)]"  # pylint: disable=line-too-long
    )


def test_update_cost():
    trade.create_cryptocurrency('crypto_1', '123.23')
    trade.create_cryptocurrency('crypto_2', '13.3')

    trade.update_cost(seed=10)

    assert str(trade.get_cryptocurrency_cost('crypto_1')) == '133.09'
    assert str(trade.get_cryptocurrency_cost('crypto_2')) == '14.36'
