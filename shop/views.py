from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db.models import Q, F
from django.http import JsonResponse, HttpResponseBadRequest
from .forms import SignupForm, CommentForm, CheckoutForm, FeedbackForm
from .models import (
    Product, ProductVariant, CartItem, Comment,
    Order, OrderItem, Feedback, CommentReaction, ProductColor, CarouselImage
)
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_exempt
import qrcode
import io
import base64
from django.urls import reverse
from django.core.mail import send_mail
from django.contrib.auth.forms import AuthenticationForm
from django.utils import timezone
from django import forms

# ------------------ AJAX CART HANDLERS ---------------------
@csrf_exempt
@login_required
def increase_quantity(request, item_id):
    try:
        item = CartItem.objects.get(id=item_id, user=request.user)
        max_stock = item.variant.stock if item.variant else item.product.stock
        if item.quantity < max_stock:
            item.quantity += 1
            item.save()
            status = True
        else:
            status = False
    except CartItem.DoesNotExist:
        status = False
    return JsonResponse(cart_data_response(request, status=status))

@csrf_exempt
@login_required
def decrease_quantity(request, item_id):
    try:
        item = CartItem.objects.get(id=item_id, user=request.user)
        if item.quantity > 1:
            item.quantity -= 1
            item.save()
            status = True
        else:
            status = False
    except CartItem.DoesNotExist:
        status = False
    return JsonResponse(cart_data_response(request, status=status))

@csrf_exempt
@login_required
def remove_from_cart(request, item_id):
    try:
        item = CartItem.objects.get(id=item_id, user=request.user)
        item.delete()
        status = True
    except CartItem.DoesNotExist:
        status = False
    return JsonResponse(cart_data_response(request, status=status))

def cart_data_response(request, status=True):
    items = []
    cart_items = CartItem.objects.filter(user=request.user)
    total_price = 0
    for item in cart_items:
        price = int(item.variant.price if item.variant else item.product.display_price())
        subtotal = price * item.quantity
        total_price += subtotal
        items.append({
            'id': item.id,
            'quantity': item.quantity,
            'price': price,
            'subtotal': subtotal,
        })
    return {
        'success': status,
        'items': items,
        'total_price': total_price
    }

# ----------------- CÁC VIEW KHÁC ---------------------------
def chunk_products(lst, size):
    for i in range(0, len(lst), size):
        yield lst[i:i + size]

def home(request):
    featured_products = Product.objects.filter(is_featured=True)
    product_groups = list(chunk_products(featured_products, 3))
    carousel_images = CarouselImage.objects.filter(is_active=True)
    return render(
        request,
        'shop/home.html',
        {
            'product_groups': product_groups,
            'carousel_images': carousel_images,
        }
    )

