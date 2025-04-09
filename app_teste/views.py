from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from .forms import ProdutoForm, PedidoModelForm, DateRangeForm
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
from django.db.models import Sum
from io import BytesIO

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

#lista2 = []
#nome_antigo = ""
#data_antigo = ""

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



def formata_data(data):
    nova_data = datetime.strptime(data.split(' - ')[0], "%d/%m/%Y").date()

    return nova_data

def converter_pedidos_agregados(pedidos_agregados):
    lista_filtrada = []

    for nome, dados in pedidos_agregados.items():
        data = dados.get('data_locacao_formatada', '')
        local = dados.get('local', '')
        observacao = dados.get('observacao', '')
        telefone = dados.get('telefone', '')
        endereco = dados.get('endereco', '')
        produtos_raw = dados.get('produtos', [])

        itens = []
        for item in produtos_raw:
            try:
                partes = item.split(' - ')
                nome_modelo = partes[1]
                quantidade = partes[2]

                class ProdutoFake:
                    def __init__(self, nome_modelo):
                        self.nome, self.modelo = nome_modelo.split(' ', 1) if ' ' in nome_modelo else (nome_modelo, '')

                produto_obj = ProdutoFake(nome_modelo)
                itens.append((produto_obj, quantidade))
            except Exception as e:
                print(f"Erro ao processar item: {item} → {e}")

        lista_filtrada.append((nome, data, local, observacao, itens, telefone, endereco))

    return lista_filtrada
# Função para converter a data no formato desejado
def get_date(item):
    #print(item[1])
    date_str = item[1].split(' - ')[0]  # Extrai apenas a parte "DD/MM/YYYY"
    return datetime.strptime(date_str, '%d/%m/%Y')


def agenda(request):
    form_date = DateRangeForm()

    if request.method == 'GET':

        if request.GET.get('datainicio') and request.GET.get('datafim'):
            data_inicio = request.GET.get('datainicio')
            data_fim = request.GET.get('datafim')

            data_inicio_formatada = datetime.strptime(data_inicio, "%Y-%m-%d").date()
            data_fim_formatada = datetime.strptime(data_fim, "%Y-%m-%d").date()

            pedidos_itens = ItemPedido.objects.select_related('produto', 'pedido').filter(
                pedido__data_de_locacao__range=(data_inicio_formatada, data_fim_formatada)
            )

        else:
            # Consulta para obter os itens dos pedidos com informações relacionadas
            pedidos_itens = ItemPedido.objects.select_related('produto', 'pedido').order_by('pedido__data_de_locacao')


        pedidos_agregados = {}

        quantidade_produtos = pedidos_itens.values('produto__nome', 'produto__modelo').annotate(total=Sum('quantidade_alugada')).order_by('produto__nome', 'produto__modelo')

        #print(quantidade_produtos)
        # Preencher o dicionário com os dados dos pedidos
        for pedido_item in pedidos_itens:
            id_pedido = pedido_item.pedido.id
            cliente_nome = pedido_item.pedido.nome
            produto_nome = pedido_item.produto.nome
            produto_modelo = pedido_item.produto.modelo
            produto_quantidade = pedido_item.quantidade_alugada
            telefone = pedido_item.pedido.telefone
            endereco = pedido_item.pedido.endereco
            local = pedido_item.pedido.local
            data_de_locacao = pedido_item.pedido.data_de_locacao
            observacao = pedido_item.pedido.observacao

            #print(f'hhhhh - {id_pedido}')

            produtos = f"{produto_nome} - {produto_modelo} - {produto_quantidade}"

            # Se o cliente não estiver no dicionário, adicione-o
            if cliente_nome not in pedidos_agregados:
                pedidos_agregados[cliente_nome] = {
                    'id_pedido':id_pedido,
                    'telefone': telefone,
                    'endereco': endereco,
                    'local': local,
                    'data_de_locacao': data_de_locacao,
                    'observacao': observacao,
                    'produtos': []  # Lista de produtos
                }

            #print(pedidos_agregados[cliente_nome])

            # Adiciona o nome do produto à lista de produtos do cliente
            pedidos_agregados[cliente_nome]['produtos'].append(produtos)

        # Tratamento do dia da semana e formatação da data
        for cliente_nome, dados_cliente in pedidos_agregados.items():
            data = dados_cliente['data_de_locacao']

            # Formatação da data
            data_formatada = data.strftime("%Y-%m-%d")  # Converte para string no formato correto

            # Obtém o nome do dia da semana
            dia_da_semana = unidecode(data.strftime("%A").capitalize())

            # Corrige nomes de dias da semana que perderam acentos
            print(dia_da_semana)

            if dia_da_semana == 'Sabado' or dia_da_semana =='Sa!bado':
                dia_da_semana = 'Sábado'
            elif dia_da_semana == 'Terca-feira' or dia_da_semana == 'TeraSSa-feira':
                dia_da_semana = 'Terça-feira'

            # Quebra a string no formato correto
            ano, mes, dia = data_formatada.split('-')
            data_locacao = f'{dia}/{mes}/{ano} - {dia_da_semana}'

            # Atualiza a data formatada no dicionário
            dados_cliente['data_locacao_formatada'] = data_locacao

        print(pedidos_agregados)

        if request.GET.get('pesquisar') == '1':
            print("imprimir")
            lista_filtrada = converter_pedidos_agregados(pedidos_agregados)
            return gerar_pdf(lista_filtrada)

        for item in quantidade_produtos:
            produto = Produto_Model.objects.filter(
                nome=item['produto__nome'],
                modelo=item['produto__modelo']
            ).first()

            if produto:
                item['restante'] = produto.quantidade - item['total']
            else:
                item['restante'] = 0  # ou None, dependendo de como quiser tratar produtos não encontrados

        return render(request, 'agenda.html', {'pedidos_agregados': pedidos_agregados, 'form': form_date,'quantidade_produtos':quantidade_produtos})



    elif request.method == 'POST':
        form_date = DateRangeForm(request.POST)

        if form_date.is_valid() and 'pesquisar' in request.POST:
            data_inicio = form_date.cleaned_data['data_inicio'].strftime('%Y-%m-%d')
            data_fim = form_date.cleaned_data['data_fim'].strftime('%Y-%m-%d')
            url_agenda = reverse('agenda') + f'?datainicio={data_inicio}&datafim={data_fim}'
            return redirect(url_agenda)


        elif 'editar_itens' in request.POST:

            #print("Clicou no editar...........")

            id_pedido = request.POST['id_pedido']  # Obtendo o ID do pedido diretamente do formulário

            return redirect(f'/cadastro-pedido/?id={id_pedido}')



        elif 'delete_itens' in request.POST:

            id_pedido = request.POST['id_pedido']  # Captura o ID enviado no formulário

            print(f'pedido excluido:{id_pedido}')

            if id_pedido:
                PedidoModel.objects.filter(id=id_pedido).delete()  # Exclui o pedido

            return redirect('/agenda/')  # Redireciona para recarregar a lista corretamente

        elif 'imprimir' in request.POST:
            data_inicio = form_date.cleaned_data['data_inicio'].strftime('%Y-%m-%d')
            data_fim = form_date.cleaned_data['data_fim'].strftime('%Y-%m-%d')
            valor = '1'
            url_agenda = reverse('agenda') + f'?datainicio={data_inicio}&datafim={data_fim}&pesquisar={valor}'
            return redirect(url_agenda)

        else:
            return redirect('agenda')

    return render(request, 'agenda.html', {})

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


