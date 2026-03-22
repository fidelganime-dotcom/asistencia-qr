<!DOCTYPE html>
<html lang="es" xmlns:th="http://www.thymeleaf.org">

<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Sistema Taller Mecánico - Gestión de Vehículos</title>
  <!-- Bootstrap CSS -->
  <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
  <!-- Lucide Icons (Modern Icons) -->
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/lucide/0.263.1/lucide.min.css">
  <!-- SweetAlert2 CSS -->
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/sweetalert2@11/dist/sweetalert2.min.css">
  <!-- Google Fonts -->
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  <!-- Animate.css -->
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css">
  <!-- Chart.js -->
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  
  <style>
    :root {
      --primary-color: #0066ff; /* Azul eléctrico */
      --primary-hover: #0052cc;
      --secondary-color: #2d3748; /* Gris plomo oscuro */
      --accent-color: #00ffcc; /* Azul eléctrico claro */
      --text-primary: #f8fafc; /* Blanco */
      --text-secondary: #cbd5e1;
      --bg-dark: #0f172a; /* Fondo oscuro */
      --bg-darker: #020617;
      --glass-bg: rgba(15, 23, 42, 0.7);
      --glass-border: rgba(255, 255, 255, 0.1);
      --shadow-3d: 0 10px 25px -5px rgba(0, 102, 255, 0.2), 0 10px 10px -5px rgba(0, 102, 255, 0.1);
      --shadow-hover: 0 20px 50px -10px rgba(0, 102, 255, 0.4);
      --success-gradient: linear-gradient(135deg, #00ffcc 0%, #0066ff 100%);
      --danger-gradient: linear-gradient(135deg, #ff3366 0%, #ff0066 100%);
      --warning-gradient: linear-gradient(135deg, #ffcc00 0%, #ff9900 100%);
    }

    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }

    body {
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      background-color: var(--bg-dark);
      color: var(--text-primary);
      min-height: 100vh;
      overflow-x: hidden;
      transition: all 0.3s ease;
      animation: fadeInUp 0.5s ease-out;
    }

    /* Animated background particles */
    .bg-particles {
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      pointer-events: none;
      z-index: -1;
    }

    .particle {
      position: absolute;
      width: 2px;
      height: 2px;
      background: var(--primary-color);
      border-radius: 50%;
      animation: float 8s infinite ease-in-out;
      opacity: 0.6;
    }

    .particle:nth-child(3n+1) {
      background: var(--accent-color);
    }

    .particle:nth-child(3n+2) {
      background: white;
    }

    @keyframes float {
      0%, 100% { transform: translate(0, 0) rotate(0deg); opacity: 0.6; }
      25% { transform: translate(10px, -15px) rotate(45deg); opacity: 0.8; }
      50% { transform: translate(-5px, -25px) rotate(90deg); opacity: 1; }
      75% { transform: translate(15px, -10px) rotate(135deg); opacity: 0.8; }
    }

    @keyframes pulse {
      0%, 100% { transform: scale(1); opacity: 0.8; }
      50% { transform: scale(1.1); opacity: 1; }
    }

    /* Sidebar */
    .sidebar {
      width: 280px;
      height: 100vh;
      background: var(--glass-bg);
      backdrop-filter: blur(20px);
      border-right: 1px solid var(--glass-border);
      box-shadow: var(--shadow-3d);
      padding: 25px;
      position: fixed;
      overflow-y: auto;
      z-index: 1000;
      transform: translateX(0);
      transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
    }

    .sidebar::-webkit-scrollbar {
      width: 6px;
    }

    .sidebar::-webkit-scrollbar-track {
      background: transparent;
    }

    .sidebar::-webkit-scrollbar-thumb {
      background: var(--primary-color);
      border-radius: 10px;
    }

    .logo {
      text-align: center;
      margin-bottom: 30px;
      animation: slideInDown 0.8s ease-out;
    }

    .logo img {
      width: 80px;
      height: 80px;
      border-radius: 20px;
      box-shadow: var(--shadow-3d);
      transition: all 0.3s ease;
      border: 2px solid var(--primary-color);
    }

    .logo img:hover {
      transform: scale(1.1) rotate(5deg);
      box-shadow: 0 0 20px var(--primary-color);
    }

    .logo-text {
      color: var(--text-primary);
      font-size: 16px;
      font-weight: 700;
      margin-top: 15px;
      text-shadow: 0 2px 10px rgba(0, 102, 255, 0.5);
    }

    .nav-item {
      margin: 12px 0;
      transform: translateX(-20px);
      opacity: 0;
      animation: slideInLeft 0.6s ease-out forwards;
    }

    .nav-item:nth-child(1) { animation-delay: 0.1s; }
    .nav-item:nth-child(2) { animation-delay: 0.2s; }
    .nav-item:nth-child(3) { animation-delay: 0.3s; }
    .nav-item:nth-child(4) { animation-delay: 0.4s; }
    .nav-item:nth-child(5) { animation-delay: 0.5s; }
    .nav-item:nth-child(6) { animation-delay: 0.6s; }
    .nav-item:nth-child(7) { animation-delay: 0.7s; }
    .nav-item:nth-child(8) { animation-delay: 0.8s; }
    .nav-item:nth-child(9) { animation-delay: 0.9s; }
    .nav-item:nth-child(10) { animation-delay: 1.0s; }

    .nav-link {
      display: flex;
      align-items: center;
      padding: 15px 20px;
      color: var(--text-primary);
      text-decoration: none;
      border-radius: 12px;
      background: rgba(0, 102, 255, 0.1);
      backdrop-filter: blur(10px);
      border: 1px solid rgba(0, 102, 255, 0.2);
      transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
      font-weight: 500;
      font-size: 14px;
      position: relative;
      overflow: hidden;
    }

    .nav-link::before {
      content: '';
      position: absolute;
      top: 0;
      left: -100%;
      width: 100%;
      height: 100%;
      background: linear-gradient(90deg, transparent, rgba(0, 102, 255, 0.3), transparent);
      transition: left 0.7s;
    }

    .nav-link:hover::before {
      left: 100%;
    }

    .nav-link:hover {
      transform: translateX(10px) scale(1.02);
      background: rgba(0, 102, 255, 0.3);
      box-shadow: var(--shadow-hover);
      color: white;
    }

    .nav-link.active {
      background: var(--success-gradient);
      transform: translateX(10px);
      box-shadow: var(--shadow-hover);
      color: var(--bg-darker);
      font-weight: 600;
    }

    .nav-icon {
      width: 20px;
      height: 20px;
      margin-right: 12px;
      transition: all 0.3s ease;
    }

    .nav-link:hover .nav-icon {
      transform: scale(1.2);
    }

    /* Main content */
    .content {
      margin-left: 280px;
      padding: 30px;
      min-height: 100vh;
      animation: fadeInUp 0.8s ease-out;
    }

    /* Glass cards */
    .glass-card {
      background: var(--glass-bg);
      backdrop-filter: blur(20px);
      border-radius: 16px;
      border: 1px solid var(--glass-border);
      box-shadow: var(--shadow-3d);
      padding: 30px;
      margin-bottom: 25px;
      transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
      position: relative;
      overflow: hidden;
    }

    .glass-card::before {
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
    }

    .glass-card:hover::before {
      opacity: 1;
      animation: shine 3s infinite;
    }

    @keyframes shine {
      0% { transform: rotate(30deg) translate(-10%, -10%); }
      100% { transform: rotate(30deg) translate(10%, 10%); }
    }

    .glass-card:hover {
      transform: translateY(-5px);
      box-shadow: var(--shadow-hover);
      border-color: rgba(0, 102, 255, 0.3);
    }

    .page-title {
      color: var(--text-primary);
      font-size: 2.5rem;
      font-weight: 700;
      margin-bottom: 30px;
      text-shadow: 0 2px 10px rgba(0, 102, 255, 0.3);
      position: relative;
      display: inline-block;
    }

    .page-title::after {
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

    .page-title:hover::after {
      transform: scaleX(1);
    }

    /* Form styles */
    .form-group label {
      color: var(--text-primary);
      font-weight: 600;
      margin-bottom: 8px;
      display: flex;
      align-items: center;
      font-size: 14px;
      transition: all 0.3s ease;
    }

    .form-group label svg {
      width: 16px;
      height: 16px;
      margin-right: 8px;
      color: var(--accent-color);
    }

    .form-control {
      background: rgba(15, 23, 42, 0.5);
      border: 1px solid var(--glass-border);
      border-radius: 12px;
      color: var(--text-primary);
      padding: 10px;
      transition: all 0.3s ease;
      backdrop-filter: blur(5px);
    }

    .form-control:focus {
      background: rgba(15, 23, 42, 0.8);
      border-color: var(--primary-color);
      box-shadow: 0 0 0 3px rgba(0, 102, 255, 0.2);
      color: var(--text-primary);
      transform: scale(1.01);
    }

    .form-control::placeholder {
      color: rgba(200, 200, 200, 0.6);
    }

    /* 3D Buttons with animations */
    .modern-btn {
      padding: 12px 25px;
      border: none;
      border-radius: 12px;
      font-weight: 600;
      font-size: 14px;
      transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
      position: relative;
      overflow: hidden;
      display: inline-flex;
      align-items: center;
      gap: 8px;
      text-decoration: none;
      cursor: pointer;
      transform-style: preserve-3d;
      perspective: 1000px;
      box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
      border-bottom: 3px solid rgba(0, 0, 0, 0.2);
    }

    .modern-btn::before {
      content: '';
      position: absolute;
      top: 0;
      left: -100%;
      width: 100%;
      height: 100%;
      background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
      transition: left 0.7s;
    }

    .modern-btn:hover::before {
      left: 100%;
    }

    .modern-btn:hover {
      transform: translateY(-3px) scale(1.05);
      box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
    }

    .modern-btn:active {
      transform: translateY(1px);
      box-shadow: 0 3px 10px rgba(0, 0, 0, 0.2);
    }

    .btn-primary {
      background: var(--primary-color);
      color: white;
    }

    .btn-primary:hover {
      background: var(--primary-hover);
    }

    .btn-success {
      background: var(--success-gradient);
      color: var(--bg-darker);
    }

    .btn-warning {
      background: var(--warning-gradient);
      color: var(--bg-darker);
    }

    .btn-secondary {
      background: rgba(255, 255, 255, 0.1);
      color: white;
      backdrop-filter: blur(10px);
    }

    .btn-info {
      background: var(--success-gradient);
      color: var(--bg-darker);
    }

    .btn-danger {
      background: var(--danger-gradient);
      color: white;
    }

    /* Modern table */
    .modern-table {
      background: var(--glass-bg);
      backdrop-filter: blur(20px);
      border-radius: 16px;
      overflow: hidden;
      box-shadow: var(--shadow-3d);
      border: 1px solid var(--glass-border);
      transition: all 0.3s ease;
    }

    .modern-table:hover {
      box-shadow: var(--shadow-hover);
    }

    .modern-table .table {
      margin: 0;
      color: var(--text-primary);
    }

    .modern-table thead th {
      background: linear-gradient(135deg, rgba(0,102,255,0.8) 0%, rgba(0,51,204,0.8) 100%);
      color: white;
      font-weight: 600;
      padding: 20px 15px;
      border: none;
      font-size: 14px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      position: relative;
      overflow: hidden;
    }

    .modern-table thead th::after {
      content: '';
      position: absolute;
      bottom: 0;
      left: 0;
      width: 100%;
      height: 2px;
      background: var(--accent-color);
      transform: scaleX(0);
      transition: transform 0.3s ease;
    }

    .modern-table thead th:hover::after {
      transform: scaleX(1);
    }

    .modern-table tbody tr {
      transition: all 0.3s ease;
      border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    }

   
        .modern-table tbody tr:hover {
          background: rgba(7, 196, 248, 0.9);
    transform: translateX(5px);
            
        }

    .modern-table tbody td {
      padding: 15px;
      border: none;
      vertical-align: middle;
      position: relative;
    }

    .modern-table tbody td::before {
      content: '';
      position: absolute;
      left: 0;
      top: 50%;
      transform: translateY(-50%);
      width: 3px;
      height: 0;
      background: var(--primary-color);
      transition: all 0.3s ease;
    }

    .modern-table tbody tr:hover td::before {
      height: 60%;
    }

    .action-buttons {
      display: flex;
      gap: 8px;
    }

    .action-buttons .btn {
      padding: 8px 12px;
      font-size: 12px;
      border-radius: 8px;
      transition: all 0.2s ease;
    }

    .action-buttons .btn:hover {
      transform: translateY(-2px) scale(1.1);
    }

    /* Badges */
    .badge {
      padding: 8px 12px;
      border-radius: 20px;
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
    }

    .badge-success {
      background: var(--success-gradient);
      color: var(--bg-darker);
    }

    .badge-warning {
      background: var(--warning-gradient);
      color: var(--bg-darker);
    }

    .badge-secondary {
      background: rgba(255, 255, 255, 0.2);
      color: white;
    }

    /* Infinity badge in sidebar */
    .infinity-badge {
      position: absolute;
      bottom: 25px;
      left: 25px;
      background: rgba(0, 102, 255, 0.2);
      backdrop-filter: blur(10px);
      padding: 12px 20px;
      border-radius: 50px;
      color: var(--text-primary);
      font-size: 12px;
      font-weight: 600;
      border: 1px solid var(--glass-border);
      display: flex;
      align-items: center;
      gap: 8px;
      animation: pulse 2s infinite;
      transition: all 0.3s ease;
    }

    .infinity-badge:hover {
      background: rgba(0, 102, 255, 0.3);
      transform: scale(1.05);
    }

    /* Animations */
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

    @keyframes slideInLeft {
      from {
        opacity: 0;
        transform: translateX(-30px);
      }
      to {
        opacity: 1;
        transform: translateX(0);
      }
    }

    @keyframes slideInRight {
      from {
        opacity: 0;
        transform: translateX(30px);
      }
      to {
        opacity: 1;
        transform: translateX(0);
      }
    }

    @keyframes fadeInUp {
      from {
        opacity: 0;
        transform: translateY(5px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }

    @keyframes bounceIn {
      from, 20%, 40%, 60%, 80%, to {
        animation-timing-function: cubic-bezier(0.215, 0.610, 0.355, 1.000);
      }
      0% {
        opacity: 0;
        transform: scale3d(.3, .3, .3);
      }
      20% {
        transform: scale3d(1.1, 1.1, 1.1);
      }
      40% {
        transform: scale3d(.9, .9, .9);
      }
      60% {
        opacity: 1;
        transform: scale3d(1.03, 1.03, 1.03);
      }
      80% {
        transform: scale3d(.97, .97, .97);
      }
      to {
        opacity: 1;
        transform: scale3d(1, 1, 1);
      }
    }

    @keyframes shake {
      from, to {
        transform: translate3d(0, 0, 0);
      }
      10%, 30%, 50%, 70%, 90% {
        transform: translate3d(-10px, 0, 0);
      }
      20%, 40%, 60%, 80% {
        transform: translate3d(10px, 0, 0);
      }
    }

    /* Custom scrollbar */
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

    ::-webkit-scrollbar-thumb:hover {
      background: var(--primary-hover);
    }

    /* Responsive Design */
    @media (max-width: 768px) {
      .sidebar {
        transform: translateX(-100%);
      }
      
      .content {
        margin-left: 0;
        padding: 20px;
      }
      
      .page-title {
        font-size: 2rem;
      }
    }

    /* Mobile menu button */
    .mobile-menu-btn {
      position: fixed;
      top: 20px;
      left: 20px;
      z-index: 1001;
      background: var(--primary-color);
      border: none;
      border-radius: 12px;
      padding: 12px;
      color: white;
      box-shadow: var(--shadow-3d);
      display: none;
      transition: all 0.3s ease;
    }

    .mobile-menu-btn:hover {
      transform: scale(1.1);
    }

    @media (max-width: 768px) {
      .mobile-menu-btn {
        display: block;
      }
    }

    /* Focus states */
    .form-group.focused label {
      color: var(--accent-color);
      text-shadow: 0 0 10px rgba(0, 255, 204, 0.3);
    }

    /* Table row animations */
    .table tbody tr {
      animation: fadeIn 0.5s ease-out forwards;
      opacity: 0;
    }

    @keyframes fadeIn {
      to {
        opacity: 1;
      }
    }

    /* Floating action button */
    .fab {
      position: fixed;
      bottom: 30px;
      right: 30px;
      width: 60px;
      height: 60px;
      border-radius: 50%;
      background: var(--primary-color);
      color: white;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 10px 25px rgba(0, 102, 255, 0.4);
      cursor: pointer;
      z-index: 100;
      transition: all 0.3s ease;
      animation: pulse 2s infinite;
    }

    .fab:hover {
      transform: scale(1.1) rotate(90deg);
      box-shadow: 0 15px 35px rgba(0, 102, 255, 0.6);
    }

    /* Tooltip */
    .tooltip-inner {
      background: var(--bg-darker);
      color: var(--text-primary);
      border-radius: 8px;
      padding: 8px 12px;
      box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
    }

    .bs-tooltip-auto[x-placement^=top] .arrow::before, 
    .bs-tooltip-top .arrow::before {
      border-top-color: var(--bg-darker);
    }

    /* Status indicators */
    .status-indicator {
      display: inline-block;
      width: 10px;
      height: 10px;
      border-radius: 50%;
      margin-right: 8px;
      animation: pulse 2s infinite;
    }

    .status-active {
      background: var(--accent-color);
      box-shadow: 0 0 10px var(--accent-color);
    }

    .status-inactive {
      background: #ff3366;
      box-shadow: 0 0 10px #ff3366;
    }
  </style>
</head>

<body>
  <!-- Animated background particles -->
  <div class="bg-particles" id="particles"></div>

  <!-- Mobile menu button -->
  <button class="mobile-menu-btn" onclick="toggleSidebar()">
    <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/>
    </svg>
  </button>

  <div class="sidebar">
    <div class="logo">
      <img src="https://res.cloudinary.com/toyosa-sa/production/plataforma-toyota/backend/images/toyota/hilux-lujo-ng/colores/super-blanco.png" alt="Logo">
      <div class="logo-text">SISTEMA TALLER MECÁNICO "MOTORS BLANCA"</div>
    </div>
    
    <div class="nav-item">
      <a href="/formularioEmpleado" class="nav-link">
        <svg class="nav-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
        </svg>
        Gestionar Empleado
      </a>
    </div>
    
    <div class="nav-item">
      <a href="/formularioCliente" class="nav-link">
        <svg class="nav-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/>
        </svg>
        Gestionar Cliente
      </a>
    </div>
    
    <div class="nav-item">
      <a href="formularioCita" class="nav-link">
        <svg class="nav-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/>
        </svg>
        Gestionar Citas
      </a>
    </div>
    
    <div class="nav-item">
      <a href="/formularioVehiculo" class="nav-link active">
        <svg class="nav-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/>
        </svg>
        Gestionar Vehículo
      </a>
    </div>
    
    <div class="nav-item">
      <a href="/formularioDetalleOrden" class="nav-link">
        <svg class="nav-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
        </svg>
        Detalle Orden
      </a>
    </div>
    
    <div class="nav-item">
      <a href="/formularioFactura" class="nav-link">
        <svg class="nav-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 14l6-6m-5.5.5h.01m4.99 5h.01M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16l3.5-2 3.5 2 3.5-2 3.5 2zM10 8.5a.5.5 0 11-1 0 .5.5 0 011 0zm5 5a.5.5 0 11-1 0 .5.5 0 011 0z"/>
        </svg>
        Gestionar Factura
      </a>
    </div>
      <div class="nav-item">
            <a href="/formularioServicio" class="nav-link">
                <svg class="nav-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"/>
                </svg>
                Gestionar Servicio
            </a>
        </div>
        
    
    <div class="nav-item">
      <a href="/formularioInventario" class="nav-link">
        <svg class="nav-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"/>
        </svg>
        Gestionar Inventario
      </a>
    </div>
    
    <div class="nav-item">
      <a href="/formularioOrdenDeTrabajo" class="nav-link">
        <svg class="nav-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/>
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
        </svg>
        Orden de Trabajo
      </a>
    </div>
    
    <div class="nav-item">
      <a href="/formularioProveedor" class="nav-link">
        <svg class="nav-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
        </svg>
        Gestionar Proveedor
      </a>
    </div>
    
    <div class="infinity-badge">
      <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
      </svg>
      Infinity Iterators
    </div>
  </div>

  <div class="content">
    <h1 class="page-title">Gestión de Vehículos</h1>

    <!-- Main Form -->
    <div class="glass-card">
      <form action="/guardarVehiculo" method="post">
        <input type="hidden" th:field="${vehiculo.id_Vehiculo}">
        <div class="form-row">
          <div class="form-group col-md-6">
            <label for="marca">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/>
              </svg>
              Marca
            </label>
            <input type="text" class="form-control" th:field="${vehiculo.marca}" placeholder="Ingrese la marca...">
          </div>
          <div class="form-group col-md-6">
            <label for="modelo">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"/>
              </svg>
              Modelo
            </label>
            <input type="text" class="form-control" th:field="${vehiculo.modelo}" placeholder="Ingrese el modelo...">
          </div>
        </div>
        <div class="form-row">
          <div class="form-group col-md-6">
            <label for="anio">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
              </svg>
              Año
            </label>
            <input type="text" class="form-control" th:field="${vehiculo.anio}" placeholder="Ingrese el año...">
          </div>
          <div class="form-group col-md-6">
            <label for="placa">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
              </svg>
              Placa
            </label>
            <input type="text" class="form-control" th:field="${vehiculo.placa}" placeholder="Ingrese la placa...">
          </div>
        </div>
        <div class="form-row">
          <div class="form-group col-md-6">
            <label for="numSerie">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>
              </svg>
              Número de Serie
            </label>
            <input type="text" class="form-control" th:field="${vehiculo.numSerie}" placeholder="Ingrese el número de serie...">
          </div>
          <div class="form-group col-md-6">
            <label for="color">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01"/>
              </svg>
              Color
            </label>
            <input type="text" class="form-control" th:field="${vehiculo.color}" placeholder="Ingrese el color...">
          </div>
          <div class="form-row">
    <div class="form-group col-md-16">
      <label for="cliente">Seleccionar Cliente:</label>
      <select class="form-control" th:field="${vehiculo.cliente}">
        <option value="">-- Seleccione un cliente --</option>
        <option th:each="cliente : ${clientes}" 
                th:value="${cliente.id_Cliente}" 
                th:text="${cliente.nombre + ' ' + cliente.apellido + ' - ' + cliente.telefono}">
        </option>
      </select>
    </div>
     </div>

        </div>
        <div class="mt-4">
          <button type="submit" class="modern-btn btn-primary">
            <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
            </svg>
            Guardar Vehículo
          </button>
          <button type="reset" class="modern-btn btn-secondary ml-3">
            <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
            </svg>
            Limpiar Formulario
          </button>
        </div>
      </form>
    </div>

    <!-- Search Form -->
    <div class="glass-card">
      <form id="formBuscar" action="/buscarVehiculoPorPlaca" method="post">
        <div class="row align-items-end">
          <div class="col-md-4">
            <div class="form-group">
              <label for="placa">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
                </svg>
                Buscar por Placa
              </label>
              <input type="text" class="form-control" name="placa" placeholder="Ingrese la placa..." required>
            </div>
          </div>
          <div class="col-md-2">
            <button type="submit" class="modern-btn btn-success">
              <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
              </svg>
              Buscar
            </button>
          </div>
        </div>
      </form>
    </div>

    <!-- Gráfico de distribución -->
    <div class="glass-card">
      <h3 class="mt-0 mb-4">Distribución de Motocicletas por Marca Registrados</h3>
      <canvas id="chartMarcas" width="200" height="80"></canvas>
    </div>

    <!-- Enhanced Table -->
    <div class="modern-table">
      <table class="table table-hover">
        <thead>
          <tr>
            <th>
              <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/>
              </svg>
              Marca
            </th>
            <th>
              <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"/>
              </svg>
              Modelo
            </th>
            <th>
              <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
              </svg>
              Año
            </th>
            <th>
              <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
              </svg>
              Placa
            </th>
            <th>
              <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>
              </svg>
              Número de Serie
            </th>
            <th>
              <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01"/>
              </svg>
              Color
            </th>
            <th>
  <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
          d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/>
  </svg>
  Cliente
</th>
            <th>
              <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/>
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
              </svg>
              Acciones
            </th>
          </tr>
        </thead>
        <tbody id="tablaDatos">
          <tr th:each="v: ${vehiculos}">
            <td th:text="${v.marca}"></td>
            <td th:text="${v.modelo}"></td>
            <td th:text="${v.anio}"></td>
            <td th:text="${v.placa}"></td>
            <td th:text="${v.numSerie}"></td>
            <td th:text="${v.color}"></td>
           <td th:text="${v.cliente?.nombre + ' - ' + v.cliente?.telefono}"></td>
            <td>
              <div class="action-buttons">
                <a th:href="'/editarVehiculo/' + ${v.id_Vehiculo}" class="modern-btn btn-info btn-sm edit-btn" data-toggle="tooltip" title="Editar">
                  <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                  </svg>
                </a>
                <a th:href="'/eliminarVehiculo/' + ${v.id_Vehiculo}" class="modern-btn btn-danger btn-sm delete-btn" data-toggle="tooltip" title="Eliminar">
                  <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                  </svg>
                </a>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>

  <!-- Floating Action Button -->
  <div class="fab" onclick="scrollToTop()">
    <svg width="24" height="24" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 10l7-7m0 0l7 7m-7-7v18"/>
    </svg>
  </div>

  <!-- Scripts -->
  <script src="https://code.jquery.com/jquery-3.5.1.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/@popperjs/core@2.5.4/dist/umd/popper.min.js"></script>
  <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
  
  <script>
    // Animated particles background
    function createParticles() {
      const particles = document.getElementById('particles');
      const particleCount = 100;
      
      for (let i = 0; i < particleCount; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        particle.style.left = Math.random() * 100 + '%';
        particle.style.top = Math.random() * 100 + '%';
        particle.style.animationDelay = Math.random() * 8 + 's';
        particle.style.animationDuration = (Math.random() * 5 + 5) + 's';
        particle.style.width = (Math.random() * 3 + 2) + 'px';
        particle.style.height = particle.style.width;
        particles.appendChild(particle);
      }
    }
    
    // Initialize particles
    createParticles();
    
    // Enhanced SweetAlert2 configurations with glassmorphism effect
    $(document).ready(function () {
      // Initialize tooltips
      $('[data-toggle="tooltip"]').tooltip();
      
      $('.edit-btn').click(function (event) {
        event.preventDefault();
        const url = $(this).attr('href');
        
        Swal.fire({
          title: '✏️ Editar Vehículo',
          text: '¿Deseas modificar este vehículo?',
          icon: 'question',
          showCancelButton: true,
          confirmButtonColor: '#0066ff',
          cancelButtonColor: '#ff3366',
          confirmButtonText: '✓ Sí, editar',
          cancelButtonText: '✗ Cancelar',
          background: 'rgba(15, 23, 42, 0.9)',
          backdrop: `
            rgba(0, 102, 255, 0.4)
            url("data:image/svg+xml,%3csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3e%3cg fill='none' fill-rule='evenodd'%3e%3cg fill='%230066ff' fill-opacity='0.1'%3e%3ccircle cx='30' cy='30' r='4'/%3e%3c/g%3e%3c/g%3e%3c/svg%3e")
            center left no-repeat
          `,
          customClass: {
            popup: 'animate__animated animate__fadeInUp',
            title: 'text-primary',
            confirmButton: 'modern-btn btn-primary',
            cancelButton: 'modern-btn btn-danger'
          },
          buttonsStyling: false
        }).then((result) => {
          if (result.isConfirmed) {
            // Show loading with glass effect
            Swal.fire({
              title: 'Cargando...',
              text: 'Preparando el formulario de edición',
              allowOutsideClick: false,
              background: 'rgba(15, 23, 42, 0.9)',
              backdrop: `
                rgba(0, 102, 255, 0.2)
                url("data:image/svg+xml,%3csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3e%3cg fill='none' fill-rule='evenodd'%3e%3cg fill='%2300ffcc' fill-opacity='0.1'%3e%3ccircle cx='30' cy='30' r='4'/%3e%3c/g%3e%3c/g%3e%3c/svg%3e")
                center left no-repeat
              `,
              didOpen: () => {
                Swal.showLoading()
              }
            });
            
            setTimeout(() => {
              window.location.href = url;
            }, 1000);
          }
        });
      });

      $('.delete-btn').click(function (event) {
        event.preventDefault();
        const url = $(this).attr('href');
        
        Swal.fire({
          title: '🗑️ Eliminar Vehículo',
          text: '¡Esta acción no se puede deshacer!',
          icon: 'warning',
          showCancelButton: true,
          confirmButtonColor: '#ff3366',
          cancelButtonColor: '#6c757d',
          confirmButtonText: '🗑️ Sí, eliminar',
          cancelButtonText: '↩️ Cancelar',
          background: 'rgba(15, 23, 42, 0.9)',
          backdrop: `
            rgba(255, 51, 102, 0.4)
            url("data:image/svg+xml,%3csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3e%3cg fill='none' fill-rule='evenodd'%3e%3cg fill='%23ff3366' fill-opacity='0.1'%3e%3cpath d='M30 0l4 8h8l-6 6 2 8-8-4-8 4 2-8-6-6h8z'/%3e%3c/g%3e%3c/g%3e%3c/svg%3e")
            center left no-repeat
          `,
          customClass: {
            popup: 'animate__animated animate__shakeX',
            title: 'text-danger',
            confirmButton: 'modern-btn btn-danger',
            cancelButton: 'modern-btn btn-secondary'
          },
          buttonsStyling: false
        }).then((result) => {
          if (result.isConfirmed) {
            // Show success message with glass effect
            Swal.fire({
              title: '¡Eliminado!',
              text: 'El vehículo ha sido eliminado correctamente.',
              icon: 'success',
              timer: 2000,
              showConfirmButton: false,
              background: 'rgba(15, 23, 42, 0.9)',
              backdrop: `
                rgba(0, 255, 204, 0.2)
                url("data:image/svg+xml,%3csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3e%3cg fill='none' fill-rule='evenodd'%3e%3cg fill='%2300ffcc' fill-opacity='0.1'%3e%3ccircle cx='30' cy='30' r='4'/%3e%3c/g%3e%3c/g%3e%3c/svg%3e")
                center left no-repeat
              `,
              customClass: {
                popup: 'animate__animated animate__bounceIn'
              }
            });
            
            setTimeout(() => {
              window.location.href = url;
            }, 2000);
          }
        });
      });
      
      // Form validation enhancement
      $('form').on('submit', function(e) {
        const requiredFields = $(this).find('[required]');
        let hasError = false;
        
        requiredFields.each(function() {
          if (!$(this).val()) {
            hasError = true;
            $(this).addClass('is-invalid');
          } else {
            $(this).removeClass('is-invalid');
          }
        });
        
        if (hasError) {
          e.preventDefault();
          Swal.fire({
            title: '⚠️ Campos Requeridos',
            text: 'Por favor, complete todos los campos obligatorios.',
            icon: 'warning',
            confirmButtonColor: '#ffcc00',
            confirmButtonText: 'Entendido',
            background: 'rgba(15, 23, 42, 0.9)',
            customClass: {
              confirmButton: 'modern-btn btn-warning'
            },
            buttonsStyling: false
          });
        }
      });
      
      // Enhanced form animations
      $('.form-control').on('focus', function() {
        $(this).closest('.form-group').addClass('focused');
      }).on('blur', function() {
        $(this).closest('.form-group').removeClass('focused');
      });
      
      // Table row animations
      $('.table tbody tr').each(function(index) {
        $(this).css('animation-delay', (index * 0.1) + 's');
      });
      
      // Show floating action button when scrolling
      $(window).scroll(function() {
        if ($(this).scrollTop() > 300) {
          $('.fab').fadeIn();
        } else {
          $('.fab').fadeOut();
        }
      });
      
      // Gráfico de distribución de marcas (sin cambios)
      function obtenerDatosTabla() {
        var marcas = [];
        var vehiculosPorMarca = [];
  
        // Recorrer las filas de la tabla de vehículos y contar los vehículos por marca
        $('#tablaDatos tr').each(function(){
          var marca = $(this).find('td:nth-child(1)').text(); // Obtener el texto de la primera columna (marca)
          var indice = marcas.indexOf(marca);
  
          if (indice === -1) {
            marcas.push(marca);
            vehiculosPorMarca.push(1); // Comenzar con un vehículo para esta marca
          } else {
            vehiculosPorMarca[indice]++;
          }
        });
  
        return { marcas: marcas, vehiculosPorMarca: vehiculosPorMarca };
      }
  
      // Obtener los datos de la tabla
      var datosTabla = obtenerDatosTabla();
  
      // Colores vibrantes predefinidos para evitar repeticiones
      var colores = [
        'rgba(255, 99, 132, 0.6)',   // Rojo
        'rgba(54, 162, 235, 0.6)',   // Azul
        'rgba(255, 206, 86, 0.6)',   // Amarillo
        'rgba(75, 192, 192, 0.6)',   // Verde Agua
        'rgba(153, 102, 255, 0.6)',  // Púrpura
        'rgba(255, 159, 64, 0.6)',   // Naranja
        'rgba(255, 99, 71, 0.6)',    // Tomate
        'rgba(127, 255, 0, 0.6)',    // Verde Lima
        'rgba(0, 255, 255, 0.6)',    // Cian
        'rgba(255, 20, 147, 0.6)',   // Rosa Profundo
        'rgba(240, 230, 140, 0.6)'   // Caqui
      ];
  
      // Configurar el gráfico de barras con los datos obtenidos
      var ctx = document.getElementById('chartMarcas').getContext('2d');
      var myChart = new Chart(ctx, {
        type: 'bar',
        data: {
          labels: datosTabla.marcas,
          datasets: [{
            label: 'Marca de Vehículos más frecuente',
            data: datosTabla.vehiculosPorMarca,
            backgroundColor: colores.slice(0, datosTabla.marcas.length), // Asignar colores únicos
            borderColor: colores.slice(0, datosTabla.marcas.length).map(color => color.replace('0.6', '1')), // Colores con opacidad total para los bordes
            borderWidth: 1
          }]
        },
        options: {
          responsive: true,
          scales: {
            xAxes: [{
              ticks: {
                autoSkip: false,
                maxRotation: 0, // Rotación de 0 grados para que las etiquetas sean legibles
                minRotation: 0
              }
            }],
            yAxes: [{
              ticks: {
                beginAtZero: true
              }
            }]
          }
        }
      });
    });
    
    // Mobile menu toggle (for responsive design)
    function toggleSidebar() {
      $('.sidebar').toggleClass('mobile-hidden');
    }
    
    // Scroll to top function
    function scrollToTop() {
      $('html, body').animate({ scrollTop: 0 }, 'smooth');
    }
    
    // Add animation to page title on hover
    $('.page-title').hover(
      function() {
        $(this).addClass('animate__animated animate__pulse');
      },
      function() {
        $(this).removeClass('animate__animated animate__pulse');
      }
    );
  </script>
</body>
</html>
