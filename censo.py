import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import hashlib
import json
import os
import folium
from streamlit_folium import st_folium
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fpdf import FPDF
import tempfile

# ==================== CONFIGURACIÓN ====================
st.set_page_config(
    page_title="Censo de Científicos y Técnicos",
    page_icon="🌋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Archivos
DB_FILE = "censo_sismologia.db"
CONFIG_FILE = "config.json"
LOGO_SIDEBAR = "log.png"
LOGO_HEADER = "logo02.png"

# ==================== DATOS DE MUNICIPIOS DE SUCRE ====================
MUNICIPIOS_SUCRE = {
    "Andrés Eloy Blanco (Casanay)": [
        "Casanay", "Andrés Eloy Blanco"
    ],
    "Andrés Mata (San José de Areocuar)": [
        "San José de Areocuar", "Andrés Mata"
    ],
    "Arismendi (Río Caribe)": [
        "Río Caribe", "Antonio José de Sucre", "El Morro de Puerto Santo", 
        "Puerto Santo", "San Juan de las Galdonas"
    ],
    "Benítez (El Pilar)": [
        "El Pilar", "El Rincón", "General Francisco Antonio Vázquez", 
        "Guaraúnos", "Tunapuicito", "Unión"
    ],
    "Bermúdez (Carúpano)": [
        "Carúpano", "Santa Catalina", "Santa Rosa", "Santa Teresa"
    ],
    "Bolívar (Marigüitar)": [
        "Bolívar", "Maracapana", "Marigüitar"
    ],
    "Cajigal (Yaguaraparo)": [
        "Yaguaraparo", "El Paujil", "Libertador"
    ],
    "Cruz Salmerón Acosta (Araya)": [
        "Araya", "Chacopata", "Manicuare"
    ],
    "Libertador (Tunapuy)": [
        "Tunapuy", "Campo Elíseo"
    ],
    "Mariño (Irapa)": [
        "Irapa", "Campo Claro", "Maraval", 
        "San Antonio de Irapa", "Sosa"
    ],
    "Mejía (San Antonio del Golfo)": [
        "San Antonio del Golfo"
    ],
    "Montes (Cumanacoa)": [
        "Cumanacoa", "Arenas", "Aricagua", 
        "Cocollar", "San Fernando", "San Lorenzo"
    ],
    "Ribero (Cariaco)": [
        "Cariaco", "Catuaro", "El Rincón", 
        "Santa Cruz", "Rendón"
    ],
    "Sucre (Cumaná)": [
        "Altagracia", "Ayacucho", "Gran Mariscal", 
        "Raúl Leoni", "San Juan", "Santa Inés", 
        "Valentín Valiente"
    ],
    "Valdez (Güiria)": [
        "Güiria", "Bideau", "Cristóbal Colón", 
        "Flamingo", "Pascual Magallanes"
    ]
}

# ==================== TODAS LAS PARROQUIAS DE VENEZUELA ====================
PARROQUIAS_VENEZUELA = [
    "Mariño", "Rómulo Gallegos", "San José de Aerocuar", "Tavera Acosta", 
    "Río Caribe", "Antonio José de Sucre", "El Morro de Puerto Santo", 
    "Puerto Santo", "San Juan de las Galdonas", "El Pilar", "El Rincón", 
    "General Francisco Antonio Vázquez", "Guaraúnos", "Tunapuicito", "Unión", 
    "Santa Catalina", "Santa Rosa", "Santa Teresa", "Bolívar", "Maracapana", 
    "Marigüitar", "Yaguaraparo", "El Paujil", "Libertador", "San Vicente de Paúl", 
    "Araya", "Chacopata", "Manicuare", "Tunapuy", "Campo Elíseo", "Irapa", 
    "Campo Claro", "Maraval", "San Antonio de Irapa", "Sosa", 
    "San Antonio del Golfo", "Cumanacoa", "Arenas", "Aricagua", "Cocollar", 
    "El Chaparral", "San Fernando", "San Lorenzo", "Cariaco", "Catuaro", 
    "Santa Cruz", "Rendón", "Altagracia", "Ayacucho", "Gran Mariscal", 
    "Raúl Leoni", "San Juan", "Santa Inés", "Valentín Valiente", "Güiria", 
    "Bideau", "Cristóbal Colón", "Flamingo", "Pascual Magallanes"
]

# ==================== ESTILOS CSS COMPATIBLE CON MODO OSCURO ====================
st.markdown("""
    <style>
    /* Fondo principal - usa el color nativo de Streamlit */
    .stApp {
        background: transparent !important;
    }

    .main-header {
        font-size: 2.4rem;
        font-weight: 800;
        color: #1e40af;
        text-align: center;
        margin: 0;
        letter-spacing: -0.5px;
        text-shadow: 0 2px 4px rgba(30, 64, 175, 0.1);
    }

    [data-theme="dark"] .main-header {
        color: #60a5fa;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
    }

    .convocatoria-badge {
        display: inline-block;
        background: linear-gradient(135deg, #059669 0%, #047857 100%);
        color: white;
        padding: 0.5rem 1.5rem;
        border-radius: 50px;
        font-weight: 700;
        font-size: 0.95rem;
        letter-spacing: 1px;
        text-transform: uppercase;
        box-shadow: 0 4px 15px rgba(5, 150, 105, 0.3);
        animation: pulse 2s infinite;
    }

    @keyframes pulse {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.9; transform: scale(1.02); }
    }

    /* ============================================
       SIDEBAR - FONDO AZUL + LETRAS BLANCAS SIEMPRE
       ============================================ */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e3a5f 0%, #1e40af 100%) !important;
    }

    [data-testid="stSidebar"] * {
        color: #f8fafc !important;
    }

    [data-testid="stSidebar"] .stRadio > div {
        background: rgba(255, 255, 255, 0.08) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 10px;
        padding: 0.5rem 1rem;
    }

    [data-testid="stSidebar"] .stRadio > div:hover {
        background: rgba(255, 255, 255, 0.15) !important;
    }

    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] h4 {
        color: #f8fafc !important;
    }

    [data-testid="stSidebar"] .stAlert {
        background: rgba(255, 255, 255, 0.1) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
    }

    [data-testid="stSidebar"] .stAlert * {
        color: #f8fafc !important;
    }

    [data-testid="stSidebar"] hr {
        border-color: rgba(255, 255, 255, 0.2) !important;
    }

    .admin-badge {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        color: white;
        padding: 0.4rem 1rem;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.85rem;
        display: inline-block;
        box-shadow: 0 2px 10px rgba(245, 158, 11, 0.3);
    }

    .stButton>button {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
        color: white;
        font-weight: 700;
        border-radius: 10px;
        padding: 0.6rem 2.5rem;
        border: none;
        box-shadow: 0 4px 15px rgba(37, 99, 235, 0.3);
        transition: all 0.3s ease;
    }

    .stButton>button:hover {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        box-shadow: 0 6px 20px rgba(37, 99, 235, 0.5);
        transform: translateY(-2px);
    }

    .stForm {
        background: rgba(128, 128, 128, 0.05);
        padding: 2rem;
        border-radius: 16px;
        border: 1px solid rgba(128, 128, 128, 0.2);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
    }

    [data-theme="dark"] .stForm {
        border-color: rgba(255, 255, 255, 0.1);
        background: rgba(255, 255, 255, 0.03);
    }

    .stTextInput>div>div>input, 
    .stSelectbox>div>div>select, 
    .stTextArea>div>div>textarea {
        border-radius: 10px;
        padding: 0.5rem;
    }

    .stTextInput>div>div>input:focus, 
    .stSelectbox>div>div>select:focus {
        border-color: #3b82f6;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
    }

    .stTextInput label, .stSelectbox label, .stTextArea label, 
    .stNumberInput label, .stDateInput label, .stRadio label {
        font-weight: 600;
        font-size: 0.95rem;
    }

    .success-msg {
        padding: 1.2rem;
        background: rgba(16, 185, 129, 0.15);
        border-left: 5px solid #10b981;
        border-radius: 12px;
    }

    [data-theme="dark"] .success-msg {
        background: rgba(16, 185, 129, 0.1);
    }

    .warning-msg {
        padding: 1.2rem;
        background: rgba(245, 158, 11, 0.15);
        border-left: 5px solid #f59e0b;
        border-radius: 12px;
    }

    [data-theme="dark"] .warning-msg {
        background: rgba(245, 158, 11, 0.1);
    }

    .info-box {
        padding: 1.2rem;
        border-radius: 12px;
        border: 1px solid rgba(59, 130, 246, 0.3);
        background: rgba(59, 130, 246, 0.1);
    }

    [data-theme="dark"] .info-box {
        background: rgba(59, 130, 246, 0.08);
        border-color: rgba(59, 130, 246, 0.2);
    }

    .login-box {
        max-width: 400px;
        margin: 0 auto;
        padding: 2.5rem;
        border-radius: 16px;
        border: 1px solid rgba(128, 128, 128, 0.2);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        background: rgba(128, 128, 128, 0.05);
    }

    [data-theme="dark"] .login-box {
        border-color: rgba(255, 255, 255, 0.1);
        background: rgba(255, 255, 255, 0.03);
    }

    .stDataFrame {
        border-radius: 12px;
        border: 1px solid rgba(128, 128, 128, 0.2);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    }

    .stRadio > div {
        padding: 0.5rem 1rem;
        border-radius: 10px;
        border: 2px solid rgba(128, 128, 128, 0.2);
        background: rgba(128, 128, 128, 0.05);
    }

    .stMultiSelect > div > div {
        border-radius: 10px;
        border: 2px solid rgba(128, 128, 128, 0.2);
    }

    .stMarkdown {
        color: inherit;
    }

    .stMarkdown h3, .stMarkdown h4 {
        border-bottom: 2px solid rgba(128, 128, 128, 0.2);
        padding-bottom: 0.5rem;
        margin-top: 1.5rem;
    }

    .stAlert {
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    }

    .stDownloadButton>button {
        background: linear-gradient(135deg, #7c3aed 0%, #6d28d9 100%);
        box-shadow: 0 4px 15px rgba(124, 58, 237, 0.3);
    }

    .stDownloadButton>button:hover {
        background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
        box-shadow: 0 6px 20px rgba(124, 58, 237, 0.5);
    }

    .css-1r6slb0, .css-1xarl3l {
        border-radius: 12px;
        border: 1px solid rgba(128, 128, 128, 0.2);
        padding: 1rem;
    }

    [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlockBorderWrapper"] {
        background: transparent !important;
    }

    [data-testid="stAppViewContainer"] {
        background: transparent !important;
    }

    .block-container {
        background: transparent !important;
    }

    [data-testid="stForm"] {
        background: transparent !important;
    }

    [data-theme="dark"] .stMarkdown p,
    [data-theme="dark"] .stMarkdown span,
    [data-theme="dark"] .stTextInput label,
    [data-theme="dark"] .stSelectbox label,
    [data-theme="dark"] .stTextArea label,
    [data-theme="dark"] .stNumberInput label,
    [data-theme="dark"] .stDateInput label,
    [data-theme="dark"] .stRadio label {
        color: inherit !important;
    }
    </style>
""", unsafe_allow_html=True)

# ==================== FUNCIONES DE AUTENTICACIÓN ====================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_config():
    if not os.path.exists(CONFIG_FILE):
        default_config = {
            "admin_password": hash_password("admin123"),
            "admin_email": "tucorreo@gmail.com",
            "email_password": "tu_contraseña_de_aplicacion"
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(default_config, f)
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def verify_admin(password):
    config = init_config()
    return hash_password(password) == config["admin_password"]

def change_admin_password(new_password):
    config = init_config()
    config["admin_password"] = hash_password(new_password)
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f)

def update_admin_email(email, email_password):
    config = init_config()
    config["admin_email"] = email
    config["email_password"] = email_password
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f)

