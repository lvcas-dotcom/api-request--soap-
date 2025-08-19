#!/usr/bin/env python3
"""
Sistema de Extração de Cadastros Imobiliários
Clevelandia Municipal - Sistema Completo
"""

from service.cadastro_service import CadastroService
from controller.database_controller import DatabaseController
from interface.cli_interface import CLIInterface
from interface.styles.colors import Colors
from interface.styles.ascii_art import *
import time


def main():
    """Função principal com interface estilizada completa"""

    # Animação de abertura estilizada
    CLIInterface.animacao_inicio()

    # Loop principal do menu
    while True:
        # Mostrar menu e obter escolha
        escolha = CLIInterface.mostrar_menu()

        if escolha == "sair":
            break
        elif escolha == "extrair":
            executar_extracao()
        elif escolha == "banco":
            executar_operacoes_banco()


def executar_operacoes_banco():
    """Executa operações relacionadas ao banco de dados"""

    try:
        # Criar controlador de banco
        db_controller = DatabaseController()

        while True:
            # Mostrar menu ASCII estilizado
            print(Colors.menu(DATABASE_MENU_ASCII))

            escolha = input(f"\n{Colors.progress('🔹 Escolha uma opção: ')}")

            if escolha == "0":
                break
            elif escolha == "1":
                db_controller.testar_conexao_banco()
            elif escolha == "2":
                db_controller.inicializar_banco()
            elif escolha == "3":
                db_controller.processar_arquivo_json_para_banco()
            elif escolha == "4":
                db_controller.executar_workflow_completo()
            elif escolha == "5":
                db_controller.obter_estatisticas_banco()
            elif escolha == "6":
                db_controller.listar_arquivos_disponiveis()
            else:
                print(Colors.error("❌ Opção inválida!"))

            # Pausa entre operações
            input(f"\n{Colors.info('📝 Pressione ENTER para continuar...')}")

    except Exception as e:
        CLIInterface.mostrar_erro(f"Erro nas operações de banco: {e}")


def executar_extracao():
    """Executa a extração completa com interface visual"""

    # Animação de carregamento inicial
    CLIInterface.loading_spinner("Inicializando sistema", 2)

    try:
        # Mostrar início da extração
        CLIInterface.mostrar_inicio_extracao()

        # Animação de carregamento dos serviços
        print(Colors.info("🔧 Carregando serviços..."))
        CLIInterface.loading_spinner("Carregando módulos", 1)

        # Criar serviço
        servico = CadastroService()
        print(Colors.success("✅ Conexão com API estabelecida"))

        # Confirmação visual
        print(f"\n{Colors.progress('🚀 Iniciando Processamento...')}")
        CLIInterface.loading_spinner("Preparando extração", 2)

        print(f"\n{Colors.header('=' * 60)}")
        print(Colors.progress("                 🔥 PROCESSAMENTO INICIADO!"))
        print(Colors.header("=" * 60))

        # Executar extração (MÉTODO CORRETO)
        resultados = servico.extrair_completo()

        # Processar resultado
        if resultados:
            mostrar_resultado_sucesso(resultados)
        else:
            mostrar_resultado_erro({"erro": "Falha desconhecida"})

    except KeyboardInterrupt:
        print(f"\n{Colors.warning('⚠️  Extração interrompida pelo usuário')}")
        CLIInterface.loading_spinner("Finalizando", 1)
    except Exception as e:
        CLIInterface.mostrar_erro(f"Erro inesperado: {str(e)}")

    # Pausa antes de voltar ao menu
    print(f"\n{Colors.info(SEPARATOR_THIN)}")
    input(Colors.menu("🔹 Pressione ENTER para voltar ao menu principal..."))


def mostrar_resultado_sucesso(resultados):
    """Exibe resultado de sucesso com animações"""

    # Animação de conclusão
    CLIInterface.loading_spinner("Finalizando", 2)

    print(Colors.success(CONCLUSION_ASCII))
    print(Colors.stats("📊 EXTRAÇÃO FINALIZADA COM SUCESSO!"))
    print(Colors.stats(SEPARATOR_THICK))

    # Criar barra de progresso de 100%
    barra_completa = Colors.success(PROGRESS_BAR_FULL * 40)
    print(f"[{barra_completa}] {Colors.stats('100.0%')} - CONCLUÍDO")

    print(f"\n{Colors.info('📈 ARQUIVOS GERADOS:')}")
    for nome, caminho in resultados.items():
        if caminho:
            print(f"  ✔ {nome}.json → {Colors.success(caminho)}")
        else:
            print(f"  ✖ {nome}.json não foi salvo")


def mostrar_resultado_erro(resultado):
    """Exibe resultado de erro com formatação"""

    erro = (
        resultado.get("erro", "Erro desconhecido") if resultado else "Falha na extração"
    )

    print(Colors.error("❌ ERRO NA EXTRAÇÃO"))
    print(Colors.error(SEPARATOR_THIN))
    print(f"   {Colors.warning(str(erro))}")

    # Verificar se há dados parciais
    if resultado and resultado.get("cadastros"):
        total_parcial = len(resultado["cadastros"])
        arquivo_parcial = resultado.get("arquivo_salvo")

        print(f"\n{Colors.warning('⚠️  DADOS PARCIAIS SALVOS:')}")
        print(
            f"  {ICONS['data']} Extraídos: {Colors.info(str(total_parcial))} cadastros"
        )
        if arquivo_parcial:
            print(f"  {ICONS['save']} Arquivo: {Colors.info(arquivo_parcial)}")


if __name__ == "__main__":
    main()
