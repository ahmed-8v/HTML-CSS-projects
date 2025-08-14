from django.contrib import admin
from .models import Category, Ad, AdImage, Contact


class AdImageInline(admin.TabularInline):
    """Inline admin for ad images"""
    model = AdImage
    extra = 1
    max_num = 5


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin configuration for Category model"""
    list_display = ['name', 'created_at']
    search_fields = ['name']
    list_filter = ['created_at']


@admin.register(Ad)
class AdAdmin(admin.ModelAdmin):
    """Admin configuration for Ad model"""
    list_display = ['title', 'seller', 'category', 'price', 'condition', 'is_active', 'created_at']
    list_filter = ['category', 'condition', 'is_active', 'created_at']
    search_fields = ['title', 'description', 'seller__username']
    list_editable = ['is_active']
    inlines = [AdImageInline]
    readonly_fields = ['created_at', 'updated_at']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('seller', 'category')


@admin.register(AdImage)
class AdImageAdmin(admin.ModelAdmin):
    """Admin configuration for AdImage model"""
    list_display = ['ad', 'caption', 'uploaded_at']
    list_filter = ['uploaded_at']
    search_fields = ['ad__title', 'caption']


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    """Admin configuration for Contact model"""
    list_display = ['ad', 'sender_name', 'sender_email', 'created_at']
    list_filter = ['created_at']
    search_fields = ['sender_name', 'sender_email', 'ad__title']
    readonly_fields = ['created_at']