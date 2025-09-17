import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs.jsx'
import DeviceEditDialog from './DeviceEditDialog.jsx'
import TimelineView from './history/TimelineView'
import { 
  ArrowLeft, Monitor, Laptop, Smartphone, Printer,
  Cpu, MemoryStick, HardDrive, Wifi, Clock, Thermometer,
  Package, History, Edit, Info, Usb, User, Activity, AlertCircle
} from 'lucide-react'
import { Progress } from '@/components/ui/progress.jsx'
import { Alert, AlertDescription } from '@/components/ui/alert.jsx'

const API_BASE = "http://localhost:8000"

const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  return isNaN(date.getTime()) ? 'N/A' : date.toLocaleString('pt-BR')
}

const safeNumber = (value) => {
  const num = Number(value)
  return isNaN(num) ? 0 : num
}

const getTemperatureColor = (temp) => {
  temp = safeNumber(temp)
  if (!temp) return 'text-muted-foreground'
  if (temp < 40) return 'text-blue-600'
  if (temp < 70) return 'text-green-600'
  if (temp < 85) return 'text-yellow-600'
  return 'text-red-600'
}

const getDeviceIcon = (type) => {
  switch (type) {
    case 'computer': return <Monitor className="h-8 w-8" />
    case 'laptop': return <Laptop className="h-8 w-8" />
    case 'smartphone': return <Smartphone className="h-8 w-8" />
    case 'printer': return <Printer className="h-8 w-8" />
    default: return <Monitor className="h-8 w-8" />
  }
}

const getRamType = (typeCode) => {
  const map = {
    20: 'DDR', 21: 'DDR2', 22: 'DDR2 FB-DIMM',
    24: 'DDR3', 25: 'FBD2', 26: 'DDR4', 27: 'DDR5',
  }
  return map[Number(typeCode)] || 'Desconhecido'
}

const ExpandableCard = ({ title, icon, children }) => {
  const [expanded, setExpanded] = useState(false)
  return (
    <Card>
      <CardHeader className="flex justify-between items-center">
        <CardTitle className="flex items-center gap-2">
          {icon} {title}
        </CardTitle>
        <Button size="sm" variant="outline" onClick={() => setExpanded(!expanded)}>
          {expanded ? 'Ocultar Detalhes' : 'Ver Detalhes'}
        </Button>
      </CardHeader>
      {expanded && <CardContent>{children}</CardContent>}
    </Card>
  )
}

