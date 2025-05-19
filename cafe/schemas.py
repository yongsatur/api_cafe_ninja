from xmlrpc.client import _datetime
from ninja import Schema


class UserAuthentication(Schema):
    username: str
    password: str


class CategoryIn(Schema):
    name: str
    slug: str


class CategoryOut(Schema):
    name: str
    slug: str


class MenuIn(Schema):
    category: int
    name: str
    slug: str
    weight: float
    capacity: float
    description: str
    price: float 


class MenuOut(Schema):
    category: CategoryOut
    name: str
    slug: str
    weight: float
    capacity: float
    description: str
    price: float 


class TableStatusOut(Schema):
    name: str


class TableIn(Schema):
    number: int
    status: int


class TableOut(Schema):
    number: int
    status: TableStatusOut


class ReservationIn(Schema):
    table: int
    client_name: str
    client_phone: str
    datetime: _datetime
    quest_count: int
    comment: str


class ReservationOut(Schema):
    table: TableOut
    client_name: str
    client_phone: str
    datetime: _datetime
    quest_count: int
    comment: str 


class OrderStatusOut(Schema):
    name: str


class OrderIn(Schema):
    table: int
    reservation: int
    status: int
    totalAmount: float


class OrderOut(Schema):
    table: TableOut
    reservation: ReservationOut
    status: OrderStatusOut
    totalAmount: float


class OrderItemIn(Schema):
    order: int
    menu: int
    price: float
    quantity: int


class OrderItemOut(Schema):
    order: OrderOut
    menu: MenuOut
    price: float
    quantity: int


class PaymentIn(Schema):
    order: int


class PaymentOut(Schema):
    order: OrderOut
    status: bool