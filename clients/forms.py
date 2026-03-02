from django import forms
from .models import Client


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = [
            'full_name', 'phone', 'email',
            'id_number', 'mac_address',
            'status', 'notes'
        ]
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        input_class = (
            'w-full px-4 py-2 border border-gray-300 rounded-lg '
            'focus:outline-none focus:ring-2 focus:ring-blue-500 '
            'focus:border-transparent transition duration-200'
        )
        for field in self.fields.values():
            field.widget.attrs['class'] = input_class


class PortalConnectForm(forms.Form):
    """Form shown on captive portal for client to enter phone and buy package"""
    phone = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': '07XXXXXXXX',
        })
    )
    package_id = forms.IntegerField(widget=forms.HiddenInput())