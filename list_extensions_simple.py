"""
Script simples para listar todas as extensões em um arquivo .txt
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

def list_all_extensions():
    """Lista todas as extensões encontradas"""
    extension_dirs = find_extension_dirs()
    all_extensions = set()  # Usar set para evitar duplicatas
    
    for ext_dir in extension_dirs:
        if ext_dir.exists():
            for ext_path in ext_dir.iterdir():
                if ext_path.is_dir():
                    all_extensions.add(ext_path.name)
    
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
    
    print(f"Encontradas {len(extensions)} extensões")
    
    output_file = save_to_txt(extensions)
    
    print(f"Lista salva em: {output_file.absolute()}")
    print(f"Total: {len(extensions)} extensões")

if __name__ == "__main__":
    main()

