# shop/context_processors.py

def cart_count(request):
    """
    Контекстный процессор для подсчета количества товаров в корзине.
    """
    cart = request.session.get('cart', {})
    total_items = sum(cart.values())
    return {'cart_count': total_items}