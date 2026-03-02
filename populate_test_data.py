"""
Automated Test Data Generator for VilNet Hotspot System
Run: python manage.py shell < populate_test_data.py
Or: python populate_test_data.py
"""

import os
import django
import random
from datetime import timedelta
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hotspot_billing.settings')
django.setup()

from django.utils import timezone
from django.contrib.auth import get_user_model
from packages.models import Package
from clients.models import Client, Session
from payments.models import Payment, ManualActivation
from accounts.models import AuditLog

User = get_user_model()

print("=" * 60)
print("🚀 VilNet Test Data Generator")
print("=" * 60)


def create_admin_user():
    """Create test admin user if doesn't exist"""
    if not User.objects.filter(username='admin').exists():
        user = User.objects.create_superuser(
            username='admin',
            email='admin@vilnet.com',
            password='admin123',
            first_name='Admin',
            last_name='User',
            role='superadmin'
        )
        print("✅ Created admin user (username: admin, password: admin123)")
        return user
    else:
        print("ℹ️  Admin user already exists")
        return User.objects.get(username='admin')


def create_staff_users():
    """Create test staff users"""
    staff_data = [
        {'username': 'john_staff', 'first_name': 'John', 'last_name': 'Doe', 'role': 'staff', 'email': 'john@vilnet.com'},
        {'username': 'jane_admin', 'first_name': 'Jane', 'last_name': 'Smith', 'role': 'admin', 'email': 'jane@vilnet.com'},
    ]
    
    created = 0
    for data in staff_data:
        if not User.objects.filter(username=data['username']).exists():
            User.objects.create_user(
                username=data['username'],
                password='staff123',
                first_name=data['first_name'],
                last_name=data['last_name'],
                email=data['email'],
                role=data['role']
            )
            created += 1
    
    print(f"✅ Created {created} staff users (password: staff123)")


def create_packages():
    """Create test packages"""
    packages_data = [
        {
            'name': '1 Hour Streaming',
            'description': 'Perfect for quick browsing and social media',
            'price': Decimal('10.00'),
            'duration': 1,
            'duration_unit': 'hours',
            'data_limit_mb': None,
            'upload_speed_kbps': None,
            'download_speed_kbps': None,
            'max_devices': 1,
            'mikrotik_profile': '1hr-plan',
            'status': 'active',
            'is_featured': True,
            'sort_order': 1,
        },
        {
            'name': '6 Hours Gaming',
            'description': 'Great for gaming and video streaming',
            'price': Decimal('20.00'),
            'duration': 6,
            'duration_unit': 'hours',
            'data_limit_mb': None,
            'upload_speed_kbps': None,
            'download_speed_kbps': None,
            'max_devices': 1,
            'mikrotik_profile': '6hr-plan',
            'status': 'active',
            'is_featured': True,
            'sort_order': 2,
        },
        {
            'name': '1 Day Bundle',
            'description': 'Full day unlimited access',
            'price': Decimal('30.00'),
            'duration': 1,
            'duration_unit': 'days',
            'data_limit_mb': None,
            'upload_speed_kbps': None,
            'download_speed_kbps': None,
            'max_devices': 1,
            'mikrotik_profile': '1day-plan',
            'status': 'active',
            'is_featured': True,
            'sort_order': 3,
        },
        {
            'name': '2 Days Premium',
            'description': '48 hours of high-speed internet',
            'price': Decimal('50.00'),
            'duration': 2,
            'duration_unit': 'days',
            'data_limit_mb': None,
            'upload_speed_kbps': None,
            'download_speed_kbps': None,
            'max_devices': 2,
            'mikrotik_profile': '2day-plan',
            'status': 'active',
            'is_featured': False,
            'sort_order': 4,
        },
        {
            'name': '1 Week Ultimate',
            'description': 'One week of unlimited browsing',
            'price': Decimal('150.00'),
            'duration': 1,
            'duration_unit': 'weeks',
            'data_limit_mb': None,
            'upload_speed_kbps': None,
            'download_speed_kbps': None,
            'max_devices': 2,
            'mikrotik_profile': '1week-plan',
            'status': 'active',
            'is_featured': True,
            'sort_order': 5,
        },
        {
            'name': '1 Month Popular Deal',
            'description': 'Best value - full month access',
            'price': Decimal('600.00'),
            'duration': 1,
            'duration_unit': 'months',
            'data_limit_mb': None,
            'upload_speed_kbps': None,
            'download_speed_kbps': None,
            'max_devices': 3,
            'mikrotik_profile': '1month-plan',
            'status': 'active',
            'is_featured': True,
            'sort_order': 6,
        },
    ]
    
    Package.objects.all().delete()
    for data in packages_data:
        Package.objects.create(**data)
    
    print(f"✅ Created {len(packages_data)} packages")


