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
import re
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
API_ENDPOINT = os.getenv("API_ENDPOINT", "https://8000-icaevqvt6t558ljaxl9pk-15911c2d.manusvm.computer") # Default to localhost if not set
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
        "installed_software": [],
        "audio_devices": []
    }
    try:
        import psutil
        import subprocess
        # CPU
        details["cpu_info"] = {
            "model": platform.processor(),
            "cores": psutil.cpu_count(logical=False),
            "threads": psutil.cpu_count(logical=True),
            "frequency_mhz": psutil.cpu_freq().current if psutil.cpu_freq() else None
        }
        
        # CPU Temperature
        try:
            temperatures = psutil.sensors_temperatures()
            if temperatures:
                cpu_temp = None
                for name, entries in temperatures.items():
                    if name.lower() in ['coretemp', 'k10temp', 'ryzen', 'cpu_thermal']:
                        for entry in entries:
                            if 'package' in entry.label.lower() or 'core 0' in entry.label.lower():
                                cpu_temp = round(entry.current, 1)
                                break
                        if cpu_temp:
                            break
                
                if cpu_temp:
                    details["cpu_info"]["temperature_c"] = cpu_temp
                    details["temperature_info"]["cpu"] = cpu_temp
        except Exception as e:
            logger.error(f"Error getting CPU temperature: {e}")
        
        # RAM
        mem = psutil.virtual_memory()
        details["ram_info"] = {
            "total_gb": round(mem.total / (1024**3), 2),
            "used_gb": round(mem.used / (1024**3), 2),
            "type": "Unknown",
            "slots": "Unknown"
        }

        # RAM Frequency and Timings (dmidecode)
        try:
            if os.geteuid() == 0:
                dmi_output = subprocess.check_output(["dmidecode", "-t", "memory"], universal_newlines=True)
                speed_lines = [line for line in dmi_output.split("\n") if "Speed" in line and "Unknown" not in line]
                if speed_lines:
                    for line in speed_lines:
                        if "MT/s" in line or "MHz" in line:
                            parts = line.split(":")
                            if len(parts) > 1:
                                speed_str = parts[1].strip()
                                speed_match = re.search(r"(\d+)", speed_str)
                                if speed_match:
                                    details["ram_info"]["speed_mhz"] = int(speed_match.group(1))
                                    break
                details["ram_info"]["timings"] = "Unknown"
            else:
                logger.warning("Not running as root, skipping detailed RAM info that requires dmidecode")
        except Exception as e:
            logger.error(f"Error getting RAM details: {e}")
        
        # Disks
        for part in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(part.mountpoint)
                disk_model = "Unknown"
                disk_type = "Unknown"
                disk_temp = None
                
                try:
                    device_name = part.device.split("/")[-1]
                    if device_name.startswith("sd") or device_name.startswith("nvme"):
                        base_device = re.sub(r"\d+$", "", device_name)
                        lsblk_output = subprocess.check_output(["lsblk", "-d", "-o", "NAME,MODEL,ROTA", "-n", f"/dev/{base_device}"], universal_newlines=True).strip()
                        if lsblk_output:
                            parts = lsblk_output.split()
                            if len(parts) >= 2:
                                disk_model = " ".join(parts[1:-1])
                                disk_type = "HDD" if parts[-1] == "1" else "SSD"
                                
                                try:
                                    if os.geteuid() == 0:
                                        smart_output = subprocess.check_output(["smartctl", "-A", f"/dev/{base_device}"], universal_newlines=True)
                                        for line in smart_output.split("\n"):
                                            if "Temperature" in line or "Airflow_Temperature" in line:
                                                temp_parts = line.split()
                                                for i, p in enumerate(temp_parts):
                                                    if p.isdigit() and i < len(temp_parts) - 1:
                                                        if temp_parts[i+1] in ["C", "Celsius"]:
                                                            disk_temp = int(p)
                                                            break
                                except Exception as e:
                                    logger.error(f"Error getting disk temperature: {e}")
                except Exception as e:
                    logger.error(f"Error getting disk model/type: {e}")
                
                disk_info = {
                    "name": part.device,
                    "mountpoint": part.mountpoint,
                    "fstype": part.fstype,
                    "total_gb": round(usage.total / (1024**3), 2),
                    "free_gb": round(usage.free / (1024**3), 2),
                    "type": disk_type,
                    "model": disk_model
                }
                
                if disk_temp is not None:
                    disk_info["temperature_c"] = disk_temp
                    if "disks" not in details["temperature_info"]:
                        details["temperature_info"]["disks"] = {}
                    details["temperature_info"]["disks"][part.device] = disk_temp
                
                details["disk_info"].append(disk_info)
            except Exception as e:
                logger.error(f"Error processing disk {part.device}: {e}")
        
        # GPU
        gpu_info = {"name": "Unknown"}
        try:
            lspci_output = subprocess.check_output(["lspci"], universal_newlines=True)
            for line in lspci_output.split("\n"):
                if "VGA" in line or "3D" in line or "Display" in line:
                    parts = line.split(":")
                    if len(parts) >= 3:
                        gpu_info["name"] = parts[2].strip()
                    break
        except Exception as e:
            logger.error(f"Error getting GPU info: {e}")
        
        try:
            xrandr_output = subprocess.check_output(["xrandr"], universal_newlines=True)
            for line in xrandr_output.split("\n"):
                if " connected " in line and "x" in line:
                    parts = line.split()
                    for part in parts:
                        if "x" in part and re.search(r'\d+x\d+', part):
                            gpu_info["monitor_resolution"] = part
                            break
                    break
        except Exception as e:
            logger.error(f"Error getting monitor info: {e}")
        
        details["gpu_info"] = gpu_info
        
        # Motherboard
        mb_info = {"manufacturer": "Unknown", "model": "Unknown"}
        try:
            if os.geteuid() == 0:
                dmi_output = subprocess.check_output(["dmidecode", "-t", "baseboard"], universal_newlines=True)
                for line in dmi_output.split("\n"):
                    if "Manufacturer" in line:
                        parts = line.split(":")
                        if len(parts) > 1:
                            mb_info["manufacturer"] = parts[1].strip()
                    elif "Product Name" in line:
                        parts = line.split(":")
                        if len(parts) > 1:
                            mb_info["model"] = parts[1].strip()
            else:
                logger.warning("Not running as root, skipping motherboard info that requires dmidecode")
        except Exception as e:
            logger.error(f"Error getting motherboard info: {e}")
        
        details["motherboard_info"] = mb_info
        
        # Audio Devices
        try:
            lspci_output = subprocess.check_output(["lspci"], universal_newlines=True)
            for line in lspci_output.split("\n"):
                if "Audio" in line or "audio" in line:
                    parts = line.split(":")
                    if len(parts) >= 3:
                        details["audio_devices"].append(parts[2].strip())
        except Exception as e:
            logger.error(f"Error getting audio info: {e}")
            
        if not details["audio_devices"]:
            try:
                aplay_output = subprocess.check_output(["aplay", "-l"], universal_newlines=True)
                for line in aplay_output.split("\n"):
                    if "card" in line and ":" in line:
                        parts = line.split(":")
                        if len(parts) > 1:
                            audio_device = parts[1].strip()
                            if audio_device not in details["audio_devices"]:
                                details["audio_devices"].append(audio_device)
            except Exception as e:
                logger.error(f"Error getting audio info with aplay: {e}")
        
        net_if_addrs = psutil.net_if_addrs()
        for interface_name, interface_addresses in net_if_addrs.items():
            for address in interface_addresses:
                if str(address.family) == "AddressFamily.AF_PACKET":
                     details["network_info"].append({
                         "type": "Ethernet/Wireless",
                         "name": interface_name,
                         "mac": address.address
                     })
                     
        # USB Devices
        try:
            result = subprocess.run(["lsusb"], capture_output=True, text=True)
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    if line.strip():
                        details["usb_devices"].append(line.strip())
        except Exception as e:
            logger.error(f"Error collecting USB devices: {e}")
            
        # Installed Software
        try:
            if os.path.exists("/usr/bin/dpkg"):
                result = subprocess.run(["dpkg", "-l"], capture_output=True, text=True)
                if result.returncode == 0:
                    for line in result.stdout.splitlines()[5:]:
                        parts = line.split()
                        if len(parts) >= 3:
                            details["installed_software"].append({
                                "name": parts[1],
                                "version": parts[2],
                                "publisher": "Unknown",
                                "install_date": "Unknown"
                            })
            elif os.path.exists("/usr/bin/rpm"):
                result = subprocess.run(["rpm", "-qa", "--queryformat", "%{NAME}|%{VERSION}|%{VENDOR}|%{INSTALLTIME:date}\n"], capture_output=True, text=True)
                if result.returncode == 0:
                    for line in result.stdout.splitlines():
                        parts = line.split("|")
                        if len(parts) >= 4:
                            details["installed_software"].append({
                                "name": parts[0],
                                "version": parts[1],
                                "publisher": parts[2],
                                "install_date": parts[3]
                            })
        except Exception as e:
            logger.error(f"Error collecting installed software: {e}")

    except Exception as e:
        logger.error(f"Error during Linux details collection: {e}")
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
        "os": platform.system() + " " + platform.release(),
        "usb_devices": [],
        "installed_software": [],
        "audio_devices": []
    }
    try:
        import wmi
        c = wmi.WMI()

        # CPU
        for cpu in c.Win32_Processor():
            details["cpu_info"] = {
                "model": cpu.Name.strip(),
                "cores": cpu.NumberOfCores,
                "threads": cpu.NumberOfLogicalProcessors,
                "frequency_mhz": cpu.CurrentClockSpeed
            }
            break

        details["cpu_info"]["temperature_c"] = "N/A (Requer software de terceiros)"
        details["temperature_info"]["cpu"] = "N/A"

        # RAM
        total_ram_bytes = 0
        for ram in c.Win32_PhysicalMemory():
            total_ram_bytes += int(ram.Capacity)
            if "speed_mhz" not in details["ram_info"] and hasattr(ram, "Speed"):
                details["ram_info"]["speed_mhz"] = ram.Speed
            if "type" not in details["ram_info"] and hasattr(ram, "MemoryType"):
                memory_types = {0: "Unknown", 1: "Other", 2: "DRAM", 3: "Synchronous DRAM", 4: "Cache DRAM", 5: "EDO", 6: "SDRAM", 7: "SRAM", 8: "RAM", 9: "ROM", 10: "Flash", 11: "EEPROM", 12: "FEPROM", 13: "EPROM", 14: "CDRAM", 15: "3DRAM", 16: "RDRAM", 17: "DDR SDRAM", 18: "DDR2 SDRAM", 19: "DDR2 FB-DIMM", 20: "DDR3 SDRAM", 21: "DDR4 SDRAM", 22: "LPDDR", 23: "LPDDR2", 24: "LPDDR3", 25: "LPDDR4"}
                details["ram_info"]["type"] = memory_types.get(ram.MemoryType, "Unknown")
            if "form_factor" not in details["ram_info"] and hasattr(ram, "FormFactor"):
                form_factors = {0: "Unknown", 1: "Other", 2: "SIP", 3: "DIP", 4: "ZIP", 5: "SOJ", 6: "Mem Card", 7: "DIMM", 8: "SIMM", 9: "SPIMM", 10: "SMD", 11: "SSMP", 12: "QFP", 13: "TQFP", 14: "SOIC", 15: "LCC", 16: "PLCC", 17: "BGA", 18: "FPBGA", 19: "LGA"}
                details["ram_info"]["form_factor"] = form_factors.get(ram.FormFactor, "Unknown")

        details["ram_info"]["total_gb"] = round(total_ram_bytes / (1024**3), 2)
        try:
            import psutil
            mem = psutil.virtual_memory()
            details["ram_info"]["used_gb"] = round(mem.used / (1024**3), 2)
        except Exception as e:
            logger.warning(f"Could not get used RAM via psutil: {e}")

        num_ram_slots = 0
        for slot in c.Win32_PhysicalMemoryArray():
            num_ram_slots = slot.MemoryDevices
            break
        details["ram_info"]["slots"] = num_ram_slots

        # Disks
        for disk in c.Win32_DiskDrive():
            disk_info = {
                "name": disk.Caption,
                "model": disk.Model,
                "serial": disk.SerialNumber,
                "size_gb": round(int(disk.Size) / (1024**3), 2) if disk.Size else 0,
                "interface_type": disk.InterfaceType,
                "media_type": disk.MediaType,
                "partitions": []
            }
            try:
                for status in c.Win32_DiskDriveToDiskPartition(Antecedent=disk.path_()):
                    for partition in c.Win32_LogicalDisk(Dependent=status.Dependent.path_()):
                        disk_info["partitions"].append({
                            "name": partition.Caption,
                            "filesystem": partition.FileSystem,
                            "free_space_gb": round(int(partition.FreeSpace) / (1024**3), 2) if partition.FreeSpace else 0
                        })
            except Exception as e:
                logger.warning(f"Error getting disk partitions for {disk.Caption}: {e}")

            details["disk_info"].append(disk_info)

        # GPU
        for gpu in c.Win32_VideoController():
            gpu_info = {
                "name": gpu.Caption,
                "adapter_ram_mb": round(gpu.AdapterRAM / (1024**2), 2) if gpu.AdapterRAM else 0,
                "driver_version": gpu.DriverVersion,
                "video_processor": gpu.VideoProcessor,
                "resolution": f"{gpu.CurrentHorizontalResolution}x{gpu.CurrentVerticalResolution}" if hasattr(gpu, "CurrentHorizontalResolution") else "Unknown",
                "refresh_rate_hz": gpu.CurrentRefreshRate if hasattr(gpu, "CurrentRefreshRate") else "Unknown"
            }
            details["gpu_info"] = gpu_info
            break

        # Motherboard
        for board in c.Win32_BaseBoard():
            details["motherboard_info"] = {
                "manufacturer": board.Manufacturer,
                "model": board.Product,
                "serial": board.SerialNumber
            }
            break

        # Network
        for adapter in c.Win32_NetworkAdapterConfiguration(IPEnabled=True):
            details["network_info"].append({
                "name": adapter.Description,
                "mac": adapter.MACAddress,
                "ip_address": adapter.IPAddress[0] if adapter.IPAddress else "N/A",
                "dhcp_enabled": adapter.DHCPEnabled,
                "dns_servers": adapter.DNSServerSearchOrder
            })

        # USB Devices
        for usb in c.Win32_UsbHub():
            details["usb_devices"].append(usb.Caption)

        # Installed Software
        for product in c.Win32_Product():
            details["installed_software"].append({
                "name": product.Name,
                "version": product.Version,
                "publisher": product.Vendor,
                "install_date": product.InstallDate
            })

        # Audio Devices
        try:
            for sound_device in c.Win32_SoundDevice():
                if sound_device.Name:
                    details["audio_devices"].append(sound_device.Name)
            
            if not details["audio_devices"]:
                for pnp_entity in c.Win32_PnPEntity():
                    if pnp_entity.Name and ("audio" in pnp_entity.Name.lower() or "sound" in pnp_entity.Name.lower()):
                        if pnp_entity.Name not in details["audio_devices"]:
                            details["audio_devices"].append(pnp_entity.Name)
        except Exception as e:
            logger.error(f"Erro ao obter dispositivos de áudio: {e}")

    except Exception as e:
        logger.error(f"Error during Windows details collection: {e}")
    return details

