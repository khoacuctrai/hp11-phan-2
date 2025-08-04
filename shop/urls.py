from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from . import views
#Điều hướng URL đến view.
urlpatterns = [
    # Trang chủ
    path('', views.home, name='home'),
    

    # ✅ Auth
    path('signup/', views.signup_view, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='shop/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='shop/logout.html'), name='logout'),

    # ✅ Chi tiết & giỏ hàng
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    path('add-to-cart/<int:pk>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart_view, name='cart'),
    path('cart/increase/<int:item_id>/', views.increase_quantity, name='increase_quantity'),
    path('cart/decrease/<int:item_id>/', views.decrease_quantity, name='decrease_quantity'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),

    # ✅ Đơn hàng
    path('checkout/', views.checkout, name='checkout'),
    path('order-history/', views.order_history, name='order_history'),
    path('cart/qr-payment/', views.qr_payment, name='qr_payment'),

    # ✅ Like / Dislike bình luận
    path('comment/<int:comment_id>/<str:reaction_type>/', views.react_to_comment, name='react_to_comment'),



    # ✅ Danh mục sản phẩm
    path('iphone/', views.iphone_products, name='iphone_products'),
    path('macbook/', views.macbook_products, name='macbook_products'),
    path('ipad/', views.ipad_products, name='ipad_products'),
    path('watch/', views.watch_products, name='watch_products'),
    path('audio/', views.audio_products, name='audio_products'),
    path('accessory/', views.accessory_products, name='accessory_products'),
    

    # ✅ Góp ý
    path('feedback/', views.feedback_view, name='feedback'),
     path('inventory/', views.inventory_management, name='inventory_management'),
    # ✅ Tìm kiếm
    path('search/', views.search_products, name='search_products'),
]

# ✅ Serve ảnh media trong môi trường dev
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
