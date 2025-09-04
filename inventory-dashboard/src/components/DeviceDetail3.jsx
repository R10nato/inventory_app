import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs.jsx'
import DeviceEditDialog from './DeviceEditDialog.jsx'
import { 
  ArrowLeft, Monitor, Laptop, Smartphone, Printer,
  Cpu, MemoryStick, HardDrive, Wifi, Clock, Thermometer,
  Package, History, Edit, Info, Activity, User, Usb
} from 'lucide-react'
import { Progress } from '@/components/ui/progress.jsx' // Certifique-se que Progress está importado

const API_BASE = "http://localhost:8000"

const formatDate = (dateString) => new Date(dateString).toLocaleString('pt-BR')

const getTemperatureColor = (temp) => {
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
        const data = await response.json()

        setDevice(data)

        let hw = data.hardware_details || {}
        if (typeof hw === 'string') {
          try { hw = JSON.parse(hw) } 
          catch (err) { console.error('Erro ao parsear hardware_details:', err); hw = {} }
        }
        setHardware(hw)
        setHistoryLogs(data.history_logs || [])
      } catch (error) {
        console.error('Erro ao buscar dados do dispositivo:', error)
      }
    }

    fetchDevice()
  }, [deviceId])

  if (!device) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-muted-foreground">Carregando dispositivo...</p>
      </div>
    )
  }

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
            <h1 className="text-2xl font-bold">{device.name}</h1>
            <p className="text-muted-foreground">{device.ip_address}</p>
          </div>
        </div>
        <div className="ml-auto flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => setIsEditDialogOpen(true)}>
            <Edit className="h-4 w-4 mr-2" />
            Editar
          </Button>
          <Badge variant={device.status === 'online' ? 'default' : 'secondary'} className="text-sm">
            {device.status}
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

        {/* Aba Resumo */}
        <TabsContent value="overview" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Info className="h-5 w-5" /> Informações Básicas
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <p><strong>Nome:</strong> {device.name}</p>
              <p><strong>IP:</strong> {device.ip_address}</p>
              <p><strong>MAC:</strong> {device.mac_address}</p>
              <p><strong>Tipo:</strong> {device.device_type}</p>
              <p><strong>OS:</strong> {device.os}</p>
              <p><strong>Última visualização:</strong> {formatDate(device.last_seen)}</p>
              <p><strong>Criado em:</strong> {formatDate(device.created_at)}</p>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Aba Hardware */}
        <TabsContent value="hardware" className="space-y-4">
          {/* CPU */}
          {hardware.cpu_info && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Cpu className="h-5 w-5" /> Processador
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p>{hardware.cpu_info.model}</p>
                <p>Cores: {hardware.cpu_info.cores}</p>
                <p>Threads: {hardware.cpu_info.threads}</p>
                {hardware.cpu_info.current_temp && (
                  <p className={getTemperatureColor(hardware.cpu_info.current_temp)}>
                    Temperatura: {hardware.cpu_info.current_temp}°C
                  </p>
                )}
              </CardContent>
            </Card>
          )}

          {/* RAM */}
          {hardware.ram_info && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <MemoryStick className="h-5 w-5" /> Memória RAM
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p>Total: {hardware.ram_info.total_gb} GB</p>
                <p>Usado: {hardware.ram_info.used_gb} GB</p>
                <Progress value={(hardware.ram_info.used_gb / hardware.ram_info.total_gb) * 100} className="h-2 my-2" />
                {hardware.ram_info.modules?.map((m, i) => (
                  <div key={i} className="border-t pt-2 mt-2 text-sm">
                    <p>Banco: {m.bank_label}</p>
                    <p>Capacidade: {m.capacity_gb} GB</p>
                    <p>Tipo: {getRamType(m.type)}</p>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          {/* Temperaturas */}
          {hardware.temperature_info && Object.keys(hardware.temperature_info).length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Thermometer className="h-5 w-5 text-red-600" /> Temperaturas
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {Object.entries(hardware.temperature_info).map(([component, temp]) => (
                    <div key={component} className="text-center p-3 border rounded-lg">
                      <p className="text-sm text-muted-foreground capitalize">{component}</p>
                      <p className={`text-2xl font-bold ${getTemperatureColor(Number(temp))}`}>
                        {Number(temp) || "N/A"}°C
                      </p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Discos */}
          {hardware.disk_info && hardware.disk_info.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <HardDrive className="h-5 w-5 text-purple-600" /> Armazenamento
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {hardware.disk_info.map((disk, index) => {
                  const usedSpace = disk.total_gb - disk.free_gb
                  const usagePercentage = (usedSpace / disk.total_gb) * 100
                  return (
                    <div key={index} className="p-3 border rounded-lg space-y-2">
                      <div className="flex justify-between items-start">
                        <div>
                          <p className="font-medium">{disk.name}</p>
                          <p className="text-sm text-muted-foreground">{disk.type}</p>
                        </div>
                        <Badge variant="outline">{disk.type}</Badge>
                      </div>
                      <div className="space-y-1">
                        <div className="flex justify-between text-sm">
                          <span>{usedSpace.toFixed(1)} GB usado</span>
                          <span>{disk.total_gb} GB total</span>
                        </div>
                        <Progress value={usagePercentage} className="h-2" />
                      </div>
                      {disk.partitions && disk.partitions.length > 0 && (
                        <div className="space-y-1">
                          <p className="text-sm font-medium">Partições:</p>
                          {disk.partitions.map((partition, pIndex) => (
                            <div key={pIndex} className="text-sm text-muted-foreground">
                              {partition.drive_letter} - {partition.fstype} - {partition.free_gb}GB livre
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )
                })}
              </CardContent>
            </Card>
          )}

          {/* GPU */}
          {hardware.gpu_info && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Monitor className="h-5 w-5 text-indigo-600" /> Placa de Vídeo
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <p>Modelo: {hardware.gpu_info.model || 'N/A'}</p>
                <p>Marca: {hardware.gpu_info.brand || 'N/A'}</p>
                <p>VRAM: {hardware.gpu_info.vram_mb ? `${(hardware.gpu_info.vram_mb / 1024).toFixed(1)} GB` : 'N/A'}</p>
                <p>Driver: {hardware.gpu_info.driver_version || 'N/A'}</p>
              </CardContent>
            </Card>
          )}

          {/* Placa-mãe */}
          {hardware.motherboard_info && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Cpu className="h-5 w-5 text-gray-600" /> Placa-mãe
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <p>Fabricante: {hardware.motherboard_info.manufacturer || 'N/A'}</p>
                <p>Modelo: {hardware.motherboard_info.model || 'N/A'}</p>
                <p>Serial: {hardware.motherboard_info.serial_number || 'N/A'}</p>
              </CardContent>
            </Card>
          )}

        </TabsContent>

        {/* Aba Software */}
        <TabsContent value="software" className="space-y-4">
          {/* Software Instalado */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Package className="h-5 w-5 text-blue-600" /> Software Instalado
              </CardTitle>
              <CardDescription>Programas e aplicações detectados no sistema</CardDescription>
            </CardHeader>
            <CardContent>
              {hardware.installed_software && hardware.installed_software.length > 0 ? (
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {hardware.installed_software.map((software, index) => (
                    <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                      <div className="flex-1 min-w-0">
                        <p className="font-medium truncate">{software.name}</p>
                        <div className="flex gap-4 text-sm text-muted-foreground">
                          <span>v{software.version || 'N/A'}</span>
                          <span>{software.publisher || 'N/A'}</span>
                          <span>{software.install_date || 'N/A'}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <Package className="h-12 w-12 text-muted-foreground mx-auto mb-2" />
                  <p className="text-muted-foreground">Nenhum software detectado</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* USB Devices */}
          {hardware.usb_devices && hardware.usb_devices.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Usb className="h-5 w-5 text-green-600" /> Dispositivos USB
                </CardTitle>
              </CardHeader>
              <CardContent>
                {hardware.usb_devices.map((usb, index) => (
                  <div key={index} className="border-b py-2 flex justify-between">
                    <span>{usb.name}</span>
                    <span className="text-sm text-muted-foreground">{usb.type}</span>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Aba Rede */}
        <TabsContent value="network" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Wifi className="h-5 w-5 text-cyan-600" /> Rede
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p>IP: {device.ip_address}</p>
              <p>MAC: {device.mac_address}</p>
              {hardware.network_info && (
                <div className="space-y-2">
                  {hardware.network_info.map((net, index) => (
                    <div key={index} className="p-2 border rounded-lg">
                      <p>Interface: {net.interface}</p>
                      <p>IPv4: {net.ipv4 || 'N/A'}</p>
                      <p>IPv6: {net.ipv6 || 'N/A'}</p>
                      <p>Gateway: {net.gateway || 'N/A'}</p>
                      <p>DNS: {net.dns?.join(', ') || 'N/A'}</p>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Aba Histórico */}
        <TabsContent value="history" className="space-y-4">
          {historyLogs.length > 0 ? (
            historyLogs.map((log, index) => (
              <Card key={index}>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <History className="h-5 w-5" /> {log.action || 'Alteração'}
                  </CardTitle>
                  <CardDescription>{formatDate(log.timestamp)}</CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-sm">{log.details || 'Sem detalhes'}</p>
                </CardContent>
              </Card>
            ))
          ) : (
            <div className="text-center py-8 text-muted-foreground">Nenhum histórico registrado</div>
          )}
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
