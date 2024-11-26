from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from .forms import ProdutoForm, ClienteForm, PedidoModelForm, DateRangeForm
from .models import Produto_Model
from .models import PedidoModel, ItemPedido
from collections import defaultdict
from datetime import datetime
import locale
from unidecode import unidecode
from django.urls import reverse
from collections import defaultdict
from django.contrib import messages
import json

locale.setlocale(locale.LC_TIME, 'pt_BR.utf-8')

lista2 = []
nome_antigo = ""
data_antigo = ""

def listar_produtos(request):
    query = request.GET.get('search')
    if query:
        produtos = Produto_Model.objects.filter(nome__icontains=query)
    else:
        produtos = Produto_Model.objects.all()
    return render(request, 'pesquisa_produto.html', {'produtos': produtos})


def ola_mundo(request):
    return HttpResponse("Ola mundo!")

def index(request):
    return render(request, 'index.html')

def cadastro_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            form = ClienteForm()
            dicionario = {'form': form, 'sucesso': 1}
            return render(request, 'cadastro_cliente.html', dicionario)
        else:
            dicionario = {'form': form, 'sucesso': 0}
            return render(request, 'cadastro_cliente.html', dicionario)
    else:
        form = ClienteForm()
    return render(request, 'cadastro_cliente.html', {'form': form})


def formata_data(data):
    nova_data = datetime.strptime(data.split(' - ')[0], "%d/%m/%Y").date()

    return nova_data

