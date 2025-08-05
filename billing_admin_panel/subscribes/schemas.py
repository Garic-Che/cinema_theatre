from django import forms

class PaymentRequestForm(forms.Form):
    user_id = forms.CharField(required=True)
    subscription_id = forms.CharField(required=True)

class RefundRequestForm(forms.Form):
    user_id = forms.CharField(required=True)
    transaction_id = forms.CharField(required=True)
    amount = forms.FloatField(required=True)
    currency = forms.CharField(required=True, initial="RUB")