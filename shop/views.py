from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Product, Order, OrderItem, Review
from .forms import OrderForm, ReviewForm
from django.contrib import messages
from decimal import Decimal

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
def checkout(request):
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
            order.save()

            for pk, qty in cart.items():
                product = Product.objects.get(pk=int(pk))
                OrderItem.objects.create(order=order, product=product, quantity=qty)

            request.session['cart'] = {}
            messages.success(request, "Заказ успешно оформлен!")
            return redirect('shop:order_history')
    else:
        form = OrderForm(initial={
            'delivery_phone': getattr(request.user.userprofile, 'phone', ''),
            'delivery_address': getattr(request.user.userprofile, 'address', ''),
        })
    return render(request, 'shop:checkout.html', {'form': form})

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'shop/order_history.html', {'orders': orders})

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