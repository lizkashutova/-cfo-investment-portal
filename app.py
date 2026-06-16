import json
import os
from datetime import datetime
from fastapi import FastAPI, Response
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fpdf import FPDF

app = FastAPI(
    title="АРМ Бизнес-аналитика: СППР оценки инвестиционной привлекательности регионов ЦФО РФ",
    description="Система поддержки принятия решений для оценки регионов ЦФО",
    version="1.0.0"
)

# Монтируем корневую папку для раздачи статических файлов (видео, изображений и т.д.)
app.mount("/static", StaticFiles(directory="."), name="static")

# ВЕРИФИЦИРОВАННЫЙ ДАТАСЕТ ЦФО (Строго из диплома)
RAW_DATA = {
    "Регион": [
        "г. Москва", "Московская область", "Воронежская область", "Калужская область", 
        "Ярославская область", "Тульская область", "Рязанская область", "Тверская область", 
        "Белгородская область", "Липецкая область", "Владимирская область", "Курская область", 
        "Брянская область", "Смоленская область", "Орловская область", "Тамбовская область", 
        "Ивановская область", "Костромская область"
    ],
    "Зарплата": [
        235000, 185000, 168000, 148000, 132000, 128000, 126000, 118000, 115000, 
        108000, 105000, 98000, 96000, 94000, 92000, 89000, 87000, 85000
    ],
    "Вакансии": [
        14200, 2450, 920, 480, 410, 390, 340, 310, 290, 260, 240, 210, 190, 
        180, 160, 140, 130, 110
    ],
    "Напряженность": [
        2.8, 3.2, 4.1, 3.6, 3.9, 4.3, 4.5, 4.7, 5.1, 4.8, 4.6, 5.3, 5.5, 
        5.4, 5.8, 5.9, 6.1, 6.4
    ],
    "Концентрация": [
        0.643, 0.111, 0.042, 0.022, 0.019, 0.018, 0.015, 0.014, 0.013, 0.012, 
        0.011, 0.009, 0.008, 0.008, 0.007, 0.006, 0.006, 0.005
    ]
}

# Генератор псевдослучайных чисел LCG для воспроизводимости осей шума (seed=16)
class LCG:
    def __init__(self, seed):
        self.state = seed
    def next(self):
        self.state = (1664525 * self.state + 1013904223) % 4294967296
        return self.state / 4294967296

class ReportPDF(FPDF):
    def header(self):
        # Draw logo box
        self.set_fill_color(13, 17, 23)
        self.rect(15, 10, 16, 8, style="F")
        self.set_text_color(126, 120, 210)
        self.set_font("Arial", "B", size=10)
        self.text(18.5, 16, "LiZ")
        
        self.set_text_color(30, 41, 59)
        self.set_font("Arial", "", size=9)
        self.text(34, 15.5, "LiZ SPPR")
        
        self.set_text_color(100, 116, 139)
        self.set_font("Arial", "", size=8)
        self.cell(0, 5, "ИНВЕСТИЦИОННЫЙ ПАСПОРТ РЕГИОНОВ ЦФО РФ", align="R", new_x="LMARGIN", new_y="NEXT")
        self.cell(0, 5, "Интеллектуальная СППР v3.5", align="R", new_x="LMARGIN", new_y="NEXT")
        
        # Line separator
        self.set_draw_color(226, 232, 240)
        self.line(15, 23, 195, 23)
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_draw_color(226, 232, 240)
        self.line(15, self.get_y(), 195, self.get_y())
        self.ln(2)
        self.set_text_color(148, 163, 184)
        self.set_font("Arial", "", size=7)
        self.cell(0, 5, "Отчет подготовлен автоматически в АРМ «Инвест-Диагностика». Разработка: Шутова Е.Д. • БГТУ «Военмех» им. Д.Ф. Устинова", align="C")

