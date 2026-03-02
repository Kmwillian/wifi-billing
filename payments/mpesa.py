import requests, base64, logging
from datetime import datetime
from django.conf import settings

logger = logging.getLogger(__name__)

def mpesa_request(endpoint_url, payload=None):
    """Internal helper to handle Auth, Password, and Requests in one place."""
    try:
        # 1. Get Access Token
        auth = base64.b64encode(f"{settings.MPESA_CONSUMER_KEY}:{settings.MPESA_CONSUMER_SECRET}".encode()).decode()
        token_res = requests.get(settings.MPESA_AUTH_URL, headers={'Authorization': f'Basic {auth}'}, timeout=30)
        token_res.raise_for_status()
        token = token_res.json()['access_token']

        # 2. Setup Security & Payload
        stamp = datetime.now().strftime('%Y%m%d%H%M%S')
        pwd = base64.b64encode(f"{settings.MPESA_SHORTCODE}{settings.MPESA_PASSKEY}{stamp}".encode()).decode()
        
        if payload:
            payload.update({'BusinessShortCode': settings.MPESA_SHORTCODE, 'Password': pwd, 'Timestamp': stamp})
            # Add PartyB for STK push specifically
            if 'PhoneNumber' in payload: payload['PartyB'] = settings.MPESA_SHORTCODE

        # 3. Execute
        res = requests.post(endpoint_url, json=payload, headers={'Authorization': f'Bearer {token}'}, timeout=30)
        res.raise_for_status()
        return True, res.json()
    except Exception as e:
        logger.error(f"M-Pesa Error: {e}")
        return False, {'error': str(e)}

def initiate_stk_push(phone, amount, account_reference, description, payment_id):
    payload = {
        'TransactionType': 'CustomerPayBillOnline',
        'Amount': amount,
        'PartyA': phone,
        'PhoneNumber': phone,
        'CallBackURL': settings.MPESA_CALLBACK_URL,
        'AccountReference': account_reference,
        'TransactionDesc': description,
    }
    success, data = mpesa_request(settings.MPESA_STK_PUSH_URL, payload)
    return (success and data.get('ResponseCode') == '0'), data

def query_stk_status(checkout_request_id):
    url = f"https://{'api' if settings.MPESA_ENVIRONMENT == 'production' else 'sandbox'}.safaricom.co.ke/mpesa/stkpushquery/v1/query"
    return mpesa_request(url, {'CheckoutRequestID': checkout_request_id})