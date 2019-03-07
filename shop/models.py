from django.db import models
from django.db import transaction
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from datetime import datetime, timedelta
from django.db.models import Sum, F, ExpressionWrapper


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
    qu_in_stock = models.PositiveIntegerField(default=0, db_index=True)
    reserved = models.PositiveIntegerField(default=0, blank=True, db_index=True)
    allow_res_per_user = models.SmallIntegerField(default=1)
    photo = models.ImageField(upload_to='', verbose_name=u'Photo', help_text='jpg/png - file', blank=True, null=True)
    short_description = models.CharField(max_length=256)
    description = models.TextField(null=True, blank=True)
    date_of_come = models.DateTimeField()

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
    is_modered = models.BooleanField(choices=(('False', False), ('True', True)), default=False)


    def __str__(self):
        return self.full_name

    def get_cart(self):
        return Cart_items.objects.filter(customer=self).select_related('product')

    def check_cart(self, product_code):
        ids = []
        cart = self.get_cart()
        for item in cart:
            ids.append(item.product_code)
        return product_code in ids

    @transaction.atomic
    def add_to_cart(self, product_code, quantity):
        try:
            product_code = int(product_code)
            quantity = int(quantity)
            cart = self.get_cart()  # queryset of objects in cart
            if cart:
                if self.check_cart(product_code):
                    product = cart.get(product__code=product_code)
                    product.quantity += quantity
                    product.save()
                    return {'result': 'Success', 'reason': 'updated'}
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

    def cart_to_order(self):  # save products from cart to order
        cart = self.get_cart()
        order_items = []
        if cart:
            with transaction.atomic():
                order = Order.objects.create(customer=self)
                for obj in cart:
                    if (obj.product.qu_in_stock - obj.product.reserved - obj.quantity) >= 0:
                        order_items.append(Order_items(order=order, code=obj.product.code, name=obj.product.name,
                                                       price=obj.product.price, discount=obj.product.discount))
                    else:
                        raise ValueError(f"Not enough quantity of product {obj.product} "
                                        f"in stock. You should to choose a smaller quantity!")
                Order_items.objects.bulk_create(order_items)
                cart_wt = Order_items.objects.filter(order=order).aggregate(cart_total=ExpressionWrapper(
                    Sum(F('price') - F('price') * F('discount') / 100), output_field=models.DecimalField()))
                order.total_cost = cart_wt['cart_total']
                order.save()
                deleted = cart.delete()
                result = {'result': 'success', 'reason': f'replaced {deleted[0]}'}
        return result

    @transaction.atomic
    def reserve_product(self, product_code, quantity=1, client_resp=False):  # client_resp - check for client consent
        product = Product.objects.get(code=product_code)
        if self.check_cart(product_code):
            if not client_resp:
                return {'result': 'success', 'reason': {'question': f'Product {product} is in your cart,'
                    f' would you move it to reserve - set client_resp=Yes,'
                    f'do nothing - set client_resp=True, create reserve without touch of cart - set it to No'}}
            elif client_resp == 'Yes':
                self.get_cart().get(product_code=product_code).delete()
        Reserve.objects.create(product=product, customer=self, quantity=quantity)
        result = {'result': 'success', 'reason': f'Item {product} had been moved to reserve on 24 hours'}
        return result


class Cart_items(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()

    def __str__(self):
        return self.product


class Order(models.Model):
    customer = models.ForeignKey(Customer, related_name='orders', on_delete=models.CASCADE)
    total_cost = models.DecimalField(default=0, decimal_places=2, max_digits=8)
    date = models.DateTimeField(auto_now_add=True)
    paid = models.BooleanField(default=False, choices=(('True', True), ('False', False)))


class Order_items(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    code = models.CharField(max_length=32)
    name = models.CharField(max_length=64)
    price = models.DecimalField(null=False, decimal_places=2, max_digits=7)
    discount = models.FloatField()


class Reserve(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    date_of_reserve = models.DateTimeField(auto_now_add=True)