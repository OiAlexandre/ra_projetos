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
    
    # --- NOVO CAMPO (REQUISITO PDF MODELAGEM) --- 
    class StatusVenda(models.TextChoices):
        PENDENTE = 'PENDENTE', 'Pendente'
        PAGA = 'PAGA', 'Paga'
        CANCELADA = 'CANCELADA', 'Cancelada'
    # ---------------------------------------------

    data = models.DateTimeField(default=timezone.now)
    cliente = models.CharField(max_length=200) 
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Requisito: Armazenar ao menos um arquivo binário [cite: 44]
    comprovante = models.FileField(upload_to='comprovantes_venda/', blank=True, null=True)

    # --- NOVO CAMPO (REQUISITO PDF MODELAGEM) --- 
    status = models.CharField(
        max_length=10,
        choices=StatusVenda.choices,
        default=StatusVenda.PENDENTE,
        verbose_name="Status"
    )
    # ---------------------------------------------

    class Meta:
        verbose_name = "Venda"
        verbose_name_plural = "Vendas"

    # --- __str__ ATUALIZADO ---
    def __str__(self):
        # Usamos o .get_status_display() para pegar o "label" (ex: "Pendente")
        return f"Venda {self.id} - {self.cliente} ({self.get_status_display()})"
    
    def calcular_total(self):
        pass

# Modelo ItemVenda (Tabela associativa para N-N entre Venda e Produto)
class ItemVenda(models.Model):
    # Requisito: Relacionamento N-N [cite: 47]
    venda = models.ForeignKey(Venda, on_delete=models.CASCADE, related_name='itens')
    produto = models.ForeignKey(Produto, on_delete=models.PROTECT) 
    quantidade = models.PositiveIntegerField()
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2) 

    class Meta:
        verbose_name = "Item da Venda"
        verbose_name_plural = "Itens da Venda"
        unique_together = ('venda', 'produto') 

    def __str__(self):
        return f"{self.quantidade} x {self.produto.nome} (Venda {self.venda.id})"