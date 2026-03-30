import streamlit as st
import psycopg2
import pandas as pd

# Саҳифа созламалари
st.set_page_config(page_title="МФЙ Инвентаризация", layout="wide", page_icon="🏢")

# 1. МФЙлар рўйхати
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

# 2. Жиҳозлар луғати ("Бошқа..." варианти билан)
inventory_dict = {
    "Техника": ["Компьютер жамланмаси", "Ноутбук", "Принтер (МФУ)", "Телевизор", "Кондиционер", "Кулер", "Генератор", "Бошқа..."],
    "Мебель": ["Стол", "Стул", "Шкаф", "Диван", "Кресло", "Сейф", "Бошқа..."],
    "Юмшоқ жиҳоз": ["Гилам", "Парда", "Тўшак", "Бошқа..."],
    "Бошқа": ["Бошқа..."]
}

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
menu = st.sidebar.radio("Бўлимни танланг:", ["📥 Киритиш", "📋 Ҳисобот", "✏️ Таҳрир"])

# --- АСОСИЙ ОЙНА ---
st.title("🏢 МФЙ 7 лиги Инвентаризация")
selected_mfy = st.selectbox("🏘 Маҳаллани танланг", mfy_list)
st.divider()

# 1. КИРИТИШ БОЛИМИ
if menu == "📥 Киритиш":
    st.subheader(f"📥 {selected_mfy}: Янги кирим")
    
    # Тоифа ва Жиҳозни формадан ташқарида танлаймиз (динамик бўлиши учун)
    c1, c2 = st.columns(2)
    cat_choice = c1.selectbox("1. Тоифани танланг", list(inventory_dict.keys()))
    
    # Агар тоифа "Бошқа" бўлса, қўлда ёзиш майдони чиқади
    final_category = cat_choice
    if cat_choice == "Бошқа":
        final_category = c1.text_input("Тоифа номини ёзинг", placeholder="Масалан: Спорт анжомлари")

    item_choice = c2.selectbox("2. Жиҳоз номини танланг", inventory_dict.get(cat_choice, ["Бошқа..."]))
    
    # Агар жиҳоз "Бошқа..." бўлса, қўлда ёзиш майдони чиқади
    final_item = item_choice
    if item_choice == "Бошқа...":
        final_item = c2.text_input("Жиҳоз номини ёзинг", placeholder="Масалан: Югуриш йўлакчаси")

    # Қолган маълумотлар форма ичида
    with st.form("main_input_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        inv_num = col1.text_input("Инвентар рақами", value="0")
        cond = col2.selectbox("Ҳолати", ["Яхши", "Таъмирталаб", "Яроқсиз"])
        
        resp = col1.selectbox("Масъул ходим", ["Раис", "Ҳоким ёрдамчиси", "Ёшлар етакчиси", "Аёллар фаоли", "Инспектор", "Солиқчи", "Ижтимоий ходим"])
        price = col2.number_input("Нархи (сўм)", min_value=0, step=1000)
        
        submitted = st.form_submit_button("✅ Сақлаш")
        if submitted:
            if final_category and final_item:
                query = """INSERT INTO office_inventory (mfy_name, item_name, inventory_number, category, condition, responsible_person, price) 
                           VALUES (%s, %s, %s, %s, %s, %s, %s)"""
                run_query(query, (selected_mfy, final_item, inv_num, final_category, cond, resp, price), is_select=False)
                st.success(f"Муваффақиятли қўшилди: {final_item}")
                st.balloons()
            else:
                st.error("Илтимос, барча майдонларни тўлдиринг!")

# 2. ҲИСОБОТ БЎЛИМИ
elif menu == "📋 Ҳисобот":
    st.subheader(f"📋 {selected_mfy}: Рўйхат")
    data = run_query("SELECT item_name, inventory_number, category, condition, responsible_person, price FROM office_inventory WHERE mfy_name = %s", (selected_mfy,))
    if data:
        df = pd.DataFrame(data, columns=["Номи", "Инв №", "Тоифа", "Ҳолати", "Масъул", "Нархи"])
        st.table(df)
        st.metric("Жами қиймат", f"{df['Нархи'].sum():,.0f} сўм")
    else:
        st.info("Маълумот йўқ.")

# 3. ТАҲРИР БЎЛИМИ
elif menu == "✏️ Таҳрир":
    st.subheader(f"✏️ {selected_mfy}: Ўчириш")
    data = run_query("SELECT id, item_name, inventory_number, price FROM office_inventory WHERE mfy_name = %s", (selected_mfy,))
    if data:
        edit_df = pd.DataFrame(data, columns=["ID", "Номи", "Инв №", "Нархи"])
        st.dataframe(edit_df, use_container_width=True)
        selected_id = st.selectbox("ID ни танланг", edit_df["ID"].tolist())
        if st.button("🗑 Ўчириш", type="primary"):
            run_query("DELETE FROM office_inventory WHERE id = %s", (selected_id,), is_select=False)
            st.warning("Ўчирилди!")
            st.rerun()
