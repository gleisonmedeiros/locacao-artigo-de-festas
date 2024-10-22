from django.contrib import admin
from .models import Cliente_Model, Produto_Model, PedidoModel,ItemPedido

# Register your models here.
@admin.register(Cliente_Model)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ['nome', 'telefone', 'cep', 'estado', 'cidade', 'endereco', 'numero', 'referencia']

@admin.register(Produto_Model)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'modelo', 'quantidade']


class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido


@admin.register(PedidoModel)
class PedidoAdmin(admin.ModelAdmin):
    #list_display = ('cliente',)
    inlines = [ItemPedidoInline]

@admin.register(ItemPedido)
class ItemPedidoAdmin(admin.ModelAdmin):
    list_display = ('produto', 'quantidade_alugada')