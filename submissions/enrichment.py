import logging
import requests

logger = logging.getLogger(__name__)
PROVIDER_TIMEOUT = 3  # seconds — a slow geo API must never stall the submission response


def _try_ip_api(ip):
    resp = requests.get(f'http://ip-api.com/json/{ip}', timeout=PROVIDER_TIMEOUT)
    resp.raise_for_status()
    body = resp.json()
    if body.get('status') != 'success':
        raise ValueError(body.get('message', 'ip-api failed'))
    return {'country': body.get('country', ''), 'city': body.get('city', ''), 'provider': 'ip-api'}


def _try_ipapi_co(ip):
    resp = requests.get(f'https://ipapi.co/{ip}/json/', timeout=PROVIDER_TIMEOUT)
    resp.raise_for_status()
    body = resp.json()
    if body.get('error'):
        raise ValueError(body.get('reason', 'ipapi.co failed'))
    return {'country': body.get('country_name', ''), 'city': body.get('city', ''), 'provider': 'ipapi.co'}



PROVIDERS = [_try_ip_api, _try_ipapi_co]


def enrich_ip(ip_address):
    """Try providers in order; return empty geo (never raise) if all fail — enrichment degrades, never breaks the submission."""
    if not ip_address:
        return {'country': '', 'city': '', 'provider': ''}

    for provider_fn in PROVIDERS:
        try:
            return provider_fn(ip_address)
        except Exception as exc:
            logger.warning('Geo provider %s failed for %s: %s', provider_fn.__name__, ip_address, exc)

    return {'country': '', 'city': '', 'provider': ''}