def agenda(request):
    form_date = DateRangeForm()

    if request.method == 'GET':


        produtos_por_cliente = defaultdict(list)

        # Consulta para obter os itens dos pedidos com informações relacionadas
        pedidos_itens = ItemPedido.objects.select_related('produto', 'pedido').all()

        # Preencher o dicionário com os produtos agrupados por cliente
        for pedido_item in pedidos_itens:
            produto_nome = pedido_item.produto
            quantidade_alugada = pedido_item.quantidade_alugada
            #cliente_nome = pedido_item.pedido.cliente
            cliente_nome = (pedido_item.pedido.nome)

            data = pedido_item.pedido.data_de_locacao
            data_formatada = datetime.strptime(data, "%Y-%m-%d")
            # Obtenha o nome do dia da semana
            #print((data_formatada.strftime("%A")))
            dia_da_semana = unidecode((data_formatada.strftime("%A").capitalize()))
            if (dia_da_semana == 'Sa!bado'):
                dia_da_semana = 'Sábado'
            elif (dia_da_semana == 'TeraSSa-feira'):
                dia_da_semana = 'Terça-feira'

            ano, mes, dia = data.split('-')
            data_locacao =f'{dia}/{mes}/{ano} - {dia_da_semana}'
            local=(pedido_item.pedido.local)
            observacao = (pedido_item.pedido.observacao)
            telefone = (pedido_item.pedido.telefone)
            endereco = (pedido_item.pedido.endereco)

            chave = (cliente_nome, data_locacao,local,observacao,telefone,endereco)

            # Adicionar informações ao dicionário
            produtos_por_cliente[chave].append({
                'produto_nome': produto_nome,
                'quantidade_alugada': quantidade_alugada,
            })

        dicionario_novo = dict(produtos_por_cliente)

        result = []
        for chave, items in dicionario_novo.items():
            cliente_nome, data_locacao,local,observacao,telefone,endereco = chave  # Desempacotando a tupla
            result.append((cliente_nome, data_locacao,local,observacao,
                           [[item['produto_nome'], item['quantidade_alugada']] for item in items],telefone,endereco))

        # Exibindo a lista de resultados
        #print(result)

        # Criando a lista de dados para renderizar no template
        lista_dados = [(nome,data,local,observacao, itens,telefone,endereco) for nome, data,local,observacao, itens,telefone,endereco in result]
        #print(lista_dados)
        paramentro = False
        if request.GET.get('datainicio'):
            data_inicio = (request.GET.get('datainicio'))
            data_fim = (request.GET.get('datafim'))
            #print("ui")

            data_inicio_formatada = datetime.strptime(data_inicio, "%Y-%m-%d").date()
            data_fim_formatada = datetime.strptime(data_fim, "%Y-%m-%d").date()
            paramentro = True

        # Lista de dados filtrados com base na data alvo
            lista_filtrada = [(nome, data, local, observacao, itens, telefone, endereco) for nome, data, local, observacao, itens, telefone,endereco in lista_dados
                          if (formata_data(data) >= data_inicio_formatada) and ((formata_data(data) <= data_fim_formatada))]

        if(paramentro == False):
            return render(request, 'agenda.html', {'lista_dados': lista_dados, 'form':form_date})
        else:
            somatorio_produtos = defaultdict(int)
            for nome, data, local, observacao, itens, telefone, endereco in lista_filtrada:
                for item in itens:
                    # item é uma lista [nome_do_produto, quantidade]
                    produto_nome = item[0]  # Acessando o nome do produto
                    quantidade_alugada = item[1]  # Acessando a quantidade
                    somatorio_produtos[produto_nome] += quantidade_alugada

            novo_resultado = []

            for produto, quantidade in somatorio_produtos.items():
                print(f"Nome: {produto.nome}")
                print(f"Modelo: {produto.modelo}")
                print(f"Quantidade: {quantidade}")
                qtd_produto = Produto_Model.objects.get(nome=produto.nome, modelo=produto.modelo)
                print(qtd_produto.quantidade)
                novo_resultado.append([produto.nome,produto.modelo,quantidade,qtd_produto.quantidade-quantidade])

            for item in novo_resultado:
                print(item)

            return render(request, 'agenda.html', {'lista_dados': lista_filtrada, 'form': form_date,'novo_resultado': novo_resultado})



    elif request.method == 'POST':

        form_date = DateRangeForm(request.POST)

        if form_date.is_valid() and ('pesquisar' in request.POST):
            data_inicio = form_date.cleaned_data['data_inicio'].strftime('%Y-%m-%d')
            data_fim = form_date.cleaned_data['data_fim'].strftime('%Y-%m-%d')
            url_agenda = reverse('agenda') + '?datainicio=' + data_inicio + '&datafim=' + data_fim
            return redirect(url_agenda)

        elif 'editar_itens' in request.POST:
            #print("uiii")
            nome_cliente = (request.POST['nome'].split(' - ')[0])
            data = (request.POST['data'].split(' ')[0])
            data_datetime = datetime.strptime(data, "%d/%m/%Y")
            data_formatada = data_datetime.strftime("%Y-%m-%d")
            #print(nome_cliente)
            #print(data)
            pedido = PedidoModel.objects.get(nome=nome_cliente, data_de_locacao=data_formatada)

            # Preenche o formulário com os dados do pedido
            form = PedidoModelForm(instance=pedido)

            pedidos_itens = ItemPedido.objects.select_related('produto', 'pedido').all()


            itens = []
            # Preencher o dicionário com os produtos agrupados por cliente
            for pedido_item in pedidos_itens:
                print(pedido_item.pedido.data_de_locacao)
                print(data)
                if (pedido_item.pedido.nome == nome_cliente) and (pedido_item.pedido.data_de_locacao == data_formatada):
                    produto = (pedido_item.produto)
                    quantidade = (pedido_item.quantidade_alugada)
                    itens.append(f'{produto} - {quantidade}')

            #for item in itens:
                #print(item)

            itens_serializado = json.dumps(itens)


            # Passa os dados para o template
            #return render(request, 'cadastro_pedido.html',{'form': form, 'lista_itens': lista_itens, 'resultado': resultado})
            #return render(request, 'cadastro_pedido.html',{'form': form,'lista_itens':itens})
            return redirect(f'/cadastro-pedido/?nome={nome_cliente}&data={data_formatada}&itens={itens_serializado}')

        elif 'delete_itens' in request.POST:
            nome_cliente = (request.POST['nome'].split(' - ')[0])
            data = (request.POST['data'].split(' ')[0])
            data_datetime = datetime.strptime(data, "%d/%m/%Y")
            data_formatada = data_datetime.strftime("%Y-%m-%d")
            #print(nome_cliente)
            #print(data)
            #cliente = Cliente_Model.objects.get(nome=nome_cliente)  # Obtenha o objeto do cliente pelo nome
            pedido = PedidoModel.objects.get(nome=nome_cliente,data_de_locacao=data_formatada)  # Consulte o pedido usando o objeto do cliente
            pedido.delete()
            return redirect('agenda')
        else:
            #print('erro no POST')
            return redirect('agenda')


