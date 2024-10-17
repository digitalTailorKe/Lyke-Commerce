
import base64
from decimal import Decimal
import threading
import datetime
import json
import sys
import time
import africastalking
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from requests import session
from requests.auth import HTTPBasicAuth
import requests
from taggit.models import Tag
from core.models import Coupon, DealOfTheDay, MpesaTransaction, Product, Category, ProductComparison, Vendor, CartOrder, CartOrderProducts, ProductImages, ProductReview, wishlist_model, Address
from userauths.models import ContactUs, Profile
from core.forms import ProductReviewForm, MpesaPaymentForm
from django.template.loader import render_to_string
from django.contrib import messages

from django.urls import reverse
from django.conf import settings
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from paypal.standard.forms import PayPalPaymentsForm
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
import calendar
from django.db.models import Count, Avg
from django.db.models.functions import ExtractMonth
from django.core import serializers
import stripe
from django.contrib.gis.geoip2 import GeoIP2
from django.core.mail import EmailMultiAlternatives
import ssl
from .middleware import country_to_currency_data 


def index(request):
    cart_data = request.session.get('cart_data_obj', {})
    compared_items = request.session.get('comparison', [])

    # Fetch location and currency details from the request
    user_location = getattr(request, 'location', {}) or {}
    current_currency = getattr(request, 'user_currency_code', 'USD')
    current_currency_rate = getattr(request, 'user_exchange_rate', 1.0)

    print(current_currency, 'index view')
    print(current_currency_rate, 'index view')

    user_country = user_location.get('country_name', 'Unknown')

    if request.user.is_authenticated:
        comparison = ProductComparison.objects.filter(user=request.user).first()
        filter_products = comparison.products.all() if comparison else []
    else:
        product_ids = request.session.get('comparison', [])
        filter_products = Product.objects.filter(id__in=product_ids)
    
    categorized_products = {}
    categories = Category.objects.all()

    # Fetch products per category that are featured
    for category in categories:
        products = Product.objects.filter(
            product_status="published",
            featured=True,
            category=category
        ).order_by("-id")
        categorized_products[category] = products

    products = Product.objects.filter(product_status="published", featured=True).order_by("-id")

    # Retrieve the already converted prices from the session
    converted_product_prices = request.session.get('converted_product_prices', {})
    converted_old_price = request.session.get('converted_old_price', {})

    print(converted_product_prices, "session products")

    current_time = timezone.now()
    deals = DealOfTheDay.objects.filter(start_time__lte=current_time, end_time__gte=current_time, is_active=True)
    tags = Tag.objects.all().order_by("-id")[:6]

    countries = getattr(request, 'countries', [])

    context = {
        "products": products,
        "categorized_products": categorized_products,
        "tags": tags,
        "deals": deals,
        "categories": categories,
        "cart_data": cart_data,
        "compared_items": compared_items,
        "filter_products": filter_products,
        "user_country": user_country,
        "current_currency": current_currency,
        "converted_product_prices": converted_product_prices,
        "converted_old_price": converted_old_price,
        "countries": countries
    }

    return render(request, 'core/index.html', context)


def product_list_view(request):
    
    products = Product.objects.filter(product_status="published").order_by("-id")
    current_time = timezone.now()
    deals = DealOfTheDay.objects.filter(start_time__lte=current_time, end_time__gte=current_time, is_active=True)
    tags = Tag.objects.all().order_by("-id")[:6]
    
    cart_data = request.session.get('cart_data_obj', {})
    print(cart_data, 'find')
    compared_items = request.session.get('comparison', [])
    print(compared_items, 'find')

    converted_product_prices = request.session.get('converted_product_prices', {})
    converted_old_price = request.session.get('converted_old_price', {})
    

    context = {
        "products":products,
        "tags":tags,
        "deals": deals,
        "cart_data": cart_data,
        "compared_items": compared_items,
         "converted_product_prices": converted_product_prices,
        "converted_old_price": converted_old_price
    }

    return render(request, 'core/product-list.html', context)


def category_list_view(request):
    categories = Category.objects.all()

    context = {
        "categories":categories
    }
    return render(request, 'core/category-list.html', context)


def category_product_list__view(request, cid):

    category = Category.objects.get(cid=cid) # food, Cosmetics
    products = Product.objects.filter(product_status="published", category=category)
    
    
    cart_data = request.session.get('cart_data_obj', {})
    print(cart_data, 'find')
    compared_items = request.session.get('comparison', [])
    print(compared_items, 'find')

    context = {
        "category":category,
        "products":products,
        "cart_data": cart_data,
        "compared_items": compared_items
    }
    
    return render(request, "core/category-product-list.html", context)


def vendor_list_view(request):
    vendors = Vendor.objects.all()
    context = {
        "vendors": vendors,
    }
    return render(request, "core/vendor-list.html", context)


def vendor_detail_view(request, vid):
    vendor = Vendor.objects.get(vid=vid)
    products = Product.objects.filter(vendor=vendor, product_status="published").order_by("-id")

    context = {
        "vendor": vendor,
        "products": products,
    }
    return render(request, "core/vendor-detail.html", context)


def product_detail_view(request, pid):
    product = Product.objects.get(pid=pid)
    # product = get_object_or_404(Product, pid=pid)
    products = Product.objects.filter(category=product.category).exclude(pid=pid)

    # Getting all reviews related to a product
    reviews = ProductReview.objects.filter(product=product).order_by("-date")

    # Getting average review
    average_rating = ProductReview.objects.filter(product=product).aggregate(rating=Avg('rating'))

    # Product Review form
    review_form = ProductReviewForm()


    make_review = True 

    if request.user.is_authenticated:
    
        try:
            address = Address.objects.get(status=True, user=request.user)
        except Address.DoesNotExist:
            address = None
        user_review_count = ProductReview.objects.filter(user=request.user, product=product).count()

        if user_review_count > 0:
            make_review = False
    
    address = "Login To Continue"


    p_image = product.p_images.all()

    context = {
        "p": product,
        "address": address,
        "make_review": make_review,
        "review_form": review_form,
        "p_image": p_image,
        "average_rating": average_rating,
        "reviews": reviews,
        "products": products,
    }

    return render(request, "core/product-detail.html", context)