def create_clients_and_sessions():
    """Create test clients with realistic sessions"""
    clients_data = [
        {'name': 'James Mwangi', 'phone': '254712345001'},
        {'name': 'Mary Wanjiku', 'phone': '254723456002'},
        {'name': 'Peter Omondi', 'phone': '254734567003'},
        {'name': 'Grace Achieng', 'phone': '254745678004'},
        {'name': 'David Kamau', 'phone': '254756789005'},
        {'name': 'Sarah Njeri', 'phone': '254767890006'},
        {'name': 'Michael Otieno', 'phone': '254778901007'},
        {'name': 'Lucy Wambui', 'phone': '254789012008'},
        {'name': 'John Kipchoge', 'phone': '254790123009'},
        {'name': 'Jane Chebet', 'phone': '254701234010'},
        {'name': 'Daniel Mutua', 'phone': '254712345011'},
        {'name': 'Susan Akinyi', 'phone': '254723456012'},
        {'name': 'Robert Karanja', 'phone': '254734567013'},
        {'name': 'Elizabeth Muthoni', 'phone': '254745678014'},
        {'name': 'George Odhiambo', 'phone': '254756789015'},
    ]
    
    Client.objects.all().delete()
    Session.objects.all().delete()
    
    packages = list(Package.objects.all())
    admin_user = User.objects.filter(role='superadmin').first()
    
    created_clients = 0
    active_sessions = 0
    expired_sessions = 0
    
    now = timezone.now()
    
    for data in clients_data:
        client = Client.objects.create(
            full_name=data['name'],
            phone=data['phone'],
            email=f"{data['phone']}@example.com",
            status='inactive',
        )
        created_clients += 1
        
        # Create 1-3 past sessions per client
        num_past_sessions = random.randint(1, 3)
        for i in range(num_past_sessions):
            package = random.choice(packages)
            days_ago = random.randint(7, 60)
            started = now - timedelta(days=days_ago, hours=random.randint(0, 23))
            ended = started + timedelta(seconds=package.duration_in_seconds)
            
            Session.objects.create(
                client=client,
                package=package,
                started_at=started,
                expires_at=ended,
                ended_at=ended,
                status='expired',
                data_used_mb=random.uniform(50, 2000),
            )
            expired_sessions += 1
    
    # Create 5 active sessions
    active_clients = random.sample(list(Client.objects.all()), 5)
    for client in active_clients:
        package = random.choice(packages)
        started = now - timedelta(hours=random.randint(0, 2))
        expires = started + timedelta(seconds=package.duration_in_seconds)
        
        Session.objects.create(
            client=client,
            package=package,
            started_at=started,
            expires_at=expires,
            status='active',
            data_used_mb=random.uniform(10, 500),
        )
        client.status = 'active'
        client.save()
        active_sessions += 1
    
    print(f"✅ Created {created_clients} clients")
    print(f"✅ Created {active_sessions} active sessions")
    print(f"✅ Created {expired_sessions} expired sessions")


def create_payments():
    """Create test payment records"""
    Payment.objects.all().delete()
    
    sessions = Session.objects.all()
    admin_user = User.objects.filter(role='superadmin').first()
    
    created = 0
    total_revenue = Decimal('0.00')
    
    for session in sessions:
        # Create payment for each session
        payment = Payment.objects.create(
            client=session.client,
            package=session.package,
            session=session,
            amount=session.package.price,
            phone=session.client.phone,
            payment_method=random.choice(['mpesa', 'cash']),
            status='completed',
            mpesa_receipt_number=f'TEST{random.randint(100000, 999999)}',
            initiated_at=session.started_at,
            completed_at=session.started_at + timedelta(seconds=30),
        )
        created += 1
        total_revenue += payment.amount
        
        # Create manual activation for cash payments
        if payment.payment_method == 'cash':
            ManualActivation.objects.create(
                client=session.client,
                package=session.package,
                activated_by=admin_user,
                payment=payment,
                notes='Test cash payment',
            )
    
    print(f"✅ Created {created} payment records")
    print(f"💰 Total revenue: KES {total_revenue:,.2f}")


def create_audit_logs():
    """Create sample audit logs"""
    AuditLog.objects.all().delete()
    
    admin_user = User.objects.filter(role='superadmin').first()
    staff_user = User.objects.filter(role='staff').first()
    
    actions = [
        ('login', 'System', 'User logged in'),
        ('create', 'Package: 1 Hour Streaming', 'Created new package'),
        ('activate', 'Session #123', 'Activated client session'),
        ('update', 'Client: James Mwangi', 'Updated client details'),
        ('logout', 'System', 'User logged out'),
    ]
    
    for i in range(20):
        user = random.choice([admin_user, staff_user])
        action_data = random.choice(actions)
        timestamp = timezone.now() - timedelta(hours=random.randint(1, 72))
        
        AuditLog.objects.create(
            user=user,
            action=action_data[0],
            target=action_data[1],
            detail=action_data[2],
            ip_address=f'192.168.1.{random.randint(1, 254)}',
            timestamp=timestamp,
        )
    
    print(f"✅ Created 20 audit log entries")


def print_summary():
    """Print summary of created data"""
    print("\n" + "=" * 60)
    print("📊 DATABASE SUMMARY")
    print("=" * 60)
    print(f"👥 Users: {User.objects.count()}")
    print(f"📦 Packages: {Package.objects.count()}")
    print(f"🧑‍💼 Clients: {Client.objects.count()}")
    print(f"🔗 Sessions (Active): {Session.objects.filter(status='active').count()}")
    print(f"🔗 Sessions (Total): {Session.objects.count()}")
    print(f"💳 Payments: {Payment.objects.count()}")
    print(f"💰 Total Revenue: KES {Payment.objects.filter(status='completed').aggregate(total=django.db.models.Sum('amount'))['total'] or 0:,.2f}")
    print(f"📝 Audit Logs: {AuditLog.objects.count()}")
    print("=" * 60)
    print("\n✨ Test data created successfully!")
    print("\n🔐 LOGIN CREDENTIALS:")
    print("   Username: admin")
    print("   Password: admin123")
    print("\n🌐 ACCESS URLS:")
    print("   Dashboard: http://127.0.0.1:8000/dashboard/")
    print("   Portal:    http://127.0.0.1:8000/")
    print("   Admin:     http://127.0.0.1:8000/admin/")
    print("=" * 60)


if __name__ == '__main__':
    try:
        print("\n🔄 Creating test data...\n")
        
        admin_user = create_admin_user()
        create_staff_users()
        create_packages()
        create_clients_and_sessions()
        create_payments()
        create_audit_logs()
        
        print_summary()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()