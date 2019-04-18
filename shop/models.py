from django.db import models
from django.db import transaction
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ObjectDoesNotExist
from datetime import datetime, timedelta
from django.db.models import Sum, F, ExpressionWrapper
from django.contrib.auth.decorators import login_required
from shop.exceptions import (QuantityKeyError, CartItemIdKeyError)



class Category(models.Model):
    name = models.CharField(max_length=64, unique=True)
    parent = models.ForeignKey('self', null=True, max_length=64, verbose_name='Parent', blank=True,
                               db_index=True, on_delete=models.CASCADE)
    photo = models.ImageField(upload_to='', verbose_name=u'Photo', help_text='jpg/png - file')
    description = models.TextField(max_length=512, blank=True, null=True)


    def __str__(self):
        return self.name



class Product(models.Model):
    code = models.AutoField(primary_key=True)
    name = models.CharField(max_length=64, db_index=True)
    category = models.ForeignKey(Category, max_length=64, verbose_name='Category', db_index=True,
                                 on_delete=models.CASCADE)
    price = models.DecimalField(null=False, decimal_places=2, max_digits=9)
    discount = models.DecimalField(default=0, decimal_places=2, max_digits=9)
    qu_in_stock = models.PositiveIntegerField(default=0, db_index=True)
    reserved = models.PositiveIntegerField(default=0, blank=True, db_index=True)
    allow_res_per_user = models.SmallIntegerField(default=1)
    photo = models.ImageField(upload_to='', verbose_name=u'Photo', help_text='jpg/png - file', blank=True, null=True)
    short_description = models.CharField(max_length=256)
    description = models.TextField(null=True, blank=True)
    date_of_come = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class User(AbstractUser):
    
    phone = models.CharField(max_length=13, unique=True, db_index=True)
    address = models.CharField(max_length=256, blank=True, null=True)
    zip_code = models.IntegerField(null=True, blank=True)
    birth_day = models.DateField(default=None, null=True)

    # EMAIL_FIELD = 'email'
    # USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'phone']

    class Meta(AbstractUser.Meta):
        swappable = 'AUTH_USER_MODEL'

    def __str__(self):
        return self.username

    def get_cart(self):
        cart = Cart_items.objects.filter(user=self).select_related('product')

        total_cart_cost = Cart_items.objects.filter(user=self).aggregate(cart_total=ExpressionWrapper(
                    Sum(F('product__price') * F('quantity')), output_field=models.DecimalField()))
        total_cart_cost['cart_total'] = str(total_cart_cost['cart_total'])
        cart_ret = list(
            cart.values('id', 'product__code', 'product__name', 'product__price', 'quantity', 'user__id'))
        json_cart = {'cart': cart_ret}
        json_cart.update(total_cart_cost)
        return cart, json_cart

    def check_cart(self, product_code):  # returns tuple of quantity of checked product and it's item in cart or False if it DoesNotExist
        try:
            item = Cart_items.objects.get(product=product_code, user=self)
        except ObjectDoesNotExist:
            return False
        return item

    def del_old_reserves(self):
        res_timelim = datetime.now() - timedelta(hours=24)
        Reserve.objects.filter(datetime_of_reserve__lt=res_timelim).delete()  # delete old reserves

    def check_reserved(self, product_code):
        try:
            product = Product.objects.get(code=product_code)
            reserved = Reserve.objects.get(product=product, user=self)
        except ObjectDoesNotExist:
            return 0, 0
        return reserved.quantity, reserved

    @transaction.atomic
    def add_to_cart(self, product_code, quantity):
        cart, jc = self.get_cart()  # queryset of objects in cart
        product = Product.objects.get(code=product_code)
        if cart:
            if self.check_cart(product_code):
                cart_item = cart.get(product__code=product_code)
                if cart_item.quantity + quantity > 0:
                    cart_item.quantity += quantity
                    cart_item.save()
                else:
                    cart_item.delete()
                cart, jc = self.get_cart()
                return jc
        if quantity < 0:
            raise QuantityKeyError
        Cart_items.objects.create(user=self, product=product, quantity=quantity)
        cart, jc = self.get_cart()
        return jc

    def del_from_cart(self, ids):
            cart, jc = self.get_cart()
            deleted, d = cart.filter(id__in=ids).delete()
            cart, jc = self.get_cart()
            if not deleted:
                raise CartItemIdKeyError
            return jc

    def cart_to_order(self):  # save products from cart to order
        cart, jc = self.get_cart()
        order_items = []
        self.del_old_reserves()
        if cart:
            with transaction.atomic():
                order = Order.objects.create(user=self)

                for obj in cart:
                    res_quantity, res_item = self.check_reserved(obj.product.code)
                    if res_quantity:
                        if res_quantity >= obj.quantity:
                            res_item.quantity -= obj.quantity
                            res_item.save()
                            obj.product.reserved -= obj.quantity
                            obj.product.save()
                        else:
                            obj.product.reserved -= res_quantity
                            res_item.delete()
                    if (obj.product.qu_in_stock - obj.product.reserved - obj.quantity) >= 0:
                        order_items.append(Order_items(order=order, code=obj.product.code, name=obj.product.name,
                                                           quantity=obj.quantity,
                                                           price=obj.product.price, discount=obj.product.discount))
                        obj.product.qu_in_stock -= obj.quantity
                        obj.product.save()
                    else:
                        raise ValueError(f"Not enough quantity of product {obj.product} "
                                            f"in stock. You should to choose a smaller quantity!")
                Order_items.objects.bulk_create(order_items)
                cart_wt = Order_items.objects.filter(order=order).aggregate(cart_total=ExpressionWrapper(
                    Sum(F('price') * F('quantity')), output_field=models.DecimalField()))
                order.total_cost = cart_wt['cart_total']
                order.save()
                cart.delete()
                order_val = Order.objects.values().get(id=order.id)
                items = list(order.order_items_set.values())
                result = {'order': order_val, 'order_items': items}
        return result

    @login_required
    @transaction.atomic
    def reserve_product(self, product_code, quantity=1, client_resp=False):  # client_resp - check for client consent
        product = Product.objects.get(code=product_code)
        quantity = int(quantity)
        available_quantity = product.qu_in_stock - product.reserved
        if available_quantity - quantity >= 1 and quantity <= product.allow_res_per_user:
            if self.check_cart(product_code):
                if not client_resp:
                    return {'result': 'success', 'reason': {'question': f'Product {product} is in your cart,'
                        f' would you move it to reserve - set client_resp=Yes,'
                        f'do nothing - set client_resp=True, create reserve without touch of cart - set it to No'}}
                elif client_resp == 'Yes':
                    self.get_cart().get(product=product).delete()
            reserve, created = Reserve.objects.get_or_create(product=product, user=self, quantity=quantity)
            if created:
                product.reserved += quantity
                product.save()
                result = {'result': 'success', 'reason': f'Item {product} had been moved to reserve on 24 hours.'}
        else:
            result = {'result': 'Error', 'reason': f"You can't reserve {product}."}
        return result

    def create_obj(self, request):
        if request.POST['obj_type'] == 'category':
            return Category.objects.create(name=request.POST['name'], description=request.POST['description'],
                                           photo=request.FILES['photo'])
        elif request.POST['obj_type'] == 'product':
            category = Category.objects.get(name=request.POST['category'])
            return Product.objects.create(name=request.POST['name'], category=category,
                                          price=request.POST['price'], discount=request.POST.get('discount', 0),
                                          description=request.POST['description'], photo=request.FILES['photo'],
                                          short_description=request.POST['short_description'])
        else:
            raise KeyError('Key "obj_type"  had been set incorrectly!')


class Cart_items(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()


    def __str__(self):
        return self.product.name

    class Meta:
        unique_together = (("product", "user"),)
        verbose_name_plural = 'Cart items'

class Order(models.Model):
    user = models.ForeignKey(User, related_name='orders', on_delete=models.CASCADE)
    total_cost = models.DecimalField(default=0, decimal_places=2, max_digits=8, null=True)
    date = models.DateTimeField(auto_now_add=True)
    paid = models.BooleanField(default=False, choices=(('True', True), ('False', False)))
    status = models.CharField(max_length=16, default='processing')


class Order_items(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    code = models.CharField(max_length=32)
    name = models.CharField(max_length=64)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(null=False, decimal_places=2, max_digits=9)
    discount = models.DecimalField(null=False, decimal_places=2, max_digits=9)


class Reserve(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    datetime_of_reserve = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (("product", "user"),)