def signup_view(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            subject = "Chào mừng bạn đã đăng ký tài khoản!"
            message = f"""
Xin chào {user.username},

Cảm ơn bạn đã đăng ký tài khoản tại cửa hàng của chúng tôi!
Nếu bạn không phải là người đăng ký, vui lòng bỏ qua email này.

Trân trọng,
Đội ngũ cửa hàng
"""
            send_mail(subject, message, None, [user.email])
            messages.success(request, "🎉 Đăng ký thành công! Chào mừng bạn.")
            return redirect('home')
    else:
        form = SignupForm()
    return render(request, 'shop/signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            subject = "Thông báo: Có người vừa đăng nhập tài khoản của bạn"
            message = f"""
Xin chào {user.username},

Tài khoản của bạn vừa được đăng nhập vào lúc {timezone.now().strftime('%H:%M:%S %d/%m/%Y')}.
Nếu không phải bạn, vui lòng đổi mật khẩu ngay lập tức hoặc liên hệ hỗ trợ!

Trân trọng,
Đội ngũ cửa hàng
"""
            send_mail(subject, message, None, [user.email])
            messages.success(request, "🟢 Đăng nhập thành công!")
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'shop/login.html', {'form': form})

@login_required
def add_to_cart(request, pk):
    product = get_object_or_404(Product, pk=pk)
    variant_id = request.POST.get('variant_id')
    quantity = int(request.POST.get('quantity', 1))

    variant = None
    if variant_id:
        variant = get_object_or_404(ProductVariant, id=variant_id)
        if variant.stock < quantity:
            messages.error(request, "Sản phẩm không đủ hàng trong kho.")
            return redirect('product_detail', pk=pk)
    else:
        if hasattr(product, 'stock') and product.stock < quantity:
            messages.error(request, "Sản phẩm không đủ hàng trong kho.")
            return redirect('product_detail', pk=pk)

    cart_item, created = CartItem.objects.get_or_create(
        user=request.user,
        product=product,
        variant=variant
    )
    cart_item.quantity = quantity
    cart_item.save()
    messages.success(request, f"Đã thêm {quantity} sản phẩm vào giỏ hàng!")
    return redirect('cart')

@login_required
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    variants = product.variants.all() if product.has_variants() else []
    colors = ProductColor.objects.filter(product=product)
    comments = Comment.objects.filter(product=product).order_by('-created_at')
    related_products = Product.objects.filter(category=product.category).exclude(id=product.id)[:4]

    if request.method == 'POST':
        if 'quantity' in request.POST:
            quantity = int(request.POST.get('quantity', 1))
            variant = None
            if product.has_variants():
                variant_id = request.POST.get('variant_id')
                variant = get_object_or_404(ProductVariant, id=variant_id, product=product)
                if variant.stock < quantity:
                    messages.error(request, "Số lượng còn lại không đủ!")
                    return redirect('product_detail', pk=pk)
            else:
                if hasattr(product, 'stock') and product.stock < quantity:
                    messages.error(request, "Số lượng còn lại không đủ!")
                    return redirect('product_detail', pk=pk)
            cart_item, created = CartItem.objects.get_or_create(
                user=request.user,
                product=product,
                variant=variant
            )
            cart_item.quantity = quantity
            cart_item.save()
            messages.success(request, f'✅ Đã thêm {quantity} x "{product.name}" vào giỏ hàng.')
            return redirect('cart')
        else:
            form = CommentForm(request.POST)
            if form.is_valid():
                comment = form.save(commit=False)
                comment.user = request.user
                comment.product = product
                comment.save()
                messages.success(request, '💬 Bình luận đã được gửi.')
                return redirect('product_detail', pk=pk)
    else:
        form = CommentForm()

    return render(request, 'shop/product_detail.html', {
        'product': product,
        'variants': variants,
        'form': form,
        'comments': comments,
        'related_products': related_products,
        'colors': colors,
    })

@login_required
def cart_view(request):
    cart_items = CartItem.objects.filter(user=request.user)
    items = []
    total_price = 0
    for item in cart_items:
        price = item.variant.price if item.variant else item.product.display_price()
        subtotal = price * item.quantity
        total_price += subtotal
        items.append({
            'item': item,
            'price': price,
            'subtotal': subtotal,
        })
    return render(request, 'shop/cart.html', {
        'items': items,
        'total_price': total_price,
    })

@login_required
def checkout(request):
    cart_items = CartItem.objects.filter(user=request.user)
    if not cart_items.exists():
        messages.warning(request, "🛒 Giỏ hàng của bạn đang trống.")
        return redirect('cart')
    for item in cart_items:
        if item.variant:
            if item.quantity > item.variant.stock:
                messages.error(request, f"Sản phẩm '{item.product.name} {item.variant.storage}' chỉ còn {item.variant.stock} sản phẩm!")
                return redirect('cart')
        else:
            messages.error(request, f"Sản phẩm '{item.product.name}' hiện không còn hàng!")
            return redirect('cart')
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            order = Order.objects.create(
                user=request.user,
                full_name=form.cleaned_data['full_name'],
                email=form.cleaned_data['email'],
                phone=form.cleaned_data['phone'],
                address=form.cleaned_data['address']
            )
            for item in cart_items:
                if item.variant:
                    item.variant.stock -= item.quantity
                    item.variant.save()
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    variant=item.variant,
                    quantity=item.quantity
                )
            cart_items.delete()
            send_order_confirmation_mail(order, order.email)
            messages.success(request, "✅ Đặt hàng thành công!")
            return render(request, 'shop/checkout_success.html', {'order': order})
    else:
        form = CheckoutForm()

    return render(request, 'shop/checkout.html', {
        'form': form,
        'cart_items': cart_items
    })

@login_required
def qr_payment(request):
    cart_items = CartItem.objects.filter(user=request.user)
    if not cart_items.exists():
        messages.warning(request, "🛒 Giỏ hàng của bạn đang trống.")
        return redirect('cart')
    for item in cart_items:
        if item.variant:
            if item.quantity > item.variant.stock:
                messages.error(request, f"Sản phẩm '{item.product.name} {item.variant.storage}' chỉ còn {item.variant.stock} sản phẩm!")
                return redirect('cart')
        else:
            messages.error(request, f"Sản phẩm '{item.product.name}' hiện không còn hàng!")
            return redirect('cart')
    items = []
    total_price = 0
    for item in cart_items:
        price = item.variant.price if item.variant else item.product.display_price()
        subtotal = price * item.quantity
        total_price += subtotal
        items.append({
            'product': item.product.name,
            'variant': getattr(item.variant, 'storage', ''),
            'color': item.variant.color.name if getattr(item.variant, 'color', None) else '',
            'quantity': item.quantity,
            'subtotal': subtotal,
        })
    qr_payload = f"PAYMENT|user={request.user.id}|amount={total_price}"
    qr_code_base64 = generate_qr_code(qr_payload)
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            order = Order.objects.create(
                user=request.user,
                full_name=form.cleaned_data['full_name'],
                email=form.cleaned_data['email'],
                phone=form.cleaned_data['phone'],
                address=form.cleaned_data['address'],
                is_paid=True
            )
            for item in cart_items:
                if item.variant:
                    item.variant.stock -= item.quantity
                    item.variant.save()
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    variant=item.variant,
                    quantity=item.quantity
                )
            cart_items.delete()
            send_order_confirmation_mail(order, order.email)
            messages.success(request, "✅ Thanh toán QR thành công!")
            return render(request, 'shop/checkout_success.html', {'order': order})
    else:
        form = CheckoutForm()
    return render(request, 'shop/qr_payment.html', {
        'items': items,
        'total_price': total_price,
        'qr_code': qr_code_base64,
        'form': form
    })

