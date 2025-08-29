import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs.jsx'
import { Separator } from '@/components/ui/separator.jsx'
import DeviceEditDialog from './DeviceEditDialog.jsx'

import { 
  ArrowLeft, 
  Monitor, 
  Laptop, 
  Smartphone, 
  Printer,
  Cpu,
  MemoryStick,
  HardDrive,
  Wifi,
  Clock,
  Thermometer,
  Package,
  Network,
  History,
  Edit,
  Info,
  Activity,
  User,
  Usb
} from 'lucide-react'

// Defina a base da API aqui
const API_BASE = "http://localhost:8000"

// Funções utilitárias
const formatDate = (dateString) => {
  return new Date(dateString).toLocaleString('pt-BR')
}
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

const DeviceDetail = ({ deviceId, onBack }) => {
  const [device, setDevice] = useState(null)
  const [historyLogs, setHistoryLogs] = useState([])
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)

  // Carregar device + histórico do backend
  useEffect(() => {
    const fetchDevice = async () => {
      try {
        setLoading(true)
        setError(null)

        console.log("🔎 Buscando:", `${API_BASE}/devices/${deviceId}/full`)

        const response = await fetch(`${API_BASE}/devices/${deviceId}/full`)
        if (!response.ok) throw new Error(`Erro ao carregar dispositivo: ${response.status}`)

        const data = await response.json()
        setDevice(data)
        setHistoryLogs(data.history_logs || [])
      } catch (err) {
        console.error("Erro ao buscar dados do dispositivo:", err)
        setError("Não foi possível carregar os detalhes do dispositivo.")
      } finally {
        setLoading(false)
      }
    }
    if (deviceId) fetchDevice()
  }, [deviceId])

  const handleSaveDevice = async (updatedDevice) => {
    try {
      console.log('Dispositivo atualizado:', updatedDevice)
      Object.assign(device, updatedDevice)
      alert('Dispositivo atualizado com sucesso!')
    } catch (error) {
      console.error('Erro ao processar atualização do dispositivo:', error)
      throw error
    }
  }

  // Estado de carregamento
  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Activity className="h-6 w-6 animate-spin mr-2" />
        <p className="text-muted-foreground">Carregando dispositivo...</p>
      </div>
    )
  }

  // Estado de erro
  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-64 space-y-4">
        <p className="text-red-600">{error}</p>
        <Button onClick={onBack}>Voltar</Button>
      </div>
    )
  }

  if (!device) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-muted-foreground">Dispositivo não encontrado.</p>
      </div>
    )
  }

  const hardware = device.hardware_details || {}

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="outline" size="sm" onClick={onBack}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Voltar
        </Button>
        <div className="flex items-center gap-3">
          <div className="p-2 bg-primary/10 rounded-lg">
            {getDeviceIcon(device.device_type)}
          </div>
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
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {/* Informações Básicas */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Info className="h-5 w-5" />
                  Informações Básicas
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div>
                  <span className="text-sm text-muted-foreground">Nome:</span>
                  <p className="font-medium">{device.name}</p>
                </div>
                <div>
                  <span className="text-sm text-muted-foreground">IP:</span>
                  <p className="font-medium">{device.ip_address}</p>
                </div>
                <div>
                  <span className="text-sm text-muted-foreground">MAC:</span>
                  <p className="font-medium">{device.mac_address || 'N/A'}</p>
                </div>
                <div>
                  <span className="text-sm text-muted-foreground">Tipo:</span>
                  <p className="font-medium capitalize">{device.device_type}</p>
                </div>
                <div>
                  <span className="text-sm text-muted-foreground">OS:</span>
                  <p className="font-medium">{device.os || 'N/A'}</p>
                </div>
                <div>
                  <span className="text-sm text-muted-foreground">Última visualização:</span>
                  <p className="font-medium">{formatDate(device.last_seen)}</p>
                </div>
                <div>
                  <span className="text-sm text-muted-foreground">Criado em:</span>
                  <p className="font-medium">{formatDate(device.created_at)}</p>
                </div>
              </CardContent>
            </Card>

            {/* CPU */}
            {hardware.cpu_info && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Cpu className="h-5 w-5 text-blue-600" />
                    Processador
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div>
                    <span className="text-sm text-muted-foreground">Modelo:</span>
                    <p className="font-medium">{hardware.cpu_info.model || 'N/A'}</p>
                  </div>
                  <div>
                    <span className="text-sm text-muted-foreground">Marca:</span>
                    <p className="font-medium">{hardware.cpu_info.brand || 'N/A'}</p>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <span className="text-sm text-muted-foreground">Cores:</span>
                      <p className="font-medium">{hardware.cpu_info.cores || 'N/A'}</p>
                    </div>
                    <div>
                      <span className="text-sm text-muted-foreground">Threads:</span>
                      <p className="font-medium">{hardware.cpu_info.threads || 'N/A'}</p>
                    </div>
                  </div>
                  <div>
                    <span className="text-sm text-muted-foreground">Frequência:</span>
                    <p className="font-medium">
                      {hardware.cpu_info.frequency_mhz ? `${hardware.cpu_info.frequency_mhz} MHz` : 'N/A'}
                    </p>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* RAM */}
            {hardware.ram_info && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <MemoryStick className="h-5 w-5 text-green-600" />
                    Memória RAM
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div>
                    <span className="text-sm text-muted-foreground">Total:</span>
                    <p className="font-medium">{hardware.ram_info.total_gb ?? "N/A"} GB</p>
                  </div>
                  <div>
                    <span className="text-sm text-muted-foreground">Em uso:</span>
                    <p className="font-medium">{hardware.ram_info.used_gb ?? "N/A"} GB</p>
                  </div>
                  <div>
                    <span className="text-sm text-muted-foreground">Uso:</span>
                    <div className="space-y-1">
                      <div className="flex justify-between text-sm">
                        <span>
                          {hardware.ram_info.used_gb && hardware.ram_info.total_gb? `${((hardware.ram_info.used_gb / hardware.ram_info.total_gb) * 100).toFixed(1)}%`: "N/A"}
                        </span>
                      </div>
                      <Progress
                        value={hardware.ram_info.used_gb && hardware.ram_info.total_gb? (hardware.ram_info.used_gb / hardware.ram_info.total_gb) * 100: 0}
                        className="h-2"
                      />
                    </div>
                  </div>

                  {/* Slots */}
                  {hardware.ram_info.slots_total && (
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <span className="text-sm text-muted-foreground">Slots usados:</span>
                        <p className="font-medium">{hardware.ram_info.slots_used ?? 0}</p>
                      </div>
                      <div>
                        <span className="text-sm text-muted-foreground">Slots total:</span>
                        <p className="font-medium">{hardware.ram_info.slots_total}</p>
                      </div>
                    </div>
                  )}

                  {/* Tipo da RAM */}
                  {hardware.ram_info.modules && hardware.ram_info.modules.length > 0 && (
                    <div>
                      <span className="text-sm text-muted-foreground">Tipo:</span>
                      <p className="font-medium">
                        {
                          {
                            20: "DDR",
                            21: "DDR2",
                            22: "DDR2 FB-DIMM",
                            24: "DDR3",
                            25: "FBD2",
                            26: "DDR4",
                            27: "DDR5",
                          }[hardware.ram_info.modules[0].type] ?? "Desconhecido"}
                      </p>
                    </div>
                  )}
                </CardContent>
              </Card>
            )}

          </div>

          {/* Temperaturas */}
          {hardware.temperature_info && Object.keys(hardware.temperature_info).length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Thermometer className="h-5 w-5 text-red-600" />
                  Temperaturas
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {Object.entries(hardware.temperature_info).map(([component, temp]) => (
                    <div key={component} className="text-center p-3 border rounded-lg">
                      <p className="text-sm text-muted-foreground capitalize">{component}</p>
                      <p className={`text-2xl font-bold ${getTemperatureColor(temp)}`}>
                        {temp}°C
                      </p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Aba Hardware */}
        <TabsContent value="hardware" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Discos */}
            {hardware.disk_info && hardware.disk_info.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <HardDrive className="h-5 w-5 text-purple-600" />
                    Armazenamento
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
                          <Progress 
                            value={usagePercentage}
                            className="h-2"
                          />
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
                    <Monitor className="h-5 w-5 text-indigo-600" />
                    Placa de Vídeo
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div>
                    <span className="text-sm text-muted-foreground">Modelo:</span>
                    <p className="font-medium">{hardware.gpu_info.model || 'N/A'}</p>
                  </div>
                  <div>
                    <span className="text-sm text-muted-foreground">Marca:</span>
                    <p className="font-medium">{hardware.gpu_info.brand || 'N/A'}</p>
                  </div>
                  <div>
                    <span className="text-sm text-muted-foreground">VRAM:</span>
                    <p className="font-medium">
                      {hardware.gpu_info.vram_mb ? `${(hardware.gpu_info.vram_mb / 1024).toFixed(1)} GB` : 'N/A'}
                    </p>
                  </div>
                  <div>
                    <span className="text-sm text-muted-foreground">Driver:</span>
                    <p className="font-medium">{hardware.gpu_info.driver_version || 'N/A'}</p>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Placa-mãe */}
            {hardware.motherboard_info && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Cpu className="h-5 w-5 text-gray-600" />
                    Placa-mãe
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div>
                    <span className="text-sm text-muted-foreground">Fabricante:</span>
                    <p className="font-medium">{hardware.motherboard_info.manufacturer || 'N/A'}</p>
                  </div>
                  <div>
                    <span className="text-sm text-muted-foreground">Modelo:</span>
                    <p className="font-medium">{hardware.motherboard_info.model || 'N/A'}</p>
                  </div>
                  <div>
                    <span className="text-sm text-muted-foreground">Serial:</span>
                    <p className="font-medium">{hardware.motherboard_info.serial_number || 'N/A'}</p>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Módulos de RAM */}
            {hardware.ram_info?.modules && hardware.ram_info.modules.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <MemoryStick className="h-5 w-5 text-green-600" />
                    Módulos de RAM
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {hardware.ram_info.modules.map((module, index) => (
                    <div key={index} className="p-3 border rounded-lg">
                      <div className="grid grid-cols-2 gap-2 text-sm">
                        <div>
                          <span className="text-muted-foreground">Capacidade:</span>
                          <p className="font-medium">{module.capacity_gb} GB</p>
                        </div>
                        <div>
                          <span className="text-muted-foreground">Tipo:</span>
                          <p className="font-medium">{module.type || 'N/A'}</p>
                        </div>
                        <div>
                          <span className="text-muted-foreground">Velocidade:</span>
                          <p className="font-medium">{module.speed_mhz ? `${module.speed_mhz} MHz` : 'N/A'}</p>
                        </div>
                        <div>
                          <span className="text-muted-foreground">Fabricante:</span>
                          <p className="font-medium">{module.manufacturer || 'N/A'}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>

        {/* Aba Software */}
        <TabsContent value="software" className="space-y-4">
          {/* Lista de Software Instalado */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Package className="h-5 w-5 text-blue-600" />
                Software Instalado
              </CardTitle>
              <CardDescription>
                Programas e aplicações detectados no sistema
              </CardDescription>
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

          {/* Dispositivos USB */}
          {hardware.usb_devices && hardware.usb_devices.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Usb className="h-5 w-5 text-orange-600" />
                  Dispositivos USB
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {hardware.usb_devices.map((device, index) => (
                    <div key={index} className="p-3 border rounded-lg">
                      <p className="font-medium">
                        {typeof device === 'string' ? device : device.name || 'Dispositivo USB'}
                      </p>
                      {typeof device === 'object' && device.status && (
                        <p className="text-sm text-muted-foreground">Status: {device.status}</p>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Aba Rede */}
        <TabsContent value="network" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Wifi className="h-5 w-5 text-orange-600" />
                Interfaces de Rede
              </CardTitle>
            </CardHeader>
            <CardContent>
              {hardware.network_info && hardware.network_info.length > 0 ? (
                <div className="space-y-4">
                  {hardware.network_info.map((network, index) => (
                    <div key={index} className="p-4 border rounded-lg">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <span className="text-sm text-muted-foreground">Nome:</span>
                          <p className="font-medium">{network.name || 'N/A'}</p>
                        </div>
                        <div>
                          <span className="text-sm text-muted-foreground">Tipo:</span>
                          <p className="font-medium">{network.type || 'N/A'}</p>
                        </div>
                        <div>
                          <span className="text-sm text-muted-foreground">MAC:</span>
                          <p className="font-medium">{network.mac || 'N/A'}</p>
                        </div>
                        <div>
                          <span className="text-sm text-muted-foreground">IPs:</span>
                          <p className="font-medium">
                            {Array.isArray(network.ip_addresses) 
                              ? network.ip_addresses.join(', ') 
                              : network.ip_addresses || 'N/A'}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <Wifi className="h-12 w-12 text-muted-foreground mx-auto mb-2" />
                  <p className="text-muted-foreground">Nenhuma interface de rede detectada</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Aba Histórico */}
        <TabsContent value="history" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <History className="h-5 w-5 text-gray-600" />
                Histórico de Mudanças
              </CardTitle>
              <CardDescription>
                Registro de alterações de hardware e software
              </CardDescription>
            </CardHeader>
            <CardContent>
              {historyLogs && historyLogs.length > 0 ? (
                <div className="space-y-4">
                  {historyLogs.map((log, index) => (
                    <div key={index} className="flex gap-4 p-4 border rounded-lg">
                      <div className="flex-shrink-0">
                        <div className="w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center">
                          <Activity className="h-4 w-4 text-primary" />
                        </div>
                      </div>
                      <div className="flex-1 space-y-2">
                        <div className="flex items-center justify-between">
                          <h4 className="font-medium">{log.component}</h4>
                          <div className="flex items-center gap-2 text-sm text-muted-foreground">
                            <Clock className="h-4 w-4" />
                            {formatDate(log.timestamp)}
                          </div>
                        </div>
                        <p className="text-sm">{log.change_description}</p>
                        {(log.details_before || log.details_after) && (
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                            {log.details_before && (
                              <div>
                                <span className="text-muted-foreground">Antes:</span>
                                <p className="font-mono bg-muted p-2 rounded text-xs">
                                  {log.details_before}
                                </p>
                              </div>
                            )}
                            {log.details_after && (
                              <div>
                                <span className="text-muted-foreground">Depois:</span>
                                <p className="font-mono bg-muted p-2 rounded text-xs">
                                  {log.details_after}
                                </p>
                              </div>
                            )}
                          </div>
                        )}
                        {log.user && (
                          <div className="flex items-center gap-2 text-sm text-muted-foreground">
                            <User className="h-4 w-4" />
                            {log.user}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <History className="h-12 w-12 text-muted-foreground mx-auto mb-2" />
                  <p className="text-muted-foreground">Nenhuma mudança registrada</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Dialog de Edição */}
      <DeviceEditDialog
        device={device}
        open={isEditDialogOpen}
        onOpenChange={setIsEditDialogOpen}
        onSave={handleSaveDevice}
      />
    </div>
  )
}

export default DeviceDetail


