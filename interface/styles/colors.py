"""
Colors - Sistema de cores para terminal
"""

class Colors:
    """Classe com cores ANSI para terminal"""
    
    # Cores básicas
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Cores brilhantes
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'
    
    # Estilos
    BOLD = '\033[1m'
    DIM = '\033[2m'
    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'
    BLINK = '\033[5m'
    REVERSE = '\033[7m'
    STRIKETHROUGH = '\033[9m'
    
    # Reset
    RESET = '\033[0m'
    
    # Cores personalizadas para o sistema
    HEADER = BRIGHT_CYAN + BOLD
    SUCCESS = BRIGHT_GREEN + BOLD
    ERROR = BRIGHT_RED + BOLD
    WARNING = BRIGHT_YELLOW + BOLD
    INFO = BRIGHT_BLUE
    PROGRESS = BRIGHT_MAGENTA
    STATS = CYAN
    TIME = YELLOW
    MENU = BRIGHT_WHITE + BOLD
    
    @classmethod
    def colorize(cls, text, color):
        """Aplica cor ao texto"""
        return f"{color}{text}{cls.RESET}"
    
    @classmethod
    def header(cls, text):
        """Texto de cabeçalho estilizado"""
        return cls.colorize(text, cls.HEADER)
    
    @classmethod
    def success(cls, text):
        """Texto de sucesso estilizado"""
        return cls.colorize(text, cls.SUCCESS)
    
    @classmethod
    def error(cls, text):
        """Texto de erro estilizado"""
        return cls.colorize(text, cls.ERROR)
    
    @classmethod
    def warning(cls, text):
        """Texto de aviso estilizado"""
        return cls.colorize(text, cls.WARNING)
    
    @classmethod
    def info(cls, text):
        """Texto informativo estilizado"""
        return cls.colorize(text, cls.INFO)
    
    @classmethod
    def progress(cls, text):
        """Texto de progresso estilizado"""
        return cls.colorize(text, cls.PROGRESS)
    
    @classmethod
    def stats(cls, text):
        """Texto de estatísticas estilizado"""
        return cls.colorize(text, cls.STATS)
    
    @classmethod
    def menu(cls, text):
        """Texto de menu estilizado"""
        return cls.colorize(text, cls.MENU)
