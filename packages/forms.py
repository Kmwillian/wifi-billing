from django import forms
from .models import Package


class PackageForm(forms.ModelForm):
    class Meta:
        model = Package
        fields = [
            'name', 'description', 'price',
            'duration', 'duration_unit',
            'data_limit_mb', 'upload_speed_kbps', 'download_speed_kbps',
            'max_devices', 'mikrotik_profile',
            'status', 'is_featured', 'sort_order'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
        help_texts = {
            'data_limit_mb': 'Leave blank for unlimited data',
            'upload_speed_kbps': 'Leave blank for unlimited speed',
            'download_speed_kbps': 'Leave blank for unlimited speed',
            'mikrotik_profile': 'Must match exactly the profile name on your router',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        input_class = (
            'w-full px-4 py-2 border border-gray-300 rounded-lg '
            'focus:outline-none focus:ring-2 focus:ring-blue-500 '
            'focus:border-transparent transition duration-200'
        )
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'w-4 h-4 text-blue-600 rounded'
            else:
                field.widget.attrs['class'] = input_class