<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover, user-scalable=yes">
    <title>UTR Móvil | Asistencia y Registros</title>
    <!-- Google Fonts + Font Awesome 6 -->
    <link href="https://fonts.googleapis.com/css2?family=Inter:opsz,wght@14..32,300;14..32,400;14..32,500;14..32,600;14..32,700;14..32,800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <!-- Chart.js CDN para gráficos elegantes -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Inter', sans-serif;
            background: radial-gradient(circle at 10% 30%, #eef2fa, #d9e4f0);
            min-height: 100vh;
            padding: 20px 16px 40px;
            position: relative;
            overflow-x: hidden;
        }

        /* ---------- FONDO ANIMADO (ondas y partículas elegantes) ---------- */
        body::before {
            content: '';
            position: fixed;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle at 40% 60%, rgba(80, 150, 200, 0.08) 0%, rgba(200, 220, 250, 0) 70%);
            animation: slowDrift 26s infinite alternate;
            pointer-events: none;
            z-index: -2;
        }

        @keyframes slowDrift {
            0% { transform: translate(0%, 0%) rotate(0deg); opacity: 0.6; }
            100% { transform: translate(4%, 3%) rotate(2deg); opacity: 1; }
        }

        body::after {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-image: radial-gradient(circle at 15% 30%, rgba(255,255,245,0.25) 1.5px, transparent 1.5px);
            background-size: 38px 38px;
            pointer-events: none;
            z-index: -1;
            animation: floatShimmer 18s linear infinite;
        }

        @keyframes floatShimmer {
            0% { background-position: 0 0; }
            100% { background-position: 70px 40px; }
        }

        /* Contenedor principal estilo "app" */
        .app-container {
            max-width: 560px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.88);
            backdrop-filter: blur(12px);
            border-radius: 2.5rem;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.3), 0 0 0 1px rgba(255,255,255,0.5);
            overflow: hidden;
            transition: all 0.2s ease;
        }

        /* Header elegante */
        .app-header {
            padding: 2rem 1.8rem 1rem;
            text-align: center;
            background: linear-gradient(115deg, rgba(255,255,245,0.5), rgba(235,248,255,0.7));
            border-bottom: 1px solid rgba(255,255,255,0.7);
        }

        .app-header h1 {
            font-size: 1.9rem;
            font-weight: 800;
            background: linear-gradient(135deg, #0b3c5d, #1f6e8c);
            background-clip: text;
            -webkit-background-clip: text;
            color: transparent;
            display: inline-flex;
            align-items: center;
            gap: 12px;
            letter-spacing: -0.3px;
        }

        .app-header h1 i {
            background: none;
            color: #1f6e8c;
            font-size: 1.9rem;
            filter: drop-shadow(0 2px 6px rgba(0,0,0,0.1));
        }

        .app-header p {
            font-size: 0.8rem;
            font-weight: 500;
            color: #2c6079;
            margin-top: 6px;
            background: rgba(255,255,240,0.6);
            display: inline-block;
            padding: 4px 18px;
            border-radius: 40px;
            backdrop-filter: blur(2px);
        }

        /* MENÚ CELULAR (grid tipo app) */
        .menu-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
            gap: 14px;
            padding: 1.8rem 1.5rem;
            background: rgba(250, 252, 255, 0.6);
            border-bottom: 1px solid rgba(0,0,0,0.05);
        }

        .menu-item {
            background: rgba(255, 255, 255, 0.85);
            backdrop-filter: blur(4px);
            border-radius: 1.8rem;
            padding: 0.9rem 0.4rem;
            text-align: center;
            cursor: pointer;
            transition: all 0.25s cubic-bezier(0.2, 0.9, 0.4, 1.1);
            box-shadow: 0 6px 12px -6px rgba(0, 0, 0, 0.1);
            border: 1px solid rgba(255,255,255,0.7);
        }

        .menu-item i {
            font-size: 1.8rem;
            color: #1f6e8c;
            display: block;
            margin-bottom: 8px;
            transition: transform 0.2s;
        }

        .menu-item span {
            font-weight: 600;
            font-size: 0.75rem;
            color: #1b4e6e;
            letter-spacing: -0.2px;
        }

        .menu-item:hover {
            transform: translateY(-5px);
            background: white;
            box-shadow: 0 16px 24px -12px rgba(30, 100, 130, 0.3);
            border-color: rgba(70, 150, 200, 0.4);
        }

        .menu-item:hover i {
            transform: scale(1.08);
        }

        .menu-item.active {
            background: linear-gradient(125deg, #e6f4ff, #ffffff);
            border-left: 3px solid #2c7da0;
            border-right: 3px solid #2c7da0;
            box-shadow: 0 10px 18px -8px rgba(0,0,0,0.2);
        }

        /* Panel de contenido dinámico */
        .content-panel {
            padding: 1.8rem 1.5rem 2rem;
            background: rgba(255, 255, 255, 0.65);
            transition: all 0.2s;
        }

        /* Tarjetas y elementos internos */
        .card-elegant {
            background: rgba(255, 255, 255, 0.9);
            border-radius: 1.8rem;
            padding: 1.4rem;
            box-shadow: 0 8px 20px rgba(0,0,0,0.05);
            border: 1px solid rgba(255,255,255,0.8);
            backdrop-filter: blur(2px);
        }

        .form-group {
            margin-bottom: 1.2rem;
        }

        .form-group label {
            font-weight: 600;
            font-size: 0.8rem;
            color: #2a5f7a;
            display: flex;
            align-items: center;
            gap: 6px;
            margin-bottom: 6px;
        }

        .form-group input, .form-group select {
            width: 100%;
            padding: 12px 14px;
            border-radius: 1.2rem;
            border: 1px solid #cbdae9;
            background: white;
            font-family: 'Inter', monospace;
            font-size: 0.9rem;
            transition: 0.2s;
            outline: none;
        }

        .form-group input:focus, .form-group select:focus {
            border-color: #2c7da0;
            box-shadow: 0 0 0 3px rgba(44,125,160,0.2);
        }

        .btn-glow {
            background: linear-gradient(95deg, #0f3b5c, #1a6285);
            border: none;
            padding: 12px 18px;
            border-radius: 2rem;
            font-weight: 700;
            color: white;
            display: inline-flex;
            align-items: center;
            gap: 10px;
            justify-content: center;
            cursor: pointer;
            transition: all 0.2s ease;
            width: 100%;
            font-size: 0.9rem;
            box-shadow: 0 6px 14px rgba(0, 0, 0, 0.1);
        }

        .btn-glow i {
            font-size: 1rem;
            transition: transform 0.2s;
        }

        .btn-glow:hover {
            transform: translateY(-2px);
            background: linear-gradient(95deg, #1a5375, #2378a0);
            box-shadow: 0 14px 22px -8px rgba(30, 90, 110, 0.4);
        }

        .btn-glow:hover i {
            transform: translateX(3px);
        }

        .btn-outline {
            background: transparent;
            border: 1.5px solid #1f6e8c;
            color: #1f6e8c;
            box-shadow: none;
        }

        .student-list, .attendance-list {
            max-height: 380px;
            overflow-y: auto;
        }

        .student-item, .att-row {
            background: rgba(245, 250, 255, 0.8);
            border-radius: 1.2rem;
            padding: 12px 14px;
            margin-bottom: 8px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-left: 4px solid #2c7da0;
        }

        .badge {
            background: #e1ecf4;
            border-radius: 40px;
            padding: 4px 12px;
            font-size: 0.7rem;
            font-weight: 600;
            color: #1f5e7e;
        }

        .qr-simulator {
            text-align: center;
            background: #eef4fc;
            border-radius: 1.8rem;
            padding: 1.5rem;
            margin-bottom: 1.2rem;
            border: 1px dashed #2c7da0;
        }

        .qr-icon {
            font-size: 3.5rem;
            color: #2c7da0;
            animation: pulse 1.8s infinite;
        }

        @keyframes pulse {
            0% { opacity: 0.6; transform: scale(0.98);}
            100% { opacity: 1; transform: scale(1.05);}
        }

        .table-responsive {
            overflow-x: auto;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.8rem;
        }
        th {
            text-align: left;
            padding: 10px 4px;
            color: #0f445f;
        }
        td {
            padding: 8px 4px;
            border-bottom: 1px solid #dce5ef;
        }

        .footer-note {
            font-size: 0.7rem;
            text-align: center;
            margin-top: 1rem;
            color: #2c6d8a;
        }

        @media (max-width: 480px) {
            .menu-grid {
                gap: 8px;
                padding: 1rem;
            }
            .content-panel {
                padding: 1.2rem;
            }
            .app-header h1 {
                font-size: 1.5rem;
            }
        }
    </style>
</head>
<body>
<div class="app-container">
    <div class="app-header">
        <h1><i class="fas fa-building-user"></i> UNIDAD DE TRÁMITES Y REGISTROS <i class="fas fa-qrcode"></i></h1>
        <p><i class="fas fa-mobile-alt"></i> Gestión ágil · Asistencia y estudiantes</p>
    </div>

    <!-- Menú tipo aplicación móvil -->
    <div class="menu-grid" id="menuGrid">
        <div class="menu-item" data-view="register">
            <i class="fas fa-user-plus"></i><span>📝 Registrar estudiante</span>
        </div>
        <div class="menu-item" data-view="list">
            <i class="fas fa-list-ul"></i><span>📋 Lista estudiantes</span>
        </div>
        <div class="menu-item" data-view="qr">
            <i class="fas fa-camera"></i><span>📸 Escanear QR</span>
        </div>
        <div class="menu-item" data-view="manual">
            <i class="fas fa-pen-alt"></i><span>✍️ Asistencia manual</span>
        </div>
        <div class="menu-item" data-view="attendance">
            <i class="fas fa-chart-simple"></i><span>📊 Ver asistencia</span>
        </div>
    </div>

    <div class="content-panel" id="dynamicContent">
        <!-- Aquí se renderiza la vista activa -->
        <div class="card-elegant" style="text-align:center; padding:2rem;">
            <i class="fas fa-spinner fa-pulse" style="font-size:2rem; color:#1f6e8c;"></i>
            <p>Cargando...</p>
        </div>
    </div>
    <div class="footer-note">
        <i class="fas fa-shield-alt"></i> Datos simulados • Gestión integral
    </div>
</div>

<script>
    // ---------- DATA MODEL ----------
    let students = [
        { id: "UTR001", name: "Valeria Méndez", email: "valeria@estudiante.com" },
        { id: "UTR002", name: "Carlos Rivera", email: "carlos.r@estudiante.com" },
        { id: "UTR003", name: "Lucía Herrera", email: "lucia.h@estudiante.com" }
    ];

    // Registros de asistencia: { studentId, studentName, timestamp, dateStr, method }
    let attendanceRecords = [
        { studentId: "UTR001", studentName: "Valeria Méndez", timestamp: Date.now() - 3600000, dateStr: new Date(Date.now() - 3600000).toLocaleString(), method: "QR" },
        { studentId: "UTR002", studentName: "Carlos Rivera", timestamp: Date.now() - 7200000, dateStr: new Date(Date.now() - 7200000).toLocaleString(), method: "Manual" }
    ];

    let currentView = "register";
    let chartInstance = null;

    // Helper: obtener nombre de estudiante por ID
    function getStudentById(id) {
        return students.find(s => s.id === id);
    }

    // Registrar estudiante
    function addStudent(id, name, email) {
        if (!id || !name) return false;
        if (students.some(s => s.id === id)) return false;
        students.push({ id: id.trim(), name: name.trim(), email: email.trim() || "" });
        return true;
    }

    // Marcar asistencia (general)
    function markAttendance(studentId, method = "Manual") {
        const student = getStudentById(studentId);
        if (!student) return false;
        const now = new Date();
        attendanceRecords.unshift({
            studentId: student.id,
            studentName: student.name,
            timestamp: now.getTime(),
            dateStr: now.toLocaleString(),
            method: method
        });
        return true;
    }

    // Obtener estadísticas para gráfico (asistencias por estudiante)
    function getAttendanceStats() {
        const map = new Map();
        attendanceRecords.forEach(rec => {
            const name = rec.studentName;
            map.set(name, (map.get(name) || 0) + 1);
        });
        return { labels: Array.from(map.keys()), data: Array.from(map.values()) };
    }

    // ---------- RENDERIZADO DE VISTAS (UI DINÁMICA) ----------
    function renderRegisterView() {
        return `
            <div class="card-elegant">
                <h3 style="margin-bottom:1rem; color:#0f3b5c;"><i class="fas fa-user-graduate"></i> Registrar nuevo estudiante</h3>
                <div class="form-group">
                    <label><i class="fas fa-id-card"></i> ID / Matrícula *</label>
                    <input type="text" id="regId" placeholder="Ej: UTR099" autocomplete="off">
                </div>
                <div class="form-group">
                    <label><i class="fas fa-user"></i> Nombre completo *</label>
                    <input type="text" id="regName" placeholder="Nombres y apellidos">
                </div>
                <div class="form-group">
                    <label><i class="fas fa-envelope"></i> Correo electrónico</label>
                    <input type="email" id="regEmail" placeholder="ejemplo@dominio.com">
                </div>
                <button class="btn-glow" id="btnAddStudent"><i class="fas fa-save"></i> Registrar estudiante</button>
                <div id="regMessage" style="margin-top:12px; font-size:0.8rem; text-align:center;"></div>
            </div>
        `;
    }

    function renderListView() {
        if (students.length === 0) {
            return `<div class="card-elegant"><i class="fas fa-info-circle"></i> No hay estudiantes registrados. Usa el menú "Registrar estudiante".</div>`;
        }
        let html = `<div class="card-elegant"><h3 style="margin-bottom:1rem;"><i class="fas fa-users"></i> Lista de estudiantes (${students.length})</h3><div class="student-list">`;
        students.forEach(stud => {
            html += `
                <div class="student-item">
                    <div><strong>${stud.name}</strong><br><span class="badge">${stud.id}</span><span style="font-size:0.7rem; margin-left:8px;">${stud.email}</span></div>
                    <i class="fas fa-id-card" style="color:#2c7da0;"></i>
                </div>
            `;
        });
        html += `</div><button class="btn-glow btn-outline" id="refreshListBtn" style="margin-top:12px;"><i class="fas fa-sync-alt"></i> Actualizar lista</button></div>`;
        return html;
    }

    function renderQrView() {
        return `
            <div class="card-elegant">
                <div class="qr-simulator">
                    <i class="fas fa-qrcode qr-icon"></i>
                    <p style="margin-top:8px; font-weight:500;">📸 Escáner QR inteligente</p>
                    <small>Simula la lectura de un código QR de estudiante</small>
                </div>
                <button class="btn-glow" id="simulateQrScan"><i class="fas fa-camera"></i> Simular escaneo QR</button>
                <div id="qrResult" style="margin-top:18px; background:#eef2f9; border-radius:1.2rem; padding:12px; font-size:0.85rem;"></div>
                <p class="footer-note" style="margin-top:12px;"><i class="fas fa-info-circle"></i> Al escanear se registra asistencia automática con fecha/hora actual.</p>
            </div>
        `;
    }

    function renderManualAttendanceView() {
        let options = students.map(s => `<option value="${s.id}">${s.name} (${s.id})</option>`).join('');
        if (students.length === 0) options = '<option disabled>No hay estudiantes registrados</option>';
        return `
            <div class="card-elegant">
                <h3 style="margin-bottom:0.8rem;"><i class="fas fa-pen-fancy"></i> Registrar asistencia manual</h3>
                <div class="form-group">
                    <label><i class="fas fa-user-check"></i> Seleccionar estudiante</label>
                    <select id="manualStudentSelect">${options}</select>
                </div>
                <button class="btn-glow" id="markManualAttendance"><i class="fas fa-check-circle"></i> Marcar asistencia (ahora)</button>
                <div id="manualMsg" style="margin-top:12px; font-size:0.8rem;"></div>
            </div>
        `;
    }

    function renderAttendanceView() {
        if (attendanceRecords.length === 0) {
            return `<div class="card-elegant"><i class="fas fa-calendar-times"></i> Aún no hay registros de asistencia.</div>`;
        }
        const stats = getAttendanceStats();
        const hasChartData = stats.labels.length > 0;
        let chartCanvas = `<canvas id="attChart" style="max-height:240px; margin-top:10px;"></canvas>`;
        let tableRows = '';
        attendanceRecords.slice(0, 15).forEach(rec => {
            tableRows += `<tr><td>${rec.studentName}</td><td>${rec.dateStr}</td><td><span class="badge">${rec.method}</span></td></tr>`;
        });
        return `
            <div class="card-elegant">
                <h3><i class="fas fa-chart-line"></i> Reporte de asistencia</h3>
                ${hasChartData ? chartCanvas : '<p class="badge">Datos insuficientes para gráfico</p>'}
                <div class="table-responsive" style="margin-top:1.2rem;">
                    <table style="width:100%">
                        <thead><tr><th>Estudiante</th><th>Fecha/Hora</th><th>Método</th></tr></thead>
                        <tbody>${tableRows}</tbody>
                    </table>
                    ${attendanceRecords.length > 15 ? '<p style="font-size:0.7rem;">Mostrando últimos 15 registros</p>' : ''}
                </div>
                <button class="btn-glow btn-outline" id="refreshAttendanceBtn" style="margin-top:1rem;"><i class="fas fa-chart-simple"></i> Actualizar gráfico</button>
            </div>
        `;
    }

    // Renderizar según vista actual y luego adjuntar eventos
    function loadView(view) {
        currentView = view;
        let content = "";
        switch(view) {
            case "register": content = renderRegisterView(); break;
            case "list": content = renderListView(); break;
            case "qr": content = renderQrView(); break;
            case "manual": content = renderManualAttendanceView(); break;
            case "attendance": content = renderAttendanceView(); break;
            default: content = renderRegisterView();
        }
        document.getElementById("dynamicContent").innerHTML = content;

        // Post-renderizado: eventos específicos
        if (view === "register") {
            const btn = document.getElementById("btnAddStudent");
            if (btn) btn.addEventListener("click", () => {
                const id = document.getElementById("regId")?.value.trim();
                const name = document.getElementById("regName")?.value.trim();
                const email = document.getElementById("regEmail")?.value.trim();
                const msgDiv = document.getElementById("regMessage");
                if (!id || !name) {
                    msgDiv.innerHTML = '<span style="color:#c0392b;"><i class="fas fa-exclamation-triangle"></i> ID y nombre son obligatorios.</span>';
                    return;
                }
                if (addStudent(id, name, email)) {
                    msgDiv.innerHTML = '<span style="color:#2c7a47;"><i class="fas fa-check"></i> Estudiante registrado exitosamente.</span>';
                    document.getElementById("regId").value = "";
                    document.getElementById("regName").value = "";
                    document.getElementById("regEmail").value = "";
                    // si la vista actual es lista, actualizar después de 600ms? Solo cambia si está activa lista, pero mejor mantener
                } else {
                    msgDiv.innerHTML = '<span style="color:#c0392b;"><i class="fas fa-times"></i> ID duplicado o error. Verifica.</span>';
                }
            });
        } 
        else if (view === "list") {
            const refreshBtn = document.getElementById("refreshListBtn");
            if (refreshBtn) refreshBtn.addEventListener("click", () => { loadView("list"); });
        }
        else if (view === "qr") {
            const simulateBtn = document.getElementById("simulateQrScan");
            if (simulateBtn) {
                simulateBtn.addEventListener("click", () => {
                    if (students.length === 0) {
                        document.getElementById("qrResult").innerHTML = '<span style="color:#b85c00;"><i class="fas fa-users-slash"></i> No hay estudiantes. Registra uno primero.</span>';
                        return;
                    }
                    const randomStudent = students[Math.floor(Math.random() * students.length)];
                    const success = markAttendance(randomStudent.id, "QR");
                    if (success) {
                        document.getElementById("qrResult").innerHTML = `<div style="background:#e0f2e9; border-radius:1rem; padding:8px;"><i class="fas fa-check-circle" style="color:#2c7a47;"></i> <strong>✅ QR escaneado</strong><br>Estudiante: ${randomStudent.name}<br>Asistencia registrada a las ${new Date().toLocaleTimeString()}</div>`;
                        // Si estamos viendo asistencia más adelante se actualizará al cambiar, pero podemos refrescar notificación
                    } else {
                        document.getElementById("qrResult").innerHTML = '<span style="color:#b33;">Error al marcar asistencia</span>';
                    }
                });
            }
        }
        else if (view === "manual") {
            const btnManual = document.getElementById("markManualAttendance");
            if (btnManual) {
                btnManual.addEventListener("click", () => {
                    const select = document.getElementById("manualStudentSelect");
                    if (!select || students.length === 0) {
                        document.getElementById("manualMsg").innerHTML = '<span style="color:#c0392b;">No hay estudiantes disponibles.</span>';
                        return;
                    }
                    const studentId = select.value;
                    const success = markAttendance(studentId, "Manual");
                    if (success) {
                        document.getElementById("manualMsg").innerHTML = '<span style="color:#2c7a47;"><i class="fas fa-stamp"></i> Asistencia manual registrada correctamente.</span>';
                    } else {
                        document.getElementById("manualMsg").innerHTML = '<span style="color:#c0392b;">Error al registrar.</span>';
                    }
                });
            }
        }
        else if (view === "attendance") {
            // inicializar gráfico después de render
            initAttendanceChart();
            const refreshAttBtn = document.getElementById("refreshAttendanceBtn");
            if (refreshAttBtn) {
                refreshAttBtn.addEventListener("click", () => {
                    loadView("attendance");
                });
            }
        }
        // Resaltar menú activo
        document.querySelectorAll(".menu-item").forEach(el => {
            if (el.getAttribute("data-view") === view) el.classList.add("active");
            else el.classList.remove("active");
        });
    }

    function initAttendanceChart() {
        const canvas = document.getElementById("attChart");
        if (!canvas) return;
        const ctx = canvas.getContext("2d");
        const stats = getAttendanceStats();
        if (stats.labels.length === 0) return;
        if (chartInstance) chartInstance.destroy();
        chartInstance = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: stats.labels,
                datasets: [{
                    label: 'N° de asistencias',
                    data: stats.data,
                    backgroundColor: 'rgba(44, 125, 160, 0.7)',
                    borderRadius: 12,
                    borderSkipped: false,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: { position: 'top', labels: { font: { size: 11 } } },
                    tooltip: { backgroundColor: '#0f3b5c' }
                },
                scales: {
                    y: { beginAtZero: true, grid: { color: 'rgba(0,0,0,0.05)' }, title: { display: true, text: 'Asistencias' } },
                    x: { ticks: { maxRotation: 35, autoSkip: true } }
                }
            }
        });
    }

    // Eventos del menú
    function bindMenuEvents() {
        const items = document.querySelectorAll(".menu-item");
        items.forEach(item => {
            item.addEventListener("click", (e) => {
                const view = item.getAttribute("data-view");
                if (view) loadView(view);
            });
        });
    }

    // Inicializar con vista por defecto
    window.addEventListener("DOMContentLoaded", () => {
        bindMenuEvents();
        loadView("register");  // vista inicial elegante
    });
</script>
</body>
</html>
