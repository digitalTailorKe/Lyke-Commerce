def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
        print(ip)
    return ip


from decimal import Decimal

def convert_prices(request, products):
    current_currency_rate = Decimal(request.session.get('user_exchange_rate', 1.0))
    converted_product_prices = {}
    converted_old_prices = {}

    for product in products:
        converted_price = product.price * current_currency_rate
        converted_old_price = product.old_price * current_currency_rate
        print(converted_old_price, 'old price')

        converted_product_prices[product.id] = float(round(converted_price, 2))
        if converted_old_price:
            converted_old_prices[product.id] = float(round(converted_old_price, 2))

    request.session['converted_product_prices'] = converted_product_prices
    request.session['converted_old_prices'] = converted_old_prices
    print(converted_old_prices, 'old price')
    return converted_product_prices, converted_old_prices
