# controle_ociosidade
 Este projeto consiste em um ecossistema completo para Gestão de Produtividade e Monitoramento de Pausas, composto por um agente cliente (Python) e um servidor centralizador (FastAPI). O sistema automatiza a identificação de inatividade, obriga a justificativa pelo colaborador e gera indicadores visuais para a gestão.

# PC Activity & Idle Monitor (SYSFOREST Ecosystem)

Este projeto é um ecossistema completo para monitoramento de produtividade e gestão de pausas operacionais. Ele detecta automaticamente a inatividade em estações de trabalho, solicita justificativas em tempo real e centraliza os dados em um dashboard administrativo para análise de indicadores.

## Tecnologias Utilizadas
* **Cliente:** Python 3.x, Tkinter, Pynput (Monitoramento de Hardware), Requests.
* **Servidor:** FastAPI, SQLite (Banco de Dados local), Jinja2 (Templates), Chart.js (Gráficos).

---

## Guia de Implantação (Passo a Passo)

### Preparação do Servidor (Nuvem ou Local)
1. **Ambiente:** Certifique-se de ter o Python 3.8+ instalado.
2. **Dependências:** Instale os pacotes necessários:
   ```bash
   pip install fastapi uvicorn jinja2 python-multipart

3. Arquivos: - Coloque o arquivo ServerNUVEM.py na raiz do seu diretório.
* Crie uma pasta chamada templates e insira os arquivos login.html e dashboard.html dentro dela.

4. Para instalar o arquivo como serviço:
   ```bash
   uvicorn ServerNUVEM:app --host 0.0.0.0 --port 8000

## Configuração do Cliente (Máquinas dos Operadores)
1. Configuração de Conexão: No arquivo OCISOSIDADE.py, altere a variável SERVER_URL para o endereço IP ou domínio do seu servidor (ex: http://192.168.1.50:8000).

2. Ajuste de Sensibilidade: Altere a variável IDLE_THRESHOLD para definir o tempo de inatividade (em segundos) antes do disparo do alerta.

3. Dependências do Cliente:
   ```bash
   pip install pynput requests

Para Geração do Executável  
   ```bash
      pip install pyinstaller
      pyinstaller --noconsole --onefile --hidden-import=pynput.keyboard._win32 --hidden-import=pynput.mouse._win32 --name="MonitorOciosidade" OCISOSIDADE.py
