from django.contrib import admin
from .models import Category, Menu, Table, Reservation, Order, OrderItem, OrderStatus, TableStatus, Payment


admin.site.register(OrderStatus)
admin.site.register(TableStatus)


class CategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
admin.site.register(Category, CategoryAdmin)


class MenuAdmin(admin.ModelAdmin):
    list_display = ['category', 'name', 'slug', 'weight', 'capacity', 'price', 'description', 'image']
    prepopulated_fields = {'slug': ('name',)}
admin.site.register(Menu, MenuAdmin)


class TableAdmin(admin.ModelAdmin):
    list_display = ['number', 'status']
admin.site.register(Table, TableAdmin)


class ReservationAdmin(admin.ModelAdmin):
    list_display = ['table', 'client_name', 'client_phone', 'datetime', 'quest_count', 'comment']
admin.site.register(Reservation, ReservationAdmin)


class OrderItemAdmin(admin.StackedInline):
    extra = 0
    model = OrderItem
    fields = ['menu', 'price', 'quantity']


class PaymentAdmin(admin.StackedInline):
    extra = 0
    model = Payment
    fields = ['order', 'status']


class OrderAdmin(admin.ModelAdmin):
    list_display = ['table', 'reservation', 'totalAmount', 'status', 'created_at',]
    inlines = [OrderItemAdmin, PaymentAdmin]
admin.site.register(Order, OrderAdmin)


class PaymentsAdmin(admin.ModelAdmin):
    list_display = ['order', 'status']
admin.site.register(Payment, PaymentsAdmin)