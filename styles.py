CSS_STYLES = """
<style>
    :root {
        --primary-color: #0066ff;
        --primary-hover: #0052cc;
        --accent-color: #00ffcc;
        --text-primary: #f8fafc;
        --text-secondary: #cbd5e1;
        --bg-dark: #0f172a;
        --glass-bg: rgba(15, 23, 42, 0.7);
        --glass-border: rgba(255, 255, 255, 0.1);
        --shadow-3d: 0 10px 25px -5px rgba(0, 102, 255, 0.2), 0 10px 10px -5px rgba(0, 102, 255, 0.1);
        --shadow-hover: 0 20px 50px -10px rgba(0, 102, 255, 0.4);
        --success-gradient: linear-gradient(135deg, #00ffcc 0%, #0066ff 100%);
        --input-bg: rgba(15, 23, 42, 0.5);
        --input-bg-focus: rgba(15, 23, 42, 0.8);
        --table-header-bg: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
        --table-row-hover: rgba(0, 102, 255, 0.1);
        --badge-bg: var(--success-gradient);
        --badge-color: #020617;
    }

    @import url('https://fonts.googleapis.com/css2?family=Inter:opsz,wght@14..32,100..900&display=swap');

    .stApp {
        background-color: var(--bg-dark);
        font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
    }

    /* Estilo mejorado para mensajes de éxito */
    .stAlert[data-testid="stAlert"] {
        background: linear-gradient(135deg, rgba(0,102,255,0.15), rgba(0,51,204,0.1)) !important;
        backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(0,255,204,0.3) !important;
        border-radius: 20px !important;
        box-shadow: 0 8px 20px rgba(0,102,255,0.2), inset 0 1px 0 rgba(255,255,255,0.1) !important;
        animation: slideInDown 0.4s cubic-bezier(0.2, 0.9, 0.4, 1.1) !important;
        color: #e6f7ff !important;
    }
    
    @keyframes slideInDown {
        from { opacity: 0; transform: translateY(-30px); }
        to { opacity: 1; transform: translateY(0); }
    }

    /* Sidebar */
    .css-1d391kg, .css-1lcbmhc {
        background: var(--glass-bg) !important;
        backdrop-filter: blur(20px) !important;
        border-right: 1px solid var(--glass-border) !important;
        box-shadow: var(--shadow-3d) !important;
    }

    /* Títulos */
    h1, h2, h3 {
        background: linear-gradient(135deg, #00ffcc 0%, #0066ff 100%);
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent !important;
        font-weight: 700;
        letter-spacing: -0.02em;
        position: relative;
        display: inline-block;
    }

    h1::after, h2::after {
        content: '';
        position: absolute;
        bottom: -10px;
        left: 0;
        width: 60px;
        height: 3px;
        background: var(--success-gradient);
        border-radius: 3px;
        transition: width 0.3s ease;
    }

    h1:hover::after, h2:hover::after {
        width: 100%;
    }

    .subtitle-script {
        color: var(--text-secondary);
        margin-top: -10px;
        font-family: 'Pacifico', 'Dancing Script', 'Brush Script MT', cursive;
        font-size: 1rem;
        letter-spacing: 0.5px;
    }

    /* Tarjetas */
    .student-search-card, .student-detail-card, .password-modal {
        background: var(--glass-bg);
        backdrop-filter: blur(20px);
        border-radius: 24px;
        border: 1px solid var(--glass-border);
        box-shadow: var(--shadow-3d);
        padding: 2rem;
        margin: 1.5rem 0;
        text-align: center;
        transition: all 0.3s ease;
    }
    
    .student-search-card:hover {
        transform: translateY(-5px);
        box-shadow: var(--shadow-hover);
        border-color: rgba(0, 102, 255, 0.3);
    }
    
    .student-name {
        font-size: 2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #00ffcc 0%, #0066ff 100%);
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent !important;
        margin-bottom: 0.5rem;
        text-transform: uppercase;
    }
    
    .student-ru {
        font-size: 1.3rem;
        color: var(--text-secondary);
        margin-bottom: 1.5rem;
        letter-spacing: 1px;
        text-transform: uppercase;
    }

    /* QR */
    .qr-container {
        display: flex;
        justify-content: center;
        margin: 1.5rem 0;
    }
    
    .qr-container img {
        border-radius: 16px;
        box-shadow: var(--shadow-3d);
        transition: transform 0.3s ease;
        max-width: 100%;
        height: auto;
    }
    
    .qr-container img:hover {
        transform: scale(1.02);
    }
    
    .qr-info {
        font-size: 1.3rem;
        font-weight: 600;
        background: linear-gradient(135deg, #00ffcc 0%, #0066ff 100%);
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent !important;
        text-align: center;
        margin-bottom: 0.5rem;
        text-transform: uppercase;
    }
    
    .qr-ru {
        font-size: 1.1rem;
        color: var(--text-secondary);
        text-align: center;
        margin-bottom: 1rem;
        text-transform: uppercase;
    }

    /* Menú horizontal */
    div.row-widget.stRadio > div {
        display: flex;
        flex-direction: row;
        justify-content: center;
        gap: 0.5rem;
        background: var(--glass-bg);
        backdrop-filter: blur(20px);
        padding: 0.5rem;
        border-radius: 60px;
        box-shadow: var(--shadow-3d);
        margin-bottom: 2rem;
        border: 1px solid var(--glass-border);
        flex-wrap: wrap;
    }

    div.row-widget.stRadio > div label {
        background: transparent;
        color: var(--text-secondary);
        font-weight: 500;
        padding: 0.5rem 1rem;
        border-radius: 40px;
        transition: all 0.3s ease;
        cursor: pointer;
        font-size: 0.85rem;
    }

    div.row-widget.stRadio > div label:hover {
        background: rgba(0, 102, 255, 0.2);
        color: var(--accent-color);
        transform: translateY(-2px);
    }

    div.row-widget.stRadio > div label[data-testid="stRadioLabel"]:has(input:checked) {
        background: var(--success-gradient);
        color: var(--badge-color);
        box-shadow: var(--shadow-3d);
        font-weight: 600;
    }

    /* Botones */
    .stButton button {
        background: linear-gradient(135deg, #0066ff 0%, #0052cc 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.6rem 1.5rem;
        font-weight: 600;
        font-size: 0.9rem;
        transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
        position: relative;
        overflow: hidden;
        box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
        cursor: pointer;
        width: 100%;
    }

    .stButton button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
        transition: left 0.5s;
    }

    .stButton button:hover::before {
        left: 100%;
    }

    .stButton button:hover {
        transform: translateY(-2px) scale(1.01);
        box-shadow: 0 8px 25px rgba(0, 102, 255, 0.4);
    }

    /* Inputs */
    .stTextInput input, .stSelectbox div[data-baseweb="select"], .stTextArea textarea {
        background: var(--input-bg) !important;
        border: 1px solid var(--glass-border) !important;
        border-radius: 12px !important;
        color: var(--text-primary) !important;
        padding: 0.7rem 1rem !important;
    }

    .stTextInput input:focus, .stSelectbox div[data-baseweb="select"]:focus {
        border-color: var(--primary-color) !important;
        box-shadow: 0 0 0 3px rgba(0, 102, 255, 0.2) !important;
    }

    /* ============================================
       TABLAS CON COLORES ELEGANTES - VERSIÓN CORREGIDA
    ============================================ */
    
    .stDataFrame {
        border-radius: 20px !important;
        overflow: hidden !important;
        background: transparent !important;
    }
    
    .stDataFrame table {
        width: 100%;
        border-collapse: collapse;
        border-radius: 20px;
        overflow: hidden;
    }
    
    /* Encabezados */
    .stDataFrame thead tr th {
        background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%) !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        font-size: 0.85rem !important;
        padding: 12px 16px !important;
        text-transform: uppercase;
        letter-spacing: 1px;
        text-align: center;
        border-bottom: 2px solid rgba(255, 255, 255, 0.1) !important;
    }
    
    /* Celdas base */
    .stDataFrame tbody td {
        padding: 10px 12px !important;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05) !important;
        transition: all 0.2s ease;
    }
    
    /* Columna Índice */
    .stDataFrame tbody tr td:first-child {
        background: rgba(100, 100, 120, 0.2) !important;
        color: #b8c6db !important;
        font-weight: 600;
        text-align: center;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    /* Columna RU */
    .stDataFrame tbody tr td:nth-child(2) {
        background: rgba(45, 106, 79, 0.25) !important;
        color: #74c69d !important;
        font-weight: 700;
        font-family: monospace;
        text-align: center;
    }
    
    /* Columna Nombres */
    .stDataFrame tbody tr td:nth-child(3) {
        background: rgba(0, 100, 200, 0.18) !important;
        color: #7bc5ff !important;
        font-weight: 600;
    }
    
    /* Columna Apellido Paterno */
    .stDataFrame tbody tr td:nth-child(4) {
        background: rgba(123, 44, 191, 0.18) !important;
        color: #c77dff !important;
        font-weight: 600;
    }
    
    /* Columna Apellido Materno */
    .stDataFrame tbody tr td:nth-child(5) {
        background: rgba(255, 180, 50, 0.12) !important;
        color: #ffd966 !important;
        font-weight: 600;
    }
    
    /* Columna Fecha (si existe) */
    .stDataFrame tbody tr td:nth-child(6) {
        background: rgba(255, 214, 10, 0.12) !important;
        color: #ffe066 !important;
        font-family: monospace;
    }
    
    /* Columna Hora (si existe) */
    .stDataFrame tbody tr td:nth-child(7) {
        background: rgba(0, 255, 200, 0.1) !important;
        color: #5fffd9 !important;
        font-family: monospace;
        font-weight: 600;
    }
    
    /* Columna Estado (si existe) */
    .stDataFrame tbody tr td:last-child {
        font-weight: 700;
        text-align: center;
    }
    
    /* Estados específicos */
    .stDataFrame tbody tr td:last-child:contains("Presente"),
    .stDataFrame tbody tr td:contains("Presente") {
        background: rgba(45, 106, 79, 0.35) !important;
        color: #95d5b2 !important;
    }
    
    .stDataFrame tbody tr td:contains("Tarde") {
        background: rgba(255, 160, 0, 0.25) !important;
        color: #ffb347 !important;
    }
    
    .stDataFrame tbody tr td:contains("Permiso") {
        background: rgba(0, 150, 255, 0.25) !important;
        color: #66b0ff !important;
    }
    
    .stDataFrame tbody tr td:contains("Ausente") {
        background: rgba(220, 53, 69, 0.25) !important;
        color: #ff8a92 !important;
    }
    
    /* Hover en filas */
    .stDataFrame tbody tr:hover td {
        background: rgba(82, 183, 136, 0.25) !important;
        transform: scale(1.001);
    }
    
    .stDataFrame tbody tr:hover td:first-child {
        background: rgba(100, 100, 120, 0.4) !important;
    }
    
    .stDataFrame tbody tr:hover td:nth-child(2) {
        background: rgba(45, 106, 79, 0.45) !important;
    }
    
    .stDataFrame tbody tr:hover td:nth-child(3) {
        background: rgba(0, 100, 200, 0.35) !important;
    }
    
    .stDataFrame tbody tr:hover td:nth-child(4) {
        background: rgba(123, 44, 191, 0.35) !important;
    }
    
    .stDataFrame tbody tr:hover td:nth-child(5) {
        background: rgba(255, 180, 50, 0.28) !important;
    }

    /* Dashboard de tarjetas */
    .dashboard-compact {
        display: flex;
        gap: 0.8rem;
        margin-bottom: 1.2rem;
        flex-wrap: wrap;
    }
    
    .dashboard-card {
        flex: 1;
        min-width: 100px;
        background: var(--glass-bg);
        backdrop-filter: blur(8px);
        border-radius: 20px;
        padding: 0.6rem 0.8rem;
        text-align: center;
        border: 1px solid var(--glass-border);
        box-shadow: var(--shadow-3d);
        transition: all 0.3s ease;
    }
    
    .dashboard-card:hover {
        transform: translateY(-3px);
        border-color: rgba(0,255,204,0.3);
    }
    
    .dashboard-card .title {
        font-size: 0.7rem;
        font-weight: 600;
        color: var(--text-secondary);
        margin-bottom: 0.2rem;
        text-transform: uppercase;
        letter-spacing: 0.8px;
    }
    
    .dashboard-card .value {
        font-size: 1.3rem;
        font-weight: 700;
        color: var(--text-primary);
        line-height: 1.2;
    }
    
    .dashboard-card .percentage {
        font-size: 0.65rem;
        color: var(--text-secondary);
        margin-top: 0.2rem;
    }
    
    .progress-bar-bg {
        background: rgba(255,255,255,0.15);
        border-radius: 20px;
        height: 5px;
        width: 100%;
        margin-top: 0.5rem;
        overflow: hidden;
    }
    
    .progress-bar-fill {
        height: 100%;
        border-radius: 20px;
        transition: width 0.6s cubic-bezier(0.2, 0.9, 0.4, 1.1);
    }
    
    .green-card .progress-bar-fill {
        background: linear-gradient(90deg, #00cc88, #00ffaa);
        box-shadow: 0 0 6px #00ffaa;
    }
    
    .orange-card .progress-bar-fill {
        background: linear-gradient(90deg, #ff884d, #ffaa66);
        box-shadow: 0 0 6px #ffaa66;
    }
    
    .blue-card .progress-bar-fill {
        background: linear-gradient(90deg, #3399ff, #66ccff);
        box-shadow: 0 0 6px #66ccff;
    }
    
    .green-card {
        background: radial-gradient(circle at 30% 40%, rgba(0,200,120,0.1), rgba(0,100,80,0.1));
        border-left: 3px solid #00ffaa;
    }
    
    .orange-card {
        background: radial-gradient(circle at 30% 40%, rgba(255,140,0,0.1), rgba(200,80,0,0.1));
        border-left: 3px solid #ffaa66;
    }
    
    .blue-card {
        background: radial-gradient(circle at 30% 40%, rgba(0,150,255,0.1), rgba(0,100,200,0.1));
        border-left: 3px solid #66ccff;
    }

    /* Cámara */
    div[data-testid="stCameraInput"] video {
        width: 100% !important;
        height: 60vh !important;
        object-fit: cover;
        border-radius: 16px;
        border: 2px solid var(--primary-color);
        box-shadow: var(--shadow-3d);
    }

    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
    }
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #0066ff, #00ffcc);
        border-radius: 10px;
    }

    /* Animaciones */
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .stAlert, .stButton, .stDataFrame, .student-search-card {
        animation: fadeInUp 0.5s ease-out;
    }

    /* Responsive */
    @media (max-width: 768px) {
        .dashboard-card .value {
            font-size: 1.1rem;
        }
        .dashboard-card .title {
            font-size: 0.65rem;
        }
        .dashboard-card {
            padding: 0.5rem 0.6rem;
        }
        div.row-widget.stRadio > div label {
            padding: 0.4rem 0.8rem;
            font-size: 0.7rem;
        }
        .stDataFrame thead tr th {
            font-size: 0.7rem;
            padding: 8px 6px !important;
        }
        .stDataFrame tbody td {
            font-size: 0.7rem;
            padding: 6px 4px !important;
        }
    }
</style>
"""
