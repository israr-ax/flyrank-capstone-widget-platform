from rest_framework.exceptions import PermissionDenied
from .models import TenantMembership


def get_tenant_for_user(user):
    """Every authenticated request needs to resolve to exactly one tenant.
    Keeping this in one place means the tenant-scoping rule can never be
    forgotten or reimplemented slightly differently in a new view."""
    membership = TenantMembership.objects.filter(user=user).select_related('tenant').first()
    if membership is None:
        raise PermissionDenied('User is not a member of any tenant.')
    return membership.tenant