def tag_list(request, tag_slug=None):

    products = Product.objects.filter(product_status="published").order_by("-id")

    tag = None 
    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        products = products.filter(tags__in=[tag])

    context = {
        "products": products,
        "tag": tag
    }

    return render(request, "core/tag.html", context)


def ajax_add_review(request, pid):
    product = Product.objects.get(pk=pid)
    user = request.user 

    review = ProductReview.objects.create(
        user=user,
        product=product,
        review = request.POST['review'],
        rating = request.POST['rating'],
    )

    context = {
        'user': user.username,
        'review': request.POST['review'],
        'rating': request.POST['rating'],
    }

    average_reviews = ProductReview.objects.filter(product=product).aggregate(rating=Avg("rating"))

    return JsonResponse(
       {
         'bool': True,
        'context': context,
        'average_reviews': average_reviews
       }
    )


def search_view(request):
    query = request.GET.get("q")

    products = Product.objects.filter(title__icontains=query).order_by("-date")

    context = {
        "products": products,
        "query": query,
    }
    return render(request, "core/search.html", context)


def filter_product(request):
    categories = request.GET.getlist("category[]")
    vendors = request.GET.getlist("vendor[]")


    min_price = request.GET['min_price']
    max_price = request.GET['max_price']

    products = Product.objects.filter(product_status="published").order_by("-id").distinct()

    products = products.filter(price__gte=min_price)
    products = products.filter(price__lte=max_price)


    if len(categories) > 0:
        products = products.filter(category__id__in=categories).distinct() 

    if len(vendors) > 0:
        products = products.filter(vendor__id__in=vendors).distinct() 
    
    
    data = render_to_string("core/async/product-list.html", {"products": products})
    return JsonResponse({"data": data})


def filter_products(request):
    if request.method == 'POST':
        data = json.loads(request.body)

        min_price = data.get('minPrice', 0)
        max_price = data.get('maxPrice', 1000)
        colors = data.get('colors', [])
        conditions = data.get('conditions', [])

        # Filter products based on the price range
        products = Product.objects.filter(price__gte=min_price, price__lte=max_price)

        # Filter products based on color
        if colors:
            products = products.filter(color__in=colors)

        # Filter products based on condition
        if conditions:
            products = products.filter(condition__in=conditions)

        # Render the filtered products back into HTML format
        html = render_to_string('your_product_partial_template.html', {'products': products})
        
        return JsonResponse({'html': html})
    

def add_to_cart(request):
    cart_product = {}

    cart_product[str(request.GET['id'])] = {
        'title': request.GET['title'],
        'qty': request.GET['qty'],
        'price': request.GET['price'],
        'image': request.GET['image'],
        'pid': request.GET['pid'],
    }
    
    print(cart_product)

    if 'cart_data_obj' in request.session:
        if str(request.GET['id']) in request.session['cart_data_obj']:

            cart_data = request.session['cart_data_obj']
            cart_data[str(request.GET['id'])]['qty'] = int(cart_product[str(request.GET['id'])]['qty'])
            cart_data.update(cart_data)
            request.session['cart_data_obj'] = cart_data
        else:
            cart_data = request.session['cart_data_obj']
            cart_data.update(cart_product)
            request.session['cart_data_obj'] = cart_data

    else:
        request.session['cart_data_obj'] = cart_product
    return JsonResponse({"data":request.session['cart_data_obj'], 'totalcartitems': len(request.session['cart_data_obj'])})



def cart_view(request):
    cart_total_amount = 0
    if 'cart_data_obj' in request.session:
        
        for p_id, item in request.session['cart_data_obj'].items():
            try:
                qty = int(item.get('qty', 0))
                price = float(item.get('price', 0))  # Default to 0 if price is missing or empty
                cart_total_amount += qty * price
            except ValueError:
                # Log the error or handle the case where the conversion failed
                messages.error(request, f"Invalid price or quantity for item {item.get('title', 'Unknown Item')}")
                continue
        print("\n\n\n ", request.session['cart_data_obj'] , "\n\n\n")
        print("\n\n\n ", cart_total_amount , "\n\n\n")
        return render(request, "core/cart.html", {
            "cart_data": request.session['cart_data_obj'],
            'totalcartitems': len(request.session['cart_data_obj']),
            'cart_total_amount': cart_total_amount
        })
    else:
        messages.warning(request, "Your cart is empty")
        return redirect("core:index")


def delete_item_from_cart(request):
    product_id = str(request.GET['id'])
    if 'cart_data_obj' in request.session:
        if product_id in request.session['cart_data_obj']:
            cart_data = request.session['cart_data_obj']
            del request.session['cart_data_obj'][product_id]
            request.session['cart_data_obj'] = cart_data
    
    cart_total_amount = 0
    if 'cart_data_obj' in request.session:
        for p_id, item in request.session['cart_data_obj'].items():
            cart_total_amount += int(item['qty']) * float(item['price'])

    context = render_to_string("core/async/cart-list.html", {"cart_data":request.session['cart_data_obj'], 'totalcartitems': len(request.session['cart_data_obj']), 'cart_total_amount':cart_total_amount})
    return JsonResponse({"data": context, 'totalcartitems': len(request.session['cart_data_obj'])})


def update_cart(request):
    product_id = str(request.GET['id'])
    product_qty = request.GET['qty']

    if 'cart_data_obj' in request.session:
        if product_id in request.session['cart_data_obj']:
            cart_data = request.session['cart_data_obj']
            cart_data[str(request.GET['id'])]['qty'] = product_qty
            request.session['cart_data_obj'] = cart_data
    
    cart_total_amount = 0
    if 'cart_data_obj' in request.session:
        for p_id, item in request.session['cart_data_obj'].items():
            cart_total_amount += int(item['qty']) * float(item['price'])

    context = render_to_string("core/async/cart-list.html", {"cart_data":request.session['cart_data_obj'], 'totalcartitems': len(request.session['cart_data_obj']), 'cart_total_amount':cart_total_amount})
    return JsonResponse({"data": context, 'totalcartitems': len(request.session['cart_data_obj'])})

