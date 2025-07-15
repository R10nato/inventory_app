#!/usr/bin/env python3

import platform
import time
import requests
import json
import os
import sys
import socket
import argparse
import sqlite3
import datetime
import logging
import wmi
import psutil
import nmap
import netifaces
import shutil
import ipaddress
from pathlib import Path
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("inventory_agent.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("inventory_agent")

# Parse command line arguments
parser = argparse.ArgumentParser(description='Inventory Hardware Agent')
parser.add_argument('--self-only', action='store_true', help='Only collect and report local machine data, skip network discovery')
parser.add_argument('--discover-only', action='store_true', help='Only perform network discovery, skip local machine data collection')
parser.add_argument('--network', type=str, help='Specify network range for discovery (e.g., 192.168.1.0/24)')
parser.add_argument('--offline', action='store_true', help='Run in offline mode, store data locally for later sync')
parser.add_argument('--sync', action='store_true', help='Sync locally stored data to the server')
args = parser.parse_args()

# Load environment variables (e.g., API endpoint)
load_dotenv()
API_ENDPOINT = os.getenv("API_ENDPOINT", "http://localhost:8000") # Default to localhost if not set
API_TOKEN = os.getenv("API_TOKEN", "")  # API token for authentication

# Configuração do banco de dados local
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "inventory_data.db")

