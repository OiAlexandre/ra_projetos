from django import forms
from django.forms import inlineformset_factory
from .models import Produto, Categoria, Venda, ItemVenda

# --- Formulário de Produto (sem alteração) ---
class ProdutoForm(forms.ModelForm):
    categoria = forms.ModelChoiceField(
        queryset=Categoria.objects.all(),
        required=False,
        empty_label="Sem Categoria",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    class Meta:
        model = Produto
        fields = ['nome', 'descricao', 'categoria', 'preco', 'estoque']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome do produto'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'preco': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'estoque': forms.NumberInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'nome': 'Nome do Produto',
            'descricao': 'Descrição',
            'preco': 'Preço (R$)',
            'estoque': 'Quantidade em Estoque',
        }

# --- Formulários de Venda (sem alteração) ---
class VendaForm(forms.ModelForm):
    class Meta:
        model = Venda
        fields = ['cliente', 'status', 'comprovante']
        widgets = {
            'cliente': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome do cliente'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'comprovante': forms.FileInput(attrs={'class': 'form-control-file'}),
        }

class ItemVendaForm(forms.ModelForm):
    produto = forms.ModelChoiceField(
        queryset=Produto.objects.filter(estoque__gt=0).order_by('nome'),
        widget=forms.Select(attrs={'class': 'form-control select2'}), 
        required=True
    )
    class Meta:
        model = ItemVenda
        fields = ['produto', 'quantidade']
        widgets = {
            'quantidade': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'value': '1'}),
        }
    def clean(self):
        cleaned_data = super().clean()
        produto = cleaned_data.get('produto')
        quantidade = cleaned_data.get('quantidade')
        if produto and quantidade:
            if quantidade > produto.estoque:
                error_msg = f"Estoque insuficiente! Disponível: {produto.estoque}"
                self.add_error('quantidade', forms.ValidationError(error_msg))
        return cleaned_data

ItemVendaFormSet = inlineformset_factory(
    Venda,
    ItemVenda,
    form=ItemVendaForm,
    extra=0,
    can_delete=True,
    min_num=1,
    validate_min=True,
)

# --- (NOVO) Formulário de Categoria ---
class CategoriaForm(forms.ModelForm):
    """Formulário para Criar/Editar uma Categoria."""
    class Meta:
        model = Categoria
        fields = ['nome']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome da categoria'}),
        }