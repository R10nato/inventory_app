import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Button } from '@/components/ui/button.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Progress } from '@/components/ui/progress.jsx'
import { 
  Monitor, 
  Laptop, 
  Smartphone, 
  Printer, 
  Activity, 
  AlertTriangle, 
  CheckCircle, 
  Clock,
  TrendingUp,
  HardDrive,
  Cpu,
  MemoryStick
} from 'lucide-react'
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts'

const DashboardOverview = ({ devices, onViewDevices }) => {
  // Calcular estatísticas
  const totalDevices = devices.length
  const onlineDevices = devices.filter(d => d.status === 'online').length
  const offlineDevices = totalDevices - onlineDevices
  
  // Distribuição por tipo de dispositivo
  const deviceTypes = devices.reduce((acc, device) => {
    const type = device.device_type || 'unknown'
    acc[type] = (acc[type] || 0) + 1
    return acc
  }, {})

  const deviceTypeData = Object.entries(deviceTypes).map(([type, count]) => ({
    name: type === 'computer' ? 'Desktop' : 
          type === 'laptop' ? 'Laptop' : 
          type === 'smartphone' ? 'Smartphone' : 
          type === 'printer' ? 'Impressora' : 'Outros',
    value: count,
    color: type === 'computer' ? '#2563eb' : 
           type === 'laptop' ? '#10b981' : 
           type === 'smartphone' ? '#f59e0b' : 
           type === 'printer' ? '#8b5cf6' : '#6b7280'
  }))

  // Dados de uso de recursos (exemplo com dispositivos online)
  const resourceData = devices
    .filter(d => d.status === 'online' && d.hardware_details)
    .map(device => ({
      name: device.name.substring(0, 10) + '...',
      ram: device.hardware_details.ram_info ? 
        Math.round((device.hardware_details.ram_info.used_gb / device.hardware_details.ram_info.total_gb) * 100) : 0,
      disk: device.hardware_details.disk_info && device.hardware_details.disk_info[0] ? 
        Math.round(((device.hardware_details.disk_info[0].total_gb - device.hardware_details.disk_info[0].free_gb) / device.hardware_details.disk_info[0].total_gb) * 100) : 0
    }))

  // Alertas e problemas
  const alerts = devices.filter(d => {
    if (d.status === 'offline') return true
    if (d.hardware_details?.ram_info) {
      const ramUsage = (d.hardware_details.ram_info.used_gb / d.hardware_details.ram_info.total_gb) * 100
      if (ramUsage > 90) return true
    }
    if (d.hardware_details?.disk_info?.[0]) {
      const diskUsage = ((d.hardware_details.disk_info[0].total_gb - d.hardware_details.disk_info[0].free_gb) / d.hardware_details.disk_info[0].total_gb) * 100
      if (diskUsage > 90) return true
    }
    return false
  })

  const getDeviceIcon = (type) => {
    switch (type) {
      case 'computer': return <Monitor className="h-4 w-4" />
      case 'laptop': return <Laptop className="h-4 w-4" />
      case 'smartphone': return <Smartphone className="h-4 w-4" />
      case 'printer': return <Printer className="h-4 w-4" />
      default: return <Monitor className="h-4 w-4" />
    }
  }

  return (
    <div className="space-y-6">
      {/* Cards de Estatísticas Principais */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total de Dispositivos</CardTitle>
            <Monitor className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalDevices}</div>
            <p className="text-xs text-muted-foreground">
              Dispositivos registrados
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Online</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{onlineDevices}</div>
            <p className="text-xs text-muted-foreground">
              {totalDevices > 0 ? Math.round((onlineDevices / totalDevices) * 100) : 0}% dos dispositivos
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Offline</CardTitle>
            <AlertTriangle className="h-4 w-4 text-red-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{offlineDevices}</div>
            <p className="text-xs text-muted-foreground">
              {totalDevices > 0 ? Math.round((offlineDevices / totalDevices) * 100) : 0}% dos dispositivos
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Alertas</CardTitle>
            <Activity className="h-4 w-4 text-orange-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">{alerts.length}</div>
            <p className="text-xs text-muted-foreground">
              Requerem atenção
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Gráficos e Visualizações */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Distribuição por Tipo de Dispositivo */}
        <Card>
          <CardHeader>
            <CardTitle>Distribuição por Tipo</CardTitle>
            <CardDescription>
              Tipos de dispositivos na rede
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={deviceTypeData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {deviceTypeData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="flex flex-wrap gap-2 mt-4">
              {deviceTypeData.map((item, index) => (
                <div key={index} className="flex items-center gap-2">
                  <div 
                    className="w-3 h-3 rounded-full" 
                    style={{ backgroundColor: item.color }}
                  />
                  <span className="text-sm">{item.name}: {item.value}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Uso de Recursos */}
        <Card>
          <CardHeader>
            <CardTitle>Uso de Recursos</CardTitle>
            <CardDescription>
              RAM e Disco dos dispositivos online
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={resourceData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip formatter={(value) => `${value}%`} />
                  <Bar dataKey="ram" fill="#2563eb" name="RAM" />
                  <Bar dataKey="disk" fill="#10b981" name="Disco" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Lista de Dispositivos Recentes e Alertas */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Dispositivos Recentes */}
        <Card>
          <CardHeader>
            <CardTitle>Dispositivos Recentes</CardTitle>
            <CardDescription>
              Últimos dispositivos detectados
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {devices
                .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
                .slice(0, 5)
                .map((device) => (
                  <div key={device.id} className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="flex items-center gap-3">
                      {getDeviceIcon(device.device_type)}
                      <div>
                        <p className="font-medium">{device.name}</p>
                        <p className="text-sm text-muted-foreground">{device.ip_address}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <Badge variant={device.status === 'online' ? 'default' : 'secondary'}>
                        {device.status}
                      </Badge>
                      <p className="text-xs text-muted-foreground mt-1">
                        {new Date(device.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                ))}
            </div>
            <Button variant="outline" className="w-full mt-4" onClick={onViewDevices}>
              Ver Todos os Dispositivos
            </Button>
          </CardContent>
        </Card>

        {/* Alertas e Problemas */}
        <Card>
          <CardHeader>
            <CardTitle>Alertas e Problemas</CardTitle>
            <CardDescription>
              Dispositivos que requerem atenção
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {alerts.length === 0 ? (
                <div className="text-center py-8">
                  <CheckCircle className="h-12 w-12 text-green-600 mx-auto mb-2" />
                  <p className="text-muted-foreground">Nenhum alerta no momento</p>
                </div>
              ) : (
                alerts.slice(0, 5).map((device) => {
                  const isOffline = device.status === 'offline'
                  const ramUsage = device.hardware_details?.ram_info ? 
                    (device.hardware_details.ram_info.used_gb / device.hardware_details.ram_info.total_gb) * 100 : 0
                  const diskUsage = device.hardware_details?.disk_info?.[0] ? 
                    ((device.hardware_details.disk_info[0].total_gb - device.hardware_details.disk_info[0].free_gb) / device.hardware_details.disk_info[0].total_gb) * 100 : 0
                  
                  return (
                    <div key={device.id} className="flex items-center justify-between p-3 border rounded-lg border-orange-200 bg-orange-50">
                      <div className="flex items-center gap-3">
                        <AlertTriangle className="h-4 w-4 text-orange-600" />
                        <div>
                          <p className="font-medium">{device.name}</p>
                          <p className="text-sm text-muted-foreground">
                            {isOffline ? 'Dispositivo offline' : 
                             ramUsage > 90 ? `RAM: ${ramUsage.toFixed(1)}%` :
                             diskUsage > 90 ? `Disco: ${diskUsage.toFixed(1)}%` : ''}
                          </p>
                        </div>
                      </div>
                      <Badge variant="outline" className="border-orange-600 text-orange-600">
                        {isOffline ? 'Offline' : 'Alto Uso'}
                      </Badge>
                    </div>
                  )
                })
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

export default DashboardOverview

