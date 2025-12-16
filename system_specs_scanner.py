"""
Script para escanear especificações do sistema e verificar compatibilidade
com requisitos de jogos/modlists (ex: LoreRim)
"""
import json
import platform
import subprocess
import sys
from datetime import datetime
from pathlib import Path

try:
    import psutil
except ImportError:
    print("Erro: psutil não está instalado. Execute: pip install psutil")
    sys.exit(1)

try:
    import wmi
except ImportError:
    wmi = None
    print("Aviso: wmi não está instalado. Algumas informações de GPU podem não estar disponíveis.")


def get_cpu_info():
    """Obtém informações do processador"""
    cpu_info = {
        "model": platform.processor(),
        "cores_physical": psutil.cpu_count(logical=False),
        "cores_logical": psutil.cpu_count(logical=True),
        "frequency_mhz": psutil.cpu_freq().current if psutil.cpu_freq() else None,
        "architecture": platform.machine(),
    }
    
    # Tentar obter mais detalhes no Windows
    if platform.system() == "Windows":
        try:
            result = subprocess.run(
                ["wmic", "cpu", "get", "name,MaxClockSpeed", "/format:list"],
                capture_output=True,
                text=True,
                timeout=5
            )
            for line in result.stdout.split('\n'):
                if 'Name=' in line:
                    cpu_info["model"] = line.split('=', 1)[1].strip()
                elif 'MaxClockSpeed=' in line:
                    try:
                        cpu_info["max_frequency_mhz"] = int(line.split('=', 1)[1].strip())
                    except:
                        pass
        except:
            pass
    
    return cpu_info


def get_ram_info():
    """Obtém informações de memória RAM"""
    mem = psutil.virtual_memory()
    return {
        "total_gb": round(mem.total / (1024**3), 2),
        "available_gb": round(mem.available / (1024**3), 2),
        "used_gb": round(mem.used / (1024**3), 2),
        "percent": mem.percent
    }


