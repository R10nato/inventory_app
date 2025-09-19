import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, get_db
from models import AlertThreshold
from crud_alert_thresholds import (
    create_threshold,
    get_threshold,
    get_thresholds,
    update_threshold,
    delete_threshold,
    check_threshold_violation
)
from alert_threshold_schemas import AlertThresholdCreate, AlertThresholdUpdate

# Configuração do banco de dados de teste
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """Cria uma sessão de banco de dados para testes"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def sample_threshold_data():
    """Dados de exemplo para threshold"""
    return {
        "metric_type": "cpu",
        "threshold_value": 80.0,
        "comparison": ">",
        "is_active": True,
        "device_id": 1
    }

class TestThresholdCRUD:
    """Testes para operações CRUD de thresholds"""

    def test_create_threshold(self, db_session, sample_threshold_data):
        """Testa criação de threshold"""
        threshold = create_threshold(db_session, sample_threshold_data)
        assert threshold.id is not None
        assert threshold.metric_type == "cpu"
        assert threshold.threshold_value == 80.0
        assert threshold.comparison == ">"
        assert threshold.is_active == True
        assert threshold.device_id == 1

    def test_get_threshold(self, db_session, sample_threshold_data):
        """Testa busca de threshold por ID"""
        created = create_threshold(db_session, sample_threshold_data)
        retrieved = get_threshold(db_session, created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.metric_type == created.metric_type

    def test_get_thresholds_with_filters(self, db_session):
        """Testa busca de thresholds com filtros"""
        # Criar thresholds de teste
        thresholds_data = [
            {"metric_type": "cpu", "threshold_value": 80.0, "comparison": ">", "is_active": True, "device_id": 1},
            {"metric_type": "ram", "threshold_value": 90.0, "comparison": ">", "is_active": True, "device_id": 1},
            {"metric_type": "cpu", "threshold_value": 70.0, "comparison": ">", "is_active": False, "device_id": 2},
        ]

        for data in thresholds_data:
            create_threshold(db_session, data)

        # Testar filtro por device_id
        results = get_thresholds(db_session, device_id=1)
        assert len(results) == 2

        # Testar filtro por metric_type
        results = get_thresholds(db_session, metric_type="cpu")
        assert len(results) == 2

        # Testar filtro por status ativo
        results = get_thresholds(db_session, is_active=False)
        assert len(results) == 1

    def test_update_threshold(self, db_session, sample_threshold_data):
        """Testa atualização de threshold"""
        created = create_threshold(db_session, sample_threshold_data)

        update_data = {"threshold_value": 85.0, "is_active": False}
        updated = update_threshold(db_session, created.id, update_data)

        assert updated is not None
        assert updated.threshold_value == 85.0
        assert updated.is_active == False
        assert updated.metric_type == "cpu"  # Não mudou

    def test_delete_threshold(self, db_session, sample_threshold_data):
        """Testa exclusão de threshold"""
        created = create_threshold(db_session, sample_threshold_data)

        # Verificar que existe
        assert get_threshold(db_session, created.id) is not None

        # Deletar
        result = delete_threshold(db_session, created.id)
        assert result is not None

        # Verificar que foi removido
        assert get_threshold(db_session, created.id) is None

class TestThresholdLogic:
    """Testes para lógica de verificação de thresholds"""

    def test_check_threshold_violation_greater_than(self, db_session):
        """Testa verificação de threshold com operador '>' """
        # Criar threshold: CPU > 80
        threshold_data = {
            "metric_type": "cpu",
            "threshold_value": 80.0,
            "comparison": ">",
            "is_active": True,
            "device_id": 1
        }
        create_threshold(db_session, threshold_data)

        # Testar valor que viola (85 > 80)
        violations = check_threshold_violation(db_session, "cpu", 85.0, 1)
        assert len(violations) == 1
        assert violations[0]["violated"] == True

        # Testar valor que não viola (75 < 80)
        violations = check_threshold_violation(db_session, "cpu", 75.0, 1)
        assert len(violations) == 1
        assert violations[0]["violated"] == False

    def test_check_threshold_violation_less_than(self, db_session):
        """Testa verificação de threshold com operador '<' """
        # Criar threshold: Temperatura < 80
        threshold_data = {
            "metric_type": "temperature",
            "threshold_value": 80.0,
            "comparison": "<",
            "is_active": True,
            "device_id": 1
        }
        create_threshold(db_session, threshold_data)

        # Testar valor que viola (85 > 80, mas operador é <)
        violations = check_threshold_violation(db_session, "temperature", 85.0, 1)
        assert len(violations) == 1
        assert violations[0]["violated"] == False

        # Testar valor que viola (75 < 80)
        violations = check_threshold_violation(db_session, "temperature", 75.0, 1)
        assert len(violations) == 1
        assert violations[0]["violated"] == True

    def test_check_threshold_violation_multiple_thresholds(self, db_session):
        """Testa verificação com múltiplos thresholds"""
        thresholds_data = [
            {"metric_type": "cpu", "threshold_value": 80.0, "comparison": ">", "is_active": True, "device_id": 1},
            {"metric_type": "ram", "threshold_value": 90.0, "comparison": ">", "is_active": True, "device_id": 1},
        ]

        for data in thresholds_data:
            create_threshold(db_session, data)

        # Testar valor que viola CPU mas não RAM
        violations = check_threshold_violation(db_session, "cpu", 85.0, 1)
        assert len(violations) == 1
        assert violations[0]["metric_type"] == "cpu"

        # Testar valor que viola ambos
        violations = check_threshold_violation(db_session, "cpu", 95.0, 1)
        assert len(violations) == 1  # Apenas CPU, pois perguntamos apenas por CPU

    def test_check_threshold_violation_inactive_threshold(self, db_session):
        """Testa que thresholds inativos não geram violações"""
        threshold_data = {
            "metric_type": "cpu",
            "threshold_value": 80.0,
            "comparison": ">",
            "is_active": False,  # Inativo
            "device_id": 1
        }
        create_threshold(db_session, threshold_data)

        # Mesmo valor que violaria, não deve gerar alerta pois está inativo
        violations = check_threshold_violation(db_session, "cpu", 85.0, 1)
        assert len(violations) == 0

class TestThresholdSchemas:
    """Testes para validação de schemas Pydantic"""

    def test_alert_threshold_create_valid(self):
        """Testa criação de schema válido"""
        data = AlertThresholdCreate(
            metric_type="cpu",
            threshold_value=80.0,
            comparison=">",
            is_active=True,
            device_id=1
        )
        assert data.metric_type == "cpu"
        assert data.threshold_value == 80.0

    def test_alert_threshold_create_invalid_comparison(self):
        """Testa validação de operador de comparação inválido"""
        with pytest.raises(ValueError):
            AlertThresholdCreate(
                metric_type="cpu",
                threshold_value=80.0,
                comparison="invalid",  # Inválido
                is_active=True
            )

    def test_alert_threshold_create_negative_value(self):
        """Testa validação de valor negativo"""
        with pytest.raises(ValueError):
            AlertThresholdCreate(
                metric_type="cpu",
                threshold_value=-10.0,  # Negativo
                comparison=">",
                is_active=True
            )

if __name__ == "__main__":
    pytest.main([__file__])
