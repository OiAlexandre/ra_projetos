from django.db import models
from django.utils import timezone

# Modelo Categoria (Relacionamento 1-N com Produto)
class Categoria(models.Model):
    nome = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"

    def __str__(self):
        return self.nome

# Modelo Produto
class Produto(models.Model):
    # Requisito: Índice em campo de busca frequente
    nome = models.CharField(max_length=200, db_index=True)
    descricao = models.TextField(blank=True, null=True)
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    estoque = models.PositiveIntegerField(default=0)
    # Requisito: Relacionamento 1-N
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True, related_name='produtos')
    
    class Meta:
        verbose_name = "Produto"
        verbose_name_plural = "Produtos"

    def __str__(self):
        return self.nome

# Modelo Venda
class Venda(models.Model):
    data = models.DateTimeField(default=timezone.now)
    # Simplificado para não precisar de um modelo Cliente complexo
    cliente = models.CharField(max_length=200) 
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Requisito: Armazenar ao menos um arquivo binário
    # Vamos usar FileField para aceitar PDF, imagens, etc.
    comprovante = models.FileField(upload_to='comprovantes_venda/', blank=True, null=True)

    class Meta:
        verbose_name = "Venda"
        verbose_name_plural = "Vendas"

    def __str__(self):
        return f"Venda {self.id} - {self.cliente} em {self.data.strftime('%d/%m/%Y')}"
    
    # Futuramente, podemos ter um método para calcular o total
    def calcular_total(self):
        # Esta função será implementada depois, quando tivermos as views
        pass

# Modelo ItemVenda (Tabela associativa para N-N entre Venda e Produto)
class ItemVenda(models.Model):
    # Requisito: Relacionamento N-N (Venda <-> Produto)
    venda = models.ForeignKey(Venda, on_delete=models.CASCADE, related_name='itens')
    produto = models.ForeignKey(Produto, on_delete=models.PROTECT) # Evita deletar produto se ele estiver em uma venda
    quantidade = models.PositiveIntegerField()
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2) # Guarda o preço no momento da venda

    class Meta:
        verbose_name = "Item da Venda"
        verbose_name_plural = "Itens da Venda"
        unique_together = ('venda', 'produto') # Evita adicionar o mesmo produto duas vezes na mesma venda

    def __str__(self):
        return f"{self.quantidade} x {self.produto.nome} (Venda {self.venda.id})"
