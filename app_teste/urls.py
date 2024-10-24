from django.urls import path
from .views import (ola_mundo,
                    index,
                    cadastro_cliente,
                    cadastro_pedido,
                    cadastro_produto,
                    agenda, pesquisacliente,
                    listar_produtos)

urlpatterns = [
    path('ola-mundo/', ola_mundo, name='ola_mundo'),
    path('index/', index, name='index'),
    path('cadastro/', cadastro_cliente, name='cadastro'),
    path('cadastro-pedido/', cadastro_pedido, name='cadastro_pedido'),
    path('cadastro-produto/', cadastro_produto, name='cadastro_produto'),
    path('agenda/', agenda, name='agenda'),
    path('pesquisacliente/', pesquisacliente, name='pesquisacliente'),
    path('listar_produtos/', listar_produtos, name='listar_produtos'),
]