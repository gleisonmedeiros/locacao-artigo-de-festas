from django.db import models

class Produto_Model(models.Model):
    nome = models.CharField(max_length=80)
    modelo = models.CharField(max_length=80, blank=True, null=True)
    quantidade = models.IntegerField()

    def __str__(self):
        return f'{self.nome} - {self.modelo}'

class PedidoModel(models.Model):
    nome = models.CharField(max_length=80)
    telefone = models.CharField(max_length=20, blank=True, null=True, default='')
    endereco = models.CharField(max_length=200, blank=True, null=True, default='')
    local = models.CharField(max_length=200, blank=True, null=True, default='')
    data_de_locacao = models.DateField(null=True, blank=True)
    observacao = models.TextField(blank=True, null=True, default='')

    def __str__(self):
        return f'Pedido de {self.nome}'

class ItemPedido(models.Model):
    pedido = models.ForeignKey(PedidoModel, on_delete=models.CASCADE, related_name='itens')
    produto = models.ForeignKey(Produto_Model, on_delete=models.CASCADE)
    quantidade_alugada = models.PositiveIntegerField()

    def __str__(self):
        return f'{self.quantidade_alugada}x {self.produto.nome} (Pedido: {self.pedido.id})'
