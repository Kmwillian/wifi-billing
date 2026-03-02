from celery import shared_task
from django.utils import timezone
from django.db import transaction
import logging

logger = logging.getLogger(__name__)


@shared_task(name='clients.expire_sessions')
def expire_sessions():
    """
    Runs every minute via Celery Beat.
    Finds all active sessions that have passed their expiry time,
    disconnects them from MikroTik, and marks them expired.
    """
    from .models import Session
    from .mikrotik import disconnect_active_session

    now = timezone.now()
    expired_sessions = Session.objects.filter(
        status='active',
        expires_at__lte=now
    ).select_related('client')

    count = 0
    for session in expired_sessions:
        try:
            with transaction.atomic():
                # Disconnect from MikroTik
                disconnect_active_session(session.client.mikrotik_username)
                # Mark session expired
                session.status = 'expired'
                session.ended_at = now
                session.save()
                # Update client status
                session.client.status = 'inactive'
                session.client.save()
                count += 1
                logger.info(f"Expired session for {session.client.full_name}")
        except Exception as e:
            logger.error(f"Error expiring session {session.id}: {e}")

    logger.info(f"Session expiry task complete — {count} sessions expired")
    return f"{count} sessions expired"


@shared_task(name='clients.sync_mikrotik_sessions')
def sync_mikrotik_sessions():
    """
    Syncs active sessions with MikroTik every 5 minutes.
    Updates IP addresses and data usage.
    """
    from .models import Session, Client
    from .mikrotik import get_active_sessions

    mikrotik_sessions = get_active_sessions()
    if not mikrotik_sessions:
        return "No MikroTik sessions found or connection failed"

    mikrotik_users = {s.get('user'): s for s in mikrotik_sessions}

    active_sessions = Session.objects.filter(
        status='active'
    ).select_related('client')

    updated = 0
    for session in active_sessions:
        username = session.client.mikrotik_username
        if username in mikrotik_users:
            mt_session = mikrotik_users[username]
            # Update bytes used
            bytes_in = int(mt_session.get('bytes-in', 0))
            bytes_out = int(mt_session.get('bytes-out', 0))
            session.download_bytes = bytes_in
            session.upload_bytes = bytes_out
            session.data_used_mb = (bytes_in + bytes_out) / (1024 * 1024)
            session.ip_address = mt_session.get('address', session.ip_address)
            session.save(update_fields=[
                'download_bytes', 'upload_bytes',
                'data_used_mb', 'ip_address'
            ])
            updated += 1

    return f"{updated} sessions synced with MikroTik"