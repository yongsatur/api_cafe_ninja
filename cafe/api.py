from ninja import NinjaAPI, Query, UploadedFile, File
from ninja.security import HttpBasicAuth
from ninja.errors import HttpError, AuthenticationError

from typing import List

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import permission_required

from .models import Category, Menu, Table, Reservation, Order, OrderItem, \
    OrderStatus, TableStatus, Payment
from .schemas import CategoryIn, CategoryOut, MenuIn, MenuOut, TableIn, \
    TableOut, ReservationIn, ReservationOut, OrderIn, OrderOut, \
    OrderItemIn, OrderItemOut, PaymentIn, PaymentOut


api = NinjaAPI(csrf = True)

@api.exception_handler(PermissionDenied)
def permission_error(request, e):
    return HttpResponse('У вас недостаточно прав для совершения данной операции!', status = 403)


''' API для авторизации '''


class BasicAuth(HttpBasicAuth):
    def authenticate(self, request, username, password):
        user = authenticate(username = username, password = password)
        if user:
            return user
        raise AuthenticationError('Ошибка авторизации!')
    
@api.get("/basic", auth = BasicAuth(), summary = 'Авторизация сотрудника')
def authentication(request):
    return { 'Сообщение': 'Пользователь авторизован!', 'Логин пользователя': request.auth.username }


''' API для категорий меню '''


@api.get('/menu', response = List[CategoryOut], summary = 'Получить список категорий меню')
def get_categories(request):
    return Category.objects.all()


@api.post('/categories', response = CategoryOut, summary = 'Добавить категорию')
@permission_required('auth.add_Категория', raise_exception = True)
def create_category(request, payload: CategoryIn):
    return Category.objects.create(**payload.dict())


@api.delete('/categories/{category_id}', summary = 'Удалить категорию')
@permission_required('auth.delete_Категория', raise_exception = True)
def delete_category(request, category_id: int):
    category = get_object_or_404(Category, id = category_id)
    category.delete()
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
@permission_required('auth.add_Позиция_меню', raise_exception = True)
def create_menu(request, payload: MenuIn, image: UploadedFile = File(...)):
    payload_dict = payload.dict()
    category = get_object_or_404(Category, id = payload_dict.pop('category'))
    menu = Menu(**payload_dict, category = category)
    menu.image.save(image.name, image)
    return menu


@api.put('/menu/{menu_id}', response = MenuOut, summary = 'Изменить информацию о позиции меню')
@permission_required('auth.change_Позиция_меню', raise_exception = True)
def update_menu(request, menu_id: int, payload: MenuIn):
    menu = get_object_or_404(Menu, id = menu_id)
    for attribute, value in payload.dict().items():
        if attribute == 'category':
            category = get_object_or_404(Category, id = value)
            setattr(menu, attribute, category)
        else:
            setattr(menu, attribute, value)
    menu.save()
    return menu


@api.delete('/menu/{menu_id}', summary = 'Удалить позицию меню')
@permission_required('auth.delete_Позиция_меню', raise_exception = True)
def delete_menu(request, menu_id: int):
    menu = get_object_or_404(Menu, id = menu_id)
    menu.delete()
    return {'Сообщение': 'Позиция меню была удалена!'}


@api.get('/menu/{category_id}/search', response = List[MenuOut], summary = 'Поиск позиции меню по названию')
def search_menu(request, category_id: int, search: str = Query(None, description = 'Поиск')):
    category = get_object_or_404(Category, id = category_id)
    return Menu.objects.filter(category = category, name__icontains = search)


''' API для позиций столиков '''


@api.get('/tables', response = List[TableOut], summary = 'Получить список столиков')
@permission_required('auth.view_Столик', raise_exception = True)
def get_tables(request):
    return Table.objects.all()


@api.post('/tables', response = TableOut, summary = 'Добавить столик')
@permission_required('auth.add_Столик', raise_exception = True)
def create_table(request, payload: TableIn):
    payload_dict = payload.dict()
    status = get_object_or_404(TableStatus, id = payload_dict.pop('status'))
    table = Table(**payload_dict, status = status)
    table.save()
    return table


@api.delete('/tables/{table_id}', summary = 'Удалить столик')
@permission_required('auth.delete_Столик', raise_exception = True)
def delete_table(request, table_id: int):
    table = get_object_or_404(Table, id = table_id)
    table.delete()
    return {'Сообщение': 'Столик был удален!'}


@api.post('/tables/{table_id}/change_status', response = TableOut, summary = 'Изменить статус столика')
@permission_required('auth.change_Столик', raise_exception = True)
def change_table_status(request, table_id: int, status_id: int):
    table = get_object_or_404(Table, id = table_id)
    status = get_object_or_404(TableStatus, id = status_id)
    table.status = status
    table.save()
    return table


''' API для позиций бронирований '''


@api.get('/reservations', response = List[ReservationOut], summary = 'Получить список бронирований')
@permission_required('auth.view_Бронирование', raise_exception = True)
def get_reservations(request):
    return Reservation.objects.all()


@api.post('/reservations', response = ReservationOut, summary = 'Добавить бронирование')
@permission_required('auth.add_Бронирование', raise_exception = True)
def create_reservation(request, payload: ReservationIn):
    payload_dict = payload.dict()
    table = get_object_or_404(Table, id = payload_dict.pop('table'))
    if table.status == 3:
        reservation = Reservation(**payload_dict, table = table)
    else:
        raise HttpError(406, 'Столик уже занят!')
    reservation.save()
    return reservation


