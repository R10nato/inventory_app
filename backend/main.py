from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
import models, database
import logging

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

from apscheduler.schedulers.background import BackgroundScheduler
import atexit

from export_service import export_devices_snapshot
from compare_snapshots import generate_comparison_report

# Criar tabelas no banco ao iniciar (idealmente usar Alembic em produção)
try:
    models.Base.metadata.create_all(bind=database.engine)
    logger.info("Database tables created successfully")
except Exception as e:
    logger.error(f"Error creating database tables: {e}")
    raise

# Instância do FastAPI
app = FastAPI(
    title="Inventory & Monitoring API",
    description="API for managing network device inventory and hardware details.",
    version="0.1.0"
)

# Configuração de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency para sessão do banco
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/", tags=["Root"])
def read_root():
    """Provides a simple welcome message."""
    return {"message": "Welcome to the Inventory & Monitoring API"}

# Importando e incluindo routers
from routers import devices, history_logs
app.include_router(devices.router)
app.include_router(history_logs.router)

# Configuração do agendador
scheduler = BackgroundScheduler()
# Exportação semanal automática
scheduler.add_job(export_devices_snapshot, "interval", weeks=1, id="weekly_export")
# Comparação semanal automática
scheduler.add_job(generate_comparison_report, "interval", weeks=1, id="weekly_comparison")
scheduler.start()

# Garantir que o scheduler feche ao encerrar o servidor
atexit.register(lambda: scheduler.shutdown())
