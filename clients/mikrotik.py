import librouteros
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def get_mikrotik_connection():
    """Establish connection to MikroTik router"""
    try:
        api = librouteros.connect(
            host=settings.MIKROTIK_HOST,
            username=settings.MIKROTIK_USER,
            password=settings.MIKROTIK_PASSWORD,
            port=settings.MIKROTIK_PORT,
        )
        return api
    except Exception as e:
        logger.error(f"MikroTik connection failed: {e}")
        return None


def add_hotspot_user(username, password, profile='default', comment=''):
    """Add a user to MikroTik hotspot"""
    api = get_mikrotik_connection()
    if not api:
        return False, "Could not connect to router"
    try:
        api('/ip/hotspot/user/add', **{
            'name': username,
            'password': password,
            'profile': profile,
            'comment': comment,
        })
        api.close()
        logger.info(f"MikroTik: Added hotspot user {username}")
        return True, "User added successfully"
    except librouteros.exceptions.TrapError as e:
        logger.error(f"MikroTik trap error adding user {username}: {e}")
        return False, str(e)
    except Exception as e:
        logger.error(f"MikroTik error adding user {username}: {e}")
        return False, str(e)


def remove_hotspot_user(username):
    """Remove a user from MikroTik hotspot"""
    api = get_mikrotik_connection()
    if not api:
        return False, "Could not connect to router"
    try:
        users = list(api('/ip/hotspot/user/print', **{'?name': username}))
        if users:
            api('/ip/hotspot/user/remove', **{'.id': users[0]['.id']})
        api.close()
        logger.info(f"MikroTik: Removed hotspot user {username}")
        return True, "User removed successfully"
    except Exception as e:
        logger.error(f"MikroTik error removing user {username}: {e}")
        return False, str(e)


def disconnect_active_session(username):
    """Disconnect an active hotspot session"""
    api = get_mikrotik_connection()
    if not api:
        return False, "Could not connect to router"
    try:
        sessions = list(api('/ip/hotspot/active/print', **{'?user': username}))
        for session in sessions:
            api('/ip/hotspot/active/remove', **{'.id': session['.id']})
        api.close()
        logger.info(f"MikroTik: Disconnected session for {username}")
        return True, "Session disconnected"
    except Exception as e:
        logger.error(f"MikroTik error disconnecting {username}: {e}")
        return False, str(e)


def get_active_sessions():
    """Fetch all active hotspot sessions from MikroTik"""
    api = get_mikrotik_connection()
    if not api:
        return []
    try:
        sessions = list(api('/ip/hotspot/active/print'))
        api.close()
        return sessions
    except Exception as e:
        logger.error(f"MikroTik error fetching sessions: {e}")
        return []


def get_router_stats():
    """Fetch basic router resource stats"""
    api = get_mikrotik_connection()
    if not api:
        return None
    try:
        resources = list(api('/system/resource/print'))
        api.close()
        return resources[0] if resources else None
    except Exception as e:
        logger.error(f"MikroTik error fetching stats: {e}")
        return None


def update_hotspot_user_profile(username, new_profile):
    """Update user profile (used when upgrading package)"""
    api = get_mikrotik_connection()
    if not api:
        return False, "Could not connect to router"
    try:
        users = list(api('/ip/hotspot/user/print', **{'?name': username}))
        if users:
            api('/ip/hotspot/user/set', **{
                '.id': users[0]['.id'],
                'profile': new_profile,
            })
        api.close()
        return True, "Profile updated"
    except Exception as e:
        logger.error(f"MikroTik error updating profile for {username}: {e}")
        return False, str(e)