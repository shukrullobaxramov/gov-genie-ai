import streamlit as st
import psycopg2
import pandas as pd

# Саҳифа созламалари
st.set_page_config(page_title="МФЙ Инвентаризация", layout="wide", page_icon="🏢")

# Маҳаллалар рўйхати
mfy_list = [
    "Гулбоғ", "Хўжамозор", "Асил", "Ўрта", "Эски қалъа", "Сортепа", "Боғзор", "Абдужалилбоб", 
    "Ўртаовул", "Обод турмуш", "Катта чинор", "Олмазор", "Файз", "Кенг кечик", "Эшонгузар", 
    "Амир Темур", "Нурафшон", "Намуна", "Навқирон", "Ўратепа", "Далигазар", "Обод", "Токзор", 
    "Назарбек", "М.М.Хоразмий", "Фаробий", "Ахилобод", "Найман", "Ахмад Яссавий", "Бўстон", 
    "Истиқлолнинг 5-йиллиги", "Боғишамол", "Саховат", "Тўқимачи", "Балиқчи", "Тарнов", 
    "Навбаҳор", "Шодлик", "Алимбува", "Туропобод", "Рамадон", "Илғор", "Обод тўқимачи", 
    "Ҳаракат", "Мевазор", "Янги бўзсув", "Зарафшон", "Нуробод", "Маданият", "Деҳқонобод", 
    "Чинор", "Ўрикзор", "Истиқлол", "Эркин", "Қурилиш", "Қуёшли", "Тариқ-тешар", "Қаҳрамон", 
    "Бодомзор", "Туркистон"
]

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
                return None
    except Exception as e:
        st.error(f"Хатолик: {e}")
        return []

# --- ИНТЕРФЕЙС ---
st.title("🏢 МФЙ 7 лиги Инвентаризация тизими")

# Маҳаллани танлаш (Асосий филтр)
selected_mfy = st.sidebar.selectbox("🏠 Маҳаллани танланг", mfy_list)
st.sidebar.markdown(f"**Ҳозирги ҳудуд:** {selected_mfy}")

tab1, tab2 = st.tabs(["📋 Жиҳозлар рўйхати", "➕ Янги кирим қилиш"])

with tab1:
    st.subheader(f"{selected_mfy} маҳалласи инвентар рўйхати")
    # Фақат танланган маҳалла маълумотларини олиш
    query = "SELECT item_name, inventory_number, category, condition, responsible_person, price FROM office_inventory WHERE mfy_name = %s"
    data = run_query(query, (selected_mfy,))
    
    if data:
        df = pd.DataFrame(data, columns=["Жиҳоз номи", "Инвентар №", "Тоифа", "Ҳолати", "Масъул", "Нархи"])
        st.dataframe(df, use_container_width=True)
        
        total_sum = df["Нархи"].sum()
        st.metric(f"{selected_mfy} бўйича умумий қиймат", f"{total_sum:,.0f} сўм")
    else:
        st.warning(f"{selected_mfy} маҳалласида ҳали жиҳозлар рўйхатга олинмаган.")

with tab2:
    st.subheader(f"🆕 {selected_mfy} учун янги жиҳоз қўшиш")
    with st.form("add_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        name = col1.text_input("Жиҳоз номи")
        inv_num = col2.text_input("Инвентар рақами")
        cat = col1.selectbox("Тоифа", ["Техника", "Мебель", "Юмшоқ жиҳоз", "Хўжалик"])
        cond = col2.selectbox("Ҳолати", ["Яхши", "Таъмирталаб", "Яроқсиз"])
        resp = col1.selectbox("Масъул", ["Раис", "Ҳоким ёрдамчиси", "Ёшлар етакчиси", "Хотин-қизлар фаоли", "Профилактика инс.", "Солиқ инс.", "Ижтимоий ходим"])
        price = col2.number_input("Нархи (сўм)", min_value=0)
        
        if st.form_submit_button("Сақлаш"):
            if name and inv_num:
                insert_query = """
                    INSERT INTO office_inventory (item_name, inventory_number, category, condition, responsible_person, price, mfy_name)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                run_query(insert_query, (name, inv_num, cat, cond, resp, price, selected_mfy), is_select=False)
                st.success(f"Муваффақиятли сақланди: {name}")
                st.balloons()
            else:
                st.error("Номи ва инвентар рақамини тўлдиринг!")
