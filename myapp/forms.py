from django.forms import ModelForm
from .models import Item
from django import forms

class ItemForm(ModelForm):
  class Meta:
    model = Item
    fields = '__all__'

class UrunDegisimForm(forms.Form):
    gelen_urun = forms.CharField(label='Gelen Ürün Barkodu', max_length=100)
    giden_urun = forms.CharField(label='Giden Ürün Barkodu', max_length=100)