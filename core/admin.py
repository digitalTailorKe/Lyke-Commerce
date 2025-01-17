from django.contrib import admin, messages
from django.core.management import call_command
from core.models import CartOrderProducts, Country, Coupon, Currency, DealOfTheDay, Product, Category, Vendor, CartOrder, ProductImages, ProductReview, wishlist_model, Address, MpesaTransaction

class ProductImagesAdmin(admin.TabularInline):
    model = ProductImages

class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductImagesAdmin]
    list_editable = ['title', 'price', 'featured', 'product_status']
    list_display = ['user', 'title', 'product_image', 'price', 'category', 'vendor', 'featured', 'product_status', 'pid']

class CategoryAdmin(admin.ModelAdmin):
    list_display = ['title', 'category_image']

class VendorAdmin(admin.ModelAdmin):
    list_display = ['title', 'vendor_image']


class CartOrderAdmin(admin.ModelAdmin):
    list_editable = ['paid_status', 'product_status', 'sku']
    list_display = ['user',  'price', 'paid_status', 'paid_amount', 'order_date','product_status', 'sku']


class CartOrderProductsAdmin(admin.ModelAdmin):
    list_display = ['order', 'invoice_no', 'item', 'image','qty', 'price', 'total']


class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'review', 'rating']


class wishlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'date']


class AddressAdmin(admin.ModelAdmin):
    list_editable = ['address', 'status']
    list_display = ['user', 'address', 'status']

    
class MpesaTransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'MerchantRequestID', 'CheckoutRequestID', 'ResultCode', 'Amount', 'MpesaReceiptNumber', 'TransactionDate', 'PhoneNumber', 'is_finished', 'is_successful')
    search_fields = ('MerchantRequestID', 'CheckoutRequestID', 'MpesaReceiptNumber', 'PhoneNumber')
    list_filter = ('is_finished', 'is_successful', 'TransactionDate')
    ordering = ('-TransactionDate',)
    
    
class DealOfTheDayAdmin(admin.ModelAdmin):
    list_display = ['product', 'discount_percentage', 'start_time', 'end_time', 'is_active', 'is_current']
    list_filter = ['is_active', 'start_time', 'end_time']
    search_fields = ['product__title']
    readonly_fields = ['get_discounted_price']

    def get_discounted_price(self, obj):
        return obj.get_discounted_price()
    get_discounted_price.short_description = 'Discounted Price'

class CurrencyAdmin(admin.ModelAdmin):
    actions = ["seed_database"]

    def seed_database(self, request, queryset):
        try:
            call_command("seed_countries_and_currency")
            self.message_user(request, "Database seeded successfully.", messages.SUCCESS)
        except Exception as e:
            self.message_user(request, f"Error seeding database: {e}", messages.ERROR)

    seed_database.short_description = "Seed database with initial data"

    list_display = ('name', 'code', 'symbol', 'exchange_rate_to_usd')
    search_fields = ('name', 'code')
    list_filter = ('code',)
    ordering = ('name',)

class CountryAdmin(admin.ModelAdmin):
    list_display = ('name', 'currency')
    search_fields = ('name',)
    list_filter = ('currency',)
    ordering = ('name',)

admin.site.register(Country, CountryAdmin)
admin.site.register(Currency, CurrencyAdmin)
admin.site.register(DealOfTheDay, DealOfTheDayAdmin)
admin.site.register(MpesaTransaction, MpesaTransactionAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Vendor, VendorAdmin)
admin.site.register(CartOrder, CartOrderAdmin)
admin.site.register(CartOrderProducts, CartOrderProductsAdmin)
admin.site.register(ProductReview, ProductReviewAdmin)
admin.site.register(wishlist_model, wishlistAdmin)
admin.site.register(Address, AddressAdmin)
admin.site.register(Coupon)


