from django.db import models

class Produto_Model(models.Model):
    nome = models.CharField(max_length=80)
    modelo = models.CharField(max_length=80)
    quantidade = models.IntegerField()

    def __str__(self):
        return f'{self.nome} - {self.modelo}'

class Cliente_Model(models.Model):
    nome = models.CharField(max_length=80)
    telefone = models.CharField(max_length=80)
    cep = models.CharField(max_length=10)
    estado = models.CharField(max_length=20)
    cidade = models.CharField(max_length=60)
    endereco = models.CharField(max_length=100)
    numero = models.IntegerField()
    referencia = models.CharField(max_length=200)

    def __str__(self):
        return (f'{self.nome} - {self.telefone}')

class PedidoModel(models.Model):
    nome = models.CharField(max_length=80)
    telefone = models.CharField(max_length=80, blank=True, null=True,default='')
    endereco = models.CharField(max_length=100,blank=True, null=True,default='')
    local = models.CharField(max_length=200, blank=True, null=True,default='')
    itens_pedido = models.ManyToManyField('ItemPedido',blank=True, null=True)  # Use aspas para evitar referência circular
    data_de_locacao = models.CharField(max_length=10,null=True)
    observacao = models.CharField(max_length=400,null=True,blank=True,default='')
    def __str__(self):
        return self.nome

class ItemPedido(models.Model):
    produto = models.ForeignKey(Produto_Model, on_delete=models.CASCADE)
    quantidade_alugada = models.IntegerField()
    pedido = models.ForeignKey(PedidoModel, on_delete=models.CASCADE)  # Adiciona a chave estrangeira para Pedido_Model

    def __str__(self):
        return f"{self.produto.nome} - {self.quantidade_alugada}"