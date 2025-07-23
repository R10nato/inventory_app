# Frontend Dashboard - Documentação Completa

## Visão Geral

O frontend do Inventory Dashboard foi completamente redesenhado para exibir de forma bonita e organizada todas as informações coletadas pelo agente de inventário. A aplicação utiliza React com Tailwind CSS e componentes shadcn/ui para uma interface moderna e responsiva.

## Tecnologias Utilizadas

- **React 18**: Framework principal
- **Vite**: Build tool e servidor de desenvolvimento
- **Tailwind CSS**: Framework de CSS utilitário
- **shadcn/ui**: Biblioteca de componentes UI
- **Lucide React**: Ícones
- **Recharts**: Gráficos e visualizações

## Estrutura da Aplicação

### Componentes Principais

1. **App.jsx**: Componente principal com roteamento e gerenciamento de estado
2. **DashboardOverview.jsx**: Visão geral com estatísticas e gráficos
3. **DeviceGrid.jsx**: Lista de dispositivos com filtros
4. **DeviceDetail.jsx**: Detalhes completos de um dispositivo

### Arquitetura de Dados

A aplicação está preparada para consumir dados da API backend no formato definido pelo schema atualizado, incluindo:

- Informações básicas do dispositivo
- Detalhes completos de hardware
- Histórico de mudanças
- Temperaturas e monitoramento
- Software instalado
- Interfaces de rede

## Funcionalidades Implementadas

### 1. Dashboard Overview (Visão Geral)

**Estatísticas Principais:**
- Total de dispositivos
- Dispositivos online/offline
- Alertas ativos

**Visualizações:**
- Gráfico de pizza: Distribuição por tipo de dispositivo
- Gráfico de barras: Uso de recursos (RAM e Disco)

**Seções Informativas:**
- Dispositivos recentes
- Alertas e problemas
- Navegação rápida

### 2. Lista de Dispositivos (DeviceGrid)

**Filtros e Busca:**
- Campo de busca por nome, IP ou OS
- Filtro por status (online/offline)
- Filtro por tipo de dispositivo
- Contador de resultados

**Cards de Dispositivos:**
- Informações básicas (nome, IP, OS, status)
- Preview de hardware (CPU, RAM, Disco, Rede)
- Barras de progresso para uso de recursos
- Indicação de última visualização
- Botão para ver detalhes

### 3. Detalhes do Dispositivo (DeviceDetail)

**Navegação por Abas:**

#### Aba Resumo
- Informações básicas do dispositivo
- Dados do processador
- Informações de memória RAM com uso
- Temperaturas com código de cores

#### Aba Hardware
- Detalhes de armazenamento com uso
- Informações da placa de vídeo
- Dados da placa-mãe
- Módulos de RAM individuais

#### Aba Software
- Lista de software instalado
- Dispositivos USB conectados
- Informações de versão e fabricante

#### Aba Rede
- Interfaces de rede disponíveis
- Endereços MAC e IP
- Tipo de conexão

#### Aba Histórico
- Registro de mudanças de hardware
- Comparação antes/depois
- Timestamp e usuário responsável

## Design e UX

### Sistema de Cores

- **Verde**: Status online, temperaturas normais
- **Azul**: Temperaturas baixas, elementos primários
- **Amarelo**: Alertas, uso médio de recursos
- **Vermelho**: Status offline, temperaturas altas, uso crítico
- **Cinza**: Elementos secundários, dados não disponíveis

### Responsividade

- Layout adaptativo para desktop, tablet e mobile
- Grid responsivo para cards de dispositivos
- Navegação otimizada para touch

### Indicadores Visuais

- Barras de progresso para uso de recursos
- Badges coloridos para status
- Ícones contextuais para cada tipo de informação
- Código de cores para temperaturas

## Integração com Backend

### Endpoints Esperados

```javascript
// Listar todos os dispositivos
GET /devices/

// Obter detalhes de um dispositivo
GET /devices/{device_id}

// Dados esperados no formato do schema atualizado
```

### Tratamento de Dados

- Fallback para dados não disponíveis
- Formatação automática de datas e valores
- Cálculo de percentuais de uso
- Validação de tipos de dados

## Configuração e Execução

### Pré-requisitos

- Node.js 18+
- pnpm (recomendado) ou npm

### Instalação

```bash
cd inventory-dashboard
pnpm install
```

### Desenvolvimento

```bash
pnpm run dev
```

### Build para Produção

```bash
pnpm run build
```

### Deploy

```bash
pnpm run preview
```

## Configurações Importantes

### vite.config.js

```javascript
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    strictPort: true
  }
})
```

### Estrutura de Pastas

```
src/
├── components/
│   ├── ui/              # Componentes shadcn/ui
│   ├── DashboardOverview.jsx
│   ├── DeviceGrid.jsx
│   └── DeviceDetail.jsx
├── assets/              # Recursos estáticos
├── App.jsx              # Componente principal
├── App.css              # Estilos globais
└── main.jsx             # Ponto de entrada
```

## Melhorias Futuras

### Funcionalidades Planejadas

1. **Edição de Dispositivos**: Interface para editar informações manualmente
2. **Exportação de Relatórios**: PDF e Excel
3. **Notificações em Tempo Real**: WebSocket para atualizações
4. **Filtros Avançados**: Mais opções de filtragem
5. **Dashboards Personalizados**: Widgets configuráveis
6. **Modo Escuro**: Tema alternativo
7. **Gráficos Históricos**: Tendências ao longo do tempo

### Otimizações Técnicas

1. **Lazy Loading**: Carregamento sob demanda
2. **Cache de Dados**: Reduzir chamadas à API
3. **Paginação**: Para grandes volumes de dados
4. **Busca Avançada**: Filtros mais sofisticados
5. **PWA**: Funcionalidades offline

## Troubleshooting

### Problemas Comuns

1. **Erro de CORS**: Configurar backend para aceitar requisições do frontend
2. **Dados não carregam**: Verificar URL da API e conectividade
3. **Layout quebrado**: Verificar se Tailwind CSS está carregando
4. **Componentes não renderizam**: Verificar importações dos componentes UI

### Logs e Debug

- Usar console do navegador para debug
- Verificar Network tab para chamadas de API
- Usar React DevTools para inspeção de componentes

## Conclusão

O frontend foi desenvolvido com foco na usabilidade e apresentação clara das informações de inventário. A arquitetura modular permite fácil manutenção e extensão das funcionalidades. O design responsivo garante uma boa experiência em diferentes dispositivos.

A integração com o backend atualizado permite exibir todas as informações coletadas pelo agente de forma organizada e visualmente atrativa, facilitando o gerenciamento e monitoramento do inventário de hardware.

