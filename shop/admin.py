from django.contrib import admin
from .models import Category, Product, Customer, Order, Cart_items


class CategoryAdmin(admin.ModelAdmin):
    list_display = [field.name for field in Category._meta.fields if field.name != "id"]


class ProductAdmin(admin.ModelAdmin):
    list_display = [field.name for field in Product._meta.fields if field.name != "id"]


class CustomerAdmin(admin.ModelAdmin):
    list_display = [field.name for field in Customer._meta.fields if field.name != "id"]


class OrderAdmin(admin.ModelAdmin):
    list_display = [field.name for field in Order._meta.fields if field.name != "id"]


class Cart_itemsAdmin(admin.ModelAdmin):
    list_display = [field.name for field in Cart_items._meta.fields if field.name != "id"]


admin.site.register(Category, CategoryAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Customer, CustomerAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(Cart_items, Cart_itemsAdmin)
