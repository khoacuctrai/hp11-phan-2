from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db.models import Q, F
from django.http import JsonResponse, HttpResponseBadRequest
from django.urls import reverse
from django.core.mail import send_mail
from django.contrib.auth.forms import AuthenticationForm
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
import qrcode, io, base64

from django import forms

from .forms import SignupForm, CommentForm, CheckoutForm, FeedbackForm, CouponApplyForm
from .models import (
    Product, ProductVariant, CartItem, Comment,
    Order, OrderItem, Feedback, CommentReaction, ProductColor, CarouselImage, Coupon
)

# ----------------- Helpers (pricing) -----------------

def pricing_with_session(request, include_items=False):
    """Tính giá giỏ hàng + áp dụng coupon (đọc từ session)."""
    cart_qs = CartItem.objects.filter(user=request.user)
    items, subtotal = [], 0
    for it in cart_qs:
        price = int(it.variant.price if it.variant else it.product.display_price())
        sub = price * it.quantity
        subtotal += sub
        if include_items:
            items.append({'id': it.id, 'quantity': it.quantity, 'price': price, 'subtotal': sub})

    coupon_id = request.session.get('coupon_id')
    applied_coupon, discount_amount = None, 0
    if coupon_id:
        try:
            c = Coupon.objects.get(id=coupon_id)
            if c.is_valid():
                applied_coupon = c
                discount_amount = int(subtotal * (c.discount / 100))
            else:
                request.session.pop('coupon_id', None)
        except Coupon.DoesNotExist:
            request.session.pop('coupon_id', None)

    final_total = max(0, subtotal - discount_amount)
    return {
        'items': items,
        'subtotal': subtotal,
        'coupon': applied_coupon,
        'discount_amount': discount_amount,
        'final_total': final_total,
    }

# ------------------ AJAX CART ---------------------

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
    data = pricing_with_session(request, include_items=True)
    data.update({'success': status})
    data['coupon_code'] = data['coupon'].code if data['coupon'] else None
    return data

# ----------------- CÁC VIEW CHÍNH ---------------------------

def chunk_products(lst, size):
    for i in range(0, len(lst), size):
        yield lst[i:i + size]

def home(request):
    featured_products = Product.objects.filter(is_featured=True)
    product_groups = list(chunk_products(featured_products, 3))
    carousel_images = CarouselImage.objects.filter(is_active=True)
    return render(request, 'shop/home.html', {
        'product_groups': product_groups,
        'carousel_images': carousel_images,
    })

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

    cart_item, _ = CartItem.objects.get_or_create(user=request.user, product=product, variant=variant)
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
            cart_item, _ = CartItem.objects.get_or_create(user=request.user, product=product, variant=variant)
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
    pricing = pricing_with_session(request, include_items=True)
    cart_items = CartItem.objects.filter(user=request.user)
    items_vm = []
    for it in cart_items:
        price = it.variant.price if it.variant else it.product.display_price()
        items_vm.append({'item': it, 'price': price, 'subtotal': price * it.quantity})

    return render(request, 'shop/cart.html', {
        'items': items_vm,
        'total_price': pricing['subtotal'],
        'discount_amount': pricing['discount_amount'],
        'final_price': pricing['final_total'],
        'coupon': pricing['coupon'],
        'coupon_form': CouponApplyForm(),
    })

@login_required
def checkout(request):
    cart_qs = CartItem.objects.filter(user=request.user)
    if not cart_qs.exists():
        messages.warning(request, "🛒 Giỏ hàng của bạn đang trống.")
        return redirect('cart')

    for item in cart_qs:
        if item.variant:
            if item.quantity > item.variant.stock:
                messages.error(request, f"Sản phẩm '{item.product.name} {item.variant.storage}' chỉ còn {item.variant.stock} sản phẩm!")
                return redirect('cart')
        else:
            messages.error(request, f"Sản phẩm '{item.product.name}' hiện không còn hàng!")
            return redirect('cart')

    pricing = pricing_with_session(request)

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            order = Order.objects.create(
                user=request.user,
                full_name=form.cleaned_data['full_name'],
                email=form.cleaned_data['email'],
                phone=form.cleaned_data['phone'],
                address=form.cleaned_data['address'],
                coupon=pricing['coupon'],
                discount_percent=(pricing['coupon'].discount if pricing['coupon'] else 0),
                subtotal_before_discount=pricing['subtotal'],
                discount_amount=pricing['discount_amount'],
                total_after_discount=pricing['final_total'],
            )
            for item in cart_qs:
                if item.variant:
                    item.variant.stock -= item.quantity
                    item.variant.save()
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    variant=item.variant,
                    quantity=item.quantity
                )
            cart_qs.delete()
            request.session.pop('coupon_id', None)
            send_order_confirmation_mail(order, order.email)
            messages.success(request, "✅ Đặt hàng thành công!")
            return render(request, 'shop/checkout_success.html', {'order': order})
    else:
        form = CheckoutForm()

    return render(request, 'shop/checkout.html', {
        'form': form,
        'cart_items': cart_qs,
        'subtotal': pricing['subtotal'],
        'discount_amount': pricing['discount_amount'],
        'final_total': pricing['final_total'],
        'coupon': pricing['coupon'],
    })