def generate_qr_code(data: str) -> str:
    qr = qrcode.QRCode(version=1, box_size=6, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()

def send_order_confirmation_mail(order, email):
    subject = "Xác nhận đơn hàng thành công"
    message = f"""
Chào {order.full_name},

Cảm ơn bạn đã đặt hàng tại cửa hàng của chúng tôi!

Thông tin đơn hàng:
- Họ tên: {order.full_name}
- Số điện thoại: {order.phone}
- Email: {order.email}
- Địa chỉ: {order.address}

Các sản phẩm đã mua:
"""
    items = OrderItem.objects.filter(order=order)
    for idx, item in enumerate(items, 1):
        prod = item.product.name
        variant = item.variant.storage if item.variant else ""
        color = item.variant.color.name if hasattr(item.variant, 'color') and item.variant.color else ""
        message += f"  {idx}. {prod} {variant} {color} x{item.quantity}\n"
    message += "\nĐơn hàng của bạn sẽ sớm được xác nhận và giao hàng.\nTrân trọng!"
    send_mail(subject, message, None, [email])

class VariantStockUpdateForm(forms.ModelForm):
    class Meta:
        model = ProductVariant
        fields = ['stock']

@staff_member_required
def inventory_management(request):
    variants = ProductVariant.objects.select_related('product', 'color').order_by(
        'product__category', 'product__name', 'storage', 'color__name')
    if request.method == 'POST':
        variant_id = request.POST.get('variant_id')
        variant = get_object_or_404(ProductVariant, id=variant_id)
        form = VariantStockUpdateForm(request.POST, instance=variant)
        if form.is_valid():
            form.save()
            return redirect('inventory_management')
    else:
        form = VariantStockUpdateForm()
    return render(request, 'shop/inventory_management.html', {'variants': variants, 'form': form})

# ... các view phụ trợ khác (bình luận, order_history, search...) giữ nguyên ...


### Các view phụ trợ khác (bình luận, feedback, search...)
@require_POST
@login_required
def react_to_comment(request, comment_id, reaction_type):
    if reaction_type not in ['like', 'dislike']:
        return HttpResponseBadRequest("Phản ứng không hợp lệ.")

    comment = get_object_or_404(Comment, id=comment_id)
    reaction, created = CommentReaction.objects.get_or_create(
        user=request.user,
        comment=comment,
        defaults={'reaction': reaction_type}
    )

    if created:
        if reaction_type == 'like':
            Comment.objects.filter(pk=comment.pk).update(likes=F('likes') + 1)
        else:
            Comment.objects.filter(pk=comment.pk).update(dislikes=F('dislikes') + 1)
    elif reaction.reaction != reaction_type:
        if reaction.reaction == 'like':
            Comment.objects.filter(pk=comment.pk).update(
                likes=F('likes') - 1,
                dislikes=F('dislikes') + 1
            )
        else:
            Comment.objects.filter(pk=comment.pk).update(
                likes=F('likes') + 1,
                dislikes=F('dislikes') - 1
            )
        reaction.reaction = reaction_type
        reaction.save()

    updated_comment = Comment.objects.get(pk=comment.pk)
    return render(request, 'shop/partials/comment_card.html', {'c': updated_comment})

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'shop/order_history.html', {'orders': orders})

@require_POST
def logout_view(request):
    logout(request)
    messages.success(request, "👋 Bạn đã đăng xuất.")
    return redirect('home')

def product_by_category(request, category, template):
    product_list = Product.objects.filter(category=category)
    paginator = Paginator(product_list, 6)
    page = request.GET.get('page')
    products = paginator.get_page(page)
    return render(request, template, {'products': products})

def iphone_products(request): return product_by_category(request, 'iphone', 'shop/iphone.html')
def macbook_products(request): return product_by_category(request, 'macbook', 'shop/macbook.html')
def ipad_products(request): return product_by_category(request, 'ipad', 'shop/ipad.html')
def watch_products(request): return product_by_category(request, 'watch', 'shop/watch.html')
def audio_products(request): return product_by_category(request, 'audio', 'shop/audio.html')
def accessory_products(request): return product_by_category(request, 'accessory', 'shop/accessory.html')

@login_required
def feedback_view(request):
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.user = request.user
            feedback.save()
            messages.success(request, '✅ Phản hồi của bạn đã được gửi. Cảm ơn bạn!')
            return redirect('home') 
    else:
        form = FeedbackForm()
    return render(request, 'shop/feedback.html', {'form': form})

def search_products(request):
    query = request.GET.get('q')
    results = Product.objects.filter(Q(name__icontains=query)) if query else []
    return render(request, 'shop/search_results.html', {
        'query': query,
        'results': results
    })
