def crear_tarjeta_estudiante(estudiante):
    ru = str(estudiante["ru"])
    nombres = estudiante["nombres"]
    paterno = estudiante["apellido_paterno"]
    materno = estudiante["apellido_materno"]
    nombre_completo = f"{nombres} {paterno} {materno}".strip().upper()

    # Tamaño de tarjeta en alta resolución (1600x1600)
    card_size = 1600
    # QR más grande y con mejor calidad
    qr = qrcode.make(ru, box_size=20, border=2)  # box_size=20 para mayor detalle
    qr_size = 1000  # QR de 1000x1000
    qr = qr.resize((qr_size, qr_size), Image.LANCZOS)

    # Fondo con gradiente
    background = Image.new('RGB', (card_size, card_size), color=(10, 20, 40))
    gradient = Image.new('RGBA', (card_size, card_size), (0, 0, 0, 0))
    draw_grad = ImageDraw.Draw(gradient)
    for y in range(card_size):
        blue_intensity = int(60 * (1 - y / card_size))
        draw_grad.rectangle([0, y, card_size, y+1], fill=(0, 0, blue_intensity, 180))
    background = Image.alpha_composite(background.convert('RGBA'), gradient).convert('RGB')
    
    draw = ImageDraw.Draw(background)

    # Fuentes en tamaño grande para alta definición
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/Library/Fonts/Arial Bold.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
    ]
    font_regular_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/Library/Fonts/Arial.ttf",
        "C:\\Windows\\Fonts\\arial.ttf"
    ]
    
    title_font = None
    ru_font = None
    name_font = None
    footer_font = None

    # Buscar fuentes en negrita para textos principales
    for path in font_paths:
        if os.path.exists(path):
            title_font = ImageFont.truetype(path, 112)   # título grande
            ru_font = ImageFont.truetype(path, 96)       # RU grande
            name_font = ImageFont.truetype(path, 88)     # nombre grande
            break
    for path in font_regular_paths:
        if os.path.exists(path):
            footer_font = ImageFont.truetype(path, 56)   # pie de página
            break
    if not title_font:
        title_font = ImageFont.load_default()
        ru_font = ImageFont.load_default()
        name_font = ImageFont.load_default()
        footer_font = ImageFont.load_default()

    # Borde decorativo más grueso
    border_color = (0, 102, 255)
    border_width = 16
    draw.rectangle([0, 0, card_size-1, card_size-1], outline=border_color, width=border_width)

    # Título con contorno y sombra
    title_text = "TARJETA DE IDENTIFICACIÓN"
    bbox = draw.textbbox((0,0), title_text, font=title_font)
    title_width = bbox[2] - bbox[0]
    title_x = (card_size - title_width) // 2
    title_y = 80
    # Contorno negro más grueso
    for offset in [(4,4), (-4,4), (4,-4), (-4,-4)]:
        draw.text((title_x+offset[0], title_y+offset[1]), title_text, fill=(0,0,0), font=title_font)
    draw.text((title_x, title_y), title_text, fill=(255,255,255), font=title_font)

    # RU con contorno
    ru_text = f"RU: {ru}"
    bbox = draw.textbbox((0,0), ru_text, font=ru_font)
    ru_width = bbox[2] - bbox[0]
    ru_x = (card_size - ru_width) // 2
    ru_y = title_y + 160
    for offset in [(3,3), (-3,3), (3,-3), (-3,-3)]:
        draw.text((ru_x+offset[0], ru_y+offset[1]), ru_text, fill=(0,0,0), font=ru_font)
    draw.text((ru_x, ru_y), ru_text, fill=(255,255,200), font=ru_font)

    # Nombre completo: multilínea con más espacio
    max_width = card_size - 160
    words = nombre_completo.split()
    lines = []
    current_line = ""
    for w in words:
        test_line = current_line + (" " + w if current_line else w)
        bbox = draw.textbbox((0,0), test_line, font=name_font)
        if bbox[2] - bbox[0] <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = w
    if current_line:
        lines.append(current_line)

    if not lines:
        lines = [nombre_completo]

    line_spacing = 120
    total_height = len(lines) * line_spacing
    start_y = ru_y + 200
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0,0), line, font=name_font)
        line_width = bbox[2] - bbox[0]
        x = (card_size - line_width) // 2
        y = start_y + i * line_spacing
        for offset in [(3,3), (-3,3), (3,-3), (-3,-3)]:
            draw.text((x+offset[0], y+offset[1]), line, fill=(0,0,0), font=name_font)
        draw.text((x, y), line, fill=(255,255,255), font=name_font)

    # Posicionar QR con más margen
    qr_x = (card_size - qr_size) // 2
    qr_y = start_y + total_height + 40
    background.paste(qr, (qr_x, qr_y))

    # Pie de página
    footer_text = "INGENIERÍA DE SISTEMAS\nUAP"
    lines_footer = footer_text.split("\n")
    footer_y = qr_y + qr_size + 60
    for i, line in enumerate(lines_footer):
        bbox = draw.textbbox((0,0), line, font=footer_font)
        line_width = bbox[2] - bbox[0]
        x = (card_size - line_width) // 2
        y = footer_y + i * 70
        for offset in [(2,2), (-2,2), (2,-2), (-2,-2)]:
            draw.text((x+offset[0], y+offset[1]), line, fill=(0,0,0), font=footer_font)
        draw.text((x, y), line, fill=(220, 220, 255), font=footer_font)

    # Guardar imagen en alta calidad
    img_bytes = io.BytesIO()
    background.save(img_bytes, format='PNG', dpi=(300, 300))  # alta calidad
    img_bytes.seek(0)
    return img_bytes