def excluir_produto(request, produto_id):
    produto = get_object_or_404(Produto_Model, id=produto_id)

    # Verifica se o produto está associado a algum pedido
    if ItemPedido.objects.filter(produto=produto).exists():
        #messages.error(request, 'Não é possível excluir este produto porque ele está associado a um pedido.')
        messages = 'Não é possível excluir este produto porque ele está associado a um pedido.'
        #return redirect('listar_produtos')  # Redireciona para a lista de produtos após a verificação
        return render(request, 'pesquisa_produto.html', {'messages':messages})

    # A exclusão acontece quando a requisição é POST
    if request.method == 'POST':
        produto.delete()
        #messages.success(request, 'Produto excluído com sucesso!')
        messages = 'Produto excluído com sucesso!'
        return render(request, 'pesquisa_produto.html', {'messages':messages})

    # Retorna um redirecionamento se não for um POST
    return redirect('listar_produtos')

def cadastro_produto(request, produto_id=None):
    produto = None  # Inicialize a variável

    if produto_id:
        produto = get_object_or_404(Produto_Model, id=produto_id)
        form = ProdutoForm(request.POST or None, instance=produto)
    else:
        form = ProdutoForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            form = ProdutoForm()  # Reinicia o formulário
            dicionario = {'form': form, 'sucesso': 1}
            return render(request, 'cadastro_produto.html', dicionario)
        else:
            dicionario = {'form': form, 'sucesso': 0}
            return render(request, 'cadastro_produto.html', dicionario)

    # Atribua o produto ao formulário somente se ele existir
    if produto:
        form = ProdutoForm(instance=produto)

    return render(request, 'cadastro_produto.html', {'form': form})

def salva_pedido():
    global lista2

    #cliente = Cliente_Model.objects.get(nome=lista2[0][0])
    pedido = PedidoModel(nome=lista2[0][0], data_de_locacao=lista2[0][4],local=lista2[0][5],observacao=lista2[0][6],telefone=lista2[0][7],endereco=lista2[0][8])

    pedido.save()
    # Criar uma instância do cliente (substitua 'nome_do_cliente' pelo nome real)
    for lista in lista2:

        # Adicionar itens ao pedido
        produto1 = Produto_Model.objects.get(nome=lista[1],modelo=lista[2])
        item1 = ItemPedido(produto=produto1, quantidade_alugada=lista[3], pedido=pedido)
        item1.save()

        #print(item1)


