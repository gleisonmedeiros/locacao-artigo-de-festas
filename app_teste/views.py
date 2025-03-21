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
import os
import subprocess
from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
import time

from reportlab.lib.pagesizes import letter,landscape
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph
from reportlab.lib.units import inch

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

# Função para converter a data no formato desejado
def get_date(item):
    #print(item[1])
    date_str = item[1].split(' - ')[0]  # Extrai apenas a parte "DD/MM/YYYY"
    return datetime.strptime(date_str, '%d/%m/%Y')


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

            form_date = DateRangeForm(request.POST or None, initial={'data_inicio': data_inicio, 'data_fim': data_fim})

        # Lista de dados filtrados com base na data alvo
            lista_filtrada_a = [(nome, data, local, observacao, itens, telefone, endereco) for nome, data, local, observacao, itens, telefone,endereco in lista_dados
                          if (formata_data(data) >= data_inicio_formatada) and ((formata_data(data) <= data_fim_formatada))]

            lista_filtrada = sorted(lista_filtrada_a, key=get_date)

            #print(lista_filtrada)
            if request.GET.get('pesquisar'):
                print("entreeiii")
                gerar_pdf(lista_filtrada)
                time.sleep(2)
                arquivo = "pedido_relatorio_horizontal.pdf"
                foi = False
                while foi == False:
                    if is_file_in_use(arquivo):
                        print(f"O arquivo {arquivo} está em uso.")
                        time.sleep(1)
                    else:
                        print(f"O arquivo {arquivo} não está em uso.")
                        foi = True

                if not os.path.exists(arquivo):
                    print(f"O arquivo {arquivo} não foi encontrado.")

                # Retornar o arquivo PDF para o download
                with open(arquivo, 'rb') as file:
                    # Criando a resposta HTTP para o download
                    response = HttpResponse(file.read(), content_type='application/pdf')
                    # Forçar o download com Content-Disposition
                    response['Content-Disposition'] = f'attachment; filename="{arquivo}"'
                    return response

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
                #print(f"Nome: {produto.nome}")
                #print(f"Modelo: {produto.modelo}")
                #print(f"Quantidade: {quantidade}")
                qtd_produto = Produto_Model.objects.get(nome=produto.nome, modelo=produto.modelo)
                #print(qtd_produto.quantidade)
                novo_resultado.append([produto.nome,produto.modelo,quantidade,qtd_produto.quantidade-quantidade])


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
                #print(pedido_item.pedido.data_de_locacao)
                #print(data)
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
        elif 'imprimir' in request.POST:
            print("passei por aqui")
            data_inicio = form_date.cleaned_data['data_inicio'].strftime('%Y-%m-%d')
            data_fim = form_date.cleaned_data['data_fim'].strftime('%Y-%m-%d')
            valor = '1'
            url_agenda = reverse('agenda') + '?datainicio=' + data_inicio + '&datafim=' + data_fim + '&pesquisar='+ valor
            return redirect(url_agenda)


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
        todos_produtos = Produto_Model.objects.all()
        return render(request, 'pesquisa_produto.html', {'messages':messages,'produtos': todos_produtos})

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
                    produto_novo = request.POST.get('cidades')
                    #print(produto_novo)
                    nome_produto, modelo_produto = produto_novo.split(' - ')
                    quantidade_alugada = request.POST.get('quantidade')
                    #print(quantidade_alugada)
                    produtos = Produto_Model.objects.all()
                    #print(produtos)

                    if nome_produto and modelo_produto and (int(quantidade_alugada) > 0):
                        produto_existe = Produto_Model.objects.filter(nome=nome_produto, modelo=modelo_produto).exists()
                        print("entei assim mesmo")
                        if produto_existe:
                            print(f"O produto {nome_produto} - {modelo_produto} existe no banco de dados!")

                            salvar = True

                            for item in lista2:

                                produto_str = f'{nome_produto} - {modelo_produto}'
                                protuto2_str = f'{item[1]} - {item[2]} '

                                if (produto_str.strip()) == (protuto2_str.strip()):
                                    salvar = False
                                    break

                            if salvar:  # Se não encontrou duplicado, adiciona o item à lista
                                lista = [nome, nome_produto, modelo_produto, quantidade_alugada, nova_data, local,
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
                            produtos = Produto_Model.objects.all()
                            return render(request, 'cadastro_pedido.html', {'form': form,'lista_itens':lista_itens,'resultado':resultado,'produtos': produtos})  # Redirecionar para a página de sucesso após salvar
                        else:
                            print("Formulário do item não é válido")
                            resultado = 5
            except ValueError as e:
                print("Erro ao salvar o Item")
                print(f"Erro ao dividir o produto: {e}")
                #delete = False
                resultado = 5
            else:
                print("Formulário principal não é válido")

        elif 'save_pedido' in request.POST:
            try:
                if form.is_valid():
                    nome = form.cleaned_data.get('nome')
                    data = form.cleaned_data.get('data_de_locacao')
                    nova_data = str(data)
                    produtos = Produto_Model.objects.all()

                    # Verificar se já existe um pedido com o mesmo nome e data
                    if 'nome' not in request.GET:
                        if PedidoModel.objects.filter(nome=nome, data_de_locacao=nova_data).exists():
                            # Caso exista, mostrar uma mensagem de erro
                            form = PedidoModelForm()
                            lista2 = []

                            return render(request, 'cadastro_pedido.html',
                                          {'form': form, 'lista_itens': lista_itens, 'resultado': 4,'produtos':produtos})
                        else:
                            resultado = 1
                            salva_pedido()
                            #print(lista2)
                            form = PedidoModelForm()
                            produtos = Produto_Model.objects.all()
                            contexto = {'form': form, 'resultado': resultado,'produtos':produtos}
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
                        contexto = {'form': form, 'resultado': resultado,'produtos':produtos}
                        lista2 = []
                        #print(lista2)

                    return render(request, 'cadastro_pedido.html', contexto)

            except Exception as e:
                resultado = 0

                form = PedidoModelForm()
                #print("estou apagando aqui 2")
                produtos = Produto_Model.objects.all()
                contexto = {'form': form,'resultado':resultado,'produtos':produtos}
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
            #print(nome_antigo)
            #print(data_antigo)
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
        try:

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
        except Exception as e:
            print(f"Erro : {e}")

        form = PedidoModelForm(initial=guarda_valores)
        for item in lista2:
            resultado_temporario = (f"{item[1]} - {item[2]} - {item[3]}")
            lista_itens.append(resultado_temporario)

    produtos = Produto_Model.objects.all()  # Buscar todos os produtos

    return render(request, 'cadastro_pedido.html', {'form': form, 'lista_itens': lista_itens, 'produtos': produtos})

def handle_uploaded_file(f):
    # Caminho absoluto para a raiz do projeto
    project_root = os.getcwd()
    file_path = os.path.join(project_root, 'backup_utf8.json')

    # Salva o arquivo no caminho especificado
    with open(file_path, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)

def backup_view(request):
    if request.method == 'GET':
        # Renderiza a página com os botões de backup
        return render(request, 'backup.html')

    if request.method == 'POST':
        backup_file = 'backup.json'
        backup_utf8_file = 'backup_utf8.json'
        comando = (request.POST.get('action'))
        # Verificar qual botão foi pressionado com base no nome
        if 'download' == comando:
            # Caminho do arquivo de backup

            print("entrei aqui")

            try:
                # Passo 1: Gerar backup com dumpdata
                with open(backup_file, 'w', encoding='utf-16') as file:
                    subprocess.run(['python', 'manage.py', 'dumpdata'], stdout=file, check=True)

                # Passo 2: Verificar se o arquivo de backup foi gerado
                if not os.path.exists(backup_file):
                    raise FileNotFoundError(f"O arquivo de backup {backup_file} não foi encontrado.")
                else:
                    print("O arquivo de backup foi encontrado.")

                # Passo 3: Converter o backup para UTF-8
                # Abrindo o arquivo ANSI e lendo seu conteúdo
                with open(backup_file, 'r', encoding='mbcs') as file_ansi:
                    content = file_ansi.read()

                # Salvando o conteúdo no formato UTF-8
                with open('backup_utf8.json', 'w', encoding='utf-8') as file_utf8:
                    file_utf8.write(content)

                # Passo 4: Verificar se o arquivo de backup UTF-8 foi gerado
                if not os.path.exists(backup_utf8_file):
                    raise FileNotFoundError(f"O arquivo de backup UTF-8 {backup_utf8_file} não foi encontrado.")

                # Passo 5: Retornar o arquivo para download
                with open(backup_utf8_file, 'rb') as file:
                    # Criando a resposta HTTP para o download
                    response = HttpResponse(file.read(), content_type='application/json')
                    # Forçar o download com Content-Disposition
                    response['Content-Disposition'] = f'attachment; filename="{backup_utf8_file}"'
                    return response
            except Exception as e:
                # Redireciona para a página com mensagem de erro
                return render(request, 'backup.html', {'error': str(e)})

        elif comando == 'upload' and request.FILES.get('backup_file'):

            backup_file = request.FILES['backup_file']

            # Salva o arquivo na raiz do projeto
            handle_uploaded_file(backup_file)

            print("Entrei aqui")

            backup_utf8_file = 'backup_utf8.json'

            try:

                # Passo 3: Limpar o banco de dados

                subprocess.run(['python', 'manage.py', 'flush', '--no-input'], check=True)
                #subprocess.run(['python', 'manage.py', 'flush', '--no-input'], check=True)

                # Passo 4: Importar os dados para o banco de dados usando loaddata

                subprocess.run(['python', 'manage.py', 'loaddata', backup_utf8_file], check=True)

                # Passo 5: Retornar uma mensagem de sucesso
                resultado = 1
                return render(request, 'backup.html', {'resultado':resultado})


            except subprocess.CalledProcessError as e:

                # Em caso de erro no subprocesso, renderiza a página de backup com uma mensagem de erro

                return render(request, 'backup.html', {'error': f'Ocorreu um erro ao executar o comando: {str(e)}'})


            except Exception as e:

                # Qualquer outro erro inesperado

                return render(request, 'backup.html', {'error': f'Erro inesperado: {str(e)}'})

            # Se não for uma requisição POST ou o comando não for 'upload', renderiza o formulário

            # Limpar arquivos temporários
            if os.path.exists(backup_file):
                os.remove(backup_file)
            if os.path.exists(backup_utf8_file):
                os.remove(backup_utf8_file)
            return render(request, 'backup.html')
        else:
            resultado = 0
            return render(request, 'backup.html',{'resultado':resultado})

def is_file_in_use(file_path):
    try:
        # Tentar abrir o arquivo no modo exclusivo (somente para leitura)
        with open(file_path, 'rb'):
            return False  # Se conseguiu abrir, o arquivo não está em uso
    except IOError:
        # Se ocorreu um erro ao abrir o arquivo, provavelmente está em uso
        return True

styles = getSampleStyleSheet()
style_normal = styles["Normal"]
style_bold = styles["Heading4"]


def split_text_by_chars(text, max_chars):
    """
    Divide um texto em linhas de no máximo 'max_chars' caracteres,
    tentando não quebrar palavras no meio.
    """
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        # Se adicionar a próxima palavra ultrapassa o limite, guarda a linha atual e começa uma nova
        if len(current_line) + len(word) + 1 > max_chars:
            lines.append(current_line)
            current_line = word
        else:
            current_line += (" " if current_line else "") + word

    # Adiciona a última linha
    if current_line:
        lines.append(current_line)

    return lines


def draw_wrapped_text(canvas, text, x, y, width, max_chars=40, line_spacing=5):
    """
    Desenha um texto no PDF, quebrando por um número máximo de caracteres por linha.
    """
    lines = split_text_by_chars(text, max_chars)
    for line in lines:
        canvas.drawString(x, y, line)
        y -= 12  # Ajuste para a próxima linha (altura da fonte + espaçamento)
    return len(lines) * 12 + line_spacing  # Retorna a altura usada


def gerar_pdf(lista_filtrada):
    pdf_file = "pedido_relatorio_horizontal.pdf"
    c = canvas.Canvas(pdf_file, pagesize=landscape(letter))

    margin_left = 40
    margin_top = 550
    column_width = 130  # Mantendo a mesma largura
    current_y = margin_top

    font_path_regular = r"calibri.ttf"
    font_path_bold = r"calibri-bold.ttf"

    pdfmetrics.registerFont(TTFont('Calibri', font_path_regular))
    pdfmetrics.registerFont(TTFont('Calibri-Bold', font_path_bold))

    c.setFont("Helvetica-Bold", 16)
    c.drawString(margin_left, current_y, "Relatório de Pedidos")
    current_y -= 30

    c.setFont("Calibri", 10)

    column_positions = [
        margin_left,
        margin_left + column_width,
        margin_left + 2 * column_width,
        margin_left + 3 * column_width,
        margin_left + 4 * column_width,
        margin_left + 5 * column_width
    ]

    col = 0
    for item in lista_filtrada:
        nome, data, local, observacao, itens, telefone, endereco = item

        pedido_text = []
        pedido_text.append("")

        data_n, dia = data.split(" - ")
        if data:
            c.setFont("Calibri-Bold", 12)
            pedido_text.append(f"{dia.upper()} - {data_n}")
            c.setFont("Calibri", 10)

        if telefone is None:
            telefone = ''
        if nome:
            pedido_text.append(f"{nome.upper()} {telefone}")
        if local:
            pedido_text.append(f"Local: {local}")
        if itens:
            for i in itens:
                pedido_text.append(f"{i[1]} - {i[0].nome} {i[0].modelo}")
        if endereco:
            pedido_text.append(f"Endereço: {endereco}")
        if observacao:
            pedido_text.append(f"Observação: {observacao}")

        for line in pedido_text:
            altura_utilizada = draw_wrapped_text(c, line, column_positions[col], current_y, column_width, max_chars=50)
            current_y -= altura_utilizada

        if current_y < 100:
            col += 2
            current_y = margin_top

            if col > 5:
                c.showPage()
                col = 0
                current_y = margin_top

        c.setStrokeColor(colors.black)
        c.setLineWidth(0.5)
        c.line(column_positions[col], current_y, column_positions[col] + column_width, current_y)

        current_y -= 10

    c.save()