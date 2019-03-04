from django.shortcuts import render
from .models import Product, Category, Customer, Order
from django.http import JsonResponse
import json


def get_customer(request):
    data = request.POST
    customer_id = data.get('customer_id')
    try:
        result = Customer.objects.get(id=customer_id)
    except Exception as e:
        result = {'result': 'Error', 'reason': repr(e)}
    return result


def index(request):
    if request.GET.get('id'):
        cid = request.GET.get('id')
        cat = Category.objects.get(id=cid)
        categories = cat.category_set.all()
        products = cat.product_set.all()
        return render(request, 'shop/index.html', {'categories': categories, 'products': products})
    elif request.GET.get('code'):
        pcode = request.GET.get('code')
        product = Product.objects.get(code=pcode)
        customer = Customer.objects.values('id').get(id=1)

        return render(request, 'shop/prod_detail.html', {'product': product, 'customer': customer})
    else:
        categories = Category.objects.filter(parent=None)
        return render(request, 'shop/index.html', {'categories': categories})


def get_cart(request):
    customer = get_customer(request)
    if isinstance(customer, Customer):
        result = list(customer.get_cart().values())
    else:
        result = customer
    return JsonResponse(result, safe=False)


def add_to_cart(request):
    customer = get_customer(request)
    if isinstance(customer, Customer):
        try:
            data = request.POST
            product_id = data.get('product_id',)
            quantity = data.get('quantity')
            result = customer.add_to_cart(product_id, quantity)
        except Exception as e:
            result = {'result': 'Error', 'reason': repr(e)}
    else:
        result = customer
    return JsonResponse(result)


def del_from_cart(request):
    try:
        customer = get_customer(request)
        cart_ids = request.POST.get('cart_item_id')
        if cart_ids:
            result = customer.del_from_cart(*cart_ids)
        else:
            raise Exception('Invalid cart_ids')
    except Exception as e:
        result = {'result': 'success', 'reason': repr(e)}
    return JsonResponse(result)


def cart_to_order(request):
    customer = get_customer(request)
    try:
        result = customer.cart_to_order()
    except Exception as e:
            result = {'result': 'Error', 'reason': repr(e)}
    return JsonResponse(result)

