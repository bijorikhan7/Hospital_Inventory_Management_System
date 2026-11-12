from django.contrib import admin

from .models import Asset, AssetAssignment, AssetCategory, AssetHistory, AssetReplacement, Purchase, Vendor, Warranty

admin.site.register(AssetCategory)
admin.site.register(Vendor)
admin.site.register(Asset)
admin.site.register(Purchase)
admin.site.register(Warranty)
admin.site.register(AssetAssignment)
admin.site.register(AssetReplacement)


@admin.register(AssetHistory)
class AssetHistoryAdmin(admin.ModelAdmin):
    list_display = ("asset", "action", "performed_by", "created_at")
    readonly_fields = ("asset", "action", "old_value", "new_value", "performed_by", "description", "created_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
