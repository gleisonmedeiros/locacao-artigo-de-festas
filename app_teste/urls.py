from django.urls import path
from .views import (ola_mundo,
                    index,
                    cadastro_cliente,
                    cadastro_pedido,
                    cadastro_produto,
                    agenda, backup_view,
                    listar_produtos,
                    excluir_produto)
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('ola-mundo/', ola_mundo, name='ola_mundo'),
    path('index/', index, name='index'),
    path('cadastro/', cadastro_cliente, name='cadastro'),
    path('cadastro-pedido/', cadastro_pedido, name='cadastro_pedido'),
    path('cadastro-produto/', cadastro_produto, name='cadastro_produto'),  # Rota para criar um novo produto
    path('cadastro-produto/<int:produto_id>/', cadastro_produto, name='editar_produto'),  # Rota para editar
    path('excluir-produto/<int:produto_id>/', excluir_produto, name='excluir_produto'),
    path('agenda/', agenda, name='agenda'),
    path('backup_view/', backup_view, name='backup_view'),
    path('listar_produtos/', listar_produtos, name='listar_produtos'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)