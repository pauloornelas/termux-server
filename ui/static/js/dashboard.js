/**
 * Dashboard principal para o S10+ Server
 * 
 * Este script gerencia a interface do usuário do dashboard,
 * incluindo a exibição de dados, atualização automática e
 * interação com as abas.
 */

class Dashboard {
    /**
     * Inicializa o dashboard
     */
    constructor() {
        // Configurações
        this.updateInterval = 5000; // 5 segundos
        this.charts = {};
        this.lastData = null;
        
        // Inicializa os gráficos
        this.initCharts();
        
        // Configura abas
        this.setupTabs();
        
        // Configura atualização automática
        this.startAutoRefresh();
        
        // Configura botão de atualização manual
        document.getElementById('refresh').addEventListener('click', () => {
            this.fetchData();
        });
        
        // Carrega dados iniciais
        this.fetchData();
    }
    
    /**
     * Configura o sistema de abas
     */
    setupTabs() {
        const tabButtons = document.querySelectorAll('.tab-button');
        const tabContents = document.querySelectorAll('.tab-content');
        
        tabButtons.forEach(button => {
            button.addEventListener('click', () => {
                // Remove classe ativa de todos os botões e conteúdos
                tabButtons.forEach(btn => btn.classList.remove('active'));
                tabContents.forEach(content => content.classList.remove('active'));
                
                // Adiciona classe ativa ao botão clicado
                button.classList.add('active');
                
                // Ativa o conteúdo correspondente
                const tabId = button.getAttribute('data-tab');
                document.getElementById(`tab-${tabId}`).classList.add('active');
            });
        });
    }
    
    /**
     * Inicializa os gráficos do dashboard
     */
    initCharts() {
        // Implementação de gráficos será adicionada posteriormente
        // Usando biblioteca de gráficos como Chart.js
    }
    
    /**
     * Inicia a atualização automática dos dados
     */
    startAutoRefresh() {
        setInterval(() => {
            this.fetchData();
        }, this.updateInterval);
    }
    
    /**
     * Busca dados atualizados da API
     */
    async fetchData() {
        try {
            const response = await fetch('/api/status');
            if (!response.ok) {
                throw new Error(`Erro HTTP: ${response.status}`);
            }
            
            const data = await response.json();
            this.lastData = data;
            
            // Atualiza a interface
            this.updateUI(data);
            
            // Atualiza o timestamp de última atualização
            document.getElementById('last-updated').textContent = 
                new Date().toLocaleTimeString();
                
            // Esconde mensagens de erro
            document.getElementById('error').style.display = 'none';
        } catch (error) {
            console.error('Erro ao buscar dados:', error);
            document.getElementById('error').style.display = 'block';
            document.getElementById('error-message').textContent = error.message;
        }
    }
    
    /**
     * Atualiza a interface com os novos dados
     * @param {Object} data - Dados recebidos da API
     */
    updateUI(data) {
        // Atualiza informações de IP
        if (data.network && data.network.ip) {
            document.getElementById('server-ip').textContent = `IP: ${data.network.ip}`;
            document.getElementById('ssh-ip').textContent = data.network.ip;
        }
        
        // Atualiza visão geral
        this.updateOverview(data);
        
        // Atualiza informações de hardware
        this.updateHardware(data);
        
        // Atualiza informações de rede
        this.updateNetwork(data);
        
        // Atualiza informações de armazenamento
        this.updateStorage(data);
        
        // Atualiza informações de processos
        this.updateProcesses(data);
    }
    
