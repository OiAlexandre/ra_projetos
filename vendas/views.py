from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpRequest, HttpResponse, Http404
from django.contrib import messages
from django.db import transaction

from .models import Produto, Categoria, Venda
from .forms import ProdutoForm, VendaForm, ItemVendaFormSet
from .exporters import ExporterFactory
from .facades import VendaFacade

# View para a página inicial (Dashboard)
def home(request):
    context = {} 
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

# --- View de Exportação de Produtos ---
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


# --- CRUD de Vendas ---

# READ (Listar Vendas)
class VendaListView(ListView):
    model = Venda
    template_name = 'venda_list.html'
    context_object_name = 'vendas'
    paginate_by = 10
    def get_queryset(self):
        return Venda.objects.prefetch_related('itens__produto').order_by('-data')

# CREATE (Criar Venda)
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
            # Passa o 'empty_form' para o JS
            context['formset'] = ItemVendaFormSet(prefix='itens')
            context['empty_form'] = ItemVendaFormSet(prefix='itens').empty_form
        return context

    def post(self, request, *args, **kwargs):
        self.object = None 
        form = self.get_form()
        formset = ItemVendaFormSet(request.POST, prefix='itens')

        if form.is_valid() and (form.cleaned_data['status'] == Venda.StatusVenda.CANCELADA or formset.is_valid()):
            # Se for 'CANCELADA', não precisamos validar o formset
            # Se NÃO for 'CANCELADA', o formset.is_valid() é checado
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

# (NOVO) UPDATE (Atualizar Venda)
class VendaUpdateView(SuccessMessageMixin, UpdateView):
    model = Venda
    form_class = VendaForm # Reutiliza o form principal
    template_name = 'venda_form.html' # Reutiliza o template
    success_url = reverse_lazy('venda_list')
    success_message = "Status da Venda atualizado com sucesso!"

    def get_context_data(self, **kwargs):
        """Adiciona flag para o template saber que é modo de edição."""
        context = super().get_context_data(**kwargs)
        # Esta flag será usada no template para esconder o formset de itens
        context['is_update_view'] = True 
        return context

    def form_valid(self, form):
        """
        Chama a Facade para lidar com a lógica de negócio da
        mudança de status ANTES de salvar o formulário.
        """
        # Pega o status antigo (antes da mudança)
        old_status = self.get_object().status
        # Pega o novo status (do formulário enviado)
        new_status = form.cleaned_data['status']
        
        if old_status != new_status:
            facade = VendaFacade()
            try:
                # Chama a Facade para aplicar a lógica (devolver/retirar estoque)
                facade.atualizar_status_venda(self.object, old_status, new_status)
            except Exception as e:
                messages.error(self.request, str(e))
                return self.form_invalid(form)
        
        # Salva o formulário (atualizando a Venda com o novo status)
        return super().form_valid(form)