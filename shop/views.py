from django.shortcuts import render
from .models import Product, Category, User, Order, Cart_items
from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist


# def get_customer(request):
#     data = request.POST
#     user_id = data.get('customer_id')
#     try:
#         result = User.objects.get(id=user_id)
#     except ObjectDoesNotExist as e:
#         result = {'result': 'Error', 'reason': repr(e)}
#     return result


def index(request):

        if request.POST.get('category_id'):
            cid = request.POST.get('category_id')

            cat = Category.objects.get(id=cid)
            categories = cat.category_set.all()
            products = cat.product_set.all()
            return render(request, 'shop/index.html', {'categories': categories, 'products': products})
        elif request.GET.get('code'):
            pcode = request.GET.get('code')
            product = Product.objects.get(code=pcode)
            user = User.objects.values('id').get(id=1)
            return render(request, 'shop/index.html', {'product': product, 'user': user})

        else:
            categories = Category.objects.filter(parent=None)
            return render(request, 'shop/index.html', {'categories': categories})



def get_cart(request):
    user = request.user
    if isinstance(user, User):
        result = list(user.get_cart().values('id', 'product__code', 'product__name', 'product__price', 'user__id'))
    else:
        result = user
    return JsonResponse(result, safe=False)


def add_to_cart(request):
    user = request.user
    try:
        if isinstance(user, User):
            data = request.POST
            product_code = int(data.get('product_code'))
            quantity = int(data.get('quantity'))

            result = user.add_to_cart(product_code, quantity)
        else:
            raise TypeError('User is not authenticated')
    except (ObjectDoesNotExist, TypeError) as e:
        result = {'Error': repr(e)}
    return JsonResponse({'response': result})



def del_from_cart(request):
    try:
        user = request.user
        if isinstance(User, user):
            cart_ids = request.POST.get('id')
            if cart_ids:
                result = user.del_from_cart(*cart_ids)
            else:
                raise ObjectDoesNotExist('Invalid cart_ids')
    except (ObjectDoesNotExist, TypeError) as e:
        result = {'result': 'success', 'reason': repr(e)}
    return JsonResponse(result)


def cart_to_order(request):
    customer = get_customer(request)
    try:
        result = customer.cart_to_order()
    except Exception as e:
            result = {'result': 'Error', 'reason': repr(e)}
    return JsonResponse(result)

def to_reserve(request):
    user = get_customer(request)
    if isinstance(user, User):
        try:
            data = request.POST
            product_code = data.get('product_code')
            quantity = data.get('quantity')
            if not quantity:
                quantity = 1
            result = user.reserve_product(product_code, quantity)
        except Exception as e:
            result = {'result': 'Error', 'reason': repr(e)}
    else:
        result = user
    return JsonResponse(result)
