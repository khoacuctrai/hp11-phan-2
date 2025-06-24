from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db.models import Q, F
from django.http import JsonResponse, HttpResponseBadRequest
from django.template.loader import render_to_string
from .forms import SignupForm, CommentForm, CheckoutForm, FeedbackForm
from .models import (
    Product, ProductVariant, CartItem, Comment,
    Order, OrderItem, Feedback, CommentReaction, ProductColor
)

# Chia nhóm cho carousel
def chunk_products(lst, size):
    for i in range(0, len(lst), size):
        yield lst[i:i + size]

def home(request):
    featured_products = Product.objects.filter(is_featured=True)
    product_groups = list(chunk_products(featured_products, 3))
    return render(request, 'shop/home.html', {'product_groups': product_groups})

def signup_view(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "🎉 Đăng ký thành công! Chào mừng bạn.")
            return redirect('home')
    else:
        form = SignupForm()
    return render(request, 'shop/signup.html', {'form': form})

# ✅ Chi tiết sản phẩm + Gợi ý + Bình luận
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
            if product.category in ['iphone', 'macbook']:
                variant_id = request.POST.get('variant_id')
                variant = get_object_or_404(ProductVariant, id=variant_id, product=product)
            cart_item, created = CartItem.objects.get_or_create(
                user=request.user,
                product=product,
                variant=variant
            )
            cart_item.quantity += quantity
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

# ✅ Giỏ hàng
@login_required
def cart_view(request):
    cart_items = CartItem.objects.filter(user=request.user)
    total_price = sum(
        (item.variant.price if item.variant else item.product.display_price()) * item.quantity
        for item in cart_items
    )
    return render(request, 'shop/cart.html', {
        'cart_items': cart_items,
        'total_price': total_price
    })

@login_required
def add_to_cart(request, pk):
    product = get_object_or_404(Product, pk=pk)
    variant_id = request.POST.get('variant_id')
    quantity = int(request.POST.get('quantity', 1))
    variant = get_object_or_404(ProductVariant, id=variant_id)

    cart_item, created = CartItem.objects.get_or_create(
        user=request.user,
        product=product,
        variant=variant
    )
    cart_item.quantity += quantity
    cart_item.save()
    messages.success(request, f'🛒 Đã thêm {quantity} x {variant} vào giỏ hàng.')
    return redirect('cart')

# ✅ Tăng/giảm/xoá
@login_required
def increase_quantity(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, user=request.user)
    item.quantity += 1
    item.save()
    return redirect('cart')

@login_required
def decrease_quantity(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, user=request.user)
    if item.quantity > 1:
        item.quantity -= 1
        item.save()
    else:
        item.delete()
    return redirect('cart')

@login_required
def remove_from_cart(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, user=request.user)
    item.delete()
    return redirect('cart')

# ✅ Like / Dislike bình luận
from django.http import HttpResponse, HttpResponseBadRequest

@require_POST
@login_required
def react_to_comment(request, comment_id, reaction_type):
    if reaction_type not in ['like', 'dislike']:
        return HttpResponseBadRequest("Phản ứng không hợp lệ.")

    comment = get_object_or_404(Comment, id=comment_id)

    # Kiểm tra xem user đã từng phản ứng chưa
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

# ✅ Checkout
@login_required
def checkout(request):
    cart_items = CartItem.objects.filter(user=request.user)
    if not cart_items.exists():
        messages.warning(request, "🛒 Giỏ hàng của bạn đang trống.")
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
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    variant=item.variant,
                    quantity=item.quantity
                )
            cart_items.delete()
            messages.success(request, "✅ Đặt hàng thành công!")
            return render(request, 'shop/checkout_success.html', {'order': order})
    else:
        form = CheckoutForm()

    return render(request, 'shop/checkout.html', {
        'form': form,
        'cart_items': cart_items
    })

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'shop/order_history.html', {'orders': orders})

@require_POST
def logout_view(request):
    logout(request)
    messages.success(request, "👋 Bạn đã đăng xuất.")
    return redirect('home')

# ✅ Sản phẩm theo danh mục
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

# ✅ Góp ý
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

# ✅ Tìm kiếm   
def search_products(request):
    query = request.GET.get('q')
    results = Product.objects.filter(Q(name__icontains=query)) if query else []
    return render(request, 'shop/search_results.html', {
        'query': query,
        'results': results
    })