from ninja import NinjaAPI, Query, UploadedFile, File
from ninja.security import HttpBasicAuth
from ninja.errors import HttpError, AuthenticationError

from typing import List

from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate

from .models import Category, Menu, Table, Reservation, Order, OrderItem, \
    OrderStatus, TableStatus, Payment
from .schemas import CategoryIn, CategoryOut, MenuIn, MenuOut, TableIn, \
    TableOut, ReservationIn, ReservationOut, OrderIn, OrderOut, \
    OrderItemIn, OrderItemOut, PaymentIn, PaymentOut
from .decorators import *


class BasicAuth(HttpBasicAuth):
    def authenticate(self, request, username, password):
        user = authenticate(username = username, password = password)
        if user:
            return user
        raise AuthenticationError('Ошибка авторизации!')


api = NinjaAPI(csrf = True, auth = BasicAuth())


''' API для авторизации '''
    

@api.get('/basic', auth = BasicAuth(), summary = 'Проверка авторизации сотрудника')
def basic(request):
    return { 'Сообщение': 'Пользователь авторизован!', 'Логин пользователя': request.auth.username }


''' API для категорий меню '''


@api.get('/menu', response = List[CategoryOut], summary = 'Получить список категорий меню')
def get_categories(request):
    return Category.objects.all()


@api.post('/categories', response = CategoryOut, summary = 'Добавить категорию')
@check_permission('cafe.add_category', raise_exception = True, use_auth = True)
def create_category(request, payload: CategoryIn):
    try:
        return Category.objects.create(**payload.dict())
    except:
        raise HttpError(400, 'Неккоректный запрос!')
    


@api.delete('/categories/{category_id}', summary = 'Удалить категорию')
@check_permission('cafe.delete_category', raise_exception = True, use_auth = True)
def delete_category(request, category_id: int):
    try:
        category = get_object_or_404(Category, id = category_id)
        category.delete()
    except:
        raise HttpError(400, 'Неккоректный запрос!')
    return {'Сообщение': 'Категория была удалена!'}


''' API для позиций меню '''


@api.get('/menu/{category_id}', response = List[MenuOut], summary = 'Получить позиции меню по категории')
def get_menu(request, category_id: int):
    category = get_object_or_404(Category, id = category_id)
    menu = Menu.objects.filter(category = category)
    return menu


@api.get('/menu/{category_id}/sort', response = List[MenuOut], summary = 'Сортировка позиций меню по цене')
def menu_sort(request, category_id: int, sort: str = Query(None, description = 'Введите asc или desc')):
    category = get_object_or_404(Category, id = category_id)
    menu = Menu.objects.filter(category = category)

    if sort == 'asc':
        menu = menu.order_by('price')
    elif sort == 'desc':
        menu = menu.order_by('-price')
    else:
        raise HttpError(400, 'Неккоректный запрос!')
    return menu


@api.post('/menu', response = MenuOut, summary = 'Добавить позицию меню')
@check_permission('cafe.add_menu', raise_exception = True, use_auth = True)
def create_menu(request, payload: MenuIn, image: UploadedFile = File(...)):
    try:
        payload_dict = payload.dict()
        category = get_object_or_404(Category, id = payload_dict.pop('category'))
        menu = Menu(**payload_dict, category = category)
        menu.image.save(image.name, image)
    except:
        raise HttpError(400, 'Неккоректный запрос!')
    return menu


@api.put('/menu/{menu_id}', response = MenuOut, summary = 'Изменить информацию о позиции меню')
@check_permission('cafe.change_menu', raise_exception = True, use_auth = True)
def update_menu(request, menu_id: int, payload: MenuIn):
    try:
        menu = get_object_or_404(Menu, id = menu_id)
        for attribute, value in payload.dict().items():
            if attribute == 'category':
                category = get_object_or_404(Category, id = value)
                setattr(menu, attribute, category)
            else:
                setattr(menu, attribute, value)
        menu.save()
    except:
        raise HttpError(400, 'Неккоректный запрос!')
    return menu


@api.delete('/menu/{menu_id}', summary = 'Удалить позицию меню')
@check_permission('cafe.delete_menu', raise_exception = True, use_auth = True)
def delete_menu(request, menu_id: int):
    try:
        menu = get_object_or_404(Menu, id = menu_id)
        menu.delete()
    except:
        raise HttpError(400, 'Неккоректный запрос!')
    return {'Сообщение': 'Позиция меню была удалена!'}


@api.get('/menu/{category_id}/search', response = List[MenuOut], summary = 'Поиск позиции меню по названию')
def search_menu(request, category_id: int, search: str = Query(None, description = 'Поиск')):
    category = get_object_or_404(Category, id = category_id)
    return Menu.objects.filter(category = category, name__icontains = search)


