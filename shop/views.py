# shop/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Product, Order, OrderItem, Review
from .forms import OrderForm, ReviewForm
from django.contrib import messages
from decimal import Decimal
from accounts.models import UserProfile

# --- ИМПОРТ ДЛЯ УВЕДОМЛЕНИЙ АДМИНИСТРАТОРА ---
# Импортируем функцию и обёртку сюда, чтобы отправлять уведомление из views.py
from telegram_manager_bot.notifications import send_new_order_to_managers, run_async_notification
# --- /ИМПОРТ ДЛЯ УВЕДОМЛЕНИЙ АДМИНИСТРАТОРА ---

@login_required
def checkout(request):
    try:
        user_profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        user_profile = None

    cart = request.session.get('cart', {})
    if not cart:
        messages.error(request, "Ваша корзина пуста.")
        return redirect('shop:product_list')

    cart_items = []
    total = Decimal('0.00')
    for product_id, item_data in cart.items():
        product = get_object_or_404(Product, id=product_id)
        quantity = item_data['quantity']
        price = product.price * quantity
        cart_items.append({
            'product': product,
            'quantity': quantity,
            'price': price,
        })
        total += price

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False) # <-- Создаём объект Order, НО НЕ СОХРАНЯЕМ В БАЗУ
            order.user = request.user
            order.total_price = total
            order.payment_status = 'pending' # Устанавливаем статус оплаты
            order.save() # <-- ТЕПЕРЬ сохраняем Order в базу. Его ID теперь доступен.

            # - ЦИКЛ СОЗДАНИЯ OrderItem -
            # Создаём OrderItem и связываем с Order. Это важно сделать до уведомления.
            for product_id, item_data in cart.items():
                product = get_object_or_404(Product, id=product_id)
                quantity = item_data['quantity']
                OrderItem.objects.create(order=order, product=product, quantity=quantity)
            # - /ЦИКЛ СОЗДАНИЯ OrderItem -

            # - ОТПРАВКА УВЕДОМЛЕНИЯ АДМИНУ О НОВОМ ЗАКАЗЕ (ВНЕШНЕЕ НАПРАВЛЕНИЕ) -
            # Вызываем run_async_notification с функцией и её аргументами (без bot_instance)
            print(f"[DEBUG shop/views.py] Уведомление о новом заказе #{order.id} поставлено в очередь на отправку.")
            run_async_notification(send_new_order_to_managers, order.id) # <-- Передаём функцию и ID заказа
            # - /ОТПРАВКА УВЕДОМЛЕНИЯ АДМИНУ О НОВОМ ЗАКАЗЕ -

            # Очищаем корзину
            request.session['cart'] = {}
            messages.success(request, f"Заказ #{order.id} создан. Ожидается оплата.")

            # Возвращаем на страницу истории заказов, где пользователь увидит новый заказ
            return redirect('shop:order_history')
        else:
            # Используем безопасно полученный профиль
            form = OrderForm(initial={
                'delivery_phone': getattr(user_profile, 'phone', ''),
                'delivery_address': getattr(user_profile, 'address', ''),
            })
    else:
        # Используем безопасно полученный профиль
        form = OrderForm(initial={
            'delivery_phone': getattr(user_profile, 'phone', ''),
            'delivery_address': getattr(user_profile, 'address', ''),
        })

    return render(request, 'shop/checkout.html', {'form': form, 'cart_items': cart_items, 'total': total})

# ... (остальные функции, например, product_list, add_to_cart, view_cart, remove_from_cart, order_history, initiate_payment, edit_order, order_detail, add_review) ...