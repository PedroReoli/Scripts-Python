"""
Script para listar todas as extensões do Cursor/VSCode
e identificar possíveis problemas
"""
import os
import json
from pathlib import Path
from datetime import datetime

def find_extension_dirs():
    """Encontra os diretórios de extensões do Cursor e VSCode"""
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

def get_extension_info(ext_path):
    """Obtém informações de uma extensão"""
    package_json = ext_path / 'package.json'
    
    info = {
        "name": ext_path.name,
        "path": str(ext_path),
        "installed": False,
        "display_name": None,
        "version": None,
        "publisher": None,
        "description": None,
        "enabled": True,
        "issues": []
    }
    
    if package_json.exists():
        try:
            with open(package_json, 'r', encoding='utf-8') as f:
                package_data = json.load(f)
            
            info["installed"] = True
            info["display_name"] = package_data.get('displayName') or package_data.get('name', 'Unknown')
            info["version"] = package_data.get('version', 'Unknown')
            info["publisher"] = package_data.get('publisher', 'Unknown')
            info["description"] = package_data.get('description', 'No description')
            
            # Verificar se está desabilitada
            if (ext_path / '.disabled').exists():
                info["enabled"] = False
                info["issues"].append("EXTENSÃO DESABILITADA")
            
        except Exception as e:
            info["issues"].append(f"Erro ao ler package.json: {str(e)}")
    else:
        info["issues"].append("package.json não encontrado")
    
    return info

def list_all_extensions():
    """Lista todas as extensões"""
    extension_dirs = find_extension_dirs()
    
    if not extension_dirs:
        return {
            "error": "Nenhum diretório de extensões encontrado",
            "checked_paths": [str(Path(os.environ.get('USERPROFILE', '')))]
        }
    
    all_extensions = []
    
    for ext_dir in extension_dirs:
        print(f"Verificando: {ext_dir}")
        
        if not ext_dir.exists():
            continue
        
        # Listar todas as pastas de extensões
        for ext_path in ext_dir.iterdir():
            if ext_path.is_dir():
                ext_info = get_extension_info(ext_path)
                ext_info["extension_dir"] = str(ext_dir)
                all_extensions.append(ext_info)
    
    return {
        "extension_dirs": [str(d) for d in extension_dirs],
        "total_extensions": len(all_extensions),
        "extensions": all_extensions,
        "scan_date": datetime.now().isoformat()
    }

def save_extensions_report(data, filename="extensions_report.txt"):
    """Salva o relatório em arquivo TXT"""
    output_path = Path(filename)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("RELATÓRIO DE EXTENSÕES - CURSOR/VSCODE\n")
        f.write("=" * 80 + "\n\n")
        
        if "error" in data:
            f.write(f"ERRO: {data['error']}\n")
            return output_path
        
        f.write(f"Data do Scan: {data['scan_date']}\n")
        f.write(f"Total de Extensões: {data['total_extensions']}\n")
        f.write(f"Diretórios Verificados:\n")
        for ext_dir in data['extension_dirs']:
            f.write(f"  - {ext_dir}\n")
        f.write("\n" + "=" * 80 + "\n\n")
        
        # Agrupar por status
        enabled = [e for e in data['extensions'] if e['enabled']]
        disabled = [e for e in data['extensions'] if not e['enabled']]
        with_issues = [e for e in data['extensions'] if e['issues']]
        
        # Extensões habilitadas
        f.write(f"EXTENSÕES HABILITADAS ({len(enabled)}):\n")
        f.write("-" * 80 + "\n")
        for ext in sorted(enabled, key=lambda x: x['display_name'] or x['name']):
            f.write(f"\n{ext['display_name'] or ext['name']}\n")
            f.write(f"  ID: {ext['name']}\n")
            f.write(f"  Publisher: {ext['publisher'] or 'Unknown'}\n")
            f.write(f"  Version: {ext['version'] or 'Unknown'}\n")
            if ext['description']:
                f.write(f"  Description: {ext['description'][:100]}...\n" if len(ext['description']) > 100 else f"  Description: {ext['description']}\n")
            f.write(f"  Path: {ext['path']}\n")
            if ext['issues']:
                f.write(f"  ⚠️  ISSUES: {', '.join(ext['issues'])}\n")
        
        # Extensões desabilitadas
        if disabled:
            f.write("\n\n" + "=" * 80 + "\n")
            f.write(f"EXTENSÕES DESABILITADAS ({len(disabled)}):\n")
            f.write("-" * 80 + "\n")
            for ext in sorted(disabled, key=lambda x: x['display_name'] or x['name']):
                f.write(f"\n{ext['display_name'] or ext['name']}\n")
                f.write(f"  ID: {ext['name']}\n")
        
        # Extensões com problemas
        if with_issues:
            f.write("\n\n" + "=" * 80 + "\n")
            f.write(f"EXTENSÕES COM PROBLEMAS ({len(with_issues)}):\n")
            f.write("-" * 80 + "\n")
            for ext in sorted(with_issues, key=lambda x: x['display_name'] or x['name']):
                f.write(f"\n⚠️  {ext['display_name'] or ext['name']}\n")
                f.write(f"  ID: {ext['name']}\n")
                for issue in ext['issues']:
                    f.write(f"  PROBLEMA: {issue}\n")
                f.write(f"  Path: {ext['path']}\n")
        
        # Lista completa formatada para análise
        f.write("\n\n" + "=" * 80 + "\n")
        f.write("LISTA COMPLETA (Formato Simples):\n")
        f.write("-" * 80 + "\n")
        for ext in sorted(data['extensions'], key=lambda x: x['display_name'] or x['name']):
            status = "🔴 DESABILITADA" if not ext['enabled'] else "🟢 HABILITADA"
            issues_marker = " ⚠️" if ext['issues'] else ""
            f.write(f"{status}{issues_marker} | {ext['display_name'] or ext['name']} ({ext['name']})\n")
    
    print(f"\nRelatório salvo em: {output_path.absolute()}")
    return output_path

def main():
    """Função principal"""
    print("=" * 80)
    print("LISTANDO EXTENSÕES DO CURSOR/VSCODE")
    print("=" * 80)
    
    data = list_all_extensions()
    
    if "error" in data:
        print(f"\n❌ {data['error']}")
        return
    
    print(f"\n✓ Encontradas {data['total_extensions']} extensões")
    print(f"✓ Diretórios verificados: {len(data['extension_dirs'])}")
    
    # Mostrar resumo
    enabled = len([e for e in data['extensions'] if e['enabled']])
    disabled = len([e for e in data['extensions'] if not e['enabled']])
    with_issues = len([e for e in data['extensions'] if e['issues']])
    
    print(f"\nResumo:")
    print(f"  - Habilitadas: {enabled}")
    print(f"  - Desabilitadas: {disabled}")
    print(f"  - Com problemas: {with_issues}")
    
    # Salvar relatório
    output_file = save_extensions_report(data)
    
    print("\n" + "=" * 80)
    print("Scan concluído!")
    print("=" * 80)
    print(f"\nArquivo gerado: {output_file.absolute()}")

if __name__ == "__main__":
    main()

