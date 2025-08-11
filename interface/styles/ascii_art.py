"""
ASCII Art - Arte ASCII para interface visual
"""

# Header principal do sistema
HEADER_ASCII = """
╔════════════════════════════════════════════════════════════════╗
                    ┏┓┏┓┳  ┏┓┏┓┏┓┏┳┓┳┓┏┓┏┓┏┳┓
                    ┣┫┃┃┃  ┣  ┃┃  ┃ ┣┫┣┫┃  ┃
                    ┛┗┣┛┻  ┗┛┗┛┗┛ ┻ ┛┗┛┗┗┛ ┻
╚════════════════════════════════════════════════════════════════╝
"""

# Loading ASCII
LOADING_FRAMES = [
    "⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"
]

# Barra de progresso ASCII
PROGRESS_BAR_FULL = "█"
PROGRESS_BAR_EMPTY = "░"
PROGRESS_BAR_PARTIAL = "▓"

# Separadores
SEPARATOR_THICK = "═" * 70
SEPARATOR_THIN = "─" * 50
SEPARATOR_DOTS = "·" * 30

# Menu ASCII
MENU_ASCII = """
╭─────────────────────────────────────────────────╮
│            ┳┳┓┏┓┳┓┳┳  ┏┓┳┓┳┳┓┏┓┳┏┓┏┓┓           │
│            ┃┃┃┣ ┃┃┃┃  ┃┃┣┫┃┃┃┃ ┃┃┃┣┫┃           │
│            ┛ ┗┗┛┛┗┗┛  ┣┛┛┗┻┛┗┗┛┻┣┛┛┗┗┛          │
├─────────────────────────────────────────────────┤
│                                                 │
│  1️⃣  ➤ Extrair cadastros (SOAP API)              │
│  2️⃣  ➤ Operações de banco de dados               │
│  0️⃣  ➤ Sair do Sistema                           │
│                                                 │
╰─────────────────────────────────────────────────╯
"""

# Menu Banco de Dados ASCII
DATABASE_MENU_ASCII = """
╭─────────────────────────────────────────────────╮
│                ┳┓┏┓┏┳┓┏┓┳┓┏┓┏┓┏┓                │
│                ┃┃┣┫ ┃ ┣┫┣┫┣┫┗┓┣                 │
│                ┻┛┛┗ ┻ ┛┗┻┛┛┗┗┛┗┛                │
├─────────────────────────────────────────────────┤
│  1️⃣  ➤ Testar conexão                            │
│  2️⃣  ➤ Inicializar banco                         │
│  3️⃣  ➤ Processar arquivo JSON                    │
│  4️⃣  ➤ Workflow completo                         │
│  5️⃣  ➤ Ver estatísticas                          │
│  6️⃣  ➤ Listar arquivos                           │
│  0️⃣  ➤ Voltar ao menu principal                  │
╰─────────────────────────────────────────────────╯
"""

# Status icons
ICONS = {
    "success": "✅",
    "error": "❌",
    "warning": "⚠️",
    "info": "ℹ️",
    "loading": "🔄",
    "save": "💾",
    "stats": "📊",
    "time": "⏱️",
    "folder": "📁",
    "rocket": "🚀",
    "check": "✓",
    "arrow": "➤",
    "building": "🏢",
    "data": "📋",
    "gear": "⚙️",
    "fire": "🔥"
}

# Conclusão ASCII
CONCLUSION_ASCII = """
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║    🎉 EXTRAÇÃO FINALIZADA COM SUCESSO!                               ║
║    ✅ Todos os cadastros disponíveis foram processados               ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
"""
