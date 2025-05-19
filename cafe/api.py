from ninja import NinjaAPI
from typing import List
from ninja import Query
from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate, login, logout
from ninja.errors import HttpError, AuthenticationError
from ninja import UploadedFile, File

from .models import Category, Menu, Table, Reservation, Order, OrderItem, \
    OrderStatus, TableStatus, Payment
from .schemas import CategoryIn, CategoryOut, MenuIn, MenuOut, TableIn, \
    TableOut, ReservationIn, ReservationOut, OrderIn, OrderOut, \
    OrderItemIn, OrderItemOut, PaymentIn, PaymentOut, UserAuthentication


api = NinjaAPI(csrf = True)


''' API для аккаунтов сотрудников '''


@api.post('/login', summary = 'Авторизация сотрудника')
def login_user(request, payload: UserAuthentication):
    user = authenticate(username = payload.username, password = payload.password)
    if user is not None:
        login(request, user)
        return { 'Сообщение': 'Пользователь авторизован!', 'Логин пользователя': user.username }
    raise AuthenticationError('Ошибка авторизации!')


@api.get('/account', summary = 'Проверка авторизации сотрудника')
def account(request):
    if not request.user.is_authenticated:
        raise HttpError(401, 'Пользователь не авторизован!')
    return { 'Авторизованный пользователь': request.user.username }


@api.post('/logout', auth = None, summary = 'Выход из аккаунта')
def logout_user(request):
    logout(request)
    return {'Сообщение': 'Вы вышли из аккаунта!'}


''' API для категорий меню '''


@api.get('/menu', response = List[CategoryOut], summary = 'Получить список категорий меню')
def get_categories(request):
    return Category.objects.all()


@api.post('/categories', response = CategoryOut, summary = 'Добавить категорию')
def create_category(request, payload: CategoryIn):
    account(request)
    if request.user.has_perm('auth.add_Категория'):
        category = Category.objects.create(**payload.dict())
    else:
        raise HttpError(403, 'У вас недостаточно прав!')
    return category


@api.delete('/categories/{category_id}', summary = 'Удалить категорию')
def delete_category(request, category_id: int):
    account(request)
    if request.user.has_perm('auth.delete_Категория'):
        category = get_object_or_404(Category, id = category_id)
        category.delete()
    else:
        raise HttpError(403, 'У вас недостаточно прав!')
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
def create_menu(request, payload: MenuIn, image: UploadedFile = File(...)):
    account(request)
    if request.user.has_perm('auth.add_Позиция_меню'):
        payload_dict = payload.dict()
        category = get_object_or_404(Category, id = payload_dict.pop('category'))
        menu = Menu(**payload_dict, category = category)
        menu.image.save(image.name, image)
    else:
        raise HttpError(403, 'У вас недостаточно прав!')
    return menu


@api.put('/menu/{menu_id}', response = MenuOut, summary = 'Изменить информацию о позиции меню')
def update_menu(request, menu_id: int, payload: MenuIn):
    account(request)
    if request.user.has_perm('auth.change_Позиция_меню'):
        menu = get_object_or_404(Menu, id = menu_id)
        for attribute, value in payload.dict().items():
            if attribute == 'category':
                category = get_object_or_404(Category, id = value)
                setattr(menu, attribute, category)
            else:
                setattr(menu, attribute, value)
        menu.save()
    else:
        raise HttpError(403, 'У вас недостаточно прав!')
    return menu


@api.delete('/menu/{menu_id}', summary = 'Удалить позицию меню')
def delete_menu(request, menu_id: int):
    account(request)
    if request.user.has_perm('auth.delete_Позиция_меню'):
        menu = get_object_or_404(Menu, id = menu_id)
        menu.delete()
    else:
        raise HttpError(403, 'У вас недостаточно прав!')
    return {'Сообщение': 'Позиция меню была удалена!'}


@api.get('/menu/{category_id}/search', response = List[MenuOut], summary = 'Поиск позиции меню по названию')
def search_menu(request, category_id: int, search: str = Query(None, description = 'Поиск')):
    category = get_object_or_404(Category, id = category_id)
    return Menu.objects.filter(category = category, name__icontains = search)