def cadastro_pedido(request):
    lista_itens = []
    resultado = 10

    if request.method == 'POST':
        form = PedidoModelForm(request.POST)

        # Excluir item da lista
        if 'delete_index' in request.POST:
            delete_index = int(request.POST['delete_index'])
            lista2 = request.session.get('lista2', [])

            if 0 <= delete_index < len(lista2):
                del lista2[delete_index]
                request.session['lista2'] = lista2  # Atualiza a sessão

            if 'id' in request.GET:  # Mantém os dados do pedido ao excluir
                id = request.GET['id']
                pedido = PedidoModel.objects.get(id=id)
                form = PedidoModelForm(instance=pedido)

        # Adicionar item à lista
        elif 'save_itens' in request.POST:
            if form.is_valid():
                dados_pedido = form.cleaned_data

                produto_html = request.POST.get('cidades')
                quantidade_html = (request.POST.get('quantidade', '0'))

                print(f'Produto: {produto_html}')
                print(f'Quantidade_html: {quantidade_html}')

                if (quantidade_html == ''):
                    quantidade_html = 0

                if produto_html and int(quantidade_html) > 0:

                    nome_produto, modelo_produto = request.POST.get('cidades').split(" - ")
                    quantidade_alugada = int(request.POST.get('quantidade', 0))

                    produto = Produto_Model.objects.filter(nome=nome_produto, modelo=modelo_produto).first()
                    if produto:
                        lista2 = request.session.get('lista2', [])

                        # Verifica se o produto já está na lista
                        for item in lista2:
                            if item[1] == nome_produto and item[2] == modelo_produto:
                                resultado = 3  # Produto já existe
                                break
                        else:
                            lista2.append([
                                dados_pedido['nome'], nome_produto, modelo_produto, quantidade_alugada,
                                str(dados_pedido['data_de_locacao']), dados_pedido['local'],
                                dados_pedido['observacao'], dados_pedido['telefone'],
                                dados_pedido['endereco']
                            ])
                            request.session['lista2'] = lista2
                            resultado = 2  # Produto adicionado

                    else:
                        resultado = 5  # Produto não encontrado
                else:
                    resultado = 5  # Dados inválidos

        # Salvar pedido no banco
        elif 'save_pedido' in request.POST:
            if form.is_valid():
                nome = form.cleaned_data['nome']
                data_de_locacao = str(form.cleaned_data['data_de_locacao'])
                pedido_id = request.GET.get('id')

                # Verifica se já existe um pedido com o mesmo nome e data, excluindo o atual
                if PedidoModel.objects.filter(nome=nome, data_de_locacao=data_de_locacao).exclude(id=pedido_id).exists():
                    resultado = 4  # Pedido já existe
                else:
                    if pedido_id:
                        pedido = PedidoModel.objects.get(id=pedido_id)
                        pedido.__dict__.update(**form.cleaned_data)
                        pedido.save()

                        # Remove os itens antigos antes de adicionar os novos
                        ItemPedido.objects.filter(pedido=pedido).delete()
                    else:
                        pedido = PedidoModel.objects.create(**form.cleaned_data)

                    # Adiciona os novos itens ao pedido
                    for item in request.session.get('lista2', []):
                        produto = Produto_Model.objects.get(nome=item[1], modelo=item[2])
                        ItemPedido.objects.create(pedido=pedido, produto=produto, quantidade_alugada=item[3])

                    resultado = 1  # Pedido salvo com sucesso
                    request.session['lista2'] = []  # Limpa a lista de itens
                    form = PedidoModelForm()  # Limpa os campos

    else:
        form = PedidoModelForm()

        # Carregar pedido existente ao acessar via URL com ID
        if 'id' in request.GET:
            id = request.GET['id']
            try:
                pedido = PedidoModel.objects.get(id=id)
                form = PedidoModelForm(instance=pedido)

                # Carregar itens do pedido na sessão
                itens_pedido = ItemPedido.objects.filter(pedido=pedido)
                lista2 = [[
                    pedido.nome, item.produto.nome, item.produto.modelo, item.quantidade_alugada,
                    str(pedido.data_de_locacao), pedido.local, pedido.observacao,
                    pedido.telefone, pedido.endereco
                ] for item in itens_pedido]

                request.session['lista2'] = lista2
                lista_itens = list(itens_pedido.values('id', 'produto__nome', 'produto__modelo', 'quantidade_alugada'))

            except PedidoModel.DoesNotExist:
                request.session['lista2'] = []
        else:
            request.session['lista2'] = []  # Reseta a lista ao criar um novo pedido

    # Ajusta a lista de itens para exibição na tabela
    lista_itens = [
        {'produto__nome': item[1], 'produto__modelo': item[2], 'quantidade_alugada': item[3]}
        for item in request.session.get('lista2', [])
    ]

    produtos = Produto_Model.objects.all()
    return render(request, 'cadastro_pedido.html', {
        'form': form,
        'lista_itens': lista_itens,
        'resultado': resultado,
        'produtos': produtos
    })
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

            #print("entrei aqui")

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


