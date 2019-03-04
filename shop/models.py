from django.db import models
from django.db import transaction
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from django.db.models import Sum
from django.db.models import F
import json

class Category(models.Model):
    name = models.CharField(max_length=64, unique=True)
    parent = models.ForeignKey('self', null=True, max_length=64, verbose_name='Parent', blank=True,
                               db_index=True, on_delete=models.CASCADE)
    icon = models.ImageField(upload_to='', verbose_name=u'Photo', help_text='jpg/png - file')
    description = models.TextField(max_length=512, blank=True, null=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    code = models.AutoField(primary_key=True)
    name = models.CharField(max_length=64, db_index=True)
    category = models.ForeignKey(Category, max_length=64, verbose_name='Category', db_index=True,
                                 on_delete=models.CASCADE)
    price = models.DecimalField(null=False, decimal_places=2, max_digits=7)
    discount = models.FloatField(default=0)
    qu_in_stock = models.IntegerField(default=0, db_index=True)
    photo = models.ImageField(upload_to='', verbose_name=u'Photo', help_text='jpg/png - file', blank=True, null=True)
    short_description = models.CharField(max_length=256)
    description = models.TextField(null=True, blank=True)
    date_of_come = models.DateTimeField(default=None)

    def __str__(self):
        return self.name


class Customer(models.Model):
    id = models.AutoField(primary_key=True)
    full_name = models.CharField(max_length=128, db_index=True, null=False)
    email = models.EmailField(max_length=64, unique=True, db_index=True)
    phone = models.CharField(max_length=13, unique=True, db_index=True)
    address = models.CharField(max_length=256, blank=True, null=True)
    zip_code = models.IntegerField()
    birth_day = models.DateField(default=None, null=True)
    purse = models.DecimalField(default=0, decimal_places=2, max_digits=7)
    pwd = models.CharField(max_length=64)
    is_modered = models.CharField(max_length=5,
                                  choices=(('false', 'false'), ('true', 'true')), default='false')

    def __str__(self):
        return self.full_name

    def get_cart(self):
        return Cart_items.objects.filter(customer=self)

    @transaction.atomic
    def add_to_cart(self, product_code, quantity):
        try:
            product_code = int(product_code)
            quantity = int(quantity)
            cart = self.get_cart()  # queryset of objects in cart
            if cart:
                ids = []
                for item in cart:
                    ids.append(item.product.code)
                if product_code in ids:
                    product = cart.get(product__code=product_code)
                    product.quantity += quantity
                    product.save()
                    result = {'result': 'Success', 'reason': 'updated'}
            else:
                product = Product.objects.get(code=product_code)
                Cart_items.objects.create(customer=self, product=product, quantity=quantity)
                result = {'result': 'Success', 'reason': 'created'}
        except (TypeError, ObjectDoesNotExist) as e:
            result = {'result': 'Error', 'reason': repr(e)}
        return result

    def del_from_cart(self, *ids):
        try:
            cart = self.get_cart()
            deleted = cart.filter(id__in=ids).delete()
        except ObjectDoesNotExist as e:
            result = {'result': 'Error', 'reason': repr(e)}
        else:
            result = {'result': 'Success', 'reason': f'deleted: {deleted}'}
            return result

    def cart_to_order(self):
        cart = self.get_cart()
        order_items = []
        if cart:
            with transaction.atomic():
                order = Order.objects.create(Customer=self, total_cost=cart.aggregate(Sum(F('price') - F('price')*F('discount')/100)))
                objs = list(cart.select_related('product'))
                for obj in objs:
                    order_items.append(Order_items(order=order, code=obj.code, name=obj.name, price=obj.price,
                                                   discount=obj.discount))
                Order_items.objects.bulk_create(order_items)
                deleted = cart.delete()
                result = {'result': 'success', 'reason': f'replaced {deleted[0]}'}
        return result


class Cart_items(models.Model):
    customer = models.OneToOneField(Customer, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()


class Order(models.Model):
    customer = models.ForeignKey(Customer, related_name='orders', on_delete=models.CASCADE)
    total_cost = models.DecimalField(default=0, decimal_places=2, max_digits=8)
    date = models.DateTimeField(default=timezone.now())


class Order_items(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    code = models.CharField(max_length=32)
    name = models.CharField(max_length=64)
    price = models.DecimalField(null=False, decimal_places=2, max_digits=7)
    discount = models.FloatField(default=0)