def cadastro_pedido(request):
    global lista2
    #print (lista2)
    #print("")
    global delete
    global guarda_valores
    global nome_antigo
    global data_antigo

    delete = False

    lista_itens = []

    #print(lista_itens)
    #print("passei por aqui")
    if request.method == 'POST':
        form = PedidoModelForm(request.POST or None)
        delete = True
        # Excluir item se delete_index estiver no POST
        delete_index = request.POST.get('delete_index')
        if delete_index is not None:
            delete = True
            try:
                delete_index = int(delete_index)
                if 0 <= delete_index < len(lista2):
                    del lista2[delete_index]
                    #print(f"Item na posição {delete_index} removido de lista2.")
            except ValueError:
                print("Índice de exclusão inválido")

        elif 'save_itens' in request.POST:
            try:

                if form.is_valid():

                    # Salvar pedido principal
                    nome = form.cleaned_data.get('nome')

                    data = form.cleaned_data.get('data_de_locacao')
                    local = form.cleaned_data.get('local')
                    observacao = form.cleaned_data.get('observacao')
                    telefone = form.cleaned_data.get('telefone')
                    endereco = form.cleaned_data.get('endereco')
                    nova_data = str(data)

                    if telefone is None:
                        telefone = ''
                    if local is None:
                        local = ''
                    if endereco is None:
                        endereco = ''
                    if observacao is None:
                        observacao = ''

                    guarda_valores = {
                        'nome': nome,
                        'data_de_locacao': nova_data,
                        'local': local,
                        'observacao': observacao,
                        'telefone': telefone,
                        'endereco': endereco
                    }

                    # Salvar itens do pedido
                    itens_pedido_formset = form.itens_pedido(queryset=ItemPedido.objects.none(), data=request.POST)
                    if itens_pedido_formset.is_valid():
                        salvar = True
                        for formset_form in itens_pedido_formset:
                            produto = formset_form.cleaned_data.get('produto')
                            quantidade_alugada = formset_form.cleaned_data.get('quantidade_alugada')

                            for item in lista2:

                                produto_str = f'{produto.nome} - {produto.modelo}'
                                protuto2_str = f'{item[1]} - {item[2]} '

                                if (produto_str.strip()) == (protuto2_str.strip()):
                                    salvar = False
                                    break

                        if salvar:  # Se não encontrou duplicado, adiciona o item à lista
                            lista = [nome, produto.nome, produto.modelo, quantidade_alugada, nova_data, local,
                                     observacao, telefone, endereco]
                            lista2.append(lista)
                            #print("Produto adicionado:", lista)
                            resultado = 2

                        else:
                            print("Produto já existe, não adicionado.")
                            resultado = 3

                        #print(lista2)

                        for item in lista2:
                            resultado_temporario = (f"{item[1]} - {item[2]} - {item[3]}")
                            lista_itens.append(resultado_temporario)

                        #print(lista_itens)

                        return render(request, 'cadastro_pedido.html', {'form': form,'lista_itens':lista_itens,'resultado':resultado})  # Redirecionar para a página de sucesso após salvar
                    else:
                        print("Formulário do item não é válido")
            except:
                print("Erro ao salvar o Item")
            else:
                print("Formulário principal não é válido")

        elif 'save_pedido' in request.POST:
            try:
                if form.is_valid():
                    nome = form.cleaned_data.get('nome')
                    data = form.cleaned_data.get('data_de_locacao')
                    nova_data = str(data)

                    # Verificar se já existe um pedido com o mesmo nome e data
                    if 'nome' not in request.GET:
                        if PedidoModel.objects.filter(nome=nome, data_de_locacao=nova_data).exists():
                            # Caso exista, mostrar uma mensagem de erro
                            form = PedidoModelForm()
                            lista2 = []
                            return render(request, 'cadastro_pedido.html',
                                          {'form': form, 'lista_itens': lista_itens, 'resultado': 4})
                        else:
                            resultado = 1
                            salva_pedido()
                            #print(lista2)
                            form = PedidoModelForm()
                            contexto = {'form': form, 'resultado': resultado}
                            lista2 = []

                    else:
                        local = form.cleaned_data.get('local')
                        observacao = form.cleaned_data.get('observacao')
                        telefone = form.cleaned_data.get('telefone')
                        endereco = form.cleaned_data.get('endereco')

                        guarda_valores = {
                            'nome': nome,
                            'data_de_locacao': nova_data,
                            'local': local,
                            'observacao': observacao,
                            'telefone': telefone,
                            'endereco': endereco
                        }

                        # Atualizando os dados na lista
                        for item in lista2:
                            # Atualiza o nome (índice 0)
                            item[0] = nome  # Atualiza o nome (índice 0)

                            # Atualizar a data e o local
                            item[4] = nova_data  # Atualiza a data de locação (índice 4)
                            item[5] = local  # Atualiza o local (índice 5)

                            # Atualizar observação, telefone e endereço
                            item[6] = observacao  # Atualiza a observação (índice 6)
                            item[7] = telefone  # Atualiza o telefone (índice 7)
                            item[8] = endereco  # Atualiza o endereço (índice 8)
                        #pedido = PedidoModel.objects.get(nome=nome,data_de_locacao=data)
                        pedido = PedidoModel.objects.get(nome=nome_antigo, data_de_locacao=data_antigo)
                        pedido.delete()
                        #print(lista2)
                        resultado = 1
                        salva_pedido()
                        form = PedidoModelForm()
                        contexto = {'form': form, 'resultado': resultado}
                        lista2 = []
                        #print(lista2)

                    return render(request, 'cadastro_pedido.html', contexto)

            except Exception as e:
                resultado = 0

                form = PedidoModelForm()
                #print("estou apagando aqui 2")
                contexto = {'form': form,'resultado':resultado}
                lista2 = []
                print(f'Erro: {e}')

                return render(request, 'cadastro_pedido.html', contexto)

    elif  request.method == 'GET':

        if request.GET:
            print("Encontrado parametro")
            nome = request.GET['nome']
            data = request.GET['data']
            nome_antigo = request.GET['nome']
            data_antigo = request.GET['data']
            print(nome_antigo)
            print(data_antigo)
            itens_serializado = request.GET.get('itens', '[]')
            lista_itens = json.loads(itens_serializado)
            #print(lista_itens)
            #print(data)
            pedido = PedidoModel.objects.get(nome=nome, data_de_locacao=data)

            # Preenche o formulário com os dados do pedido
            form = PedidoModelForm(instance=pedido)
            lista2 = []

            for item in lista_itens:
                temp = [item.strip() for item in item.split('-')]
                lista2.append([pedido.nome,temp[0],temp[1],temp[2],data,pedido.local,pedido.observacao,pedido.telefone,pedido.endereco])
        else:
            lista2 = []
            form = PedidoModelForm()

    #print(delete)
    #print(lista2)
    if delete:

        #print(lista2)

        nome = lista2[0][0]
        data = lista2[0][4]
        nova_data = str(data)
        local = lista2[0][5]
        observacao = lista2[0][6]
        telefone = lista2[0][7]
        endereco = lista2[0][8]

        guarda_valores = {
            'nome': nome,
            'data_de_locacao': nova_data,
            'local': local,
            'observacao': observacao,
            'telefone': telefone,
            'endereco': endereco
        }


        form = PedidoModelForm(initial=guarda_valores)
        for item in lista2:
            resultado_temporario = (f"{item[1]} - {item[2]} - {item[3]}")
            lista_itens.append(resultado_temporario)


    return render(request, 'cadastro_pedido.html', {'form': form,'lista_itens':lista_itens})