    /**
     * Atualiza a seção de visão geral
     * @param {Object} data - Dados recebidos da API
     */
    updateOverview(data) {
        // Atualiza métricas de visão geral
        const overviewMetrics = document.getElementById('overview-metrics');
        
        // Limpa conteúdo anterior
        overviewMetrics.innerHTML = '';
        
        // Adiciona métrica de CPU
        if (data.hardware && data.hardware.cpu) {
            const cpuUsage = data.hardware.cpu.usage;
            overviewMetrics.innerHTML += `
                <div class="metric">
                    <h3>🔄 CPU</h3>
                    <div class="value">${cpuUsage !== null ? cpuUsage.toFixed(1) + '%' : 'N/A'}</div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${cpuUsage || 0}%"></div>
                    </div>
                </div>
            `;
        }
        
        // Adiciona métrica de memória
        if (data.hardware && data.hardware.memory) {
            const memory = data.hardware.memory;
            overviewMetrics.innerHTML += `
                <div class="metric">
                    <h3>💾 Memória</h3>
                    <div class="value">${memory.percent ? memory.percent.toFixed(1) + '%' : 'N/A'}</div>
                    <small>${memory.used || '0'} de ${memory.total || '0'}</small>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${memory.percent || 0}%"></div>
                    </div>
                </div>
            `;
        }
        
        // Adiciona métrica de armazenamento
        if (data.storage && data.storage.disk_usage) {
            const disk = data.storage.disk_usage;
            overviewMetrics.innerHTML += `
                <div class="metric">
                    <h3>💽 Armazenamento</h3>
                    <div class="value">${disk.percent || '0%'}</div>
                    <small>${disk.used || '0'} de ${disk.total || '0'}</small>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${disk.percent_num || 0}%"></div>
                    </div>
                </div>
            `;
        }
        
        // Adiciona métrica de bateria
        if (data.hardware && data.hardware.battery && data.hardware.battery.percentage) {
            const battery = data.hardware.battery;
            overviewMetrics.innerHTML += `
                <div class="metric">
                    <h3>🔋 Bateria</h3>
                    <div class="value">${battery.percentage}%</div>
                    <small>Status: ${battery.status || 'Desconhecido'}</small>
                    <div class="battery-indicator">
                        <div class="battery-level" style="width: ${100 - battery.percentage}%"></div>
                    </div>
                </div>
            `;
        }
        
        // Atualiza informações seguras do sistema
        const safeInfoContent = document.getElementById('safe-info-content');
        if (data.system) {
            let safeInfoHtml = '<ul>';
            
            if (data.system.uptime) {
                safeInfoHtml += `<li><strong>Uptime:</strong> ${data.system.uptime}</li>`;
            }
            
            if (data.system.hostname) {
                safeInfoHtml += `<li><strong>Hostname:</strong> ${data.system.hostname}</li>`;
            }
            
            if (data.system.python_version) {
                safeInfoHtml += `<li><strong>Python:</strong> ${data.system.python_version}</li>`;
            }
            
            if (data.system.system_time) {
                safeInfoHtml += `<li><strong>Hora do Sistema:</strong> ${data.system.system_time}</li>`;
            }
            
            if (data.android && data.android.device_info) {
                const device = data.android.device_info;
                safeInfoHtml += `<li><strong>Dispositivo:</strong> ${device.manufacturer || ''} ${device.model || 'Galaxy S10+'}</li>`;
                
                if (device.android_version) {
                    safeInfoHtml += `<li><strong>Android:</strong> ${device.android_version}</li>`;
                }
            }
            
            safeInfoHtml += '</ul>';
            safeInfoContent.innerHTML = safeInfoHtml;
        }
    }
    
    /**
     * Atualiza a seção de hardware
     * @param {Object} data - Dados recebidos da API
     */
    updateHardware(data) {
        if (!data.hardware) return;
        
        // Atualiza informações de CPU
        if (data.hardware.cpu) {
            const cpuContent = document.getElementById('cpu-content');
            const cpu = data.hardware.cpu;
            
            let cpuHtml = '';
            
            if (cpu.usage !== null) {
                cpuHtml += `<div class="value">${cpu.usage.toFixed(1)}%</div>`;
                cpuHtml += `<div class="progress-bar">
                    <div class="progress-fill" style="width: ${cpu.usage}%"></div>
                </div>`;
            }
            
            if (cpu.cores) {
                cpuHtml += `<p><strong>Cores:</strong> ${cpu.cores.count || 'N/A'}</p>`;
                if (cpu.cores.model) {
                    cpuHtml += `<p><strong>Modelo:</strong> ${cpu.cores.model}</p>`;
                }
            }
            
            if (cpu.frequency) {
                cpuHtml += `<p><strong>Frequência:</strong> ${cpu.frequency.toFixed(0)} MHz</p>`;
            }
            
            cpuContent.innerHTML = cpuHtml || 'Informações não disponíveis';
        }
        
        // Atualiza informações de memória
        if (data.hardware.memory) {
            const memoryContent = document.getElementById('memory-content');
            const memory = data.hardware.memory;
            
            let memoryHtml = '';
            
            if (memory.percent) {
                memoryHtml += `<div class="value">${memory.percent.toFixed(1)}%</div>`;
                memoryHtml += `<div class="progress-bar">
                    <div class="progress-fill" style="width: ${memory.percent}%"></div>
                </div>`;
            }
            
            memoryHtml += `<p><strong>Total:</strong> ${memory.total || 'N/A'}</p>`;
            memoryHtml += `<p><strong>Usado:</strong> ${memory.used || 'N/A'}</p>`;
            
            memoryContent.innerHTML = memoryHtml || 'Informações não disponíveis';
        }
        
        // Atualiza informações de bateria
        if (data.hardware.battery) {
            const batteryContent = document.getElementById('battery-content');
            const battery = data.hardware.battery;
            
            let batteryHtml = '';
            
            if (battery.percentage) {
                batteryHtml += `<div class="value">${battery.percentage}%</div>`;
                batteryHtml += `<div class="battery-indicator">
                    <div class="battery-level" style="width: ${100 - battery.percentage}%"></div>
                </div>`;
            }
            
            if (battery.status) {
                batteryHtml += `<p><strong>Status:</strong> ${battery.status}</p>`;
            }
            
            if (battery.temperature) {
                batteryHtml += `<p><strong>Temperatura:</strong> ${battery.temperature.toFixed(1)}°C</p>`;
            }
            
            if (battery.health) {
                batteryHtml += `<p><strong>Saúde:</strong> ${battery.health}</p>`;
            }
            
            batteryContent.innerHTML = batteryHtml || 'Informações não disponíveis';
        }
        
        // Atualiza informações de temperatura
        if (data.hardware.temperature) {
            const temperatureContent = document.getElementById('temperature-content');
            const temps = data.hardware.temperature;
            
            let tempHtml = '<ul>';
            
            for (const [sensor, temp] of Object.entries(temps)) {
                tempHtml += `<li><strong>${sensor}:</strong> ${temp}°C</li>`;
            }
            
            tempHtml += '</ul>';
            
            temperatureContent.innerHTML = tempHtml || 'Informações não disponíveis';
        } else {
            document.getElementById('temperature-content').innerHTML = 'Informações de temperatura não disponíveis';
        }
    }
    
