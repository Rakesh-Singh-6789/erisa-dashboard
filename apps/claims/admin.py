from django.contrib import admin
from .models import Claim, ClaimDetail, ClaimFlag, ClaimNote, DataUpload


@admin.register(Claim)
class ClaimAdmin(admin.ModelAdmin):
    list_display = ('claim_id', 'patient_name', 'billed_amount', 'paid_amount', 'status', 'insurer_name', 'discharge_date')
    list_filter = ('status', 'insurer_name', 'discharge_date')
    search_fields = ('claim_id', 'patient_name', 'insurer_name')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'discharge_date'


@admin.register(ClaimDetail)
class ClaimDetailAdmin(admin.ModelAdmin):
    list_display = ('claim', 'denial_reason')
    search_fields = ('claim__claim_id', 'denial_reason', 'cpt_codes')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ClaimFlag)
class ClaimFlagAdmin(admin.ModelAdmin):
    list_display = ('claim', 'user', 'flag_type', 'created_at', 'is_active')
    list_filter = ('flag_type', 'is_active', 'created_at')
    search_fields = ('claim__claim_id', 'user__username', 'reason')
    readonly_fields = ('created_at',)


@admin.register(ClaimNote)
class ClaimNoteAdmin(admin.ModelAdmin):
    list_display = ('claim', 'user', 'created_at')
    search_fields = ('claim__claim_id', 'user__username', 'note')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(DataUpload)
class DataUploadAdmin(admin.ModelAdmin):
    list_display = ('upload_type', 'file_name', 'records_processed', 'upload_timestamp', 'user')
    list_filter = ('upload_type', 'upload_timestamp')
    readonly_fields = ('upload_timestamp',)