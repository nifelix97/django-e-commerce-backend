from django.contrib import admin
from .models import CustomUser, Product, Order, Comment

# Register your models here.
admin.site.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    search_fields = ['username', 'email', 'id'],
admin.site.register(Product)
admin.site.register(Order)
admin.site.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    search_fields = ['product', 'user', 'text', 'is_new'],
    list_display = ['product', 'user', 'text', 'is_new'],