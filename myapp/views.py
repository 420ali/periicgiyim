from django.shortcuts import render, HttpResponse, redirect, get_object_or_404
from .models import Item, Sale
from .forms import ItemForm, UrunDegisimForm
from django.utils.timezone import now, timedelta
from django.utils import timezone
from django.db.models import Sum, F
from datetime import timedelta
from django.http import JsonResponse
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

    # Paginator ile sayfalara ayır
    paginator = Paginator(items, 15)  # Her sayfada 15 ürün göster
    page_number = request.GET.get('page')  # Sayfa numarasını al
    page_obj = paginator.get_page(page_number)  # İlgili sayfayı al

    context = {
        "items": page_obj,  # `items` yerine `page_obj` gönder
        "page_obj": page_obj,  # Sayfalama bilgileri için
    }
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
    sales = Sale.objects.all()

    if request.method == 'POST':
        barcodes = request.POST.getlist('barcodes[]')
        quantities = request.POST.getlist('quantities[]')
        payment_method = request.POST.get('payment_method')

        # request nesnesini geçerek process_sale'i çağır
        response = process_sale(request)

        # Hataları kontrol et
        if response.get('success'):
            messages.success(request, 'Satış işlemi başarılı.')
        else:
            errors = response.get('error', '').split('; ')
            for error in errors:
                messages.error(request, error)

        return redirect('kasa')

    context = {
        "items": items,
        "sales": sales,
    }
    return render(request, "kasa.html", context)



@login_required
def process_sale(request):
    if request.method == 'POST':
        barcodes = request.POST.getlist('barcodes[]')
        quantities = request.POST.getlist('quantities[]')
        payment_method = request.POST.get('payment_method')

        print("Received barcodes:", barcodes)  # Debugging: Gelen barkodlar
        print("Received quantities:", quantities)  # Debugging: Gelen miktarlar
        print("Payment method:", payment_method)  # Debugging: Ödeme yöntemi

        errors = []
        success = True

        for barcode, quantity_str in zip(barcodes, quantities):
            print(f'Processing barcode: {barcode} with quantity: {quantity_str}')  # Debugging: İşlemdeki barkod ve miktar
            try:
                item = Item.objects.get(barcode=barcode)
                quantity = int(quantity_str)

                # Stoğu kontrol et
                if quantity > item.quantity:
                    errors.append(f'{item.name} için yeterli stok yok. Mevcut stok: {item.quantity}.')
                    success = False
                else:
                    # Stok yeterliyse ürünü güncelle ve satışı gerçekleştir
                    print(f'Updating quantity for item: {item.name}, current quantity: {item.quantity}, sold quantity: {quantity}')  # Debugging: Stok güncelleme
                    item.update_quantity(quantity)  # Stoğu azalt
                    Sale.objects.create(item=item, quantity=quantity, sale_price=item.sell_price, payment_method=payment_method)
                    print(f'Sale recorded: {item.name}, quantity: {quantity}, sale price: {item.sell_price}')  # Debugging: Satış kaydı

            except Item.DoesNotExist:
                errors.append(f'{barcode} barkoduna sahip ürün bulunamadı.')
                success = False
                print(f'Error: Item not found for barcode: {barcode}')  # Debugging: Ürün bulunamadı hatası
            except ValueError:
                errors.append(f'{quantity_str} geçersiz bir sayı. Lütfen geçerli bir miktar girin.')
                success = False
                print(f'Error: Invalid quantity entered: {quantity_str}')  # Debugging: Geçersiz miktar hatası
            except Exception as e:
                errors.append(f'Hata: {str(e)}')
                success = False
                print(f'Error: {str(e)}')  # Debugging: Genel hata

        if success:
            return JsonResponse({'success': True, 'message': 'Satış başarıyla işlendi.'})
        else:
            return JsonResponse({'success': False, 'errors': errors})

    return JsonResponse({'success': False, 'error': 'Geçersiz istek.'})





@login_required
def get_item(request, barcode):
    if not barcode or not isinstance(barcode, str):
        return JsonResponse({'error': 'Geçersiz barkod.'}, status=400)

    try:
        item = Item.objects.get(barcode=barcode)
        if item.quantity <= 0:
            return JsonResponse({'error': 'Stokta bu ürün bulunmuyor.'}, status=200)  # 200 OK ile hata mesajı döndür

        return JsonResponse({
            'barcode': item.barcode,
            'name': item.name,
            'sell_price': item.sell_price,
            'quantity': item.quantity  # Stok bilgisi
        })
    except Item.DoesNotExist:
        return JsonResponse({'error': 'Ürün bulunamadı.'}, status=404)




