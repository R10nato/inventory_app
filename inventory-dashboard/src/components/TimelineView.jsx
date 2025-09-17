import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Input } from '@/components/ui/input.jsx'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select.jsx'
import { 
  History, Filter, Search, Calendar, Clock, 
  ArrowUpDown, ChevronDown, ChevronRight, Eye,
  GitCompare, AlertTriangle, Info, Plus, Minus
} from 'lucide-react'
import { Progress } from '@/components/ui/progress.jsx'

const API_BASE = "http://localhost:8000"

const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  return isNaN(date.getTime()) ? 'N/A' : date.toLocaleString('pt-BR')
}

const getChangeTypeColor = (changeType) => {
  switch (changeType) {
    case 'NEW_DEVICE': return 'bg-green-100 text-green-800 border-green-200'
    case 'REMOVED_DEVICE': return 'bg-red-100 text-red-800 border-red-200'
    case 'UPDATED_DEVICE': return 'bg-blue-100 text-blue-800 border-blue-200'
    default: return 'bg-gray-100 text-gray-800 border-gray-200'
  }
}

const getChangeIcon = (changeType) => {
  switch (changeType) {
    case 'NEW_DEVICE': return <Plus className="h-4 w-4" />
    case 'REMOVED_DEVICE': return <Minus className="h-4 w-4" />
    case 'UPDATED_DEVICE': return <GitCompare className="h-4 w-4" />
    default: return <Info className="h-4 w-4" />
  }
}

