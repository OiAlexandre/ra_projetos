from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpRequest, HttpResponse, Http404
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.db.models import Sum, Count, F, DecimalField
import json
import xml.etree.ElementTree as ET
from decimal import Decimal, InvalidOperation

# Importamos CategoriaForm
from .models import Produto, Categoria, Venda, ItemVenda
from .forms import (
    ProdutoForm, VendaForm, ItemVendaFormSet, CategoriaForm
)
from .exporters import ExporterFactory
from .facades import VendaFacade

# --- View da Home/Dashboard ---
def home(request):
    today = timezone.localdate()
    vendas_hoje = Venda.objects.filter(
        data__date=today, 
        status=Venda.StatusVenda.PAGA
    )
    total_vendido_hoje = vendas_hoje.aggregate(
        total=Sum('total', output_field=DecimalField())
    )['total'] or Decimal('0.00')
    itens_vendidos_hoje = ItemVenda.objects.filter(
        venda__in=vendas_hoje
    ).aggregate(
        count=Sum('quantidade')
    )['count'] or 0
    receita_total = Venda.objects.filter(
        status=Venda.StatusVenda.PAGA
    ).aggregate(
        total=Sum('total', output_field=DecimalField())
    )['total'] or Decimal('0.00')
    total_produtos = Produto.objects.count()
    context = {
        'total_vendido_hoje': total_vendido_hoje,
        'itens_vendidos_hoje': itens_vendidos_hoje,
        'receita_total': receita_total,
        'total_produtos': total_produtos,
    } 
    return render(request, 'home.html', context)

# --- CRUD de Produtos ---
class ProdutoListView(ListView):
    model = Produto
    template_name = 'produto_list.html'
    context_object_name = 'produtos'
    def get_queryset(self):
        queryset = super().get_queryset().order_by('nome')
        categoria_id = self.request.GET.get('categoria')
        if categoria_id:
            queryset = queryset.filter(categoria_id=categoria_id)
        return queryset
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categorias'] = Categoria.objects.all().order_by('nome')
        return context
class ProdutoCreateView(SuccessMessageMixin, CreateView):
    model = Produto
    form_class = ProdutoForm
    template_name = 'produto_form.html'
    success_url = reverse_lazy('produto_list') 
    success_message = "Produto criado com sucesso!" 
class ProdutoUpdateView(SuccessMessageMixin, UpdateView):
    model = Produto
    form_class = ProdutoForm
    template_name = 'produto_form.html'
    success_url = reverse_lazy('produto_list')
    success_message = "Produto atualizado com sucesso!"
class ProdutoDeleteView(SuccessMessageMixin, DeleteView):
    model = Produto
    template_name = 'produto_confirm_delete.html'
    success_url = reverse_lazy('produto_list')
    # success_message = "Produto deletado com sucesso!" # Requer workaround

# --- (NOVO) CRUD de Categorias ---
class CategoriaListView(ListView):
    model = Categoria
    template_name = 'categoria_list.html'
    context_object_name = 'categorias'
    paginate_by = 10
    ordering = ['nome']

class CategoriaCreateView(SuccessMessageMixin, CreateView):
    model = Categoria
    form_class = CategoriaForm
    template_name = 'categoria_form.html' # Novo template
    success_url = reverse_lazy('categoria_list')
    success_message = "Categoria criada com sucesso!"

class CategoriaUpdateView(SuccessMessageMixin, UpdateView):
    model = Categoria
    form_class = CategoriaForm
    template_name = 'categoria_form.html' # Reutiliza o template
    success_url = reverse_lazy('categoria_list')
    success_message = "Categoria atualizada com sucesso!"

class CategoriaDeleteView(DeleteView): # Removido SuccessMessageMixin
    model = Categoria
    template_name = 'categoria_confirmar_delete.html' # Novo template
    success_url = reverse_lazy('categoria_list')
    # success_message = "Categoria deletada com sucesso!" # Requer workaround
    
    # Adicionando a mensagem de sucesso manualmente
    def form_valid(self, form):
        messages.success(self.request, "Categoria deletada com sucesso!")
        return super().form_valid(form)


# --- View de Exportação de Produtos ---
@transaction.atomic 
def export_produtos(request: HttpRequest) -> HttpResponse:
    export_format = request.GET.get('format', 'json').lower()
    categoria_id = request.GET.get('categoria')
    queryset = Produto.objects.all().select_related('categoria').order_by('nome')
    if categoria_id:
        queryset = queryset.filter(categoria_id=categoria_id)
    factory = ExporterFactory()
    try:
        exporter = factory.get_exporter(export_format, queryset)
    except ValueError as e:
        raise Http404(str(e))
    return exporter.export()

