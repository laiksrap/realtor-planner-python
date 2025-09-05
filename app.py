import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
import random
import io

TYPES = ["Совет","Обзор объекта","История сделки","Рынок/аналитика","FAQ покупателя","Ипотека/ставки","Район vs район"]
CITIES = ["Ижевск","Казань","Пермь","Екатеринбург","Уфа","Тюмень","Нижний Новгород","Самара","Санкт-Петербург","Москва"]
DISTRICTS = ["центр","новый город","пригород","спальный район","деловой квартал","район у набережной"]
HOOKS = [
    "3 ошибки, из-за которых теряют деньги",
    "Как выбрать без сюрпризов",
    "Что не расскажут в рекламе",
    "Гид для занятых",
    "Только факты"
]
CTA = [
    "Сохраните пост — пригодится.",
    "Задайте вопрос в ЛС — отвечу сегодня.",
    "Нужен подбор? Напишите «ПОДБОР».",
    "Записать вас на показ?"
]

def rand(arr): return random.choice(arr)

def make_title(t):
    city, dA, dB = rand(CITIES), rand(DISTRICTS), rand(DISTRICTS)
    if t == "Совет": return f"{rand(HOOKS)} при покупке в {city}"
    if t == "Обзор объекта": return f"Обзор: двушка в {dA}, {city} — стоит ли брать?"
    if t == "История сделки": return "Как мы сбили цену на 350 тыс.: реальный кейс"
    if t == "Рынок/аналитика": return f"{city}: что происходит с ценами в этом месяце"
    if t == "FAQ покупателя": return "Отвечаю на частый вопрос: что проверить на показе"
    if t == "Ипотека/ставки": return "Ипотека без паники: как читать одобрение банка"
    if t == "Район vs район": return f"{dA} vs {dB}: где жить удобнее в {city}?"
    return f"Полезное для покупателей в {city}"

def make_text(t, tone):
    if tone == "Дружеская":
        tone_line = "Пишу простым языком, без сложных терминов."
    elif tone == "Легкий юмор":
        tone_line = "Немного иронии — но по делу."
    else:
        tone_line = "Коротко и по делу, как для занятых людей."
    benefits = [
        "сравнивайте не только цену м², но и расходы после покупки — ремонт, мебель, коммуналка;",
        "смотрите на шум, солнце и двор в разное время суток;",
        "узнавайте план ремонта у застройщика и реальную толщину стен;",
        "просите расчёт ипотеки у 2–3 банков — всегда есть разница;",
        "не стесняйтесь торговаться — аргументы решают."
    ]
    return "\n".join([
        tone_line,
        f"Что важно: {rand(benefits)} {rand(benefits)}",
        "Мой совет: сначала критерии (район, бюджет, сроки), потом показы.",
        rand(CTA)
    ])

def make_tags(t, platform):
    base = ["#недвижимость","#квартира","#покупка","#ипотека","#риелтор","#советы"]
    spec = {
        "Совет":["#лайфхаки","#чеклист"],
        "Обзор объекта":["#обзор","#новостройка","#вторичка"],
        "История сделки":["#реальныйкейс","#переговоры"],
        "Рынок/аналитика":["#аналитика","#цены","#ставки"],
        "FAQ покупателя":["#вопросответ","#faq"],
        "Ипотека/ставки":["#банк","#процентнаяставка"],
        "Район vs район":["#локация","#район"]
    }.get(t, [])
    plat = {"Telegram":["#телеграм"], "VK":["#вконтакте"], "Instagram":["#instagram"]}.get(platform, [])
    return " ".join(base + spec + plat)

def start_of_week(d: date) -> date:
    return d - timedelta(days=(d.weekday()))

def generate_week(start: date, platforms, posts_per_week, tone):
    rows = []
    for p in platforms:
        days = list(range(7))
        random.shuffle(days)
        chosen = sorted(days[:max(1, min(7, posts_per_week))])
        for offset in chosen:
            dt = start + timedelta(days=offset)
            typ = rand(TYPES)
            rows.append({
                "Дата": dt.strftime("%Y-%m-%d"),
                "Время": "09:00",
                "Платформа": p,
                "Тип": typ,
                "Заголовок": make_title(typ),
                "Текст": make_text(typ, tone),
                "Хэштеги": make_tags(typ, p),
                "Статус": "Черновик"
            })
    df = pd.DataFrame(rows).sort_values(["Дата","Время","Платформа"]).reset_index(drop=True)
    return df

