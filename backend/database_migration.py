"""
Script de migração de banco de dados para adicionar novos campos aos modelos existentes.
Executa ALTER TABLE para adicionar as colunas que foram adicionadas aos models.py.
"""

import sqlite3
import os
from datetime import datetime


class DatabaseMigrator:
    """Classe para gerenciar migrações de banco de dados"""
    
    def __init__(self, db_path: str = "inventory.db"):
        self.db_path = db_path
        self.migrations = []
        self._setup_migrations()
    
    def _setup_migrations(self):
        """Define todas as migrações necessárias"""
        
        # Migração 1: Adicionar campos de identificadores únicos à tabela devices
        self.migrations.append({
            'name': 'add_unique_identifiers_to_devices',
            'description': 'Adiciona system_uuid, motherboard_serial, bios_* e chassis_serial',
            'sql_commands': [
                'ALTER TABLE devices ADD COLUMN system_uuid VARCHAR(36)',
                'ALTER TABLE devices ADD COLUMN motherboard_serial VARCHAR(255)',
                'ALTER TABLE devices ADD COLUMN bios_version VARCHAR(255)',
                'ALTER TABLE devices ADD COLUMN bios_vendor VARCHAR(255)',
                'ALTER TABLE devices ADD COLUMN bios_date VARCHAR(20)',
                'ALTER TABLE devices ADD COLUMN chassis_serial VARCHAR(255)',
            ]
        })
        
        # Migração 2: Adicionar metadados de coleta à tabela devices
        self.migrations.append({
            'name': 'add_collection_metadata_to_devices',
            'description': 'Adiciona agent_version, collection_method, uptime_seconds',
            'sql_commands': [
                'ALTER TABLE devices ADD COLUMN agent_version VARCHAR(50)',
                'ALTER TABLE devices ADD COLUMN collection_method VARCHAR(50)',
                'ALTER TABLE devices ADD COLUMN uptime_seconds BIGINT',
            ]
        })
        
        # Migração 3: Adicionar timestamps UTC à tabela devices
        self.migrations.append({
            'name': 'add_utc_timestamps_to_devices',
            'description': 'Adiciona first_seen timestamp',
            'sql_commands': [
                'ALTER TABLE devices ADD COLUMN first_seen TIMESTAMP',
            ]
        })
        
        # Migração 5: Adicionar updated_at ausente
        self.migrations.append({
            'name': 'add_missing_updated_at_to_devices',
            'description': 'Adiciona updated_at timestamp ausente',
            'sql_commands': [
                'ALTER TABLE devices ADD COLUMN updated_at TIMESTAMP',
            ]
        })
        
        # Migração 4: Adicionar campos expandidos à tabela hardware_details
        self.migrations.append({
            'name': 'add_expanded_fields_to_hardware_details',
            'description': 'Adiciona seriais, metadados e evidência de coleta',
            'sql_commands': [
                'ALTER TABLE hardware_details ADD COLUMN cpu_serial VARCHAR(255)',
                'ALTER TABLE hardware_details ADD COLUMN ram_serial VARCHAR(255)',
                'ALTER TABLE hardware_details ADD COLUMN disk_serial VARCHAR(255)',
                'ALTER TABLE hardware_details ADD COLUMN gpu_uuid VARCHAR(255)',
                'ALTER TABLE hardware_details ADD COLUMN network_mac VARCHAR(255)',
                'ALTER TABLE hardware_details ADD COLUMN psu_serial VARCHAR(255)',
                'ALTER TABLE hardware_details ADD COLUMN usb_serial VARCHAR(255)',
                'ALTER TABLE hardware_details ADD COLUMN part_number VARCHAR(255)',
                'ALTER TABLE hardware_details ADD COLUMN capacity_bytes BIGINT',
                'ALTER TABLE hardware_details ADD COLUMN speed VARCHAR(100)',
                'ALTER TABLE hardware_details ADD COLUMN firmware_version VARCHAR(100)',
                'ALTER TABLE hardware_details ADD COLUMN slot_location VARCHAR(100)',
                'ALTER TABLE hardware_details ADD COLUMN wmi_raw_data TEXT',
                'ALTER TABLE hardware_details ADD COLUMN lshw_raw_data TEXT',
                'ALTER TABLE hardware_details ADD COLUMN collection_hash VARCHAR(64)',
                'ALTER TABLE hardware_details ADD COLUMN collection_timestamp TIMESTAMP',
            ]
        })
    
    def column_exists(self, cursor, table_name: str, column_name: str) -> bool:
        """Verifica se uma coluna existe na tabela"""
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [row[1] for row in cursor.fetchall()]
        return column_name in columns
    
    def table_exists(self, cursor, table_name: str) -> bool:
        """Verifica se uma tabela existe"""
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        return cursor.fetchone() is not None
    
    def run_migration(self, migration: dict, cursor) -> bool:
        """Executa uma migração específica"""
        print(f"\n[MIGRATION] Executando: {migration['name']}")
        print(f"[MIGRATION] Descrição: {migration['description']}")
        
        success_count = 0
        total_commands = len(migration['sql_commands'])
        
        for sql_command in migration['sql_commands']:
            try:
                # Extrair nome da tabela e coluna do comando ALTER TABLE
                if 'ALTER TABLE' in sql_command and 'ADD COLUMN' in sql_command:
                    parts = sql_command.split()
                    table_name = parts[2]
                    column_name = parts[5]
                    
                    # Verificar se a coluna já existe
                    if self.column_exists(cursor, table_name, column_name):
                        print(f"[MIGRATION] Coluna {table_name}.{column_name} já existe - pulando")
                        success_count += 1
                        continue
                
                # Executar comando
                cursor.execute(sql_command)
                print(f"[MIGRATION] OK {sql_command}")
                success_count += 1
                
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e).lower():
                    print(f"[MIGRATION] WARNING Coluna ja existe - pulando: {sql_command}")
                    success_count += 1
                else:
                    print(f"[MIGRATION] ERROR: {sql_command} - {e}")
        
        success_rate = success_count / total_commands
        print(f"[MIGRATION] Concluída: {success_count}/{total_commands} comandos executados ({success_rate:.1%})")
        
        return success_rate >= 0.8  # Considerar sucesso se 80%+ dos comandos funcionaram
    
    def migrate(self) -> bool:
        """Executa todas as migrações pendentes"""
        
        if not os.path.exists(self.db_path):
            print(f"[MIGRATION] Banco de dados {self.db_path} não encontrado!")
            return False
        
        print(f"[MIGRATION] Iniciando migração do banco: {self.db_path}")
        print(f"[MIGRATION] Timestamp: {datetime.now().isoformat()}")
        
        # Fazer backup do banco antes da migração
        backup_path = f"{self.db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        try:
            import shutil
            shutil.copy2(self.db_path, backup_path)
            print(f"[MIGRATION] Backup criado: {backup_path}")
        except Exception as e:
            print(f"[MIGRATION] WARNING Falha ao criar backup: {e}")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Verificar se as tabelas principais existem
            if not self.table_exists(cursor, 'devices'):
                print("[MIGRATION] ERROR Tabela 'devices' nao encontrada!")
                return False
            
            if not self.table_exists(cursor, 'hardware_details'):
                print("[MIGRATION] ERROR Tabela 'hardware_details' nao encontrada!")
                return False
            
            # Executar migrações
            successful_migrations = 0
            
            for migration in self.migrations:
                if self.run_migration(migration, cursor):
                    successful_migrations += 1
                else:
                    print(f"[MIGRATION] WARNING Migracao {migration['name']} teve problemas")
            
            # Commit das mudanças
            conn.commit()
            
            # Verificar integridade do banco
            cursor.execute("PRAGMA integrity_check")
            integrity_result = cursor.fetchone()[0]
            
            if integrity_result == "ok":
                print("[MIGRATION] OK Verificacao de integridade: OK")
            else:
                print(f"[MIGRATION] WARNING Problema de integridade: {integrity_result}")
            
            conn.close()
            
            success_rate = successful_migrations / len(self.migrations)
            print(f"\n[MIGRATION] Migração concluída!")
            print(f"[MIGRATION] Migrações bem-sucedidas: {successful_migrations}/{len(self.migrations)} ({success_rate:.1%})")
            
            return success_rate >= 0.8
            
        except Exception as e:
            print(f"[MIGRATION] ERROR Erro durante migracao: {e}")
            return False
    
    def show_current_schema(self):
        """Mostra o schema atual das tabelas principais"""
        
        if not os.path.exists(self.db_path):
            print(f"[SCHEMA] Banco de dados {self.db_path} não encontrado!")
            return
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for table_name in ['devices', 'hardware_details', 'snapshots', 'alerts']:
                if self.table_exists(cursor, table_name):
                    print(f"\n[SCHEMA] Tabela: {table_name}")
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = cursor.fetchall()
                    
                    for col in columns:
                        col_id, name, data_type, not_null, default_val, pk = col
                        nullable = "NOT NULL" if not_null else "NULL"
                        primary = "PRIMARY KEY" if pk else ""
                        print(f"  {name:<25} {data_type:<15} {nullable:<10} {primary}")
                else:
                    print(f"\n[SCHEMA] Tabela {table_name}: NÃO ENCONTRADA")
            
            conn.close()
            
        except Exception as e:
            print(f"[SCHEMA] Erro ao mostrar schema: {e}")


def main():
    """Função principal para executar a migração"""
    
    migrator = DatabaseMigrator()
    
    print("=" * 60)
    print("MIGRAÇÃO DE BANCO DE DADOS - INVENTORY APP")
    print("=" * 60)
    
    # Mostrar schema atual
    print("\n1. SCHEMA ATUAL:")
    migrator.show_current_schema()
    
    # Executar migração
    print("\n2. EXECUTANDO MIGRAÇÕES:")
    success = migrator.migrate()
    
    # Mostrar schema após migração
    print("\n3. SCHEMA APÓS MIGRAÇÃO:")
    migrator.show_current_schema()
    
    if success:
        print("\n[SUCCESS] MIGRACAO CONCLUIDA COM SUCESSO!")
        print("O banco de dados foi atualizado para incluir os novos campos.")
    else:
        print("\n[WARNING] MIGRACAO TEVE PROBLEMAS!")
        print("Verifique os logs acima para detalhes.")
    
    return success


if __name__ == "__main__":
    main()
