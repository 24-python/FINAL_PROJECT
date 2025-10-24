from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from django.contrib.auth.models import User
from .models import UserProfile
import logging

logger = logging.getLogger('pdn')

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=False, help_text='Необязательно.')
    last_name = forms.CharField(max_length=30, required=False, help_text='Необязательно.')

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Пользователь с таким email уже существует.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data.get("first_name", "")
        user.last_name = self.cleaned_data.get("last_name", "")
        # Устанавливаем username равным email для аутентификации
        if not user.username or user.username == user.email: # Если username не задан или совпадает с email
            user.username = user.email # Используем email как username
        if commit:
            user.save()
            logger.info(f"Создан пользователь: {user.username}, email: {user.email}, id: {user.id}")
        return user

class UserProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=False, label="Имя")
    last_name = forms.CharField(max_length=30, required=False, label="Фамилия")

    class Meta:
        model = UserProfile
        fields = ['phone', 'address']

    def __init__(self, *args, **kwargs):
        # Получаем пользователя из view
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            # Инициализируем поля формы данными из User
            self.fields['first_name'].initial = self.user.first_name
            self.fields['last_name'].initial = self.user.last_name

    def save(self, commit=True):
        profile = super().save(commit=False)
        if self.user:
            # Сохраняем first_name и last_name в User
            self.user.first_name = self.cleaned_data.get("first_name", "")
            self.user.last_name = self.user.cleaned_data.get("last_name", "")
            if commit:
                self.user.save()
        if commit:
            profile.save()
        return profile

class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(widget=forms.EmailInput(attrs={'autofocus': True}), label="Email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Email'
        self.fields['username'].help_text = ""

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not User.objects.filter(email=username).exists():
            raise forms.ValidationError("Пожалуйста, введите правильный email и пароль. Оба поля могут быть чувствительны к регистру.")
        return username

# Форма для смены пароля
class CustomPasswordChangeForm(PasswordChangeForm):
    # Можете добавить кастомные поля или валидацию, если нужно
    pass