def pesquisacliente(request):
    if request.method == 'GET':
        return render(request, 'pesquisa_cliente.html', {})

"""
from django.core.management.base import BaseCommand
import os
import subprocess

class Command(BaseCommand):
    help = 'Faz backup dos dados, converte para UTF-8 e importa para o banco de dados'

    def handle(self, *args, **kwargs):
        # Passo 1: Fazer backup usando dumpdata
        backup_file = 'backup.json'
        self.stdout.write(self.style.SUCCESS('Fazendo backup dos dados...'))
        subprocess.run(['python', 'manage.py', 'dumpdata'], stdout=open(backup_file, 'w', encoding='utf-16'))

        # Passo 2: Converter de UTF-16 para UTF-8
        self.stdout.write(self.style.SUCCESS('Convertendo arquivo para UTF-8...'))
        with open(backup_file, 'r', encoding='utf-16') as file:
            content = file.read()

        backup_utf8_file = 'backup_utf8.json'
        with open(backup_utf8_file, 'w', encoding='utf-8') as file:
            file.write(content)

        self.stdout.write(self.style.SUCCESS(f'Arquivo convertido para UTF-8: {backup_utf8_file}'))

        # Passo 3: Importar os dados usando loaddata
        self.stdout.write(self.style.SUCCESS('Importando dados para o banco de dados...'))
        subprocess.run(['python', 'manage.py', 'loaddata', backup_utf8_file])

        self.stdout.write(self.style.SUCCESS('Backup e importação concluídos com sucesso!'))
"""