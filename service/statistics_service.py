"""
Statistics Service - Serviço especializado em análise e geração de estatísticas
Responsável por processar dados dos cadastros e gerar análises detalhadas
"""

from typing import List, Dict, Any, Optional
from interface.cli_interface import CLIInterface


class StatisticsService:
    """
    Serviço especializado em análise estatística de dados de cadastros
    Centraliza toda a lógica de cálculos e geração de relatórios estatísticos
    """
    
    def __init__(self):
        """Inicializa o serviço de estatísticas"""
        pass
    
    def gerar_estatisticas_completas(self, cadastros: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Gera estatísticas completas dos cadastros extraídos
        
        Args:
            cadastros: Lista de cadastros para análise
            
        Returns:
            Dicionário com estatísticas completas
        """
        if not cadastros:
            return {'total': 0, 'erro': 'Nenhum cadastro fornecido para análise'}
        
        # Contadores básicos
        stats = {
            'total': len(cadastros),
            'com_proprietarios': 0,
            'com_enderecos': 0,
            'com_area_terreno': 0,
            'com_area_construida': 0,
            'tipos_situacao': {},
            'tipos_categoria': {},
            'zonas': {},
            'area_total_terrenos': 0,
            'area_total_construida': 0,
            'distribuicao_areas': self._analisar_distribuicao_areas(cadastros),
            'qualidade_dados': self._analisar_qualidade_dados(cadastros)
        }
        
        # Processar cada cadastro
        for cadastro in cadastros:
            if isinstance(cadastro, dict):
                self._processar_cadastro_individual(cadastro, stats)
        
        # Cálculos finais
        stats['area_media_terreno'] = (
            stats['area_total_terrenos'] / stats['com_area_terreno'] 
            if stats['com_area_terreno'] > 0 else 0
        )
        
        stats['area_media_construida'] = (
            stats['area_total_construida'] / stats['com_area_construida'] 
            if stats['com_area_construida'] > 0 else 0
        )
        
        return stats
    
    def _processar_cadastro_individual(self, cadastro: Dict[str, Any], stats: Dict[str, Any]):
        """
        Processa um cadastro individual e atualiza as estatísticas
        
        Args:
            cadastro: Dados do cadastro individual
            stats: Dicionário de estatísticas para atualizar
        """
        # Análise de propriedades
        if cadastro.get('proprietariosbci'):
            stats['com_proprietarios'] += 1
        
        if cadastro.get('enderecos'):
            stats['com_enderecos'] += 1
        
        # Análise de áreas
        area_terreno = self._extrair_valor_numerico(cadastro.get('area_terreno'))
        if area_terreno and area_terreno > 0:
            stats['com_area_terreno'] += 1
            stats['area_total_terrenos'] += area_terreno
        
        area_construida = self._extrair_valor_numerico(cadastro.get('area_construida'))
        if area_construida and area_construida > 0:
            stats['com_area_construida'] += 1
            stats['area_total_construida'] += area_construida
        
        # Contagem de situações
        situacao = cadastro.get('situacao', 'Não informado')
        stats['tipos_situacao'][situacao] = stats['tipos_situacao'].get(situacao, 0) + 1
        
        # Contagem de categorias
        categoria = cadastro.get('categoria', 'Não informado')
        stats['tipos_categoria'][categoria] = stats['tipos_categoria'].get(categoria, 0) + 1
        
        # Análise de zoneamentos
        zoneamentos = cadastro.get('zoneamentos', [])
        for zone in zoneamentos:
            if isinstance(zone, dict):
                zona = zone.get('zona', 'Não informado')
                stats['zonas'][zona] = stats['zonas'].get(zona, 0) + 1
    
    def analisar_codigos_cadastro(self, cadastros: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analisa distribuição e características dos códigos de cadastro
        
        Args:
            cadastros: Lista de cadastros para análise
            
        Returns:
            Informações sobre códigos
        """
        if not cadastros:
            CLIInterface.mostrar_erro("Nenhum cadastro fornecido para análise.")
            return {
                'total': 0,
                'menor_codigo': None,
                'maior_codigo': None,
                'intervalo_cobertura': 0,
                'densidade_ocupacao': 0,
                'erro': 'Nenhum cadastro fornecido'
            }
        
        codigos = []
        codigos_invalidos = 0
        
        # Extrair códigos válidos
        for cadastro in cadastros:
            if isinstance(cadastro, dict):
                codigo = cadastro.get('codigo_cadastro')
                if codigo is None:
                    codigos_invalidos += 1
                    continue
                
                try:
                    codigo_int = int(codigo)
                    codigos.append(codigo_int)
                except (ValueError, TypeError):
                    codigos_invalidos += 1
                    continue
        
        if not codigos:
            CLIInterface.mostrar_erro("Nenhum código válido encontrado nos cadastros.")
            return {
                'total': 0,
                'codigos_invalidos': codigos_invalidos,
                'intervalo_cobertura': 0,
                'densidade_ocupacao': 0,
                'erro': 'Nenhum código válido encontrado'
            }
        
        try:
            menor_codigo = min(codigos)
            maior_codigo = max(codigos)
            intervalo_cobertura = maior_codigo - menor_codigo + 1
            densidade_ocupacao = len(codigos) / intervalo_cobertura * 100
            
            # Análise de lacunas
            lacunas = self._analisar_lacunas_codigos(codigos)
            
            return {
                'total': len(codigos),
                'codigos_invalidos': codigos_invalidos,
                'menor_codigo': menor_codigo,
                'maior_codigo': maior_codigo,
                'intervalo_cobertura': intervalo_cobertura,
                'densidade_ocupacao': densidade_ocupacao,
                'codigos_unicos': len(set(codigos)),
                'duplicados': len(codigos) - len(set(codigos)),
                'lacunas': lacunas
            }
            
        except ValueError as e:
            CLIInterface.mostrar_erro(f"Erro ao calcular estatísticas de códigos: {e}")
            return {
                'total': len(codigos),
                'codigos_invalidos': codigos_invalidos,
                'menor_codigo': None,
                'maior_codigo': None,
                'intervalo_cobertura': 0,
                'densidade_ocupacao': 0,
                'erro': str(e)
            }
    
    def _analisar_lacunas_codigos(self, codigos: List[int]) -> Dict[str, Any]:
        """
        Analisa lacunas na sequência de códigos
        
        Args:
            codigos: Lista de códigos para análise
            
        Returns:
            Informações sobre lacunas encontradas
        """
        if not codigos:
            return {'total_lacunas': 0, 'maiores_lacunas': []}
        
        codigos_ordenados = sorted(set(codigos))
        lacunas = []
        
        for i in range(len(codigos_ordenados) - 1):
            atual = codigos_ordenados[i]
            proximo = codigos_ordenados[i + 1]
            
            if proximo - atual > 1:
                lacuna = {
                    'inicio': atual + 1,
                    'fim': proximo - 1,
                    'tamanho': proximo - atual - 1
                }
                lacunas.append(lacuna)
        
        # Ordenar por tamanho (maiores primeiro)
        lacunas_ordenadas = sorted(lacunas, key=lambda x: x['tamanho'], reverse=True)
        
        return {
            'total_lacunas': len(lacunas),
            'maiores_lacunas': lacunas_ordenadas[:10],  # Top 10 maiores lacunas
            'lacuna_media': sum(l['tamanho'] for l in lacunas) / len(lacunas) if lacunas else 0
        }
    
    def _analisar_distribuicao_areas(self, cadastros: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analisa distribuição das áreas dos cadastros
        
        Args:
            cadastros: Lista de cadastros para análise
            
        Returns:
            Estatísticas de distribuição de áreas
        """
        areas_terreno = []
        areas_construida = []
        
        for cadastro in cadastros:
            if isinstance(cadastro, dict):
                area_terreno = self._extrair_valor_numerico(cadastro.get('area_terreno'))
                if area_terreno and area_terreno > 0:
                    areas_terreno.append(area_terreno)
                
                area_construida = self._extrair_valor_numerico(cadastro.get('area_construida'))
                if area_construida and area_construida > 0:
                    areas_construida.append(area_construida)
        
        return {
            'terreno': self._calcular_estatisticas_lista(areas_terreno),
            'construida': self._calcular_estatisticas_lista(areas_construida)
        }
    
    def _calcular_estatisticas_lista(self, valores: List[float]) -> Dict[str, Any]:
        """
        Calcula estatísticas básicas de uma lista de valores
        
        Args:
            valores: Lista de valores numéricos
            
        Returns:
            Estatísticas calculadas
        """
        if not valores:
            return {
                'count': 0,
                'min': 0,
                'max': 0,
                'media': 0,
                'mediana': 0
            }
        
        valores_ordenados = sorted(valores)
        n = len(valores)
        
        return {
            'count': n,
            'min': min(valores),
            'max': max(valores),
            'media': sum(valores) / n,
            'mediana': (
                valores_ordenados[n // 2] if n % 2 == 1
                else (valores_ordenados[n // 2 - 1] + valores_ordenados[n // 2]) / 2
            )
        }
    
    def _analisar_qualidade_dados(self, cadastros: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analisa qualidade dos dados dos cadastros
        
        Args:
            cadastros: Lista de cadastros para análise
            
        Returns:
            Métricas de qualidade dos dados
        """
        total = len(cadastros)
        campos_obrigatorios = ['codigo_cadastro', 'tipo_cadastro', 'situacao']
        campos_importantes = ['area_terreno', 'area_construida', 'enderecos', 'proprietariosbci']
        
        qualidade = {
            'total_cadastros': total,
            'campos_obrigatorios_completos': 0,
            'campos_importantes_completos': 0,
            'percentual_completude_obrigatorios': 0.0,
            'percentual_completude_importantes': 0.0,
            'cadastros_completos': 0
        }
        
        for cadastro in cadastros:
            if not isinstance(cadastro, dict):
                continue
            
            # Verificar campos obrigatórios
            campos_obrig_ok = all(
                cadastro.get(campo) is not None and str(cadastro.get(campo)).strip() != ""
                for campo in campos_obrigatorios
            )
            
            if campos_obrig_ok:
                qualidade['campos_obrigatorios_completos'] += 1
            
            # Verificar campos importantes
            campos_import_ok = True
            for campo in campos_importantes:
                valor = cadastro.get(campo)
                if valor is None:
                    campos_import_ok = False
                    break
                
                if isinstance(valor, str):
                    if valor.strip() == "":
                        campos_import_ok = False
                        break
                elif isinstance(valor, list):
                    if len(valor) == 0:
                        campos_import_ok = False
                        break
                elif isinstance(valor, (int, float)):
                    if valor <= 0:
                        campos_import_ok = False
                        break
            
            if campos_import_ok:
                qualidade['campos_importantes_completos'] += 1
            
            # Cadastro considerado completo
            if campos_obrig_ok and campos_import_ok:
                qualidade['cadastros_completos'] += 1
        
        # Calcular percentuais
        if total > 0:
            qualidade['percentual_completude_obrigatorios'] = (
                qualidade['campos_obrigatorios_completos'] / total * 100
            )
            qualidade['percentual_completude_importantes'] = (
                qualidade['campos_importantes_completos'] / total * 100
            )
            qualidade['percentual_completude_geral'] = (
                qualidade['cadastros_completos'] / total * 100
            )
        
        return qualidade
    
    def _extrair_valor_numerico(self, valor: Any) -> Optional[float]:
        """
        Extrai valor numérico de diferentes tipos de entrada
        
        Args:
            valor: Valor para converter
            
        Returns:
            Valor numérico ou None se conversão falhar
        """
        if valor is None:
            return None
        
        if isinstance(valor, (int, float)):
            return float(valor)
        
        if isinstance(valor, str):
            try:
                # Substituir vírgula por ponto se necessário
                valor_normalizado = valor.replace(',', '.')
                return float(valor_normalizado)
            except ValueError:
                return None
        
        return None
    
    def gerar_relatorio_resumido(self, cadastros: List[Dict[str, Any]]) -> str:
        """
        Gera relatório textual resumido das estatísticas
        
        Args:
            cadastros: Lista de cadastros para análise
            
        Returns:
            String com relatório formatado
        """
        stats = self.gerar_estatisticas_completas(cadastros)
        codigos_info = self.analisar_codigos_cadastro(cadastros)
        
        relatorio = []
        relatorio.append("📊 RELATÓRIO ESTATÍSTICO DE CADASTROS")
        relatorio.append("=" * 50)
        relatorio.append(f"Total de cadastros analisados: {stats['total']}")
        relatorio.append("")
        
        # Informações de código
        if 'erro' not in codigos_info:
            relatorio.append("🔢 Análise de Códigos:")
            relatorio.append(f"  • Menor código: {codigos_info['menor_codigo']}")
            relatorio.append(f"  • Maior código: {codigos_info['maior_codigo']}")
            relatorio.append(f"  • Densidade: {codigos_info['densidade_ocupacao']:.1f}%")
            relatorio.append(f"  • Duplicados: {codigos_info['duplicados']}")
            relatorio.append("")
        
        # Qualidade dos dados
        qualidade = stats.get('qualidade_dados', {})
        if qualidade:
            relatorio.append("✅ Qualidade dos Dados:")
            relatorio.append(f"  • Completude geral: {qualidade.get('percentual_completude_geral', 0):.1f}%")
            relatorio.append(f"  • Cadastros completos: {qualidade.get('cadastros_completos', 0)}")
            relatorio.append("")
        
        # Distribuição de áreas
        dist_areas = stats.get('distribuicao_areas', {})
        if dist_areas.get('terreno', {}).get('count', 0) > 0:
            terreno = dist_areas['terreno']
            relatorio.append("🏞️ Áreas de Terreno:")
            relatorio.append(f"  • Média: {terreno['media']:.2f} m²")
            relatorio.append(f"  • Mínima: {terreno['min']:.2f} m²")
            relatorio.append(f"  • Máxima: {terreno['max']:.2f} m²")
            relatorio.append("")
        
        return "\n".join(relatorio)