@login_required
def qr_payment(request):
    cart_qs = CartItem.objects.filter(user=request.user)
    if not cart_qs.exists():
        messages.warning(request, "🛒 Giỏ hàng của bạn đang trống.")
        return redirect('cart')

    for item in cart_qs:
        if item.variant:
            if item.quantity > item.variant.stock:
                messages.error(request, f"Sản phẩm '{item.product.name} {item.variant.storage}' chỉ còn {item.variant.stock} sản phẩm!")
                return redirect('cart')
        else:
            messages.error(request, f"Sản phẩm '{item.product.name}' hiện không còn hàng!")
            return redirect('cart')

    pricing = pricing_with_session(request)

    items = []
    for item in cart_qs:
        price = item.variant.price if item.variant else item.product.display_price()
        items.append({
            'product': item.product.name,
            'variant': getattr(item.variant, 'storage', ''),
            'color': item.variant.color.name if getattr(item.variant, 'color', None) else '',
            'quantity': item.quantity,
            'subtotal': price * item.quantity,
        })

    qr_payload = f"PAYMENT|user={request.user.id}|amount={pricing['final_total']}"
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
                is_paid=True,
                coupon=pricing['coupon'],
                discount_percent=(pricing['coupon'].discount if pricing['coupon'] else 0),
                subtotal_before_discount=pricing['subtotal'],
                discount_amount=pricing['discount_amount'],
                total_after_discount=pricing['final_total'],
            )
            for item in cart_qs:
                if item.variant:
                    item.variant.stock -= item.quantity
                    item.variant.save()
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    variant=item.variant,
                    quantity=item.quantity
                )
            cart_qs.delete()
            request.session.pop('coupon_id', None)
            send_order_confirmation_mail(order, order.email)
            messages.success(request, "✅ Thanh toán QR thành công!")
            return render(request, 'shop/checkout_success.html', {'order': order})
    else:
        form = CheckoutForm()

    return render(request, 'shop/qr_payment.html', {
        'items': items,
        'subtotal': pricing['subtotal'],
        'discount_amount': pricing['discount_amount'],
        'final_total': pricing['final_total'],
        'coupon': pricing['coupon'],
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

@require_POST
def apply_coupon(request):
    form = CouponApplyForm(request.POST)
    if form.is_valid():
        code = form.cleaned_data['code'].strip()
        try:
            coupon = Coupon.objects.get(code__iexact=code)
            if coupon.is_valid():
                request.session['coupon_id'] = coupon.id
                messages.success(request, f"Áp dụng mã {coupon.code} thành công!")
            else:
                request.session.pop('coupon_id', None)
                messages.error(request, "Mã giảm giá đã hết hạn hoặc không khả dụng.")
        except Coupon.DoesNotExist:
            request.session.pop('coupon_id', None)
            messages.error(request, "Mã giảm giá không tồn tại.")
    return redirect('cart')

@require_POST
def clear_coupon(request):
    request.session.pop('coupon_id', None)
    messages.info(request, "Đã hủy mã giảm giá.")
    return redirect('cart')

@require_POST
def logout_view(request):
    logout(request)
    messages.success(request, "👋 Bạn đã đăng xuất.")
    return redirect('home')

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'shop/order_history.html', {'orders': orders})

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
        # đổi trạng thái: like -> dislike hoặc ngược lại
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


from django.core.paginator import Paginator
from django.shortcuts import render
from .models import Product

def product_by_category(request, category, template):
    product_list = Product.objects.filter(category=category)
    paginator = Paginator(product_list, 6)  # 6 sản phẩm / trang
    page = request.GET.get('page')
    products = paginator.get_page(page)
    return render(request, template, {'products': products})

def iphone_products(request):
    return product_by_category(request, 'iphone', 'shop/iphone.html')

def macbook_products(request):
    return product_by_category(request, 'macbook', 'shop/macbook.html')

def ipad_products(request):
    return product_by_category(request, 'ipad', 'shop/ipad.html')

def watch_products(request):
    return product_by_category(request, 'watch', 'shop/watch.html')

def audio_products(request):
    return product_by_category(request, 'audio', 'shop/audio.html')

def accessory_products(request):
    return product_by_category(request, 'accessory', 'shop/accessory.html')


from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import FeedbackForm

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


from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, get_object_or_404, redirect
from .models import ProductVariant
from django import forms

# Form cập nhật tồn kho
class VariantStockUpdateForm(forms.ModelForm):
    class Meta:
        model = ProductVariant
        fields = ['stock']

@staff_member_required
def inventory_management(request):
    # để auto-scroll khi search
    q = request.GET.get('q', '').strip()

    variants = (ProductVariant.objects
                .select_related('product', 'color')
                .order_by('product__category', 'product__name', 'storage', 'color__name'))

    if request.method == 'POST':
        variant_id = request.POST.get('variant_id')
        variant = get_object_or_404(ProductVariant, id=variant_id)
        form = VariantStockUpdateForm(request.POST, instance=variant)
        if form.is_valid():
            form.save()
            return redirect('inventory_management')
    else:
        form = VariantStockUpdateForm()

    return render(
        request,
        'shop/inventory_management.html',
        {'variants': variants, 'form': form, 'q': q}
    )


from django.db.models import Q
from django.shortcuts import render
from .models import Product

def search_products(request):
    query = request.GET.get('q', '')
    results = Product.objects.filter(Q(name__icontains=query)) if query else []
    return render(request, 'shop/search_results.html', {
        'query': query,
        'results': results
    })



