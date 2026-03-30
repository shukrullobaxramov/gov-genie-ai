import streamlit as st
import psycopg2
import pandas as pd

# Саҳифа созламалари
st.set_page_config(page_title="МФЙ Инвентаризация", layout="wide", page_icon="🏢")

# 1. Маҳаллалар рўйхати (Алфавит бўйича сараланган)
mfy_list = sorted([
    "Гулбоғ", "Хўжамозор", "Асил", "Ўрта", "Эски қалъа", "Сортепа", "Боғзор", "Абдужалилбоб", 
    "Ўртаовул", "Обод турмуш", "Катта чинор", "Олмазор", "Файз", "Кенг кечик", "Эшонгузар", 
    "Амир Темур", "Нурафшон", "Намуна", "Навқирон", "Ўратепа", "Далигазар", "Обод", "Токзор", 
    "Назарбек", "М.М.Хоразмий", "Фаробий", "Ахилобод", "Найман", "Ахмад Яссавий", "Бўстон", 
    "Истиқлолнинг 5-йиллиги", "Боғишамол", "Саховат", "Тўқимачи", "Балиқчи", "Тарнов", 
    "Навбаҳор", "Шодлик", "Алимбува", "Туропобод", "Рамадон", "Илғор", "Обод тўқимачи", 
    "Ҳаракат", "Мевазор", "Янги бўзсув", "Зарафшон", "Нуробод", "Маданият", "Деҳқонобод", 
    "Чинор", "Ўрикзор", "Истиқлол", "Эркин", "Қурилиш", "Қуёшли", "Тариқ-тешар", "Қаҳрамон", 
    "Бодомзор", "Туркистон"
])

# 2. Жиҳозлар рўйхати (Танлаш учун)
items_list = [
    "Компьютер жамланмаси", "Ноутбук", "Принтер (МФУ)", "Телевизор", "Кондиционер", 
    "Стол (ходим учун)", "Стол (мажлислар зали)", "Стул (ходим учун)", "Стул (меҳмон учун)", 
    "Шкаф (ҳужжатлар учун)", "Кийим илгич", "Диван", "Кресло", "Гилам", "Парда", 
    "Сейф", "Сув совутгич (Кулер)", "Электрон табло", "Генератор", "Видеокузатув қурилмаси"
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
    except Exception as e:
        st.error(f"Хатолик: {e}")
        return []

# --- ИНТЕРФЕЙС ---
st.title("🏢 МФЙ 7 лиги Инвентаризация тизими")

# Sidebar - Маҳаллани танлаш
selected_mfy = st.sidebar.selectbox("🏠 Маҳаллани танланг", mfy_list)
st.sidebar.info(f"Танланган ҳудуд: **{selected_mfy}**")

tab1, tab2 = st.tabs(["📋 Жиҳозлар рўйхати", "➕ Янги кирим қилиш"])

with tab1:
    st.subheader(f"📊 {selected_mfy} маҳалласи инвентар рўйхати")
    query = "SELECT item_name, inventory_number, category, condition, responsible_person, price FROM office_inventory WHERE mfy_name = %s"
    data = run_query(query, (selected_mfy,))
    
    if data:
        df = pd.DataFrame(data, columns=["Жиҳоз номи", "Инвентар №", "Тоифа", "Ҳолати", "Масъул", "Нархи (сўм)"])
        st.dataframe(df, use_container_width=True)
        
        total_sum = df["Нархи (сўм)"].sum()
        st.metric("Умумий баланс", f"{total_sum:,.0f} сўм")
    else:
        st.warning(f"Ҳозирча {selected_mfy} маҳалласида жиҳозлар рўйхатга олинмаган.")

with tab2:
    st.subheader(f"➕ {selected_mfy} учун янги жиҳоз қўшиш")
    with st.form("add_inventory_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        # Жиҳоз номи энди рўйхатдан танланади
        item_name = col1.selectbox("Жиҳоз турини танланг", items_list)
        inv_num = col2.text_input("Инвентар рақами (Unique ID)")
        
        category = col1.selectbox("Тоифа", ["Техника", "Мебель", "Юмшоқ жиҳоз", "Хўжалик"])
        condition = col2.selectbox("Ҳолати", ["Яхши", "Ўрта (таъмирталаб)", "Яроқсиз"])
        
        responsible = col1.selectbox("Масъул ходим", [
            "Раис", "Ҳоким ёрдамчиси", "Ёшлар етакчиси", 
            "Хотин-қизлар фаоли", "Профилактика инс.", 
            "Солиқ инс.", "Ижтимоий ходим"
        ])
        price = col2.number_input("Нархи (сўм)", min_value=0, step=1000)
        
        if st.form_submit_button("Базага сақлаш"):
            if inv_num:
                # Инвентар рақами такрорланмаслигини текшириш
                check_inv = run_query("SELECT id FROM office_inventory WHERE inventory_number = %s", (inv_num,))
                if check_inv:
                    st.error(f"Хато: {inv_num} рақамли жиҳоз аллақачон базада бор!")
                else:
                    insert_query = """
                        INSERT INTO office_inventory (mfy_name, item_name, inventory_number, category, condition, responsible_person, price)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """
                    run_query(insert_query, (selected_mfy, item_name, inv_num, category, condition, responsible, price), is_select=False)
                    st.success(f"Муваффақиятли сақланди: {item_name} ({selected_mfy})")
                    st.rerun() # Маълумотни янгилаш
            else:
                st.warning("Илтимос, инвентар рақамини киритинг!")
