CSS_STYLES = """
<style>
    /* ========== ROOT: PALETA DE COLORES ELEGANTE Y MODERNA ========== */
    :root {
        --primary-color: #7c3aed;
        --primary-hover: #6d28d9;
        --accent-color: #f59e0b;
        --accent-secondary: #ec4899;
        --success-color: #10b981;
        --text-primary: #f8fafc;
        --text-secondary: #cbd5e1;
        --bg-dark: #0b0f19;
        --glass-bg: rgba(11, 15, 25, 0.65);
        --glass-border: rgba(255, 255, 255, 0.08);
        --shadow-3d: 0 25px 40px -12px rgba(124, 58, 237, 0.25);
        --shadow-hover: 0 30px 55px -12px rgba(124, 58, 237, 0.4);
        --success-gradient: linear-gradient(135deg, #f59e0b 0%, #ec4899 50%, #7c3aed 100%);
        --input-bg: rgba(15, 23, 42, 0.6);
        --input-bg-focus: rgba(30, 41, 59, 0.9);
        --table-header-bg: linear-gradient(135deg, rgba(124,58,237,0.9) 0%, rgba(236,72,153,0.9) 100%);
        --table-row-hover: rgba(124, 58, 237, 0.15);
        --badge-bg: var(--success-gradient);
        --badge-color: #ffffff;
    }

    /* Importación de fuentes modernas */
    @import url('https://fonts.googleapis.com/css2?family=Inter:opsz,wght@14..32,100..900&family=Space+Grotesk:wght@300..700&display=swap');

    /* ========== ESTILO BASE DE LA APP ========== */
    .stApp {
        background: radial-gradient(ellipse at 20% 30%, #0f172a 0%, #020617 100%);
        font-family: 'Inter', 'Space Grotesk', system-ui, sans-serif;
    }

    /* ========== EFECTO DE FONDO DINÁMICO ========== */
    .stApp::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: 
            radial-gradient(circle at 10% 20%, rgba(124,58,237,0.08) 0%, transparent 50%),
            radial-gradient(circle at 90% 70%, rgba(236,72,153,0.06) 0%, transparent 50%),
            radial-gradient(circle at 50% 50%, rgba(245,158,11,0.04) 0%, transparent 80%);
        pointer-events: none;
        z-index: 0;
    }

    /* ========== MENSAJES CON EFECTO JASPEADO ========== */
    .stAlert[data-testid="stAlert"] {
        background: linear-gradient(135deg, rgba(124,58,237,0.2), rgba(236,72,153,0.15), rgba(245,158,11,0.1)) !important;
        backdrop-filter: blur(16px) !important;
        border: 1px solid rgba(255,255,255,0.15) !important;
        border-radius: 24px !important;
        box-shadow: 0 15px 35px rgba(124,58,237,0.2), inset 0 1px 0 rgba(255,255,255,0.1) !important;
        animation: slideInDown 0.5s cubic-bezier(0.34, 1.2, 0.64, 1) !important;
        color: #fff !important;
        font-weight: 500;
    }

    @keyframes slideInDown {
        from { opacity: 0; transform: translateY(-40px) scale(0.96); }
        to { opacity: 1; transform: translateY(0) scale(1); }
    }

    /* ========== SIDEBAR CON EFECTO GLASS ========== */
    .css-1d391kg, .css-1lcbmhc, [data-testid="stSidebar"] {
        background: rgba(11, 15, 25, 0.7) !important;
        backdrop-filter: blur(24px) !important;
        border-right: 1px solid rgba(255,255,255,0.08) !important;
        box-shadow: var(--shadow-3d) !important;
    }

    /* ========== TÍTULOS CON EFECTO NEON ========== */
    h1, h2, h3 {
        color: var(--text-primary);
        font-weight: 700;
        letter-spacing: -0.02em;
        background: linear-gradient(135deg, #fff 30%, #cbd5e1 70%);
        background-clip: text;
        -webkit-background-clip: text;
        color: transparent;
        position: relative;
        display: inline-block;
        font-family: 'Space Grotesk', 'Inter', sans-serif;
    }

    h1::after, h2::after {
        content: '';
        position: absolute;
        bottom: -8px;
        left: 0;
        width: 60%;
        height: 3px;
        background: var(--success-gradient);
        border-radius: 3px;
        transform: scaleX(0);
        transform-origin: left;
        transition: transform 0.4s ease;
    }

    h1:hover::after, h2:hover::after {
        transform: scaleX(1);
    }

    /* ========== TEXTO DE SUBTÍTULO ELEGANTE ========== */
    .subtitle-script {
        color: var(--text-secondary);
        margin-top: -8px;
        font-family: 'Space Grotesk', monospace;
        font-size: 0.95rem;
        letter-spacing: 1px;
        font-weight: 300;
        text-transform: uppercase;
        opacity: 0.8;
    }

    /* ========== TARJETAS CON EFECTO JASPEADO Y BRILLO ========== */
    .info-card, .student-info, .stDataFrame, .student-search-card {
        background: linear-gradient(135deg, rgba(15,23,42,0.7), rgba(30,41,59,0.5));
        backdrop-filter: blur(20px);
        border-radius: 28px;
        border: 1px solid rgba(255,255,255,0.1);
        box-shadow: var(--shadow-3d);
        transition: all 0.4s cubic-bezier(0.2, 0.9, 0.4, 1.1);
        position: relative;
        overflow: hidden;
    }

    /* Efecto jaspeado animado en las tarjetas */
    .info-card::before, .student-info::before, .stDataFrame::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(124,58,237,0.15) 0%, rgba(236,72,153,0.08) 30%, rgba(245,158,11,0.05) 70%, transparent);
        transform: rotate(25deg);
        transition: all 0.6s ease;
        opacity: 0;
        pointer-events: none;
    }

    .info-card:hover::before, .student-info:hover::before, .stDataFrame:hover::before {
        opacity: 1;
        animation: marbleShift 4s infinite linear;
    }

    @keyframes marbleShift {
        0% { transform: rotate(25deg) translate(-10%, -10%); }
        50% { transform: rotate(25deg) translate(10%, 10%); }
        100% { transform: rotate(25deg) translate(-10%, -10%); }
    }

    .info-card:hover, .student-info:hover, .stDataFrame:hover, .student-search-card:hover {
        transform: translateY(-6px);
        box-shadow: var(--shadow-hover);
        border-color: rgba(124,58,237,0.4);
    }

    /* ========== BOTONES CON EFECTO JASPEADO Y 3D ========== */
    .stButton button {
        background: linear-gradient(135deg, #7c3aed 0%, #c026d3 50%, #f59e0b 100%);
        background-size: 200% 200%;
        color: white;
        border: none;
        border-radius: 16px;
        padding: 0.7rem 1.8rem;
        font-weight: 600;
        font-size: 0.9rem;
        transition: all 0.35s cubic-bezier(0.2, 0.9, 0.4, 1.2);
        position: relative;
        overflow: hidden;
        box-shadow: 0 8px 20px rgba(124,58,237,0.3);
        border-bottom: 2px solid rgba(255,255,255,0.2);
        font-family: 'Space Grotesk', monospace;
        letter-spacing: 0.5px;
        animation: gradientShift 3s ease infinite;
    }

    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    /* Efecto de brillo deslizante en botones */
    .stButton button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.25), transparent);
        transition: left 0.6s;
    }

    .stButton button:hover::before {
        left: 100%;
    }

    .stButton button:hover {
        transform: translateY(-4px) scale(1.03);
        box-shadow: 0 15px 35px rgba(124,58,237,0.5);
        filter: brightness(1.05);
    }

    .stButton button:active {
        transform: translateY(2px);
    }

    /* ========== RADIO BUTTONS MODERNOS ========== */
    div.row-widget.stRadio > div {
        display: flex;
        flex-direction: row;
        justify-content: center;
        gap: 0.5rem;
        background: rgba(11, 15, 25, 0.6);
        backdrop-filter: blur(20px);
        padding: 0.5rem;
        border-radius: 60px;
        box-shadow: var(--shadow-3d);
        margin-bottom: 2rem;
        border: 1px solid rgba(255,255,255,0.08);
    }

    div.row-widget.stRadio > div label {
        background: transparent;
        color: var(--text-secondary);
        font-weight: 500;
        padding: 0.6rem 1.4rem;
        border-radius: 50px;
        transition: all 0.3s ease;
        cursor: pointer;
        font-size: 0.9rem;
        font-family: 'Inter', sans-serif;
    }

    div.row-widget.stRadio > div label:hover {
        background: rgba(124,58,237,0.2);
        color: #f59e0b;
        transform: translateY(-2px);
    }

    div.row-widget.stRadio > div label[data-testid="stRadioLabel"]:has(input:checked) {
        background: linear-gradient(135deg, #7c3aed, #ec4899);
        color: white;
        box-shadow: 0 5px 15px rgba(124,58,237,0.4);
        font-weight: 600;
    }

    /* ========== INPUTS CON EFECTO GLASS ========== */
    .stTextInput input, .stSelectbox div[data-baseweb="select"], .stNumberInput input {
        background: var(--input-bg) !important;
        border: 1px solid rgba(255,255,255,0.12) !important;
        border-radius: 16px !important;
        color: var(--text-primary) !important;
        padding: 0.8rem 1rem !important;
        backdrop-filter: blur(8px) !important;
        font-family: 'Inter', sans-serif;
        transition: all 0.3s ease;
    }

    .stTextInput input:focus, .stSelectbox div[data-baseweb="select"]:focus, .stNumberInput input:focus {
        background: var(--input-bg-focus) !important;
        border-color: #7c3aed !important;
        box-shadow: 0 0 0 4px rgba(124,58,237,0.2) !important;
        transform: scale(1.01);
    }

    /* ========== TABLAS MODERNAS ========== */
    .stDataFrame {
        padding: 0;
        overflow: hidden;
        border-radius: 20px;
    }

    .stDataFrame table {
        width: 100%;
        border-collapse: collapse;
        color: var(--text-primary);
        font-family: 'Inter', sans-serif;
    }

    .stDataFrame thead tr th {
        background: var(--table-header-bg) !important;
        color: white !important;
        font-weight: 600;
        padding: 1rem 1rem !important;
        border: none !important;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .stDataFrame tbody tr {
        transition: all 0.3s ease;
        border-bottom: 1px solid rgba(255,255,255,0.05);
    }

    .stDataFrame tbody tr:hover {
        background: var(--table-row-hover);
        transform: translateX(4px);
    }

    .stDataFrame tbody td {
        padding: 0.8rem 1rem !important;
        border: none !important;
    }

    /* ========== SCROLLBAR PERSONALIZADA ========== */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    ::-webkit-scrollbar-track {
        background: rgba(255,255,255,0.05);
        border-radius: 10px;
    }
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #7c3aed, #ec4899);
        border-radius: 10px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #8b5cf6, #f472b6);
    }

    /* ========== ANIMACIONES DE ENTRADA ========== */
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(25px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes glowPulse {
        0% { box-shadow: 0 0 0 0 rgba(124,58,237,0.4); }
        70% { box-shadow: 0 0 0 10px rgba(124,58,237,0); }
        100% { box-shadow: 0 0 0 0 rgba(124,58,237,0); }
    }

    .stAlert, .stButton button, .stDataFrame, .info-card, .student-info {
        animation: fadeInUp 0.5s ease-out;
    }
    
    /* ========== TARJETA DE ESTUDIANTE CON DESTAQUE ========== */
    .student-name {
        font-size: 2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #f59e0b, #ec4899, #7c3aed);
        background-clip: text;
        -webkit-background-clip: text;
        color: transparent;
        margin-bottom: 0.5rem;
        text-transform: uppercase;
    }
    
    .student-ru {
        font-size: 1.2rem;
        color: var(--text-secondary);
        margin-bottom: 1.2rem;
        letter-spacing: 2px;
        font-family: monospace;
    }

    /* ========== QR CON EFECTO BRILLANTE ========== */
    .qr-container img {
        border-radius: 20px;
        box-shadow: var(--shadow-3d);
        transition: all 0.4s ease;
        border: 1px solid rgba(255,255,255,0.2);
    }
    .qr-container img:hover {
        transform: scale(1.02);
        box-shadow: 0 20px 40px rgba(124,58,237,0.3);
    }

    /* ========== DASHBOARD COMPACTO MEJORADO ========== */
    .dashboard-compact {
        display: flex;
        gap: 1rem;
        margin-bottom: 1.5rem;
        flex-wrap: wrap;
    }
    .dashboard-card {
        flex: 1;
        min-width: 110px;
        background: linear-gradient(135deg, rgba(15,23,42,0.7), rgba(30,41,59,0.5));
        backdrop-filter: blur(12px);
        border-radius: 24px;
        padding: 0.8rem 1rem;
        text-align: center;
        border: 1px solid rgba(255,255,255,0.1);
        box-shadow: var(--shadow-3d);
        transition: all 0.35s ease;
    }
    .dashboard-card:hover {
        transform: translateY(-5px);
        border-color: rgba(124,58,237,0.4);
        box-shadow: var(--shadow-hover);
    }
    .dashboard-card .title {
        font-size: 0.7rem;
        font-weight: 600;
        color: var(--text-secondary);
        margin-bottom: 0.3rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .dashboard-card .value {
        font-size: 1.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #fff, #cbd5e1);
        background-clip: text;
        -webkit-background-clip: text;
        color: transparent;
        line-height: 1.2;
    }
    .progress-bar-bg {
        background: rgba(255,255,255,0.1);
        border-radius: 20px;
        height: 6px;
        width: 100%;
        margin-top: 0.6rem;
        overflow: hidden;
    }
    .progress-bar-fill {
        height: 100%;
        border-radius: 20px;
        transition: width 0.7s cubic-bezier(0.2, 0.9, 0.4, 1.2);
    }
    .green-card .progress-bar-fill {
        background: linear-gradient(90deg, #10b981, #34d399);
        box-shadow: 0 0 8px #34d399;
    }
    .orange-card .progress-bar-fill {
        background: linear-gradient(90deg, #f59e0b, #fbbf24);
        box-shadow: 0 0 8px #fbbf24;
    }
    .blue-card .progress-bar-fill {
        background: linear-gradient(90deg, #3b82f6, #60a5fa);
        box-shadow: 0 0 8px #60a5fa;
    }
    .green-card {
        border-left: 3px solid #10b981;
    }
    .orange-card {
        border-left: 3px solid #f59e0b;
    }
    .blue-card {
        border-left: 3px solid #3b82f6;
    }

    /* ========== RESPONSIVE ========== */
    @media (max-width: 768px) {
        .dashboard-card .value {
            font-size: 1.2rem;
        }
        .dashboard-card .title {
            font-size: 0.6rem;
        }
        .dashboard-card {
            padding: 0.5rem;
        }
        .stButton button {
            padding: 0.5rem 1.2rem;
            font-size: 0.8rem;
        }
    }
</style>
"""