def setup_local_db():
    """Configura o banco de dados SQLite local para armazenamento temporário."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Tabela para armazenar dados de inventário
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS inventory_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id TEXT,
        data TEXT,
        timestamp TEXT,
        synced INTEGER DEFAULT 0
    )
    ''')
    
    # Tabela para armazenar histórico de alterações
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS inventory_changes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id TEXT,
        component TEXT,
        old_value TEXT,
        new_value TEXT,
        timestamp TEXT,
        synced INTEGER DEFAULT 0
    )
    ''')
    
    conn.commit()
    conn.close()
    logger.info(f"Local database setup complete at {DB_PATH}")

# --- Platform Specific Collection --- 
def get_linux_details():
    """Collects hardware details on Linux systems."""
    details = {
        "cpu_info": {},
        "ram_info": {},
        "disk_info": [],
        "gpu_info": {},
        "motherboard_info": {},
        "network_info": [],
        "temperature_info": {},
        "os": platform.system() + " " + platform.release(),
        "usb_devices": [],
        "installed_software": []
    }
    # Placeholder for Linux collection logic using psutil, subprocess (lshw, dmidecode), etc.
    # Example using psutil (needs more detailed implementation)
    try:
        import psutil
        # CPU
        details["cpu_info"] = {
            "model": platform.processor(),
            "cores": psutil.cpu_count(logical=False),
            "threads": psutil.cpu_count(logical=True),
            "frequency_mhz": psutil.cpu_freq().current if psutil.cpu_freq() else None
        }
        # RAM
        mem = psutil.virtual_memory()
        details["ram_info"] = {
            "total_gb": round(mem.total / (1024**3), 2),
            "used_gb": round(mem.used / (1024**3), 2),
            # Type, slots etc. require dmidecode or similar
        }
        # Disks
        for part in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(part.mountpoint)
                details["disk_info"].append({
                    "name": part.device,
                    "mountpoint": part.mountpoint,
                    "fstype": part.fstype,
                    "total_gb": round(usage.total / (1024**3), 2),
                    "free_gb": round(usage.free / (1024**3), 2),
                    "type": "Unknown"  # Needs lsblk or similar to determine SSD/HDD
                    # SMART status requires specific tools (smartctl)
                })
            except Exception:
                pass # Ignore errors for specific partitions
        # Network
        net_if_addrs = psutil.net_if_addrs()
        for interface_name, interface_addresses in net_if_addrs.items():
            for address in interface_addresses:
                if str(address.family) == 'AddressFamily.AF_PACKET':
                     details["network_info"].append({
                         "type": "Ethernet/Wireless", # Simplification
                         "name": interface_name,
                         "mac": address.address
                     })
                     
        # USB Devices (usando lsusb)
        try:
            import subprocess
            result = subprocess.run(['lsusb'], capture_output=True, text=True)
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    if line.strip():
                        details["usb_devices"].append(line.strip())
        except Exception as e:
            logger.error(f"Error collecting USB devices: {e}")
            
        # Installed Software (usando dpkg ou rpm)
        try:
            if os.path.exists('/usr/bin/dpkg'):
                # Debian/Ubuntu
                result = subprocess.run(['dpkg', '-l'], capture_output=True, text=True)
                if result.returncode == 0:
                    for line in result.stdout.splitlines()[5:]:  # Pular cabeçalho
                        parts = line.split()
                        if len(parts) >= 3:
                            details["installed_software"].append({
                                "name": parts[1],
                                "version": parts[2],
                                "publisher": "Unknown",
                                "install_date": "Unknown"
                            })
            elif os.path.exists('/usr/bin/rpm'):
                # Red Hat/Fedora/CentOS
                result = subprocess.run(['rpm', '-qa', '--queryformat', '%{NAME}|%{VERSION}|%{VENDOR}|%{INSTALLTIME:date}\n'], 
                                       capture_output=True, text=True)
                if result.returncode == 0:
                    for line in result.stdout.splitlines():
                        parts = line.split('|')
                        if len(parts) >= 4:
                            details["installed_software"].append({
                                "name": parts[0],
                                "version": parts[1],
                                "publisher": parts[2],
                                "install_date": parts[3]
                            })
        except Exception as e:
            logger.error(f"Error collecting installed software: {e}")
            
    except ImportError:
        logger.error("psutil not found, install it for detailed info.")
    except Exception as e:
        logger.error(f"Error collecting Linux details with psutil: {e}")

    # TODO: Add collection using lshw, dmidecode for more details (GPU, Motherboard, RAM Type/Slots)

    return details

def get_windows_details():
    """Collects hardware details on Windows systems."""
    details = {
        "cpu_info": {},
        "ram_info": {},
        "disk_info": [],
        "gpu_info": {},
        "motherboard_info": {},
        "network_info": [],
        "temperature_info": {},
        "os": platform.system() + " " + platform.release() + " " + platform.version(),
        "usb_devices": [],
        "installed_software": []
    }
    try:
        
        c = wmi.WMI()

        # OS
        os_info = c.Win32_OperatingSystem()[0]
        details["os"] = os_info.Caption + " (" + os_info.OSArchitecture + ")"

        # CPU
        cpu = c.Win32_Processor()[0]
        details["cpu_info"] = {
            "brand": cpu.Manufacturer,
            "model": cpu.Name,
            "cores": cpu.NumberOfCores,
            "threads": cpu.NumberOfLogicalProcessors,
            "frequency_mhz": cpu.MaxClockSpeed
        }

        # Motherboard
        mb = c.Win32_BaseBoard()[0]
        details["motherboard_info"] = {
            "manufacturer": mb.Manufacturer,
            "model": mb.Product,
            "serial_number": mb.SerialNumber
        }

        # RAM
        mem_total_bytes = int(os_info.TotalVisibleMemorySize) * 1024 # KB to Bytes
        mem = psutil.virtual_memory()
        details["ram_info"] = {
            "total_gb": round(mem_total_bytes / (1024**3), 2), 
            "used_gb": round(mem.used / (1024**3), 2),
            "modules": [], 
            "slots_total": 0
        }
        # Get individual RAM modules and slots
        try:
            slots = c.Win32_PhysicalMemoryArray()[0].MemoryDevices
            details["ram_info"]["slots_total"] = slots
            for module in c.Win32_PhysicalMemory():
                details["ram_info"]["modules"].append({
                    "capacity_gb": round(int(module.Capacity) / (1024**3), 2),
                    "type": module.MemoryType, # Needs mapping to DDR types
                    "speed_mhz": module.Speed,
                    "manufacturer": module.Manufacturer,
                    "part_number": module.PartNumber
                })
            details["ram_info"]["slots_used"] = len(details["ram_info"]["modules"])
        except Exception as e:
             logger.error(f"Could not get detailed RAM info: {e}")

        # Disks
        for disk in c.Win32_DiskDrive():
            disk_detail = {
                "name": disk.Caption,
                "type": "HDD" if "HDD" in disk.MediaType else "SSD" if "SSD" in disk.MediaType else disk.MediaType,
                "model": disk.Model,
                "serial_number": disk.SerialNumber.strip() if disk.SerialNumber else None,
                "total_gb": round(int(disk.Size) / (1024**3), 2),
                "partitions": []
            }
            # Get partitions and usage
            for partition in disk.associators("Win32_DiskDriveToDiskPartition"):
                for logical_disk in partition.associators("Win32_LogicalDiskToPartition"):
                    try:
                        usage = psutil.disk_usage(logical_disk.DeviceID + "\\")
                        disk_detail["partitions"].append({
                            "drive_letter": logical_disk.DeviceID,
                            "total_gb": round(usage.total / (1024**3), 2),
                            "free_gb": round(usage.free / (1024**3), 2),
                            "fstype": logical_disk.FileSystem
                        })
                    except Exception as e:
                        logger.error(f"Could not get usage for {logical_disk.DeviceID}: {e}")
            details["disk_info"].append(disk_detail)
            # TODO: Add S.M.A.R.T. status if possible (requires admin rights and specific libraries)

        # GPU
        try:
            gpu = c.Win32_VideoController()[0]
            details["gpu_info"] = {
                "brand": gpu.AdapterCompatibility,
                "model": gpu.Name,
                "vram_mb": round(int(gpu.AdapterRAM) / (1024**2), 2) if gpu.AdapterRAM else None,
                "driver_version": gpu.DriverVersion
            }
        except IndexError:
            logger.warning("No Win32_VideoController found.")

        # Network
        for adapter in c.Win32_NetworkAdapterConfiguration(IPEnabled=True):
            details["network_info"].append({
                "type": "Ethernet" if "ethernet" in adapter.Description.lower() else "Wireless" if "wi-fi" in adapter.Description.lower() else adapter.Description,
                "name": adapter.Description,
                "mac": adapter.MACAddress,
                "ip_addresses": adapter.IPAddress
            })

        # USB Devices
        try:
            for usb in c.Win32_USBHub():
                details["usb_devices"].append({
                    "name": usb.Name,
                    "device_id": usb.DeviceID,
                    "status": usb.Status
                })

            # Adicionar dispositivos USB conectados
            for device in c.Win32_PnPEntity():
                if device.Name and "USB" in device.Name:
                    if not any(d.get("name") == device.Name for d in details["usb_devices"]):
                        details["usb_devices"].append({
                            "name": device.Name,
                            "device_id": device.DeviceID,
                            "status": device.Status
                        })
        except Exception as e:
            logger.error(f"Error collecting USB devices: {e}")

        # Installed Software
        try:
            # Método 1: WMI
            for product in c.Win32_Product():
                install_date = product.InstallDate
                if install_date:
                    # Converter formato YYYYMMDD para YYYY-MM-DD
                    try:
                        install_date = f"{install_date[0:4]}-{install_date[4:6]}-{install_date[6:8]}"
                    except:
                        install_date = "Unknown"
                        
                details["installed_software"].append({
                    "name": product.Name,
                    "version": product.Version,
                    "publisher": product.Vendor,
                    "install_date": install_date
                })
                
            # Método 2: Registro do Windows (para programas que não aparecem no WMI)
            import winreg
            
            def get_software_from_registry(hive, flag):
                registry_software = []
                try:
                    aReg = winreg.ConnectRegistry(None, hive)
                    aKey = winreg.OpenKey(aReg, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall", 0, winreg.KEY_READ | flag)
                    
                    count_subkey = winreg.QueryInfoKey(aKey)[0]
                    
                    for i in range(count_subkey):
                        try:
                            subkey_name = winreg.EnumKey(aKey, i)
                            subkey = winreg.OpenKey(aKey, subkey_name)
                            
                            try:
                                name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                try:
                                    version = winreg.QueryValueEx(subkey, "DisplayVersion")[0]
                                except:
                                    version = "Unknown"
                                try:
                                    publisher = winreg.QueryValueEx(subkey, "Publisher")[0]
                                except:
                                    publisher = "Unknown"
                                try:
                                    install_date = winreg.QueryValueEx(subkey, "InstallDate")[0]
                                    # Converter formato YYYYMMDD para YYYY-MM-DD se possível
                                    if install_date and len(install_date) == 8:
                                        install_date = f"{install_date[0:4]}-{install_date[4:6]}-{install_date[6:8]}"
                                except:
                                    install_date = "Unknown"
                                    
                                # Verificar se já existe na lista
                                if not any(s.get("name") == name for s in details["installed_software"]):
                                    registry_software.append({
                                        "name": name,
                                        "version": version,
                                        "publisher": publisher,
                                        "install_date": install_date
                                    })
                            except:
                                pass
                            
                            winreg.CloseKey(subkey)
                        except:
                            continue
                    
                    winreg.CloseKey(aKey)
                    winreg.CloseKey(aReg)
                except Exception as e:
                    logger.error(f"Error accessing registry: {e}")
                    
                return registry_software
            
            # Obter software do registro (32-bit e 64-bit)
            registry_software = get_software_from_registry(winreg.HKEY_LOCAL_MACHINE, 0)
            if platform.machine().endswith('64'):
                registry_software.extend(get_software_from_registry(winreg.HKEY_LOCAL_MACHINE, winreg.KEY_WOW64_32KEY))
                registry_software.extend(get_software_from_registry(winreg.HKEY_LOCAL_MACHINE, winreg.KEY_WOW64_64KEY))
                
            # Adicionar software do registro à lista
            for software in registry_software:
                if not any(s.get("name") == software["name"] for s in details["installed_software"]):
                    details["installed_software"].append(software)
                    
        except Exception as e:
            logger.error(f"Error collecting installed software: {e}")

        # TODO: Add Temperature (requires external libraries like OpenHardwareMonitor) and Power Supply info (very difficult via software)

    except ImportError:
        logger.error("WMI or psutil not found. Please install them (pip install wmi psutil pywin32)")
    except Exception as e:
        logger.error(f"Error collecting Windows details: {e}")

    return details

def get_hardware_details():
    """Gets hardware details based on the current OS."""
    system = platform.system()
    if system == "Windows":
        return get_windows_details()
    elif system == "Linux":
        return get_linux_details()
    else:
        logger.warning(f"Unsupported OS: {system}")
        return {"os": system}

logger = logging.getLogger("inventory_agent")

def check_nmap_installed():
    """Verifica se o nmap está instalado e acessível."""
    nmap_path = shutil.which("nmap")
    if nmap_path:
        return True

    if platform.system() == "Windows":
        common_paths = [
            "C:\\Program Files (x86)\\Nmap\\nmap.exe",
            "C:\\Program Files\\Nmap\\nmap.exe"
        ]
        for path in common_paths:
            if os.path.exists(path):
                os.environ["PATH"] += os.pathsep + os.path.dirname(path)
                return True
    return False


def get_cidr_network_range():
    """
    Detecta o IP local e a máscara, e retorna a rede em formato CIDR (ex: 192.168.0.0/23).
    Compatível com redes privadas e ignora interfaces virtuais/VPN.
    """
    try:
        for iface in netifaces.interfaces():
            addrs = netifaces.ifaddresses(iface)
            if netifaces.AF_INET in addrs:
                for addr in addrs[netifaces.AF_INET]:
                    ip = addr.get('addr')
                    netmask = addr.get('netmask')

                    # Ignora loopback, link-local e IPs fora da faixa privada
                    if not ip or ip.startswith(('127.', '169.254')):
                        continue
                    if not ip.startswith(('10.', '172.', '192.168.')):
                        continue  # ignora IPs públicos ou não locais

                    # Calcula a rede CIDR com base na máscara
                    network = ipaddress.IPv4Network(f"{ip}/{netmask}", strict=False)
                    logger.info(f"Interface selecionada: {iface} -> IP: {ip} / {netmask} -> Rede: {network}")

                    return str(network)

    except Exception as e:
        logger.error(f"Erro ao detectar faixa CIDR: {e}")

    # Fallback padrão
    logger.warning("Não foi possível detectar a rede correta. Usando fallback 192.168.1.0/24")
    return "192.168.1.0/24"

def discover_devices(network_range=None):
    """
    Descobre dispositivos na rede local usando Nmap.
    Usa -sn (ping scan) e, se necessário, tenta novamente com -sn -Pn.
    """
    devices = []

    if not check_nmap_installed():
        logger.error("nmap não está instalado ou fora do PATH.")
        logger.error("Instale via: https://nmap.org/download.html ou 'sudo apt install nmap'")
        return devices

    try:
        nm = nmap.PortScanner()
        range_to_scan = network_range or get_cidr_network_range()
        logger.info(f"Varredura de rede iniciada: {range_to_scan}")

        # Primeira tentativa: scan rápido tipo ping
        nm.scan(hosts=range_to_scan, arguments='-sn --host-timeout 10s')
        hosts = nm.all_hosts()

        # Se nada for detectado, tentar varredura mais forçada
        if not hosts:
            logger.warning("Nenhum host detectado. Tentando novamente com '-sn -Pn'.")
            nm.scan(hosts=range_to_scan, arguments='-sn -Pn --host-timeout 10s')
            hosts = nm.all_hosts()

        for host in hosts:
            if nm[host].state() == 'up':
                try:
                    mac = nm[host]['addresses'].get('mac', None)
                    vendor = nm[host]['vendor'].get(mac, 'Unknown') if mac and 'vendor' in nm[host] else 'Unknown'
                    device_type = 'printer' if vendor and 'printer' in vendor.lower() else 'computer'

                    devices.append({
                        "ip_address": host,
                        "mac_address": mac,
                        "status": "online",
                        "name": nm[host].hostname() or host,
                        "device_type": device_type
                    })
                except Exception as e:
                    logger.error(f"Erro ao processar host {host}: {e}")

        logger.info(f"Varredura finalizada. {len(devices)} dispositivo(s) encontrados.")
        return devices

    except ImportError:
        logger.error("Módulo python-nmap não encontrado. Instale com: pip install python-nmap")
    except Exception as e:
        logger.error(f"Erro durante descoberta de rede: {e}")

    return devices

def store_data_locally(device_id, data):
    """Armazena dados de inventário localmente para sincronização posterior."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Verificar se já existe um registro para este dispositivo
    cursor.execute("SELECT data FROM inventory_data WHERE device_id = ? ORDER BY timestamp DESC LIMIT 1", (device_id,))
    previous_data = cursor.fetchone()
    
    # Armazenar os novos dados
    timestamp = datetime.datetime.now().isoformat()
    cursor.execute(
        "INSERT INTO inventory_data (device_id, data, timestamp, synced) VALUES (?, ?, ?, ?)",
        (device_id, json.dumps(data), timestamp, 0)
    )
    
    # Se houver dados anteriores, verificar alterações
    if previous_data:
        try:
            old_data = json.loads(previous_data[0])
            detect_changes(device_id, old_data, data, cursor)
        except Exception as e:
            logger.error(f"Error detecting changes: {e}")
    
    conn.commit()
    conn.close()
    logger.info(f"Data for device {device_id} stored locally")

