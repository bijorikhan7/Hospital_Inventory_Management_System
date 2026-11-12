from django.db import transaction
from rest_framework.exceptions import ValidationError

from assets.models import Asset, AssetHistory


ALLOWED_TRANSITIONS = {
    Asset.Status.AVAILABLE: {
        Asset.Status.ASSIGNED,
        Asset.Status.UNDER_REPAIR,
        Asset.Status.DAMAGED,
        Asset.Status.LOST,
        Asset.Status.DISPOSED,
        Asset.Status.REPLACED,
    },
    Asset.Status.ASSIGNED: {
        Asset.Status.AVAILABLE,
        Asset.Status.UNDER_REPAIR,
        Asset.Status.DAMAGED,
        Asset.Status.LOST,
        Asset.Status.REPLACED,
    },
    Asset.Status.UNDER_REPAIR: {
        Asset.Status.ASSIGNED,
        Asset.Status.AVAILABLE,
        Asset.Status.DAMAGED,
        Asset.Status.REPLACED,
    },
    Asset.Status.DAMAGED: {
        Asset.Status.UNDER_REPAIR,
        Asset.Status.REPLACED,
        Asset.Status.DISPOSED,
    },
    Asset.Status.LOST: {Asset.Status.DISPOSED},
    Asset.Status.REPLACED: {Asset.Status.DISPOSED},
    Asset.Status.DISPOSED: set(),
}

ACTION_FOR_STATUS = {
    Asset.Status.DAMAGED: AssetHistory.Action.DAMAGED,
    Asset.Status.LOST: AssetHistory.Action.LOST,
    Asset.Status.DISPOSED: AssetHistory.Action.DISPOSED,
    Asset.Status.REPLACED: AssetHistory.Action.REPLACED,
}


def log_history(asset, action, user, description="", old_value=None, new_value=None):
    AssetHistory.objects.create(
        asset=asset,
        action=action,
        performed_by=user if getattr(user, "is_authenticated", False) else None,
        description=description,
        old_value=old_value,
        new_value=new_value,
    )


def generate_asset_code(category) -> str:
    prefix = f"IT-{category.code.upper()}-"
    existing = (
        Asset.objects.filter(asset_code__startswith=prefix)
        .values_list("asset_code", flat=True)
    )
    max_n = 0
    for code in existing:
        suffix = code[len(prefix) :]
        if suffix.isdigit():
            max_n = max(max_n, int(suffix))
    return f"{prefix}{max_n + 1:04d}"


def assert_transition(asset: Asset, new_status: str):
    allowed = ALLOWED_TRANSITIONS.get(asset.status, set())
    if new_status == asset.status:
        return
    if new_status not in allowed:
        raise ValidationError(f"Cannot change asset status from {asset.status} to {new_status}.")


def apply_status(asset: Asset, new_status: str, user, description: str = ""):
    assert_transition(asset, new_status)
    old = asset.status
    if old == new_status:
        return asset
    asset.status = new_status
    if new_status != Asset.Status.ASSIGNED:
        if new_status in {
            Asset.Status.AVAILABLE,
            Asset.Status.DISPOSED,
            Asset.Status.LOST,
            Asset.Status.REPLACED,
            Asset.Status.DAMAGED,
        }:
            if new_status != Asset.Status.UNDER_REPAIR:
                pass
    asset.save()
    action = ACTION_FOR_STATUS.get(new_status, AssetHistory.Action.UPDATED)
    log_history(asset, action, user, description, old_value={"status": old}, new_value={"status": new_status})
    return asset