def get_device_details():
    """Collects hardware details based on the operating system."""
    system = platform.system()
    if system == "Linux":
        return get_linux_details()
    elif system == "Windows":
        return get_windows_details()
    else:
        logger.warning(f"Unsupported operating system: {system}")
        return {}

def send_data_to_server(data, endpoint):
    """Sends collected data to the API endpoint."""
    headers = {"Content-Type": "application/json"}
    if API_TOKEN:
        headers["Authorization"] = f"Bearer {API_TOKEN}"
    try:
        response = requests.post(f"{endpoint}/devices/inventory", json=data, headers=headers)
        response.raise_for_status()
        logger.info(f"Data sent successfully to {endpoint}. Response: {response.status_code}")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Error sending data to server: {e}")
        return False

def save_local_data(device_id, data, table="inventory_data"):
    """Saves data to the local SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    timestamp = datetime.datetime.now().isoformat()
    try:
        if table == "inventory_data":
            cursor.execute("INSERT INTO inventory_data (device_id, data, timestamp) VALUES (?, ?, ?)",
                           (device_id, json.dumps(data), timestamp))
        elif table == "inventory_changes":
            cursor.execute("INSERT INTO inventory_changes (device_id, component, old_value, new_value, timestamp) VALUES (?, ?, ?, ?, ?)",
                           (device_id, data["component"], data["old_value"], data["new_value"], timestamp))
        conn.commit()
        logger.info(f"Data saved locally to {table} for device {device_id}")
    except Exception as e:
        logger.error(f"Error saving data locally: {e}")
    finally:
        conn.close()

def load_local_data(table="inventory_data", synced=False):
    """Loads data from the local SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        query = f"SELECT id, device_id, data, timestamp FROM {table} WHERE synced = ?"
        cursor.execute(query, (1 if synced else 0,))
        rows = cursor.fetchall()
        data = []
        for row in rows:
            data.append({"id": row[0], "device_id": row[1], "data": json.loads(row[2]), "timestamp": row[3]})
        logger.info(f"Loaded {len(data)} records from local {table} (synced={synced})")
        return data
    except Exception as e:
        logger.error(f"Error loading local data: {e}")
        return []
    finally:
        conn.close()