def detect_changes(device_id, old_data, new_data, cursor):
    """Detecta alterações entre inventários e registra no histórico."""
    timestamp = datetime.datetime.now().isoformat()
    
    # Verificar alterações no hardware
    components = {
        "cpu_info": "CPU",
        "ram_info": "RAM",
        "disk_info": "Discos",
        "gpu_info": "GPU",
        "motherboard_info": "Placa-mãe",
        "usb_devices": "Dispositivos USB"
    }
    
    for key, name in components.items():
        if key in old_data and key in new_data:
            if key == "disk_info" or key == "usb_devices":
                # Para listas, verificar diferenças mais complexas
                if key == "disk_info":
                    old_disks = {disk.get("name", ""): disk for disk in old_data.get(key, [])}
                    new_disks = {disk.get("name", ""): disk for disk in new_data.get(key, [])}
                    
                    # Discos removidos
                    for disk_name in set(old_disks.keys()) - set(new_disks.keys()):
                        cursor.execute(
                            "INSERT INTO inventory_changes (device_id, component, old_value, new_value, timestamp, synced) VALUES (?, ?, ?, ?, ?, ?)",
                            (device_id, f"{name} (Removido)", json.dumps(old_disks[disk_name]), "", timestamp, 0)
                        )
                    
                    # Discos adicionados
                    for disk_name in set(new_disks.keys()) - set(old_disks.keys()):
                        cursor.execute(
                            "INSERT INTO inventory_changes (device_id, component, old_value, new_value, timestamp, synced) VALUES (?, ?, ?, ?, ?, ?)",
                            (device_id, f"{name} (Adicionado)", "", json.dumps(new_disks[disk_name]), timestamp, 0)
                        )
                    
                    # Discos alterados
                    for disk_name in set(old_disks.keys()) & set(new_disks.keys()):
                        if old_disks[disk_name] != new_disks[disk_name]:
                            cursor.execute(
                                "INSERT INTO inventory_changes (device_id, component, old_value, new_value, timestamp, synced) VALUES (?, ?, ?, ?, ?, ?)",
                                (device_id, f"{name} ({disk_name})", json.dumps(old_disks[disk_name]), json.dumps(new_disks[disk_name]), timestamp, 0)
                            )
                elif key == "usb_devices":
                    # Comparar dispositivos USB por nome
                    old_usb_names = [dev.get("name", dev) if isinstance(dev, dict) else dev for dev in old_data.get(key, [])]
                    new_usb_names = [dev.get("name", dev) if isinstance(dev, dict) else dev for dev in new_data.get(key, [])]
                    
                    # Dispositivos removidos
                    for dev in set(old_usb_names) - set(new_usb_names):
                        cursor.execute(
                            "INSERT INTO inventory_changes (device_id, component, old_value, new_value, timestamp, synced) VALUES (?, ?, ?, ?, ?, ?)",
                            (device_id, f"{name} (Removido)", dev, "", timestamp, 0)
                        )
                    
                    # Dispositivos adicionados
                    for dev in set(new_usb_names) - set(old_usb_names):
                        cursor.execute(
                            "INSERT INTO inventory_changes (device_id, component, old_value, new_value, timestamp, synced) VALUES (?, ?, ?, ?, ?, ?)",
                            (device_id, f"{name} (Adicionado)", "", dev, timestamp, 0)
                        )
            else:
                # Para objetos, comparar diretamente
                if old_data.get(key) != new_data.get(key):
                    cursor.execute(
                        "INSERT INTO inventory_changes (device_id, component, old_value, new_value, timestamp, synced) VALUES (?, ?, ?, ?, ?, ?)",
                        (device_id, name, json.dumps(old_data.get(key, {})), json.dumps(new_data.get(key, {})), timestamp, 0)
                    )
    
    # Verificar alterações no software instalado
    old_software = {sw.get("name", ""): sw for sw in old_data.get("installed_software", [])}
    new_software = {sw.get("name", ""): sw for sw in new_data.get("installed_software", [])}
    
    # Software removido
    for sw_name in set(old_software.keys()) - set(new_software.keys()):
        cursor.execute(
            "INSERT INTO inventory_changes (device_id, component, old_value, new_value, timestamp, synced) VALUES (?, ?, ?, ?, ?, ?)",
            (device_id, "Software (Removido)", json.dumps(old_software[sw_name]), "", timestamp, 0)
        )
    
    # Software adicionado
    for sw_name in set(new_software.keys()) - set(old_software.keys()):
        cursor.execute(
            "INSERT INTO inventory_changes (device_id, component, old_value, new_value, timestamp, synced) VALUES (?, ?, ?, ?, ?, ?)",
            (device_id, "Software (Instalado)", "", json.dumps(new_software[sw_name]), timestamp, 0)
        )
    
    # Software atualizado
    for sw_name in set(old_software.keys()) & set(new_software.keys()):
        if old_software[sw_name].get("version") != new_software[sw_name].get("version"):
            cursor.execute(
                "INSERT INTO inventory_changes (device_id, component, old_value, new_value, timestamp, synced) VALUES (?, ?, ?, ?, ?, ?)",
                (device_id, f"Software ({sw_name})", json.dumps(old_software[sw_name]), json.dumps(new_software[sw_name]), timestamp, 0)
            )