const DeviceDetail = ({ deviceId, onBack }) => {
  const [device, setDevice] = useState(null)
  const [hardware, setHardware] = useState({})
  const [historyLogs, setHistoryLogs] = useState([])
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false)
  const [historyLoading, setHistoryLoading] = useState(true)
  const [historyError, setHistoryError] = useState(null)

  useEffect(() => {
    const fetchDeviceData = async () => {
      try {
        setHistoryLoading(true)
        setHistoryError(null)
        
        const response = await fetch(`${API_BASE}/devices/${deviceId}`)
        if (!response.ok) throw new Error('Erro ao buscar dados do dispositivo')
        
        const data = await response.json()
        const hw = data.hardware_details || {}  // Corrigido: hardware_details em vez de hardware

        // Força arrays e objetos válidos
        hw.cpu_info = hw.cpu_info || {}
        hw.ram_info = hw.ram_info || { modules: [] }
        hw.disk_info = Array.isArray(hw.disk_info) ? hw.disk_info : []
        hw.gpu_info = hw.gpu_info || {}
        hw.motherboard_info = hw.motherboard_info || {}
        hw.temperature_info = hw.temperature_info || {}
        hw.installed_software = Array.isArray(hw.installed_software) ? hw.installed_software : []
        hw.usb_devices = Array.isArray(hw.usb_devices) ? hw.usb_devices : []
        hw.network_info = Array.isArray(hw.network_info) ? hw.network_info : []

        setDevice(data)
        setHardware(hw)
        
        // Buscar histórico do dispositivo separadamente
        try {
          console.log('Buscando histórico para device:', deviceId)
          const historyResponse = await fetch(`${API_BASE}/history_logs/device/${deviceId}?limit=20`)
          console.log('Resposta do histórico:', historyResponse.status)
            
          if (historyResponse.ok) {
            const historyData = await historyResponse.json()
            console.log('Dados do histórico recebidos:', historyData)
            
            // Handle both formats: direct array or paginated response
            const logs = Array.isArray(historyData) 
              ? historyData 
              : (Array.isArray(historyData?.items) ? historyData.items : [])
            
            console.log('Logs processados:', logs.length, 'itens')
            setHistoryLogs(logs)
          } else {
            const errorText = await historyResponse.text()
            console.warn('Erro ao buscar histórico:', historyResponse.status, errorText)
            setHistoryError(`Erro ao carregar histórico: ${historyResponse.status} - ${historyResponse.statusText}`)
            setHistoryLogs([])
          }
        } catch (historyErr) {
          console.error('Não foi possível carregar histórico:', historyErr)
          setHistoryLogs([])
        }
        
      } catch (error) {
        console.error('Erro ao buscar dados do dispositivo:', error)
        setHistoryError('Erro ao carregar os dados. Tente novamente mais tarde.')
      } finally {
        setHistoryLoading(false)
      }
    }
    fetchDeviceData()
  }, [deviceId])

  if (!device) return <div className="flex items-center justify-center h-64 text-muted-foreground">Carregando dispositivo...</div>

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="outline" size="sm" onClick={onBack}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Voltar
        </Button>
        <div className="flex items-center gap-3">
          <div className="p-2 bg-primary/10 rounded-lg">{getDeviceIcon(device.device_type)}</div>
          <div>
            <h1 className="text-2xl font-bold">{device.name || 'N/A'}</h1>
            <p className="text-muted-foreground">{device.ip_address || 'N/A'}</p>
          </div>
        </div>
        <div className="ml-auto flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => setIsEditDialogOpen(true)}>
            <Edit className="h-4 w-4 mr-2" />
            Editar
          </Button>
          <Badge variant={device.status === 'online' ? 'default' : 'secondary'} className="text-sm">
            {device.status || 'Desconhecido'}
          </Badge>
        </div>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview">Resumo</TabsTrigger>
          <TabsTrigger value="hardware">Hardware</TabsTrigger>
          <TabsTrigger value="software">Software</TabsTrigger>
          <TabsTrigger value="network">Rede</TabsTrigger>
          <TabsTrigger value="history">Histórico</TabsTrigger>
        </TabsList>

        {/* Resumo */}
        <TabsContent value="overview" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Info className="h-5 w-5" /> Informações Básicas
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <p><strong>Nome:</strong> {device.name || 'N/A'}</p>
              <p><strong>IP:</strong> {device.ip_address || 'N/A'}</p>
              <p><strong>MAC:</strong> {device.mac_address || 'N/A'}</p>
              <p><strong>Tipo:</strong> {device.device_type || 'N/A'}</p>
              <p><strong>OS:</strong> {device.os || 'N/A'}</p>
              <p><strong>Última visualização:</strong> {formatDate(device.last_seen)}</p>
              <p><strong>Criado em:</strong> {formatDate(device.created_at)}</p>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Hardware */}
        <TabsContent value="hardware" className="space-y-4">
          {/* CPU */}
              <ExpandableCard title="Processador" icon={<Cpu className="h-5 w-5" />}>
                <p>Modelo: {hardware?.cpu_info?.model || 'N/A'}</p>
                <p>Cores: {hardware?.cpu_info?.cores ?? 'N/A'}</p>
                <p>Threads: {hardware?.cpu_info?.threads ?? 'N/A'}</p>
                {hardware?.cpu_info?.frequency_mhz != null && (
                  <p>Frequência: {hardware.cpu_info.frequency_mhz} MHz</p>
                )}
                {hardware?.cpu_info?.current_temp != null && (
                  <p className={getTemperatureColor(hardware.cpu_info.current_temp)}>
                    Temperatura: {safeNumber(hardware.cpu_info.current_temp)}°C
                  </p>
                )}
              </ExpandableCard>

          {/** RAM */}
          <ExpandableCard title="Memória RAM" icon={<MemoryStick className="h-5 w-5" />}>
            <p>Total: {safeNumber(hardware?.ram_info?.total_gb)} GB</p>
            <p>Usado: {safeNumber(hardware?.ram_info?.used_gb)} GB</p>
            <p>Slots: {hardware?.ram_info?.slots_used || 0} / {hardware?.ram_info?.slots_total || 0}</p>
            <Progress value={(safeNumber(hardware?.ram_info?.used_gb) / safeNumber(hardware?.ram_info?.total_gb)) * 100 || 0} className="h-2 my-2" />
            {hardware?.ram_info?.modules && hardware.ram_info.modules.map((m, i) => (
              <div key={i} className="border-t pt-2 mt-2 text-sm">
                <p>Módulo {i + 1}</p>
                <p>Capacidade: {safeNumber(m.capacity_gb)} GB</p>
                <p>Tipo: {m.type || 'N/A'}</p>
                <p>Velocidade: {m.speed_mhz ? `${m.speed_mhz} MHz` : 'N/A'}</p>
                <p>Fabricante: {m.manufacturer || 'N/A'}</p>
                {m.part_number && <p>Part Number: {m.part_number.trim()}</p>}
              </div>
            ))}
          </ExpandableCard>

          {/** Discos */}
          <ExpandableCard title="Armazenamento" icon={<HardDrive className="h-5 w-5 text-purple-600" />}>
            {hardware?.disk_info && hardware.disk_info.length > 0 ? hardware.disk_info.map((disk, index) => (
                <div key={index} className="p-3 border rounded-lg mb-2">
                  <p className="font-medium">{disk.name || 'N/A'}</p>
                  <p className="text-sm text-muted-foreground">Modelo: {disk.model || 'N/A'}</p>
                  <p className="text-sm text-muted-foreground">Tipo: {disk.type || 'N/A'}</p>
                  <p className="text-sm text-muted-foreground">Serial: {disk.serial_number || 'N/A'}</p>
                  <p className="text-sm">Capacidade Total: {safeNumber(disk.total_gb).toFixed(1)} GB</p>
                  
                  {Array.isArray(disk.partitions) && disk.partitions.length > 0 ? (
                    <div className="mt-2">
                      <p className="text-sm font-medium">Partições:</p>
                      {disk.partitions.map((p, i) => {
                        const usedSpace = safeNumber(p.total_gb) - safeNumber(p.free_gb)
                        const usagePercentage = safeNumber(p.total_gb) ? (usedSpace / safeNumber(p.total_gb)) * 100 : 0
                        return (
                          <div key={i} className="ml-4 mt-1 p-2 bg-gray-50 rounded">
                            <p className="text-sm font-medium">{p.drive_letter || 'N/A'} ({p.fstype || 'N/A'})</p>
                            <div className="flex justify-between text-xs mb-1">
                              <span>{usedSpace.toFixed(1)} GB usado</span>
                              <span>{safeNumber(p.total_gb).toFixed(1)} GB total</span>
                            </div>
                            <Progress value={usagePercentage} className="h-1" />
                            <p className="text-xs text-muted-foreground mt-1">
                              {safeNumber(p.free_gb).toFixed(1)} GB livres
                            </p>
                          </div>
                        )
                      })}
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground mt-2">Nenhuma partição detectada</p>
                  )}
                </div>
            )) : (
              <p className="text-muted-foreground text-center py-4">Nenhum disco detectado</p>
            )}
          </ExpandableCard>

          {/** GPU */}
          <ExpandableCard title="Placa de Vídeo" icon={<Monitor className="h-5 w-5 text-indigo-600" />}>
            <p>Modelo: {hardware?.gpu_info?.model || 'N/A'}</p>
            <p>Marca: {hardware?.gpu_info?.brand || 'N/A'}</p>
            <p>VRAM: {hardware?.gpu_info?.vram_mb ? `${(safeNumber(hardware.gpu_info.vram_mb)/1024).toFixed(1)} GB` : 'N/A'}</p>
            <p>Driver: {hardware?.gpu_info?.driver_version || 'N/A'}</p>
          </ExpandableCard>

          {/** Placa-mãe */}
          <ExpandableCard title="Placa-mãe" icon={<Cpu className="h-5 w-5 text-gray-600" />}>
            <p>Fabricante: {hardware?.motherboard_info?.manufacturer || 'N/A'}</p>
            <p>Modelo: {hardware?.motherboard_info?.model || 'N/A'}</p>
            <p>Serial: {hardware?.motherboard_info?.serial_number || 'N/A'}</p>
          </ExpandableCard>

          {/** Temperaturas */}
          <ExpandableCard title="Temperaturas" icon={<Thermometer className="h-5 w-5 text-red-600" />}>
            {hardware.temperature_info && (hardware.temperature_info.cpu_temp || hardware.temperature_info.disk_temps) ? (
              <div className="space-y-2">
                {/* CPU Temperature */}
                {hardware.temperature_info.cpu_temp && (
                  <p className={`${getTemperatureColor(hardware.temperature_info.cpu_temp)}`}>
                    CPU: {safeNumber(hardware.temperature_info.cpu_temp)}°C
                  </p>
                )}
                
                {/* Disk Temperatures */}
                {hardware.temperature_info.disk_temps && Object.keys(hardware.temperature_info.disk_temps).length > 0 && (
                  <div className="space-y-1">
                    <p className="text-sm font-medium text-muted-foreground">Discos:</p>
                    {Object.entries(hardware.temperature_info.disk_temps).map(([diskName, temp]) => (
                      <p key={diskName} className={`ml-2 ${getTemperatureColor(temp)}`}>
                        {diskName}: {safeNumber(temp)}°C
                      </p>
                    ))}
                  </div>
                )}
                
                {/* Mostrar notas personalizadas se existirem */}
                {hardware.temperature_info.custom_notes && hardware.temperature_info.custom_notes.length > 0 && (
                  <div className="mt-2">
                    {hardware.temperature_info.custom_notes.map((note, i) => (
                      <p key={i} className="text-sm text-yellow-600 bg-yellow-50 p-2 rounded">
                        ⚠️ {note}
                      </p>
                    ))}
                  </div>
                )}
                
                {/* Mostrar erro do LHM apenas se existir */}
                {hardware.temperature_info.lhm_error && (
                  <p className="text-xs text-muted-foreground mt-2">
                    Nota: LibreHardwareMonitor não disponível, usando WMI
                  </p>
                )}
              </div>
            ) : (
              <p className="text-muted-foreground">Nenhuma temperatura registrada</p>
            )}
          </ExpandableCard>
        </TabsContent>

        {/* Software */}
        <TabsContent value="software" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Package className="h-5 w-5" /> Software Instalado
              </CardTitle>
              <CardDescription>
                {hardware.installed_software ? `${hardware.installed_software.length} programas encontrados` : 'Nenhum software detectado'}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {hardware.installed_software && hardware.installed_software.length > 0 ? (
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {hardware.installed_software.map((software, index) => (
                    <div key={index} className="flex justify-between items-center p-3 border rounded-lg hover:bg-gray-50">
                      <div className="flex-1">
                        <p className="font-medium text-sm">{software.name || 'N/A'}</p>
                        <div className="flex gap-4 text-xs text-muted-foreground mt-1">
                          <span>Versão: {software.version || 'N/A'}</span>
                          <span>Editor: {software.publisher || 'N/A'}</span>
                          <span>Instalado: {software.install_date || 'N/A'}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-muted-foreground text-center py-8">
                  Nenhum software instalado foi detectado
                </p>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Network */}
        <TabsContent value="network" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Wifi className="h-5 w-5" /> Informações de Rede
              </CardTitle>
            </CardHeader>
            <CardContent>
              {hardware.network_info && hardware.network_info.length > 0 ? (
                <div className="space-y-3">
                  {hardware.network_info.map((adapter, index) => (
                    <div key={index} className="p-3 border rounded-lg">
                      <p className="font-medium">{adapter.name || 'N/A'}</p>
                      <div className="text-sm text-muted-foreground mt-1 space-y-1">
                        <p>Tipo: {adapter.type || 'N/A'}</p>
                        <p>MAC: {adapter.mac || 'N/A'}</p>
                        {adapter.ip_addresses && Array.isArray(adapter.ip_addresses) && (
                          <p>IPs: {adapter.ip_addresses.join(', ')}</p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-muted-foreground">Nenhuma interface de rede detectada</p>
              )}
            </CardContent>
          </Card>

          {/* USB Devices */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Usb className="h-5 w-5" /> Dispositivos USB
              </CardTitle>
            </CardHeader>
            <CardContent>
              {hardware.usb_devices && hardware.usb_devices.length > 0 ? (
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {hardware.usb_devices.map((device, index) => (
                    <div key={index} className="p-2 border rounded text-sm">
                      <p className="font-medium">{typeof device === 'string' ? device : device.name || 'N/A'}</p>
                      {typeof device === 'object' && device.status && (
                        <p className="text-xs text-muted-foreground">Status: {device.status}</p>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-muted-foreground">Nenhum dispositivo USB detectado</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* History */}
        <TabsContent value="history" className="space-y-4">
          {console.log('Renderizando aba histórico:', { deviceId, historyLogs: historyLogs?.length, historyLoading, historyError })}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <History className="h-5 w-5" /> Histórico de Alterações
              </CardTitle>
              <CardDescription>
                Visualize o histórico de alterações deste dispositivo
              </CardDescription>
            </CardHeader>
            <CardContent>
              {historyError ? (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    {historyError}
                  </AlertDescription>
                </Alert>
              ) : (
                <TimelineView 
                  deviceId={deviceId} 
                  initialLogs={historyLogs}
                  loading={historyLoading}
                />
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Modal de Edição */}
      <DeviceEditDialog
        open={isEditDialogOpen}
        onOpenChange={setIsEditDialogOpen}
        device={device}
        onSave={(updated) => setDevice({ ...device, ...updated })}
      />
    </div>
  )
}

export default DeviceDetail
