from django.contrib import admin
from .models import Produto_Model, PedidoModel, ItemPedido

# Register your models here.
@admin.register(Produto_Model)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'modelo', 'quantidade']

class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 1

@admin.register(PedidoModel)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'telefone', 'endereco','local','data_de_locacao']
    inlines = [ItemPedidoInline]

@admin.register(ItemPedido)
class ItemPedidoAdmin(admin.ModelAdmin):
    list_display = ['produto', 'quantidade_alugada', 'pedido']