def sync_local_data():
    """Sincroniza dados armazenados localmente com o servidor."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Obter dados não sincronizados
    cursor.execute("SELECT id, device_id, data, timestamp FROM inventory_data WHERE synced = 0")
    inventory_records = cursor.fetchall()
    
    # Obter alterações não sincronizadas
    cursor.execute("SELECT id, device_id, component, old_value, new_value, timestamp FROM inventory_changes WHERE synced = 0")
    change_records = cursor.fetchall()
    
    success_inventory = []
    success_changes = []
    
    # Sincronizar dados de inventário
    for record in inventory_records:
        record_id, device_id, data_str, timestamp = record
        try:
            data = json.loads(data_str)
            if report_data(data):
                success_inventory.append(record_id)
                logger.info(f"Successfully synced inventory data for device {device_id}")
        except Exception as e:
            logger.error(f"Error syncing inventory data for device {device_id}: {e}")
    
    # Sincronizar alterações (se houver endpoint para isso)
    for record in change_records:
        record_id, device_id, component, old_value, new_value, timestamp = record
        try:
            # Aqui você implementaria a lógica para enviar as alterações para o servidor
            # Por enquanto, vamos apenas marcar como sincronizado
            success_changes.append(record_id)
            logger.info(f"Successfully synced change record for device {device_id}")
        except Exception as e:
            logger.error(f"Error syncing change record for device {device_id}: {e}")
    
    # Atualizar registros sincronizados
    for record_id in success_inventory:
        cursor.execute("UPDATE inventory_data SET synced = 1 WHERE id = ?", (record_id,))
    
    for record_id in success_changes:
        cursor.execute("UPDATE inventory_changes SET synced = 1 WHERE id = ?", (record_id,))
    
    conn.commit()
    conn.close()
    
    logger.info(f"Sync complete: {len(success_inventory)} inventory records and {len(success_changes)} change records synchronized")
    return len(success_inventory) + len(success_changes)

# --- Main Agent Logic --- 
def report_data(data):
    """Sends collected data to the backend API."""
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {API_TOKEN}' if API_TOKEN else ''
    }
    api_url = f"{API_ENDPOINT}/devices/"
    try:
        response = requests.post(api_url, headers=headers, data=json.dumps(data), timeout=15)
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        logger.info(f"Successfully reported data for {data.get('ip_address', 'unknown IP')}. Status: {response.status_code}")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Error reporting data to {api_url}: {e}")
        logger.error(f"Please check if the API server is running at {API_ENDPOINT}")
        return False

def get_local_network_info():
    """Get local IP and MAC address information."""
    local_ip = "127.0.0.1"  # Default
    local_mac = None
    
    try:
        import psutil
        net_if_addrs = psutil.net_if_addrs()
        
        # First try: Find non-loopback interfaces with IPv4 addresses
        for interface_name, interface_addresses in net_if_addrs.items():
            is_loopback = "loopback" in interface_name.lower() or interface_name.startswith("lo")
            if not is_loopback:
                ipv4_address = None
                mac_address = None
                
                for address in interface_addresses:
                    if "AF_INET" in str(address.family):  # IPv4
                        ipv4_address = address.address
                    elif "AF_LINK" in str(address.family) or "AF_PACKET" in str(address.family):  # MAC
                        mac_address = address.address
                
                if ipv4_address and not ipv4_address.startswith("169.254"):  # Avoid link-local
                    local_ip = ipv4_address
                    local_mac = mac_address
                    break
        
        # Second try: If no suitable interface found, accept link-local addresses
        if local_ip == "127.0.0.1":
            for interface_name, interface_addresses in net_if_addrs.items():
                if "loopback" not in interface_name.lower() and not interface_name.startswith("lo"):
                    for address in interface_addresses:
                        if "AF_INET" in str(address.family):
                            local_ip = address.address
                            # Find corresponding MAC
                            for addr in interface_addresses:
                                if "AF_LINK" in str(addr.family) or "AF_PACKET" in str(addr.family):
                                    local_mac = addr.address
                            break
                    if local_ip != "127.0.0.1":
                        break
    
    except Exception as e:
        logger.error(f"Could not reliably determine local IP/MAC: {e}")
        logger.error("Using loopback address (127.0.0.1) as fallback.")
    
    return local_ip, local_mac

def get_machine_id():
    """Gera um ID único para a máquina baseado em hardware."""
    try:
        if platform.system() == "Windows":
            import wmi
            c = wmi.WMI()
            # Combinar informações de hardware para criar um ID único
            cpu = c.Win32_Processor()[0]
            mb = c.Win32_BaseBoard()[0]
            os_info = c.Win32_OperatingSystem()[0]
            
            # Criar hash baseado em informações de hardware
            import hashlib
            hw_str = f"{cpu.ProcessorId}_{mb.SerialNumber}_{os_info.SerialNumber}"
            return hashlib.md5(hw_str.encode()).hexdigest()
        else:
            # Para Linux, usar o machine-id do sistema
            machine_id_file = "/etc/machine-id"
            if os.path.exists(machine_id_file):
                with open(machine_id_file, "r") as f:
                    return f.read().strip()
            else:
                # Fallback para Linux
                import uuid
                return str(uuid.getnode())
    except Exception as e:
        logger.error(f"Error generating machine ID: {e}")
        # Fallback para qualquer sistema
        import uuid
        return str(uuid.getnode())

def run_agent():
    """Runs the agent tasks: discovery and/or self-reporting."""
    # Configurar banco de dados local
    setup_local_db()
    
    # Determinar o que executar com base nos argumentos de linha de comando
    discover = not args.self_only
    report_self = not args.discover_only
    offline_mode = args.offline
    sync_mode = args.sync
    
    # Sincronizar dados armazenados localmente, se solicitado
    if sync_mode:
        logger.info("Starting sync of locally stored data...")
        synced_count = sync_local_data()
        logger.info(f"Sync complete: {synced_count} records synchronized")
        if not report_self and not discover:
            return
    
    if report_self:
        logger.info("Collecting local hardware details...")
        local_details = get_hardware_details()
        
        # Get local IP and MAC
        local_ip, local_mac = get_local_network_info()
        
        # Gerar ID único para a máquina
        machine_id = get_machine_id()
        
        payload = {
            "ip_address": local_ip,
            "mac_address": local_mac,
            "name": platform.node(),
            "os": local_details.pop("os", platform.system()),
            "device_type": "computer",
            "status": "online",
            "hardware_details": local_details,
            "machine_id": machine_id,  # Adicionar ID único da máquina
            "last_seen": datetime.datetime.now().isoformat()
        }
        
        logger.info(f"Reporting local machine ({local_ip})...")
        
        if offline_mode:
            # Armazenar dados localmente
            store_data_locally(machine_id, payload)
        else:
            # Enviar dados diretamente para o servidor
            success = report_data(payload)
            if not success and not args.offline:
                # Se falhar e não estiver explicitamente em modo offline, armazenar localmente
                logger.info("Failed to report data to server, storing locally...")
                store_data_locally(machine_id, payload)

    if discover:
        logger.info("Starting network discovery...")
        discovered_devices = discover_devices()
        logger.info(f"Reporting {len(discovered_devices)} discovered devices...")
        
        for device in discovered_devices:
            # Avoid reporting self again if already done
            if report_self and device["ip_address"] == local_ip:
                continue
                
            # Gerar ID para o dispositivo descoberto
            import hashlib
            device_id = hashlib.md5(f"{device['ip_address']}_{device.get('mac_address', '')}".encode()).hexdigest()
            device["machine_id"] = device_id
            device["last_seen"] = datetime.datetime.now().isoformat()
            
            # For discovered devices, we don't have hardware details yet
            device_payload = {k: v for k, v in device.items() if k != 'vendor'}  # Remove temporary vendor info
            
            if offline_mode:
                # Armazenar dados localmente
                store_data_locally(device_id, device_payload)
            else:
                # Enviar dados diretamente para o servidor
                success = report_data(device_payload)
                if not success and not args.offline:
                    # Se falhar e não estiver explicitamente em modo offline, armazenar localmente
                    logger.info(f"Failed to report device {device['ip_address']} to server, storing locally...")
                    store_data_locally(device_id, device_payload)

def print_help():
    """Print help information about the agent."""
    print("\nInventory Hardware Agent Help")
    print("============================")
    print("This agent collects hardware information from the local machine and discovers")
    print("other devices on the network, reporting all data to a central inventory system.")
    print("\nUsage Options:")
    print("  python agent.py                  # Run both local collection and network discovery")
    print("  python agent.py --self-only      # Only collect and report local machine data")
    print("  python agent.py --discover-only  # Only perform network discovery")
    print("  python agent.py --network 192.168.1.0/24  # Specify network range for discovery")
    print("  python agent.py --offline        # Run in offline mode, store data locally")
    print("  python agent.py --sync           # Sync locally stored data to the server")
    print("  python agent.py --help           # Show this help message")
    print("\nRequirements:")
    print("  - For Windows: wmi, psutil, python-nmap, pywin32, nmap installed")
    print("  - For Linux: psutil, python-nmap, nmap installed")
    print("  - API server running (set in .env file or defaults to http://localhost:8000)")
    print("\nTroubleshooting:")
    print("  - Run as administrator/root for best results")
    print("  - Ensure nmap is installed and in PATH")
    print("  - Check firewall settings if network discovery fails")
    print("  - Verify API server is running and accessible")

if __name__ == "__main__":
    # Show help if requested
    if "--help" in sys.argv or "-h" in sys.argv:
        print_help()
        sys.exit(0)
        
    logger.info("Starting Inventory Agent...")
    run_agent()
    logger.info("Agent run finished.")
