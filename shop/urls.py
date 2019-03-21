"""megashop URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path, re_path
from . import views


urlpatterns = [
    path('', views.index, name='home'),
    path('categories/', views.index, name='category'),
    path('products/add', views.add_to_cart, name='add'),
    path('cart', views.get_cart),
    path('del_from_cart', views.del_from_cart),
    path('make_order', views.cart_to_order),
    path('product/reserve', views.to_reserve),
]
