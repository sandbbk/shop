from django.shortcuts import render
from .models import Product, Category, User, Order, Cart_items
from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from shop.exceptions import (CodeKeyError, QuantityKeyError, UserAuthError, EmptyValue, SearchKeyError, DecimalValueError)
from django.core.paginator import (Paginator, EmptyPage, PageNotAnInteger)
from django.db.models import Q
from authentication.views import (log_in, log_out)
from django.conf import settings
import json
from django.forms.models import model_to_dict


def p_range(pages, num_page):   # function which creates convenient list of page-numbers;
    p_set = {1, pages.num_pages}
    try:
        num_page = int(num_page)
    except (ValueError, TypeError):
        num_page = 1
    base_set = set(pages.page_range)
    p_set.update(range(num_page - 5, num_page + 6))
    p_set.update(range(0, pages.num_pages, 50))
    p_set.intersection_update(base_set)
    return sorted(list(p_set))


def paginate(request, obj, fields=None):
    pages = Paginator(obj, 30)
    try:
        num_page = json.loads(request.body).get('page')
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
        category_id = json.loads(request.body)['category_id']
        category = Category.objects.get(id=category_id)
        if category.category_set.all():
            obj = category.category_set.all()
            content, p_list = paginate(request, obj)
            result['response'].update({'categories': content, 'p_list': p_list})
        elif category.product_set.all():
            obj = category.product_set.all()
            content, p_list = paginate(request, obj, ('code', 'name', 'price', 'category', 'photo', 'short_description'))
            result['response'].update({'products': content, 'p_list': p_list})
    except (ValueError, KeyError):
        obj = Category.objects.all()
        content, p_list = paginate(request, obj)
        result['response'].update({'categories': content, 'p_list': p_list})
    except ObjectDoesNotExist as e:
        result['response'].update({'error': repr(e)})
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
    val_list = []
    if not val:
        return val_list
    if val.isdecimal():
        val_list.append(val)
        return val_list
    val = val.split(',')
    for cid in val:
        if not cid.strip().isdecimal():
            raise DecimalValueError
        val_list.append(cid.strip())
    return val_list


def del_from_cart(request):
    try:
        user = request.user
        cart_ids = json.loads(request.body).get('id')
        if isinstance(user, User):
            result = user.del_from_cart(dcmls_to_list(cart_ids))
        else:
            raise UserAuthError
    except (ObjectDoesNotExist, TypeError, UserAuthError, EmptyValue, DecimalValueError) as e:
        result = {'error': repr(e)}
    return JsonResponse({'response': result})


def cart_to_order(request):
    user = request.user
    result = {'response': {}}
    try:
        result['response'].update(user.cart_to_order())
    except Exception as e:
        result.update({'error': repr(e)})
    return JsonResponse(result)


def to_reserve(request):
    user = request.user
    result = {'response': {}}
    try:
        if not isinstance(user, User):
            raise UserAuthError
        data = json.loads(request.body)
        product_code = data.get('product_code')
        if not product_code:
            raise CodeKeyError
        quantity = data.get('quantity')
        if not quantity:
            quantity = 1
        result = user.reserve_product(product_code, quantity)
    except (UserAuthError, CodeKeyError) as e:
        result.update({'error': repr(e)})
    return JsonResponse(result)


def search(request):
    try:
        data = json.loads(request.body)
        categories = dcmls_to_list(data.get('category_id'))
        text_list = (data.get('search_text', '')).split()
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


def get_uploaded_file(file, path):
    with open(path, 'wb+') as dest:
        for chunk in file:
            dest.write(chunk)


def create_object(request):
    result = {'response': {}}
    user = request.user
    obj_type = request.POST['obj_type']
    permission = 'shop.create_' + obj_type
    if user.has_perm(permission):
        obj = user.create_obj(request)
        if isinstance(obj, (Category, Product)):
            result['response'].update({obj_type: model_to_dict(obj, exclude=['qu_in_stock', 'reserved', 'allow_res_per_user', 'photo'])})
    else:
        result['response'].update({'error': 'Invalid data for creating object' + obj_type,
                                   'data': (request.POST, type(request.FILES['photo']))})
    return JsonResponse(result)

def actions(request):
    actions_dict = {'index': index, 'catalog': catalog, 'product_detail': product_detail, 'get_cart': get_cart,
                    'add_to_cart': add_to_cart, 'del_from_cart': del_from_cart, 'cart_to_order': cart_to_order,
                    'to_reserve': to_reserve, 'search': search, 'login': log_in, 'logout': log_out, 'create':
                        create_object}
    if request.method == 'POST' and request.POST.get('action'):
        action = request.POST.get('action')
        return actions_dict[action](request)
    if request.method == 'POST':  # and request.is_ajax():
        try:
            data = json.loads(request.body)
            action = data['action']
            func = actions_dict[action](request)
        except (KeyError, ValueError):
            return JsonResponse({'response': {'error': 'Value of action key is invalid!'}})
        return func