def to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")

def to_ics_bytes(df: pd.DataFrame) -> bytes:
    def z(n): return str(n).zfill(2)
    lines = ["BEGIN:VCALENDAR","VERSION:2.0","PRODID:-//Realtor Planner//RU"]
    for i, row in df.iterrows():
        y, m, d = row["Дата"].split("-")
        hh, mm = (row.get("Время","09:00") or "09:00").split(":")
        dt = f"{y}{m}{d}T{z(hh)}{z(mm)}00"
        summary = f"{row['Платформа']} · {row['Заголовок']}".replace("\n","\\n").replace(",","\\,").replace(";","\\;")
        desc = (f"{row['Текст']}\n\n{row['Хэштеги']}").replace("\n","\\n").replace(",","\\,").replace(";","\\;")
        uid = f"{i}-{row['Дата']}-{row['Платформа']}"
        lines += [
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTART:{dt}",
            f"SUMMARY:{summary}",
            f"DESCRIPTION:{desc}",
            "END:VEVENT"
        ]
    lines.append("END:VCALENDAR")
    return ("\r\n".join(lines)).encode("utf-8")

st.set_page_config(page_title="Генератор контента для риелторов", page_icon="📅", layout="wide")
st.title("📅 Генератор контента для риелторов — Python (Streamlit)")

with st.sidebar:
    st.markdown("### Настройки")
    tone = st.selectbox("Тональность", ["Экспертная","Дружеская","Легкий юмор"])
    platforms = st.multiselect("Платформы", ["VK","Telegram","Instagram"], default=["VK","Telegram","Instagram"])
    posts_per_week = st.number_input("Постов в неделю (на каждую платформу)", 1, 7, 3)
    start_input = st.date_input("Неделя начинается", start_of_week(date.today()))
    start_week = start_of_week(start_input)
    st.caption("Подсказка: неделя считается с понедельника.")

col1, col2 = st.columns([1,1])
with col1:
    if st.button("Сгенерировать неделю", use_container_width=True):
        st.session_state["plan"] = generate_week(start_week, platforms, posts_per_week, tone)
with col2:
    if st.button("Очистить", use_container_width=True):
        st.session_state["plan"] = pd.DataFrame(columns=["Дата","Время","Платформа","Тип","Заголовок","Текст","Хэштеги","Статус"])

plan: pd.DataFrame = st.session_state.get("plan", pd.DataFrame(columns=["Дата","Время","Платформа","Тип","Заголовок","Текст","Хэштеги","Статус"]))

st.markdown("### План (редактируемый)")
edited = st.data_editor(
    plan,
    num_rows="dynamic",
    use_container_width=True,
    height=480,
    column_config={
        "Дата": st.column_config.DateColumn(format="YYYY-MM-DD"),
        "Время": st.column_config.TextColumn(help="например 09:00"),
        "Платформа": st.column_config.SelectboxColumn(options=["VK","Telegram","Instagram"]),
        "Тип": st.column_config.SelectboxColumn(options=TYPES),
        "Статус": st.column_config.SelectboxColumn(options=["Черновик","Готово","Опубликовано"]),
        "Хэштеги": st.column_config.TextColumn(help="через пробел")
    }
)
st.session_state["plan"] = edited

total = len(edited)
done = (edited["Статус"] != "Черновик").sum() if total else 0
st.info(f"Готовность: {done}/{total}")

colA, colB, colC = st.columns(3)
with colA:
    st.download_button("⬇️ Экспорт CSV", data=to_csv_bytes(edited), file_name=f"content-plan-{start_week}.csv", mime="text/csv")
with colB:
    st.download_button("⬇️ Экспорт ICS", data=to_ics_bytes(edited), file_name=f"content-plan-{start_week}.ics", mime="text/calendar")
with colC:
    st.caption("Импорт CSV можно будет добавить позже (парсер + загрузка файла).")

st.caption("© Твой прототип на Python/Streamlit. Дальше можно прикрутить Google Sheets, БД или ChatGPT API.")
