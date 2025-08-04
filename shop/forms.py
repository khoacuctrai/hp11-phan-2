from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Comment
from .models import Feedback
#quản lí form nhập biễu mẫu
#Định nghĩa các Form (biểu mẫu), ví dụ form góp ý, form đăng ký, form mua hàng...

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, get_object_or_404, redirect
from .models import ProductVariant

class SignupForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["content"]
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'style': 'width: 100%; font-size: 16px;',
                'placeholder': 'Nhập bình luận của bạn...'
            }),
        }

class CheckoutForm(forms.Form):
    full_name = forms.CharField(label="Họ và tên", max_length=100)
    email = forms.EmailField(label="Email")
    phone = forms.CharField(label="Số điện thoại", max_length=15)
    address = forms.CharField(label="Địa chỉ", widget=forms.Textarea(attrs={'rows': 3}))

class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['is_complaint', 'message']
        labels = {
            'is_complaint': 'Loại phản hồi',
            'message': 'Nội dung'
        }
        widgets = {
            'is_complaint': forms.RadioSelect(choices=[(True, 'Khiếu nại'), (False, 'Góp ý')]),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Nội dung...'}),
        }



class VariantStockUpdateForm(forms.ModelForm):
    class Meta:
        model = ProductVariant
        fields = ['stock']

@staff_member_required
def inventory_management(request):
    variants = ProductVariant.objects.select_related('product', 'color').order_by('product__category', 'product__name', 'storage', 'color__name')
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