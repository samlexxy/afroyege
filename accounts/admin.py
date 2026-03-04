from django.contrib import admin
from .models import User, UserProfile
# Register your models here.


admin.site.register(User)
admin.site.register(UserProfile)

# from django.contrib import admin
# from django.contrib.auth import get_user_model
# from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

# from .models import UserProfile

# User = get_user_model()


# class UserProfileInline(admin.StackedInline):
#     model = UserProfile
#     can_delete = False
#     extra = 0

#     # If your profile uses AuditModel fields:
#     readonly_fields = (
#         "created_at",
#         "created_by",
#         "updated_at",
#         "updated_by",
#     )


# @admin.register(User)
# class UserAdmin(DjangoUserAdmin):
#     ordering = ("email",)
#     list_display = ("email", "uuid", "is_active", "is_staff")
#     search_fields = ("email", "uuid")
#     inlines = (UserProfileInline,)

#     fieldsets = (
#         (None, {"fields": ("email", "password", "uuid")}),
#         ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
#         ("Important dates", {"fields": ("last_login", "date_joined")}),
#     )
#     add_fieldsets = (
#         (None, {"classes": ("wide",), "fields": ("email", "password1", "password2")}),
#     )


# @admin.register(UserProfile)
# class UserProfileAdmin(admin.ModelAdmin):
#     list_display = ("user", "role", "phone_number", "phone_verified", "is_runner_verified", "is_suspended")
#     search_fields = ("user__email", "phone_number", "postcode")
#     list_select_related = ("user",)
#     readonly_fields = ("created_at", "created_by", "updated_at", "updated_by")