''' API для позиций столиков '''


@api.get('/tables', response = List[TableOut], summary = 'Получить список столиков')
@check_permission('cafe.view_table', raise_exception = True, use_auth = True)
def get_tables(request):
    return Table.objects.all()


@api.post('/tables', response = TableOut, summary = 'Добавить столик')
@check_permission('cafe.add_table', raise_exception = True, use_auth = True)
def create_table(request, payload: TableIn):
    try:
        payload_dict = payload.dict()
        status = get_object_or_404(TableStatus, id = payload_dict.pop('status'))
        table = Table(**payload_dict, status = status)
        table.save()
    except:
        raise HttpError(406, 'Столик с данным номером уже существует!')
    return table


@api.delete('/tables/{table_id}', summary = 'Удалить столик')
@check_permission('cafe.delete_table', raise_exception = True, use_auth = True)
def delete_table(request, table_id: int):
    try:
        table = get_object_or_404(Table, id = table_id)
        table.delete()
    except:
        raise HttpError(400, 'Неккоректный запрос!')
    return {'Сообщение': 'Столик был удален!'}


@api.post('/tables/{table_id}/change_status', response = TableOut, summary = 'Изменить статус столика')
@check_permission('cafe.change_table', raise_exception = True, use_auth = True)
def change_table_status(request, table_id: int, status_id: int):
    try:
        table = get_object_or_404(Table, id = table_id)
        status = get_object_or_404(TableStatus, id = status_id)
        table.status = status
        table.save()
    except:
        raise HttpError(400, 'Некорректный запрос!')
    return table


''' API для позиций бронирований '''


@api.get('/reservations', response = List[ReservationOut], summary = 'Получить список бронирований')
@check_permission('cafe.view_reservation', raise_exception = True, use_auth = True)
def get_reservations(request):
    return Reservation.objects.all()


@api.post('/reservations', response = ReservationOut, summary = 'Добавить бронирование')
@check_permission('cafe.add_reservation', raise_exception = True, use_auth = True)
def create_reservation(request, payload: ReservationIn):
    try:
        payload_dict = payload.dict()
        table = get_object_or_404(Table, id = payload_dict.pop('table'))
        if table.status.id == 3:
            status = get_object_or_404(TableStatus, id = 2)
            table.status = status
            reservation = Reservation(**payload_dict, table = table)
        else:
            raise HttpError(406, 'Столик уже занят!')
        reservation.save()
    except:
        raise HttpError(400, 'Неккоректный запрос!')
    return reservation


@api.put('/reservations/{reservation_id}', response = ReservationOut, summary = 'Изменить информацию о бронировании')
@check_permission('cafe.change_reservation', raise_exception = True, use_auth = True)
def update_reservation(request, reservation_id: int, payload: ReservationIn):
    reservation = get_object_or_404(Reservation, id = reservation_id)
    for attribute, value in payload.dict().items():
        if attribute == 'table':
            table = get_object_or_404(Table, id = value)
            if table.status.id == 3:
                status = get_object_or_404(TableStatus, id = 2)
                table.status = status
                setattr(reservation, attribute, table)
            else:
                raise HttpError(406, 'Столик уже занят!')
        else:
            setattr(reservation, attribute, value)
        reservation.save()
    return reservation


@api.delete('/reservations/{reservation_id}', summary = 'Удалить бронирование')
@check_permission('cafe.delete_reservation', raise_exception = True, use_auth = True)
def delete_reservation(request, reservation_id: int):
    try:
        reservation = get_object_or_404(Reservation, id = reservation_id)
        reservation.delete()
    except:
        raise HttpError(400, 'Неккоректный запрос!')
    return {'Сообщение': 'Бронирование было удалено!'}


''' API для позиций заказов '''


@api.get('/orders', response = List[OrderItemOut], summary = 'Получить список заказов')
@check_permission('cafe.view_orderitem', raise_exception = True, use_auth = True)
def get_orders(request):
    return OrderItem.objects.all()


@api.get('/order/{order_id}/', response = List[OrderItemOut], summary = 'Получить информацию о заказе')
@check_permission('cafe.view_orderitem', raise_exception = True, use_auth = True)
def get_order(request, order_id: int):
    try:
        order = get_object_or_404(Order, id = order_id)
        order_items = OrderItem.objects.filter(order = order)
    except:
        raise HttpError(400, 'Неккоректный запрос!')
    return order_items


