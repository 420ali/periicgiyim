from django.shortcuts import render, HttpResponse, redirect
from .models import Item, Sale
from .forms import ItemForm
from django.utils.timezone import now, timedelta
from django.utils import timezone
from django.db.models import Sum, F
from datetime import timedelta
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator


# Ana sayfa
@login_required
def home(request):
    return render(request, "home.html")

# Ürün listesi
@login_required
def urun_listesi(request):
    search_query = request.GET.get('search', '')  # Arama sorgusunu al
    
    if search_query:
        items = Item.objects.filter(
            barcode__icontains=search_query
        ) | Item.objects.filter(
            name__icontains=search_query
        )
    else:
        items = Item.objects.all()

    context = {"items": items}
    return render(request, "urun_listesi.html", context)

# Ürün ekleme
@login_required
def urun_ekle(request):
    form = ItemForm()
    if request.method == 'POST':
        form = ItemForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('urun_ekle')
    context = {'form': form}
    return render(request, "urun_ekle.html", context)

# Ürün güncelleme
@login_required
def updateItem(request, pk):
    item = Item.objects.get(id=pk)
    form = ItemForm(instance=item)
    if request.method == 'POST':
        form = ItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            return redirect('urun_listesi')
    context = {'form': form}
    return render(request, 'urun_ekle.html', context)

# Ürün satış miktarını güncelleme
@login_required
def update_quantity(item_id, quantity_sold):
    item = get_object_or_404(Item, id=item_id)
    if item.quantity is not None and item.quantity >= quantity_sold:
        item.quantity -= quantity_sold
        item.save()

# Kasa işlemleri (Satış ekranı)
@login_required
def kasa(request):
    items = Item.objects.all()
    sales = Sale.objects.all()  # Satışları burada alıyorsunuz

    if request.method == 'POST':
        barcodes = request.POST.getlist('barcodes[]')
        quantities = request.POST.getlist('quantities[]')  # Birden fazla miktar alıyoruz
        payment_methods = request.POST.getlist('payment_methods[]')  # Ödeme yöntemlerini alıyoruz

        for barcode, quantity_str, payment_method in zip(barcodes, quantities, payment_methods):
            try:
                quantity_sold = int(quantity_str)  # Her bir miktarı integer olarak dönüştürüyoruz
                item = Item.objects.get(barcode=barcode)
                
                if item.quantity is not None and item.quantity >= quantity_sold:
                    sale_price = item.sell_price
                    Sale.objects.create(item=item, quantity=quantity_sold, sale_price=sale_price, payment_method=payment_method)
                    item.update_quantity(quantity_sold)  # Ürün miktarını güncelliyoruz
                else:
                    # Hata mesajı veya işlem yapılmadan geçmek
                    pass
            except ValueError:
                pass
            except Item.DoesNotExist:
                pass

        return redirect('kasa')

    context = {
        "items": items,
        "sales": sales,  # Satışları bağlamda gönderiyoruz
    }
    return render(request, "kasa.html", context)



@login_required
def get_item(request, barcode):
    try:
        item = Item.objects.get(barcode=barcode)
        data = {
            'quantity': item.quantity,
            'sell_price': item.sell_price
        }
        return JsonResponse(data)
    except Item.DoesNotExist:
        return JsonResponse({'error': 'Ürün bulunamadı'}, status=404)


@login_required
def process_sale(request):
    if request.method == 'POST':
        barcodes = request.POST.getlist('barcodes[]')
        quantities = request.POST.getlist('quantities[]')
        payment_methods = request.POST.getlist('payment_methods[]')

        for barcode, quantity, payment_method in zip(barcodes, quantities, payment_methods):
            try:
                item = Item.objects.get(barcode=barcode)
                quantity = int(quantity)
                
                # Ödeme yöntemini uygun formata çevir
                
                
                if item.quantity >= quantity:
                    Sale.objects.create(item=item, quantity=quantity, sale_price=item.sell_price, payment_method=payment_method)
                    item.update_quantity(quantity)
                else:
                    # Hata mesajını oluştur
                    messages.error(request, f'{item.name} ürününün yeterli stoğu yok. Mevcut: {item.quantity}, Satılmak İstenen: {quantity}')
                    
            except Item.DoesNotExist:
                continue

    return redirect('kasa')


# Raporlama
@login_required
def rapor(request):
    today = now().date()
    one_month_ago = today - timedelta(days=30)
    three_months_ago = today - timedelta(days=90)
    six_months_ago = today - timedelta(days=180)

    sales_last_month = Sale.objects.filter(sale_date__gte=one_month_ago).order_by('-sale_date')
    sales_last_3_months = Sale.objects.filter(sale_date__gte=three_months_ago).order_by('-sale_date')
    sales_last_6_months = Sale.objects.filter(sale_date__gte=six_months_ago).order_by('-sale_date')

    def calculate_report(sales):
        total_sales = sum(sale.total_sale() for sale in sales)
        total_items_sold = sum(sale.quantity for sale in sales)
        net_profit = sum(sale.profit() for sale in sales)
        total_cash_sales = sales.filter(payment_method='cash').aggregate(total=Sum(F('quantity') * F('sale_price')))['total'] or 0
        total_credit_sales = sales.filter(payment_method='credit_card').aggregate(total=Sum(F('quantity') * F('sale_price')))['total'] or 0
        return total_sales, total_items_sold, net_profit, total_cash_sales, total_credit_sales

    # Raporlar için hesaplamalar
    total_sales, total_items_sold, net_profit, total_cash_sales, total_credit_sales = calculate_report(sales_last_month)
    total_sales_3_months, total_items_sold_3_months, net_profit_3_months, total_cash_sales_3_months, total_credit_sales_3_months = calculate_report(sales_last_3_months)
    total_sales_6_months, total_items_sold_6_months, net_profit_6_months, total_cash_sales_6_months, total_credit_sales_6_months = calculate_report(sales_last_6_months)

    #Pagination
    sales = Sale.objects.all().order_by('-sale_date')
    paginator = Paginator(sales_last_month, 15)  # Her sayfada 15 satış göster
    page_number = request.GET.get('page')  # Sayfa numarasını al
    page_obj = paginator.get_page(page_number)  # Sayfa nesnesini al


    context = {
        "total_sales": total_sales,
        "total_items_sold": total_items_sold,
        "net_profit": net_profit,
        "total_sales_3_months": total_sales_3_months,
        "total_items_sold_3_months": total_items_sold_3_months,
        "net_profit_3_months": net_profit_3_months,
        "total_sales_6_months": total_sales_6_months,
        "total_items_sold_6_months": total_items_sold_6_months,
        "net_profit_6_months": net_profit_6_months,
        "total_cash_sales": total_cash_sales,
        "total_credit_sales": total_credit_sales,
        "total_cash_sales_3_months": total_cash_sales_3_months,
        "total_credit_sales_3_months": total_credit_sales_3_months,
        "total_cash_sales_6_months": total_cash_sales_6_months,
        "total_credit_sales_6_months": total_credit_sales_6_months,
        "page_obj": page_obj,  # Sayfa nesnesini bağlamda gönder
        "sales": page_obj.object_list,
    }

    return render(request, "rapor.html", context)


@login_required
def deleteItem(request, pk):
    item = Item.objects.get(id=pk)
    if request.method == 'POST':
        item.delete()
        return redirect('urun_listesi')
    return render(request, 'delete.html', {'obj':item})