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

    # --- URLs do CRUD de Vendas ---
    path('vendas/', views.VendaListView.as_view(), name='venda_list'),
    path('vendas/nova/', views.VendaCreateView.as_view(), name='venda_create'),
    # (NOVO) URL de Edição de Venda
    path('vendas/<int:pk>/editar/', views.VendaUpdateView.as_view(), name='venda_update'),
]