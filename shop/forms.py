from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Comment
from .models import Feedback
#quản lí form nhập biễu mẫu
#Định nghĩa các Form (biểu mẫu), ví dụ form góp ý, form đăng ký, form mua hàng...



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


