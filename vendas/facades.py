from decimal import Decimal
from django.db import transaction
from django.db.models import F
from .models import Venda, ItemVenda, Produto

# --- Padrão de Projeto: Facade ---

class VendaFacade:
    """
    Simplifica os processos complexos de 'criar_venda' e 'atualizar_status_venda'.
    """

    def __init__(self):
        self.total_venda_calculado = Decimal('0.00')

    @transaction.atomic
    def _devolver_estoque(self, venda: Venda):
        """Método helper para retornar itens ao estoque."""
        print(f"Devolvendo estoque para Venda {venda.id}")
        itens = venda.itens.all()
        for item in itens:
            # Usamos F() para segurança contra race conditions
            item.produto.estoque = F('estoque') + item.quantidade
            item.produto.save(update_fields=['estoque'])

    @transaction.atomic
    def _retirar_estoque(self, venda: Venda):
        """Método helper para retirar itens do estoque (ao criar ou re-ativar)."""
        print(f"Retirando estoque para Venda {venda.id}")
        itens = venda.itens.all()
        for item in itens:
            # Recarrega o produto para ter o estoque mais atual
            produto = Produto.objects.get(pk=item.produto.pk)
            if produto.estoque < item.quantidade:
                raise Exception(f"Estoque insuficiente para re-ativar venda: {produto.nome}")
            produto.estoque = F('estoque') - item.quantidade
            produto.save(update_fields=['estoque'])

    @transaction.atomic
    def atualizar_status_venda(self, venda: Venda, old_status: str, new_status: str):
        """
        Lida com a lógica de negócio de mudança de status.
        Ex: Devolver estoque se for cancelada.
        """
        # Caso 1: Venda está sendo CANCELADA (e não estava antes)
        if new_status == Venda.StatusVenda.CANCELADA and old_status != Venda.StatusVenda.CANCELADA:
            self._devolver_estoque(venda)
        
        # Caso 2: Venda estava CANCELADA e está sendo re-ativada (ex: PAGA ou PENDENTE)
        elif new_status != Venda.StatusVenda.CANCELADA and old_status == Venda.StatusVenda.CANCELADA:
            # Verifica se há estoque para re-ativar
            self._retirar_estoque(venda)
        
        # Outras transições (ex: PENDENTE -> PAGA) não afetam o estoque.
        return True


    @transaction.atomic 
    def criar_venda(self, venda_form, itens_formset, request_files):
        
        # 1. Salva a Venda principal (mas sem o total ainda)
        venda = venda_form.save(commit=False)
        venda.total = Decimal('0.00') # Total é calculado abaixo
        
        # 2. Adiciona o comprovante (arquivo binário)
        if 'comprovante' in request_files:
            venda.comprovante = request_files['comprovante']
            
        venda.save() # Salva a Venda para obter um ID

        # 3. *** CORREÇÃO DO BUG ***
        # Se a venda já nasce 'Cancelada', não processa itens,
        # não mexe no estoque e o total fica zero.
        if venda.status == Venda.StatusVenda.CANCELADA:
            return venda # Retorna a venda salva com total 0.00

        # --- Se a venda não for cancelada, continua o fluxo normal ---
        
        itens_para_salvar = []
        produtos_para_atualizar_estoque = []

        # 4. Itera sobre os itens do formset
        for form in itens_formset:
            if form.is_valid() and form.cleaned_data:
                produto = form.cleaned_data.get('produto')
                quantidade = form.cleaned_data.get('quantidade')
                
                if produto and quantidade and quantidade > 0:
                    # 5. Verifica estoque
                    if produto.estoque < quantidade:
                        raise Exception(f"Estoque insuficiente para o produto: {produto.nome}")

                    # 6. Calcula o subtotal e o total
                    preco_unitario_venda = produto.preco
                    subtotal = preco_unitario_venda * quantidade
                    self.total_venda_calculado += subtotal

                    # Cria o ItemVenda em memória
                    item = ItemVenda(
                        venda=venda,
                        produto=produto,
                        quantidade=quantidade,
                        preco_unitario=preco_unitario_venda
                    )
                    itens_para_salvar.append(item)

                    # 7. Prepara a baixa de estoque (otimizado)
                    produto.estoque = F('estoque') - quantidade
                    produtos_para_atualizar_estoque.append(produto)

        # 8. Salva os Itens e atualiza o Estoque
        if not itens_para_salvar:
             raise Exception("Uma venda (não cancelada) precisa ter pelo menos um item.")
             
        ItemVenda.objects.bulk_create(itens_para_salvar)
        Produto.objects.bulk_update(produtos_para_atualizar_estoque, ['estoque'])

        # 9. Atualiza a Venda com o total final
        venda.total = self.total_venda_calculado
        venda.save(update_fields=['total'])
        
        return venda