def get_gpu_info():
    """Obtém informações da GPU"""
    gpu_info = {
        "model": "Não detectado",
        "vram_gb": None,
        "driver_version": None
    }
    
    if platform.system() == "Windows":
        if wmi:
            try:
                c = wmi.WMI()
                for gpu in c.Win32_VideoController():
                    if gpu.Name:
                        gpu_info["model"] = gpu.Name
                        gpu_info["driver_version"] = gpu.DriverVersion
                        # Tentar obter VRAM
                        if hasattr(gpu, 'AdapterRAM') and gpu.AdapterRAM:
                            gpu_info["vram_gb"] = round(gpu.AdapterRAM / (1024**3), 2)
                        break
            except Exception as e:
                print(f"Aviso ao obter info GPU via WMI: {e}")
        
        # Tentar obter VRAM via dxdiag ou outras fontes
        if not gpu_info.get("vram_gb"):
            try:
                # Tentar via GPU do Windows
                result = subprocess.run(
                    ["wmic", "path", "win32_VideoController", "get", "AdapterRAM,Name", "/format:list"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                for line in result.stdout.split('\n'):
                    if 'AdapterRAM=' in line and 'Name=' not in line:
                        try:
                            vram_bytes = int(line.split('=', 1)[1].strip())
                            if vram_bytes > 0:
                                gpu_info["vram_gb"] = round(vram_bytes / (1024**3), 2)
                                break
                        except:
                            pass
            except:
                pass
    
    return gpu_info


def get_disk_info():
    """Obtém informações de discos e espaço disponível"""
    disks = []
    for partition in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(partition.mountpoint)
            disk_info = {
                "device": partition.device,
                "mountpoint": partition.mountpoint,
                "fstype": partition.fstype,
                "total_gb": round(usage.total / (1024**3), 2),
                "used_gb": round(usage.used / (1024**3), 2),
                "free_gb": round(usage.free / (1024**3), 2),
                "percent": usage.percent
            }
            
            # Tentar detectar se é SSD
            if platform.system() == "Windows":
                try:
                    result = subprocess.run(
                        ["wmic", "diskdrive", "get", "Model,MediaType", "/format:list"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    # Esta é uma aproximação - pode não ser 100% preciso
                    disk_info["is_ssd"] = "SSD" in partition.fstype or "nvme" in partition.device.lower()
                except:
                    disk_info["is_ssd"] = None
            else:
                disk_info["is_ssd"] = None
            
            disks.append(disk_info)
        except PermissionError:
            continue
    
    return disks


def get_pagefile_info():
    """Obtém informações do pagefile (Windows)"""
    pagefile_info = {
        "exists": False,
        "size_gb": None,
        "location": None
    }
    
    if platform.system() == "Windows":
        try:
            result = subprocess.run(
                ["wmic", "pagefileset", "get", "AllocatedBaseSize,InitialSize,MaximumSize,Name", "/format:list"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            for line in result.stdout.split('\n'):
                if 'AllocatedBaseSize=' in line:
                    try:
                        size_mb = int(line.split('=', 1)[1].strip())
                        pagefile_info["size_gb"] = round(size_mb / 1024, 2)
                        pagefile_info["exists"] = True
                    except:
                        pass
                elif 'Name=' in line and pagefile_info["exists"]:
                    pagefile_info["location"] = line.split('=', 1)[1].strip()
                    break
        except Exception as e:
            print(f"Aviso ao obter info de pagefile: {e}")
    
    return pagefile_info


def check_vc_runtime():
    """Verifica se Visual C++ está instalado"""
    vc_installed = False
    vc_versions = []
    
    if platform.system() == "Windows":
        try:
            result = subprocess.run(
                ["wmic", "product", "where", "name like '%Visual C++%'", "get", "Name,Version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            for line in result.stdout.split('\n'):
                if 'Visual C++' in line:
                    vc_installed = True
                    vc_versions.append(line.strip())
        except:
            # Tentar método alternativo
            try:
                import winreg
                key = winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
                )
                for i in range(winreg.QueryInfoKey(key)[0]):
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        subkey = winreg.OpenKey(key, subkey_name)
                        name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                        if "Visual C++" in name:
                            vc_installed = True
                            version = winreg.QueryValueEx(subkey, "DisplayVersion")[0] if winreg.QueryValueEx(subkey, "DisplayVersion")[0] else "Unknown"
                            vc_versions.append(f"{name} - {version}")
                        winreg.CloseKey(subkey)
                    except:
                        continue
                winreg.CloseKey(key)
            except:
                pass
    
    return {
        "installed": vc_installed,
        "versions": vc_versions
    }


def check_dotnet_runtime():
    """Verifica se .NET Runtime está instalado"""
    dotnet_installed = False
    dotnet_versions = []
    
    if platform.system() == "Windows":
        try:
            result = subprocess.run(
                ["wmic", "product", "where", "name like '%.NET%'", "get", "Name,Version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            for line in result.stdout.split('\n'):
                if '.NET' in line and ('Runtime' in line or 'Framework' in line):
                    dotnet_installed = True
                    dotnet_versions.append(line.strip())
        except:
            # Tentar método alternativo via registro
            try:
                import winreg
                key = winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    r"SOFTWARE\Microsoft\NET Framework Setup\NDP"
                )
                for i in range(winreg.QueryInfoKey(key)[0]):
                    subkey_name = winreg.EnumKey(key, i)
                    try:
                        subkey = winreg.OpenKey(key, subkey_name)
                        version = winreg.QueryValueEx(subkey, "Version")[0]
                        dotnet_installed = True
                        dotnet_versions.append(f".NET {version}")
                        winreg.CloseKey(subkey)
                    except:
                        continue
                winreg.CloseKey(key)
            except:
                pass
    
    return {
        "installed": dotnet_installed,
        "versions": dotnet_versions
    }


def check_lore_rim_compatibility(system_specs):
    """Verifica compatibilidade com LoreRim baseado nos requisitos"""
    requirements = {
        "cpu": {
            "min": "11th gen Intel i7 ou AMD equivalente",
            "status": "Não verificado"
        },
        "ram": {
            "min_gb": 16,
            "status": "Não verificado"
        },
        "gpu_vram": {
            "ultra_gb": 16,
            "default_gb": 10,
            "status": "Não verificado"
        },
        "disk_space": {
            "total_gb": 600,
            "ssd_gb": 350,
            "status": "Não verificado"
        },
        "pagefile": {
            "min_gb": 40,
            "status": "Não verificado"
        },
        "vc_runtime": {
            "required": True,
            "status": "Não verificado"
        },
        "dotnet_runtime": {
            "required": True,
            "status": "Não verificado"
        }
    }
    
    # Verificar RAM
    ram_total = system_specs.get("ram", {}).get("total_gb", 0)
    if ram_total >= 16:
        requirements["ram"]["status"] = "OK"
    else:
        requirements["ram"]["status"] = f"INSUFICIENTE (tem {ram_total}GB, precisa 16GB)"
    
    # Verificar GPU VRAM
    gpu_vram = system_specs.get("gpu", {}).get("vram_gb")
    if gpu_vram:
        if gpu_vram >= 16:
            requirements["gpu_vram"]["status"] = "OK para Ultra"
        elif gpu_vram >= 10:
            requirements["gpu_vram"]["status"] = "OK para Default"
        else:
            requirements["gpu_vram"]["status"] = f"INSUFICIENTE (tem {gpu_vram}GB, precisa 10GB mínimo)"
    else:
        requirements["gpu_vram"]["status"] = "Não detectado"
    
    # Verificar espaço em disco (SSD)
    disks = system_specs.get("disks", [])
    max_ssd_free = 0
    total_free = 0
    
    for disk in disks:
        free_gb = disk.get("free_gb", 0)
        total_free += free_gb
        
        # Considerar SSD se is_ssd for True ou None (assumir que pode ser)
        is_ssd = disk.get("is_ssd")
        if is_ssd or is_ssd is None:
            max_ssd_free = max(max_ssd_free, free_gb)
    
    if max_ssd_free >= 350:
        requirements["disk_space"]["status"] = f"OK (SSD: {max_ssd_free}GB livre)"
    else:
        requirements["disk_space"]["status"] = f"INSUFICIENTE no SSD (tem {max_ssd_free}GB livre, precisa 350GB)"
    
    if total_free < 600:
        requirements["disk_space"]["status"] += f" | Espaço total insuficiente ({total_free}GB livre, precisa 600GB)"
    
    # Verificar pagefile
    pagefile = system_specs.get("pagefile", {})
    pagefile_size = pagefile.get("size_gb", 0)
    if pagefile_size >= 40:
        requirements["pagefile"]["status"] = "OK"
    else:
        requirements["pagefile"]["status"] = f"INSUFICIENTE (tem {pagefile_size}GB, precisa 40GB mínimo)"
    
    # Verificar Visual C++
    vc_runtime = system_specs.get("vc_runtime", {})
    if vc_runtime.get("installed"):
        requirements["vc_runtime"]["status"] = "OK"
    else:
        requirements["vc_runtime"]["status"] = "NÃO INSTALADO"
    
    # Verificar .NET Runtime
    dotnet_runtime = system_specs.get("dotnet_runtime", {})
    if dotnet_runtime.get("installed"):
        requirements["dotnet_runtime"]["status"] = "OK"
    else:
        requirements["dotnet_runtime"]["status"] = "NÃO INSTALADO"
    
    # CPU - verificação básica (análise de modelo)
    cpu_model = system_specs.get("cpu", {}).get("model", "").lower()
    cpu_ok = False
    
    if "intel" in cpu_model:
        # Tentar detectar geração i7
        import re
        if re.search(r'i[357]-(\d{4,5})', cpu_model) or re.search(r'i7-(\d{4,5})', cpu_model):
            match = re.search(r'i7-(\d{4,5})', cpu_model)
            if match:
                gen = match.group(1)[0]
                if gen and int(gen) >= 1:  # i7-11xxx ou superior
                    cpu_ok = True
        if "i7" in cpu_model and ("11" in cpu_model or "12" in cpu_model or "13" in cpu_model or "14" in cpu_model):
            cpu_ok = True
    elif "amd" in cpu_model:
        # AMD Ryzen equivalente (Ryzen 5 3600+ ou similar)
        if "ryzen" in cpu_model:
            cpu_ok = True
    
    if cpu_ok:
        requirements["cpu"]["status"] = "OK (pode precisar de verificação manual)"
    else:
        requirements["cpu"]["status"] = "Verificar manualmente se atende aos requisitos"
    
    return requirements


def scan_system():
    """Escaneia todas as especificações do sistema"""
    print("Escaneando sistema...")
    
    system_specs = {
        "scan_date": datetime.now().isoformat(),
        "os": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "architecture": platform.architecture()[0],
            "machine": platform.machine()
        },
        "cpu": get_cpu_info(),
        "ram": get_ram_info(),
        "gpu": get_gpu_info(),
        "disks": get_disk_info(),
        "pagefile": get_pagefile_info(),
        "vc_runtime": check_vc_runtime(),
        "dotnet_runtime": check_dotnet_runtime()
    }
    
    # Verificar compatibilidade com LoreRim
    system_specs["lore_rim_compatibility"] = check_lore_rim_compatibility(system_specs)
    
    return system_specs


def save_to_file(specs, filename="system_specs.json"):
    """Salva as especificações em arquivo JSON"""
    output_path = Path(filename)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(specs, f, indent=2, ensure_ascii=False)
    
    print(f"\nEspecificações salvas em: {output_path.absolute()}")
    return output_path


def main():
    """Função principal"""
    print("=" * 60)
    print("Scanner de Especificações do Sistema")
    print("=" * 60)
    
    specs = scan_system()
    
    # Mostrar resumo no console
    print("\n" + "=" * 60)
    print("RESUMO DO SISTEMA")
    print("=" * 60)
    print(f"CPU: {specs['cpu']['model']}")
    print(f"RAM: {specs['ram']['total_gb']} GB")
    print(f"GPU: {specs['gpu']['model']}")
    if specs['gpu']['vram_gb']:
        print(f"VRAM: {specs['gpu']['vram_gb']} GB")
    
    print("\n" + "=" * 60)
    print("COMPATIBILIDADE COM LORERIM")
    print("=" * 60)
    compatibility = specs['lore_rim_compatibility']
    for req_name, req_data in compatibility.items():
        if isinstance(req_data, dict) and 'status' in req_data:
            status = req_data['status']
            icon = "✓" if "OK" in status else "✗"
            print(f"{icon} {req_name.upper()}: {status}")
    
    # Salvar em arquivo
    output_file = save_to_file(specs)
    
    print("\n" + "=" * 60)
    print("Scan concluído!")
    print("=" * 60)


if __name__ == "__main__":
    main()