@csrf_exempt
def save_checkout_info(request):
    total_amount = 0
    if request.method == "POST":
        full_name = request.POST.get("full_name")
        email = request.POST.get("email")
        mobile = request.POST.get("mobile")
        address = request.POST.get("address")
        city = request.POST.get("city")
        state = request.POST.get("state")
        country = request.POST.get("country")
        cart_total_amount = 0


        print(full_name)
        print(email)
        print(mobile)
        print(address)
        print(city)
        print(state)
        print(country)

        request.session['full_name'] = full_name
        request.session['email'] = email
        request.session['mobile'] = mobile
        request.session['address'] = address
        request.session['city'] = city
        request.session['state'] = state
        request.session['country'] = country


        if 'cart_data_obj' in request.session:

            # Getting total amount for Paypal Amount
            for p_id, item in request.session['cart_data_obj'].items():
                total_amount += int(item['qty']) * float(item['price'])


            full_name = request.session['full_name']
            email = request.session['email']
            mobile = request.session['mobile']
            address = request.session['address']
            city = request.session['city']
            state = request.session['state']
            country = request.session['country']

            # Create ORder Object
            order = CartOrder.objects.create(
                # user=request.user,
                user=request.user if request.user.is_authenticated else None,
                price=total_amount,
                full_name=full_name,
                email=email,
                phone=mobile,
                address=address,
                city=city,
                state=state,
                country=country,
            )
            
            print(order.oid)
            print(order.email)
            

            del request.session['full_name']
            del request.session['email']
            del request.session['mobile']
            del request.session['address']
            del request.session['city']
            del request.session['state']
            del request.session['country']

            # Getting total amount for The Cart
            for p_id, item in request.session['cart_data_obj'].items():
                cart_total_amount += int(item['qty']) * float(item['price'])

                cart_order_products = CartOrderProducts.objects.create(
                    order=order,
                    invoice_no="INVOICE_NO-" + str(order.id), # INVOICE_NO-5,
                    item=item['title'],
                    image=item['image'],
                    qty=item['qty'],
                    price=item['price'],
                    total=float(item['qty']) * float(item['price'])
                )

            clear_cart(request)


            send_payment_confirmation_email(request, to_email=email, order_id=order.oid)
            send_sms(mobile, order.oid, total_amount)

          
        return redirect("core:checkout", order.oid)
    return redirect("core:checkout", order.oid)


africastalking.initialize(settings.AFRICASTALKING_USERNAME, settings.AFRICASTALKING_API_KEY)
sms = africastalking.SMS

def send_sms(phone_number, order, price):

    if not phone_number.startswith('+'):
        phone_number = f'+{phone_number}'
        print(phone_number)

    message = f"Dear customer, your payment of {price} for order {order} has been received successfully. Thank you for shopping with us!"
    sender = "Lyke Enterprise LTD"
    sender_id = "43435"

    try:
        # Send the SMS using AfricasTalking SMS service
        response = sms.send(message, [phone_number])
        print(f"SMS sent successfully: {response}")
        return {"message": "SMS sent successfully", "response": response}
    except Exception as e:
        print(f"Failed to send SMS: {e}")
        return {"error": str(e)}

@csrf_exempt
def sms_delivery_callback(request):
    if request.method == 'POST':
        try:
            # Parse the incoming JSON data
            data = json.loads(request.body.decode('utf-8'))
            print(f'Delivery report response...\n {data}')
            
            # Return a 200 OK response
            return HttpResponse(status=200)
        
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    # Return 405 Method Not Allowed for non-POST requests
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def create_checkout_session(request, oid):
    order = CartOrder.objects.get(oid=oid)
    stripe.api_key = settings.STRIPE_SECRET_KEY

    checkout_session = stripe.checkout.Session.create(
        customer_email = order.email,
        payment_method_types=['card'],
        line_items = [
            {
                'price_data': {
                    'currency': 'USD',
                    'product_data': {
                        'name': order.full_name
                    },
                    'unit_amount': int(order.price * 100)
                },
                'quantity': 1
            }
        ],
        mode = 'payment',
        success_url = request.build_absolute_uri(reverse("core:payment-completed", args=[order.oid])) + "?session_id={CHECKOUT_SESSION_ID}",
        cancel_url = request.build_absolute_uri(reverse("core:payment-completed", args=[order.oid]))
    )

    order.paid_status = False
    order.stripe_payment_intent = checkout_session['id']
    order.save()

    print("checkkout session", checkout_session)
    return JsonResponse({"sessionId": checkout_session.id})


# @login_required  
def checkout(request, oid):
    order = CartOrder.objects.get(oid=oid)
    order_items = CartOrderProducts.objects.filter(order=order)
    
    initial_data = {
        'order_id': order.oid,
        'amount':  round(order.price), 
        'phone_number': order.phone,  
    }
    mpesa_form = MpesaPaymentForm(initial=initial_data)
    print(mpesa_form)
    if request.method == "POST":
      if 'code' in request.POST:
        code = request.POST.get("code")
        print("code========", code)
        coupon = Coupon.objects.filter(code=code, active=True).first()
        if coupon:
            if coupon in order.coupons.all():
                messages.warning(request, "Coupon already activated")
                return redirect("core:checkout", order.oid)
            else:
                discount = order.price * coupon.discount / 100 
                order.coupons.add(coupon)
                order.price -= discount
                order.saved += discount
                order.save()
                messages.success(request, "Coupon Activated")
        else:
            messages.error(request, "Coupon Does Not Exists")
        return redirect("core:checkout", order.oid)
    elif 'mpesa_form' in request.POST:
        print("Mpesa running")
        response = lipa_na_mpesa_online(request)
        print(response)
        return redirect("core:payment-completed", order.oid)

    context = {
        "order": order,
        "order_items": order_items,
        "stripe_publishable_key": settings.STRIPE_PUBLIC_KEY,
        "mpesa_form": mpesa_form
    }

    return render(request, "core/checkout.html", context)




# @login_required
def payment_completed_view(request, oid):
    order = CartOrder.objects.get(oid=oid)

    if order.paid_status == False:
        order.paid_status = True
        order.save()
    send_payment_confirmation_mail(order.email,order.oid)
        
    context = {
        "order": order,
        "stripe_publishable_key": settings.STRIPE_PUBLIC_KEY,
    }
    return render(request, 'core/payment-completed.html',  context)

    ## clear cart objects

