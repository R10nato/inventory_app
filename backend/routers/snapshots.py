from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import os

import models, schemas, database, crud
from export_service import export_devices_snapshot

router = APIRouter(
    prefix="/snapshots",
    tags=["Snapshots"],
    responses={404: {"description": "Not found"}},
)

# Dependency para obter sessão do DB
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/", response_model=List[schemas.Snapshot])
def get_all_snapshots(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retorna todos os snapshots registrados no sistema.
    """
    snapshots = crud.get_snapshots(db, skip=skip, limit=limit)
    return [schemas.Snapshot.model_validate(snapshot) for snapshot in snapshots]


@router.get("/{snapshot_id}", response_model=schemas.Snapshot)
def get_snapshot_by_id(snapshot_id: int, db: Session = Depends(get_db)):
    """
    Retorna um snapshot específico pelo ID.
    """
    snapshot = crud.get_snapshot(db, snapshot_id=snapshot_id)
    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot não encontrado.")
    return schemas.Snapshot.model_validate(snapshot)


@router.post("/", response_model=schemas.Snapshot, status_code=status.HTTP_201_CREATED)
def create_new_snapshot(db: Session = Depends(get_db)):
    """
    Cria um novo snapshot do estado atual de todos os dispositivos.
    """
    try:
        # Gera o snapshot
        result = export_devices_snapshot()
        if result is None or result[0] is None:
            raise Exception("Falha ao gerar snapshot")
        
        filepath, snapshot_hash = result
        
        # Obter tamanho do arquivo
        file_size = os.path.getsize(filepath) if filepath and os.path.exists(filepath) else None
        
        # Contar dispositivos
        devices = crud.get_devices(db)
        device_count = len(devices)
        
        # Criar registro no banco
        snapshot_data = schemas.SnapshotCreate(
            hash_sha256=snapshot_hash,
            device_count=device_count,
            file_path=filepath,
            file_size=file_size
        )
        
        created_snapshot = crud.create_snapshot(db, snapshot=snapshot_data)
        return schemas.Snapshot.model_validate(created_snapshot)
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Erro ao criar snapshot: {str(e)}"
        )


@router.post("/compare", status_code=status.HTTP_200_OK)
def compare_latest_snapshots(db: Session = Depends(get_db)):
    """
    Compara os dois snapshots mais recentes e gera logs de histórico.
    """
    try:
        from compare_snapshots import generate_comparison_report
        
        changes = generate_comparison_report()
        
        if changes is None:
            return {
                "message": "Nenhuma alteração detectada ou snapshots insuficientes",
                "changes_count": 0
            }
        
        return {
            "message": f"{len(changes)} alterações detectadas e registradas",
            "changes_count": len(changes),
            "changes": changes
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao comparar snapshots: {str(e)}"
        )


@router.delete("/{snapshot_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_snapshot(snapshot_id: int, db: Session = Depends(get_db)):
    """
    Remove um snapshot do sistema (apenas o registro do banco, não o arquivo).
    """
    snapshot = crud.delete_snapshot(db, snapshot_id=snapshot_id)
    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot não encontrado.")
    return None
