"""
CLI Interface - Interface de linha de comando estilizada
Responsável por toda a apresentação visual e interação com usuário
"""

import time
import sys
from datetime import datetime
from .styles.colors import Colors
from .styles.ascii_art import *


class CLIInterface:
    @staticmethod
    def animacao_inicio():
        """Animação de abertura: header, texto digitando e barra de progresso fake, depois limpa terminal"""
        import sys
        import time
        import os
        from interface.styles.ascii_art import HEADER_ASCII, PROGRESS_BAR_FULL, PROGRESS_BAR_EMPTY
        from interface.styles.colors import Colors

        # Mostrar header
        print(Colors.header(HEADER_ASCII))
        time.sleep(0.5)


        # Mostrar texto direto
        print(Colors.progress("\nCarregando aplicação..."))

        # Barra de progresso fake
        total = 30
        for i in range(total+1):
            barra = Colors.success(PROGRESS_BAR_FULL * i) + Colors.warning(PROGRESS_BAR_EMPTY * (total - i))
            print(f"\r[{barra}] {Colors.stats(f'{(i/total)*100:5.1f}%')}", end="", flush=True)
            time.sleep(0.04 + (0.12 if i < 5 else 0))
        print("\n")
        time.sleep(0.3)

        # Limpar terminal (cross-platform)
        if os.name == 'nt':
            os.system('cls')
        else:
            os.system('clear')
    """Interface de linha de comando com elementos visuais estilizados"""

    @staticmethod
    def mostrar_header():
        """Exibe cabeçalho principal do sistema"""
        print(Colors.header(HEADER_ASCII))

    @staticmethod
    def mostrar_menu():
        """Exibe menu principal com opções"""
        print(Colors.menu(MENU_ASCII))

        while True:
            try:
                escolha = input(Colors.info("🔹 Digite sua opção: ")).strip()

                if escolha == "1":
                    return "extrair"
                elif escolha == "2":
                    return "banco"
                elif escolha == "0":
                    print(Colors.warning("👋 Saindo do sistema..."))
                    return "sair"
                else:
                    print(Colors.error("❌ Opção inválida! Digite 1, 2 ou 0."))
            except KeyboardInterrupt:
                print(Colors.warning("\n👋 Saindo do sistema..."))
                return "sair"

    @staticmethod
    def mostrar_inicio_extracao():
        """Exibe informações de início da extração"""
        print(Colors.info(SEPARATOR_THIN))

    @staticmethod
    def mostrar_progresso_inicial(total_intervalos):
        """Exibe informações iniciais do progresso"""
        print(Colors.info(f"⚙️  Paginação (0-100, 101-200...)"))
        print(Colors.warning("⏳ Este processo pode demorar"))

    @staticmethod
    def mostrar_progresso_intervalo(atual, total, inicio, fim, cadastros_encontrados):
        """Exibe progresso do intervalo atual com barra visual"""
        porcentagem = (atual / total) * 100

        # Barra de progresso colorida
        progresso_cheio = int(porcentagem // 2.5)  # 40 caracteres max
        barra_colorida = (
            Colors.success(PROGRESS_BAR_FULL * progresso_cheio) +
            Colors.warning(PROGRESS_BAR_EMPTY * (40 - progresso_cheio))
        )

        # Status line
        status = f"[{barra_colorida}] {Colors.stats(f'{porcentagem:5.1f}%')} | "
        status += f"Intervalo {Colors.info(f'{inicio}-{fim}')}: "
        status += Colors.success(f"{cadastros_encontrados} cadastros")

        print(f"\r{status}", end="", flush=True)

    @staticmethod
    def mostrar_progresso_banco(atual, total, operacao="Processando"):
        """Exibe progresso de operações de banco com barra visual"""
        porcentagem = (atual / total) * 100

        # Barra de progresso colorida (40 caracteres max)
        progresso_cheio = int(porcentagem // 2.5)
        barra_colorida = (
            Colors.success(PROGRESS_BAR_FULL * progresso_cheio) +
            Colors.warning(PROGRESS_BAR_EMPTY * (40 - progresso_cheio))
        )

        # Status line com cores apropriadas
        status = f"[{barra_colorida}] {Colors.success(f'{porcentagem:5.1f}%')} | "
        status += f"{Colors.info(operacao)}: {Colors.success(f'{atual}/{total}')}"

        print(f"\r{status}", end="", flush=True)

    @staticmethod
    def mostrar_resultado_lote(total_acumulado, total_requisicoes):
        """Exibe resultado acumulado de forma limpa"""
        print(f"\n{Colors.success('✅')} Total acumulado: {Colors.stats(str(total_acumulado))} cadastros " +
              f"({Colors.info(str(total_requisicoes))} requisições)")

    @staticmethod
    def mostrar_salvamento_progresso():
        """Exibe informação sobre salvamento de progresso"""
        print(f"    {Colors.warning('💾 Backup automático salvo')}")

    @staticmethod
    def mostrar_conclusao(total_cadastros, total_requisicoes, tempo_execucao):
        """Exibe informações de conclusão"""
        print(f"\n{Colors.success(CONCLUSION_ASCII)}")

        print(Colors.stats("📊 RESULTADOS FINAIS:"))
        print(Colors.stats(SEPARATOR_THIN))
        print(f"  {ICONS['data']} Total extraído: {Colors.success(str(total_cadastros))} cadastros")
        print(f"  {ICONS['gear']} Requisições: {Colors.info(str(total_requisicoes))}")
        print(f"  {ICONS['time']} Tempo total: {Colors.warning(str(tempo_execucao))}")
        print(f"  {ICONS['save']} Dados salvos com metadados completos")

    @staticmethod
    def mostrar_estatisticas(stats, codigos_info=None):
        """Exibe estatísticas detalhadas dos dados extraídos"""
        print(f"\n{Colors.stats('📊 ANÁLISE DOS DADOS EXTRAÍDOS')}")
        print(Colors.stats(SEPARATOR_THIN))

        print(f"📋 Total processado: {Colors.success(str(stats['total']))} cadastros")

        if codigos_info:
            print(f"\n🔢 Análise de códigos:")
            print(f"  • Menor código: {Colors.info(str(codigos_info.get('menor_codigo', 'N/A')))}")
            print(f"  • Maior código: {Colors.info(str(codigos_info.get('maior_codigo', 'N/A')))}")
            print(f"  • Códigos únicos: {Colors.success(str(codigos_info.get('codigos_unicos', codigos_info.get('total', 'N/A'))))}")
            densidade = codigos_info.get('densidade_ocupacao', 0)
            densidade_txt = f"{densidade:.1f}%"
            print(f"  • Densidade: {Colors.warning(densidade_txt)}")

        if stats.get('tipos_categoria'):
            print(f"\n🏷️ Distribuição por categoria:")
            for categoria, count in stats['tipos_categoria'].items():
                print(f"  • Categoria {Colors.info(str(categoria))}: {Colors.success(str(count))} cadastros")

        if stats.get('tipos_situacao'):
            print(f"\n📈 Situações cadastrais:")
            for situacao, count in stats['tipos_situacao'].items():
                print(f"  • Situação {Colors.info(str(situacao))}: {Colors.success(str(count))} cadastros")

    @staticmethod
    def mostrar_amostra_dados(cadastros, limite=3):
        """Exibe amostra dos dados extraídos"""
        print(f"\n{Colors.info('🔍 AMOSTRA DOS DADOS')}")
        print(Colors.info(SEPARATOR_THIN))

        for i, cadastro in enumerate(cadastros[:limite]):
            codigo = cadastro.get('codigo_cadastro', 'N/A')
            situacao = cadastro.get('situacao_cadastral', 'N/A')
            data_cadastro = cadastro.get('data_cadastro', 'N/A')

            print(f"  📄 Cadastro {i+1}:")
            print(f"    • Código: {Colors.success(str(codigo))}")
            print(f"    • Situação: {Colors.info(str(situacao))}")
            print(f"    • Data: {Colors.warning(str(data_cadastro))}")

        if len(cadastros) > limite:
            print(Colors.info(f"  ... e mais {len(cadastros) - limite} cadastros"))

    @staticmethod
    def mostrar_arquivo_salvo(filepath):
        """Exibe informação sobre arquivo salvo"""
        print(f"\n{Colors.success('💾 ARQUIVO SALVO:')}")
        print(f"  📁 Local: {Colors.info(filepath)}")

    @staticmethod
    def mostrar_erro(mensagem):
        """Exibe mensagem de erro formatada"""
        print(Colors.error(f"❌ ERRO: {mensagem}"))

    @staticmethod
    def mostrar_aviso(mensagem):
        """Exibe mensagem de aviso formatada"""
        print(Colors.warning(f"⚠️  {mensagem}"))

    @staticmethod
    def loading_spinner(texto="Processando", duracao=2):
        """Exibe spinner de loading estilizado"""
        for i in range(duracao * 10):
            frame = LOADING_FRAMES[i % len(LOADING_FRAMES)]
            print(f"\r{Colors.progress(f'{frame} {texto}...')}", end="", flush=True)
            time.sleep(0.1)
        print(f"\r{' ' * 50}\r", end="")


class ProgressTracker:
    """Classe para tracking de progresso detalhado"""

    def __init__(self, total_intervalos):
        self.total_intervalos = total_intervalos
        self.intervalos_processados = 0
        self.cadastros_totais = 0
        self.inicio_tempo = datetime.now()
        self.requisicoes_realizadas = 0

    def atualizar_intervalo(self, cadastros_encontrados):
        """Atualiza progresso do intervalo atual"""
        self.intervalos_processados += 1
        self.cadastros_totais += cadastros_encontrados
        self.requisicoes_realizadas += 1

    def obter_tempo_decorrido(self):
        """Retorna tempo decorrido desde o início"""
        return datetime.now() - self.inicio_tempo

    def obter_progresso_percentual(self):
        """Retorna progresso em percentual"""
        return (self.intervalos_processados / self.total_intervalos) * 100