# --- View de Importação de Produtos ---
@transaction.atomic 
def import_produtos(request: HttpRequest) -> HttpResponse:
    if request.method != 'POST':
        messages.error(request, "Método não permitido.")
        return redirect('produto_list')
    
    arquivo = request.FILES.get('arquivo_importacao')
    if not arquivo:
        messages.error(request, "Nenhum arquivo enviado.")
        return redirect('produto_list')

    try:
        if arquivo.name.endswith('.json'):
            count = _processar_json(arquivo)
        elif arquivo.name.endswith('.xml'):
            count = _processar_xml(arquivo)
        else:
            messages.error(request, "Formato de arquivo inválido. Use .json ou .xml.")
            return redirect('produto_list')
        
        messages.success(request, f"{count} produtos foram importados/atualizados com sucesso!")
    
    except Exception as e:
        messages.error(request, f"Erro ao processar o arquivo: {e}")
    
    return redirect('produto_list')

def _get_categoria_dinamicamente(categoria_nome: str) -> Categoria:
    if not categoria_nome:
        return None
    categoria, _ = Categoria.objects.get_or_create(
        nome__iexact=categoria_nome,
        defaults={'nome': categoria_nome.capitalize()}
    )
    return categoria
def _processar_json(arquivo) -> int:
    dados = json.load(arquivo)
    if not isinstance(dados, list):
        raise ValueError("JSON deve ser uma lista (array) de produtos.")
    count = 0
    for item in dados:
        categoria_obj = _get_categoria_dinamicamente(item.get('categoria'))
        Produto.objects.update_or_create(
            nome=item.get('nome'),
            defaults={
                'preco': Decimal(item.get('preco', 0)),
                'estoque': int(item.get('estoque', 0)),
                'descricao': item.get('descricao', ''),
                'categoria': categoria_obj
            }
        )
        count += 1
    return count
def _processar_xml(arquivo) -> int:
    tree = ET.parse(arquivo)
    root = tree.getroot()
    count = 0
    for produto_node in root.findall('produto'):
        nome = produto_node.find('nome').text
        categoria_nome = produto_node.find('categoria').text if produto_node.find('categoria') is not None else None
        categoria_obj = _get_categoria_dinamicamente(categoria_nome)
        Produto.objects.update_or_create(
            nome=nome,
            defaults={
                'preco': Decimal(produto_node.find('preco').text or 0),
                'estoque': int(produto_node.find('estoque').text or 0),
                'descricao': produto_node.find('descricao').text if produto_node.find('descricao') is not None else '',
                'categoria': categoria_obj
            }
        )
        count += 1
    return count

# --- CRUD de Vendas ---
class VendaListView(ListView):
    model = Venda
    template_name = 'venda_list.html'
    context_object_name = 'vendas'
    def get_queryset(self):
        return Venda.objects.prefetch_related('itens__produto').order_by('-data')
class VendaCreateView(SuccessMessageMixin, CreateView):
    model = Venda
    form_class = VendaForm
    template_name = 'venda_form.html'
    success_url = reverse_lazy('venda_list')
    success_message = "Venda registrada com sucesso!"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = ItemVendaFormSet(self.request.POST, prefix='itens')
        else:
            context['formset'] = ItemVendaFormSet(prefix='itens')
            context['empty_form'] = ItemVendaFormSet(prefix='itens').empty_form
        return context
    def post(self, request, *args, **kwargs):
        self.object = None 
        form = self.get_form()
        formset = ItemVendaFormSet(request.POST, prefix='itens')
        if form.is_valid() and (form.cleaned_data['status'] == Venda.StatusVenda.CANCELADA or formset.is_valid()):
            try:
                facade = VendaFacade()
                facade.criar_venda(form, formset, request.FILES)
                messages.success(request, self.success_message)
                return redirect(self.success_url)
            except Exception as e:
                messages.error(request, f"Erro ao salvar a venda: {e}")
                context = self.get_context_data(form=form, formset=formset)
                context['empty_form'] = ItemVendaFormSet(prefix='itens').empty_form
                return self.render_to_response(context)
        messages.error(request, "Por favor, corrija os erros abaixo.")
        context = self.get_context_data(form=form, formset=formset)
        context['empty_form'] = ItemVendaFormSet(prefix='itens').empty_form
        return self.render_to_response(context)
class VendaUpdateView(SuccessMessageMixin, UpdateView):
    model = Venda
    form_class = VendaForm
    template_name = 'venda_form.html'
    success_url = reverse_lazy('venda_list')
    success_message = "Status da Venda atualizado com sucesso!"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_update_view'] = True 
        return context
    def form_valid(self, form):
        old_status = self.get_object().status
        new_status = form.cleaned_data['status']
        if old_status != new_status:
            facade = VendaFacade()
            try:
                facade.atualizar_status_venda(self.object, old_status, new_status)
            except Exception as e:
                messages.error(self.request, str(e))
                return self.form_invalid(form)
        return super().form_valid(form)