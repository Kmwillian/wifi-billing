from django import forms
from clients.models import Client
from packages.models import Package


class ManualActivationForm(forms.Form):
    """
    Used by staff to manually activate a session for cash payments
    """
    client_phone = forms.CharField(
        max_length=15,
        label='Client Phone Number',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': '07XXXXXXXX',
        })
    )
    package = forms.ModelChoiceField(
        queryset=Package.objects.filter(status='active'),
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
        })
    )
    amount_paid = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
        })
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'rows': 2,
            'placeholder': 'Optional notes e.g. cash received at counter',
        })
    )

    def clean_client_phone(self):
        phone = self.cleaned_data['client_phone'].strip()
        if phone.startswith('0'):
            phone = '254' + phone[1:]
        elif phone.startswith('+'):
            phone = phone[1:]
        return phone