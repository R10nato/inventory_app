#!/home/ubuntu/inventory_app/agents/venv/bin/python

import platform
import time
import requests
import json
import os
from dotenv import load_dotenv
import subprocess
import xml.etree.ElementTree as ET
import tempfile
import socket
import psutil

# Load environment variables (e.g., API endpoint)
load_dotenv()
API_ENDPOINT = os.getenv("API_ENDPOINT", "http://localhost:8000") # Default to localhost if not set
#API_ENDPOINT = "https://8000-i03zz0nw448b669gcbhbb-c0653f8b.manusvm.computer"

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
        "os": platform.system() + " " + platform.release()
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
    except ImportError:
        print("psutil not found, install it for detailed info.")
    except Exception as e:
        print(f"Error collecting Linux details with psutil: {e}")

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
        "os": platform.system() + " " + platform.release() + " " + platform.version()
    }
    try:
        import wmi
        import psutil
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
        details["ram_info"] = {"total_gb": round(mem_total_bytes / (1024**3), 2), "modules": [], "slots_total": 0}
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
             print(f"Could not get detailed RAM info: {e}")

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
                        print(f"Could not get usage for {logical_disk.DeviceID}: {e}")
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
            print("No Win32_VideoController found.")

        # Network
        for adapter in c.Win32_NetworkAdapterConfiguration(IPEnabled=True):
            details["network_info"].append({
                "type": "Ethernet" if "ethernet" in adapter.Description.lower() else "Wireless" if "wi-fi" in adapter.Description.lower() else adapter.Description,
                "name": adapter.Description,
                "mac": adapter.MACAddress,
                "ip_addresses": adapter.IPAddress
            })

        # TODO: Add Temperature (requires external libraries like OpenHardwareMonitor) and Power Supply info (very difficult via software)

    except ImportError:
        print("WMI or psutil not found. Please install them (pip install wmi psutil pywin32)")
    except Exception as e:
        print(f"Error collecting Windows details: {e}")

    return details

def get_hardware_details():
    """Gets hardware details based on the current OS."""
    system = platform.system()
    if system == "Windows":
        return get_windows_details()
    elif system == "Linux":
        return get_linux_details()
    else:
        print(f"Unsupported OS: {system}")
        return {"os": system}

# --- Network Discovery --- 
"""def discover_devices():
    #Discovers devices on the local network using nmap.
    devices = []
    try:
        import nmap
        nm = nmap.PortScanner()
        # TODO: Determine local network range dynamically or use config
        # Using a common private range for now, ADJUST AS NEEDED
        network_range = "192.168.1.0/24" 
        print(f"Scanning network: {network_range}...")
        nm.scan(hosts=network_range, arguments='-T4 -F --host-timeout 10s') # Fast scan, limited timeout

        for host in nm.all_hosts():
            if nm[host].state() == 'up':
                mac = nm[host]['addresses'].get('mac', None)
                vendor = nm[host]['vendor'].get(mac, 'Unknown') if mac else 'Unknown'
                device_type = 'computer' # Basic assumption, needs better fingerprinting
                if 'printer' in vendor.lower(): device_type = 'printer'
                # TODO: Add more sophisticated OS/device type detection if possible
                devices.append({
                    "ip_address": host,
                    "mac_address": mac,
                    "status": "online",
                    "name": nm[host].hostname() if nm[host].hostname() else host,
                    "device_type": device_type
                })
        print(f"Discovery finished. Found {len(devices)} online devices.")
    except ImportError:
        print("python-nmap not found. Please install it (pip install python-nmap) and ensure nmap is installed on the system.")
        # Fallback: return only the current machine?
        # devices.append({"ip_address": "127.0.0.1", "status": "online", "name": platform.node()})
    except Exception as e:
        print(f"Error during network discovery: {e}")
    return devices  """

def get_network_range():
    """Detecta dinamicamente a sub-rede local com base no IP da interface ativa."""
    for interface, addrs in psutil.net_if_addrs().items():
        for addr in addrs:
            if addr.family == socket.AF_INET and not addr.address.startswith("127."):
                ip = addr.address
                ip_parts = ip.split(".")
                first_octet = int(ip_parts[0])

                # Classe A (10.0.0.0 - 10.255.255.255)
                if first_octet == 10:
                    return f"{ip_parts[0]}.0.0.0/8"
                # Classe B (172.16.0.0 - 172.31.255.255)
                elif first_octet == 172 and 16 <= int(ip_parts[1]) <= 31:
                    return f"{ip_parts[0]}.{ip_parts[1]}.0.0/16"
                # Classe C (192.168.0.0 - 192.168.255.255)
                elif first_octet == 192 and ip_parts[1] == "168":
                    return f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.0/24"
                # Default fallback (substituir último octeto por 0/24)
                return f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.0/24"
    return "192.168.0.0/24"  # fallback padrão

