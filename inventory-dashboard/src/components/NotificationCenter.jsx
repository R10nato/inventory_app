import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { 
  Bell, BellRing, X, Check, AlertTriangle, Info, 
  CheckCircle, XCircle, Filter, MoreVertical, Trash2
} from 'lucide-react'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover.jsx'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs.jsx'

const API_BASE = "http://localhost:8000"

const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  return isNaN(date.getTime()) ? 'N/A' : date.toLocaleString('pt-BR')
}

const getAlertIcon = (alertType) => {
  switch (alertType) {
    case 'success': return <CheckCircle className="h-4 w-4 text-green-600" />
    case 'warning': return <AlertTriangle className="h-4 w-4 text-yellow-600" />
    case 'error': return <XCircle className="h-4 w-4 text-red-600" />
    default: return <Info className="h-4 w-4 text-blue-600" />
  }
}

const getAlertColor = (alertType, severity) => {
  const baseColors = {
    success: 'bg-green-50 border-green-200 text-green-800',
    warning: 'bg-yellow-50 border-yellow-200 text-yellow-800',
    error: 'bg-red-50 border-red-200 text-red-800',
    info: 'bg-blue-50 border-blue-200 text-blue-800'
  }
  
  const severityColors = {
    critical: 'bg-red-100 border-red-300 text-red-900',
    high: 'bg-orange-50 border-orange-200 text-orange-800',
    medium: baseColors[alertType] || baseColors.info,
    low: 'bg-gray-50 border-gray-200 text-gray-700'
  }
  
  return severityColors[severity] || baseColors[alertType] || baseColors.info
}

const getSeverityBadge = (severity) => {
  const colors = {
    critical: 'bg-red-600 text-white',
    high: 'bg-orange-500 text-white',
    medium: 'bg-yellow-500 text-white',
    low: 'bg-gray-400 text-white'
  }
  
  return colors[severity] || colors.medium
}

const AlertItem = ({ alert, onMarkAsRead, onResolve, onDelete }) => {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className={`p-3 rounded-lg border ${getAlertColor(alert.alert_type, alert.severity)} ${!alert.is_read ? 'ring-2 ring-blue-200' : ''}`}>
      <div className="flex items-start justify-between">
        <div className="flex items-start space-x-3 flex-1">
          {getAlertIcon(alert.alert_type)}
          <div className="flex-1 min-w-0">
            <div className="flex items-center space-x-2 mb-1">
              <h4 className="font-medium text-sm truncate">{alert.title}</h4>
              <Badge className={`text-xs ${getSeverityBadge(alert.severity)}`}>
                {alert.severity.toUpperCase()}
              </Badge>
              {!alert.is_read && (
                <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
              )}
            </div>
            <p className="text-sm text-muted-foreground mb-2">{alert.message}</p>
            <div className="flex items-center space-x-4 text-xs text-muted-foreground">
              <span>{formatDate(alert.created_at)}</span>
              <span>Origem: {alert.source}</span>
              {alert.is_resolved && (
                <Badge variant="outline" className="text-xs">
                  Resolvido
                </Badge>
              )}
            </div>
          </div>
        </div>
        
        <div className="flex items-center space-x-1">
          {!alert.is_read && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onMarkAsRead(alert.id)}
              title="Marcar como lido"
            >
              <Check className="h-4 w-4" />
            </Button>
          )}
          {!alert.is_resolved && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onResolve(alert.id)}
              title="Marcar como resolvido"
            >
              <CheckCircle className="h-4 w-4" />
            </Button>
          )}
          <Popover>
            <PopoverTrigger asChild>
              <Button variant="ghost" size="sm">
                <MoreVertical className="h-4 w-4" />
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-40">
              <div className="space-y-1">
                <Button
                  variant="ghost"
                  size="sm"
                  className="w-full justify-start"
                  onClick={() => setExpanded(!expanded)}
                >
                  {expanded ? 'Ocultar' : 'Ver'} Detalhes
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="w-full justify-start text-red-600"
                  onClick={() => onDelete(alert.id)}
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  Excluir
                </Button>
              </div>
            </PopoverContent>
          </Popover>
        </div>
      </div>
      
      {expanded && alert.alert_metadata && (
        <div className="mt-3 pt-3 border-t border-gray-200">
          <h5 className="text-xs font-medium mb-2">Detalhes Técnicos:</h5>
          <pre className="text-xs bg-gray-100 p-2 rounded overflow-auto">
            {JSON.stringify(alert.alert_metadata, null, 2)}
          </pre>
        </div>
      )}
    </div>
  )
}

