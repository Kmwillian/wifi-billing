from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views import View
from django.http import JsonResponse
from .models import Package
from .forms import PackageForm
from accounts.decorators import admin_required


@method_decorator(login_required, name='dispatch')
class PackageListView(View):
    template_name = 'packages/package_list.html'

    def get(self, request):
        packages = Package.objects.all().order_by('sort_order', 'price')
        active_count = packages.filter(status='active').count()
        inactive_count = packages.filter(status='inactive').count()
        context = {
            'packages': packages,
            'active_count': active_count,
            'inactive_count': inactive_count,
        }
        return render(request, self.template_name, context)


@method_decorator([login_required, admin_required], name='dispatch')
class PackageCreateView(View):
    template_name = 'packages/package_form.html'

    def get(self, request):
        form = PackageForm()
        return render(request, self.template_name, {'form': form, 'title': 'Add New Package'})

    def post(self, request):
        form = PackageForm(request.POST)
        if form.is_valid():
            package = form.save()
            messages.success(request, f'Package "{package.name}" created successfully.')
            return redirect('packages:list')
        return render(request, self.template_name, {'form': form, 'title': 'Add New Package'})


@method_decorator([login_required, admin_required], name='dispatch')
class PackageUpdateView(View):
    template_name = 'packages/package_form.html'

    def get(self, request, pk):
        package = get_object_or_404(Package, pk=pk)
        form = PackageForm(instance=package)
        return render(request, self.template_name, {
            'form': form,
            'title': f'Edit Package — {package.name}',
            'package': package
        })

    def post(self, request, pk):
        package = get_object_or_404(Package, pk=pk)
        form = PackageForm(request.POST, instance=package)
        if form.is_valid():
            form.save()
            messages.success(request, f'Package "{package.name}" updated successfully.')
            return redirect('packages:list')
        return render(request, self.template_name, {
            'form': form,
            'title': f'Edit Package — {package.name}',
            'package': package
        })


@login_required
@admin_required
def package_delete_view(request, pk):
    package = get_object_or_404(Package, pk=pk)
    name = package.name
    package.delete()
    messages.success(request, f'Package "{name}" deleted successfully.')
    return redirect('packages:list')


@login_required
@admin_required
def package_toggle_status(request, pk):
    package = get_object_or_404(Package, pk=pk)
    package.status = 'inactive' if package.status == 'active' else 'active'
    package.save()
    return JsonResponse({
        'status': package.status,
        'message': f'Package is now {package.status}'
    })


@login_required
def package_detail_api(request, pk):
    """Used by captive portal to fetch package details via AJAX"""
    package = get_object_or_404(Package, pk=pk, status='active')
    return JsonResponse({
        'id': package.pk,
        'name': package.name,
        'price': str(package.price),
        'duration_display': package.duration_display,
        'data_limit_display': package.data_limit_display,
        'speed_display': package.speed_display,
        'max_devices': package.max_devices,
    })