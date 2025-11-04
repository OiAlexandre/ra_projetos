from django.contrib import admin
from .models import Categoria, Produto, Venda, ItemVenda

# Para permitir adicionar Itens de Venda dentro da Venda
class ItemVendaInline(admin.TabularInline):
    model = ItemVenda
    extra = 1 # Quantos campos extras de item de venda aparecem por padrão
    # Podemos tornar campos readonly após a criação, se necessário
    # readonly_fields = ('preco_unitario',) 

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nome',)
    search_fields = ('nome',)

@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'categoria', 'preco', 'estoque')
    list_filter = ('categoria',)
    search_fields = ('nome', 'descricao')
    list_editable = ('preco', 'estoque') # Permite editar direto na lista

@admin.register(Venda)
class VendaAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'data', 'total', 'comprovante')
    list_filter = ('data',)
    search_fields = ('cliente', 'id')
    inlines = [ItemVendaInline] # Adiciona os itens de venda na página da venda

    # Futuramente, podemos adicionar um campo readonly para o total calculado
    # readonly_fields = ('total',) 

@admin.register(ItemVenda)
class ItemVendaAdmin(admin.ModelAdmin):
    list_display = ('venda', 'produto', 'quantidade', 'preco_unitario')
    list_filter = ('produto', 'venda__data')
    search_fields = ('produto__nome', 'venda__cliente')
