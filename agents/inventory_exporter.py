import os
import json
from datetime import datetime, timedelta
import logging

from core.collector import collect_local_hardware_data
from core.utils import get_hostname, get_ip_address

EXPORT_DIR = os.path.join(os.path.dirname(__file__), "exports")
os.makedirs(EXPORT_DIR, exist_ok=True)

logger = logging.getLogger("inventory_export")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

def generate_export_filename():
    now = datetime.now()
    hostname = get_hostname()
    return os.path.join(EXPORT_DIR, f"inventory_{hostname}_{now.strftime('%Y%m%d_%H%M%S')}.json")

def export_inventory():
    """
    Coleta o inventário atual e exporta para arquivo JSON com timestamp.
    """
    try:
        inventory = collect_local_hardware_data()
        inventory["ip_address"] = get_ip_address()
        inventory["hostname"] = get_hostname()
        inventory["timestamp"] = datetime.now().isoformat()

        export_path = generate_export_filename()
        with open(export_path, "w", encoding="utf-8") as f:
            json.dump(inventory, f, indent=4, ensure_ascii=False)

        logger.info(f"Inventário exportado com sucesso: {export_path}")
        return export_path
    except Exception as e:
        logger.error(f"Erro ao exportar inventário: {str(e)}")
        return None

if __name__ == "__main__":
    export_inventory()
