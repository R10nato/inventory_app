import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Button } from '@/components/ui/button.jsx'
import { Input } from '@/components/ui/input.jsx'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select.jsx'
import { Progress } from '@/components/ui/progress.jsx'
import { 
  Monitor, 
  Laptop, 
  Smartphone, 
  Printer, 
  Cpu, 
  MemoryStick, 
  HardDrive, 
  Wifi,
  Search,
  Filter,
  Eye,
  Clock,
  Activity
} from 'lucide-react'
import { useState } from 'react'

const DeviceGrid = ({ devices, onDeviceSelect }) => {
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [typeFilter, setTypeFilter] = useState('all')

  // Filtrar dispositivos
  const filteredDevices = devices.filter(device => {
    const matchesSearch = device.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         device.ip_address.includes(searchTerm) ||
                         (device.os && device.os.toLowerCase().includes(searchTerm.toLowerCase()))
    
    const matchesStatus = statusFilter === 'all' || device.status === statusFilter
    const matchesType = typeFilter === 'all' || device.device_type === typeFilter

    return matchesSearch && matchesStatus && matchesType
  })

  const getDeviceIcon = (type) => {
    switch (type) {
      case 'computer': return <Monitor className="h-6 w-6" />
      case 'laptop': return <Laptop className="h-6 w-6" />
      case 'smartphone': return <Smartphone className="h-6 w-6" />
      case 'printer': return <Printer className="h-6 w-6" />
      default: return <Monitor className="h-6 w-6" />
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'online': return 'default'
      case 'offline': return 'secondary'
      case 'warning': return 'destructive'
      default: return 'outline'
    }
  }

  const formatLastSeen = (dateString) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffMs = now - date
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return 'Agora'
    if (diffMins < 60) return `${diffMins}m atrás`
    if (diffHours < 24) return `${diffHours}h atrás`
    return `${diffDays}d atrás`
  }

  const getResourceUsage = (device) => {
    if (!device.hardware_details) return null

    const ramUsage = device.hardware_details.ram_info ? 
      (device.hardware_details.ram_info.used_gb / device.hardware_details.ram_info.total_gb) * 100 : 0
    
    const diskUsage = device.hardware_details.disk_info?.[0] ? 
      ((device.hardware_details.disk_info[0].total_gb - device.hardware_details.disk_info[0].free_gb) / device.hardware_details.disk_info[0].total_gb) * 100 : 0

    return { ramUsage, diskUsage }
  }

  return (
    <div className="space-y-6">
      {/* Filtros e Busca */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="h-5 w-5" />
            Filtros
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Buscar dispositivos..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger>
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todos os Status</SelectItem>
                <SelectItem value="online">Online</SelectItem>
                <SelectItem value="offline">Offline</SelectItem>
              </SelectContent>
            </Select>

            <Select value={typeFilter} onValueChange={setTypeFilter}>
              <SelectTrigger>
                <SelectValue placeholder="Tipo" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todos os Tipos</SelectItem>
                <SelectItem value="computer">Desktop</SelectItem>
                <SelectItem value="laptop">Laptop</SelectItem>
                <SelectItem value="smartphone">Smartphone</SelectItem>
                <SelectItem value="printer">Impressora</SelectItem>
              </SelectContent>
            </Select>

            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <span>{filteredDevices.length} de {devices.length} dispositivos</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Grid de Dispositivos */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {filteredDevices.map((device) => {
          const resourceUsage = getResourceUsage(device)
          
          return (
            <Card key={device.id} className="hover:shadow-lg transition-shadow cursor-pointer">
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-primary/10 rounded-lg">
                      {getDeviceIcon(device.device_type)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <CardTitle className="text-base truncate">{device.name}</CardTitle>
                      <CardDescription className="text-sm">{device.ip_address}</CardDescription>
                    </div>
                  </div>
                  <Badge variant={getStatusColor(device.status)} className="ml-2">
                    {device.status}
                  </Badge>
                </div>
              </CardHeader>
              
              <CardContent className="space-y-4">
                {/* Informações Básicas */}
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-sm">
                    <Activity className="h-4 w-4 text-muted-foreground" />
                    <span className="text-muted-foreground">OS:</span>
                    <span className="truncate">{device.os || 'N/A'}</span>
                  </div>
                  
                  <div className="flex items-center gap-2 text-sm">
                    <Clock className="h-4 w-4 text-muted-foreground" />
                    <span className="text-muted-foreground">Visto:</span>
                    <span>{formatLastSeen(device.last_seen)}</span>
                  </div>
                </div>

                {/* Hardware Preview */}
                {device.hardware_details && (
                  <div className="space-y-3 pt-2 border-t">
                    <h4 className="text-sm font-medium">Hardware</h4>
                    
                    {/* CPU */}
                    {device.hardware_details.cpu_info && (
                      <div className="flex items-center gap-2 text-sm">
                        <Cpu className="h-4 w-4 text-blue-600" />
                        <span className="truncate">
                          {device.hardware_details.cpu_info.model || 'CPU N/A'}
                        </span>
                      </div>
                    )}

                    {/* RAM */}
                    {device.hardware_details.ram_info && (
                      <div className="space-y-1">
                        <div className="flex items-center gap-2 text-sm">
                          <MemoryStick className="h-4 w-4 text-green-600" />
                          <span>
                            {device.hardware_details.ram_info.used_gb}GB / {device.hardware_details.ram_info.total_gb}GB
                          </span>
                        </div>
                        {resourceUsage && (
                          <Progress 
                            value={resourceUsage.ramUsage} 
                            className="h-2"
                          />
                        )}
                      </div>
                    )}

                    {/* Disco */}
                    {device.hardware_details.disk_info?.[0] && (
                      <div className="space-y-1">
                        <div className="flex items-center gap-2 text-sm">
                          <HardDrive className="h-4 w-4 text-purple-600" />
                          <span>
                            {device.hardware_details.disk_info[0].free_gb}GB livre / {device.hardware_details.disk_info[0].total_gb}GB
                          </span>
                        </div>
                        {resourceUsage && (
                          <Progress 
                            value={resourceUsage.diskUsage} 
                            className="h-2"
                          />
                        )}
                      </div>
                    )}

                    {/* Rede */}
                    {device.hardware_details.network_info?.[0] && (
                      <div className="flex items-center gap-2 text-sm">
                        <Wifi className="h-4 w-4 text-orange-600" />
                        <span className="truncate">
                          {device.hardware_details.network_info[0].name || 'Rede N/A'}
                        </span>
                      </div>
                    )}
                  </div>
                )}

                {/* Botão de Detalhes */}
                <Button 
                  variant="outline" 
                  size="sm" 
                  className="w-full"
                  onClick={() => onDeviceSelect(device)}
                >
                  <Eye className="h-4 w-4 mr-2" />
                  Ver Detalhes
                </Button>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* Mensagem quando não há dispositivos */}
      {filteredDevices.length === 0 && (
        <Card>
          <CardContent className="text-center py-12">
            <Monitor className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-medium mb-2">Nenhum dispositivo encontrado</h3>
            <p className="text-muted-foreground">
              {searchTerm || statusFilter !== 'all' || typeFilter !== 'all' 
                ? 'Tente ajustar os filtros de busca'
                : 'Nenhum dispositivo foi detectado ainda'
              }
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

export default DeviceGrid

