from django.db import models
from django.urls import reverse


class Category(models.Model):
    name = models.CharField(verbose_name = 'Наименование', max_length = 250)
    slug = models.SlugField(verbose_name = 'Slug', max_length = 250, unique = True)

    class Meta:
        ordering = ('name', )
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.name


class Menu(models.Model):
    category = models.ForeignKey(Category, verbose_name = 'Категория', related_name = 'menu', on_delete = models.CASCADE)
    name = models.CharField(verbose_name = 'Наименование', max_length = 250)
    slug = models.SlugField(verbose_name = 'Slug', max_length = 250)
    weight = models.DecimalField(verbose_name = 'Вес', max_digits = 10, decimal_places = 2, blank = True, null = True)
    capacity = models.DecimalField(verbose_name = 'Объем', max_digits = 10, decimal_places = 2, blank = True, null = True)
    price = models.DecimalField(verbose_name = 'Цена', max_digits = 10, decimal_places = 2)
    description = models.TextField(verbose_name = 'Описание', blank = True, null = True)
    image = models.ImageField(verbose_name = 'Изображение', upload_to = 'images/', blank = True, null = True)

    class Meta:
        ordering = ('name', )
        verbose_name = 'Позиция меню'
        verbose_name_plural = 'Позиции меню'

    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('menu_detail', kwargs = { 'id': self.id, 'slug': self.slug })
    

class TableStatus(models.Model):
    name = models.CharField(verbose_name = 'Наименование', max_length = 250)

    class Meta:
        verbose_name = 'Статус столика'
        verbose_name_plural = 'Статусы столиков'

    def __str__(self):
        return self.name
    

class Table(models.Model):
    number = models.PositiveIntegerField(verbose_name = 'Номер столика', unique = True)
    status = models.ForeignKey(TableStatus, verbose_name = 'Статус', on_delete = models.CASCADE)

    class Meta:
        verbose_name = 'Столик'
        verbose_name_plural = 'Столики'

    def __str__(self):
        return 'Столик №' + str(self.number)
    

class Reservation(models.Model):
    table = models.ForeignKey(Table, verbose_name = 'Столик', on_delete = models.CASCADE)
    client_name = models.CharField(verbose_name = 'Фамилия Имя Отчество', max_length = 250)
    client_phone = models.CharField(verbose_name = 'Номер телефона', max_length = 20)
    datetime = models.DateTimeField(verbose_name = 'Дата и время')
    quest_count = models.PositiveIntegerField(verbose_name = 'Количество', default = 1)
    comment = models.TextField(verbose_name = 'Примечания', blank = True, null = True)

    class Meta:
        ordering = ('datetime', )
        verbose_name = 'Бронирование'
        verbose_name_plural = 'Бронирования'

    def __str__(self):
        return self.client_name + ' (' + self.client_phone + ')'


class OrderStatus(models.Model):
    name = models.CharField(verbose_name = 'Наименование', max_length = 250)

    class Meta:
        verbose_name = 'Статус заказа'
        verbose_name_plural = 'Статусы заказов'

    def __str__(self):
        return self.name


class Order(models.Model):
    table = models.ForeignKey(Table, verbose_name = 'Столик', on_delete = models.CASCADE)
    reservation = models.OneToOneField(Reservation, verbose_name = 'Клиент', on_delete = models.CASCADE, blank = True, null = True)
    status = models.ForeignKey(OrderStatus, verbose_name = 'Статус', on_delete = models.CASCADE)
    totalAmount = models.DecimalField(verbose_name = 'Итоговая стоимость', max_digits = 10, decimal_places = 2)
    created_at = models.DateTimeField(verbose_name = 'Дата создания', auto_now_add = True)

    class Meta:
        ordering = ('created_at', )
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    def __str__(self):
        return 'Заказ №' + str(self.id)

    def get_total_amount(self):
        return sum(item.get_amount() for item in self.order_items.all())  


class OrderItem(models.Model):
    order = models.ForeignKey(Order, verbose_name = 'Заказ', related_name = 'order_items', on_delete = models.CASCADE)
    menu = models.ForeignKey(Menu, verbose_name = 'Позиция меню', on_delete = models.CASCADE)
    price = models.DecimalField(verbose_name = 'Стоимость', max_digits = 10, decimal_places = 2)
    quantity = models.PositiveBigIntegerField(verbose_name = 'Количество', default = 1)

    class Meta:
        verbose_name = 'Позиция заказа'
        verbose_name_plural = 'Позиции заказа'

    def get_amount(self):
        self.price = self.menu.price * self.quantity
        return self.price
    

class Payment(models.Model):
    order = models.OneToOneField(Order, verbose_name = 'Заказ', related_name = 'order_payments', on_delete = models.CASCADE)
    status = models.BooleanField(verbose_name = 'Статус', default = False)

    class Meta:
        verbose_name = 'Оплата'
        verbose_name_plural = 'Оплаты'

    def __str__(self):
        return 'Оплата для заказа №' + str(self.order.id)