''' API для позиций столиков '''

@api.get('/tables', response = List[TableOut], summary = 'Получить список столиков')
def get_tables(request):
    account(request)
    if request.user.has_perm('auth.view_Столик'):
        return Table.objects.all()
    else:
        raise HttpError(403, 'У вас недостаточно прав!')


@api.post('/tables', response = TableOut, summary = 'Добавить столик')
def create_table(request, payload: TableIn):
    account(request)
    if request.user.has_perm('auth.add_Столик'):
        payload_dict = payload.dict()
        status = get_object_or_404(TableStatus, id = payload_dict.pop('status'))
        table = Table(**payload_dict, status = status)
        table.save()
    else:
        raise HttpError(403, 'У вас недостаточно прав!')
    return table


@api.delete('/tables/{table_id}', summary = 'Удалить столик')
def delete_table(request, table_id: int):
    account(request)
    if request.user.has_perm('auth.delete_Столик'):
        table = get_object_or_404(Table, id = table_id)
        table.delete()
    else:
        raise HttpError(403, 'У вас недостаточно прав!')
    return {'Сообщение': 'Столик был удален!'}


@api.post('/tables/{table_id}/change_status', response = TableOut, summary = 'Изменить статус столика')
def change_table_status(request, table_id: int, status_id: int):
    account(request)
    if request.user.has_perm('auth.change_Столик'):
        table = get_object_or_404(Table, id = table_id)
        status = get_object_or_404(TableStatus, id = status_id)
        table.status = status
        table.save()
    else:
        raise HttpError(403, 'У вас недостаточно прав!')
    return table


''' API для позиций бронирований '''


@api.get('/reservations', response = List[ReservationOut], summary = 'Получить список бронирований')
def get_reservations(request):
    account(request)
    if request.user.has_perm('auth.view_Бронирование'):
        return Reservation.objects.all()
    else:
        raise HttpError(403, 'У вас недостаточно прав!')


@api.post('/reservations', response = ReservationOut, summary = 'Добавить бронирование')
def create_reservation(request, payload: ReservationIn):
    account(request)
    if request.user.has_perm('auth.add_Бронирование'):
        payload_dict = payload.dict()
        table = get_object_or_404(Table, id = payload_dict.pop('table'))
        reservation = Reservation(**payload_dict, table = table)
        reservation.save()
    else:
        raise HttpError(403, 'У вас недостаточно прав!')
    return reservation


@api.put('/reservations/{reservation_id}', response = ReservationOut, summary = 'Изменить информацию о позиции меню')
def update_reservation(request, reservation_id: int, payload: ReservationIn):
    account(request)
    if request.user.has_perm('auth.change_Бронирование'):
        reservation = get_object_or_404(Reservation, id = reservation_id)
        for attribute, value in payload.dict().items():
            if attribute == 'table':
                table = get_object_or_404(Table, id = value)
                setattr(reservation, attribute, table)
            else:
                setattr(reservation, attribute, value)
        reservation.save()
    else:
        raise HttpError(403, 'У вас недостаточно прав!')
    return reservation


@api.delete('/reservations/{reservation_id}', summary = 'Удалить бронирование')
def delete_reservation(request, reservation_id: int):
    account(request)
    if request.user.has_perm('auth.delete_Бронирование'):
        reservation = get_object_or_404(Reservation, id = reservation_id)
        reservation.delete()
    else:
        raise HttpError(403, 'У вас недостаточно прав!')
    return {'Сообщение': 'Бронирование было удалено!'}


''' API для позиций заказов '''


@api.get('/orders', response = List[OrderItemOut], summary = 'Получить список заказов')
def get_orders(request):
    account(request)
    if request.user.has_perm('auth.'):
        return OrderItem.objects.all()
    else:
        raise HttpError(403, 'У вас недостаточно прав!')


@api.get('/order/{order_id}/', response = List[OrderItemOut], summary = 'Получить информацию о заказе')
def get_order(request, order_id: int):
    account(request)
    if request.user.has_perm('auth.view_Позиция_заказа'):
        try:
            order = get_object_or_404(Order, id = order_id)
            order_items = OrderItem.objects.filter(order = order)
            return order_items
        except: 
            raise HttpError(404, 'Произошла ошибка!')
    else:
        raise HttpError(403, 'У вас недостаточно прав!')


