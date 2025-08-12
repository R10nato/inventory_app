import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs.jsx'
import { Monitor, Cpu, HardDrive, MemoryStick, Wifi, Activity, Clock, AlertTriangle } from 'lucide-react'
import DashboardOverview from './components/DashboardOverview'
import DeviceGrid from './components/DeviceGrid'
import DeviceDetail from './components/DeviceDetail'
import './App.css'

function App() {
  const [devices, setDevices] = useState([])
  const [selectedDevice, setSelectedDevice] = useState(null)
  const [currentView, setCurrentView] = useState('overview') // 'overview', 'devices', 'detail'
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Mock data para desenvolvimento - substituir pela API real
  const mockDevices = [
    {
      id: 1,
      name: "DESKTOP-ABC123",
      ip_address: "192.168.1.100",
      mac_address: "00:11:22:33:44:55",
      device_type: "computer",
      os: "Windows 11 Pro",
      status: "online",
      last_seen: new Date().toISOString(),
      created_at: new Date(Date.now() - 86400000).toISOString(),
      hardware_details: {
        cpu_info: {
          brand: "Intel",
          model: "Intel Core i7-12700K",
          cores: 12,
          threads: 20,
          frequency_mhz: 3600
        },
        ram_info: {
          total_gb: 32,
          used_gb: 16.5,
          modules: [
            { capacity_gb: 16, type: "DDR4", speed_mhz: 3200, manufacturer: "Corsair" },
            { capacity_gb: 16, type: "DDR4", speed_mhz: 3200, manufacturer: "Corsair" }
          ],
          slots_total: 4,
          slots_used: 2
        },
        disk_info: [
          {
            name: "Samsung SSD 980 PRO",
            type: "SSD",
            total_gb: 1000,
            free_gb: 450,
            partitions: [
              { drive_letter: "C:", total_gb: 1000, free_gb: 450, fstype: "NTFS" }
            ]
          }
        ],
        gpu_info: {
          brand: "NVIDIA",
          model: "GeForce RTX 4070",
          vram_mb: 12288,
          driver_version: "546.17"
        },
        motherboard_info: {
          manufacturer: "ASUS",
          model: "ROG STRIX Z690-E",
          serial_number: "MB123456789"
        },
        network_info: [
          {
            type: "Ethernet",
            name: "Intel I225-V",
            mac: "00:11:22:33:44:55",
            ip_addresses: ["192.168.1.100"]
          }
        ],
        temperature_info: {
          cpu: 45,
          gpu: 38,
          motherboard: 35
        }
      },
      history_logs: [
        {
          id: 1,
          component: "RAM",
          change_description: "Módulo de RAM adicionado",
          details_before: "16GB DDR4",
          details_after: "32GB DDR4",
          user: "admin",
          timestamp: new Date(Date.now() - 3600000).toISOString()
        }
      ]
    },
    {
      id: 2,
      name: "LAPTOP-XYZ789",
      ip_address: "192.168.1.101",
      mac_address: "AA:BB:CC:DD:EE:FF",
      device_type: "laptop",
      os: "Windows 11 Home",
      status: "offline",
      last_seen: new Date(Date.now() - 7200000).toISOString(),
      created_at: new Date(Date.now() - 172800000).toISOString(),
      hardware_details: {
        cpu_info: {
          brand: "AMD",
          model: "Ryzen 7 5800H",
          cores: 8,
          threads: 16,
          frequency_mhz: 3200
        },
        ram_info: {
          total_gb: 16,
          used_gb: 8.2,
          modules: [
            { capacity_gb: 16, type: "DDR4", speed_mhz: 3200, manufacturer: "Samsung" }
          ],
          slots_total: 2,
          slots_used: 1
        },
        disk_info: [
          {
            name: "WD Blue SN570",
            type: "SSD",
            total_gb: 512,
            free_gb: 180,
            partitions: [
              { drive_letter: "C:", total_gb: 512, free_gb: 180, fstype: "NTFS" }
            ]
          }
        ],
        gpu_info: {
          brand: "NVIDIA",
          model: "GeForce RTX 3060",
          vram_mb: 6144,
          driver_version: "546.17"
        }
      },
      history_logs: []
    }
  ]

  useEffect(() => {
    // Simular carregamento de dados
    const loadDevices = async () => {
      try {
        setLoading(true)
        // Chamada real para a API
        const response = await fetch('http://localhost:8000/devices/')
        const data = await response.json()
        
        // Se não houver dispositivos na API, usar dados mock para demonstração
        if (data.length === 0) {
          setDevices(mockDevices)
        } else {
          setDevices(data)
        }
        setError(null)
      } catch (err) {
        setError('Erro ao carregar dispositivos')
        console.error('Error loading devices:', err)
      } finally {
        setLoading(false)
      }
    }

    loadDevices()
  }, [])

  const handleDeviceSelect = (device) => {
    setSelectedDevice(device)
    setCurrentView('detail')
  }

  const handleBackToDevices = () => {
    setSelectedDevice(null)
    setCurrentView('devices')
  }

  const handleBackToOverview = () => {
    setSelectedDevice(null)
    setCurrentView('overview')
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <Activity className="h-8 w-8 animate-spin mx-auto mb-4" />
          <p className="text-muted-foreground">Carregando dispositivos...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Card className="w-96">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-destructive" />
              Erro
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground mb-4">{error}</p>
            <Button onClick={() => window.location.reload()}>
              Tentar Novamente
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-card">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Monitor className="h-8 w-8 text-primary" />
              <div>
                <h1 className="text-2xl font-bold">Inventory Dashboard</h1>
                <p className="text-sm text-muted-foreground">Sistema de Gerenciamento de Hardware</p>
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              <Badge variant={devices.filter(d => d.status === 'online').length > 0 ? 'default' : 'secondary'}>
                {devices.filter(d => d.status === 'online').length} Online
              </Badge>
              <Badge variant="outline">
                {devices.length} Total
              </Badge>
            </div>
          </div>
          
          {/* Navigation */}
          <nav className="mt-4">
            <div className="flex gap-2">
              <Button 
                variant={currentView === 'overview' ? 'default' : 'ghost'}
                onClick={handleBackToOverview}
              >
                Visão Geral
              </Button>
              <Button 
                variant={currentView === 'devices' ? 'default' : 'ghost'}
                onClick={() => setCurrentView('devices')}
              >
                Dispositivos
              </Button>
            </div>
          </nav>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-6">
        {currentView === 'overview' && (
          <DashboardOverview 
            devices={devices} 
            onViewDevices={() => setCurrentView('devices')}
          />
        )}
        
        {currentView === 'devices' && (
          <DeviceGrid 
            devices={devices} 
            onDeviceSelect={handleDeviceSelect}
          />
        )}
        
        {currentView === 'detail' && selectedDevice && (
          <DeviceDetail 
            device={selectedDevice} 
            onBack={handleBackToDevices}
          />
        )}
      </main>
    </div>
  )
}

export default App

