"""
Script para listar todas as extensões (limpo) em um arquivo .txt
Filtra extensões corrompidas e duplicatas
"""
import os
from pathlib import Path

def find_extension_dirs():
    """Encontra os diretórios de extensões"""
    user_profile = os.environ.get('USERPROFILE') or os.environ.get('HOME')
    if not user_profile:
        return []
    
    possible_paths = [
        Path(user_profile) / '.cursor' / 'extensions',
        Path(user_profile) / '.vscode' / 'extensions',
        Path(user_profile) / 'AppData' / 'Roaming' / 'Cursor' / 'User' / 'extensions',
        Path(user_profile) / 'AppData' / 'Roaming' / 'Code' / 'User' / 'extensions',
    ]
    
    found_paths = []
    for path in possible_paths:
        if path.exists():
            found_paths.append(path)
    
    return found_paths

def clean_extension_name(ext_name):
    """Remove versão e sufixos do nome da extensão"""
    # Remove sufixos como -universal, -win32-x64, etc.
    if '-' in ext_name:
        # Tenta extrair o nome base (publisher.extension-name)
        parts = ext_name.split('-')
        # Se começa com ponto, é corrompida
        if ext_name.startswith('.'):
            return None
        
        # Remove sufixos de versão e build
        # Formato típico: publisher.extension-name-version-build
        base_parts = []
        for part in parts:
            # Se encontrar um número de versão (ex: 1.2.3), para aqui
            if part.replace('.', '').isdigit() or part == 'universal':
                break
            base_parts.append(part)
        
        if base_parts:
            return '-'.join(base_parts)
    
    return ext_name

def list_all_extensions():
    """Lista todas as extensões encontradas (limpas)"""
    extension_dirs = find_extension_dirs()
    all_extensions = set()
    
    for ext_dir in extension_dirs:
        if ext_dir.exists():
            for ext_path in ext_dir.iterdir():
                if ext_path.is_dir():
                    ext_name = ext_path.name
                    # Filtra extensões corrompidas (começam com ponto)
                    if not ext_name.startswith('.'):
                        cleaned = clean_extension_name(ext_name)
                        if cleaned:
                            all_extensions.add(cleaned)
    
    return sorted(list(all_extensions))

def save_to_txt(extensions, filename="extensions_list.txt"):
    """Salva a lista de extensões em um arquivo .txt"""
    output_path = Path(filename)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for ext in extensions:
            f.write(f"{ext}\n")
    
    return output_path

def main():
    """Função principal"""
    print("Buscando extensões...")
    
    extensions = list_all_extensions()
    
    if not extensions:
        print("Nenhuma extensão encontrada!")
        return
    
    print(f"Encontradas {len(extensions)} extensões únicas")
    
    output_file = save_to_txt(extensions)
    
    print(f"Lista salva em: {output_file.absolute()}")
    print(f"Total: {len(extensions)} extensões")

if __name__ == "__main__":
    main()

