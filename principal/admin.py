from django.contrib import admin
from principal.models import Principal


@admin.register(Principal)
class PrincipalAdmin(admin.ModelAdmin):
    list_display = ('user', 'employee_id', 'designation', 'phone')
    search_fields = ('user__username', 'user__first_name', 'employee_id')