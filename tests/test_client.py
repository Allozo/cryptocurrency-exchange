import pytest
import sqlalchemy as sa

from app.app import application
from app.trade import Trade

client = application.app.test_client()
engine = sa.create_engine('sqlite:///test_client.db')
application.trade = Trade(engine)


@pytest.fixture(
    autouse=True,
    params=[
        {
            'user_login': '',
            'user_balance': None,
            'history_operation': None,
            'user_exist': False,
        },
        {
            'user_login': 'user_1',
            'user_balance': '123.34',
            'history_operation': [],
            'user_exist': False,
        },
        {
            'user_login': 'user_1',
            'user_balance': '123.34',
            'history_operation': [
                ('Buy', 'crypto_1', 5),
                ('Sell', 'crypto_2', 3),
                ('Buy', 'crypto_1', 5),
                ('Sell', 'crypto_2', 3),
                ('Buy', 'crypto_1', 5),
                ('Sell', 'crypto_2', 3),
                ('Buy', 'crypto_1', 5),
                ('Sell', 'crypto_2', 3),
                ('Buy', 'crypto_1', 5),
                ('Sell', 'crypto_2', 3),
                ('Buy', 'crypto_1', 5),
                ('Sell', 'crypto_2', 3),
            ],
            'user_exist': True,
        },
    ],
)
def mocker_trade(mocker, request):
    mocker.patch('app.trade', autospec=True)

    mocker.patch.object(application, 'now_user_login', new=request.param['user_login'])
    mocker.patch.object(
        application.trade,
        'get_user_balance',
        return_value=request.param['user_balance'],
    )
    mocker.patch.object(
        application.trade,
        'get_all_crypto',
        return_value=[
            ('crypto_1', '123.23'),
            ('crypto_2', '13.23'),
            ('crypto_3', '12'),
            ('crypto_4', '1.23'),
            ('crypto_5', '163.23'),
        ],
    )
    mocker.patch.object(
        application.trade,
        'get_user_history_operation',
        return_value=request.param['history_operation'],
    )
    mocker.patch.object(
        application.trade, 'is_user_exist', return_value=request.param['user_exist']
    )
    mocker.patch.object(application.trade, 'create_user', return_value=None)
    mocker.patch.object(
        application.trade, 'get_cryptocurrency_cost', return_value='123'
    )
    mocker.patch.object(application.trade, 'user_buy_cryptocurrency', return_value=None)
    mocker.patch.object(
        application.trade, 'user_sell_cryptocurrency', return_value=None
    )
    mocker.patch.object(application.trade, 'get_user_portfolio', return_value=[])
    mocker.patch.object(application.trade, 'create_cryptocurrency', return_value=None)
    return request.param


def test_list_cryptocurrency():
    res = client.get('/list_cryptocurrency')
    assert res.status_code == 200
    assert application.trade.get_all_crypto.call_count == 1  # type: ignore


def test_authorization_user(mocker_trade):
    res = client.post(
        '/authorization_user', data={'user_login_in': mocker_trade['user_login']}
    )
    assert res.status_code == 302
    assert application.trade.create_user.call_count == int(  # type: ignore
        not mocker_trade['user_exist']
    )


def test_exit_user():
    res = client.post('/exit_user')
    assert res.status_code == 302
    assert application.now_user_login == ''


@pytest.mark.parametrize(
    ('count', 'crypto_name', 'crypto_cost', 'status_code'),
    [
        ['12', 'crypto_1', '123', 302],
        ['120', 'crypto_1', '12', 200],
        ['we', 'crypto_1', '12', 200],
    ],
)
def test_user_buy_cryptocurrency(mocker, count, crypto_name, crypto_cost, status_code):
    if count == '120':
        mocker.patch.object(
            application.trade, 'user_buy_cryptocurrency', side_effect=ValueError
        )

    res = client.post(
        f'/user_buy_cryptocurrency?crypto_name={crypto_name}&crypto_cost={crypto_cost}',
        data={'count_buy_crypto': count},
    )

    assert res.status_code == status_code


@pytest.mark.parametrize(
    ('count', 'crypto_name', 'status_code'),
    [
        ['12', 'crypto_1', 302],
        ['120', 'crypto_2', 200],
        ['we', 'crypto_1', 200],
    ],
)
def test_user_sell_cryptocurrency(mocker, count, crypto_name, status_code):
    if crypto_name == 'crypto_2':
        mocker.patch.object(
            application.trade, 'user_sell_cryptocurrency', side_effect=ValueError
        )

    res = client.post(
        f'/user_sell_cryptocurrency?crypto_name={crypto_name}',
        data={'count_sell_crypto': count},
    )

    assert res.status_code == status_code


def test_get_user_portfolio():
    res = client.get('/user_portfolio')
    assert res.status_code == 200


def test_get_history_operation():
    res = client.get('/history_operations')
    assert res.status_code == 200


def test_get_history_operation_with_page_error_val():
    res = client.get('/history_operations?page=njh')
    assert res.status_code == 200


def test_get_history_operation_with_page_error_int_m_12():
    res = client.get('/history_operations?page=-12')
    assert res.status_code == 200


def test_get_history_operation_with_page_error_int_p_12():
    res = client.get('/history_operations?page=12')
    assert res.status_code == 200


def test_get_history_operation_with_page_error_big_int():
    res = client.get('/history_operations?page=12')
    assert res.status_code == 200


def test_get_history_operation_with_page_error_min_int():
    res = client.get('/history_operations?page=2')
    assert res.status_code == 200


def test_get_history_operation_without_page():
    res = client.get('/history_operations')
    assert res.status_code == 200


@pytest.mark.parametrize(
    ('crypto_name', 'crypto_cost', 'stats_code'),
    [
        ['crypto_1', '234.4', 302],
        ['crypto_2', 'xvx', 200],
        ['crypto_3', '234.4', 200],
    ],
)
def test_add_cryptocurrency(mocker, crypto_name, crypto_cost, stats_code):
    if crypto_name == 'crypto_3':
        mocker.patch.object(
            application.trade, 'create_cryptocurrency', side_effect=ValueError
        )
    res = client.post(
        '/add_cryptocurrency',
        data={
            'crypto_name': crypto_name,
            'crypto_cost': crypto_cost,
        },
    )
    assert res.status_code == stats_code
