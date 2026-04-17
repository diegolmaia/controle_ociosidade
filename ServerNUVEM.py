import os, sqlite3, csv, io
from fastapi import FastAPI, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime
from collections import Counter

# Configurações de Caminho e Login
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data.db")
USER_ADMIN = "SEU_USUARIO_ADMIN"
PASS_ADMIN = "SEU_PASSWORD"

app = FastAPI()
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Tabela de motivos e logs (já existentes)
    cursor.execute('''CREATE TABLE IF NOT EXISTS reasons (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS logs (id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, start_time TEXT, end_time TEXT, reason TEXT, date TEXT)''')
    
    # NOVA TABELA: Usuários do Painel
    cursor.execute('''CREATE TABLE IF NOT EXISTS web_users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT)''')
    
    # Inserir o admin padrão se não existir
    cursor.execute("INSERT OR IGNORE INTO web_users (username, password) VALUES (?, ?)", ('admin', 'admin123'))
    
    # ... (restante dos motivos padrão)
    conn.commit()
    conn.close()


init_db()

def calcular_minutos(inicio, fim):
    try:
        fmt = "%H:%M:%S"
        tdelta = datetime.strptime(fim, fmt) - datetime.strptime(inicio, fmt)
        return int(tdelta.total_seconds() / 60)
    except: return 0

# --- ROTAS DE AUTENTICAÇÃO ---
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, error: bool = False):
    return templates.TemplateResponse("login.html", {"request": request, "error": error})

@app.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    # 1. Primeiro verifica no Banco de Dados
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM web_users WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()
    conn.close()

    # 2. Valida se o usuário existe no banco OU se é o admin das variáveis globais
    if user or (username == USER_ADMIN and password == PASS_ADMIN):
        res = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
        # Boa prática: httponly ajuda a proteger o cookie contra roubo via JS
        res.set_cookie(key="auth_token", value="valid_session", httponly=True)
        return res
    
    # 3. Se falhar, redireciona com erro
    return RedirectResponse(url="/login?error=true", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/users/add")
async def add_web_user(request: Request, new_username: str = Form(...), new_password: str = Form(...)):
    # Proteção: só quem já está logado pode adicionar outros
    if request.cookies.get("auth_token") != "valid_session":
        return RedirectResponse(url="/login")
        
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("INSERT INTO web_users (username, password) VALUES (?, ?)", (new_username, new_password))
        conn.commit()
    except sqlite3.IntegrityError:
        pass # Usuário já existe
    finally:
        conn.close()
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/logout")
async def logout():
    res = RedirectResponse(url="/login")
    res.delete_cookie("auth_token")
    return res

# --- DASHBOARD ---
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, data_inicio: str = None, data_fim: str = None):
    if request.cookies.get("auth_token") != "valid_session":
        return RedirectResponse(url="/login")
    
    # Define o dia de hoje no formato ISO (YYYY-MM-DD) como padrão
    hoje_iso = datetime.now().strftime("%Y-%m-%d")
    inicio = data_inicio if data_inicio else hoje_iso
    fim = data_fim if data_fim else hoje_iso

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Busca Logs filtrando pelo INTERVALO de datas (Formato ISO permite BETWEEN direto)
    cursor.execute("""
        SELECT user, start_time, end_time, reason, date 
        FROM logs 
        WHERE date BETWEEN ? AND ? 
        ORDER BY id DESC
    """, (inicio, fim))
    logs_raw = cursor.fetchall()
    logs = [list(l) + [f"{calcular_minutos(l[1], l[2])} min"] for l in logs_raw]
    
    # 2. Dados para os Gráficos filtrados pelo mesmo período
    cursor.execute("SELECT start_time, end_time FROM logs WHERE date BETWEEN ? AND ?", (inicio, fim))
    periodo_pausas = cursor.fetchall()
    
    turnos_labels = ["00h-06h", "06h-12h", "12h-18h", "18h-24h"]
    pausas_por_turno = [0, 0, 0, 0]
    qtd_por_turno = [0, 0, 0, 0]
    
    for start, end in periodo_pausas:
        try:
            hora = int(start.split(':')[0])
            minutos = calcular_minutos(start, end)
            
            if 0 <= hora < 6: idx = 0
            elif 6 <= hora < 12: idx = 1
            elif 12 <= hora < 18: idx = 2
            else: idx = 3
            
            pausas_por_turno[idx] += minutos
            qtd_por_turno[idx] += 1
        except: continue

    atividade_por_turno = [max(0, 360 - p) for p in pausas_por_turno]

    # 3. Gráfico de Frequência de Motivos (Quantidade) no período
    cursor.execute("SELECT reason FROM logs WHERE date BETWEEN ? AND ?", (inicio, fim))
    m_data = [row[0] for row in cursor.fetchall()]
    m_counts = dict(Counter(m_data))

    # Motivos para a barra lateral
    cursor.execute("SELECT id, name FROM reasons")
    reasons_list = cursor.fetchall()

    conn.close()
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "data_inicio": inicio,
        "data_fim": fim,
        "data_selecionada": inicio, # Compatibilidade com campo único se necessário
        "logs": logs, 
        "reasons": reasons_list,
        "t_labels": turnos_labels,
        "t_pausas": pausas_por_turno,
        "t_atividade": atividade_por_turno,
        "t_qtd": qtd_por_turno,
        "m_labels": list(m_counts.keys()), 
        "m_values": list(m_counts.values())
    })


# --- GESTÃO DE MOTIVOS E EXPORTAÇÃO ---
@app.post("/reasons/add")
async def add_r(name: str = Form(...)):
    conn = sqlite3.connect(DB_PATH); conn.execute("INSERT OR IGNORE INTO reasons (name) VALUES (?)", (name,))
    conn.commit(); conn.close()
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/reasons/del/{rid}")
async def del_r(rid: int):
    conn = sqlite3.connect(DB_PATH); conn.execute("DELETE FROM reasons WHERE id=?", (rid,))
    conn.commit(); conn.close()
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/api/export")
async def export():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Buscamos os dados do banco
    cursor.execute("SELECT user, date, start_time, end_time, reason FROM logs")
    rows = cursor.fetchall()
    
    si = io.StringIO()
    cw = csv.writer(si)
    
    # Cabeçalho do Excel/CSV
    cw.writerow(['Operador', 'Data', 'Inicio', 'Fim', 'Motivo', 'Duracao (Minutos)'])
    
    # Processa cada linha para calcular a duração antes de escrever no CSV
    for row in rows:
        user, date, start, end, reason = row
        duracao = calcular_minutos(start, end)
        cw.writerow([user, date, start, end, reason, f"{duracao} min"])
    
    conn.close()
    
    # Retorna o arquivo para download
    return StreamingResponse(
        io.StringIO(si.getvalue()), 
        media_type="text/csv", 
        headers={"Content-Disposition": "attachment; filename=relatorio_detalhado.csv"}
    )

# API CLIENTE
@app.get("/api/reasons")
async def api_r():
    conn = sqlite3.connect(DB_PATH); r = [row[0] for row in conn.execute("SELECT name FROM reasons").fetchall()]; conn.close()
    return r

@app.post("/api/log")
async def api_l(d: dict):
    conn = sqlite3.connect(DB_PATH)
    # Deve ser %Y-%m-%d para funcionar com o novo filtro
    today_iso = datetime.now().strftime("%Y-%m-%d") 
    conn.execute(
        "INSERT INTO logs (user, start_time, end_time, reason, date) VALUES (?,?,?,?,?)", 
        (d['user'], d['start'], d['end'], d['reason'], today_iso)
    )
    conn.commit()
    conn.close()
    return {"ok": True}
