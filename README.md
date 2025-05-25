# README - Dashboard S10+ para Termux

## Visão Geral

Este é um dashboard web modular e extensível para monitoramento de recursos do sistema em um Galaxy S10+ rodando Termux. O dashboard foi completamente refatorado seguindo princípios de clean code e design modular, permitindo fácil manutenção e extensão.

## Características Principais

- **Arquitetura Modular**: Código organizado em módulos com responsabilidades bem definidas
- **Coletores Especializados**: Módulos dedicados para coleta de diferentes tipos de informações
- **Interface Responsiva**: Design adaptável para diferentes tamanhos de tela
- **Visualização em Tempo Real**: Atualização automática de dados e gráficos
- **Histórico de Métricas**: Armazenamento de dados históricos para análise de tendências
- **Tratamento de Erros Robusto**: Sistema consistente de tratamento e log de erros
- **Configuração Centralizada**: Parâmetros configuráveis em um único local

## Estrutura do Projeto

```
www/
├── config/               # Configurações centralizadas
├── core/                 # Núcleo do servidor e utilitários
├── collectors/           # Coletores de dados do sistema
├── api/                  # Rotas e manipuladores da API
├── storage/              # Armazenamento de dados históricos
├── ui/                   # Interface do usuário
│   ├── static/           # Arquivos estáticos (CSS, JS, imagens)
│   └── templates/        # Templates HTML
├── tools/                # Ferramentas auxiliares
├── logs/                 # Diretório para logs
├── dashboard.py          # Ponto de entrada principal
└── README.md             # Esta documentação
```

## Requisitos

- Termux instalado no Galaxy S10+
- Python 3.6 ou superior
- Pacotes: `psutil` (opcional, para métricas avançadas)
- Termux-API (opcional, para acesso a sensores e recursos do Android)

## Instalação

1. Copie todos os arquivos para o diretório `~/www/` no seu Termux
2. Certifique-se de que o arquivo `dashboard.py` tem permissão de execução:
   ```
   chmod +x ~/www/dashboard.py
   ```
3. Atualize o script de inicialização em `~/.bashrc` para apontar para o novo dashboard:
   ```bash
   # Verificar se o dashboard já está rodando, se não, iniciar
   if ! pgrep -f "python.*dashboard.py" > /dev/null; then
     echo "Iniciando o dashboard..."
     cd ~/www && nohup python dashboard.py > ~/dashboard.log 2>&1 &
     echo "Dashboard iniciado com PID: $!"
   else
     echo "Dashboard já está em execução."
   fi
   ```

## Uso

1. Acesse o dashboard através do navegador em `http://[IP_DO_DISPOSITIVO]:8080`
2. A interface mostrará informações sobre:
   - CPU, memória e bateria
   - Rede e conexões
   - Armazenamento e partições
   - Processos em execução
   - Informações do sistema Android

## Configuração

As configurações do dashboard podem ser ajustadas no arquivo `config/settings.py`:

- `SERVER_PORT`: Porta do servidor HTTP (padrão: 8080)
- `DEBUG`: Modo de depuração (padrão: True)
- `COLLECTION_INTERVAL`: Intervalo de coleta de dados em segundos (padrão: 5)
- `HISTORY_SIZE`: Número de pontos de dados históricos a manter (padrão: 60)

## Extensão

Para adicionar novos coletores de dados:

1. Crie uma nova classe no diretório `collectors/` que herde de `BaseCollector`
2. Implemente o método `_collect_data()` para coletar as informações desejadas
3. Registre o novo coletor em `api/routes.py`

## Limitações Conhecidas

- Algumas funcionalidades dependem do Termux-API e podem não funcionar se não estiver instalado
- O acesso a informações detalhadas de hardware pode ser limitado sem permissões root
- O monitoramento de GPU é limitado no ambiente Termux
- O histórico de dados é mantido apenas em memória e será perdido ao reiniciar o servidor

## Solução de Problemas

- Verifique os logs em `~/dashboard.log` para mensagens de erro detalhadas
- Ative o modo DEBUG em `config/settings.py` para logs mais verbosos
- Reinicie o dashboard com `pkill -f "python.*dashboard.py" && cd ~/www && python dashboard.py`

## Melhorias Futuras

- Implementação de gráficos interativos com Chart.js
- Persistência de dados históricos em SQLite
- Autenticação básica para acesso ao dashboard
- Notificações para eventos críticos
- Temas adicionais para a interface

## Licença

Este software é fornecido "como está", sem garantias expressas ou implícitas.
