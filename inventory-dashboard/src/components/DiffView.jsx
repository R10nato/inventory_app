import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { 
  GitCompare, ArrowLeft, ArrowRight, Plus, Minus, 
  Equal, Eye, EyeOff, Copy, Download
} from 'lucide-react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs.jsx'

const formatValue = (value) => {
  if (value === null || value === undefined) return 'null'
  if (typeof value === 'object') return JSON.stringify(value, null, 2)
  return String(value)
}

const DiffLine = ({ type, label, oldValue, newValue, path }) => {
  const [showDetails, setShowDetails] = useState(false)
  
  const getLineStyle = () => {
    switch (type) {
      case 'added': return 'bg-green-50 border-l-4 border-green-500'
      case 'removed': return 'bg-red-50 border-l-4 border-red-500'
      case 'modified': return 'bg-blue-50 border-l-4 border-blue-500'
      default: return 'bg-gray-50 border-l-4 border-gray-300'
    }
  }

  const getIcon = () => {
    switch (type) {
      case 'added': return <Plus className="h-4 w-4 text-green-600" />
      case 'removed': return <Minus className="h-4 w-4 text-red-600" />
      case 'modified': return <GitCompare className="h-4 w-4 text-blue-600" />
      default: return <Equal className="h-4 w-4 text-gray-600" />
    }
  }

  const getBadgeVariant = () => {
    switch (type) {
      case 'added': return 'bg-green-100 text-green-800'
      case 'removed': return 'bg-red-100 text-red-800'
      case 'modified': return 'bg-blue-100 text-blue-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  return (
    <div className={`p-3 rounded-lg ${getLineStyle()}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          {getIcon()}
          <div>
            <div className="font-medium text-sm">{label}</div>
            {path && <div className="text-xs text-muted-foreground">{path}</div>}
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <Badge className={`text-xs ${getBadgeVariant()}`}>
            {type === 'added' ? 'Adicionado' : 
             type === 'removed' ? 'Removido' : 
             type === 'modified' ? 'Modificado' : 'Igual'}
          </Badge>
          {(oldValue !== undefined || newValue !== undefined) && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowDetails(!showDetails)}
            >
              {showDetails ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </Button>
          )}
        </div>
      </div>
      
      {showDetails && (
        <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-4">
          {oldValue !== undefined && (
            <div className="space-y-2">
              <div className="text-xs font-medium text-red-700">Valor Anterior:</div>
              <pre className="text-xs bg-red-50 p-2 rounded border overflow-x-auto">
                {formatValue(oldValue)}
              </pre>
            </div>
          )}
          {newValue !== undefined && (
            <div className="space-y-2">
              <div className="text-xs font-medium text-green-700">Novo Valor:</div>
              <pre className="text-xs bg-green-50 p-2 rounded border overflow-x-auto">
                {formatValue(newValue)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

const SideBySideView = ({ oldData, newData, title }) => {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <Minus className="h-4 w-4 text-red-600" />
            Estado Anterior
          </CardTitle>
        </CardHeader>
        <CardContent>
          <pre className="text-xs bg-gray-50 p-3 rounded border overflow-auto max-h-96">
            {formatValue(oldData)}
          </pre>
        </CardContent>
      </Card>
      
      <Card>
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <Plus className="h-4 w-4 text-green-600" />
            Estado Atual
          </CardTitle>
        </CardHeader>
        <CardContent>
          <pre className="text-xs bg-gray-50 p-3 rounded border overflow-auto max-h-96">
            {formatValue(newData)}
          </pre>
        </CardContent>
      </Card>
    </div>
  )
}

const DiffView = ({ changeData, onClose }) => {
  const [parsedChanges, setParsedChanges] = useState(null)
  const [viewMode, setViewMode] = useState('unified') // 'unified' or 'sidebyside'

  useEffect(() => {
    if (changeData && changeData.change_description) {
      try {
        const parsed = JSON.parse(changeData.change_description)
        setParsedChanges(parsed)
      } catch (error) {
        console.error('Error parsing change data:', error)
        setParsedChanges(null)
      }
    }
  }, [changeData])

  const generateDiffLines = (changes) => {
    const lines = []
    
    if (!changes || typeof changes !== 'object') return lines

    Object.entries(changes).forEach(([key, value]) => {
      if (typeof value === 'object' && value !== null) {
        if (value.old !== undefined && value.new !== undefined) {
          // Valor modificado
          lines.push({
            type: 'modified',
            label: key,
            oldValue: value.old,
            newValue: value.new,
            path: key
          })
        } else if (value.old !== undefined) {
          // Valor removido
          lines.push({
            type: 'removed',
            label: key,
            oldValue: value.old,
            path: key
          })
        } else if (value.new !== undefined) {
          // Valor adicionado
          lines.push({
            type: 'added',
            label: key,
            newValue: value.new,
            path: key
          })
        }
      } else {
        // Valor simples
        lines.push({
          type: 'modified',
          label: key,
          newValue: value,
          path: key
        })
      }
    })

    return lines
  }

  const diffLines = parsedChanges ? generateDiffLines(parsedChanges) : []

  const handleCopyDiff = () => {
    const diffText = diffLines.map(line => {
      const prefix = line.type === 'added' ? '+' : line.type === 'removed' ? '-' : '~'
      return `${prefix} ${line.label}: ${formatValue(line.newValue || line.oldValue)}`
    }).join('\n')
    
    navigator.clipboard.writeText(diffText)
  }

  const handleDownloadDiff = () => {
    const diffData = {
      timestamp: changeData?.timestamp,
      component: changeData?.component,
      change_type: changeData?.change_type,
      changes: parsedChanges
    }
    
    const blob = new Blob([JSON.stringify(diffData, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `diff_${changeData?.id || Date.now()}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  if (!changeData) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center h-64">
          <div className="text-center">
            <GitCompare className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <p className="text-muted-foreground">Nenhuma alteração selecionada</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          {onClose && (
            <Button variant="outline" size="sm" onClick={onClose}>
              <ArrowLeft className="h-4 w-4 mr-2" />
              Voltar
            </Button>
          )}
          <div>
            <h2 className="text-xl font-bold flex items-center gap-2">
              <GitCompare className="h-5 w-5" />
              Visualização de Diferenças
            </h2>
            <p className="text-sm text-muted-foreground">
              {changeData.component} • {changeData.change_type} • 
              {new Date(changeData.timestamp).toLocaleString('pt-BR')}
            </p>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          <Button variant="outline" size="sm" onClick={handleCopyDiff}>
            <Copy className="h-4 w-4 mr-2" />
            Copiar
          </Button>
          <Button variant="outline" size="sm" onClick={handleDownloadDiff}>
            <Download className="h-4 w-4 mr-2" />
            Download
          </Button>
        </div>
      </div>

      {/* Content */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Alterações Detectadas</CardTitle>
              <CardDescription>
                {diffLines.length} alteração(ões) encontrada(s)
              </CardDescription>
            </div>
            <Tabs value={viewMode} onValueChange={setViewMode}>
              <TabsList>
                <TabsTrigger value="unified">Unificado</TabsTrigger>
                <TabsTrigger value="sidebyside">Lado a Lado</TabsTrigger>
              </TabsList>
            </Tabs>
          </div>
        </CardHeader>
        
        <CardContent>
          <Tabs value={viewMode} className="w-full">
            <TabsContent value="unified" className="space-y-3">
              {diffLines.length > 0 ? (
                diffLines.map((line, index) => (
                  <DiffLine
                    key={index}
                    type={line.type}
                    label={line.label}
                    oldValue={line.oldValue}
                    newValue={line.newValue}
                    path={line.path}
                  />
                ))
              ) : (
                <div className="text-center py-8">
                  <GitCompare className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                  <p className="text-muted-foreground">
                    Nenhuma diferença estruturada encontrada
                  </p>
                  {changeData.change_description && (
                    <div className="mt-4 p-3 bg-gray-50 rounded text-sm text-left">
                      <strong>Descrição bruta:</strong>
                      <pre className="mt-2 whitespace-pre-wrap">
                        {changeData.change_description}
                      </pre>
                    </div>
                  )}
                </div>
              )}
            </TabsContent>
            
            <TabsContent value="sidebyside">
              {parsedChanges ? (
                <div className="space-y-4">
                  {Object.entries(parsedChanges).map(([key, value]) => (
                    <div key={key}>
                      <h4 className="font-medium mb-2">{key}</h4>
                      <SideBySideView
                        oldData={value.old}
                        newData={value.new}
                        title={key}
                      />
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <p className="text-muted-foreground">
                    Visualização lado a lado não disponível para este tipo de alteração
                  </p>
                </div>
              )}
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      {/* Summary */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Resumo da Alteração</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <strong>Componente:</strong> {changeData.component || 'N/A'}
            </div>
            <div>
              <strong>Tipo:</strong> {changeData.change_type || 'N/A'}
            </div>
            <div>
              <strong>Data/Hora:</strong> {new Date(changeData.timestamp).toLocaleString('pt-BR')}
            </div>
            <div>
              <strong>Usuário:</strong> {changeData.user || 'Sistema'}
            </div>
          </div>
          
          {changeData.details_before && (
            <div className="mt-4">
              <strong>Estado Anterior:</strong>
              <pre className="mt-1 p-2 bg-gray-50 rounded text-xs overflow-auto">
                {changeData.details_before}
              </pre>
            </div>
          )}
          
          {changeData.details_after && (
            <div className="mt-4">
              <strong>Estado Posterior:</strong>
              <pre className="mt-1 p-2 bg-gray-50 rounded text-xs overflow-auto">
                {changeData.details_after}
              </pre>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

export default DiffView
