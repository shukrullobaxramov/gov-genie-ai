import streamlit as st
import psycopg2
import pandas as pd

# Саҳифа созламалари
st.set_page_config(page_title="МФЙ Инвентаризация", layout="wide", page_icon="🏢")

# 1. МФЙлар рўйхати (Алфавит бўйича сараланган)
mfy_list = sorted([
    "Абдужалилбоб", "Алимбува", "Амир Темур", "Асил", "Ахилобод", "Ахмад Яссавий", 
    "Балиқчи", "Боғишамол", "Бодомзор", "Боғзор", "Бўстон", "Гулбоғ", "Далигазар", 
    "Деҳқонобод", "Зарафшон", "Илғор", "Истиқлол", "Истиқлолнинг 5-йиллиги", 
    "Катта чинор", "Кенг кечик", "Қурилиш", "Қуёшли", "Маданият", "М.М.Хоразмий", 
    "Мевазор", "Навбаҳор", "Навқирон", "Назарбек", "Найман", "Намуна", "Нурафшон", 
    "Нуробод", "Обод", "Обод тўқимачи", "Обод турмуш", "Олмазор", "Рамадон", 
    "Саховат", "Сортепа", "Тариқ-тешар", "Тарнов", "Токзор", "Туропобод", 
    "Туркистон", "Тўқимачи", "Файз", "Фаробий", "Ҳаракат", "Хўжамозор", "Чинор", 
    "Шодлик", "Эркин", "Эски қалъа", "Эшонгузар", "Янги бўзсув", "Ўратепа", 
    "Ўрикзор", "Ўрта", "Ўртаовул"
])

# 2. Жиҳозлар рўйхати
items_list = [
    "Компьютер жамланмаси", "Ноутбук", "Принтер (МФУ)", "Телевизор", "Кондиционер", 
    "Стол", "Стул", "Шкаф", "Диван", "Гилам", "Парда", "Сейф", "Кулер", "Генератор"
]

def run_query(query, params=None, is_select=True):
    try:
        conn = psycopg2.connect(st.secrets["DB_URL"])
        with conn.cursor() as cur:
            cur.execute(query, params)
            if is_select:
                res = cur.fetchall()
                conn.close()
                return res
            conn.commit()
            conn.close()
    except Exception as e:
        st.error(f"Базада хатолик: {e}")
        return []

# --- SIDEBAR МЕНЮ ---
st.sidebar.title("⚙️ Бошқарув")
menu = st.sidebar.radio("Бўлимни танланг:", ["📥 Киритиш", "📋 Ҳисобот", "✏️ Таҳрирлаш"])

# --- АСОСИЙ ОЙНА ---
st.title("🏢 МФЙ 7 лиги Инвентаризация тизими")
selected_mfy = st.selectbox("🏘 Маҳаллани танланг", mfy_list)
st.divider()

# 1. КИРИТИШ БЎЛИМИ
if menu == "📥 Киритиш":
    st.subheader(f"📥 {selected_mfy}: Янги жиҳоз киритиш")
    with st.form("input_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        item = c1.selectbox("Жиҳоз номи", items_list)
        inv_num = c2.text_input("Инвентар рақами", value="0")
        
        cat = c1.selectbox("Тоифа", ["Техника", "Мебель", "Юмшоқ жиҳоз", "Бошқа"])
        cond = c2.selectbox("Ҳолати", ["Яхши", "Таъмирталаб", "Яроқсиз"])
        
        resp = c1.selectbox("Масъул", ["Раис", "Ҳоким ёрдамчиси", "Ёшлар етакчиси", "Аёллар фаоли", "Инспектор", "Солиқчи", "Ижтимоий ходим"])
        price = c2.number_input("Нархи (сўм)", min_value=0, step=1000)
        
        if st.form_submit_button("✅ Базага сақлаш"):
            query = """INSERT INTO office_inventory (mfy_name, item_name, inventory_number, category, condition, responsible_person, price) 
                       VALUES (%s, %s, %s, %s, %s, %s, %s)"""
            run_query(query, (selected_mfy, item, inv_num, cat, cond, resp, price), is_select=False)
            st.success(f"Муваффақиятли сақланди!")
            st.balloons()

# 2. ҲИСОБОТ БЎЛИМИ
elif menu == "📋 Ҳисобот":
    st.subheader(f"📋 {selected_mfy}: Молиявий ҳисобот ва рўйхат")
    data = run_query("SELECT item_name, inventory_number, category, condition, responsible_person, price FROM office_inventory WHERE mfy_name = %s", (selected_mfy,))
    
    if data:
        df = pd.DataFrame(data, columns=["Номи", "Инв №", "Тоифа", "Ҳолати", "Масъул", "Нархи"])
        st.table(df) # Жадвал кўринишида чиқариш
        
        total_sum = df["Нархи"].sum()
        st.metric(f"{selected_mfy} бўйича жами қиймат", f"{total_sum:,.0f} сўм")
    else:
        st.info(f"{selected_mfy} маҳалласида ҳозирча маълумот йўқ.")

# 3. ТАҲРИРЛАШ БЎЛИМИ
elif menu == "✏️ Таҳрирлаш":
    st.subheader(f"✏️ {selected_mfy}: Маълумотларни ўчириш")
    data = run_query("SELECT id, item_name, inventory_number, price FROM office_inventory WHERE mfy_name = %s", (selected_mfy,))
    
    if data:
        edit_df = pd.DataFrame(data, columns=["ID", "Номи", "Инв №", "Нархи"])
        st.dataframe(edit_df, use_container_width=True)
        
        selected_id = st.selectbox("Ўчириш учун ID рақамини танланг", edit_df["ID"].tolist())
        
        if st.button("🗑 Танланганни базадан ўчириш", type="primary"):
            run_query("DELETE FROM office_inventory WHERE id = %s", (selected_id,), is_select=False)
            st.warning(f"ID {selected_id} бўлган жиҳоз ўчирилди!")
            st.rerun()
    else:
        st.info("Таҳрирлаш учун базада маълумот топилмади.")