def discover_devices():
    """Discovers devices on the local network using nmap (cross-platform safe)."""
    devices = []
    try:
        network_range = get_network_range()
        print(f"Scanning network: {network_range}...")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".xml") as tmpfile:
            output_file = tmpfile.name

        result = subprocess.run(
            ["nmap", "-T4", "-F", "--host-timeout", "10s", "-oX", output_file, network_range],
            capture_output=True,
            text=True
        )

        tree = ET.parse(output_file)
        root = tree.getroot()

        for host in root.findall("host"):
            status = host.find("status").attrib.get("state")
            if status != "up":
                continue

            address_elements = host.findall("address")
            ip = None
            mac = None
            for addr in address_elements:
                if addr.attrib.get("addrtype") == "ipv4":
                    ip = addr.attrib.get("addr")
                elif addr.attrib.get("addrtype") == "mac":
                    mac = addr.attrib.get("addr")

            hostname_tag = host.find("hostnames/hostname")
            hostname = hostname_tag.attrib.get("name") if hostname_tag is not None else ip

            devices.append({
                "ip_address": ip,
                "mac_address": mac,
                "status": "online",
                "name": hostname,
                "device_type": "computer"  # Pode melhorar usando OS detection futuramente
            })

        print(f"Discovery finished. Found {len(devices)} online devices.")

    except Exception as e:
        print(f"Error during network discovery: {e}")

    return devices

# --- Main Agent Logic --- 
def report_data(data):
    """Sends collected data to the backend API."""
    headers = {'Content-Type': 'application/json'}
    api_url = f"{API_ENDPOINT}/devices/"
    try:
        response = requests.post(api_url, headers=headers, data=json.dumps(data), timeout=15)
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        print(f"Successfully reported data for {data.get('ip_address', 'unknown IP')}. Status: {response.status_code}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error reporting data to {api_url}: {e}")
        return False

def run_agent(discover=True, report_self=True):
    """Runs the agent tasks: discovery and/or self-reporting."""
    if report_self:
        print("Collecting local hardware details...")
        local_details = get_hardware_details()
        # Get local IP and MAC (best effort)
        local_ip = "127.0.0.1" # Default
        local_mac = None
        try:
            import psutil
            net_if_addrs = psutil.net_if_addrs()
            for interface_name, interface_addresses in net_if_addrs.items():
                 # Try to find a non-loopback IPv4 address
                 is_loopback = "loopback" in interface_name.lower() or interface_name.startswith("lo")
                 if not is_loopback:
                     for address in interface_addresses:
                         if str(address.family) == 'AddressFamily.AF_INET':
                             local_ip = address.address
                         elif str(address.family) == 'AddressFamily.AF_PACKET':
                             local_mac = address.address
                     if local_ip != "127.0.0.1": # Found a potential primary IP
                         break 
        except Exception as e:
            print(f"Could not reliably determine local IP/MAC: {e}")

        payload = {
            "ip_address": local_ip,
            "mac_address": local_mac,
            "name": platform.node(),
            "os": local_details.pop("os", platform.system()),
            "device_type": "computer",
            "status": "online",
            "hardware_details": local_details
        }
        print(f"Reporting local machine ({local_ip})...")
        report_data(payload)

    if discover:
        print("Starting network discovery...")
        discovered_devices = discover_devices()
        print(f"Reporting {len(discovered_devices)} discovered devices...")
        for device in discovered_devices:
            # Avoid reporting self again if already done
            if report_self and device["ip_address"] == local_ip:
                continue
            # For discovered devices, we don't have hardware details yet
            device_payload = {k: v for k, v in device.items() if k != 'vendor'} # Remove temporary vendor info
            report_data(device_payload)

if __name__ == "__main__":
    print("Starting Inventory Agent...")
    # In a real scenario, this would run periodically (e.g., using APScheduler or as a service)
    # For now, run once:
    run_agent(discover=True, report_self=True)
    print("Agent run finished.")


