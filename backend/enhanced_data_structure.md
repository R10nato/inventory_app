# Enhanced Data Structure - Inventory System

## Identificadores Únicos Implementados

### Device Level
- `system_uuid`: UUID único do sistema (Win32_ComputerSystemProduct.UUID)
- `motherboard_serial`: Serial da placa-mãe (Win32_BaseBoard.SerialNumber)
- `bios_version`: Versão da BIOS/UEFI (Win32_BIOS.SMBIOSBIOSVersion)
- `bios_vendor`: Fabricante da BIOS (Win32_BIOS.Manufacturer)
- `bios_date`: Data da BIOS (Win32_BIOS.ReleaseDate)
- `chassis_serial`: Serial do chassi (Win32_SystemEnclosure.SerialNumber)

### Hardware Components

#### CPU
```json
{
  "model": "Intel Core i7-12700K",
  "vendor": "Intel",
  "cores": 12,
  "threads": 20,
  "cache_l1": 80000,
  "cache_l2": 1200000,
  "cache_l3": 25600000,
  "serial": "BFEBFBFF000906E9",
  "stepping": "5",
  "microcode": "0x2C"
}
```

#### RAM
```json
{
  "modules": [
    {
      "serial": "12345678",
      "part_number": "CMK32GX4M2E3200C16",
      "capacity_bytes": 17179869184,
      "speed_mhz": 3200,
      "slot_location": "DIMM1",
      "manufacturer": "Corsair",
      "memory_type": "DDR4",
      "form_factor": "DIMM"
    }
  ]
}
```

#### Storage
```json
{
  "drives": [
    {
      "serial": "S4EWNX0N123456",
      "model": "Samsung SSD 980 PRO 1TB",
      "capacity_bytes": 1000204886016,
      "interface_type": "NVMe",
      "firmware_version": "5B2QGXA7",
      "vendor": "Samsung",
      "health_status": "OK",
      "temperature_celsius": 42
    }
  ]
}
```

#### GPU
```json
{
  "cards": [
    {
      "device_id": "0x2684",
      "vendor_id": "0x10DE",
      "uuid": "GPU-12345678-1234-1234-1234-123456789012",
      "vram_bytes": 12884901888,
      "driver_version": "531.79",
      "name": "NVIDIA GeForce RTX 4070",
      "pci_bus": "01:00.0"
    }
  ]
}
```

#### Network
```json
{
  "interfaces": [
    {
      "mac_address": "AA:BB:CC:DD:EE:FF",
      "vendor": "Intel Corporation",
      "speed_mbps": 1000,
      "driver_version": "12.19.2.12",
      "interface_name": "Ethernet",
      "pci_id": "8086:15F3"
    }
  ]
}
```

#### Power Supply
```json
{
  "serial": "PSU123456789",
  "model": "Corsair RM850x",
  "wattage": 850,
  "efficiency_rating": "80+ Gold",
  "vendor": "Corsair"
}
```

#### USB Devices
```json
{
  "devices": [
    {
      "vendor_id": "0x046D",
      "product_id": "0xC52B",
      "serial": "USB123456",
      "description": "Logitech USB Receiver",
      "port": "USB3.0-Port1"
    }
  ]
}
```

## Evidência de Coleta

### WMI Raw Data (Windows)
```json
{
  "Win32_ComputerSystem": {...},
  "Win32_Processor": {...},
  "Win32_PhysicalMemory": [...],
  "Win32_DiskDrive": [...],
  "Win32_VideoController": [...],
  "Win32_NetworkAdapter": [...]
}
```

### LSHW Raw Data (Linux)
```json
{
  "lshw_output": "...",
  "dmidecode_output": "...",
  "lscpu_output": "...",
  "lsblk_output": "..."
}
```

## Metadados de Coleta

- `agent_version`: Versão do agente (ex: "1.2.3")
- `collection_method`: Método usado (ex: "WMI", "lshw", "dmidecode")
- `collection_timestamp`: UTC ISO8601 (ex: "2025-09-15T05:47:49.123Z")
- `collection_hash`: SHA256 dos dados coletados
- `uptime_seconds`: Uptime do sistema em segundos

## Timestamps Padronizados

Todos os timestamps são armazenados em UTC ISO8601:
- `created_at`: Primeira vez que o dispositivo foi visto
- `updated_at`: Última atualização dos dados
- `last_seen`: Último contato com o dispositivo
- `collection_timestamp`: Quando os dados foram coletados

## Benefícios da Estrutura Aprimorada

1. **Rastreabilidade**: Identificadores únicos permitem rastrear componentes mesmo após reinstalação do OS
2. **Auditoria**: Dados brutos preservados para verificação posterior
3. **Detecção de Mudanças**: Seriais e part numbers detectam substituições de hardware
4. **Inventário Preciso**: Capacidades em bytes, velocidades exatas, versões de firmware
5. **Troubleshooting**: Dados técnicos detalhados para suporte
6. **Compliance**: Evidência completa para auditorias de conformidade
