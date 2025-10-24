from django import forms
from .models import Order, Review
from django.core.exceptions import ValidationError
from django.utils import timezone

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['delivery_address', 'delivery_phone', 'delivery_date']
        widgets = {
            'delivery_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def clean_delivery_date(self):
        delivery_date = self.cleaned_data.get('delivery_date')
        if delivery_date:
            # Проверяем, что дата не в прошлом
            if delivery_date < timezone.now():
                raise ValidationError("Дата доставки не может быть в прошлом.")
        return delivery_date

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 4}),
        }