styles = getSampleStyleSheet()
style_normal = styles["Normal"]
style_bold = styles["Heading4"]


def split_text_by_chars(text, max_chars):
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        if len(current_line) + len(word) + 1 > max_chars:
            lines.append(current_line)
            current_line = word
        else:
            current_line += (" " if current_line else "") + word

    if current_line:
        lines.append(current_line)

    return lines


def draw_wrapped_text(canvas, text, x, y, width, max_chars=40, line_spacing=5):
    lines = split_text_by_chars(text, max_chars)
    for line in lines:
        canvas.drawString(x, y, line)
        y -= 12
    return len(lines) * 12 + line_spacing


def gerar_pdf(lista_filtrada):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=landscape(letter))

    margin_left = 40
    margin_top = 550
    column_width = 130
    current_y = margin_top
    ALTURA_MINIMA = 70  # margem inferior segura

    # Altere os caminhos se precisar
    font_path_regular = r"calibri.ttf"
    font_path_bold = r"calibri-bold.ttf"

    pdfmetrics.registerFont(TTFont('Calibri', font_path_regular))
    pdfmetrics.registerFont(TTFont('Calibri-Bold', font_path_bold))

    c.setFont("Helvetica-Bold", 16)
    c.drawString(margin_left, current_y, "Relatório de Pedidos")
    current_y -= 30
    c.setFont("Calibri", 10)

    column_positions = [margin_left + i * column_width for i in range(6)]
    col = 0

    for item in lista_filtrada:
        nome, data, local, observacao, itens, telefone, endereco = item
        pedido_text = []

        if data:
            data_n, dia = data.split(" - ")
            c.setFont("Calibri-Bold", 12)
            pedido_text.append(f"{dia.upper()} - {data_n}")
            c.setFont("Calibri", 10)

        if nome:
            pedido_text.append(f"{nome.upper()} {telefone or ''}")
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
            # Estimar altura necessária
            altura_esperada = 12 * ((len(line) // 50) + 1)

            # Verificar antes de desenhar se cabe
            if current_y - altura_esperada < ALTURA_MINIMA:
                col += 2
                current_y = margin_top
                if col > 5:
                    c.showPage()
                    col = 0
                    current_y = margin_top

            altura_utilizada = draw_wrapped_text(
                c, line, column_positions[col], current_y, column_width, max_chars=50
            )
            current_y -= altura_utilizada

        # Linha de separação, só se houver espaço
        if current_y > ALTURA_MINIMA:
            c.setStrokeColor(colors.black)
            c.setLineWidth(0.5)
            c.line(column_positions[col], current_y, column_positions[col] + column_width, current_y)
            current_y -= 10

    c.save()
    buffer.seek(0)

    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="pedido_relatorio_horizontal.pdf"'
    return response