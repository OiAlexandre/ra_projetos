from django.urls import path
from . import views

urlpatterns = [
    # URL da Home
    path('', views.home, name='home'),

    # --- URLs do CRUD de Produtos ---
    path('produtos/', views.ProdutoListView.as_view(), name='produto_list'),
    path('produtos/novo/', views.ProdutoCreateView.as_view(), name='produto_create'),
    path('produtos/<int:pk>/editar/', views.ProdutoUpdateView.as_view(), name='produto_update'),
    path('produtos/<int:pk>/deletar/', views.ProdutoDeleteView.as_view(), name='produto_delete'),
    path('produtos/export/', views.export_produtos, name='produto_export'),
    path('produtos/import/', views.import_produtos, name='produto_import'),

    # --- (NOVO) URLs do CRUD de Categorias ---
    path('categorias/', views.CategoriaListView.as_view(), name='categoria_list'),
    path('categorias/nova/', views.CategoriaCreateView.as_view(), name='categoria_create'),
    path('categorias/<int:pk>/editar/', views.CategoriaUpdateView.as_view(), name='categoria_update'),
    path('categorias/<int:pk>/deletar/', views.CategoriaDeleteView.as_view(), name='categoria_delete'),

    # --- URLs do CRUD de Vendas ---
    path('vendas/', views.VendaListView.as_view(), name='venda_list'),
    path('vendas/nova/', views.VendaCreateView.as_view(), name='venda_create'),
    path('vendas/<int:pk>/editar/', views.VendaUpdateView.as_view(), name='venda_update'),
]