import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs.jsx'
import DeviceEditDialog from './DeviceEditDialog.jsx'
import { 
  ArrowLeft, Monitor, Laptop, Smartphone, Printer,
  Cpu, MemoryStick, HardDrive, Wifi, Clock, Thermometer,
  Package, History, Edit, Info, Usb, User, Activity
} from 'lucide-react'
import { Progress } from '@/components/ui/progress.jsx'

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

  useEffect(() => {
    const fetchDevice = async () => {
      try {
        const response = await fetch(`${API_BASE}/devices/${deviceId}/full`)
        if (!response.ok) throw new Error('Erro ao carregar dispositivo')
        let data = await response.json()

        console.log("📡 Dados recebidos do backend:", data)   // 👈 Adicione isto

        // Normaliza hardware_details
        let hw = data.hardware_details || {}
        if (typeof hw === 'string') {
          try { hw = JSON.parse(hw) } catch { hw = {} }
        }

        console.log("🖥️ Hardware normalizado:", hw)   // 👈 E isto

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
        setHistoryLogs(Array.isArray(data.history_logs) ? data.history_logs : [])
      } catch (error) {
        console.error('Erro ao buscar dados do dispositivo:', error)
      }
    }
    fetchDevice()
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
            <p>Total: {safeNumber(hardware.ram_info.total_gb)} GB</p>
            <p>Usado: {safeNumber(hardware.ram_info.used_gb)} GB</p>
            <Progress value={(safeNumber(hardware.ram_info.used_gb) / safeNumber(hardware.ram_info.total_gb)) * 100 || 0} className="h-2 my-2" />
            {hardware.ram_info.modules.map((m, i) => (
              <div key={i} className="border-t pt-2 mt-2 text-sm">
                <p>Banco: {m.bank_label || 'N/A'}</p>
                <p>Capacidade: {safeNumber(m.capacity_gb)} GB</p>
                <p>Tipo: {getRamType(m.typeCode)}</p>
              </div>
            ))}
          </ExpandableCard>

          {/** Discos */}
          <ExpandableCard title="Armazenamento" icon={<HardDrive className="h-5 w-5 text-purple-600" />}>
            {hardware.disk_info.map((disk, index) => {
              const usedSpace = safeNumber(disk.total_gb) - safeNumber(disk.free_gb)
              const usagePercentage = safeNumber(disk.total_gb) ? (usedSpace / safeNumber(disk.total_gb)) * 100 : 0
              return (
                <div key={index} className="p-3 border rounded-lg mb-2">
                  <p className="font-medium">{disk.name || 'N/D'} ({disk.type || 'N/D'})</p>
                  <div className="flex justify-between text-sm mb-1">
                    <span>{usedSpace.toFixed(1)} GB usado</span>
                    <span>{safeNumber(disk.total_gb)} GB total</span>
                  </div>
                  <Progress value={usagePercentage} className="h-2" />
                  {Array.isArray(disk.partitions) && disk.partitions.map((p, i) => (
                    <p key={i} className="text-sm text-muted-foreground">
                      {p.drive_letter || 'N/A'} - {p.fstype || 'N/A'} - {safeNumber(p.free_gb)} GB livre
                    </p>
                  ))}
                </div>
              )
            })}
          </ExpandableCard>

          {/** GPU */}
          <ExpandableCard title="Placa de Vídeo" icon={<Monitor className="h-5 w-5 text-indigo-600" />}>
            <p>Modelo: {hardware.gpu_info.model || 'N/A'}</p>
            <p>Marca: {hardware.gpu_info.brand || 'N/A'}</p>
            <p>VRAM: {hardware.gpu_info.vram_mb ? `${(safeNumber(hardware.gpu_info.vram_mb)/1024).toFixed(1)} GB` : 'N/A'}</p>
            <p>Driver: {hardware.gpu_info.driver_version || 'N/A'}</p>
          </ExpandableCard>

          {/** Placa-mãe */}
          <ExpandableCard title="Placa-mãe" icon={<Cpu className="h-5 w-5 text-gray-600" />}>
            <p>Fabricante: {hardware.motherboard_info.manufacturer || 'N/A'}</p>
            <p>Modelo: {hardware.motherboard_info.model || 'N/A'}</p>
            <p>Serial: {hardware.motherboard_info.serial_number || 'N/A'}</p>
          </ExpandableCard>

          {/** Temperaturas */}
          <ExpandableCard title="Temperaturas" icon={<Thermometer className="h-5 w-5 text-red-600" />}>
            {Object.keys(hardware.temperature_info).length > 0 ? (
              Object.entries(hardware.temperature_info).map(([component, temp]) => (
                <p key={component} className={`capitalize ${getTemperatureColor(temp)}`}>
                  {component}: {safeNumber(temp)}°C
                </p>
              ))
            ) : (
              <p className="text-muted-foreground">Nenhuma temperatura registrada</p>
            )}
          </ExpandableCard>
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
