from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.messages.views import SuccessMessageMixin

from .models import Produto, Categoria, Venda # Importamos Categoria e Venda
from .forms import ProdutoForm

# View para a página inicial (Dashboard)
def home(request):
    context = {} 
    return render(request, 'home.html', context)

# --- CRUD de Produtos ---

# READ (Listar)
class ProdutoListView(ListView):
    model = Produto
    template_name = 'produto_list.html'
    context_object_name = 'produtos'
    paginate_by = 10

    # (NOVO) Sobrescrevemos o get_queryset para aplicar o filtro
    def get_queryset(self):
        # Pega o queryset base (todos os produtos)
        queryset = super().get_queryset().order_by('nome')
        
        # Pega o 'categoria_id' do parâmetro GET da URL (ex: ?categoria=2)
        categoria_id = self.request.GET.get('categoria')
        
        # Se um categoria_id foi fornecido e não está vazio
        if categoria_id:
            # Filtra o queryset
            queryset = queryset.filter(categoria_id=categoria_id)
            
        return queryset

    # (NOVO) Adiciona o contexto para o template
    def get_context_data(self, **kwargs):
        # Pega o contexto existente
        context = super().get_context_data(**kwargs)
        # Adiciona a lista de todas as categorias ao contexto
        # para popularmos o dropdown de filtro no template
        context['categorias'] = Categoria.objects.all().order_by('nome')
        return context


# CREATE (Criar)
class ProdutoCreateView(SuccessMessageMixin, CreateView):
    model = Produto
    form_class = ProdutoForm
    template_name = 'produto_form.html'
    success_url = reverse_lazy('produto_list') 
    success_message = "Produto criado com sucesso!" 

# UPDATE (Atualizar/Editar)
class ProdutoUpdateView(SuccessMessageMixin, UpdateView):
    model = Produto
    form_class = ProdutoForm
    template_name = 'produto_form.html'
    success_url = reverse_lazy('produto_list')
    success_message = "Produto atualizado com sucesso!"

# DELETE (Deletar)
class ProdutoDeleteView(SuccessMessageMixin, DeleteView):
    model = Produto
    template_name = 'produto_confirm_delete.html'
    success_url = reverse_lazy('produto_list')
    # (Para a mensagem de sucesso na deleção, precisaríamos de um ajuste)
    # success_message = "Produto deletado com sucesso!" 


# --- CRUD de Vendas ---

# (NOVO) READ (Listar Vendas) - Requisito: "Consulta com Join"
class VendaListView(ListView):
    model = Venda
    template_name = 'venda_list.html'
    context_object_name = 'vendas'
    paginate_by = 10

    def get_queryset(self):
        # Este é o "JOIN" (otimizado pelo Django com prefetch_related)
        # 1. Buscamos todas as Vendas
        # 2. Damos 'prefetch' (buscar junto) nos 'itens' de cada venda
        # 3. E também damos 'prefetch' no 'produto' de cada 'item'
        # 4. Ordenamos pelas mais recentes
        return Venda.objects.prefetch_related('itens__produto').order_by('-data')