@api.put('/reservations/{reservation_id}', response = ReservationOut, summary = 'Изменить информацию о бронировании')
@permission_required('auth.change_Бронирование', raise_exception = True)
def update_reservation(request, reservation_id: int, payload: ReservationIn):
    reservation = get_object_or_404(Reservation, id = reservation_id)
    for attribute, value in payload.dict().items():
        if attribute == 'table':
            table = get_object_or_404(Table, id = value)
            if table.status == 3:
                setattr(reservation, attribute, table)
            else:
                raise HttpError(406, 'Столик уже занят!')
        else:
            setattr(reservation, attribute, value)
    reservation.save()
    return reservation


@api.delete('/reservations/{reservation_id}', summary = 'Удалить бронирование')
@permission_required('auth.delete_Бронирование', raise_exception = True)
def delete_reservation(request, reservation_id: int):
    reservation = get_object_or_404(Reservation, id = reservation_id)
    reservation.delete()
    return {'Сообщение': 'Бронирование было удалено!'}


''' API для позиций заказов '''


@api.get('/orders', response = List[OrderItemOut], summary = 'Получить список заказов')
@permission_required('auth.view_Заказ', raise_exception = True)
def get_orders(request):
    return OrderItem.objects.all()


@api.get('/order/{order_id}/', response = List[OrderItemOut], summary = 'Получить информацию о заказе')
@permission_required('auth.view_Позиция_заказа', raise_exception = True)
def get_order(request, order_id: int):
    order = get_object_or_404(Order, id = order_id)
    order_items = OrderItem.objects.filter(order = order)
    return order_items


@api.post('/order', response = OrderOut, summary = 'Создать заказ')
@permission_required('auth.add_Заказ', raise_exception = True)
def create_order(request, payload: OrderIn):
    payload_dict = payload.dict()
    status = get_object_or_404(OrderStatus, id = payload_dict.pop('status'))
    table = get_object_or_404(Table, id = payload_dict.pop('table'))
    try:
        reservation = Reservation.objects.get(id = payload_dict.pop('reservation'))
    except Reservation.DoesNotExist:
        reservation = None

    if reservation is not None:
        order = Order(**payload_dict, table = table, status = status, reservation = reservation) 
    else:
        order = Order(**payload_dict, table = table, status = status)     
    order.save()
    return order


@api.post('/order/add_item', response = OrderItemOut, summary = 'Добавить позицию заказа в заказ')
@permission_required('auth.add_Позиция_заказа', raise_exception = True)
def add_order_item(request, payload: OrderItemIn):
    payload_dict = payload.dict()
    order = get_object_or_404(Order, id = payload_dict.pop('order'))
    menu = get_object_or_404(Menu, id = payload_dict.pop('menu'))
    order_item, created = OrderItem.objects.get_or_create(order = order, menu = menu, **payload_dict)
    if not created:
        order_item.quantity += 1
    order_item.price = order_item.get_amount()
    order_item.save() 
    return order_item


@api.post('/order/{order_item_id}/append', response = OrderItemOut, summary = 'Увеличить количество позиций заказа на 1')
@permission_required('auth.change_Позиция_заказа', raise_exception = True)
def append_order_item(request, order_item_id: int):
    order_item = get_object_or_404(OrderItem, id = order_item_id)
    order_item.quantity += 1
    order_item.save()
    return order_item


@api.post('/order/{order_item_id}/delete', response = OrderItemOut, summary = 'Уменьшить количество позиций заказа на 1')
@permission_required('auth.change_Позиция_заказа', raise_exception = True)
def delete_order_item(request, order_item_id: int):
    order_item = get_object_or_404(OrderItem, id = order_item_id)
    order_item.quantity -= 1
    if order_item.quantity == 0:
        order_item.delete()
    else:
        order_item.save()
    order_item.save()
    return order_item


@api.post('/order/{order_id}/change_status', response = OrderOut, summary = 'Изменить статус заказа')
@permission_required('auth.change_Заказ', raise_exception = True)
def change_order_status(request, order_id: int, status_id: int):
    order = get_object_or_404(Order, id = order_id)
    status = get_object_or_404(OrderStatus, id = status_id)
    order.status = status
    order.save()
    return order


''' API для чеков на оплату '''


@api.get('/payments', response = List[PaymentOut], summary = 'Получить список всех чеков на оплату')
@permission_required('auth.view_Оплата', raise_exception = True)
def get_payments(request):
    return Payment.objects.all()


@api.get('/payments/{payment_id}', response = PaymentOut, summary = 'Получить информацию о чеке на оплату')
@permission_required('auth.view_Оплата', raise_exception = True)
def get_payment(request, payment_id: int):
    return get_object_or_404(Payment, id = payment_id)


@api.post('/payments', response = PaymentOut, summary = 'Добавить чек на оплату')
@permission_required('auth.add_Оплата', raise_exception = True)
def create_payment(request, payload: PaymentIn):
    payload_dict = payload.dict()
    order = get_object_or_404(Order, id = payload_dict.pop('order'))
    payment = Payment(**payload_dict, order = order)
    payment.save()
    return payment


@api.get('/payments/{payment_id}/change_status', response = PaymentOut, summary = 'Изменить статус оплаты')
@permission_required('auth.change_Оплата', raise_exception = True)
def change_payment_status(request, payment_id: int):
    payment = get_object_or_404(Payment, id = payment_id)
    payment.status = True
    payment.save()
    return payment