@api.post('/order', response = OrderOut, summary = 'Создать заказ')
@check_permission('cafe.add_order', raise_exception = True, use_auth = True)
def create_order(request, payload: OrderIn):
    try:
        payload_dict = payload.dict()
        status = get_object_or_404(OrderStatus, id = payload_dict.pop('status'))
        table = get_object_or_404(Table, id = payload_dict.pop('table'))
        try:
            reservation = Reservation.objects.get(id = payload_dict.pop('reservation'))
        except Reservation.DoesNotExist:
            reservation = None

        if table.status.id != 3:
            raise HttpError(406, 'Столик уже занят!')            

        if reservation is not None:
            order = Order(**payload_dict, table = table, status = status, reservation = reservation) 
        else:
            order = Order(**payload_dict, table = table, status = status)     
        order.save()
    except:
        raise HttpError(400, 'Неккоректный запрос!')
    return order


@api.post('/order/add_item', response = OrderItemOut, summary = 'Добавить позицию заказа в заказ')
@check_permission('cafe.add_orderitem', raise_exception = True, use_auth = True)
def add_order_item(request, payload: OrderItemIn):
    try:
        payload_dict = payload.dict()
        order = get_object_or_404(Order, id = payload_dict.pop('order'))
        menu = get_object_or_404(Menu, id = payload_dict.pop('menu'))
        order_item, created = OrderItem.objects.get_or_create(order = order, menu = menu, **payload_dict)
        if not created:
            order_item.quantity += 1
        order_item.price = order_item.get_amount()
        order_item.save() 
    except:
        raise HttpError(400, 'Неккоректный запрос!')
    return order_item


@api.post('/order/{order_item_id}/append', response = OrderItemOut, summary = 'Увеличить количество позиций заказа на 1')
@check_permission('cafe.change_orderitem', raise_exception = True, use_auth = True)
def append_order_item(request, order_item_id: int):
    try:
        order_item = get_object_or_404(OrderItem, id = order_item_id)
        order_item.quantity += 1
        order_item.save()
    except:
        raise HttpError(400, 'Неккоректный запрос!')
    return order_item


@api.post('/order/{order_item_id}/delete', response = OrderItemOut, summary = 'Уменьшить количество позиций заказа на 1')
@check_permission('cafe.change_orderitem', raise_exception = True, use_auth = True)
def delete_order_item(request, order_item_id: int):
    try:
        order_item = get_object_or_404(OrderItem, id = order_item_id)
        order_item.quantity -= 1
        if order_item.quantity == 0:
            order_item.delete()
        else:
            order_item.save()
        order_item.save()
    except:
        raise HttpError(400, 'Неккоректный запрос!')
    return order_item


@api.post('/order/{order_id}/change_status', response = OrderOut, summary = 'Изменить статус заказа')
@check_permission('cafe.change_order', raise_exception = True, use_auth = True)
def change_order_status(request, order_id: int, status_id: int):
    try:
        order = get_object_or_404(Order, id = order_id)
        status = get_object_or_404(OrderStatus, id = status_id)
        order.status = status
        order.save()
    except:
        raise HttpError(400, 'Неккоректный запрос!')
    return order


''' API для чеков на оплату '''


@api.get('/payments', response = List[PaymentOut], summary = 'Получить список всех чеков на оплату')
@check_permission('cafe.view_payment', raise_exception = True, use_auth = True)
def get_payments(request):
    return Payment.objects.all()


@api.get('/payments/{payment_id}', response = PaymentOut, summary = 'Получить информацию о чеке на оплату')
@check_permission('cafe.view_payment', raise_exception = True, use_auth = True)
def get_payment(request, payment_id: int):
    try:
        return get_object_or_404(Payment, id = payment_id)
    except:
        raise HttpError(400, 'Неккоректный запрос!')   


@api.post('/payments', response = PaymentOut, summary = 'Добавить чек на оплату')
@check_permission('cafe.add_payment', raise_exception = True, use_auth = True)
def create_payment(request, payload: PaymentIn):
    try:
        payload_dict = payload.dict()
        order = get_object_or_404(Order, id = payload_dict.pop('order'))
        payment = Payment(**payload_dict, order = order)
        payment.save()
    except:
        raise HttpError(400, 'Неккоректный запрос!')
    return payment


@api.post('/payments/{payment_id}/change_status', response = PaymentOut, summary = 'Изменить статус оплаты')
@check_permission('cafe.change_payment', raise_exception = True, use_auth = True)
def change_payment_status(request, payment_id: int):
    try:
        payment = get_object_or_404(Payment, id = payment_id)
        payment.status = True
        payment.save()
    except:
        raise HttpError(400, 'Неккоректный запрос!')
    return payment