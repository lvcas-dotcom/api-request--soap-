#!/usr/bin/env python3
"""
Sistema de Extração de Cadastros Imobiliários
Clevelandia Municipal - Sistema Completo
"""

from service.cadastro_service import CadastroService
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
            print(Colors.success("👋 Obrigado por usar o sistema!"))
            break
        elif escolha == "extrair":
            executar_extracao()
    
    # Despedida final
    print(Colors.header("\n" + SEPARATOR_THICK))
    print(Colors.success("🚀 Até logo!"))
    print(Colors.header(SEPARATOR_THICK))


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
    
        # Executar extração
        resultado = servico.extrair_todos_cadastros()
        
        # Processar resultado
        if resultado and resultado.get('sucesso'):
            mostrar_resultado_sucesso(resultado)
        else:
            mostrar_resultado_erro(resultado)
            
    except KeyboardInterrupt:
        print(f"\n{Colors.warning('⚠️  Extração interrompida pelo usuário')}")
        CLIInterface.loading_spinner("Finalizando", 1)
    except Exception as e:
        CLIInterface.mostrar_erro(f"Erro inesperado: {str(e)}")
    
    # Pausa antes de voltar ao menu
    print(f"\n{Colors.info(SEPARATOR_THIN)}")
    input(Colors.menu("🔹 Pressione ENTER para voltar ao menu principal..."))


def mostrar_resultado_sucesso(resultado):
    """Exibe resultado de sucesso com animações"""
    
    total = resultado.get('total_cadastros', 0)
    tempo = resultado.get('tempo_execucao', 'N/A')
    arquivo = resultado.get('arquivo_salvo', 'dados_extraidos.json')
    requisicoes = resultado.get('total_requisicoes', 0)
    
    # Animação de conclusão
    CLIInterface.loading_spinner("Finalizando", 2)
    
    # Mostrar resultado final
    print(Colors.success(CONCLUSION_ASCII))
    
    print(Colors.stats("📊 EXTRAÇÃO FINALIZADA COM SUCESSO!"))
    print(Colors.stats(SEPARATOR_THICK))
    
    # Criar barra de progresso de 100%
    barra_completa = Colors.success(PROGRESS_BAR_FULL * 40)
    print(f"[{barra_completa}] {Colors.stats('100.0%')} - CONCLUÍDO")
    
    # Estatísticas finais
    print(f"\n{Colors.info('📈 ESTATÍSTICAS FINAIS:')}")
    print(f"  {ICONS['data']} Total extraído: {Colors.success(str(total))} cadastros")
    print(f"  {ICONS['gear']} Requisições: {Colors.info(str(requisicoes))}")
    print(f"  {ICONS['time']} Tempo total: {Colors.warning(str(tempo))}")
    print(f"  {ICONS['save']} Arquivo: {Colors.info(arquivo)}")
    
    # Animação de salvamento
    print(f"\n{Colors.progress('💾 Salvando dados...')}")
    for i in range(3):
        print(f"\r{Colors.progress('💾')} Salvando dados{'.' * (i+1)}", end="", flush=True)
        time.sleep(0.5)
    print(f"\r{Colors.success('✅ Dados salvos com sucesso!')}")


def mostrar_resultado_erro(resultado):
    """Exibe resultado de erro com formatação"""
    
    erro = resultado.get('erro', 'Erro desconhecido') if resultado else 'Falha na extração'
    
    print(Colors.error("❌ ERRO NA EXTRAÇÃO"))
    print(Colors.error(SEPARATOR_THIN))
    print(f"   {Colors.warning(str(erro))}")
    
    # Verificar se há dados parciais
    if resultado and resultado.get('cadastros'):
        total_parcial = len(resultado['cadastros'])
        arquivo_parcial = resultado.get('arquivo_salvo')
        
        print(f"\n{Colors.warning('⚠️  DADOS PARCIAIS SALVOS:')}")
        print(f"  {ICONS['data']} Extraídos: {Colors.info(str(total_parcial))} cadastros")
        if arquivo_parcial:
            print(f"  {ICONS['save']} Arquivo: {Colors.info(arquivo_parcial)}")


if __name__ == "__main__":
    main()