    /**
     * Atualiza a seção de rede
     * @param {Object} data - Dados recebidos da API
     */
    updateNetwork(data) {
        if (!data.network) return;
        
        // Atualiza informações básicas de rede
        const networkContent = document.getElementById('network-content');
        let networkHtml = '';
        
        if (data.network.ip) {
            networkHtml += `<p><strong>IP:</strong> ${data.network.ip}</p>`;
        }
        
        networkContent.innerHTML = networkHtml || 'Informações não disponíveis';
        
        // Atualiza informações de interfaces
        if (data.network.interfaces && data.network.interfaces.length > 0) {
            const interfacesContent = document.getElementById('interfaces-content');
            let interfacesHtml = '<table><tr><th>Interface</th><th>IP</th><th>RX</th><th>TX</th></tr>';
            
            data.network.interfaces.forEach(iface => {
                interfacesHtml += `<tr>
                    <td>${iface.name}</td>
                    <td>${iface.ip || 'N/A'}</td>
                    <td>${iface.rx_bytes || 'N/A'}</td>
                    <td>${iface.tx_bytes || 'N/A'}</td>
                </tr>`;
            });
            
            interfacesHtml += '</table>';
            interfacesContent.innerHTML = interfacesHtml;
        } else {
            document.getElementById('interfaces-content').innerHTML = 'Nenhuma interface encontrada';
        }
        
        // Atualiza informações de conexões
        if (data.network.connections) {
            const connectionsContent = document.getElementById('connections-content');
            const conn = data.network.connections;
            
            let connectionsHtml = '';
            
            connectionsHtml += `<p><strong>Total:</strong> ${conn.count || 0}</p>`;
            connectionsHtml += `<p><strong>TCP:</strong> ${conn.tcp || 0}</p>`;
            connectionsHtml += `<p><strong>UDP:</strong> ${conn.udp || 0}</p>`;
            connectionsHtml += `<p><strong>Listening:</strong> ${conn.listening || 0}</p>`;
            connectionsHtml += `<p><strong>Established:</strong> ${conn.established || 0}</p>`;
            
            connectionsContent.innerHTML = connectionsHtml;
        } else {
            document.getElementById('connections-content').innerHTML = 'Informações de conexões não disponíveis';
        }
        
        // Atualiza informações de WiFi
        if (data.network.wifi) {
            const wifiContent = document.getElementById('wifi-content');
            const wifi = data.network.wifi;
            
            let wifiHtml = '';
            
            if (wifi.ssid) {
                wifiHtml += `<p><strong>SSID:</strong> ${wifi.ssid}</p>`;
            }
            
            if (wifi.signal_strength) {
                wifiHtml += `<p><strong>Sinal:</strong> ${wifi.signal_strength} dBm</p>`;
            }
            
            if (wifi.frequency) {
                wifiHtml += `<p><strong>Frequência:</strong> ${wifi.frequency} MHz</p>`;
            }
            
            if (wifi.link_speed) {
                wifiHtml += `<p><strong>Velocidade:</strong> ${wifi.link_speed}</p>`;
            }
            
            wifiContent.innerHTML = wifiHtml || 'Informações não disponíveis';
        } else {
            document.getElementById('wifi-content').innerHTML = 'Informações de WiFi não disponíveis';
        }
    }
    