def clear_cart(request):
    if 'cart_data_obj' in request.session:
        del request.session['cart_data_obj']
    return JsonResponse({"status": "Cart cleared"})


@login_required
def payment_failed_view(request):
    return render(request, 'core/payment-failed.html')


@login_required
def customer_dashboard(request):
    orders_list = CartOrder.objects.filter(user=request.user).order_by("-id")
    address = Address.objects.filter(user=request.user)


    orders = CartOrder.objects.annotate(month=ExtractMonth("order_date")).values("month").annotate(count=Count("id")).values("month", "count")
    month = []
    total_orders = []

    for i in orders:
        month.append(calendar.month_name[i["month"]])
        total_orders.append(i["count"])

    if request.method == "POST":
        address = request.POST.get("address")
        mobile = request.POST.get("mobile")

        new_address = Address.objects.create(
            user=request.user,
            address=address,
            mobile=mobile,
        )
        messages.success(request, "Address Added Successfully.")
        return redirect("core:dashboard")
    else:
        print("Error")
    
    user_profile = Profile.objects.get(user=request.user)
    print("user profile is: #########################",  user_profile)

    context = {
        "user_profile": user_profile,
        "orders": orders,
        "orders_list": orders_list,
        "address": address,
        "month": month,
        "total_orders": total_orders,
    }
    return render(request, 'core/dashboard.html', context)

def order_detail(request, id):
    order = CartOrder.objects.get(user=request.user, id=id)
    order_items = CartOrderProducts.objects.filter(order=order)

    
    context = {
        "order_items": order_items,
    }
    return render(request, 'core/order-detail.html', context)


def make_address_default(request):
    id = request.GET['id']
    Address.objects.update(status=False)
    Address.objects.filter(id=id).update(status=True)
    return JsonResponse({"boolean": True})

@login_required
def wishlist_view(request):
    wishlist = wishlist_model.objects.all()
    context = {
        "w":wishlist
    }
    return render(request, "core/wishlist.html", context)


    # w

def add_to_wishlist(request):
    product_id = request.GET['id']
    product = Product.objects.get(id=product_id)
    print("product id isssssssssssss:" + product_id)

    context = {}

    wishlist_count = wishlist_model.objects.filter(product=product, user=request.user).count()
    print(wishlist_count)

    if wishlist_count > 0:
        context = {
            "bool": True
        }
    else:
        new_wishlist = wishlist_model.objects.create(
            user=request.user,
            product=product,
        )
        context = {
            "bool": True
        }

    return JsonResponse(context)


# def remove_wishlist(request):
#     pid = request.GET['id']
#     wishlist = wishlist_model.objects.filter(user=request.user).values()

#     product = wishlist_model.objects.get(id=pid)
#     h = product.delete()

#     context = {
#         "bool": True,
#         "wishlist":wishlist
#     }
#     t = render_to_string("core/async/wishlist-list.html", context)
#     return JsonResponse({"data": t, "w":wishlist})

def remove_wishlist(request):
    pid = request.GET['id']
    wishlist = wishlist_model.objects.filter(user=request.user)
    wishlist_d = wishlist_model.objects.get(id=pid)
    delete_product = wishlist_d.delete()
    
    context = {
        "bool":True,
        "w":wishlist
    }
    wishlist_json = serializers.serialize('json', wishlist)
    t = render_to_string('core/async/wishlist-list.html', context)
    return JsonResponse({'data':t,'w':wishlist_json})





# Other Pages 
def contact(request):
    return render(request, "core/contact.html")


def ajax_contact_form(request):
    full_name = request.GET['full_name']
    email = request.GET['email']
    phone = request.GET['phone']
    subject = request.GET['subject']
    message = request.GET['message']

    contact = ContactUs.objects.create(
        full_name=full_name,
        email=email,
        phone=phone,
        subject=subject,
        message=message,
    )

    data = {
        "bool": True,
        "message": "Message Sent Successfully"
    }

    return JsonResponse({"data":data})


def about_us(request):
    return render(request, "core/about_us.html")


def purchase_guide(request):
    return render(request, "core/purchase_guide.html")

def privacy_policy(request):
    return render(request, "core/privacy_policy.html")

def terms_of_service(request):
    return render(request, "core/terms_of_service.html")

def get_mpesa_access_token(request):
    consumer_key = settings.MPESA_CONSUMER_KEY
    consumer_secret = settings.MPESA_CONSUMER_SECRET
    api_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    response = requests.get(api_url, auth=HTTPBasicAuth(consumer_key, consumer_secret))
    access_token = response.json().get('access_token')
    return JsonResponse({"access_token": access_token})


