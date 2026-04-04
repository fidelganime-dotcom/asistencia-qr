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
        --table-header-bg: linear-gradient(135deg, rgba(0,102,255,0.8) 0%, rgba(0,51,204,0.8) 100%);
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
        from {
            opacity: 0;
            transform: translateY(-30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    .css-1d391kg, .css-1lcbmhc {
        background: var(--glass-bg) !important;
        backdrop-filter: blur(20px) !important;
        border-right: 1px solid var(--glass-border) !important;
        box-shadow: var(--shadow-3d) !important;
    }

    h1, h2, h3 {
        color: var(--text-primary);
        font-weight: 700;
        letter-spacing: -0.02em;
        text-shadow: 0 2px 10px rgba(0, 102, 255, 0.3);
        position: relative;
        display: inline-block;
        font-family: 'Inter', system-ui, sans-serif;
    }

    h1::after, h2::after {
        content: '';
        position: absolute;
        bottom: -10px;
        left: 0;
        width: 100%;
        height: 3px;
        background: var(--success-gradient);
        border-radius: 3px;
        transform: scaleX(0);
        transform-origin: left;
        transition: transform 0.3s ease;
    }

    h1:hover::after, h2:hover::after {
        transform: scaleX(1);
    }

    .subtitle-script {
        color: var(--text-secondary);
        margin-top: -10px;
        font-family: 'Pacifico', 'Dancing Script', 'Brush Script MT', cursive;
        font-size: 1.1rem;
        letter-spacing: 0.5px;
        font-weight: normal;
        text-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }

    .student-search-card {
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
        color: var(--accent-color);
        margin-bottom: 0.5rem;
        text-shadow: 0 0 10px rgba(0,255,204,0.3);
        text-transform: uppercase;
    }
    .student-ru {
        font-size: 1.3rem;
        color: var(--text-secondary);
        margin-bottom: 1.5rem;
        letter-spacing: 1px;
        text-transform: uppercase;
    }
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
    .download-buttons {
        display: flex;
        gap: 1rem;
        justify-content: center;
        margin-top: 1.5rem;
    }
    .info-card, .student-info, .stDataFrame {
        background: var(--glass-bg);
        backdrop-filter: blur(20px);
        border-radius: 16px;
        border: 1px solid var(--glass-border);
        box-shadow: var(--shadow-3d);
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
        position: relative;
        overflow: hidden;
    }

    .info-card::before, .student-info::before, .stDataFrame::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(0,102,255,0.1) 0%, rgba(0,102,255,0) 70%);
        transform: rotate(30deg);
        transition: all 0.5s ease;
        opacity: 0;
        pointer-events: none;
    }

    .info-card:hover::before, .student-info:hover::before, .stDataFrame:hover::before {
        opacity: 1;
        animation: shine 3s infinite;
    }

    @keyframes shine {
        0% { transform: rotate(30deg) translate(-10%, -10%); }
        100% { transform: rotate(30deg) translate(10%, 10%); }
    }

    .info-card:hover, .student-info:hover, .stDataFrame:hover {
        transform: translateY(-5px);
        box-shadow: var(--shadow-hover);
        border-color: rgba(0, 102, 255, 0.3);
    }

    div.row-widget.stRadio > div {
        display: flex;
        flex-direction: row;
        justify-content: center;
        gap: 0.75rem;
        background: var(--glass-bg);
        backdrop-filter: blur(20px);
        padding: 0.5rem;
        border-radius: 60px;
        box-shadow: var(--shadow-3d);
        margin-bottom: 2rem;
        border: 1px solid var(--glass-border);
    }

    div.row-widget.stRadio > div label {
        background: transparent;
        color: var(--text-secondary);
        font-weight: 500;
        padding: 0.6rem 1.2rem;
        border-radius: 40px;
        transition: all 0.3s ease;
        cursor: pointer;
        font-size: 0.9rem;
        font-family: 'Inter', system-ui, sans-serif;
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

    .stButton button {
        background: linear-gradient(135deg, #0a2f1f, #0e4d2e, #166534);
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
        border-bottom: 3px solid rgba(0, 0, 0, 0.2);
        font-family: 'Inter', system-ui, sans-serif;
    }

    .stButton button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
        transition: left 0.7s;
    }

    .stButton button:hover::before {
        left: 100%;
    }

    .stButton button:hover {
        background: var(--primary-hover);
        transform: translateY(-3px) scale(1.02);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
    }

    .stTextInput input, .stSelectbox div[data-baseweb="select"] {
        background: var(--input-bg) !important;
        border: 1px solid var(--glass-border) !important;
        border-radius: 12px !important;
        color: var(--text-primary) !important;
        padding: 0.75rem 1rem !important;
        backdrop-filter: blur(5px) !important;
        font-family: 'Inter', system-ui, sans-serif;
    }

    .stTextInput input:focus, .stSelectbox div[data-baseweb="select"]:focus {
        background: var(--input-bg-focus) !important;
        border-color: var(--primary-color) !important;
        box-shadow: 0 0 0 3px rgba(0, 102, 255, 0.2) !important;
        transform: scale(1.01);
    }

    .stDataFrame {
        padding: 0;
        overflow: hidden;
    }

    .stDataFrame table {
        width: 100%;
        border-collapse: collapse;
        color: var(--text-primary);
        font-family: 'Inter', system-ui, sans-serif;
    }

    .stDataFrame thead tr th {
        background: var(--table-header-bg) !important;
        color: white !important;
        font-weight: 600;
        padding: 1rem 1rem !important;
        border: none !important;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .stDataFrame tbody tr {
        transition: all 0.3s ease;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    }

    .stDataFrame tbody tr:hover {
        background: var(--table-row-hover);
        transform: translateX(5px);
    }

    .stDataFrame tbody td {
        padding: 0.75rem 1rem !important;
        border: none !important;
    }

    .stAlert {
        background: var(--glass-bg) !important;
        backdrop-filter: blur(20px) !important;
        border: 1px solid var(--glass-border) !important;
        border-radius: 16px !important;
        color: var(--text-primary) !important;
        padding: 1rem !important;
        box-shadow: var(--shadow-3d) !important;
        font-family: 'Inter', system-ui, sans-serif;
    }

    div[data-testid="stCameraInput"] video {
        width: 100% !important;
        height: 70vh !important;
        object-fit: cover;
        border-radius: 16px;
        border: 2px solid var(--primary-color);
        box-shadow: var(--shadow-3d);
    }

    ::-webkit-scrollbar {
        width: 8px;
    }
    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.1);
    }
    ::-webkit-scrollbar-thumb {
        background: var(--primary-color);
        border-radius: 4px;
    }

    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .stAlert, .stButton, .stDataFrame, .info-card, .student-info {
        animation: fadeInUp 0.5s ease-out;
    }
    
    .qr-info {
        font-size: 1.3rem;
        font-weight: 600;
        color: var(--accent-color);
        text-align: center;
        margin-bottom: 0.5rem;
        letter-spacing: 0.5px;
        text-shadow: 0 0 8px rgba(0,255,204,0.3);
        text-transform: uppercase;
    }
    .qr-ru {
        font-size: 1.1rem;
        color: var(--text-secondary);
        text-align: center;
        margin-bottom: 1rem;
        text-transform: uppercase;
    }
    
    /* Estilos para la pantalla flotante de contraseña */
    .password-modal {
        background: var(--glass-bg);
        backdrop-filter: blur(20px);
        border-radius: 24px;
        border: 1px solid var(--glass-border);
        box-shadow: var(--shadow-3d);
        padding: 2rem;
        margin: 2rem auto;
        max-width: 500px;
        text-align: center;
        animation: fadeInUp 0.4s ease-out;
    }
    .password-modal h3 {
        margin-top: 0;
        margin-bottom: 1rem;
    }
    .password-modal input {
        width: 100%;
        background: var(--input-bg);
        border: 1px solid var(--glass-border);
        border-radius: 12px;
        padding: 0.75rem;
        color: var(--text-primary);
        margin-bottom: 1rem;
    }
    .password-modal button {
        background: var(--primary-color);
        border: none;
        border-radius: 12px;
        padding: 0.6rem 1.5rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        color: white;
    }
    .password-modal button:hover {
        background: var(--primary-hover);
        transform: translateY(-2px);
    }
    .password-error {
        color: #ff6b6b;
        margin-top: 0.5rem;
        font-size: 0.9rem;
    }

    /* Estilo para tarjeta de información del estudiante */
    .student-detail-card {
        background: var(--glass-bg);
        backdrop-filter: blur(12px);
        border-radius: 20px;
        border: 1px solid var(--glass-border);
        padding: 1rem;
        margin: 1rem 0;
        text-align: center;
        box-shadow: var(--shadow-3d);
    }
    .student-detail-card h4 {
        margin: 0 0 0.5rem 0;
        color: var(--accent-color);
    }
    .student-detail-card p {
        margin: 0.2rem 0;
        color: var(--text-primary);
    }

    /* Dashboard compacto - tres tarjetas */
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
    @media (max-width: 600px) {
        .dashboard-card .value {
            font-size: 1.1rem;
        }
        .dashboard-card .title {
            font-size: 0.65rem;
        }
        .dashboard-card {
            padding: 0.5rem 0.6rem;
        }
    }
</style>
"""
