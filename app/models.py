from typing import Any

import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base: Any = declarative_base()


class UserCryptocurrency(Base):
    __tablename__ = 'UserCryptocurrency'

    user_id = sa.Column(sa.ForeignKey('user.id'), primary_key=True)
    cryptocurrency_id = sa.Column(sa.ForeignKey('cryptocurrency.id'), primary_key=True)

    count = sa.Column(sa.Integer, nullable=False)

    users = relationship('User', back_populates='portfolio')
    cryptocurrencies = relationship('Cryptocurrency', back_populates='users')

    def __repr__(self) -> str:
        return f'{self.count} {self.cryptocurrencies}'


class Cryptocurrency(Base):
    __tablename__ = 'cryptocurrency'

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(20), nullable=False, unique=True)
    cost = sa.Column(sa.Numeric(10, 2), nullable=False)

    users = relationship('UserCryptocurrency', back_populates='cryptocurrencies')

    def __repr__(self) -> str:
        return f'Cryptocurrency({self.id}, {self.name}, {self.cost})'


class User(Base):
    __tablename__ = 'user'

    id = sa.Column(sa.Integer, primary_key=True)
    login = sa.Column(sa.String(20), nullable=False, unique=True)
    balance = sa.Column(sa.Numeric(10, 2), nullable=False)

    portfolio = relationship('UserCryptocurrency', back_populates='users')
    history_operations = relationship('HistoryOperation', back_populates='user')

    def __repr__(self) -> str:
        return f'User({self.id}, {self.login}, {self.balance}, {self.portfolio})'


class Operation(Base):
    __tablename__ = 'operation'

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(20), nullable=False, unique=True)

    all_history_operation = relationship('HistoryOperation', back_populates='operation')

    def __repr__(self) -> str:
        return f'Operaion({self.name})'


class HistoryOperation(Base):
    __tablename__ = 'HistoryOperation'

    id = sa.Column(sa.Integer, primary_key=True)
    user_id = sa.Column(sa.ForeignKey('user.id'), nullable=False)
    operation_id = sa.Column(sa.ForeignKey('operation.id'), nullable=False)
    cryptocurrency_id = sa.Column(sa.ForeignKey('cryptocurrency.id'), nullable=False)
    count = sa.Column(sa.Integer, nullable=False)
    price = sa.Column(sa.Numeric(10, 2), nullable=False)

    user = relationship('User', back_populates='history_operations')
    operation = relationship('Operation', back_populates='all_history_operation')
    cryptocurrency = relationship('Cryptocurrency', uselist=False)

    def __repr__(self) -> str:
        return f'HistoryOperation({self.user.login}, {self.operation.name}, {self.count}, {self.cryptocurrency.name}, {self.price})'  # pylint: disable=line-too-long