def mark_data_as_synced(id, table="inventory_data"):
    """Marks data in the local database as synced."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(f"UPDATE {table} SET synced = 1 WHERE id = ?", (id,))
        conn.commit()
        logger.info(f"Record with id {id} marked as synced in {table}")
    except Exception as e:
        logger.error(f"Error marking data as synced: {e}")
    finally:
        conn.close()

def sync_local_data_to_server():
    """Syncs unsynced local data to the server."""
    unsynced_inventory = load_local_data(table="inventory_data", synced=False)
    unsynced_changes = load_local_data(table="inventory_changes", synced=False)

    logger.info(f"Attempting to sync {len(unsynced_inventory)} inventory records and {len(unsynced_changes)} change records.")

    for record in unsynced_inventory:
        if send_data_to_server(record["data"], API_ENDPOINT):
            mark_data_as_synced(record["id"], table="inventory_data")

    for record in unsynced_changes:
        change_data = {"device_id": record["device_id"], "changes": [record["data"]] }
        if send_data_to_server(change_data, API_ENDPOINT):
            mark_data_as_synced(record["id"], table="inventory_changes")

def get_local_ip():
    """Get the local IP address of the machine."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        IP = s.getsockname()[0]
    except Exception:
        IP = "127.0.0.1"
    finally:
        s.close()
    return IP