@csrf_exempt
def query_mpesa_payment(request):
    if request.method != 'POST':
        return JsonResponse({"error": "Only POST requests are allowed"}, status=405)

    try:
        data = json.loads(request.body)
        checkout_id = data.get('CheckoutRequestID')
        if not checkout_id:
            return JsonResponse({"error": "Checkout ID is required"}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON data"}, status=400)

    access_token = get_mpesa_access_token(request).content
    access_token_data = json.loads(access_token)
    access_token = access_token_data.get('access_token')

    if not access_token:
        return JsonResponse({"error": "Access token not found"}, status=500)

    api_url = "https://sandbox.safaricom.co.ke/mpesa/stkpushquery/v1/query"
    headers = {"Authorization": "Bearer " + access_token}

    business_short_code = settings.MPESA_EXPRESS_SHORTCODE
    lipa_na_mpesa_online_passkey = settings.MPESA_PASSKEY
    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    data_to_encode = business_short_code + lipa_na_mpesa_online_passkey + timestamp
    password = base64.b64encode(data_to_encode.encode()).decode('utf-8')

    payload = {
        "BusinessShortCode": business_short_code,
        "Password": password,
        "Timestamp": timestamp,
        "CheckoutRequestID": checkout_id
    }

    response = requests.post(api_url, json=payload, headers=headers)
    
    print("MPesa Raw response", response.text)
    
    try:
        json_response = json.loads(response.text)
    except json.JSONDecodeError as e:
        print("JSON Decode Error:", str(e))
        return JsonResponse({"error": "Invalid response from Mpesa"}, status=500)

    if 'ResultCode' in json_response:
        requestId = json_response.get('CheckoutRequestID')
        result_code = json_response['ResultCode']
        response_message = json_response['ResultDesc']
        
        try:
            transaction = MpesaTransaction.objects.get(CheckoutRequestID=requestId)
            order=CartOrder.objects.get(mpesa_checkout_request_id=checkout_id)
            
            transaction.ResultDesc=response_message
            transaction.ResultCode=result_code
            
            transaction.is_finished = True
            # transaction.is_successful = True
            if result_code == "0":
                transaction.is_successful = True
                order.payment_status="compeleted"
                order.paid_status = True
            else:
                transaction.is_successful = False
        
            transaction.save()
            
            # print(order.balance, "found order")
            
            
            
            return JsonResponse({
                "result_code": result_code,
                "finished": transaction.is_finished,
                "successful": transaction.is_successful,
                "message": response_message
            })
        except MpesaTransaction.DoesNotExist:
            return JsonResponse({"error": "Transaction not found"}, status=404)
    
    # Handle response and return it as JSON
    try:
        return JsonResponse(response.json(), status=response.status_code)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid response from M-Pesa API"}, status=500)


@csrf_exempt
def mpesa_callback(request):
    if request.method == "POST":
        try:
            # Parse the JSON data sent by the Daraja API
            data = json.loads(request.body.decode('utf-8'))
            print("Received Callback Data:", data)
            
            # You can process the data here (e.g., saving it to the database)
            # Example: Log the data or extract necessary details
            result_code = data.get("Body", {}).get("stkCallback", {}).get("ResultCode", None)
            result_desc = data.get("Body", {}).get("stkCallback", {}).get("ResultDesc", None)
            checkout_request_id = data.get("Body", {}).get("stkCallback", {}).get("CheckoutRequestID", None)
            
            
            # Extract the MpesaReceiptNumber from CallbackMetadata
            callback_metadata = data.get("Body", {}).get("stkCallback", {}).get("CallbackMetadata", {}).get("Item", [])
            
            mpesa_receipt_number = None
            amount = None
            phone_number = None
            transaction_date = None
            
            for item in callback_metadata:
                name = item.get("Name")
                value = item.get("Value")

                if name == "Amount":
                    amount = value
                elif name == "MpesaReceiptNumber":
                    mpesa_receipt_number = value
                elif name == "TransactionDate":
                    transaction_date = value
                elif name == "PhoneNumber":
                    phone_number = value

            # Log the extracted values for debugging
            print("Amount:", amount)
            print("MpesaReceiptNumber:", mpesa_receipt_number)
            print("TransactionDate:", transaction_date)
            print("PhoneNumber:", phone_number)
            
            print(f"Mpesa Receipt Number: {mpesa_receipt_number}")
            # Process the transaction (e.g., update the transaction in the database)
            # You might want to update your transaction records based on the ResultCode
            if result_code == 0:
                
                if checkout_request_id:
                    try:
                        mpesa_transaction = MpesaTransaction.objects.get(CheckoutRequestID = checkout_request_id)
                        
                        mpesa_transaction.ResultCode = result_code
                        mpesa_transaction.ResultDesc=result_desc
                        
                        mpesa_transaction.MpesaReceiptNumber=mpesa_receipt_number
                        mpesa_transaction.PhoneNumber=phone_number
                        mpesa_transaction.Amount=amount
                        mpesa_transaction.save()
                        
                        order = CartOrder.objects.get(mpesa_checkout_request_id = checkout_request_id)
                          
                        if order:
                            
                            # if order.mpesa_checkout_request_id == checkout_request_id:
                            #     return JsonResponse({"error": "Cannot use similar checkout id"})
                            
                            print("order found")
        
                            order.mpesa_receipt_number = mpesa_receipt_number
                            order.paid_amount = amount
                            order.payment_status = "completed"
                            order.paid_status = True
                            
                            order.save()
                            print("here")
                            send_payment_confirmation_mail(order.email,order.oid)
                            print("after here")


                        else:
                            print("order not found")
                        
                        print(f"Transaction {checkout_request_id} updated successfully.")
                        print(f"order {order.oid} updated successfully.")

                    except MpesaTransaction.DoesNotExist:
                            print(f"Transaction {checkout_request_id} does not exist.")
                            return JsonResponse({"error": f"Transaction {checkout_request_id} does not exist."}, status=400)
            else:
                if checkout_request_id:
                    try:
                        mpesa_transaction = MpesaTransaction.objects.get(CheckoutRequestID = checkout_request_id)
                        mpesa_transaction.ResultCode = result_code
                        mpesa_transaction.ResultDesc=result_desc
                        mpesa_transaction.is_finished=True
                        mpesa_transaction.is_successful=True
                        mpesa_transaction.save()
                        
                    except MpesaTransaction.DoesNotExist:
                        print(f"Transaction {checkout_request_id} does not exist.", file=sys.stderr)
                        return JsonResponse({"error": f"Transaction {checkout_request_id} does not exist."}, status=500)
                        
            # Log for demonstration
            response = f"Transaction {checkout_request_id} - Result: {result_desc} (Code: {result_code})"



            # Return a response to Safaricom
            # response = {
            #     "ResultCode": 0,  # 0 means success in Safaricom's API
            #     "ResultDesc": "Accepted"
            # }

            return JsonResponse(response, safe=False)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data"}, status=400)
        except Exception as e:
            print(f"Error processing callback: {e}")
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Invalid request method"}, status=405)

@csrf_exempt
def lipa_na_mpesa_online(request):
    if request.method == "POST":
        try:
            # Extract data from the request body (assuming it's JSON)
            data = json.loads(request.body.decode('utf-8'))
            amount = data.get('amount')
            phone_number = data.get('phone_number')
            order_id = data.get('order_id')
            order = CartOrder.objects.get(oid=order_id)
            
            if not amount or not phone_number:
                return JsonResponse({"error": "Amount and phone number are required"}, status=400)

            # Get the access token
            access_token = get_mpesa_access_token(request).content
            access_token_data = json.loads(access_token)
            access_token = access_token_data.get('access_token')

            if not access_token:
                return JsonResponse({"error": "Access token not found"}, status=500)

            # STK Push API URL and headers
            api_url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
            headers = {"Authorization": "Bearer " + access_token}

            # Payment details
            business_short_code = settings.MPESA_EXPRESS_SHORTCODE
            lipa_na_mpesa_passkey = settings.MPESA_PASSKEY
            timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
            data_to_encode = business_short_code + lipa_na_mpesa_passkey + timestamp
            password = base64.b64encode(data_to_encode.encode()).decode('utf-8')

            payload = {
                "BusinessShortCode": business_short_code,
                "Password": password,
                "Timestamp": timestamp,
                "TransactionType": "CustomerPayBillOnline",
                "Amount": str(amount),
                "PartyA": phone_number,
                "PartyB": business_short_code,
                "PhoneNumber": phone_number,
                "CallBackURL": "https://dc53-2409-4072-ebf-8658-cd16-f006-9df0-bab0.ngrok-free.app/mpesa/callback/",
                "AccountReference": order_id,
                "TransactionDesc": "Payment for XYZ"
            }
            
            print(payload)

            # Make the STK Push request
            response = requests.post(api_url, json=payload, headers=headers)
            json_response = response.json()
            print("Mpesa response", json_response)

            if json_response.get("ResponseCode") == "0":
                checkout_id = json_response["CheckoutRequestID"]
                
                
                # Save the transaction to the database
                MpesaTransaction.objects.create(
                    MerchantRequestID=json_response["MerchantRequestID"],
                    CheckoutRequestID=checkout_id,
                    ResultCode=json_response["ResponseCode"],
                    ResultDesc=json_response["ResponseDescription"],
                    PhoneNumber=phone_number,
                    order_id=order_id,
                    is_finished=False,
                    is_successful=False
                )
                
                # Update order with payment info
                order.mpesa_checkout_request_id = checkout_id
                # order.paid_status = False
                order.save()

                # Start background thread for querying payment status
                # query_thread = threading.Thread(target=query_mpesa_payment_async, args=(checkout_id, request))
                # query_thread.start()

                # Respond to the user immediately
                return JsonResponse({"CheckoutRequestID": json_response["CheckoutRequestID"]})

            else:
                return JsonResponse({"error": json_response.get("errorMessage", "Unknown error")}, status=400)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=405)

