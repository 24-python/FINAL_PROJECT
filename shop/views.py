# shop/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Product, Order, OrderItem, Review
from .forms import OrderForm, ReviewForm
from django.contrib import messages
from decimal import Decimal
from accounts.models import UserProfile
from django import forms # Импортируем для создания формы редактирования

# --- НОВАЯ форма для редактирования заказа ---
class EditOrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['delivery_address', 'delivery_phone', 'delivery_date']
        widgets = {
            'delivery_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def clean_delivery_date(self):
        delivery_date = self.cleaned_data.get('delivery_date')
        if delivery_date:
            from django.utils import timezone
            if delivery_date < timezone.now():
                raise forms.ValidationError("Дата доставки не может быть в прошлом.")
        return delivery_date
# --- /НОВАЯ форма ---

def catalog(request):
    products = Product.objects.all()
    return render(request, 'shop/catalog.html', {'products': products})

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    reviews = Review.objects.filter(product=product)
    form = None
    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.product = product
            review.save()
            messages.success(request, "Спасибо за отзыв!")
            return redirect('shop:product_detail', pk=pk)
    else:
        form = ReviewForm()

    return render(request, 'shop/product_detail.html', {
        'product': product,
        'reviews': reviews,
        'form': form
    })

@login_required
def add_to_cart(request, pk):
    product = get_object_or_404(Product, pk=pk)
    cart = request.session.get('cart', {})
    cart[str(pk)] = cart.get(str(pk), 0) + 1
    request.session['cart'] = cart
    messages.success(request, f"{product.name} добавлен в корзину.")
    return redirect('shop:catalog')

@login_required
def quick_add_to_cart(request, pk):
    """
    Быстрое добавление одного товара в корзину из каталога.
    Перенаправляет в корзину.
    """
    product = get_object_or_404(Product, pk=pk)
    cart = request.session.get('cart', {})
    cart[str(pk)] = cart.get(str(pk), 0) + 1
    request.session['cart'] = cart
    messages.success(request, f"{product.name} добавлен в корзину.")
    return redirect('shop:cart') # Перенаправляем в корзину

@login_required
def view_cart(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total = Decimal('0.00')
    for pk, qty in cart.items():
        product = Product.objects.get(pk=int(pk))
        item_total = product.price * qty
        total += item_total
        cart_items.append({
            'product': product,
            'quantity': qty,
            'item_total': item_total
        })
    return render(request, 'shop/cart.html', {'cart_items': cart_items, 'total': total})

@login_required
def initiate_payment(request):
    """
    Имитация оплаты. Создаёт заказ из корзины и устанавливает статус оплаты.
    """
    if request.method != 'POST':
        # Запрещаем GET-запросы к этой функции
        return redirect('shop:cart')

    cart = request.session.get('cart', {})
    if not cart:
        messages.error(request, "Ваша корзина пуста.")
        return redirect('shop:cart')

    # Получаем или создаем UserProfile для текущего пользователя
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)

    # Используем данные из профиля
    delivery_address = getattr(user_profile, 'address', '')
    delivery_phone = getattr(user_profile, 'phone', '')

    # Рассчитываем итоговую цену
    total = Decimal('0.00')
    for pk, qty in cart.items():
        product = Product.objects.get(pk=int(pk))
        total += product.price * qty

    # --- delivery_date не передаём, пусть будет NULL ---
    order = Order.objects.create(
        user=request.user,
        status='new',
        payment_status='pending',
        delivery_address=delivery_address,
        delivery_phone=delivery_phone,
        # delivery_date не передаём, пусть будет NULL
        total_price=total
    )
    # --- /delivery_date ---

    # Создаём OrderItem для каждого товара в корзине
    for pk, qty in cart.items():
        product = Product.objects.get(pk=int(pk))
        OrderItem.objects.create(order=order, product=product, quantity=qty)

    # Очищаем корзину
    request.session['cart'] = {}

    # --- ИМИТАЦИЯ ОПЛАТЫ ---
    # В реальном приложении здесь был бы вызов API платёжной системы
    # и обработка ответа (успешно/неуспешно)
    # Для имитации считаем, что платёж всегда успешен
    # order.payment_status = 'paid'
    # order.status = 'confirmed' # Меняем статус заказа на подтверждён
    # order.save()
    # messages.success(request, f"Заказ #{order.id} успешно оплачен!")
    # return redirect('shop:order_history')

    # --- ИЛИ ---
    # Имитируем "ожидание оплаты" или "платёж на рассмотрении"
    # В админке статус будет 'pending', и админ может его изменить
    messages.success(request, f"Заказ #{order.id} создан. Ожидается оплата.")
    # --- /ИМИТАЦИЯ ОПЛАТЫ ---

    # Возвращаем на страницу истории заказов, где пользователь увидит новый заказ
    return redirect('shop:order_history')

@login_required
def checkout(request):
    # Получаем или создаем UserProfile для текущего пользователя
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            cart = request.session.get('cart', {})
            total = Decimal('0.00')
            for pk, qty in cart.items():
                product = Product.objects.get(pk=int(pk))
                total += product.price * qty
            order.total_price = total
            # Устанавливаем статус оплаты при создании через checkout
            order.payment_status = 'pending' # или 'paid', если оплата сразу
            order.save() # <-- Сохраняем Order, но сигнал post_save НЕ вызывает уведомление

            # --- ЦИКЛ СОЗДАНИЯ OrderItem ---
            for pk, qty in cart.items():
                product = Product.objects.get(pk=int(pk))
                OrderItem.objects.create(order=order, product=product, quantity=qty)
            # --- /ЦИКЛ СОЗДАНИЯ OrderItem ---

            # --- ОТПРАВКА УВЕДОМЛЕНИЯ ---
            # Вызываем уведомление ВРУЧНУЮ ПОСЛЕ создания всех OrderItem
            # Импортируем здесь, чтобы избежать циклических импортов при старте Django
            try:
                from telegram_manager_bot.notifications import send_new_order_to_managers, run_async_notification
                run_async_notification(send_new_order_to_managers(order.id))
            except ImportError:
                # Логгируем ошибку или просто игнорируем, если бот не настроен
                print("Модуль telegram_manager_bot не найден. Уведомление о новом заказе не отправлено.")
            # --- /ОТПРАВКА УВЕДОМЛЕНИЯ ---

            request.session['cart'] = {}
            messages.success(request, "Заказ успешно оформлен!")
            return redirect('shop:order_history')
    else:
        # Используем безопасно полученный профиль
        form = OrderForm(initial={
            'delivery_phone': getattr(user_profile, 'phone', ''),
            'delivery_address': getattr(user_profile, 'address', ''),
        })
    return render(request, 'shop/checkout.html', {'form': form})

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'shop/order_history.html', {'orders': orders})

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    items = OrderItem.objects.filter(order=order)

    # --- Проверка, можно ли редактировать ---
    can_edit = order.status in ['new', 'pending'] # Или другие статусы, когда можно редактировать
    # --- /Проверка ---

    # --- Обработка формы редактирования ---
    edit_form = None
    if can_edit and request.method == 'POST':
        edit_form = EditOrderForm(request.POST, instance=order)
        if edit_form.is_valid():
            # Сохраняем без проверки обязательных полей здесь
            edit_form.save()
            messages.success(request, "Данные заказа обновлены.")
            return redirect('shop:order_detail', order_id=order.id)
    elif can_edit:
        edit_form = EditOrderForm(instance=order)

    # --- /Обработка формы редактирования ---

    # --- Алерт: проверка обязательных полей ---
    missing_fields = []
    if not order.delivery_address:
        missing_fields.append("адрес доставки")
    if not order.delivery_phone:
        missing_fields.append("телефон")
    if not order.delivery_date:
        missing_fields.append("дата доставки")

    if missing_fields:
        # Используем warning, так как это важная информация, но не ошибка валидации формы
        messages.warning(request, f"В заказе не указаны: {', '.join(missing_fields)}. Пожалуйста, укажите их ниже, если это возможно.")

    # --- /Алерт ---

    return render(request, 'shop/order_detail.html', {
        'order': order,
        'items': items,
        'can_edit': can_edit,
        'edit_form': edit_form # Передаём форму в шаблон
    })

@login_required
def repeat_order(request, order_id):
    """
    Повторяет заказ, добавляя товары из старого заказа в корзину.
    """
    old_order = get_object_or_404(Order, id=order_id, user=request.user)
    cart = request.session.get('cart', {})

    # Извлекаем товары из старого заказа
    for item in old_order.orderitem_set.all():
        product_id = str(item.product.id)
        # Увеличиваем количество, если товар уже в корзине
        cart[product_id] = cart.get(product_id, 0) + item.quantity

    # Сохраняем обновленную корзину
    request.session['cart'] = cart

    messages.success(request, f"Товары из заказа #{old_order.id} добавлены в корзину.")
    return redirect('shop:cart') # Перенаправляем в корзину