# controle_ociosidade
 Este projeto consiste em um ecossistema completo para Gestão de Produtividade e Monitoramento de Pausas, composto por um agente cliente (Python) e um servidor centralizador (FastAPI). O sistema automatiza a identificação de inatividade, obriga a justificativa pelo colaborador e gera indicadores visuais para a gestão.

🚀 Guia de Implantação (Passo a Passo)
Para colocar a estrutura em funcionamento, siga estas etapas:

1. Preparação do Servidor (Nuvem ou Local)
Ambiente: Certifique-se de ter o Python 3.8+ instalado no servidor.

Dependências: Instale os pacotes necessários:

Bash
pip install fastapi uvicorn jinja2 python-multipart
Arquivos: Crie uma pasta raiz e dentro dela uma pasta chamada templates.

Coloque ServerNUVEM.py na raiz.

Coloque login.html e dashboard.html dentro da pasta templates.

Configuração: Edite as variáveis USER_ADMIN e PASS_ADMIN no ServerNUVEM.py para sua segurança.

Execução: Inicie o servidor:

Bash
uvicorn ServerNUVEM:app --host 0.0.0.0 --port 8000
2. Configuração do Cliente (Máquinas dos Operadores)
Edição do Script: No arquivo OCISOSIDADE.py, altere a variável SERVER_URL para o IP ou domínio do seu servidor (ex: http://192.168.1.50:8000).

Ajuste de Sensibilidade: Altere IDLE_THRESHOLD para o tempo desejado (em segundos) antes de disparar o alerta.

Compilação (Opcional): Para não precisar instalar Python em cada PC, gere o executável:

Bash
pyinstaller --noconsole --onefile --hidden-import=pynput.keyboard._win32 --hidden-import=pynput.mouse._win32 --name="MonitorOciosidade" OCISOSIDADE.py
3. Operação do Painel
Acesse http://seu-ip:8000/login para entrar no dashboard.

Cadastro: Use a barra lateral para cadastrar os motivos de pausa (ex: Reunião, Intervalo, Problema Técnico).

Acompanhamento: Utilize o filtro de datas para visualizar gráficos de atividade vs. pausas e exportar relatórios em CSV.

📊 Estrutura de Dados
O sistema utiliza SQLite, o que dispensa a configuração de bancos de dados externos complexos. Ao iniciar o servidor pela primeira vez, o arquivo data.db será criado automaticamente com as tabelas de logs, motivos e usuários.
