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
     * Escapa caracteres HTML para prevenir XSS
     * @param {*} value - Valor a ser escapado
     * @returns {string} Valor seguro para inserção em HTML
     */
    esc(value) {
        if (value === null || value === undefined) return '';
        const div = document.createElement('div');
        div.textContent = String(value);
        return div.innerHTML;
    }

    /**
     * Formata número com casas decimais, retornando 'N/A' se inválido
     * @param {*} value - Valor numérico
     * @param {number} decimals - Casas decimais
     * @returns {string} Número formatado ou 'N/A'
     */
    num(value, decimals = 1) {
        if (value === null || value === undefined || isNaN(value)) return 'N/A';
        return Number(value).toFixed(decimals);
    }

    /**
     * Configura o sistema de abas
     */
    setupTabs() {
        const tabButtons = document.querySelectorAll('.tab-button');
        const tabContents = document.querySelectorAll('.tab-content');

        tabButtons.forEach(button => {
            button.addEventListener('click', () => {
                tabButtons.forEach(btn => btn.classList.remove('active'));
                tabContents.forEach(content => content.classList.remove('active'));

                button.classList.add('active');

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

        this.updateOverview(data);
        this.updateHardware(data);
        this.updateNetwork(data);
        this.updateStorage(data);
        this.updateProcesses(data);
    }

    /**
     * Atualiza a seção de visão geral
     * @param {Object} data - Dados recebidos da API
     */
    updateOverview(data) {
        const overviewMetrics = document.getElementById('overview-metrics');
        overviewMetrics.innerHTML = '';

        // CPU
        if (data.hardware && data.hardware.cpu) {
            const cpuUsage = data.hardware.cpu.usage;
            const cpuVal = this.num(cpuUsage);
            const cpuWidth = (cpuUsage != null && !isNaN(cpuUsage)) ? cpuUsage : 0;
            overviewMetrics.innerHTML += `
                <div class="metric">
                    <h3>🔄 CPU</h3>
                    <div class="value">${cpuVal !== 'N/A' ? cpuVal + '%' : 'N/A'}</div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${cpuWidth}%"></div>
                    </div>
                </div>
            `;
        }

        // Memória
        if (data.hardware && data.hardware.memory) {
            const memory = data.hardware.memory;
            const memVal = this.num(memory.percent);
            const memWidth = (memory.percent != null && !isNaN(memory.percent)) ? memory.percent : 0;
            overviewMetrics.innerHTML += `
                <div class="metric">
                    <h3>💾 Memória</h3>
                    <div class="value">${memVal !== 'N/A' ? memVal + '%' : 'N/A'}</div>
                    <small>${this.esc(memory.used || '0')} de ${this.esc(memory.total || '0')}</small>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${memWidth}%"></div>
                    </div>
                </div>
            `;
        }

        // Armazenamento
        if (data.storage && data.storage.disk_usage) {
            const disk = data.storage.disk_usage;
            overviewMetrics.innerHTML += `
                <div class="metric">
                    <h3>💽 Armazenamento</h3>
                    <div class="value">${this.esc(disk.percent || '0%')}</div>
                    <small>${this.esc(disk.used || '0')} de ${this.esc(disk.total || '0')}</small>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${disk.percent_num || 0}%"></div>
                    </div>
                </div>
            `;
        }

        // Bateria (agora vem do android collector)
        const battery = (data.android && data.android.battery) || {};
        if (battery.percentage) {
            overviewMetrics.innerHTML += `
                <div class="metric">
                    <h3>🔋 Bateria</h3>
                    <div class="value">${this.esc(battery.percentage)}%</div>
                    <small>Status: ${this.esc(battery.status || 'Desconhecido')}</small>
                    <div class="battery-indicator">
                        <div class="battery-level" style="width: ${100 - battery.percentage}%"></div>
                    </div>
                </div>
            `;
        }

        // Informações do sistema
        const safeInfoContent = document.getElementById('safe-info-content');
        if (data.system) {
            let safeInfoHtml = '<ul>';

            if (data.system.uptime) {
                safeInfoHtml += `<li><strong>Uptime:</strong> ${this.esc(data.system.uptime)}</li>`;
            }
            if (data.system.hostname) {
                safeInfoHtml += `<li><strong>Hostname:</strong> ${this.esc(data.system.hostname)}</li>`;
            }
            if (data.system.python_version) {
                safeInfoHtml += `<li><strong>Python:</strong> ${this.esc(data.system.python_version)}</li>`;
            }
            if (data.system.system_time) {
                safeInfoHtml += `<li><strong>Hora do Sistema:</strong> ${this.esc(data.system.system_time)}</li>`;
            }
            if (data.android && data.android.device_info) {
                const device = data.android.device_info;
                safeInfoHtml += `<li><strong>Dispositivo:</strong> ${this.esc(device.manufacturer || '')} ${this.esc(device.model || 'Galaxy S10+')}</li>`;
                if (device.android_version) {
                    safeInfoHtml += `<li><strong>Android:</strong> ${this.esc(device.android_version)}</li>`;
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

        // CPU
        if (data.hardware.cpu) {
            const cpuContent = document.getElementById('cpu-content');
            const cpu = data.hardware.cpu;
            let cpuHtml = '';

            if (cpu.usage != null && !isNaN(cpu.usage)) {
                cpuHtml += `<div class="value">${this.num(cpu.usage)}%</div>`;
                cpuHtml += `<div class="progress-bar">
                    <div class="progress-fill" style="width: ${cpu.usage}%"></div>
                </div>`;
            }

            if (cpu.cores) {
                cpuHtml += `<p><strong>Cores:</strong> ${this.esc(cpu.cores.count || 'N/A')}</p>`;
                if (cpu.cores.model) {
                    cpuHtml += `<p><strong>Modelo:</strong> ${this.esc(cpu.cores.model)}</p>`;
                }
            }

            if (cpu.frequency != null && !isNaN(cpu.frequency)) {
                cpuHtml += `<p><strong>Frequência:</strong> ${this.num(cpu.frequency, 0)} MHz</p>`;
            }

            cpuContent.innerHTML = cpuHtml || 'Informações não disponíveis';
        }

        // Memória
        if (data.hardware.memory) {
            const memoryContent = document.getElementById('memory-content');
            const memory = data.hardware.memory;
            let memoryHtml = '';

            if (memory.percent != null && !isNaN(memory.percent)) {
                memoryHtml += `<div class="value">${this.num(memory.percent)}%</div>`;
                memoryHtml += `<div class="progress-bar">
                    <div class="progress-fill" style="width: ${memory.percent}%"></div>
                </div>`;
            }

            memoryHtml += `<p><strong>Total:</strong> ${this.esc(memory.total || 'N/A')}</p>`;
            memoryHtml += `<p><strong>Usado:</strong> ${this.esc(memory.used || 'N/A')}</p>`;

            memoryContent.innerHTML = memoryHtml || 'Informações não disponíveis';
        }

        // Bateria (do android collector)
        const battery = (data.android && data.android.battery) || {};
        const batteryContent = document.getElementById('battery-content');
        let batteryHtml = '';

        if (battery.percentage) {
            batteryHtml += `<div class="value">${this.esc(battery.percentage)}%</div>`;
            batteryHtml += `<div class="battery-indicator">
                <div class="battery-level" style="width: ${100 - battery.percentage}%"></div>
            </div>`;
        }
        if (battery.status) {
            batteryHtml += `<p><strong>Status:</strong> ${this.esc(battery.status)}</p>`;
        }
        if (battery.temperature != null && !isNaN(battery.temperature)) {
            batteryHtml += `<p><strong>Temperatura:</strong> ${this.num(battery.temperature)}°C</p>`;
        }
        if (battery.health) {
            batteryHtml += `<p><strong>Saúde:</strong> ${this.esc(battery.health)}</p>`;
        }

        batteryContent.innerHTML = batteryHtml || 'Informações não disponíveis';

        // Temperatura
        if (data.hardware.temperature) {
            const temperatureContent = document.getElementById('temperature-content');
            const temps = data.hardware.temperature;
            let tempHtml = '<ul>';

            for (const [sensor, temp] of Object.entries(temps)) {
                tempHtml += `<li><strong>${this.esc(sensor)}:</strong> ${this.esc(temp)}°C</li>`;
            }

            tempHtml += '</ul>';
            temperatureContent.innerHTML = tempHtml;
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

        // Informações básicas
        const networkContent = document.getElementById('network-content');
        let networkHtml = '';
        if (data.network.ip) {
            networkHtml += `<p><strong>IP:</strong> ${this.esc(data.network.ip)}</p>`;
        }
        networkContent.innerHTML = networkHtml || 'Informações não disponíveis';

        // Interfaces
        if (data.network.interfaces && data.network.interfaces.length > 0) {
            const interfacesContent = document.getElementById('interfaces-content');
            let interfacesHtml = '<table><tr><th>Interface</th><th>IP</th><th>RX</th><th>TX</th></tr>';

            data.network.interfaces.forEach(iface => {
                interfacesHtml += `<tr>
                    <td>${this.esc(iface.name)}</td>
                    <td>${this.esc(iface.ip || 'N/A')}</td>
                    <td>${this.esc(iface.rx_bytes || 'N/A')}</td>
                    <td>${this.esc(iface.tx_bytes || 'N/A')}</td>
                </tr>`;
            });

            interfacesHtml += '</table>';
            interfacesContent.innerHTML = interfacesHtml;
        } else {
            document.getElementById('interfaces-content').innerHTML = 'Nenhuma interface encontrada';
        }

        // Conexões
        if (data.network.connections) {
            const connectionsContent = document.getElementById('connections-content');
            const conn = data.network.connections;
            let connectionsHtml = '';

            connectionsHtml += `<p><strong>Total:</strong> ${this.esc(conn.count || 0)}</p>`;
            connectionsHtml += `<p><strong>TCP:</strong> ${this.esc(conn.tcp || 0)}</p>`;
            connectionsHtml += `<p><strong>UDP:</strong> ${this.esc(conn.udp || 0)}</p>`;
            connectionsHtml += `<p><strong>Listening:</strong> ${this.esc(conn.listening || 0)}</p>`;
            connectionsHtml += `<p><strong>Established:</strong> ${this.esc(conn.established || 0)}</p>`;

            connectionsContent.innerHTML = connectionsHtml;
        } else {
            document.getElementById('connections-content').innerHTML = 'Informações de conexões não disponíveis';
        }

        // WiFi
        if (data.network.wifi) {
            const wifiContent = document.getElementById('wifi-content');
            const wifi = data.network.wifi;
            let wifiHtml = '';

            if (wifi.ssid) {
                wifiHtml += `<p><strong>SSID:</strong> ${this.esc(wifi.ssid)}</p>`;
            }
            if (wifi.signal_strength) {
                wifiHtml += `<p><strong>Sinal:</strong> ${this.esc(wifi.signal_strength)} dBm</p>`;
            }
            if (wifi.frequency) {
                wifiHtml += `<p><strong>Frequência:</strong> ${this.esc(wifi.frequency)} MHz</p>`;
            }
            if (wifi.link_speed) {
                wifiHtml += `<p><strong>Velocidade:</strong> ${this.esc(wifi.link_speed)}</p>`;
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

        // Uso de disco
        if (data.storage.disk_usage) {
            const diskContent = document.getElementById('disk-content');
            const disk = data.storage.disk_usage;
            let diskHtml = '';

            diskHtml += `<div class="value">${this.esc(disk.percent || '0%')}</div>`;
            diskHtml += `<div class="progress-bar">
                <div class="progress-fill" style="width: ${disk.percent_num || 0}%"></div>
            </div>`;

            diskHtml += `<p><strong>Total:</strong> ${this.esc(disk.total || 'N/A')}</p>`;
            diskHtml += `<p><strong>Usado:</strong> ${this.esc(disk.used || 'N/A')}</p>`;
            diskHtml += `<p><strong>Livre:</strong> ${this.esc(disk.free || 'N/A')}</p>`;

            if (disk.mount_point) {
                diskHtml += `<p><strong>Ponto de Montagem:</strong> ${this.esc(disk.mount_point)}</p>`;
            }

            diskContent.innerHTML = diskHtml;
        }

        // Partições
        if (data.storage.partitions && data.storage.partitions.length > 0) {
            const partitionsContent = document.getElementById('partitions-content');
            let partitionsHtml = '<table><tr><th>Dispositivo</th><th>Ponto de Montagem</th><th>Total</th><th>Usado</th><th>Livre</th><th>Uso</th></tr>';

            data.storage.partitions.forEach(part => {
                partitionsHtml += `<tr>
                    <td>${this.esc(part.device)}</td>
                    <td>${this.esc(part.mount_point)}</td>
                    <td>${this.esc(part.total || 'N/A')}</td>
                    <td>${this.esc(part.used || 'N/A')}</td>
                    <td>${this.esc(part.free || 'N/A')}</td>
                    <td>${this.esc(part.percent || '0%')}</td>
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

        // Resumo
        if (data.process.summary) {
            const processSummaryContent = document.getElementById('process-summary-content');
            const summary = data.process.summary;
            let summaryHtml = '';

            summaryHtml += `<div class="value">${this.esc(summary.total || 0)}</div>`;
            summaryHtml += `<p><strong>Em Execução:</strong> ${this.esc(summary.running || 0)}</p>`;
            summaryHtml += `<p><strong>Dormindo:</strong> ${this.esc(summary.sleeping || 0)}</p>`;
            summaryHtml += `<p><strong>Parados:</strong> ${this.esc(summary.stopped || 0)}</p>`;
            summaryHtml += `<p><strong>Zumbis:</strong> ${this.esc(summary.zombie || 0)}</p>`;

            processSummaryContent.innerHTML = summaryHtml;
        }

        // Top processos
        if (data.process.top_processes && data.process.top_processes.length > 0) {
            const topProcessesContent = document.getElementById('top-processes-content');
            let processesHtml = '<table><tr><th>PID</th><th>Usuário</th><th>CPU%</th><th>MEM%</th><th>Comando</th></tr>';

            data.process.top_processes.forEach(proc => {
                processesHtml += `<tr>
                    <td>${this.esc(proc.pid)}</td>
                    <td>${this.esc(proc.user)}</td>
                    <td>${this.num(proc.cpu_percent)}%</td>
                    <td>${this.num(proc.mem_percent)}%</td>
                    <td>${this.esc(proc.command)}</td>
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