@api.post('/order', response = OrderOut, summary = 'Создать заказ')
def create_order(request, payload: OrderIn):
    account(request)
    if request.user.has_perm('auth.add_Заказ'):
        payload_dict = payload.dict()
        status = get_object_or_404(OrderStatus, id = 1)
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
    else:
        raise HttpError(403, 'У вас недостаточно прав!')
    return order


@api.post('/order/add_item', response = OrderItemOut, summary = 'Добавить позицию заказа в заказ')
def add_order_item(request, payload: OrderItemIn):
    account(request)
    if request.user.has_perm('auth.add_Позиция_заказа'):
        payload_dict = payload.dict()
        order = get_object_or_404(Order, id = payload_dict.pop('order'))
        menu = get_object_or_404(Menu, id = payload_dict.pop('menu'))

        order_item, created = OrderItem.objects.get_or_create(order = order, menu = menu)
        if not created:
            order_item.quantity += 1

        order_item.save() 
    else:
        raise HttpError(403, 'У вас недостаточно прав!')
    return order_item


@api.post('/order/{order_item_id}/append', response = OrderItemOut, summary = 'Увеличить количество позиций заказа на 1')
def add_order_item(request, order_item_id: int):
    account(request)
    if request.user.has_perm('auth.change_Позиция_заказа'):
        order_item = get_object_or_404(OrderItem, id = order_item_id)
        order_item.quantity += 1
        order_item.save()
    else:
        raise HttpError(403, 'У вас недостаточно прав!')
    return order_item


@api.post('/order/{order_item_id}/delete', response = OrderItemOut, summary = 'Уменьшить количество позиций заказа на 1')
def delete_order_item(request, order_item_id: int):
    account(request)
    if request.user.has_perm('auth.change_Позиция_заказа'):
        order_item = get_object_or_404(OrderItem, id = order_item_id)
        order_item.quantity -= 1
        if order_item.quantity == 0:
            order_item.delete()
        else:
            order_item.save()
        order_item.save()
    else:
        raise HttpError(403, 'У вас недостаточно прав!')
    return order_item


@api.post('/order/{order_id}/change_status', response = OrderOut, summary = 'Изменить статус заказа')
def change_order_status(request, order_id: int, status_id: int):
    if request.user.has_perm('auth.change_Заказ'):
        order = get_object_or_404(Order, id = order_id)
        status = get_object_or_404(OrderStatus, id = status_id)
        order.status = status
        order.save()
    else:
        raise HttpError(403, 'У вас недостаточно прав!')
    return order


''' API для чеков на оплату '''


@api.get('/payments', response = List[PaymentOut], summary = 'Получить список всех чеков на оплату')
def get_payments(request):
    if request.user.has_perm('auth.view_Оплата'):
        return Payment.objects.all()
    else:
        raise HttpError(403, 'У вас недостаточно прав!')


@api.get('/payments/{payment_id}', response = PaymentOut, summary = 'Получить информацию о чеке на оплату')
def get_payment(request, payment_id: int):
    if request.user.has_perm('auth.view_Оплата'):
        return get_object_or_404(Payment, id = payment_id)
    else:
        raise HttpError(403, 'У вас недостаточно прав!')


@api.post('/payments', response = PaymentOut, summary = 'Добавить чек на оплату')
def create_payment(request, payload: PaymentIn):
    if request.user.has_perm('auth.add_Оплата'):
        payload_dict = payload.dict()
        order = get_object_or_404(Order, id = payload_dict.pop('order'))
        payment = Payment(**payload_dict, order = order)
        payment.save()
    else:
        raise HttpError(403, 'У вас недостаточно прав!')
    return payment


@api.get('/payments/{payment_id}/change_status', response = PaymentOut, summary = 'Изменить статус оплаты')
def change_payment_status(request, payment_id: int):
    if request.user.has_perm('auth.change_Оплата'):
        payment = get_object_or_404(Payment, id = payment_id)
        payment.status = True
        payment.save()
    else:
        raise HttpError(403, 'У вас недостаточно прав!')
    return payment