@csrf_exempt
def register_url(request):
    access_token = get_mpesa_access_token(request).content
    access_token_data = json.loads(access_token)
    print(access_token_data)
    access_token = access_token_data.get('access_token')
    
    if not access_token:
        return JsonResponse({"error": "Access token invalid"})
    
    api_url = "https://sandbox.safaricom.co.ke/mpesa/c2b/v1/registerurl"
    headers = { "Authorization": "Bearer " + access_token }
    
    business_short_code = settings.MPESA_EXPRESS_SHORTCODE
    response_type = settings.MPESA_RESPONSE_TYPE
    confirmation_url = "127.0.0.1:8000/lyke/confirmation/"
    validation_url = "[127.0.0.1:8000/validation/]"
   
 
    payload = {
        "ShortCode": business_short_code,
        "ResponseType": response_type,
        "ConfirmationURL": confirmation_url,
        "ValidationURL": validation_url,
    }
    
    print(payload)

    response = requests.post(api_url, json=payload, headers=headers)
    json_response = response.json()
    print("registered urls", json_response)

    return JsonResponse(json_response)
    
@csrf_exempt
def confirm(request):
    if request.method == "POST":
        data = json.loads(request.body.decode('utf-8'))
        trans_type = data.get('TransactionType')
        trans_id = data.get('TransID')
        trans_time = data.get('TransTime')
        trans_amount = data.get('TransAmount')
        business_code = data.get('BusinessShortCode')
        invoice = data.get('InvoiceNumber')
        bill_refrence = data.get('BillRefNumber')
        org_account_balance = data.get('OrgAccountBalance')
        third_party_trans_id = data.get('ThirdPartyTransID')
        msisdn = data.get('MSISDN')
        first_name = data.get('FirstName')
        middle_name = data.get('MiddleName')
        last_name = data.get('LastName')
        
        if bill_refrence:
            try:
                order = CartOrder.objects.get(oid=bill_refrence)
                previous_receipt = order.mpesa_receipt_number
                if previous_receipt == trans_id:
                    return JsonResponse({
                        "ResultCode": "C2B00012",
                        "ResultDesc": "rejected"
                    })
                if order.price != Decimal(trans_amount):
                    return JsonResponse({ 
                        "ResultCode": "C2B00013", 
                        "ResultDesc": "rejected" 
                    })
                order.mpesa_receipt_number = trans_id
                order.save()

            except CartOrder.DoesNotExist:
                return JsonResponse({ 
                    "ResultCode": "C2B00012", 
                    "ResultDesc": "rejected" 
                })
            
        else:
            return JsonResponse({
                "ResultCode": "C2B00012",
                "ResultDesc": "rejected"
            })

        # if bill_refrence:
            
        #     try:
        #         order = CartOrder.objects.get(oid=bill_refrence)
        #         previous_receipt = order.mpesa_receipt_number                
        #         if previous_receipt == trans_id:
        #            return JsonResponse({
        #                 "ResultCode": "C2B00012",
        #                 "ResultDesc": "rejected"
        #             })
        #         else:
        #             order.mpesa_receipt_number = trans_id
        #     except CartOrder.DoesNotExist:
        #         return JsonResponse({ "ResultCode": "C2B00012", "ResultDesc": "rejected" })
            
        #     order_balance = order.balance
        #     original_pay = order.paid_amount
        #     order_price = order.price
            
        #     print(original_pay)
        #     paid_balance = order_balance - Decimal(trans_amount)
        #     updated_pay = original_pay + Decimal(trans_amount)
            
        #     order.paid_amount  = updated_pay
        #     order.balance = paid_balance
            
        #     if updated_pay == order_price:
        #         order.payment_status = "draft"
        #     elif updated_pay < order_price:
        #         order.payment_status = "paid-partially"
        #     elif updated_pay > order_price:
        #         order.payment_status = "over-pay"
                
        #     print(order.payment_status)

        #     print(paid_balance)
        #     order.paid_status = True
            
        #     order.save() 
        # else:
        #     return JsonResponse({
        #         "ResultCode": "C2B00012",
        #         "ResultDesc": "rejected"
        #     })
            
        
        # return JsonResponse({
        #     "ResultCode": "0",
        #     "ResultDesc": "Accepted"
        #     })
     
