from django import forms
from stripe import Review 
from core.models import ProductReview


class ProductReviewForm(forms.ModelForm):
    review = forms.CharField(widget=forms.Textarea(attrs={'placeholder': "Write review"}))

    class Meta:
        model = ProductReview
        fields = ['review', 'rating']
        
class MpesaPaymentForm(forms.Form):
    phone_number = forms.CharField(
        max_length=13, 
        label='Phone Number',
        widget=forms.HiddenInput()
    )
    
    amount = forms.DecimalField(
        max_digits=10,
        label='Amount',
        widget=forms.HiddenInput() 
    )
    order_id = forms.IntegerField(
        label='Order ID',
        widget=forms.HiddenInput() 
    )
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        return int(amount)

        