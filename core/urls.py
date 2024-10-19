from django import views
from django.urls import path, include
from core.views import add_to_cart, add_to_comparison, add_to_wishlist, ajax_add_review, ajax_contact_form, cart_view, category_list_view, category_product_list__view, checkout, compare_count, compare_products, customer_dashboard, delete_item_from_cart, filter_product, index, make_address_default, order_detail, payment_completed_view, payment_failed_view, product_detail_view, product_list_view, remove_from_comparison, remove_wishlist, search_view, show_and_delete_messages, tag_list, update_cart, valid, vendor_detail_view, vendor_list_view, wishlist_view, contact, about_us, purchase_guide, privacy_policy, terms_of_service, query_mpesa_payment, lipa_na_mpesa_online, query_mpesa_payment,mpesa_callback, send_payment_confirmation_email, deals_of_the_day, order_tracking, order_tracking_detail, track_order
from core import views

app_name = "core"

urlpatterns = [

    # Homepage
    path("", index, name="index"),
    path("products/", product_list_view, name="product-list"),
    path("product/<pid>/", product_detail_view, name="product-detail"),
    path('messages/', show_and_delete_messages, name='show_and_delete_messages'),


    # Category
    path("category/", category_list_view, name="category-list"),
    path("category/<cid>/", category_product_list__view, name="category-product-list"),

    # Vendor
    path("vendors/", vendor_list_view, name="vendor-list"),
    path("vendor/<vid>/", vendor_detail_view, name="vendor-detail"),

    # Tags
    path("products/tag/<slug:tag_slug>/", tag_list, name="tags"),

    # Add Review
    path("ajax-add-review/<int:pid>/", ajax_add_review, name="ajax-add-review"),

    # Search
    path("search/", search_view, name="search"),

    # Filter product URL
    path("filter-products/", filter_product, name="filter-product"),

    # Add to cart URL
    path("add-to-cart/", add_to_cart, name="add-to-cart"),

    # Cart Page URL
    path("cart/", cart_view, name="cart"),

    # Delete ITem from Cart
    path("delete-from-cart/", delete_item_from_cart, name="delete-from-cart"),

    # Update  Cart
    path("update-cart/", update_cart, name="update-cart"),

      # Checkout  URL
    path("checkout/<oid>/", checkout, name="checkout"),

    # Paypal URL
    path('paypal/', include('paypal.standard.ipn.urls')),

    # Payment Successful
    path("payment-completed/<oid>/", payment_completed_view, name="payment-completed"),

    # Payment Failed
    path("payment-failed/", payment_failed_view, name="payment-failed"),

    # Dahboard URL
    path("dashboard/", customer_dashboard, name="dashboard"),

    # Order Detail URL
    path("dashboard/order/<int:id>", order_detail, name="order-detail"),

    # Making address defauly
    path("make-default-address/", make_address_default, name="make-default-address"),

    # wishlist page
    path("wishlist/", wishlist_view, name="wishlist"),

    # adding to wishlist
    path("add-to-wishlist/", add_to_wishlist, name="add-to-wishlist"),


    # Remvoing from wishlist
    path("remove-from-wishlist/", remove_wishlist, name="remove-from-wishlist"),


    path("contact/", contact, name="contact"),
    path("ajax-contact-form/", ajax_contact_form, name="ajax-contact-form"),

    path("about_us/", about_us, name="about_us"),
    path("purchase_guide/", purchase_guide, name="purchase_guide"),
    path("privacy_policy/", privacy_policy, name="privacy_policy"),
    path("terms_of_service/", terms_of_service, name="terms_of_service"),
    
    #Admin soft new code
    path('', include('admin_soft.urls')),


    #New Routes

    path("save_checkout_info/", views.save_checkout_info, name="save_checkout_info"),
    path("api/create_checkout_session/<oid>/", views.create_checkout_session, name="create_checkout_session"),

    path('mpesa/token', views.get_mpesa_access_token, name="get_mpesa_access_token"),
    path('mpesa/stkpush', views.lipa_na_mpesa_online, name="lipa_na_mpesa_online"),

    # path('mpesa/token/', get_mpesa_access_token, name='get_mpesa_access_token'),
    # path('mpesa/pay/', lipa_na_mpesa_online, name='lipa_na_mpesa_online'),
    path('mpesa/callback/', mpesa_callback, name='mpesa_callback'),
    path('mpesa/query/', query_mpesa_payment, name='query_mpesa_payment'),
    # path('payment-confirm-sms/', send_payment_confirmation_sms, name="send_payment_confirmation_sms"),
    path('payment-confirm-email/', send_payment_confirmation_email, name="send_payment_confirmation_email"),
    
    path('compare/add/<int:product_id>/', add_to_comparison, name='add_to_comparison'),
    path('compare/remove/<int:product_id>/', remove_from_comparison, name='remove_from_comparison'),
    path('compare/', compare_products, name='compare_products'),
    path('compare/count/', compare_count, name='compare_count'),
    path('deals-of-days/', deals_of_the_day, name="deals_of_the_day"),
    path('order-tracking/', order_tracking, name="order_tracking"),
    path("order-tracking/<int:oid>/", order_tracking_detail, name="order-tracking-detail"),
    path('track-order/', views.track_order, name='track-order'),
    path('confirm-payment/<int:oid>/', views.confirm_payment, name='confirm_payment'),
    path('register-url/', views.register_url, name="register-url"),
    path('validation/', valid, name="valid"),
    path("lyke/confirmation", views.confirm, name="confirm"),
    path("confirmation/email", views.send_payment_email_view, name="order_confirmation"),
    path("sms/callback", views.sms_delivery_callback, name="sms_callback" ),
    path('check-order-status/<str:oid>/', views.check_order_status, name='check_order_status')   
]