from django.db import models
from shortuuid.django_fields import ShortUUIDField
from django.utils.html import mark_safe
from userauths.models import User
from taggit.managers import TaggableManager
from django_ckeditor_5.fields import CKEditor5Field 
from django.utils import timezone


STATUS_CHOICE = (
    ("processing", "Processing"),
    ("shipped", "Shipped"),
    ("delivered", "Delivered"),
)

PAYMENT_CHOICE = (
    ("draft", "Draft"),
    ("pending", "Pending"),
    ("processing", "Processing"),
    ("onhold", "Onhold"),
    ("completed", "Completed"),
    ("failed", "Failed"),
    ("cancelled", "Cancelled"),
    ("refunded", "Refunded"),
    ("paid-partially", "Paid partially"),
    ("over-pay", "Over pay"),
    ("failed", "Failed"),
)

STATUS = (
    ("draft", "Draft"),
    ("disabled", "Disabled"),
    ("rejected", "Rejected"),
    ("in_review", "In Review"),
    ("published", "Published"),
)



RATING = (
    ( 1,  "★☆☆☆☆"),
    ( 2,  "★★☆☆☆"),
    ( 3,  "★★★☆☆"),
    ( 4,  "★★★★☆"),
    ( 5,  "★★★★★"),
)




def user_directory_path(instance, filename):
    return 'user_{0}/{1}'.format(instance.user.id, filename)

class Category(models.Model):
    cid = ShortUUIDField(unique=True, length=10, max_length=20, prefix="cat", alphabet="abcdefgh12345")
    title = models.CharField(max_length=100, default="Food")
    image = models.ImageField(upload_to="category", default="category.jpg")

    class Meta:
        verbose_name_plural = "Categories"

    def category_image(self):
        return mark_safe('<img src="%s" width="50" height="50" />' % (self.image.url))

    def __str__(self):
        return self.title

class Tags(models.Model):
    pass


class Vendor(models.Model):
    vid = ShortUUIDField(unique=True, length=10, max_length=20, prefix="ven", alphabet="abcdefgh12345")

    title = models.CharField(max_length=100, default="Nestify")
    image = models.ImageField(upload_to=user_directory_path, default="vendor.jpg")
    cover_image = models.ImageField(upload_to=user_directory_path, default="vendor.jpg")
    # description = models.TextField(null=True, blank=True, default="I am am Amazing Vendor")
    description = CKEditor5Field(null=True, blank=True, default="I am am Amazing Vendor")

    address = models.CharField(max_length=100, default="123 Main Street.")
    contact = models.CharField(max_length=100, default="+123 (456) 789")
    chat_resp_time = models.CharField(max_length=100, default="100")
    shipping_on_time = models.CharField(max_length=100, default="100")
    authentic_rating = models.CharField(max_length=100, default="100")
    days_return = models.CharField(max_length=100, default="100")
    warranty_period = models.CharField(max_length=100, default="100")

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    date = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        verbose_name_plural = "Vendors"

    def vendor_image(self):
        return mark_safe('<img src="%s" width="50" height="50" />' % (self.image.url))

    def __str__(self):
        return self.title


class Product(models.Model):
    pid = ShortUUIDField(unique=True, length=10, max_length=20, alphabet="abcdefgh12345")

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name="category")
    vendor = models.ForeignKey(Vendor, on_delete=models.SET_NULL, null=True, related_name="product")

    title = models.CharField(max_length=100, default="Fresh Pear")
    image = models.ImageField(upload_to=user_directory_path, default="product.jpg")
    # description = models.TextField(null=True, blank=True, default="This is the product")
    description = CKEditor5Field(null=True, blank=True, default="This is the product")

    price = models.DecimalField(max_digits=12, decimal_places=2, default="1.99")
    old_price = models.DecimalField(max_digits=12, decimal_places=2, default="2.99")

    specifications = CKEditor5Field(null=True, blank=True)
    # specifications = models.TextField(null=True, blank=True)
    type = models.CharField(max_length=100, default="Organic", null=True, blank=True)
    stock_count = models.CharField(max_length=100, default="10", null=True, blank=True)
    life = models.CharField(max_length=100, default="100 Days", null=True, blank=True)
    mfd = models.DateTimeField(auto_now_add=False, null=True, blank=True)

    tags = TaggableManager(blank=True)

    # tags = models.ForeignKey(Tags, on_delete=models.SET_NULL, null=True)

    product_status = models.CharField(choices=STATUS, max_length=10, default="in_review")

    status = models.BooleanField(default=True)
    in_stock = models.BooleanField(default=True)
    featured = models.BooleanField(default=False)
    digital = models.BooleanField(default=False)

    sku = ShortUUIDField(unique=True, length=4, max_length=10, prefix="sku", alphabet="1234567890")

    date = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(null=True, blank=True)



    class Meta:
        verbose_name_plural = "Products"

    def product_image(self):
        return mark_safe('<img src="%s" width="50" height="50" />' % (self.image.url))

    def __str__(self):
        return self.title

    def get_precentage(self):
        new_price = (self.price / self.old_price) * 100
        return new_price


class ProductImages(models.Model):
    images = models.ImageField(upload_to="product-images", default="product.jpg")
    product = models.ForeignKey(Product, related_name="p_images", on_delete=models.SET_NULL, null=True)
    date = models.DateTimeField(auto_now_add=True)


    class Meta:
        verbose_name_plural = "Product Images"


