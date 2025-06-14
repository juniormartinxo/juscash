from pathlib import Path
from dotenv import load_dotenv
import sys


def find_project_root(marker=".git"):
    """Encontra a raiz do projeto procurando por um arquivo ou diretório marcador."""
    path = Path(__file__).resolve()
    while path.parent != path:
        if (path / marker).exists():
            return path
        path = path.parent
    raise FileNotFoundError(f"Raiz do projeto com marcador '{marker}' não encontrada.")


# --- MODO DE USAR A SOLUÇÃO ROBUSTA ---
try:
    # 1. Encontra a raiz do projeto de forma dinâmica
    project_root = find_project_root()

    # 2. Adiciona a raiz ao path do sistema
    sys.path.insert(0, str(project_root))

    # 3. Define o caminho exato para o .env
    dotenv_path = project_root / ".env"

    # 4. Carrega o arquivo .env
    load_dotenv(dotenv_path=dotenv_path)

    # Mensagens de sucesso para você saber que funcionou
    print(f"✅ Raiz do projeto encontrada em: {project_root}")
    print(f"✅ Variáveis de ambiente carregadas de: {dotenv_path}")

except FileNotFoundError as e:
    print(f"❌ ERRO: {e}")


def get_project_root():
    return project_root


def get_dotenv_path():
    return dotenv_path