@csrf_exempt  
def valid(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode('utf-8'))
            bill_refrence = data.get('BillRefNumber')
            amount = data.get('TransAmount')

            try:
                order = CartOrder.objects.filter(oid=bill_refrence).first()
                order_price = order.price
                if order:
                    if order_price == Decimal(amount):
                        return JsonResponse({
                           "ResultCode": "0",
                           "ResultDesc": "Accepted"
                        })
                    else:
                        return JsonResponse({
                          "ResultCode": "C2B00013",
                          "ResultDesc": "rejected"
                        })
                else:
                    return JsonResponse({
                        "ResultCode": "C2B00012",
                        "ResultDesc": "rejected"
                    })

            
            except:
                return JsonResponse({
                    "ResultCode": "C2B00012",
                    "ResultDesc": "rejected"
                })    
    
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data"}, status=400)
        except Exception as e:
            print(f"Error processing validation: {e}")
            return JsonResponse({"error": str(e)}, status=500)
    else:
      return JsonResponse({ "error": "Invalid request method"}, status=405)
        


# @csrf_exempt
# def send_payment_confirmation_sms(request):
#     json_data = json.loads(request.body.decode('utf-8'))
#     number = json_data.get('phone_number')
#     phone_number = [number]
#     # phone_number = ["+254794570888"]
#     # order = '10000'
#     # price= '20'
#     order = json_data.get('order')
#     price = json_data.get('price')

#     message = f"Dear customer, your payment of {price} for order {order} has been received successfully. Thank you for shopping with us!"
#     sender = "Lyke Enterprise LTD"
#     sender_id="43435"
    
#     # def on_finish(error, response):
#     # if error is not None:
#     #     raise error
#     # print(response)
 
#     try:
#         # Send the SMS using AfricasTalking SMS service
#         response = sms.send(message, phone_number)
#         print(f"SMS sent successfully: {response}")
#         # Return a dictionary as the JsonResponse data
#         return JsonResponse({"message": "SMS sent successfully", "response": response})
#     except Exception as e:
#         print(f"Failed to send SMS: {e}")
#         # Return the exception as a string in a dictionary
#         return JsonResponse({"error": str(e)})

@csrf_exempt
def send_payment_confirmation_email(request, to_email, order_id):
    
    order = CartOrder.objects.get(oid=order_id)
    print(order, "inside email")
    """
    Send a payment confirmation email to the client using Django's email service
    """
    subject = "Payment Confirmation"
    from_email = settings.DEFAULT_FROM_EMAIL
    print(to_email)
    print(f"Sending email from: {from_email}")

    # HTML content (email body)
    html_content = render_to_string("email/order_confirmation.html", {
        'order': order,  # You can pass any variables you want to the template
    })

    # Sending the email with both plain text and HTML versions
    try:
        email = EmailMultiAlternatives(subject, html_content, from_email, [to_email])
        email.content_subtype = "html"  # Main content is now HTML
        email.send()
        print(f"Email sent successfully to {to_email}")
    except Exception as e:
        print(f"Failed to send email: {e}")


def send_payment_confirmation_mail( to_email, order_id ):
    
    order = CartOrder.objects.get(oid=order_id)
    print(order, "inside email")
    """
    Send a payment confirmation email to the client using Django's email service
    """
    subject = "Payment Confirmation"
    from_email = settings.DEFAULT_FROM_EMAIL
    print(to_email)
    print(f"Sending email from: {from_email}")

    # HTML content (email body)
    html_content = render_to_string("email/payment_confirmation.html", {
        'order': order,  # You can pass any variables you want to the template
    })

    # Sending the email with both plain text and HTML versions
    try:
        email = EmailMultiAlternatives(subject, html_content, from_email, [to_email])
        email.content_subtype = "html"  # Main content is now HTML
        email.send()
        print(f"Email sent successfully to {to_email}")
    except Exception as e:
        print(f"Failed to send email: {e}")
        
        
        
@csrf_exempt  # This is just to allow the view to accept requests without CSRF token, remove in production or secure with a CSRF token
def send_payment_email_view(request):
    if request.method == "POST":
        try:
            # Assuming the data comes in JSON format
            data = json.loads(request.body)

            # Extract the necessary data (email, order ID, etc.)
            to_email = data.get('email')
            order_id = data.get('order_id')
            print(to_email)
            # Retrieve the order from the database
            order = CartOrder.objects.get(oid=order_id)
            print(order)

            # Call the email sending function
            send_payment_confirmation_email(to_email, order)

            # Return a success response
            return JsonResponse({'status': 'success', 'message': 'Email sent successfully'})

        except CartOrder.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Order not found'}, status=404)

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)
        