############################################## Cart, Order, OrderITems and Address ##################################
############################################## Cart, Order, OrderITems and Address ##################################
############################################## Cart, Order, OrderITems and Address ##################################
############################################## Cart, Order, OrderITems and Address ##################################


class CartOrder(models.Model):
    # user = models.ForeignKey(User, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    full_name = models.CharField(max_length=100, null=True, blank=True)
    email = models.CharField(max_length=100, null=True, blank=True)
    phone = models.CharField(max_length=100, null=True, blank=True)

    address = models.CharField(max_length=100, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=100, null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)


    price = models.DecimalField(max_digits=12, decimal_places=2, default="0.00")
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, default="0.00")
    saved = models.DecimalField(max_digits=12, decimal_places=2, default="0.00")
    coupons = models.ManyToManyField("core.Coupon", blank=True)
    shipping_method = models.CharField(max_length=100, null=True, blank=True)
    tracking_id = models.CharField(max_length=100, null=True, blank=True)
    tracking_website_address = models.CharField(max_length=100, null=True, blank=True)


    paid_status = models.BooleanField(default=False, null=True, blank=True)
    payment_status = models.CharField(choices=PAYMENT_CHOICE, max_length=30, default="draft")
    order_date = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    product_status = models.CharField(choices=STATUS_CHOICE, max_length=30, default="processing")
    sku = ShortUUIDField(null=True, blank=True, length=5, prefix="SKU", max_length=20, alphabet="1234567890")
    oid = ShortUUIDField(null=True, blank=True, length=8, max_length=20, alphabet="1234567890")
    stripe_payment_intent = models.CharField(max_length=1000, null=True, blank=True)
    mpesa_checkout_request_id = models.CharField(max_length=1000, null=True, blank=True)
    mpesa_receipt_number = models.CharField(max_length=1000, null=True, blank=True)
    
    
    
    date = models.DateTimeField(default=timezone.now, null=True, blank=True)

    class Meta:
        verbose_name_plural = "Cart Order"


class CartOrderProducts(models.Model):
    order = models.ForeignKey(CartOrder, on_delete=models.CASCADE)
    invoice_no = models.CharField(max_length=200)
    product_status = models.CharField(max_length=200)
    item = models.CharField(max_length=200)
    image = models.CharField(max_length=200)
    qty = models.IntegerField(default=0)
    price = models.DecimalField(max_digits=12, decimal_places=2, default="0.00")
    total = models.DecimalField(max_digits=12, decimal_places=2, default="0.00")


    class Meta:
        verbose_name_plural = "Cart Order Items"


    def order_img(self):
        return mark_safe('<img src="/media/%s" width="50" height="50" />' % (self.image))


############################################## Product Revew, wishlists, Address ##################################
############################################## Product Revew, wishlists, Address ##################################
############################################## Product Revew, wishlists, Address ##################################
############################################## Product Revew, wishlists, Address ##################################


class ProductReview(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, related_name="reviews")
    review = models.TextField()
    rating = models.IntegerField(choices=RATING, default=None)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Product Reviews"

    def __str__(self):
        return self.product.title

    def get_rating(self):
        return self.rating



class wishlist_model(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "wishlists"

    def __str__(self):
        return self.product.title


class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    mobile = models.CharField(max_length=300, null=True)
    address = models.CharField(max_length=100, null=True)
    status = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "Address"


class Coupon(models.Model):
    code = models.CharField(max_length=1000)
    discount = models.IntegerField(default=1)
    active =models.BooleanField(default=True)

    def __str__(self):
        return(self.code)


class MpesaTransaction(models.Model):
    transaction_id = models.PositiveIntegerField(unique=True, blank=True, null=True)
    # user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    MerchantRequestID = models.CharField(max_length=100, unique=True)
    CheckoutRequestID = models.CharField(max_length=100, unique=True)
    ResultCode = models.IntegerField()
    ResultDesc = models.CharField(max_length=255)
    Amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    MpesaReceiptNumber = models.CharField(max_length=100, null=True, blank=True)
    TransactionDate = models.DateTimeField(null=True, blank=True)
    PhoneNumber = models.CharField(max_length=13,null=True)
    order_id = models.CharField(max_length=255, null=False, blank=False, default="not valid")
    is_finished = models.BooleanField(default=False)
    is_successful = models.BooleanField(default=False)
    
    
    def save(self, *args, **kwargs):
        if not self.transaction_id:
            last_transaction = MpesaTransaction.objects.order_by('transaction_id').last()
            if last_transaction and last_transaction.transaction_id is not None:
                self.transaction_id = last_transaction.transaction_id + 1
            else:
                self.transaction_id = 1
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Transaction {self.transaction_id} - {self.CheckoutRequestID} - {self.ResultDesc}"

class ProductComparison(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    products = models.ManyToManyField('Product', related_name='comparisons')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comparison by {self.user.username if self.user else 'Anonymous'}"
  
class DealOfTheDay(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='deal_of_the_day')
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField()
    
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Deals of the Day"
        ordering = ['-start_time']

    def __str__(self):
        return f"Deal of the Day for {self.product.title}"

    def is_current(self):
        """
        Check if the deal is active based on the current time.
        """
        now = timezone.now()
        return self.start_time <= now <= self.end_time and self.is_active

    def get_discounted_price(self):
        """
        Calculate the discounted price based on the deal percentage.
        """
        return self.product.price - (self.product.price * (self.discount_percentage / 100))