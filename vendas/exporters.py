import json
from abc import ABC, abstractmethod
from dicttoxml import dicttoxml
from xml.dom.minidom import parseString
from django.db.models import QuerySet
from django.http import HttpResponse

# --- Padrão de Projeto: Factory Method ---

# Interface (Produto Abstrato)
class BaseExporter(ABC):
    """
    Interface para diferentes tipos de exportadores.
    Define o método 'export' que todas as classes concretas devem implementar.
    """
    def __init__(self, queryset: QuerySet):
        self.queryset = queryset

    @abstractmethod
    def export(self) -> HttpResponse:
        pass

    def get_data_to_export(self) -> list:
        """Helper que transforma o queryset do Django em uma lista de dicionários."""
        return list(self.queryset.values(
            'id', 
            'nome', 
            'descricao', 
            'categoria__nome', 
            'preco', 
            'estoque'
        ))

# Produto Concreto 1: JSON
class JsonExporter(BaseExporter):
    """Exporta os dados como um arquivo JSON."""
    
    def export(self) -> HttpResponse:
        data = self.get_data_to_export()
        json_data = json.dumps(data, indent=4, ensure_ascii=False, default=str)
        
        response = HttpResponse(json_data, content_type='application/json')
        response['Content-Disposition'] = 'attachment; filename="produtos.json"'
        return response

# Produto Concreto 2: XML
class XmlExporter(BaseExporter):
    """Exporta os dados como um arquivo XML."""

    def export(self) -> HttpResponse:
        data = self.get_data_to_export()
        
        # Usamos a biblioteca dicttoxml para converter a lista de dicts
        # O 'custom_root' será <produtos>, e cada item será <produto>
        xml_data = dicttoxml(data, custom_root='produtos', item_func=lambda x: 'produto')
        
        # Deixa o XML bonito (com indentação)
        dom = parseString(xml_data)
        pretty_xml = dom.toprettyxml(indent="  ")
        
        response = HttpResponse(pretty_xml, content_type='application/xml')
        response['Content-Disposition'] = 'attachment; filename="produtos.xml"'
        return response

# Produto Concreto 3: TXT (Relatório Simples)
class TxtExporter(BaseExporter):
    """Exporta os dados como um relatório simples em .txt."""

    def export(self) -> HttpResponse:
        data = self.get_data_to_export()
        
        report_lines = []
        report_lines.append("RELATÓRIO DE PRODUTOS\n")
        report_lines.append("="*40 + "\n\n")
        
        total_estoque = 0
        total_valor_estoque = 0
        
        for item in data:
            preco = item.get('preco', 0)
            estoque = item.get('estoque', 0)
            valor_item = (preco or 0) * (estoque or 0)
            
            report_lines.append(f"ID:       {item.get('id')}")
            report_lines.append(f"Nome:     {item.get('nome')}")
            report_lines.append(f"Categoria:{item.get('categoria__nome', '-')}")
            report_lines.append(f"Preço:    R$ {preco:.2f}")
            report_lines.append(f"Estoque:  {estoque} unidades")
            report_lines.append(f"Subtotal: R$ {valor_item:.2f}")
            report_lines.append("-"*40 + "\n")
            
            total_estoque += estoque
            total_valor_estoque += valor_item

        report_lines.append("\n" + "="*40)
        report_lines.append("RESUMO DO RELATÓRIO\n")
        report_lines.append(f"Total de Itens:   {len(data)}")
        report_lines.append(f"Total em Estoque: {total_estoque} unidades")
        report_lines.append(f"Valor Total:      R$ {total_valor_estoque:.2f}")
        report_lines.append("="*40)
        
        report_content = "\n".join(report_lines)
        
        response = HttpResponse(report_content, content_type='text/plain; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="relatorio_produtos.txt"'
        return response

# O Criador (Factory)
class ExporterFactory:
    """
    A Fábrica (Factory) que decide qual exportador concreto instanciar.
    """
    exporters = {
        'json': JsonExporter,
        'xml': XmlExporter,
        'txt': TxtExporter,
    }

    def get_exporter(self, format: str, queryset: QuerySet) -> BaseExporter:
        """
        O "Factory Method".
        Recebe o formato e o queryset, e retorna a instância correta.
        """
        exporter_class = self.exporters.get(format)
        
        if not exporter_class:
            raise ValueError(f"Formato de exportação desconhecido: {format}")
            
        return exporter_class(queryset)