def get_network_range(ip_address):
    """Determines the network range from an IP address."""
    parts = ip_address.split(".")
    if len(parts) == 4:
        return f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"
    return ""

def discover_devices(network_range):
    """Discovers devices on the local network using nmap."""
    logger.info(f"Starting network discovery on {network_range}...")
    discovered_ips = []
    try:
        subprocess.run(["nmap", "-V"], capture_output=True, check=True)
        logger.info("nmap is installed. Proceeding with discovery.")

        command = ["nmap", "-sn", "-n", "-T4", network_range]
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        
        for line in result.stdout.splitlines():
            if "Nmap scan report for" in line:
                ip_address = line.split()[-1]
                if all(part.isdigit() and 0 <= int(part) <= 255 for part in ip_address.split(".")):
                    discovered_ips.append(ip_address)
                    logger.info(f"Discovered device: {ip_address}")

    except FileNotFoundError:
        logger.error("nmap not found. Please install nmap.")
    except subprocess.CalledProcessError as e:
        logger.error(f"nmap command failed: {e}\nStdout: {e.stdout}\nStderr: {e.stderr}")
    except Exception as e:
        logger.error(f"An unexpected error occurred during nmap discovery: {e}")
    
    logger.info(f"Network discovery finished. Found {len(discovered_ips)} devices.")
    return discovered_ips

