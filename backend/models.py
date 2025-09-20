from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON, Boolean, BigInteger, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
from enum import Enum
from passlib.context import CryptContext
from sqlalchemy import Enum as SQLEnum

# Contexto para hash de senhas
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True)
    ip_address = Column(String(45), unique=True, index=True, nullable=False)
    mac_address = Column(String(17), index=True)
    device_type = Column(String(50), default="unknown")
    os = Column(String(255))
    status = Column(String(20), default="online", index=True)
    last_seen = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Identificadores Ãºnicos estÃ¡veis
    system_uuid = Column(String(36), unique=True, index=True, nullable=True)
    motherboard_serial = Column(String(255), index=True, nullable=True)
    bios_version = Column(String(255), nullable=True)
    bios_vendor = Column(String(255), nullable=True)
    bios_date = Column(String(20), nullable=True)
    chassis_serial = Column(String(255), nullable=True)

    # Metadados de coleta
    agent_version = Column(String(50), nullable=True)
    collection_method = Column(String(50), nullable=True)  # WMI, lshw, etc
    uptime_seconds = Column(BigInteger, nullable=True)

    # Timestamps em UTC ISO8601
    first_seen = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relacionamentos
    hardware_details = relationship(
        "HardwareDetail",
        back_populates="device",
        uselist=False,
        cascade="all, delete-orphan"
    )
    history_logs = relationship(
        "HistoryLog",
        back_populates="device",
        cascade="all, delete-orphan"
    )


class HardwareDetail(Base):
    __tablename__ = "hardware_details"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), unique=True, nullable=False)

    # InformaÃ§Ãµes de hardware com identificadores Ãºnicos e metadados
    cpu_info = Column(JSON, nullable=True)  # + model, vendor, cores, threads, cache_sizes
    ram_info = Column(JSON, nullable=True)  # + serial, part_number, capacity_bytes, speed_mhz, slot_location
    disk_info = Column(JSON, nullable=True)  # + serial, model, capacity_bytes, interface_type, firmware_version
    gpu_info = Column(JSON, nullable=True)  # + device_id, vendor_id, uuid, vram_bytes, driver_version
    motherboard_info = Column(JSON, nullable=True)  # + serial, model, vendor, bios_version, chipset
    network_info = Column(JSON, nullable=True)  # + mac_address, vendor, speed_mbps, driver_version
    temperature_info = Column(JSON, nullable=True)
    power_supply_info = Column(JSON, nullable=True)  # + serial, model, wattage, efficiency_rating
    installed_software = Column(JSON, nullable=True)
    usb_devices = Column(JSON, nullable=True)  # + vendor_id, product_id, serial, description
    os = Column(String(255), nullable=True)
    custom_notes = Column(Text, nullable=True)
    
    # EvidÃªncia de coleta (dados brutos)
    wmi_raw_data = Column(JSON, nullable=True)  # Dados brutos WMI para auditoria
    lshw_raw_data = Column(JSON, nullable=True)  # Dados brutos lshw para Linux
    collection_hash = Column(String(64), nullable=True)  # Hash dos dados coletados
    collection_timestamp = Column(DateTime(timezone=True), nullable=True)  # UTC ISO8601

    device = relationship("Device", back_populates="hardware_details")


class HistoryLog(Base):
    __tablename__ = "history_logs"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    component = Column(String(100), index=True)
    change_description = Column(Text, nullable=False)
    details_before = Column(Text, nullable=True)
    details_after = Column(Text, nullable=True)
    user = Column(String(100), nullable=True)
    
    # Enhanced fields for new structure
    change_hash = Column(String(64), nullable=True, index=True)  # SHA256 for deduplication
    change_type = Column(String(50), nullable=True, index=True)  # added, removed, modified, replaced
    path = Column(String(500), nullable=True)  # hardware.disks[0].serial
    old_value = Column(JSON, nullable=True)  # structured old value
    new_value = Column(JSON, nullable=True)  # structured new value
    evidence = Column(JSON, nullable=True)  # raw WMI/lshw snippets
    agent_version = Column(String(50), nullable=True)

    device = relationship("Device", back_populates="history_logs")
    
    # Add unique constraint for deduplication
    __table_args__ = (
        Index('idx_device_change_hash', 'device_id', 'change_hash', unique=True),
        Index('idx_device_timestamp', 'device_id', 'timestamp'),
        Index('idx_change_type', 'change_type'),
    )