# ==================== FUNCIONES DE BASE DE DATOS ====================

def get_db_connection():
    return sqlite3.connect(DB_FILE)

def verificar_y_migrar_tabla():
    """Verifica que la tabla tenga todas las columnas necesarias y las agrega si faltan."""
    conn = get_db_connection()
    c = conn.cursor()

    # Obtener columnas actuales
    c.execute("PRAGMA table_info(cientificos)")
    columnas_existentes = {col[1] for col in c.fetchall()}

    # Columnas requeridas
    columnas_requeridas = {
        'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
        'codigo': 'TEXT UNIQUE',
        'fecha_registro': 'TEXT',
        'nombre_completo': 'TEXT NOT NULL',
        'correo_electronico': 'TEXT NOT NULL',
        'telefono': 'TEXT',
        'fecha_nacimiento': 'TEXT',
        'genero': 'TEXT',
        'pais': 'TEXT',
        'ciudad': 'TEXT',
        'profesion': 'TEXT',
        'nivel_academico': 'TEXT',
        'institucion': 'TEXT',
        'anos_experiencia': 'INTEGER',
        'area_especializacion': 'TEXT',
        'idiomas': 'TEXT',
        'equipos_maneja': 'TEXT',
        'misiones_campo': 'TEXT',
        'disponibilidad': 'TEXT',
        'certificaciones': 'TEXT',
        'municipio': 'TEXT',
        'parroquia': 'TEXT',
        'comentarios': 'TEXT'
    }

    # Si la tabla no existe, crearla
    if not columnas_existentes:
        columnas_sql = ", \
            ".join([f"{k} {v}" for k, v in columnas_requeridas.items()])
        c.execute(f"CREATE TABLE cientificos ({columnas_sql})")
        conn.commit()
        conn.close()
        return

    # Si existe, verificar columnas faltantes
    for columna, tipo in columnas_requeridas.items():
        if columna not in columnas_existentes:
            try:
                c.execute(f"ALTER TABLE cientificos ADD COLUMN {columna} {tipo}")
            except sqlite3.OperationalError:
                pass  # Columna ya existe o error menor

    conn.commit()
    conn.close()

