import sys
import os
sys.path.append('backend')

from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Criar conexão direta com o banco
DATABASE_URL = "sqlite:///backend/inventory.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
import models
import schemas
import json
from datetime import datetime

def test_history_endpoint():
    db = SessionLocal()
    
    try:
        # Buscar logs diretamente do banco
        device_id = 1
        query = db.query(models.HistoryLog).filter(models.HistoryLog.device_id == device_id)
        
        total = query.count()
        logs = query.order_by(models.HistoryLog.timestamp.desc()).limit(5).all()
        
        print(f"Total de logs encontrados: {total}")
        print(f"Processando {len(logs)} logs...")
        
        # Tentar serializar cada log
        for i, log in enumerate(logs):
            print(f"\nLog {i+1}:")
            print(f"  ID: {log.id}")
            print(f"  Device ID: {log.device_id}")
            print(f"  Component: {log.component}")
            print(f"  Change Type: {log.change_type}")
            print(f"  Timestamp: {log.timestamp}")
            
            try:
                # Tentar criar o schema Pydantic
                log_schema = schemas.HistoryLog.model_validate(log)
                print("  [OK] Schema Pydantic criado com sucesso")
                
                # Tentar converter para dict
                log_dict = log_schema.model_dump()
                print("  [OK] Convertido para dict com sucesso")
                
                # Tentar serializar para JSON
                json_str = json.dumps(log_dict, default=str)
                print(f"  [OK] Serializado para JSON ({len(json_str)} bytes)")
                
            except Exception as e:
                print(f"  [ERRO] ao processar: {e}")
                print(f"    Tipo do erro: {type(e).__name__}")
                
                # Verificar campos problemáticos
                print("  Verificando campos:")
                for field in ['old_value', 'new_value', 'evidence']:
                    value = getattr(log, field, None)
                    if value is not None:
                        print(f"    {field}: tipo={type(value)}, valor={str(value)[:50]}...")
        
        # Tentar criar a resposta paginada
        print("\n\nTentando criar resposta paginada...")
        try:
            response = schemas.PaginatedResponse[schemas.HistoryLog](
                items=[schemas.HistoryLog.model_validate(log) for log in logs],
                total=total,
                skip=0,
                limit=5
            )
            print("[OK] Resposta paginada criada com sucesso")
            
            # Tentar serializar
            response_dict = response.model_dump()
            json_str = json.dumps(response_dict, default=str)
            print(f"[OK] Resposta serializada ({len(json_str)} bytes)")
            
        except Exception as e:
            print(f"[ERRO] ao criar resposta paginada: {e}")
            
    except Exception as e:
        print(f"ERRO GERAL: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        db.close()

if __name__ == "__main__":
    test_history_endpoint()
