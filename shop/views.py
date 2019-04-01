from django.shortcuts import render
from .models import Product, Category, User, Order, Cart_items
from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from shop.exceptions import (QuantityKeyError, UserAuthError, EmptyValue, SearchKeyError, DecimalValueError)
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q


def p_range(pages, num_page):   # function which creates list of page-links;
    p_set = set()
    if not num_page:
        num_page = 1
    for n in pages.page_range:
        if n == int(num_page):
            for d in range(n - 5, n + 6):
                if 1 <= d <= pages.num_pages:
                    p_set.add(d)
    s = (k for k in range(1, pages.num_pages + 1) if k % 50 == 0 or k == 1 or k == pages.num_pages)
    for k in s:
        p_set.add(k)
    p_list = sorted(list(p_set))
    return p_list


def paginate(request, obj, fields=None):
    pages = Paginator(obj, 30)
    try:
        num_page = request.POST.get('page')
        p_list = p_range(pages, num_page)
        page_content = pages.page(num_page)
    except PageNotAnInteger:
        page_content = pages.page(1)
        p_list = p_range(pages, 1)
    except EmptyPage:
        page_content = pages.page(pages.num_pages)
        p_list = p_range(pages, pages.num_pages)
    if fields:
        content = list(page_content.object_list.values(*fields))
    else:
        content = list(page_content.object_list.values())
    return content, p_list


def index(request):
    return render(request, 'shop/index.html')


def catalog(request):
    result = {'response': {}}
    try:
        category_id = request.POST.get('category_id')
        if category_id:
            category = Category.objects.get(id=category_id)
            if category.category_set.all():
                obj = category.category_set.all()
                content, p_list = paginate(request, obj)
                result['response'].update({'categories': content, 'p_list': p_list})
            elif category.product_set.all():
                obj = category.product_set.all()
                content, p_list = paginate(request, obj, ('code', 'name', 'price',
                                                          'category', 'photo', 'short_description'))
                result['response'].update({'products': content, 'p_list': p_list})
    except (ObjectDoesNotExist, ValueError) as e:
        result['response'].update({'error': repr(e)})
    obj = Category.objects.all()
    content, p_list = paginate(request, obj)
    result['response'].update({'categories': content, 'p_list': p_list})
    return JsonResponse(result)



def product_detail(request):
    result = {'response': {}}
    try:
        product_code = int(request.POST.get('product_code'))
        product = Product.objects.values('code', 'name', 'price', 'category', 'photo', 'short_description',
                                         'description', 'discount').get(code=product_code)
        result['response'].update({'product': product})
        obj = Category.objects.all()
        content, p_list = paginate(request, obj)
        result['response'].update({'categories': content, 'p_list': p_list})
    except (ObjectDoesNotExist, ValueError) as e:
        result['response'].update({'error': repr(e)})
    return JsonResponse(result)



def get_cart(request):
    try:
        user = request.user
        if isinstance(user, User):
            cart, result = user.get_cart()
        else:
            raise UserAuthError
    except UserAuthError as e:
        result = {'response': {'error': repr(e)}}
    return JsonResponse({'response': result})


def add_to_cart(request):
    user = request.user
    try:
        if isinstance(user, User):
            data = request.POST
            product_code = int(data.get('product_code'))
            quantity = int(data.get('quantity'))
            if not quantity:
                raise QuantityKeyError
            result = user.add_to_cart(product_code, quantity)
        else:
            raise UserAuthError
    except (ObjectDoesNotExist, UserAuthError, QuantityKeyError) as e:
        result = {'error': repr(e)}
    return JsonResponse({'response': result})


def dcmls_to_list(val):
    if val:
        val_list = []
        if val.isdecimal():
            val_list.append(val)
        else:
            val = val.split(',')
            for cid in val:
                if cid.strip().isdecimal():
                    val_list.append(cid.strip())
                else:
                    raise DecimalValueError
        return val_list
    return []


def del_from_cart(request):
    try:
        user = request.user
        cart_ids = request.POST.get('id')
        if isinstance(user, User):
            result = user.del_from_cart(dcmls_to_list(cart_ids))
        else:
            raise UserAuthError
    except (ObjectDoesNotExist, TypeError, UserAuthError, EmptyValue, DecimalValueError) as e:
        result = {'result': 'error', 'reason': repr(e)}
    return JsonResponse({'response': result})


def cart_to_order(request):
    user = request.user
    result = {'response': {}}
    try:
        result['response'].update(user.cart_to_order())
    except Exception as e:
            result = {'result': 'Error', 'reason': repr(e)}
    return JsonResponse(result)


def to_reserve(request):
    user = request.POST.get('user')
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


def search(request):
    try:
        categories = dcmls_to_list(request.POST.get('category_id'))
        text_list = (request.POST.get('search_text')).split()
        if categories:
            products = Product.objects.filter(category__id__in=categories)
        else:
            products = Product.objects.all()
        if text_list:
            query = Q()
            for word in text_list:
                query &= (Q(name__icontains=word) | Q(category__name__icontains=word)
                      | Q(short_description__icontains=word) | Q(description__icontains=word))
            searched_products = products.filter(query)
        else:
            raise SearchKeyError
        content, p_list = paginate(request, searched_products, fields=('code', 'name', 'price', 'category', 'photo',
                                                                  'short_description', 'description', 'discount'))
    except (UserAuthError, SearchKeyError, DecimalValueError) as e:
        return JsonResponse({'response': {'error': repr(e)}})
    return JsonResponse({'response': {'products': content, 'p_list': p_list}})


def actions(request):
    if request.method == 'POST' and request.is_ajax():
        try:
            actions_dict = {'index': index, 'catalog': catalog, 'product_detail': product_detail, 'get_cart': get_cart,
                            'add_to_cart': add_to_cart, 'del_from_cart': del_from_cart, 'cart_to_order': cart_to_order,
                            'to_reserve': to_reserve, 'search': search}
            action = request.POST.get('action')
            func = actions_dict[action](request)
        except KeyError:
            return JsonResponse({'response': {'error': 'Value of action key is invalid!'}})
        return func
