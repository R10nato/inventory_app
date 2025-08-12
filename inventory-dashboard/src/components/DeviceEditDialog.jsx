import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Input } from '@/components/ui/input.jsx'
import { Label } from '@/components/ui/label.jsx'
import { Textarea } from '@/components/ui/textarea.jsx'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select.jsx'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog.jsx'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs.jsx'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Separator } from '@/components/ui/separator.jsx'
import { 
  Save, 
  X, 
  Monitor, 
  Laptop, 
  Smartphone, 
  Printer,
  Cpu,
  MemoryStick,
  HardDrive,
  Wifi,
  Plus,
  Trash2,
  AlertCircle
} from 'lucide-react'
import { format } from 'date-fns'
import { ptBR } from 'date-fns/locale'

const DeviceEditDialog = ({ device, open, onOpenChange, onSave }) => {
  const [formData, setFormData] = useState({
    name: '',
    ip_address: '',
    mac_address: '',
    device_type: '',
    os: '',
    status: '',
    hardware_details: {
      cpu_info: {
        brand: '',
        model: '',
        cores: '',
        threads: '',
        frequency_mhz: ''
      },
      ram_info: {
        total_gb: '',
        modules: []
      },
      disk_info: [],
      gpu_info: {
        brand: '',
        model: '',
        vram_mb: '',
        driver_version: ''
      },
      motherboard_info: {
        manufacturer: '',
        model: '',
        serial_number: ''
      },
      network_info: []
    }
  })
  
  const [errors, setErrors] = useState({})
  const [isLoading, setIsLoading] = useState(false)

  // Inicializar dados do formulário quando o dispositivo mudar
  useEffect(() => {
    if (device) {
      setFormData({
        name: device.name || '',
        ip_address: device.ip_address || '',
        mac_address: device.mac_address || '',
        device_type: device.device_type || '',
        os: device.os || '',
        status: device.status || '',
        hardware_details: {
          cpu_info: {
            brand: device.hardware_details?.cpu_info?.brand || '',
            model: device.hardware_details?.cpu_info?.model || '',
            cores: device.hardware_details?.cpu_info?.cores?.toString() || '',
            threads: device.hardware_details?.cpu_info?.threads?.toString() || '',
            frequency_mhz: device.hardware_details?.cpu_info?.frequency_mhz?.toString() || ''
          },
          ram_info: {
            total_gb: device.hardware_details?.ram_info?.total_gb?.toString() || '',
            modules: device.hardware_details?.ram_info?.modules || []
          },
          disk_info: device.hardware_details?.disk_info || [],
          gpu_info: {
            brand: device.hardware_details?.gpu_info?.brand || '',
            model: device.hardware_details?.gpu_info?.model || '',
            vram_mb: device.hardware_details?.gpu_info?.vram_mb?.toString() || '',
            driver_version: device.hardware_details?.gpu_info?.driver_version || ''
          },
          motherboard_info: {
            manufacturer: device.hardware_details?.motherboard_info?.manufacturer || '',
            model: device.hardware_details?.motherboard_info?.model || '',
            serial_number: device.hardware_details?.motherboard_info?.serial_number || ''
          },
          network_info: device.hardware_details?.network_info || []
        }
      })
      setErrors({})
    }
  }, [device])

  const handleInputChange = (path, value) => {
    setFormData(prev => {
      const newData = { ...prev }
      const keys = path.split('.')
      let current = newData
      
      for (let i = 0; i < keys.length - 1; i++) {
        if (!current[keys[i]]) current[keys[i]] = {}
        current = current[keys[i]]
      }
      
      current[keys[keys.length - 1]] = value
      return newData
    })
    
    // Limpar erro do campo quando o usuário começar a digitar
    if (errors[path]) {
      setErrors(prev => ({ ...prev, [path]: null }))
    }
  }

  const validateForm = () => {
    const newErrors = {}
    
    // Validações básicas
    if (!formData.name.trim()) {
      newErrors.name = 'Nome é obrigatório'
    }
    
    if (!formData.ip_address.trim()) {
      newErrors.ip_address = 'Endereço IP é obrigatório'
    } else if (!/^(\d{1,3}\.){3}\d{1,3}$/.test(formData.ip_address)) {
      newErrors.ip_address = 'Formato de IP inválido'
    }
    
    if (formData.mac_address && !/^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$/.test(formData.mac_address)) {
      newErrors.mac_address = 'Formato de MAC inválido'
    }
    
    if (!formData.device_type) {
      newErrors.device_type = 'Tipo de dispositivo é obrigatório'
    }
    
    // Validações de hardware (opcionais mas com formato)
    if (formData.hardware_details.cpu_info.cores && isNaN(formData.hardware_details.cpu_info.cores)) {
      newErrors['hardware_details.cpu_info.cores'] = 'Número de cores deve ser numérico'
    }
    
    if (formData.hardware_details.cpu_info.threads && isNaN(formData.hardware_details.cpu_info.threads)) {
      newErrors['hardware_details.cpu_info.threads'] = 'Número de threads deve ser numérico'
    }
    
    if (formData.hardware_details.cpu_info.frequency_mhz && isNaN(formData.hardware_details.cpu_info.frequency_mhz)) {
      newErrors['hardware_details.cpu_info.frequency_mhz'] = 'Frequência deve ser numérica'
    }
    
    if (formData.hardware_details.ram_info.total_gb && isNaN(formData.hardware_details.ram_info.total_gb)) {
      newErrors['hardware_details.ram_info.total_gb'] = 'Total de RAM deve ser numérico'
    }
    
    if (formData.hardware_details.gpu_info.vram_mb && isNaN(formData.hardware_details.gpu_info.vram_mb)) {
      newErrors['hardware_details.gpu_info.vram_mb'] = 'VRAM deve ser numérica'
    }
    
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSave = async () => {
    if (!validateForm()) {
      return
    }
    
    setIsLoading(true)
    
    try {
      // Converter strings numéricas de volta para números
      const processedData = {
        ...formData,
        hardware_details: {
          ...formData.hardware_details,
          cpu_info: {
            ...formData.hardware_details.cpu_info,
            cores: formData.hardware_details.cpu_info.cores ? parseInt(formData.hardware_details.cpu_info.cores) : null,
            threads: formData.hardware_details.cpu_info.threads ? parseInt(formData.hardware_details.cpu_info.threads) : null,
            frequency_mhz: formData.hardware_details.cpu_info.frequency_mhz ? parseInt(formData.hardware_details.cpu_info.frequency_mhz) : null
          },
          ram_info: {
            ...formData.hardware_details.ram_info,
            total_gb: formData.hardware_details.ram_info.total_gb ? parseFloat(formData.hardware_details.ram_info.total_gb) : null,
            modules: formData.hardware_details.ram_info.modules.map(module => ({
              ...module,
              capacity_gb: module.capacity_gb ? parseFloat(module.capacity_gb) : null,
              speed_mhz: module.speed_mhz ? parseInt(module.speed_mhz) : null
            }))
          },
          gpu_info: {
            ...formData.hardware_details.gpu_info,
            vram_mb: formData.hardware_details.gpu_info.vram_mb ? parseInt(formData.hardware_details.gpu_info.vram_mb) : null
          }
        }
      }
      
      // Fazer chamada para a API
      const response = await fetch(`http://localhost:8000/devices/${device.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(processedData)
      })
      
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Erro ao salvar as alterações')
      }
      
      const updatedDevice = await response.json()
      
      // Criar log de histórico para a mudança manual
      await fetch(`http://localhost:8000/devices/${device.id}/history`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          change_type: 'manual_edit',
          description: 'Dispositivo editado manualmente',
          old_value: JSON.stringify(device),
          new_value: JSON.stringify(updatedDevice),
          user: 'admin' // Em uma implementação real, isso viria do sistema de autenticação
        })
      })
      
      await onSave(updatedDevice)
      onOpenChange(false)
    } catch (error) {
      console.error('Erro ao salvar dispositivo:', error)
      setErrors({ general: error.message || 'Erro ao salvar as alterações. Tente novamente.' })
    } finally {
      setIsLoading(false)
    }
  }

  const getDeviceIcon = (type) => {
    switch (type) {
      case 'computer': return <Monitor className="h-5 w-5" />
      case 'laptop': return <Laptop className="h-5 w-5" />
      case 'smartphone': return <Smartphone className="h-5 w-5" />
      case 'printer': return <Printer className="h-5 w-5" />
      default: return <Monitor className="h-5 w-5" />
    }
  }

  const addRAMModule = () => {
    setFormData(prev => ({
      ...prev,
      hardware_details: {
        ...prev.hardware_details,
        ram_info: {
          ...prev.hardware_details.ram_info,
          modules: [
            ...prev.hardware_details.ram_info.modules,
            { capacity_gb: '', type: '', speed_mhz: '', manufacturer: '' }
          ]
        }
      }
    }))
  }

  const removeRAMModule = (index) => {
    setFormData(prev => ({
      ...prev,
      hardware_details: {
        ...prev.hardware_details,
        ram_info: {
          ...prev.hardware_details.ram_info,
          modules: prev.hardware_details.ram_info.modules.filter((_, i) => i !== index)
        }
      }
    }))
  }

  const updateRAMModule = (index, field, value) => {
    setFormData(prev => ({
      ...prev,
      hardware_details: {
        ...prev.hardware_details,
        ram_info: {
          ...prev.hardware_details.ram_info,
          modules: prev.hardware_details.ram_info.modules.map((module, i) => 
            i === index ? { ...module, [field]: value } : module
          )
        }
      }
    }))
  }

  const addNetworkInterface = () => {
    setFormData(prev => ({
      ...prev,
      hardware_details: {
        ...prev.hardware_details,
        network_info: [
          ...prev.hardware_details.network_info,
          { type: '', name: '', mac: '', ip_addresses: [] }
        ]
      }
    }))
  }

  const removeNetworkInterface = (index) => {
    setFormData(prev => ({
      ...prev,
      hardware_details: {
        ...prev.hardware_details,
        network_info: prev.hardware_details.network_info.filter((_, i) => i !== index)
      }
    }))
  }

  const updateNetworkInterface = (index, field, value) => {
    setFormData(prev => ({
      ...prev,
      hardware_details: {
        ...prev.hardware_details,
        network_info: prev.hardware_details.network_info.map((network, i) => 
          i === index ? { ...network, [field]: value } : network
        )
      }
    }))
  }

  if (!device) return null

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            {getDeviceIcon(device.device_type)}
            Editar Dispositivo: {device.name}
          </DialogTitle>
          <DialogDescription>
            Edite as informações do dispositivo. Os campos marcados com * são obrigatórios.
          </DialogDescription>
        </DialogHeader>

        {errors.general && (
          <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700">
            <AlertCircle className="h-4 w-4" />
            {errors.general}
          </div>
        )}

        <Tabs defaultValue="basic" className="space-y-4">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="basic">Básico</TabsTrigger>
            <TabsTrigger value="hardware">Hardware</TabsTrigger>
            <TabsTrigger value="memory">Memória</TabsTrigger>
            <TabsTrigger value="network">Rede</TabsTrigger>
          </TabsList>

          {/* Aba Básico */}
          <TabsContent value="basic" className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="name">Nome do Dispositivo *</Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) => handleInputChange('name', e.target.value)}
                  placeholder="Ex: DESKTOP-ABC123"
                />
                {errors.name && <p className="text-sm text-red-600">{errors.name}</p>}
              </div>

              <div className="space-y-2">
                <Label htmlFor="ip_address">Endereço IP *</Label>
                <Input
                  id="ip_address"
                  value={formData.ip_address}
                  onChange={(e) => handleInputChange('ip_address', e.target.value)}
                  placeholder="Ex: 192.168.1.100"
                />
                {errors.ip_address && <p className="text-sm text-red-600">{errors.ip_address}</p>}
              </div>

              <div className="space-y-2">
                <Label htmlFor="mac_address">Endereço MAC</Label>
                <Input
                  id="mac_address"
                  value={formData.mac_address}
                  onChange={(e) => handleInputChange('mac_address', e.target.value)}
                  placeholder="Ex: 00:11:22:33:44:55"
                />
                {errors.mac_address && <p className="text-sm text-red-600">{errors.mac_address}</p>}
              </div>

              <div className="space-y-2">
                <Label htmlFor="device_type">Tipo de Dispositivo *</Label>
                <Select value={formData.device_type} onValueChange={(value) => handleInputChange('device_type', value)}>
                  <SelectTrigger>
                    <SelectValue placeholder="Selecione o tipo" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="computer">Desktop</SelectItem>
                    <SelectItem value="laptop">Laptop</SelectItem>
                    <SelectItem value="smartphone">Smartphone</SelectItem>
                    <SelectItem value="printer">Impressora</SelectItem>
                    <SelectItem value="server">Servidor</SelectItem>
                    <SelectItem value="router">Roteador</SelectItem>
                    <SelectItem value="switch">Switch</SelectItem>
                  </SelectContent>
                </Select>
                {errors.device_type && <p className="text-sm text-red-600">{errors.device_type}</p>}
              </div>

              <div className="space-y-2">
                <Label htmlFor="os">Sistema Operacional</Label>
                <Input
                  id="os"
                  value={formData.os}
                  onChange={(e) => handleInputChange('os', e.target.value)}
                  placeholder="Ex: Windows 11 Pro"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="status">Status</Label>
                <Select value={formData.status} onValueChange={(value) => handleInputChange('status', value)}>
                  <SelectTrigger>
                    <SelectValue placeholder="Selecione o status" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="online">Online</SelectItem>
                    <SelectItem value="offline">Offline</SelectItem>
                    <SelectItem value="maintenance">Manutenção</SelectItem>
                    <SelectItem value="retired">Aposentado</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </TabsContent>

          {/* Aba Hardware */}
          <TabsContent value="hardware" className="space-y-4">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* CPU */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Cpu className="h-5 w-5 text-blue-600" />
                    Processador
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Marca</Label>
                      <Input
                        value={formData.hardware_details.cpu_info.brand}
                        onChange={(e) => handleInputChange('hardware_details.cpu_info.brand', e.target.value)}
                        placeholder="Ex: Intel"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Modelo</Label>
                      <Input
                        value={formData.hardware_details.cpu_info.model}
                        onChange={(e) => handleInputChange('hardware_details.cpu_info.model', e.target.value)}
                        placeholder="Ex: Core i7-12700K"
                      />
                    </div>
                  </div>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="space-y-2">
                      <Label>Cores</Label>
                      <Input
                        type="number"
                        value={formData.hardware_details.cpu_info.cores}
                        onChange={(e) => handleInputChange('hardware_details.cpu_info.cores', e.target.value)}
                        placeholder="Ex: 12"
                      />
                      {errors['hardware_details.cpu_info.cores'] && (
                        <p className="text-sm text-red-600">{errors['hardware_details.cpu_info.cores']}</p>
                      )}
                    </div>
                    <div className="space-y-2">
                      <Label>Threads</Label>
                      <Input
                        type="number"
                        value={formData.hardware_details.cpu_info.threads}
                        onChange={(e) => handleInputChange('hardware_details.cpu_info.threads', e.target.value)}
                        placeholder="Ex: 20"
                      />
                      {errors['hardware_details.cpu_info.threads'] && (
                        <p className="text-sm text-red-600">{errors['hardware_details.cpu_info.threads']}</p>
                      )}
                    </div>
                    <div className="space-y-2">
                      <Label>Frequência (MHz)</Label>
                      <Input
                        type="number"
                        value={formData.hardware_details.cpu_info.frequency_mhz}
                        onChange={(e) => handleInputChange('hardware_details.cpu_info.frequency_mhz', e.target.value)}
                        placeholder="Ex: 3600"
                      />
                      {errors['hardware_details.cpu_info.frequency_mhz'] && (
                        <p className="text-sm text-red-600">{errors['hardware_details.cpu_info.frequency_mhz']}</p>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* GPU */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Monitor className="h-5 w-5 text-indigo-600" />
                    Placa de Vídeo
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Marca</Label>
                      <Input
                        value={formData.hardware_details.gpu_info.brand}
                        onChange={(e) => handleInputChange('hardware_details.gpu_info.brand', e.target.value)}
                        placeholder="Ex: NVIDIA"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Modelo</Label>
                      <Input
                        value={formData.hardware_details.gpu_info.model}
                        onChange={(e) => handleInputChange('hardware_details.gpu_info.model', e.target.value)}
                        placeholder="Ex: GeForce RTX 4070"
                      />
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>VRAM (MB)</Label>
                      <Input
                        type="number"
                        value={formData.hardware_details.gpu_info.vram_mb}
                        onChange={(e) => handleInputChange('hardware_details.gpu_info.vram_mb', e.target.value)}
                        placeholder="Ex: 12288"
                      />
                      {errors['hardware_details.gpu_info.vram_mb'] && (
                        <p className="text-sm text-red-600">{errors['hardware_details.gpu_info.vram_mb']}</p>
                      )}
                    </div>
                    <div className="space-y-2">
                      <Label>Versão do Driver</Label>
                      <Input
                        value={formData.hardware_details.gpu_info.driver_version}
                        onChange={(e) => handleInputChange('hardware_details.gpu_info.driver_version', e.target.value)}
                        placeholder="Ex: 546.17"
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Placa-mãe */}
              <Card className="lg:col-span-2">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Cpu className="h-5 w-5 text-gray-600" />
                    Placa-mãe
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="space-y-2">
                      <Label>Fabricante</Label>
                      <Input
                        value={formData.hardware_details.motherboard_info.manufacturer}
                        onChange={(e) => handleInputChange('hardware_details.motherboard_info.manufacturer', e.target.value)}
                        placeholder="Ex: ASUS"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Modelo</Label>
                      <Input
                        value={formData.hardware_details.motherboard_info.model}
                        onChange={(e) => handleInputChange('hardware_details.motherboard_info.model', e.target.value)}
                        placeholder="Ex: ROG STRIX Z690-E"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Número de Série</Label>
                      <Input
                        value={formData.hardware_details.motherboard_info.serial_number}
                        onChange={(e) => handleInputChange('hardware_details.motherboard_info.serial_number', e.target.value)}
                        placeholder="Ex: MB123456789"
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Aba Memória */}
          <TabsContent value="memory" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <MemoryStick className="h-5 w-5 text-green-600" />
                  Informações de RAM
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>Total de RAM (GB)</Label>
                  <Input
                    type="number"
                    value={formData.hardware_details.ram_info.total_gb}
                    onChange={(e) => handleInputChange('hardware_details.ram_info.total_gb', e.target.value)}
                    placeholder="Ex: 32"
                  />
                  {errors['hardware_details.ram_info.total_gb'] && (
                    <p className="text-sm text-red-600">{errors['hardware_details.ram_info.total_gb']}</p>
                  )}
                </div>

                <Separator />

                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h4 className="font-medium">Módulos de RAM</h4>
                    <Button type="button" variant="outline" size="sm" onClick={addRAMModule}>
                      <Plus className="h-4 w-4 mr-2" />
                      Adicionar Módulo
                    </Button>
                  </div>

                  {formData.hardware_details.ram_info.modules.map((module, index) => (
                    <Card key={index} className="p-4">
                      <div className="flex items-center justify-between mb-3">
                        <h5 className="font-medium">Módulo {index + 1}</h5>
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={() => removeRAMModule(index)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="space-y-2">
                          <Label>Capacidade (GB)</Label>
                          <Input
                            type="number"
                            value={module.capacity_gb}
                            onChange={(e) => updateRAMModule(index, 'capacity_gb', e.target.value)}
                            placeholder="Ex: 16"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label>Tipo</Label>
                          <Input
                            value={module.type}
                            onChange={(e) => updateRAMModule(index, 'type', e.target.value)}
                            placeholder="Ex: DDR4"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label>Velocidade (MHz)</Label>
                          <Input
                            type="number"
                            value={module.speed_mhz}
                            onChange={(e) => updateRAMModule(index, 'speed_mhz', e.target.value)}
                            placeholder="Ex: 3200"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label>Fabricante</Label>
                          <Input
                            value={module.manufacturer}
                            onChange={(e) => updateRAMModule(index, 'manufacturer', e.target.value)}
                            placeholder="Ex: Corsair"
                          />
                        </div>
                      </div>
                    </Card>
                  ))}
                </div>
              </CardContent>
            </Card>
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
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <p className="text-sm text-muted-foreground">
                    Configure as interfaces de rede do dispositivo
                  </p>
                  <Button type="button" variant="outline" size="sm" onClick={addNetworkInterface}>
                    <Plus className="h-4 w-4 mr-2" />
                    Adicionar Interface
                  </Button>
                </div>

                {formData.hardware_details.network_info.map((network, index) => (
                  <Card key={index} className="p-4">
                    <div className="flex items-center justify-between mb-3">
                      <h5 className="font-medium">Interface {index + 1}</h5>
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => removeNetworkInterface(index)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="space-y-2">
                        <Label>Tipo</Label>
                        <Select 
                          value={network.type} 
                          onValueChange={(value) => updateNetworkInterface(index, 'type', value)}
                        >
                          <SelectTrigger>
                            <SelectValue placeholder="Selecione o tipo" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="Ethernet">Ethernet</SelectItem>
                            <SelectItem value="WiFi">WiFi</SelectItem>
                            <SelectItem value="Bluetooth">Bluetooth</SelectItem>
                            <SelectItem value="USB">USB</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="space-y-2">
                        <Label>Nome</Label>
                        <Input
                          value={network.name}
                          onChange={(e) => updateNetworkInterface(index, 'name', e.target.value)}
                          placeholder="Ex: Intel I225-V"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>MAC Address</Label>
                        <Input
                          value={network.mac}
                          onChange={(e) => updateNetworkInterface(index, 'mac', e.target.value)}
                          placeholder="Ex: 00:11:22:33:44:55"
                        />
                      </div>
                    </div>
                  </Card>
                ))}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={isLoading}>
            <X className="h-4 w-4 mr-2" />
            Cancelar
          </Button>
          <Button onClick={handleSave} disabled={isLoading}>
            <Save className="h-4 w-4 mr-2" />
            {isLoading ? 'Salvando...' : 'Salvar Alterações'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export default DeviceEditDialog

