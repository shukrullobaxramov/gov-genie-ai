import streamlit as st
import psycopg2
import pandas as pd

# Саҳифа созламалари
st.set_page_config(page_title="МФЙ Инвентаризация", layout="wide", page_icon="🏢")

# 1. МФЙлар рўйхати (Кирилл алифбосида тўғри саралаш учун)
raw_mfy = [
    "Абдужалилбоб", "Алимбува", "Амир Темур", "Асил", "Ахилобод", "Ахмад Яссавий", 
    "Балиқчи", "Боғишамол", "Бодомзор", "Боғзор", "Бўстон", "Гулбоғ", "Далигазар", 
    "Деҳқонобод", "Зарафшон", "Илғор", "Истиқлол", "Истиқлолнинг 5-йиллиги", 
    "Катта чинор", "Кенг кечик", "Курилиш", "Куёшли", "Маданият", "М.М.Хоразмий", 
    "Мевазор", "Навбаҳор", "Навқирон", "Назарбек", "Найман", "Намуна", "Нурафшон", 
    "Нуробод", "Обод", "Обод тўқимачи", "Обод турмуш", "Олмазор", "Рамадон", 
    "Саховат", "Сортепа", "Тариқ-тешар", "Тарнов", "Телевизор", "Токзор", "Туропобод", 
    "Туркистон", "Тўқимачи", "Файз", "Фаробий", "Ҳаракат", "Хўжамозор", "Чинор", 
    "Шодлик", "Эркии", "Эски қалъа", "Эшонгузар", "Юқори", "Янги бўзсув", "Ўратепа", 
    "Ўрикзор", "Ўрта", "Ўртаовул"
]
mfy_list = sorted(raw_mfy) # Алфавит бўйича саралаш

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

# --- АСОСИЙ ОЙНАДА МФЙ ТАНЛАШ ---
st.title("🏢 МФЙ 7 лиги Инвентаризация")
selected_mfy = st.selectbox("🏘 Маҳаллани танланг", mfy_list)
st.markdown(f"### Ҳозирги ҳудуд: **{selected_mfy}**")

# --- МЕНЮ (КИРИТИШ, ҲИСОБОТ, ТАҲРИР) ---
menu = st.radio("⚙️ Амалиётни танланг:", ["📥 Киритиш", "📋 Ҳисобот", "✏️ Таҳрирлаш"], horizontal=True)

st.divider()

# 1. КИРИТИШ БЎЛИМИ
if menu == "📥 Киритиш":
    with st.form("input_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        item = c1.selectbox("Жиҳоз номи", items_list)
        inv_num = c2.text_input("Инвентар рақами (бўлмаса 0 қолдиринг)", value="0")
        
        cat = c1.selectbox("Тоифа", ["Техника", "Мебель", "Юмшоқ жиҳоз", "Бошқа"])
        cond = c2.selectbox("Ҳолати", ["Яхши", "Таъмирталаб", "Яроқсиз"])
        
        resp = c1.selectbox("Масъул", ["Раис", "Ҳоким ёрдамчиси", "Ёшлар етакчиси", "Аёллар фаоли", "Инспектор"])
        price = c2.number_input("Нархи (сўм)", min_value=0)
        
        if st.form_submit_button("✅ Сақлаш"):
            query = """INSERT INTO office_inventory (mfy_name, item_name, inventory_number, category, condition, responsible_person, price) 
                       VALUES (%s, %s, %s, %s, %s, %s, %s)"""
            run_query(query, (selected_mfy, item, inv_num, cat, cond, resp, price), is_select=False)
            st.success(f"{item} муваффақиятли қўшилди!")

# 2. ҲИСОБОТ БЎЛИМИ
elif menu == "📋 Ҳисобот":
    data = run_query("SELECT id, item_name, inventory_number, category, condition, responsible_person, price FROM office_inventory WHERE mfy_name = %s", (selected_mfy,))
    if data:
        df = pd.DataFrame(data, columns=["ID", "Номи", "Инв №", "Тоифа", "Ҳолати", "Масъул", "Нархи"])
        st.dataframe(df.drop(columns=["ID"]), use_container_width=True)
        st.metric("Умумий қиймат", f"{df['Нархи'].sum():,.0f} сўм")
    else:
        st.info("Маълумот мавжуд эмас.")

# 3. ТАҲРИРЛАШ БЎЛИМИ
elif menu == "✏️ Таҳрирлаш":
    data = run_query("SELECT id, item_name, inventory_number, price FROM office_inventory WHERE mfy_name = %s", (selected_mfy,))
    if data:
        edit_df = pd.DataFrame(data, columns=["ID", "Номи", "Инв №", "Нархи"])
        st.write("Ўчириш ёки ўзгартириш учун ID ни танланг:")
        selected_id = st.selectbox("Жиҳоз ID си", edit_df["ID"].tolist())
        
        if st.button("🗑 Танланганни ўчириш", type="primary"):
            run_query("DELETE FROM office_inventory WHERE id = %s", (selected_id,), is_select=False)
            st.warning("Маълумот ўчирилди!")
            st.rerun()
    else:
        st.info("Таҳрирлаш учун маълумот йўқ.")
