🏗 models.py

👉 Define as tabelas e relacionamentos no SQLAlchemy ORM.

Device

Dados básicos (nome, IP, MAC, status, etc).

Relacionamento: hardware_details (1:1) e history_logs (1:N).

HardwareDetail

JSON para CPU, RAM, GPU, discos, rede, etc.

Relacionamento com Device.

HistoryLog

Registra mudanças (componente, descrição, antes/depois, usuário, timestamp).

Relacionamento com Device.

📑 schemas.py

👉 Define modelos de dados no Pydantic v2 para validação/retorno.

HardwareDetailBase / Create / Response

HistoryLogBase / Create / Response

DeviceBase / Create / Update / Response

DeviceFull
→ Inclui history_logs: list[HistoryLog] = Field(default_factory=list)
→ Usado no endpoint /devices/{id}/full.

⚠️ Padrão:

Tipagem moderna (str | None, list[dict] | None).

Field(default_factory=list) → evita problema de lista mutável.

model_config = {"from_attributes": True} → validação direta do ORM.

⚙️ crud.py

👉 Contém toda a lógica de banco de dados.

Dispositivos

get_device, get_device_by_ip_or_mac, get_devices

create_device → cria dispositivo (ou atualiza se MAC já existe).

update_device → atualiza dispositivo existente.

create_or_update_device → cria ou atualiza com base em IP/MAC.

delete_device → remove dispositivo.

Histórico

create_history_log → cria log para dispositivo.

get_history_logs → retorna logs de um dispositivo.

get_all_history_logs → retorna todos os logs (auditoria global).

⚠️ Cuidados aplicados:

Verificação hasattr(..., "model_dump") → funciona tanto com dict quanto com modelo Pydantic.

datetime.now(timezone.utc) → para timestamps consistentes.

🖥 devices.py (Router)

👉 Gerencia dispositivos e seus próprios logs.

POST /devices/ → cria ou atualiza dispositivo + registra logs de alteração.

GET /devices/ → lista todos os dispositivos.

GET /devices/{id} → busca dispositivo específico.

PUT /devices/{id} → atualiza dispositivo.

DELETE /devices/{id} → remove dispositivo.

POST /devices/{id}/history → cria log manual para o dispositivo.

GET /devices/{id}/history → retorna apenas os logs daquele dispositivo.

GET /devices/{id}/full → retorna dispositivo + todos os seus logs.

⚡ Função auxiliar:

generate_change_logs → compara valores antigos/novos e gera mensagens automáticas.

📝 history_logs.py (Router)

👉 Usado apenas para auditoria global.

GET /history_logs/
→ retorna todos os logs do sistema, independente do dispositivo.
→ útil para debug e auditoria.

⚠️ Atenção: pode trazer muitos registros, use com paginação (skip, limit).

📌 Fluxo Geral

O agente coleta dados → envia para POST /devices/.

Se o dispositivo já existe:

É atualizado.

Mudanças são detectadas (generate_change_logs).

Logs são salvos em history_logs.

Se o dispositivo não existe:

É criado.

Log de criação é salvo.

Consultas:

/devices/{id}/history → histórico só daquele dispositivo.

/devices/{id}/full → dispositivo + histórico.

/history_logs/ → todos os logs do sistema (auditoria).