def map_to_backend_schema(details):
    """Mapeia os dados coletados para o esquema esperado pelo backend."""
    mapped_data = {
        "cpu": details.get("cpu_info"),
        "ram": details.get("ram_info"),
        "storage": details.get("disk_info"),
        "gpu": details.get("gpu_info"),
        "motherboard": details.get("motherboard_info"),
        "network_info": details.get("network_info"),
        "audio": details.get("audio_devices"),
        "temperature_info": details.get("temperature_info"),
        "os": details.get("os"),
        "usb_devices": details.get("usb_devices"),
        "installed_software": details.get("installed_software")
    }
    return mapped_data

def main():
    setup_local_db()

    if args.sync:
        logger.info("Syncing local data to server...")
        sync_local_data_to_server()
        sys.exit(0)

    if not args.self_only and not args.discover_only:
        logger.info("Starting full inventory collection (local + discovery)...")
        local_details = get_device_details()
        local_details["device_id"] = platform.node()
        local_details["ip_address"] = get_local_ip()
        local_details["last_check_in"] = datetime.datetime.now().isoformat()

        # Mapear os detalhes coletados para o esquema do backend
        mapped_details = map_to_backend_schema(local_details)

        if not args.offline and API_ENDPOINT:
            if not send_data_to_server(mapped_details, API_ENDPOINT):
                logger.warning("Failed to send local machine data to server. Saving locally.")
                save_local_data(local_details["device_id"], mapped_details)
        else:
            logger.warning("Running in offline mode or API_ENDPOINT not set. Saving local machine data locally.")
            save_local_data(local_details["device_id"], mapped_details)

    elif args.self_only:
        logger.info("Starting local machine inventory collection (self-only)...")
        local_details = get_device_details()
        local_details["device_id"] = platform.node()
        local_details["ip_address"] = get_local_ip()
        local_details["last_check_in"] = datetime.datetime.now().isoformat()

        # Mapear os detalhes coletados para o esquema do backend
        mapped_details = map_to_backend_schema(local_details)

        if not args.offline and API_ENDPOINT:
            if not send_data_to_server(mapped_details, API_ENDPOINT):
                logger.warning("Failed to send local machine data to server. Saving locally.")
                save_local_data(local_details["device_id"], mapped_details)
        else:
            logger.warning("Running in offline mode or API_ENDPOINT not set. Saving local machine data locally.")
            save_local_data(local_details["device_id"], mapped_details)

    logger.info("Inventory agent finished.")

if __name__ == "__main__":
    main()




def map_to_backend_schema(details):
    """Mapeia os dados coletados para o esquema esperado pelo backend."""
    mapped_data = {
        "cpu": details.get("cpu_info"),
        "ram": details.get("ram_info"),
        "storage": details.get("disk_info"),
        "gpu": details.get("gpu_info"),
        "motherboard": details.get("motherboard_info"),
        "network_info": details.get("network_info"),
        "audio": details.get("audio_devices"),
        "temperature_info": details.get("temperature_info"),
        "os": details.get("os"),
        "usb_devices": details.get("usb_devices"),
        "installed_software": details.get("installed_software")
    }
    return mapped_data