class Snapshot(Base):
    __tablename__ = "snapshots"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    hash_sha256 = Column(String(64), unique=True, index=True, nullable=False)
    device_count = Column(Integer, nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=True)
    
    # Enhanced fields for new structure
    device_id = Column(String(255), nullable=True, index=True)  # device identifier
    agent_id = Column(String(255), nullable=True)
    agent_version = Column(String(50), nullable=True)
    data = Column(JSON, nullable=True)  # normalized hardware data
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    alert_type = Column(String(50), nullable=False, index=True)  # 'info', 'warning', 'error', 'success'
    severity = Column(String(20), default="medium", index=True)  # 'low', 'medium', 'high', 'critical'
    source = Column(String(100), nullable=True)  # 'system', 'snapshot', 'device', etc.
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=True)
    snapshot_id = Column(Integer, ForeignKey("snapshots.id", ondelete="CASCADE"), nullable=True)
    
    # Status do alerta
    is_read = Column(Boolean, default=False, index=True)
    is_resolved = Column(Boolean, default=False, index=True)
    resolved_by = Column(String(100), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadados adicionais
    alert_metadata = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relacionamentos
    device = relationship("Device", backref="alerts")
    snapshot = relationship("Snapshot", backref="alerts")

class AlertThreshold(Base):
    __tablename__ = "alert_thresholds"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=True)  # Null para thresholds globais
    metric_type = Column(String(50), nullable=False)
    threshold_value = Column(Float, nullable=False)
    comparison = Column(String(2), nullable=False)  # '>', '<', '=='
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())#   = = =   M O D E L O S   D E   S E G U R A N Ç A   E   A U D I T O R I A   = = = 
 
 f r o m   e n u m   i m p o r t   E n u m 
 
 f r o m   e n u m   i m p o r t   E n u m 
 
 f r o m   p a s s l i b . c o n t e x t   i m p o r t   C r y p t C o n t e x t 
 
 f r o m   s q l a l c h e m y   i m p o r t   C o l u m n ,   I n t e g e r ,   S t r i n g ,   D a t e T i m e ,   F o r e i g n K e y ,   T e x t ,   B o o l e a n ,   E n u m   a s   S Q L E n u m 
 
 f r o m   s q l a l c h e m y . o r m   i m p o r t   r e l a t i o n s h i p 
 
 f r o m   s q l a l c h e m y . s q l   i m p o r t   f u n c 
 
 
 
 #   C o n t e x t o   p a r a   h a s h   d e   s e n h a s 
 
 p w d _ c o n t e x t   =   C r y p t C o n t e x t ( s c h e m e s = [ ' b c r y p t ' ] ,   d e p r e c a t e d = ' a u t o ' ) 
 
 
 
 c l a s s   U s e r R o l e ( s t r ,   E n u m ) : 
 
         A D M I N   =   ' a d m i n ' 
 
         T E C H N I C I A N   =   ' t e c h n i c i a n ' 
 
         R E A D O N L Y   =   ' r e a d o n l y ' 
 
 
 
 c l a s s   U s e r ( B a s e ) : 
 
         _ _ t a b l e n a m e _ _   =   ' u s e r s ' 
 
         
 
         i d   =   C o l u m n ( I n t e g e r ,   p r i m a r y _ k e y = T r u e ,   i n d e x = T r u e ) 
 
         u s e r n a m e   =   C o l u m n ( S t r i n g ( 5 0 ) ,   u n i q u e = T r u e ,   i n d e x = T r u e ,   n u l l a b l e = F a l s e ) 
 
         e m a i l   =   C o l u m n ( S t r i n g ( 1 0 0 ) ,   u n i q u e = T r u e ,   i n d e x = T r u e ,   n u l l a b l e = F a l s e ) 
 
         f u l l _ n a m e   =   C o l u m n ( S t r i n g ( 1 0 0 ) ) 
 
         h a s h e d _ p a s s w o r d   =   C o l u m n ( S t r i n g ( 2 5 5 ) ,   n u l l a b l e = F a l s e ) 
 
         r o l e   =   C o l u m n ( S Q L E n u m ( U s e r R o l e ) ,   d e f a u l t = U s e r R o l e . R E A D O N L Y ,   n u l l a b l e = F a l s e ) 
 
         i s _ a c t i v e   =   C o l u m n ( B o o l e a n ,   d e f a u l t = T r u e ) 
 
         i s _ a d _ u s e r   =   C o l u m n ( B o o l e a n ,   d e f a u l t = F a l s e )     #   P a r a   u s u á r i o s   d o   A c t i v e   D i r e c t o r y 
 
         a d _ u s e r n a m e   =   C o l u m n ( S t r i n g ( 5 0 ) )     #   U s e r n a m e   n o   A D 
 
         l a s t _ l o g i n   =   C o l u m n ( D a t e T i m e ( t i m e z o n e = T r u e ) ) 
 
         c r e a t e d _ a t   =   C o l u m n ( D a t e T i m e ( t i m e z o n e = T r u e ) ,   s e r v e r _ d e f a u l t = f u n c . n o w ( ) ) 
 
         u p d a t e d _ a t   =   C o l u m n ( D a t e T i m e ( t i m e z o n e = T r u e ) ,   o n u p d a t e = f u n c . n o w ( ) ) 
 
         
 
         #   R e l a c i o n a m e n t o s 
 
         a u d i t _ l o g s   =   r e l a t i o n s h i p ( ' A u d i t L o g ' ,   b a c k _ p o p u l a t e s = ' u s e r ' ) 
 
         
 
         d e f   v e r i f y _ p a s s w o r d ( s e l f ,   p a s s w o r d :   s t r )   - >   b o o l : 
 
                 r e t u r n   p w d _ c o n t e x t . v e r i f y ( p a s s w o r d ,   s e l f . h a s h e d _ p a s s w o r d ) 
 
         
 
         d e f   s e t _ p a s s w o r d ( s e l f ,   p a s s w o r d :   s t r ) : 
 
                 s e l f . h a s h e d _ p a s s w o r d   =   p w d _ c o n t e x t . h a s h ( p a s s w o r d ) 
 
 
 
 c l a s s   A u d i t A c t i o n ( s t r ,   E n u m ) : 
 
         C R E A T E   =   ' c r e a t e ' 
 
         R E A D   =   ' r e a d ' 
 
         U P D A T E   =   ' u p d a t e ' 
 
         D E L E T E   =   ' d e l e t e ' 
 
         L O G I N   =   ' l o g i n ' 
 
         L O G O U T   =   ' l o g o u t ' 
 
         E X P O R T   =   ' e x p o r t ' 
 
 
 
 c l a s s   A u d i t L o g ( B a s e ) : 
 
         _ _ t a b l e n a m e _ _   =   ' a u d i t _ l o g s ' 
 
         
 
         i d   =   C o l u m n ( I n t e g e r ,   p r i m a r y _ k e y = T r u e ,   i n d e x = T r u e ) 
 
         u s e r _ i d   =   C o l u m n ( I n t e g e r ,   F o r e i g n K e y ( ' u s e r s . i d ' ) ,   n u l l a b l e = T r u e )     #   P o d e   s e r   N o n e   p a r a   a ç õ e s   d o   s i s t e m a 
 
         a c t i o n   =   C o l u m n ( S Q L E n u m ( A u d i t A c t i o n ) ,   n u l l a b l e = F a l s e ) 
 
         r e s o u r c e   =   C o l u m n ( S t r i n g ( 1 0 0 ) ,   n u l l a b l e = F a l s e )     #   E x :   ' d e v i c e s ' ,   ' a l e r t s ' ,   ' s n a p s h o t s ' 
 
         r e s o u r c e _ i d   =   C o l u m n ( S t r i n g ( 1 0 0 ) )     #   I D   d o   r e c u r s o   a f e t a d o 
 
         d e s c r i p t i o n   =   C o l u m n ( T e x t ) 
 
         i p _ a d d r e s s   =   C o l u m n ( S t r i n g ( 4 5 ) )     #   I P v 4 / I P v 6 
 
         u s e r _ a g e n t   =   C o l u m n ( T e x t ) 
 
         s u c c e s s   =   C o l u m n ( B o o l e a n ,   d e f a u l t = T r u e ) 
 
         e r r o r _ m e s s a g e   =   C o l u m n ( T e x t ) 
 
         m e t a d a t a   =   C o l u m n ( J S O N )     #   D a d o s   a d i c i o n a i s   s o b r e   a   a ç ã o 
 
         t i m e s t a m p   =   C o l u m n ( D a t e T i m e ( t i m e z o n e = T r u e ) ,   s e r v e r _ d e f a u l t = f u n c . n o w ( ) ,   i n d e x = T r u e ) 
 
         
 
         #   R e l a c i o n a m e n t o s 
 
         u s e r   =   r e l a t i o n s h i p ( ' U s e r ' ,   b a c k _ p o p u l a t e s = ' a u d i t _ l o g s ' ) 
 
 