def generate_pdf_bytes(selected_region, w_cadres, w_econ, w_infra, w_innov, w_risks, raw_data):
    # Calculations
    salaries = raw_data["Зарплата"]
    vacancies = raw_data["Вакансии"]
    tensions = raw_data["Напряженность"]
    concentrations = raw_data["Концентрация"]
    regions = raw_data["Регион"]

    salMin, salMax = min(salaries), max(salaries)
    vacMin, vacMax = min(vacancies), max(vacancies)
    tenMin, tenMax = min(tensions), max(tensions)
    concMin, concMax = min(concentrations), max(concentrations)

    lcg = LCG(16)
    results = []
    for i, name in enumerate(regions):
        sal = salaries[i]
        vac = vacancies[i]
        ten = tensions[i]
        conc = concentrations[i]

        i_cadres = (ten - tenMin) / (tenMax - tenMin)
        i_econ = 1.0 - (sal - salMin) / (salMax - salMin)
        i_infra = (conc - concMin) / (concMax - concMin)

        v_norm = (vac - vacMin) / (vacMax - vacMin)
        noise_innov = lcg.next() * 0.3
        i_innov = min(1.0, max(0.0, v_norm * 0.7 + noise_innov))

        if name == "Белгородская область":
            i_risks = 0.15
            lcg.next()
        else:
            noise_risks = lcg.next() * 0.2
            i_risks = min(1.0, max(0.0, 1.0 - (i_infra * 0.4) - noise_risks))

        # Recalculate dynamic index
        divisor = (w_cadres + w_econ + w_infra + w_innov + w_risks) or 1.0
        weighted_sum = (
            i_cadres * w_cadres +
            i_econ * w_econ +
            i_infra * w_infra +
            i_innov * w_innov +
            i_risks * w_risks
        )
        integral_index = weighted_sum / divisor

        results.append({
            "region": name,
            "salary": sal,
            "vacancies": vac,
            "tension": ten,
            "i_cadres": i_cadres,
            "i_econ": i_econ,
            "i_infra": i_infra,
            "i_innov": i_innov,
            "i_risks": i_risks,
            "integral_index": integral_index
        })

    # Sort results
    sorted_results = sorted(results, key=lambda r: r["integral_index"], reverse=True)
    reg_data = next((r for r in results if r["region"] == selected_region), sorted_results[0])

    # Expert advice logic
    indices = [
        {"key": "i_cadres", "name": "Доступность кадров", "val": reg_data["i_cadres"]},
        {"key": "i_econ", "name": "Экономическая выгода (ФОТ)", "val": reg_data["i_econ"]},
        {"key": "i_infra", "name": "Инфраструктурная зрелость (Среда)", "val": reg_data["i_infra"]},
        {"key": "i_innov", "name": "Инновационная активность", "val": reg_data["i_innov"]},
        {"key": "i_risks", "name": "Стабильность среды / Риски", "val": reg_data["i_risks"]}
    ]
    limiting_factor = min(indices, key=lambda x: x["val"])

    recommendation_text = ""
    if limiting_factor["key"] == "i_econ":
        recommendation_text = "Рынок труда территории перегрет. Рекомендуется вынос линейных ИТ-подразделений на периферию округа для оптимизации ФОТ."
    elif limiting_factor["key"] == "i_cadres":
        recommendation_text = "Острый дефицит соискателей. Необходим запуск программ переподготовки и расширение ИТ-квот в вузах."
    elif limiting_factor["key"] in ["i_infra", "i_innov"]:
        recommendation_text = "Цифровая экосистема развита слабо. Рекомендуется введение льготных ставок по УСН (до 1%) для ИТ-бизнеса и гранты на строительство технопарков."
    elif limiting_factor["key"] == "i_risks":
        recommendation_text = "Повышенный уровень структурных рисков территории. Требуется внедрение специализированных региональных механизмов страхования активов."

    # Build PDF
    pdf = ReportPDF(orientation="P", unit="mm", format="A4")
    pdf.add_font("Arial", "", "Arial.ttf")
    pdf.add_font("Arial", "B", "Arial.ttf")
    pdf.add_page()
    pdf.set_margins(15, 15, 15)

    # Document title
    pdf.set_text_color(0, 102, 204) # #0066cc
    pdf.set_font("Arial", "B", size=15)
    pdf.cell(0, 8, "ОТЧЕТ ОБ ИНВЕСТИЦИОННОЙ ПРИВЛЕКАТЕЛЬНОСТИ ЦФО", new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_text_color(100, 116, 139)
    pdf.set_font("Arial", "", size=9)
    pdf.cell(0, 5, "Сгенерировано автоматически на основе текущей пользовательской настройки весов критериев.", new_x="LMARGIN", new_y="NEXT")
    
    date_str = datetime.now().strftime("%d.%m.%Y %H:%M")
    pdf.cell(0, 5, f"Дата отчета: {date_str}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # Section 1: Weights
    pdf.set_text_color(30, 41, 59)
    pdf.set_font("Arial", "B", size=10)
    pdf.cell(0, 6, "1. КОНФИГУРАЦИЯ ВЕСОВ КРИТЕРИЕВ", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)
    
    # Draw weights horizontal cards
    w_labels = ["Кадры", "Экономика", "Среда", "Инновации", "Риски"]
    w_vals = [w_cadres, w_econ, w_infra, w_innov, w_risks]
    col_width = 33
    
    pdf.set_font("Arial", "", size=8)
    for label in w_labels:
        pdf.cell(col_width, 5, label, border=1, align="C")
    pdf.ln(5)
    
    pdf.set_font("Arial", "B", size=9)
    for val in w_vals:
        pdf.cell(col_width, 6, f"{val:.2f}", border=1, align="C")
    pdf.ln(10)

    # Section 2: Rating Table (Top-5)
    pdf.set_font("Arial", "B", size=10)
    pdf.cell(0, 6, "2. ИНТЕГРАЛЬНЫЙ РЕЙТИНГ ПРИВЛЕКАТЕЛЬНОСТИ РЕГИОНОВ (ТОП-5)", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)
    
    # Table headers
    headers = ["Место", "Субъект РФ", "Индекс", "Вакансии IT", "Медианная ЗП", "Напряженность"]
    widths = [15, 50, 25, 25, 30, 25]
    
    pdf.set_fill_color(241, 245, 249)
    pdf.set_font("Arial", "B", size=8)
    for h, w in zip(headers, widths):
        pdf.cell(w, 6, h, border=1, align="C" if h != "Субъект РФ" else "L", fill=True)
    pdf.ln(6)

    # Table rows
    pdf.set_font("Arial", "", size=8)
    for idx, item in enumerate(sorted_results[:5]):
        pdf.cell(widths[0], 6, str(idx + 1), border=1, align="C")
        pdf.cell(widths[1], 6, item["region"], border=1)
        pdf.cell(widths[2], 6, f"{item['integral_index']:.4f}", border=1, align="R")
        pdf.cell(widths[3], 6, f"{item['vacancies']:,}", border=1, align="R")
        pdf.cell(widths[4], 6, f"{item['salary']:,} руб.", border=1, align="R")
        pdf.cell(widths[5], 6, f"{item['tension']:.1f}", border=1, align="R")
        pdf.ln(6)
    pdf.ln(6)

    # Section 3: Recommendations
    pdf.set_font("Arial", "B", size=10)
    pdf.cell(0, 6, "3. ЗАКЛЮЧЕНИЕ ЭКСПЕРТНОЙ СИСТЕМЫ", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)
    
    # Draw gray box with recommendations
    pdf.set_fill_color(248, 250, 252)
    pdf.rect(15, pdf.get_y(), 180, 50, style="F")
    pdf.set_draw_color(0, 102, 204)
    pdf.line(15, pdf.get_y(), 15, pdf.get_y() + 50) # Thick blue left border
    
    pdf.set_y(pdf.get_y() + 2)
    pdf.set_x(18)
    pdf.set_font("Arial", "B", size=9)
    pdf.set_text_color(0, 102, 204)
    pdf.cell(0, 5, f"Региональный фокус: {reg_data['region']}", new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_x(18)
    pdf.set_font("Arial", "", size=8)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(0, 5, f"Интегральный индекс региона составляет: {reg_data['integral_index']:.4f}", new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_x(18)
    pdf.cell(0, 5, f"Лимитирующий субиндекс: «{limiting_factor['name']}» с оценкой {limiting_factor['val']:.3f}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    
    pdf.set_x(18)
    pdf.set_font("Arial", "B", size=8.5)
    pdf.cell(0, 5, "Рекомендация аналитика:", new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_x(18)
    pdf.set_font("Arial", "", size=8.5)
    pdf.multi_cell(172, 5, recommendation_text)

    # Return PDF bytes
    return bytes(pdf.output())

# Главная страница
@app.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def read_root():
    # Читаем файл шаблона
    with open("templates/index.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    
    # Генерируем опции для выпадающего списка регионов
    options_html = ""
    for reg in RAW_DATA["Регион"]:
        options_html += f'<option value="{reg}">{reg}</option>\n'
        
    # Кодируем RAW_DATA в JSON-строку
    data_json = json.dumps(RAW_DATA, ensure_ascii=False)
    
    # Выполняем точечные строковые замены, исключая Jinja2 компиляцию
    html_content = html_content.replace("{{ author }}", "Шутова Елизавета Дмитриевна")
    html_content = html_content.replace("{{ university }}", "БГТУ «Военмех» им. Д.Ф. Устинова")
    html_content = html_content.replace("{{ data_json | safe }}", data_json)
    
    # Заменяем блок цикла Jinja2 на готовый сгенерированный HTML
    start_tag = "{% for reg in regions %}"
    end_tag = "{% endfor %}"
    
    if start_tag in html_content and end_tag in html_content:
        start_idx = html_content.find(start_tag)
        end_idx = html_content.find(end_tag) + len(end_tag)
        # Вырезаем блок цикла и вставляем плоский HTML
        html_content = html_content[:start_idx] + options_html + html_content[end_idx:]
        
    return HTMLResponse(content=html_content, status_code=200)

@app.get("/api/download_pdf")
async def download_pdf(
    region: str,
    w_cadres: float,
    w_econ: float,
    w_infra: float,
    w_innov: float,
    w_risks: float
):
    pdf_bytes = generate_pdf_bytes(region, w_cadres, w_econ, w_infra, w_innov, w_risks, RAW_DATA)
    headers = {
        "Content-Disposition": "attachment; filename=\"Investment_Report.pdf\""
    }
    return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8085)
