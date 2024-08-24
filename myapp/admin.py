from django.contrib import admin
from .models import Item, Sale

class SaleAdmin(admin.ModelAdmin):
    list_display = ('item', 'quantity', 'sale_price', 'sale_date', 'total_sale', 'profit')
    list_filter = ('sale_date',)
    search_fields = ('item__barcode', 'item__name',)

admin.site.register(Item)
admin.site.register(Sale, SaleAdmin)