    /**
     * Atualiza a seção de armazenamento
     * @param {Object} data - Dados recebidos da API
     */
    updateStorage(data) {
        if (!data.storage) return;
        
        // Atualiza informações de uso de disco
        if (data.storage.disk_usage) {
            const diskContent = document.getElementById('disk-content');
            const disk = data.storage.disk_usage;
            
            let diskHtml = '';
            
            diskHtml += `<div class="value">${disk.percent || '0%'}</div>`;
            diskHtml += `<div class="progress-bar">
                <div class="progress-fill" style="width: ${disk.percent_num || 0}%"></div>
            </div>`;
            
            diskHtml += `<p><strong>Total:</strong> ${disk.total || 'N/A'}</p>`;
            diskHtml += `<p><strong>Usado:</strong> ${disk.used || 'N/A'}</p>`;
            diskHtml += `<p><strong>Livre:</strong> ${disk.free || 'N/A'}</p>`;
            
            if (disk.mount_point) {
                diskHtml += `<p><strong>Ponto de Montagem:</strong> ${disk.mount_point}</p>`;
            }
            
            diskContent.innerHTML = diskHtml;
        }
        
        // Atualiza informações de partições
        if (data.storage.partitions && data.storage.partitions.length > 0) {
            const partitionsContent = document.getElementById('partitions-content');
            let partitionsHtml = '<table><tr><th>Dispositivo</th><th>Ponto de Montagem</th><th>Total</th><th>Usado</th><th>Livre</th><th>Uso</th></tr>';
            
            data.storage.partitions.forEach(part => {
                partitionsHtml += `<tr>
                    <td>${part.device}</td>
                    <td>${part.mount_point}</td>
                    <td>${part.total || 'N/A'}</td>
                    <td>${part.used || 'N/A'}</td>
                    <td>${part.free || 'N/A'}</td>
                    <td>${part.percent || '0%'}</td>
                </tr>`;
            });
            
            partitionsHtml += '</table>';
            partitionsContent.innerHTML = partitionsHtml;
        } else {
            document.getElementById('partitions-content').innerHTML = 'Nenhuma partição encontrada';
        }
    }
    
    /**
     * Atualiza a seção de processos
     * @param {Object} data - Dados recebidos da API
     */
    updateProcesses(data) {
        if (!data.process) return;
        
        // Atualiza resumo de processos
        if (data.process.summary) {
            const processSummaryContent = document.getElementById('process-summary-content');
            const summary = data.process.summary;
            
            let summaryHtml = '';
            
            summaryHtml += `<div class="value">${summary.total || 0}</div>`;
            summaryHtml += `<p><strong>Em Execução:</strong> ${summary.running || 0}</p>`;
            summaryHtml += `<p><strong>Dormindo:</strong> ${summary.sleeping || 0}</p>`;
            summaryHtml += `<p><strong>Parados:</strong> ${summary.stopped || 0}</p>`;
            summaryHtml += `<p><strong>Zumbis:</strong> ${summary.zombie || 0}</p>`;
            
            processSummaryContent.innerHTML = summaryHtml;
        }
        
        // Atualiza lista de top processos
        if (data.process.top_processes && data.process.top_processes.length > 0) {
            const topProcessesContent = document.getElementById('top-processes-content');
            let processesHtml = '<table><tr><th>PID</th><th>Usuário</th><th>CPU%</th><th>MEM%</th><th>Comando</th></tr>';
            
            data.process.top_processes.forEach(proc => {
                processesHtml += `<tr>
                    <td>${proc.pid}</td>
                    <td>${proc.user}</td>
                    <td>${proc.cpu_percent.toFixed(1)}%</td>
                    <td>${proc.mem_percent.toFixed(1)}%</td>
                    <td>${proc.command}</td>
                </tr>`;
            });
            
            processesHtml += '</table>';
            topProcessesContent.innerHTML = processesHtml;
        } else {
            document.getElementById('top-processes-content').innerHTML = 'Nenhum processo encontrado';
        }
    }
}

// Inicializa o dashboard quando a página carregar
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new Dashboard();
});