@csrf_exempt
def add_to_comparison(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.user.is_authenticated:
        # Fetch or create comparison object for the authenticated user
        comparison, created = ProductComparison.objects.get_or_create(user=request.user)
        comparison.products.add(product)
        
        # Get the total count of compared products for the authenticated user
        total_comparison_items = comparison.products.count()
        
        print("Added product to user's comparison list")
    else:
        # For non-authenticated users, handle comparison via session
        comparison = request.session.get('comparison', [])
        
        if product_id not in comparison:
            comparison.append(product_id)
            request.session['comparison'] = comparison
            print("Added product to session-based comparison list")
            messages.success(request, "Successfuly added product to comparison")
        
        # Get the total count of compared products in the session
        total_comparison_items = len(comparison)
        print(total_comparison_items)

        # Fetch updated filter_products after adding the new product
        if request.user.is_authenticated:
            comparison = ProductComparison.objects.filter(user=request.user).first()
            filter_products = comparison.products.all() if comparison else []
        else:
            product_ids = request.session.get('comparison', [])
            filter_products = Product.objects.filter(id__in=product_ids)

    # Render the comparison section HTML
        comparison_html = render_to_string('core/comparison_section.html', {
            'filter_products': filter_products
        })
        print(comparison_html)
    # Return success response along with the total number of items in comparison
    return JsonResponse({
        'success': True,
        'total_comparison_items': total_comparison_items,
        'comparison_html': comparison_html
    })

def compare_count(request):
    if request.user.is_authenticated:
        comparison = ProductComparison.objects.filter(user=request.user).first()
        count = comparison.products.count() if comparison else 0
    else:
        compare_list = request.session.get('comparison', [])
        count = len(compare_list)
    
    return JsonResponse({'compare_count': count})

def remove_from_comparison(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.user.is_authenticated:
        comparison = get_object_or_404(ProductComparison, user=request.user)
        comparison.products.remove(product)
    else:
        # Session-based comparison
        comparison = request.session.get('comparison', [])
        if product_id in comparison:
            comparison.remove(product_id)
            request.session['comparison'] = comparison

    return JsonResponse({'success': True})

def compare_products(request):
    if request.user.is_authenticated:
        comparison = ProductComparison.objects.filter(user=request.user).first()
        products = comparison.products.all() if comparison else []
    else:
        product_ids = request.session.get('comparison', [])
        products = Product.objects.filter(id__in=product_ids)


    return render(request, 'core/compare.html', {'products': products})


def deals_of_the_day(request):
    current_time = timezone.now()
    deals = DealOfTheDay.objects.filter(start_time__lte=current_time, end_time__gte=current_time, is_active=True)
    
    
    context = {
        "deals": deals
    }
    
    return render(request, 'core/deals.html', context)

@login_required
def order_tracking(request):
    orders_list = CartOrder.objects.filter(user=request.user).order_by("-id")
    address = Address.objects.filter(user=request.user)


    orders = CartOrder.objects.annotate(month=ExtractMonth("order_date")).values("month").annotate(count=Count("id")).values("month", "count")
    month = []
    total_orders = []

    for i in orders:
        month.append(calendar.month_name[i["month"]])
        total_orders.append(i["count"])

    
    user_profile = Profile.objects.get(user=request.user)
    print("user profile is: #########################",  user_profile)

    context = {
        "user_profile": user_profile,
        "orders": orders,
        "orders_list": orders_list,
        "address": address,
        "month": month,
        "total_orders": total_orders,
    }

    return render(request, 'core/order_tracking.html', context)


@login_required
def order_tracking_detail(request, oid):
    order = CartOrder.objects.get(user=request.user, oid=oid)
    order_items = CartOrderProducts.objects.filter(order=order)

    
    context = {
        "order": order,
        "order_items": order_items
    }
    return render(request, 'core/order-tracking-detail.html', context)

@login_required
def track_order(request):
    if request.method == "POST":
        order_id = request.POST.get('order_id')
        billing_email = request.POST.get('billing_email')
        
        try:
            order = CartOrder.objects.get(oid=order_id, email=billing_email)
            order_items = CartOrderProducts.objects.filter(order=order)
            return render(request, 'core/track-order.html', {'order': order, 'order_items': order_items})
        except CartOrder.DoesNotExist:
            return render(request, 'order_tracking.html', {'error': 'Order not found. Please check your Order ID and email.'})
    
    return render(request, 'core/order_tracking.html')

def confirm_payment(request, oid):
    cart_order = CartOrder.objects.get(oid=oid)
    
    initial_data = {
        'order_id': cart_order.oid,
        'amount':  round(cart_order.price), 
        'phone_number': cart_order.phone,  
    }
    mpesa_form = MpesaPaymentForm(initial=initial_data)
    print(initial_data)
    
    if request.method == "POST":
        if 'mpesa_form' in request.POST:
            print("mpesa_running")
            response = lipa_na_mpesa_online(request)
            print(response)
            return redirect("core:payment-completed", cart_order.id)
            
    
    context = {
        "cart_order": cart_order,
        "mpesa_form": mpesa_form
    }
    
    return render(request, 'core/payment-confirmation.html',  context)
    

# Assuming you have `country_to_currency_data` defined elsewhere
# and the `CURRENCY_API_URL`
CURRENCY_API_URL = 'https://api.currencyfreaks.com/v2.0/rates/latest'

def get_currency_rate(request, country_name):
    # Get the currency code for the selected country
    currency_code = None
    for entry in country_to_currency_data:
        if entry['country'] == country_name:
            currency_code = entry['currency_code']
            break

    if not currency_code:
        return JsonResponse({'success': False, 'message': 'Country not found'}, status=404)

    # Fetch the latest currency rate from the external API
    api_key = settings.CURRENCYFREAKS_API_KEY
    try:
        response = requests.get(CURRENCY_API_URL, params={'apikey': api_key})
        data = response.json()

        if response.status_code == 200 and 'rates' in data:
            rates = data.get('rates', {})
            exchange_rate = float(rates.get(currency_code, 1.0))  # Default to 1.0 if not found

            # Store currency and exchange rate in session
            request.session['user_currency_code'] = currency_code
            request.session['user_exchange_rate'] = exchange_rate
            request.session['user_country'] = country_name

            # Convert product prices and store them in session
            products = Product.objects.filter(product_status="published", featured=True)
            product_prices_in_session = {}
            product_old_prices_in_session = {}

            for product in products:
                converted_price = product.price * Decimal(exchange_rate)
                converted_old_price = product.old_price * Decimal(exchange_rate)
                product_prices_in_session[product.id] = float(converted_price)
                product_old_prices_in_session[product.id] = float(converted_old_price)

            request.session['converted_product_prices'] = product_prices_in_session
            request.session['converted_old_price'] = product_old_prices_in_session

            return JsonResponse({
                'success': True,
                'currency_code': currency_code,
                'exchange_rate': exchange_rate,
                'converted_prices': product_prices_in_session,
                'converted_old_prices': product_old_prices_in_session,
            })
        else:
            return JsonResponse({'success': False, 'message': 'Failed to fetch currency rates'}, status=500)

    except requests.exceptions.RequestException as e:
        print(f"CurrencyFreaks API Error: {e}")
        return JsonResponse({'success': False, 'message': 'API request failed'}, status=500)
