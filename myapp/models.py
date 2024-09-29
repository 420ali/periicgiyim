from django.db import models

class Item(models.Model):
    barcode = models.CharField(max_length=100, null=True, unique=True)
    name = models.CharField(max_length=100)
    size = models.CharField(max_length=10)
    quantity = models.IntegerField(null=True)
    buy_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    sell_price = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-updated', '-created']

    def __str__(self):
        return self.name
    
    def update_quantity(self, sold_quantity):
        if self.quantity >= sold_quantity:  # Satılan miktarın, mevcut miktardan fazla olmadığını kontrol edin
            self.quantity -= sold_quantity
            self.save()
            print(f"Updated quantity for {self.name}: {self.quantity}")
        else:
            print(f"Error: Satılmak istenen miktar mevcut stoktan fazla ({self.name})")



class Sale(models.Model):
    PAYMENT_METHODS = [
        ('cash', 'Nakit'),
        ('credit_card', 'Kredi Kartı'),
    ]

    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    sale_price = models.DecimalField(max_digits=10, decimal_places=2)
    sale_date = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='credit_card')

    def total_sale(self):
        return self.quantity * self.sale_price

    def profit(self):
        if self.item.buy_price:
            return self.total_sale() - (self.quantity * self.item.buy_price)
        return self.total_sale()

    def save(self, *args, **kwargs):
        # Sale modelinin save methodunda item.quantity güncellenmeyecek
        super().save(*args, **kwargs)
