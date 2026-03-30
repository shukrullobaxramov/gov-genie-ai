import streamlit as st
import psycopg2
import pandas as pd

# Саҳифа созламалари
st.set_page_config(page_title="МФЙ Инвентаризация", layout="wide", page_icon="🏢")

# 1. МФЙлар рўйхати (60 та маҳалла тўлиқ ва алфавит бўйича)
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
    "Ўрикзор", "Ўрта", "Ўртаовул", "Эркин", "Хақиқат", "Зангиота"
])

# --- КЕНГАЙТИРИЛГАН ЛУҒАТ БИЛАН ТЎЛИҚ ҚИСМ ---
inventory_dict = {
    "Техника": [
        "Компьютер жамланмаси", "Ноутбук", "Принтер (МФУ)", "Сканер", "Проектор", 
        "Телевизор", "Кондиционер", "Кулер (сув совутгич)", "Генератор", "UPS (ИБП)", 
        "Видеокузатув камераси", "DVR (видео ёзув қурилмаси)", "Микрофон", "Овоз кучайтиргич (Колонка)", 
        "Электрон табло", "Wi-Fi роутер", "Телефон аппарати", "Фотоаппарат", "Планшет", "Бошқа..."
    ],
    "Мебель": [
        "Стол (ходим учун)", "Стол (мажлислар зали)", "Компьютер столи", "Стул (ходим учун)", 
        "Стул (меҳмон учун)", "Шкаф (ҳужжатлар учун)", "Шкаф (кийим учун)", "Китоб жавони", 
        "Сейф (темир шкаф)", "Диван", "Кресло", "Журнал столи", "Кийим илгич", "Тумбочка", 
        "Минбар (трибуна)", "Парда карнизи", "Ошхона мебели", "Рецепшн столи", "Бошқа..."
    ],
    "Юмшоқ жиҳоз": [
        "Гилам", "Ковролан", "Парда", "Тюль", "Жалюзи", "Тўшак", "Ёстиқ", "Кўрпа", 
        "Дастурхон", "Кўрпача", "Чойшаб", "Матрац", "Бошқа..."
    ],
    "Бошқа": [
        "Ўт ўчириш мосламаси", "Байроқ (давлат рамзи)", "Герб", "Портрет", "Соат (девор учун)", 
        "Гултувак", "Термос", "Микротўлқинли печ", "Музлатгич", "Электр чойшаб", "Чангютгич", "Бошқа..."
    ]
}

# 3. 7 лик вакиллари
staff_7 = ["Раис", "Ҳоким ёрдамчиси", "Ёшлар етакчиси", "Аёллар фаоли", "Инспектор", "Солиқчи", "Ижтимоий ходим"]

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
        st.error(f"Хатолик: {e}")
        return []

# --- SIDEBAR ---
st.sidebar.title("⚙️ Бошқарув")
menu = st.sidebar.radio("Бўлимни танланг:", ["📥 Киритиш", "📋 Ҳисобот", "✏️ Таҳрирлаш"])

# --- АСОСИЙ ОЙНА ---
st.title("🏢 МФЙ 7 лиги Инвентаризация")
selected_mfy = st.selectbox("🏘 Маҳаллани танланг", mfy_list)
st.divider()

# 1. КИРИТИШ
if menu == "📥 Киритиш":
    st.subheader(f"📥 {selected_mfy}: Янги кирим")
    c1, c2 = st.columns(2)
    cat_choice = c1.selectbox("Тоифа", list(inventory_dict.keys()))
    final_cat = cat_choice
    if cat_choice == "Бошқа":
        final_cat = c1.text_input("Тоифа номи")

    item_choice = c2.selectbox("Жиҳоз", inventory_dict.get(cat_choice, ["Бошқа..."]))
    final_item = item_choice
    if item_choice == "Бошқа...":
        final_item = c2.text_input("Жиҳоз номи")

    with st.form("add_form", clear_on_submit=True):
        f1, f2 = st.columns(2)
        inv_num = f1.text_input("Инвентар №", value="0")
        cond = f2.selectbox("Ҳолати", ["Яхши", "Таъмирталаб", "Яроқсиз"])
        resp = f1.selectbox("Масъул (7 лик)", staff_7)
        price = f2.number_input("Нархи", min_value=0)
        
        if st.form_submit_button("✅ Сақлаш"):
            run_query("INSERT INTO office_inventory (mfy_name, item_name, inventory_number, category, condition, responsible_person, price) VALUES (%s, %s, %s, %s, %s, %s, %s)", 
                      (selected_mfy, final_item, inv_num, final_cat, cond, resp, price), is_select=False)
            st.success("Сақланди!")

