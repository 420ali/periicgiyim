from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("", views.home, name="Home"),
    path("urun-listesi/", views.urun_listesi, name="urun_listesi"),
    path("urun-ekle/", views.urun_ekle, name="urun_ekle"),
    path("urun-edit/<str:pk>/", views.updateItem, name="urun_edit"),
    path("kasa/", views.kasa, name="kasa"),
    path("rapor/", views.rapor, name="rapor"),
    path('get-item/<str:barcode>/', views.get_item, name='get_item'),
    path('process-sale/', views.process_sale, name='process_sale'),
    path('delete-item/<str:pk>/', views.deleteItem, name='delete_item'),
    # Login ve logout URL'leri
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('iade/', views.iade, name='iade'),
    path('degisim/', views.degisim, name='degisim')
]