def init_db():
    verificar_y_migrar_tabla()

def generar_codigo():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM cientificos")
    count = c.fetchone()[0] + 1
    conn.close()
    return f"SIS-{count:03d}"

def insertar_cientifico(datos):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO cientificos (
            codigo, fecha_registro, nombre_completo, correo_electronico, telefono,
            fecha_nacimiento, genero, pais, ciudad, profesion, nivel_academico,
            institucion, anos_experiencia, area_especializacion, idiomas,
            equipos_maneja, misiones_campo, disponibilidad, certificaciones,
            municipio, parroquia, comentarios
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', datos)
    conn.commit()
    conn.close()

def obtener_todos():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM cientificos ORDER BY id DESC", conn)
    conn.close()
    return df

def obtener_por_id(codigo):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM cientificos WHERE codigo = ?", (codigo,))
    row = c.fetchone()
    conn.close()
    return row

def actualizar_cientifico(codigo, datos):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        UPDATE cientificos SET
            nombre_completo=?, correo_electronico=?, telefono=?, fecha_nacimiento=?,
            genero=?, pais=?, ciudad=?, profesion=?, nivel_academico=?,
            institucion=?, anos_experiencia=?, area_especializacion=?, idiomas=?,
            equipos_maneja=?, misiones_campo=?, disponibilidad=?, certificaciones=?,
            municipio=?, parroquia=?, comentarios=?
        WHERE codigo=?
    ''', (*datos, codigo))
    conn.commit()
    conn.close()

def eliminar_cientifico(codigo):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM cientificos WHERE codigo = ?", (codigo,))
    conn.commit()
    conn.close()

# Inicializar base de datos
init_db()

# ==================== FUNCIONES DE CORREO ====================
def enviar_correo_nuevo_registro(datos_cientifico):
    try:
        config = init_config()
        admin_email = config.get("admin_email", "")
        email_password = config.get("email_password", "")

        if not admin_email or not email_password or admin_email == "tucorreo@gmail.com":
            return False, "Correo no configurado"

        msg = MIMEMultipart()
        msg['From'] = admin_email
        msg['To'] = admin_email
        msg['Subject'] = f"🌋 Nuevo registro en Censo - {datos_cientifico['nombre']}"

        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2 style="color: #1e40af;">Nuevo científico registrado</h2>
            <div style="padding: 15px; border-radius: 12px; border: 1px solid #e2e8f0;">
                <p><strong>Código:</strong> {datos_cientifico['codigo']}</p>
                <p><strong>Nombre:</strong> {datos_cientifico['nombre']}</p>
                <p><strong>Profesión:</strong> {datos_cientifico['profesion']}</p>
                <p><strong>Institución:</strong> {datos_cientifico['institucion']}</p>
                <p><strong>País:</strong> {datos_cientifico['pais']}</p>
                <p><strong>Correo:</strong> {datos_cientifico['correo']}</p>
                <p><strong>Teléfono:</strong> {datos_cientifico['telefono']}</p>
                <p><strong>Fecha de registro:</strong> {datos_cientifico['fecha']}</p>
            </div>
        </body>
        </html>
        """

        msg.attach(MIMEText(body, 'html'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(admin_email, email_password)
        server.send_message(msg)
        server.quit()

        return True, "Correo enviado correctamente"
    except Exception as e:
        return False, str(e)

# ==================== FUNCIONES DE PDF ====================
class PDFCenso(FPDF):
    def header(self):
        if os.path.exists(LOGO_HEADER):
            self.image(LOGO_HEADER, 10, 8, 25)

        self.set_font('Arial', 'B', 14)
        self.set_text_color(30, 58, 138)
        self.cell(0, 10, 'CENSO DE CIENTIFICOS Y TECNICOS', 0, 1, 'C')
        self.set_font('Arial', 'B', 10)
        self.set_text_color(5, 150, 105)
        self.cell(0, 6, 'CONVOCATORIA ACTIVA', 0, 1, 'C')
        self.set_font('Arial', '', 9)
        self.set_text_color(100, 100, 100)
        self.cell(0, 5, f'Generado el: {datetime.now().strftime("%d/%m/%Y %H:%M")}', 0, 1, 'C')
        self.ln(8)
        self.set_draw_color(37, 99, 235)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')

def generar_pdf_censo(df):
    pdf = PDFCenso()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font('Arial', '', 8)

    pdf.set_fill_color(37, 99, 235)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Arial', 'B', 8)

    headers = ['Codigo', 'Nombre', 'Profesion', 'Institucion', 'Pais', 'Nivel', 'Exp', 'Disponibilidad']
    col_widths = [20, 45, 35, 35, 25, 20, 12, 30]

    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 8, header, 1, 0, 'C', True)
    pdf.ln()

    pdf.set_text_color(30, 41, 59)
    pdf.set_font('Arial', '', 7)

    for _, row in df.iterrows():
        pdf.cell(col_widths[0], 6, str(row['codigo']), 1, 0, 'C')
        pdf.cell(col_widths[1], 6, str(row['nombre_completo'])[:25], 1, 0, 'L')
        pdf.cell(col_widths[2], 6, str(row['profesion'])[:20], 1, 0, 'L')
        pdf.cell(col_widths[3], 6, str(row['institucion'])[:20], 1, 0, 'L')
        pdf.cell(col_widths[4], 6, str(row['pais'])[:15], 1, 0, 'L')
        pdf.cell(col_widths[5], 6, str(row['nivel_academico'])[:10], 1, 0, 'C')
        pdf.cell(col_widths[6], 6, str(row['anos_experiencia']), 1, 0, 'C')
        pdf.cell(col_widths[7], 6, str(row['disponibilidad'])[:18], 1, 0, 'L')
        pdf.ln()

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    pdf.output(temp_file.name)
    return temp_file.name

# ==================== HEADER CON LOGO Y TÍTULO ====================
col_logo, col_titulo = st.columns([1, 6])

with col_logo:
    if os.path.exists(LOGO_HEADER):
        st.image(LOGO_HEADER, width=70)
    else:
        st.markdown("")

with col_titulo:
    st.markdown("""
        <div style="display: flex; align-items: center; height: 100%;">
            <h1 class="main-header" style="margin: 0; text-align: left;">Censo de Científicos y Técnicos</h1>
        </div>
    """, unsafe_allow_html=True)

st.markdown("""
    <div style="text-align: center; margin-bottom: 1.5rem;">
        <span class="convocatoria-badge">🔥 Convocatoria Activa</span>
    </div>
""", unsafe_allow_html=True)

# ==================== ESTADO DE SESIÓN ====================
if 'admin_logged_in' not in st.session_state:
    st.session_state.admin_logged_in = False

# ==================== SIDEBAR CON LOGO ====================
with st.sidebar:
    if os.path.exists(LOGO_SIDEBAR):
        st.sidebar.image(LOGO_SIDEBAR, use_container_width=True)
    else:
        st.sidebar.markdown("🌋 **Censo**")

    st.markdown("### 📊 Panel de Control")
    st.markdown("---")

    if st.session_state.admin_logged_in:
        st.markdown('<span class="admin-badge">🔐 MODO ADMINISTRADOR</span>', unsafe_allow_html=True)
        st.markdown("---")

    if st.session_state.admin_logged_in:
        menu = st.radio(
            "Selecciona una opción:",
            ["📝 Registrar Científico", "📋 Ver Registros", "✏️ Editar Registro", "🗑️ Eliminar Registro", 
             "🗺️ Mapa de Ubicaciones", "📈 Estadísticas", "📄 Generar PDF", "⚙️ Configuración Admin", "🔒 Cerrar Sesión"]
        )
    else:
        menu = st.radio(
            "Selecciona una opción:",
            ["📝 Registrar Científico", "📋 Ver Registros", "🗺️ Mapa de Ubicaciones", "📈 Estadísticas", "📄 Generar PDF", "🔐 Acceso Administrador"]
        )

    st.markdown("---")

    df_count = obtener_todos()
    st.markdown('<div class="info-box">', unsafe_allow_html=True)
    st.markdown("**Total de registros:**")
    st.markdown(f"<h2 style='text-align: center; color: #1e40af; margin: 0;'>{len(df_count)}</h2>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.info("💡 Este censo recopila información de profesionales técnicos.")

# ==================== LOGIN ADMIN ====================
def admin_login():
    st.markdown('<div class="login-box">', unsafe_allow_html=True)
    st.markdown("### 🔐 Acceso Administrador")
    st.warning("⚠️ Área restringida. Solo personal autorizado.")

    password = st.text_input("Contraseña", type="password")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Iniciar sesión"):
            if verify_admin(password):
                st.session_state.admin_logged_in = True
                st.success("✅ Acceso concedido")
                st.rerun()
            else:
                st.error("❌ Contraseña incorrecta")

    with col2:
        st.markdown("*Contraseña por defecto: admin123*")
        st.markdown("*Cámbiala en Configuración*")

    st.markdown('</div>', unsafe_allow_html=True)

# ==================== CERRAR SESIÓN ====================
def cerrar_sesion():
    st.session_state.admin_logged_in = False
    st.success("🔒 Sesión cerrada")
    st.rerun()

# ==================== FORMULARIO DE REGISTRO ====================
def formulario_registro():
    st.markdown("### 📝 Formulario de Registro")
    st.markdown("Complete todos los campos obligatorios (*)")

    with st.form("formulario_censo", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 👤 Información Personal")
            nombre = st.text_input("Nombre completo *", placeholder="Ej: Dr. María Elena Vásquez")
            correo = st.text_input("Correo electrónico *", placeholder="ejemplo@institucion.gob")
            telefono = st.text_input("Teléfono *", placeholder="+58 412 1234567")
            fecha_nac = st.date_input("Fecha de nacimiento", value=datetime(1985, 1, 1))

            genero = st.selectbox("Género *", ["", "Masculino", "Femenino"])

            st.markdown("#### 🌍 Ubicación")
            pais = st.selectbox("País *", [
                "", "Venezuela", "Colombia", "Ecuador", "Perú", "Chile", "Argentina", 
                "Brasil", "Bolivia", "México", "Estados Unidos", "Guatemala", 
                "El Salvador", "Honduras", "Nicaragua", "Costa Rica", "Panamá", 
                "España", "Japón", "Italia", "Nueva Zelanda", "Otro"
            ])
            ciudad = st.text_input("Ciudad *", placeholder="Ej: Caracas")

            st.markdown("#### 📍 Municipio del Estado Sucre")
            municipio_seleccionado = st.selectbox(
                "Municipio *",
                [""] + list(MUNICIPIOS_SUCRE.keys())
            )

            st.markdown("#### 🏘️ Parroquia")
            parroquia_seleccionada = st.selectbox(
                "Parroquia *",
                [""] + PARROQUIAS_VENEZUELA
            )

        with col2:
            st.markdown("#### 🎓 Formación Profesional")
            profesion = st.text_input("Profesión *", placeholder="Ej: Ingeniero Geofísico")
            nivel_academico = st.selectbox("Nivel académico *", [
                "", "Técnico", "Licenciatura", "Maestría", "Doctorado", "Posdoctorado"
            ])
            institucion = st.text_input("Institución u organización *", 
                                       placeholder="Ej: FUNVISIS, UCV, USB")
            anos_exp = st.number_input("Años de experiencia *", 
                                      min_value=0, max_value=50, value=5)

            st.markdown("#### 🔬 Especialización")
            area_esp = st.multiselect("Área de especialización", [
                "Sismología instrumental", "Ingeniería sísmica", "Sismología de exploración",
                "Vulcanología", "Geodesia", "Tsunamología", "Peligro sísmico",
                "Riesgo sísmico", "Sismología de pozo", "Sismología global",
                "Sismología de fuente", "Ondas de superficie", "Otro"
            ])

            equipos = st.multiselect("Equipos que maneja", [
                "Sismógrafo de banda ancha", "Acelerógrafo", "Estación GPS/GNSS",
                "Inclinómetro", "Extensómetro", "Tiltmeter", "Software SEISAN",
                "Software Antelope", "Software ObsPy", "Software SAC", "GIS (ArcGIS/QGIS)",
                "Estación meteorológica", "Dron para mapeo", "Otro"
            ])

        st.markdown("#### 💼 Información Adicional")
        col3, col4 = st.columns(2)

        with col3:
            idiomas = st.multiselect("Idiomas que domina", [
                "Español", "Inglés", "Francés", "Alemán", "Japonés", 
                "Italiano", "Portugués", "Chino", "Ruso", "Otro"
            ], default=["Español"])

            misiones = st.radio("¿Ha participado en misiones de campo? *", 
                               ["Sí", "No"], horizontal=True)

        with col4:
            disponibilidad = st.selectbox("Disponibilidad de tiempo *", [
                "", "Tiempo completo", "Medio tiempo (mañana)", "Medio tiempo (tarde)",
                "Fines de semana", "Disponibilidad inmediata", "No disponible actualmente"
            ])

            certificaciones = st.text_area("Certificaciones relevantes", 
                                          placeholder="Ej: Normas técnicas de construcción, certificaciones FUNVISIS, etc.")

        comentarios = st.text_area("Comentarios adicionales", 
                                  placeholder="Información adicional relevante para el censo...")

        submitted = st.form_submit_button("💾 Guardar Registro")

        if submitted:
            campos_obligatorios = [nombre, correo, telefono, genero, pais, ciudad, 
                                  profesion, nivel_academico, institucion, disponibilidad,
                                  municipio_seleccionado, parroquia_seleccionada]

            if "" in campos_obligatorios or None in campos_obligatorios:
                st.error("❌ Por favor complete todos los campos obligatorios (*)")
            else:
                codigo = generar_codigo()
                fecha_reg = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                datos = (
                    codigo, fecha_reg, nombre, correo, telefono,
                    fecha_nac.strftime("%Y-%m-%d"), genero, pais, ciudad,
                    profesion, nivel_academico, institucion, anos_exp,
                    ", ".join(area_esp), ", ".join(idiomas), ", ".join(equipos),
                    misiones, disponibilidad, certificaciones,
                    municipio_seleccionado, parroquia_seleccionada, comentarios
                )

                insertar_cientifico(datos)

                datos_correo = {
                    'codigo': codigo,
                    'nombre': nombre,
                    'profesion': profesion,
                    'institucion': institucion,
                    'pais': pais,
                    'correo': correo,
                    'telefono': telefono,
                    'fecha': fecha_reg
                }
                exito, mensaje = enviar_correo_nuevo_registro(datos_correo)

                st.markdown('<div class="success-msg">', unsafe_allow_html=True)
                st.success(f"✅ Registro guardado exitosamente con ID: **{codigo}**")
                st.markdown(f"**Nombre:** {nombre}")
                st.markdown(f"**Profesión:** {profesion}")
                st.markdown(f"**Institución:** {institucion}")
                st.markdown(f"**Municipio:** {municipio_seleccionado}")
                st.markdown(f"**Parroquia:** {parroquia_seleccionada}")
                if exito:
                    st.markdown(f"📧 *Notificación enviada al administrador*")
                else:
                    st.markdown(f"⚠️ *No se pudo enviar notificación: {mensaje}*")
                st.markdown('</div>', unsafe_allow_html=True)

# ==================== VER REGISTROS ====================
def ver_registros():
    st.markdown("### 📋 Registros del Censo")

    df = obtener_todos()

    if df.empty:
        st.info("📭 No hay registros en el censo.")
    else:
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            paises = df['pais'].dropna().unique().tolist()
            filtro_pais = st.multiselect("Filtrar por país", paises)
        with col_f2:
            niveles = df['nivel_academico'].dropna().unique().tolist()
            filtro_nivel = st.multiselect("Filtrar por nivel académico", niveles)
        with col_f3:
            busqueda = st.text_input("Buscar por nombre o institución")

        df_filtrado = df.copy()
        if filtro_pais:
            df_filtrado = df_filtrado[df_filtrado['pais'].isin(filtro_pais)]
        if filtro_nivel:
            df_filtrado = df_filtrado[df_filtrado['nivel_academico'].isin(filtro_nivel)]
        if busqueda:
            df_filtrado = df_filtrado[
                df_filtrado['nombre_completo'].str.contains(busqueda, case=False, na=False) |
                df_filtrado['institucion'].str.contains(busqueda, case=False, na=False)
            ]

        st.markdown(f"**Mostrando {len(df_filtrado)} de {len(df)} registros**")

        columnas_mostrar = ['codigo', 'nombre_completo', 'profesion', 'institucion', 
                           'pais', 'ciudad', 'municipio', 'parroquia', 'nivel_academico', 'anos_experiencia', 'disponibilidad']
        st.dataframe(df_filtrado[columnas_mostrar], use_container_width=True, hide_index=True)

        csv = df_filtrado.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar registros filtrados (CSV)",
            data=csv,
            file_name=f"censo_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

# ==================== EDITAR REGISTRO ====================
def editar_registro():
    st.markdown("### ✏️ Editar Registro")

    df = obtener_todos()

    if df.empty:
        st.info("📭 No hay registros para editar.")
        return

    codigo = st.selectbox("Selecciona un registro por código", df['codigo'].tolist())

    if codigo:
        row = obtener_por_id(codigo)
        if row:
            with st.form("formulario_edicion"):
                st.markdown(f"#### Editando: {row[2]} ({row[1]})")

                col1, col2 = st.columns(2)
                with col1:
                    nombre = st.text_input("Nombre completo", value=row[3])
                    correo = st.text_input("Correo electrónico", value=row[4])
                    telefono = st.text_input("Teléfono", value=row[5] if row[5] else "")
                    profesion = st.text_input("Profesión", value=row[10])
                    institucion = st.text_input("Institución", value=row[12])
                    pais = st.text_input("País", value=row[8])
                    ciudad = st.text_input("Ciudad", value=row[9])

                    municipio_actual = row[20] if row[20] else ""
                    municipio_seleccionado = st.selectbox(
                        "Municipio",
                        [""] + list(MUNICIPIOS_SUCRE.keys()),
                        index=([""] + list(MUNICIPIOS_SUCRE.keys())).index(municipio_actual) if municipio_actual in MUNICIPIOS_SUCRE else 0
                    )

                    parroquia_actual = row[21] if row[21] else ""
                    parroquia_seleccionada = st.selectbox(
                        "Parroquia",
                        [""] + PARROQUIAS_VENEZUELA,
                        index=([""] + PARROQUIAS_VENEZUELA).index(parroquia_actual) if parroquia_actual in PARROQUIAS_VENEZUELA else 0
                    )

                with col2:
                    nivel_academico = st.selectbox("Nivel académico", 
                        ["Técnico", "Licenciatura", "Maestría", "Doctorado", "Posdoctorado"],
                        index=["Técnico", "Licenciatura", "Maestría", "Doctorado", "Posdoctorado"].index(row[11]) if row[11] in ["Técnico", "Licenciatura", "Maestría", "Doctorado", "Posdoctorado"] else 0)
                    anos_exp = st.number_input("Años de experiencia", min_value=0, max_value=50, value=row[13] if row[13] else 0)

                    disponibilidad_opciones = [
                        "Tiempo completo", "Medio tiempo (mañana)", "Medio tiempo (tarde)",
                        "Fines de semana", "Disponibilidad inmediata", "No disponible actualmente"
                    ]
                    disponibilidad = st.selectbox("Disponibilidad de tiempo",
                        disponibilidad_opciones,
                        index=disponibilidad_opciones.index(row[18]) if row[18] in disponibilidad_opciones else 0)

                comentarios = st.text_area("Comentarios", value=row[22] if row[22] else "")

                submitted = st.form_submit_button("💾 Actualizar Registro")

                if submitted:
                    datos = (nombre, correo, telefono, row[6], row[7], pais, ciudad,
                            profesion, nivel_academico, institucion, anos_exp,
                            row[14], row[15], row[16], row[17], disponibilidad,
                            row[19], municipio_seleccionado, parroquia_seleccionada, comentarios)
                    actualizar_cientifico(codigo, datos)
                    st.success(f"✅ Registro {codigo} actualizado correctamente.")

# ==================== ELIMINAR REGISTRO ====================
def eliminar_registro():
    st.markdown("### 🗑️ Eliminar Registro")
    st.warning("⚠️ Esta acción no se puede deshacer.")

    df = obtener_todos()

    if df.empty:
        st.info("📭 No hay registros para eliminar.")
        return

    codigo = st.selectbox("Selecciona el registro a eliminar", df['codigo'].tolist())

    if codigo:
        registro = df[df['codigo'] == codigo].iloc[0]
        st.markdown("#### Registro seleccionado:")
        st.json(registro.to_dict())

        confirmacion = st.text_input("Escribe ELIMINAR para confirmar:")

        if st.button("🗑️ Eliminar permanentemente", type="primary"):
            if confirmacion == "ELIMINAR":
                eliminar_cientifico(codigo)
                st.success(f"✅ Registro {codigo} eliminado correctamente.")
                st.rerun()
            else:
                st.error("❌ Debes escribir ELIMINAR para confirmar.")

# ==================== MAPA ====================
def mostrar_mapa():
    st.markdown("### 🗺️ Mapa de Ubicaciones de Científicos")
    st.info("ℹ️ El mapa muestra las ubicaciones basadas en el municipio del estado Sucre.")

    df = obtener_todos()

    if df.empty:
        st.info("📭 No hay registros para mostrar.")
        return

    m = folium.Map(location=[10.5, -63.2], zoom_start=8)

    coordenadas_municipios = {
        "Andrés Eloy Blanco (Casanay)": [10.4, -63.5],
        "Andrés Mata (San José de Areocuar)": [10.3, -63.8],
        "Arismendi (Río Caribe)": [10.7, -63.1],
        "Benítez (El Pilar)": [10.2, -63.6],
        "Bermúdez (Carúpano)": [10.7, -63.2],
        "Bolívar (Marigüitar)": [10.5, -63.8],
        "Cajigal (Yaguaraparo)": [10.6, -63.0],
        "Cruz Salmerón Acosta (Araya)": [10.6, -64.6],
        "Libertador (Tunapuy)": [10.4, -63.1],
        "Mariño (Irapa)": [10.6, -62.6],
        "Mejía (San Antonio del Golfo)": [10.8, -62.3],
        "Montes (Cumanacoa)": [10.3, -63.9],
        "Ribero (Cariaco)": [10.3, -63.3],
        "Sucre (Cumaná)": [10.5, -64.2],
        "Valdez (Güiria)": [10.6, -62.3]
    }

    colores_municipios = {
        "Andrés Eloy Blanco (Casanay)": "red",
        "Andrés Mata (San José de Areocuar)": "blue",
        "Arismendi (Río Caribe)": "green",
        "Benítez (El Pilar)": "orange",
        "Bermúdez (Carúpano)": "purple",
        "Bolívar (Marigüitar)": "pink",
        "Cajigal (Yaguaraparo)": "cadetblue",
        "Cruz Salmerón Acosta (Araya)": "lightred",
        "Libertador (Tunapuy)": "darkblue",
        "Mariño (Irapa)": "darkgreen",
        "Mejía (San Antonio del Golfo)": "darkpurple",
        "Montes (Cumanacoa)": "darkred",
        "Ribero (Cariaco)": "lightblue",
        "Sucre (Cumaná)": "lightgray",
        "Valdez (Güiria)": "black"
    }

    for _, row in df.iterrows():
        municipio = row['municipio']
        if municipio and municipio in coordenadas_municipios:
            coords = coordenadas_municipios[municipio]
            color = colores_municipios.get(municipio, "gray")

            popup_text = f"""
            <b>{row['nombre_completo']}</b><br>
            {row['profesion']}<br>
            {row['institucion']}<br>
            <b>Municipio:</b> {municipio}<br>
            <b>Parroquia:</b> {row['parroquia']}<br>
            <i>{row['area_especializacion']}</i>
            """
            folium.Marker(
                location=coords,
                popup=folium.Popup(popup_text, max_width=300),
                tooltip=f"{row['nombre_completo']}",
                icon=folium.Icon(color=color, icon='info-sign')
            ).add_to(m)

    st_folium(m, width=700, height=500)

    st.markdown("---")
    st.markdown(f"**Total de científicos registrados:** {len(df)}")

# ==================== ESTADÍSTICAS ====================
def estadisticas():
    st.markdown("### 📈 Estadísticas del Censo")

    df = obtener_todos()

    if df.empty:
        st.info("📭 No hay datos suficientes.")
        return

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.metric("Total de científicos", len(df))
    with col_m2:
        st.metric("Municipios representados", df['municipio'].nunique())
    with col_m3:
        exp_prom = df['anos_experiencia'].mean()
        st.metric("Experiencia promedio (años)", f"{exp_prom:.1f}")
    with col_m4:
        con_misiones = len(df[df['misiones_campo'] == 'Sí'])
        st.metric("Con experiencia en campo", con_misiones)

    st.markdown("---")

    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.markdown("#### Distribución por municipio")
        municipio_counts = df['municipio'].value_counts().head(10)
        st.bar_chart(municipio_counts)

    with col_g2:
        st.markdown("#### Distribución por nivel académico")
        nivel_counts = df['nivel_academico'].value_counts()
        st.bar_chart(nivel_counts)

    st.markdown("---")

    col_g3, col_g4 = st.columns(2)
    with col_g3:
        st.markdown("#### Disponibilidad de tiempo")
        disp_counts = df['disponibilidad'].value_counts()
        st.bar_chart(disp_counts)

    with col_g4:
        st.markdown("#### Experiencia en campo")
        mision_counts = df['misiones_campo'].value_counts()
        st.bar_chart(mision_counts)

# ==================== GENERAR PDF ====================
def generar_pdf():
    st.markdown("### 📄 Generar Reporte PDF")

    df = obtener_todos()

    if df.empty:
        st.info("📭 No hay registros para generar el PDF.")
        return

    st.markdown("Selecciona los filtros para el reporte:")

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        paises = df['pais'].dropna().unique().tolist()
        filtro_pais = st.multiselect("Filtrar por país", paises)
    with col_f2:
        niveles = df['nivel_academico'].dropna().unique().tolist()
        filtro_nivel = st.multiselect("Filtrar por nivel académico", niveles)

    df_reporte = df.copy()
    if filtro_pais:
        df_reporte = df_reporte[df_reporte['pais'].isin(filtro_pais)]
    if filtro_nivel:
        df_reporte = df_reporte[df_reporte['nivel_academico'].isin(filtro_nivel)]

    st.markdown(f"**El PDF incluirá {len(df_reporte)} registros**")

    if st.button("📄 Generar PDF para imprimir"):
        if df_reporte.empty:
            st.warning("No hay registros con los filtros seleccionados.")
        else:
            with st.spinner("Generando PDF..."):
                try:
                    pdf_path = generar_pdf_censo(df_reporte)

                    with open(pdf_path, "rb") as f:
                        pdf_bytes = f.read()

                    st.success("✅ PDF generado correctamente")
                    st.download_button(
                        label="📥 Descargar PDF",
                        data=pdf_bytes,
                        file_name=f"censo_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                        mime="application/pdf",
                        key="download_pdf"
                    )

                    st.info("💡 Descarga el PDF y ábrelo con tu visor de PDF para imprimir.")

                except Exception as e:
                    st.error(f"❌ Error al generar el PDF: {str(e)}")
                    st.info("💡 Intenta refrescar la página y volver a intentar.")

# ==================== CONFIGURACIÓN ADMIN ====================
def configuracion_admin():
    st.markdown("### ⚙️ Configuración de Administrador")

    st.markdown("#### Cambiar contraseña")
    actual = st.text_input("Contraseña actual", type="password")
    nueva = st.text_input("Nueva contraseña", type="password")
    confirmar = st.text_input("Confirmar nueva contraseña", type="password")

    if st.button("🔑 Cambiar contraseña"):
        if not verify_admin(actual):
            st.error("❌ Contraseña actual incorrecta")
        elif nueva != confirmar:
            st.error("❌ Las contraseñas no coinciden")
        elif len(nueva) < 6:
            st.error("❌ La contraseña debe tener al menos 6 caracteres")
        else:
            change_admin_password(nueva)
            st.success("✅ Contraseña actualizada correctamente")

    st.markdown("---")

    st.markdown("#### Configuración de correo Gmail")
    st.info("📧 Configura el correo para recibir notificaciones de nuevos registros.")

    email = st.text_input("Correo Gmail del administrador", value="tucorreo@gmail.com")
    email_pass = st.text_input("Contraseña de aplicación Gmail", type="password", 
                               help="No es tu contraseña normal. Es la de 16 caracteres que generas en myaccount.google.com")

    if st.button("💾 Guardar configuración de correo"):
        update_admin_email(email, email_pass)
        st.success("✅ Configuración de correo guardada")
        st.info("ℹ️ Ahora recibirás notificaciones cuando se registre un nuevo científico.")

# ==================== RUTEO DEL MENÚ ====================
if menu == "🔐 Acceso Administrador":
    admin_login()
elif menu == "🔒 Cerrar Sesión":
    cerrar_sesion()
elif menu == "📝 Registrar Científico":
    formulario_registro()
elif menu == "📋 Ver Registros":
    ver_registros()
elif menu == "✏️ Editar Registro":
    if st.session_state.admin_logged_in:
        editar_registro()
    else:
        st.error("🔒 Acceso restringido. Inicia sesión como administrador.")
elif menu == "🗑️ Eliminar Registro":
    if st.session_state.admin_logged_in:
        eliminar_registro()
    else:
        st.error("🔒 Acceso restringido. Inicia sesión como administrador.")
elif menu == "🗺️ Mapa de Ubicaciones":
    mostrar_mapa()
elif menu == "📈 Estadísticas":
    estadisticas()
elif menu == "📄 Generar PDF":
    generar_pdf()
elif menu == "⚙️ Configuración Admin":
    if st.session_state.admin_logged_in:
        configuracion_admin()
    else:
        st.error("🔒 Acceso restringido. Inicia sesión como administrador.")