# 2. ҲИСОБОТ
elif menu == "📋 Ҳисобот":
    st.subheader(f"📋 {selected_mfy}: Умумий ҳисобот")
    data = run_query("SELECT item_name, inventory_number, category, condition, responsible_person, price FROM office_inventory WHERE mfy_name = %s", (selected_mfy,))
    
    if data:
        df = pd.DataFrame(data, columns=["Номи", "Инв №", "Тоифа", "Ҳолати", "Масъул", "Нархи"])
        st.dataframe(df, use_container_width=True)
        
        st.divider()
        st.subheader("👥 7 лик кесимида тақсимот")
        for member in staff_7:
            member_data = df[df["Масъул"] == member]
            if not member_data.empty:
                with st.expander(f"🔹 {member} (Жами: {len(member_data)} та жиҳоз)"):
                    st.table(member_data[["Номи", "Инв №", "Ҳолати", "Нархи"]])
                    st.write(f"**Кичик жами:** {member_data['Нархи'].sum():,.0f} сўм")
        
        st.metric("МАҲАЛЛА БЎЙИЧА ЖАМИ", f"{df['Нархи'].sum():,.0f} сўм")
    else:
        st.info("Маълумот йўқ.")

# 3. ТАҲРИРЛАШ
elif menu == "✏️ Таҳрирлаш":
    st.subheader(f"✏️ {selected_mfy}: Маълумотларни ўзгартириш")
    data = run_query("SELECT id, item_name, inventory_number, category, condition, responsible_person, price FROM office_inventory WHERE mfy_name = %s", (selected_mfy,))
    
    if data:
        df_edit = pd.DataFrame(data, columns=["ID", "Номи", "Инв №", "Тоифа", "Ҳолати", "Масъул", "Нархи"])
        st.dataframe(df_edit, use_container_width=True)
        
        selected_id = st.selectbox("Ўзгартириш учун ID танланг", df_edit["ID"].tolist())
        row = df_edit[df_edit["ID"] == selected_id].iloc[0]
        
        with st.form("edit_form"):
            st.write(f"**ID: {selected_id}** таҳрирланмоқда")
            e1, e2 = st.columns(2)
            new_item = e1.text_input("Номи", value=row["Номи"])
            new_inv = e2.text_input("Инв №", value=row["Инв №"])
            new_cond = e1.selectbox("Ҳолати", ["Яхши", "Таъмирталаб", "Яроқсиз"], index=["Яхши", "Таъмирталаб", "Яроқсиз"].index(row["Ҳолати"]))
            new_resp = e2.selectbox("Масъул", staff_7, index=staff_7.index(row["Масъул"]))
            new_price = e1.number_input("Нархи", value=float(row["Нархи"]))
            
            col_b1, col_b2 = st.columns(2)
            if col_b1.form_submit_button("💾 Янгилаш"):
                run_query("UPDATE office_inventory SET item_name=%s, inventory_number=%s, condition=%s, responsible_person=%s, price=%s WHERE id=%s",
                          (new_item, new_inv, new_cond, new_resp, new_price, selected_id), is_select=False)
                st.success("Маълумот янгиланди!")
                st.rerun()
            
            if col_b2.form_submit_button("🗑 Ўчириш"):
                run_query("DELETE FROM office_inventory WHERE id=%s", (selected_id,), is_select=False)
                st.warning("Ўчирилди!")
                st.rerun()
    else:
        st.info("Таҳрирлаш учун маълумот йўқ.")
