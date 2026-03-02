import logging
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)


def activate_session_after_payment(payment):
    """
    Called after successful M-Pesa payment.
    1. Creates a Session for the client
    2. Adds user to MikroTik hotspot
    3. Updates client status to active
    4. Links session to payment
    """
    from clients.models import Session
    from clients.mikrotik import add_hotspot_user, disconnect_active_session

    client = payment.client
    package = payment.package

    try:
        # Terminate any existing active session first
        existing_session = client.active_session
        if existing_session:
            disconnect_active_session(client.mikrotik_username)
            existing_session.terminate('new_payment')
            logger.info(f"Terminated existing session for {client.full_name}")

        # Calculate session expiry
        now = timezone.now()
        expires_at = now + timedelta(seconds=package.duration_in_seconds)

        # Create new session
        session = Session.objects.create(
            client=client,
            package=package,
            started_at=now,
            expires_at=expires_at,
            status='active',
        )

        # Add to MikroTik
        mikrotik_profile = package.mikrotik_profile or 'default'
        success, message = add_hotspot_user(
            username=client.mikrotik_username,
            password=client.mikrotik_password,
            profile=mikrotik_profile,
            comment=f"Payment: {payment.mpesa_receipt_number or payment.pk}",
        )

        if not success:
            logger.warning(
                f"MikroTik add failed for {client.mikrotik_username}: {message}. "
                f"Session created locally but user may not connect."
            )

        # Update client status
        client.status = 'active'
        client.save()

        # Link session to payment
        payment.session = session
        payment.status = 'completed'
        payment.completed_at = now
        payment.save()

        logger.info(
            f"Session activated for {client.full_name} | "
            f"Package: {package.name} | "
            f"Expires: {expires_at.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        return session

    except Exception as e:
        logger.error(f"Session activation error for payment {payment.pk}: {e}")
        raise