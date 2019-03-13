from django.contrib import admin
from .models import Category, Product, User, Order, Cart_items, Reserve


class CategoryAdmin(admin.ModelAdmin):
    list_display = [field.name for field in Category._meta.fields if field.name != "id"]


class ProductAdmin(admin.ModelAdmin):
    list_display = [field.name for field in Product._meta.fields if field.name != "id"]


class UserAdmin(admin.ModelAdmin):
    list_display = [field.name for field in User._meta.fields]


class OrderAdmin(admin.ModelAdmin):
    list_display = [field.name for field in Order._meta.fields if field.name != "id"]


class Cart_itemsAdmin(admin.ModelAdmin):
    list_display = [field.name for field in Cart_items._meta.fields if field.name != "id"]


class ReserveAdmin(admin.ModelAdmin):
    list_display = [field.name for field in Reserve._meta.fields]


admin.site.register(Category, CategoryAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(User, UserAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(Cart_items, Cart_itemsAdmin)
admin.site.register(Reserve, ReserveAdmin)
