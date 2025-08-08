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
│  1️⃣  ➤ Iniciar Extração Completa                 │
│  2️⃣  ➤ Sair do Sistema                           │
│                                                 │
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