# Raporlama
@login_required
def rapor(request):
    now = timezone.now()
    # 24 saat öncesini hesapla
    twenty_four_hours_ago = now - timedelta(hours=24)

    # Son 1 yıl, 6 ay, 3 ay ve 1 ay öncesini hesapla
    one_year_ago = now - timedelta(days=365)
    six_months_ago = now - timedelta(days=180)
    three_months_ago = now - timedelta(days=90)
    one_month_ago = now - timedelta(days=30)

    # Satışları filtrele
    sales_today = Sale.objects.filter(sale_date__gte=twenty_four_hours_ago).order_by('-sale_date')
    sales_last_year = Sale.objects.filter(sale_date__gte=one_year_ago).order_by('-sale_date')
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

    # Günlük rapor hesaplamaları
    total_sales_today, total_items_sold_today, net_profit_today, total_cash_sales_today, total_credit_sales_today = calculate_report(sales_today)

    # Diğer raporlar için hesaplamalar
    total_sales_year, total_items_sold_year, net_profit_year, total_cash_sales_year, total_credit_sales_year = calculate_report(sales_last_year)
    total_sales, total_items_sold, net_profit, total_cash_sales, total_credit_sales = calculate_report(sales_last_month)
    total_sales_3_months, total_items_sold_3_months, net_profit_3_months, total_cash_sales_3_months, total_credit_sales_3_months = calculate_report(sales_last_3_months)
    total_sales_6_months, total_items_sold_6_months, net_profit_6_months, total_cash_sales_6_months, total_credit_sales_6_months = calculate_report(sales_last_6_months)

    # Pagination
    paginator = Paginator(sales_last_month, 15)  # Her sayfada 15 satış göster
    page_number = request.GET.get('page')  # Sayfa numarasını al
    page_obj = paginator.get_page(page_number)  # Sayfa nesnesini al

    context = {
        "total_sales_today": total_sales_today,
        "total_items_sold_today": total_items_sold_today,
        "net_profit_today": net_profit_today,
        "total_cash_sales_today": total_cash_sales_today,
        "total_credit_sales_today": total_credit_sales_today,
        "total_sales_year": total_sales_year,
        "total_items_sold_year": total_items_sold_year,
        "net_profit_year": net_profit_year,
        "total_cash_sales_year": total_cash_sales_year,
        "total_credit_sales_year": total_credit_sales_year,
        "total_sales": total_sales,
        "total_items_sold": total_items_sold,
        "net_profit": net_profit,
        "total_cash_sales": total_cash_sales,
        "total_credit_sales": total_credit_sales,
        "total_sales_3_months": total_sales_3_months,
        "total_items_sold_3_months": total_items_sold_3_months,
        "net_profit_3_months": net_profit_3_months,
        "total_cash_sales_3_months": total_cash_sales_3_months,
        "total_credit_sales_3_months": total_credit_sales_3_months,
        "total_sales_6_months": total_sales_6_months,
        "total_items_sold_6_months": total_items_sold_6_months,
        "net_profit_6_months": net_profit_6_months,
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

@login_required
def degisim(request):
    if request.method == 'POST':
        form = UrunDegisimForm(request.POST)
        if form.is_valid():
            gelen_barkod = form.cleaned_data['gelen_urun']
            giden_barkod = form.cleaned_data['giden_urun']

            try:
                gelen_urun = Item.objects.get(barcode=gelen_barkod)
                giden_urun = Item.objects.get(barcode=giden_barkod)

                # Giden ürünün stok miktarı sıfır mı?
                if giden_urun.quantity > 0:
                    # Stok işlemleri
                    gelen_urun.quantity += 1
                    giden_urun.quantity -= 1

                    # Değişiklikleri kaydet
                    gelen_urun.save()
                    giden_urun.save()

                    messages.success(request, 'Değişim işlemi başarıyla gerçekleşti!')
                else:
                    messages.error(request, f"{giden_urun.name} ürününün stoğu sıfır olduğu için değişim yapılamıyor.")
                return redirect('degisim')

            except Item.DoesNotExist:
                messages.error(request, 'Girdiğiniz barkodlardan biri bulunamadı.')
        else:
            messages.error(request, 'Geçersiz form verisi.')

    else:
        form = UrunDegisimForm()

    return render(request, 'degisim.html', {'form': form})

@login_required
def iade(request):
    item = Item.objects.all()

    context = {"item": item}
    return render(request, 'iade.html', context)