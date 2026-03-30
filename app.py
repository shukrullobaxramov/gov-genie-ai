import streamlit as st
import psycopg2
import pandas as pd

# Саҳифа созламалари
st.set_page_config(page_title="МФЙ Инвентаризация", layout="wide", page_icon="🏢")

# Базага уланиш функцияси
def get_connection():
    return psycopg2.connect(st.secrets["DB_URL"])

def run_query(query, params=None, is_select=True):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                if is_select:
                    return cur.fetchall()
                conn.commit()
    except Exception as e:
        st.error(f"Хатолик: {e}")
        return []

# --- ИНТЕРФЕЙС ---
st.title("🏢 МФЙ 7 лиги Асосий воситалар инвентаризацияси")

tab1, tab2 = st.tabs(["📋 Мавжуд жиҳозлар", "➕ Янги қўшиш"])

with tab1:
    st.subheader("Маҳалла биносидаги асосий воситалар рўйхати")
    data = run_query("SELECT item_name, inventory_number, category, condition, responsible_person, price FROM office_inventory")
    
    if data:
        df = pd.DataFrame(data, columns=["Номи", "Инвентар №", "Тоифа", "Ҳолати", "Масъул", "Нархи (сўм)"])
        st.dataframe(df, use_container_width=True)
        
        # Статистика
        total_price = df["Нархи (сўм)"].sum()
        st.metric("Умумий қиймат", f"{total_price:,.2f} сўм")
    else:
        st.info("Ҳозирча базада жиҳозлар мавжуд эмас.")

with tab2:
    st.subheader("Янги асосий воситани рўйхатга олиш")
    with st.form("inventory_form"):
        col1, col2 = st.columns(2)
        name = col1.text_input("Жиҳоз номи (масалан: Компьютер HP)")
        inv_num = col2.text_input("Инвентар рақами")
        cat = col1.selectbox("Тоифа", ["Техника", "Мебель", "Юмшоқ жиҳоз", "Хўжалик моллари"])
        cond = col2.selectbox("Ҳолати", ["Яхши", "Ўрта (таъмирталаб)", "Яроқсиз"])
        resp = col1.selectbox("Масъул ходим", ["Раис", "Ҳоким ёрдамчиси", "Ёшлар етакчиси", "Хотин-қизлар фаоли", "Профилактика инспектори", "Солиқ инспектори", "Ижтимоий ходим"])
        price = col2.number_input("Нархи (сўм)", min_value=0.0)
        
        submitted = st.form_submit_button("Базага сақлаш")
        if submitted:
            run_query("""
                INSERT INTO office_inventory (item_name, inventory_number, category, condition, responsible_person, price)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (name, inv_num, cat, cond, resp, price), is_select=False)
            st.success("Маълумот муваффақиятли қўшилди! Саҳифани янгиланг.")

# --- AI ТАҲЛИЛ (Ихтиёрий) ---
st.markdown("---")
if st.button("🤖 AI орқали ҳолатни таҳлил қилиш"):
    st.info("Бу функция келгуси қадамда тўлиқ ишга тушади.")
