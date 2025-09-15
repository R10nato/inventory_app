import wmi
import json

def test_disk_temperature_collection():
    """Testa a coleta de temperatura dos discos"""
    
    print("=== TESTE DE COLETA DE TEMPERATURA DOS DISCOS ===\n")
    
    # 1. Listar discos disponíveis
    print("1. DISCOS DETECTADOS:")
    try:
        w = wmi.WMI()
        for i, disk in enumerate(w.Win32_DiskDrive()):
            print(f"   Disk {i}: {disk.Model}")
            print(f"      Serial: {disk.SerialNumber.strip() if disk.SerialNumber else 'N/A'}")
            print(f"      Size: {round(int(disk.Size) / (1024**3), 2) if disk.Size else 0} GB")
            print()
    except Exception as e:
        print(f"   Erro ao listar discos: {e}")
    
    # 2. Testar SMART data
    print("2. SMART DATA (MSStorageDriver_FailurePredictData):")
    try:
        w = wmi.WMI(namespace=r"root\wmi")
        for disk in w.MSStorageDriver_FailurePredictData():
            print(f"   Instance: {disk.InstanceName}")
            if hasattr(disk, 'VendorSpecific') and disk.VendorSpecific:
                vendor_data = disk.VendorSpecific
                print(f"   VendorSpecific length: {len(vendor_data)}")
                
                # Procurar atributo 194 (temperatura)
                if len(vendor_data) >= 12 * 194:
                    temp_offset = 12 * 194 + 5
                    if temp_offset < len(vendor_data):
                        temp_raw = vendor_data[temp_offset]
                        print(f"   Temperatura (offset {temp_offset}): {temp_raw}°C")
                    else:
                        print(f"   Offset {temp_offset} fora do range")
                else:
                    print(f"   VendorSpecific muito pequeno para conter atributo 194")
            else:
                print("   Sem VendorSpecific data")
            print()
    except Exception as e:
        print(f"   Erro SMART data: {e}")
    
    # 3. Testar nossa função atual
    print("3. TESTE DA FUNÇÃO get_all_temperatures():")
    try:
        from sensors import get_all_temperatures
        result = get_all_temperatures()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"   Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_disk_temperature_collection()