const NotificationCenter = ({ isOpen, onClose }) => {
  const [alerts, setAlerts] = useState([])
  const [stats, setStats] = useState({})
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('all') // 'all', 'unread', 'unresolved'

  useEffect(() => {
    if (isOpen) {
      fetchAlerts()
      fetchStats()
    }
  }, [isOpen, filter])

  const fetchAlerts = async () => {
    try {
      setLoading(true)
      const params = new URLSearchParams()
      if (filter === 'unread') params.append('unread_only', 'true')
      if (filter === 'unresolved') params.append('unresolved_only', 'true')
      
      const response = await fetch(`${API_BASE}/alerts/?${params}`)
      const data = await response.json()
      setAlerts(Array.isArray(data) ? data : [])
    } catch (error) {
      console.error('Error fetching alerts:', error)
      setAlerts([])
    } finally {
      setLoading(false)
    }
  }

  const fetchStats = async () => {
    try {
      const response = await fetch(`${API_BASE}/alerts/stats`)
      const data = await response.json()
      setStats(data)
    } catch (error) {
      console.error('Error fetching alert stats:', error)
      setStats({})
    }
  }

  const handleMarkAsRead = async (alertId) => {
    try {
      await fetch(`${API_BASE}/alerts/${alertId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_read: true })
      })
      fetchAlerts()
      fetchStats()
    } catch (error) {
      console.error('Error marking alert as read:', error)
    }
  }

  const handleResolve = async (alertId) => {
    try {
      await fetch(`${API_BASE}/alerts/${alertId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_resolved: true, resolved_by: 'user' })
      })
      fetchAlerts()
      fetchStats()
    } catch (error) {
      console.error('Error resolving alert:', error)
    }
  }

  const handleDelete = async (alertId) => {
    try {
      await fetch(`${API_BASE}/alerts/${alertId}`, { method: 'DELETE' })
      fetchAlerts()
      fetchStats()
    } catch (error) {
      console.error('Error deleting alert:', error)
    }
  }

  const handleMarkAllAsRead = async () => {
    try {
      await fetch(`${API_BASE}/alerts/mark-all-read`, { method: 'POST' })
      fetchAlerts()
      fetchStats()
    } catch (error) {
      console.error('Error marking all as read:', error)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center">
      <Card className="w-full max-w-4xl max-h-[80vh] overflow-hidden">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Bell className="h-5 w-5" />
              Central de Notificações
            </CardTitle>
            <CardDescription>
              {stats.total || 0} alertas • {stats.unread || 0} não lidos • {stats.unresolved || 0} não resolvidos
            </CardDescription>
          </div>
          <div className="flex items-center space-x-2">
            {stats.unread > 0 && (
              <Button variant="outline" size="sm" onClick={handleMarkAllAsRead}>
                Marcar Todos como Lidos
              </Button>
            )}
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="h-4 w-4" />
            </Button>
          </div>
        </CardHeader>
        
        <CardContent className="space-y-4">
          {/* Filtros */}
          <Tabs value={filter} onValueChange={setFilter}>
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="all">Todos ({stats.total || 0})</TabsTrigger>
              <TabsTrigger value="unread">Não Lidos ({stats.unread || 0})</TabsTrigger>
              <TabsTrigger value="unresolved">Não Resolvidos ({stats.unresolved || 0})</TabsTrigger>
            </TabsList>
          </Tabs>

          {/* Estatísticas */}
          {stats.by_severity && (
            <div className="grid grid-cols-4 gap-2">
              {Object.entries(stats.by_severity).map(([severity, count]) => (
                <div key={severity} className="text-center">
                  <div className={`text-xs px-2 py-1 rounded ${getSeverityBadge(severity)}`}>
                    {severity.toUpperCase()}
                  </div>
                  <div className="text-sm font-medium mt-1">{count}</div>
                </div>
              ))}
            </div>
          )}

          {/* Lista de Alertas */}
          <div className="max-h-96 overflow-y-auto space-y-3">
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <Bell className="h-8 w-8 animate-pulse text-muted-foreground" />
              </div>
            ) : alerts.length > 0 ? (
              alerts.map((alert) => (
                <AlertItem
                  key={alert.id}
                  alert={alert}
                  onMarkAsRead={handleMarkAsRead}
                  onResolve={handleResolve}
                  onDelete={handleDelete}
                />
              ))
            ) : (
              <div className="text-center py-8">
                <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-4" />
                <h3 className="text-lg font-medium mb-2">Nenhum alerta encontrado</h3>
                <p className="text-muted-foreground">
                  {filter === 'all' ? 'Não há alertas no sistema.' : 
                   filter === 'unread' ? 'Todos os alertas foram lidos.' :
                   'Todos os alertas foram resolvidos.'}
                </p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

// Componente do ícone de notificação para a navbar
export const NotificationBell = ({ onClick }) => {
  const [unreadCount, setUnreadCount] = useState(0)

  useEffect(() => {
    const fetchUnreadCount = async () => {
      try {
        const response = await fetch(`${API_BASE}/alerts/stats`)
        const data = await response.json()
        setUnreadCount(data.unread || 0)
      } catch (error) {
        console.error('Error fetching unread count:', error)
      }
    }

    fetchUnreadCount()
    // Atualizar a cada 30 segundos
    const interval = setInterval(fetchUnreadCount, 30000)
    return () => clearInterval(interval)
  }, [])

  return (
    <Button variant="ghost" size="sm" onClick={onClick} className="relative">
      {unreadCount > 0 ? (
        <BellRing className="h-5 w-5" />
      ) : (
        <Bell className="h-5 w-5" />
      )}
      {unreadCount > 0 && (
        <Badge className="absolute -top-1 -right-1 h-5 w-5 flex items-center justify-center p-0 text-xs bg-red-500">
          {unreadCount > 99 ? '99+' : unreadCount}
        </Badge>
      )}
    </Button>
  )
}

export default NotificationCenter