const TimelineItem = ({ log, onViewDiff }) => {
  const [expanded, setExpanded] = useState(false)
  const [changes, setChanges] = useState(null)

  useEffect(() => {
    if (log.change_description) {
      try {
        const parsed = JSON.parse(log.change_description)
        setChanges(parsed)
      } catch {
        setChanges(null)
      }
    }
  }, [log.change_description])

  return (
    <div className="relative">
      {/* Timeline line */}
      <div className="absolute left-6 top-12 bottom-0 w-0.5 bg-gray-200"></div>
      
      <div className="flex items-start space-x-4 pb-6">
        {/* Timeline dot */}
        <div className={`flex items-center justify-center w-12 h-12 rounded-full border-2 ${getChangeTypeColor(log.change_type)} z-10`}>
          {getChangeIcon(log.change_type)}
        </div>
        
        {/* Content */}
        <div className="flex-1 min-w-0">
          <Card className="w-full">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <CardTitle className="text-sm font-medium">
                    {log.component || 'Sistema'}
                  </CardTitle>
                  <Badge variant="outline" className={`text-xs ${getChangeTypeColor(log.change_type)}`}>
                    {log.change_type || 'Alteração'}
                  </Badge>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-xs text-muted-foreground">
                    {formatDate(log.timestamp)}
                  </span>
                  {changes && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setExpanded(!expanded)}
                    >
                      {expanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                    </Button>
                  )}
                </div>
              </div>
              <CardDescription className="text-sm">
                {log.change_description && !changes ? log.change_description : 'Alteração detectada no sistema'}
              </CardDescription>
            </CardHeader>
            
            {expanded && changes && (
              <CardContent className="pt-0">
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <h4 className="text-sm font-medium">Detalhes da Alteração</h4>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => onViewDiff && onViewDiff(log)}
                    >
                      <Eye className="h-4 w-4 mr-2" />
                      Ver Diff
                    </Button>
                  </div>
                  
                  {typeof changes === 'object' && (
                    <div className="space-y-2">
                      {Object.entries(changes).map(([key, value]) => (
                        <div key={key} className="p-2 bg-gray-50 rounded text-xs">
                          <div className="font-medium text-gray-700">{key}:</div>
                          <div className="mt-1">
                            {typeof value === 'object' ? (
                              <div className="space-y-1">
                                {value.old !== undefined && (
                                  <div className="text-red-600">- {JSON.stringify(value.old)}</div>
                                )}
                                {value.new !== undefined && (
                                  <div className="text-green-600">+ {JSON.stringify(value.new)}</div>
                                )}
                              </div>
                            ) : (
                              <div>{JSON.stringify(value)}</div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </CardContent>
            )}
          </Card>
        </div>
      </div>
    </div>
  )
}

const TimelineView = ({ deviceId = null }) => {
  const [logs, setLogs] = useState([])
  const [snapshots, setSnapshots] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  
  // Filtros
  const [searchTerm, setSearchTerm] = useState('')
  const [filterType, setFilterType] = useState('all')
  const [filterComponent, setFilterComponent] = useState('all')
  const [sortOrder, setSortOrder] = useState('desc')
  const [dateRange, setDateRange] = useState('all')
  
  // Paginação
  const [currentPage, setCurrentPage] = useState(1)
  const [itemsPerPage] = useState(20)

  useEffect(() => {
    fetchData()
  }, [deviceId])

  const fetchData = async () => {
    try {
      setLoading(true)
      
      // Buscar logs de histórico
      const logsUrl = deviceId 
        ? `${API_BASE}/history_logs/device/${deviceId}`
        : `${API_BASE}/history_logs/`
      
      const logsResponse = await fetch(logsUrl)
      const logsData = await logsResponse.json()
      
      // Buscar snapshots
      const snapshotsResponse = await fetch(`${API_BASE}/snapshots/`)
      const snapshotsData = await snapshotsResponse.json()
      
      // Handle paginated response format {items: [], total: X, skip: Y, limit: Z}
      const logsArray = logsData && Array.isArray(logsData.items) 
        ? logsData.items 
        : (Array.isArray(logsData) ? logsData : [])
      
      setLogs(logsArray)
      setSnapshots(Array.isArray(snapshotsData) ? snapshotsData : [])
      setError(null)
    } catch (err) {
      setError('Erro ao carregar dados da timeline')
      console.error('Error fetching timeline data:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleCreateSnapshot = async () => {
    try {
      const response = await fetch(`${API_BASE}/snapshots/`, { method: 'POST' })
      if (response.ok) {
        fetchData() // Recarrega os dados
      }
    } catch (err) {
      console.error('Error creating snapshot:', err)
    }
  }

  const handleCompareSnapshots = async () => {
    try {
      const response = await fetch(`${API_BASE}/snapshots/compare`, { method: 'POST' })
      if (response.ok) {
        fetchData() // Recarrega os dados
      }
    } catch (err) {
      console.error('Error comparing snapshots:', err)
    }
  }

  // Filtrar e ordenar logs
  const filteredLogs = logs.filter(log => {
    if (searchTerm && !log.change_description?.toLowerCase().includes(searchTerm.toLowerCase()) &&
        !log.component?.toLowerCase().includes(searchTerm.toLowerCase())) {
      return false
    }
    
    if (filterType !== 'all' && log.change_type !== filterType) {
      return false
    }
    
    if (filterComponent !== 'all' && log.component !== filterComponent) {
      return false
    }
    
    if (dateRange !== 'all') {
      const logDate = new Date(log.timestamp)
      const now = new Date()
      const daysDiff = (now - logDate) / (1000 * 60 * 60 * 24)
      
      switch (dateRange) {
        case '1d': return daysDiff <= 1
        case '7d': return daysDiff <= 7
        case '30d': return daysDiff <= 30
        default: return true
      }
    }
    
    return true
  }).sort((a, b) => {
    const dateA = new Date(a.timestamp)
    const dateB = new Date(b.timestamp)
    return sortOrder === 'desc' ? dateB - dateA : dateA - dateB
  })

  // Paginação
  const totalPages = Math.ceil(filteredLogs.length / itemsPerPage)
  const startIndex = (currentPage - 1) * itemsPerPage
  const paginatedLogs = filteredLogs.slice(startIndex, startIndex + itemsPerPage)

  // Obter componentes únicos para filtro
  const uniqueComponents = [...new Set(logs.map(log => log.component).filter(Boolean))]

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <History className="h-8 w-8 animate-spin mx-auto mb-4" />
          <p className="text-muted-foreground">Carregando timeline...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center h-64">
          <div className="text-center">
            <AlertTriangle className="h-8 w-8 text-destructive mx-auto mb-4" />
            <p className="text-muted-foreground">{error}</p>
            <Button onClick={fetchData} className="mt-4">
              Tentar Novamente
            </Button>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <History className="h-6 w-6" />
            Timeline {deviceId ? 'do Dispositivo' : 'do Sistema'}
          </h2>
          <p className="text-muted-foreground">
            {filteredLogs.length} eventos encontrados
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button onClick={handleCreateSnapshot} variant="outline">
            Criar Snapshot
          </Button>
          <Button onClick={handleCompareSnapshots} variant="outline">
            Comparar Snapshots
          </Button>
        </div>
      </div>

      {/* Filtros */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="h-5 w-5" />
            Filtros
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Buscar</label>
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Buscar eventos..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-9"
                />
              </div>
            </div>
            
            <div className="space-y-2">
              <label className="text-sm font-medium">Tipo de Alteração</label>
              <Select value={filterType} onValueChange={setFilterType}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todos os tipos</SelectItem>
                  <SelectItem value="NEW_DEVICE">Novo Dispositivo</SelectItem>
                  <SelectItem value="REMOVED_DEVICE">Dispositivo Removido</SelectItem>
                  <SelectItem value="UPDATED_DEVICE">Dispositivo Atualizado</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <label className="text-sm font-medium">Componente</label>
              <Select value={filterComponent} onValueChange={setFilterComponent}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todos os componentes</SelectItem>
                  {uniqueComponents.map(component => (
                    <SelectItem key={component} value={component}>
                      {component}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <label className="text-sm font-medium">Período</label>
              <Select value={dateRange} onValueChange={setDateRange}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todo o período</SelectItem>
                  <SelectItem value="1d">Últimas 24h</SelectItem>
                  <SelectItem value="7d">Últimos 7 dias</SelectItem>
                  <SelectItem value="30d">Últimos 30 dias</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          
          <div className="flex items-center justify-between mt-4">
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setSortOrder(sortOrder === 'desc' ? 'asc' : 'desc')}
              >
                <ArrowUpDown className="h-4 w-4 mr-2" />
                {sortOrder === 'desc' ? 'Mais recente primeiro' : 'Mais antigo primeiro'}
              </Button>
            </div>
            
            <div className="text-sm text-muted-foreground">
              {snapshots.length} snapshots • {logs.length} eventos totais
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Timeline */}
      <div className="space-y-4">
        {paginatedLogs.length > 0 ? (
          <>
            <div className="space-y-0">
              {paginatedLogs.map((log, index) => (
                <TimelineItem
                  key={log.id || index}
                  log={log}
                  onViewDiff={(log) => console.log('View diff for:', log)}
                />
              ))}
            </div>
            
            {/* Paginação */}
            {totalPages > 1 && (
              <div className="flex items-center justify-center space-x-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                  disabled={currentPage === 1}
                >
                  Anterior
                </Button>
                <span className="text-sm text-muted-foreground">
                  Página {currentPage} de {totalPages}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                  disabled={currentPage === totalPages}
                >
                  Próxima
                </Button>
              </div>
            )}
          </>
        ) : (
          <Card>
            <CardContent className="flex items-center justify-center h-64">
              <div className="text-center">
                <History className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-lg font-medium mb-2">Nenhum evento encontrado</h3>
                <p className="text-muted-foreground mb-4">
                  Não há eventos que correspondam aos filtros selecionados.
                </p>
                <Button onClick={() => {
                  setSearchTerm('')
                  setFilterType('all')
                  setFilterComponent('all')
                  setDateRange('all')
                }}>
                  Limpar Filtros
                </Button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}

export default TimelineView
