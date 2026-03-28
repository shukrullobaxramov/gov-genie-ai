import streamlit as st
import psycopg2
import google.generativeai as genai

# Саҳифа созламалари
st.set_page_config(page_title="Gov Genie AI", layout="wide")

# Базага уланиш функцияси
def run_query(query, params=None):
    try:
        conn = psycopg2.connect(st.secrets["DB_URL"])
        with conn.cursor() as cur:
            cur.execute(query, params)
            if cur.description:
                return cur.fetchall()
            conn.commit()
            return None
    except Exception as e:
        st.error(f"База хатолиги: {e}")
        return []

st.title("🧞 Gov Genie AI")
st.markdown("---")

# 1. ТАШКИЛОТ ВА ЛАВОЗИМНИ ТАНЛАШ
orgs = run_query("SELECT id, name FROM organizations")
if orgs:
    org_dict = {name: id for id, name in orgs}
    col1, col2 = st.columns(2)
    
    with col1:
        org_name = st.selectbox("🏢 Ташкилот", list(org_dict.keys()))
    
    roles = run_query("SELECT id, name FROM roles WHERE org_id=%s", (org_dict[org_name],))
    
    if roles:
        role_dict = {name: id for id, name in roles}
        with col2:
            role_name = st.selectbox("👨‍💼 Лавозим", list(role_dict.keys()))
        
        role_id = role_dict[role_name]

        # 2. АВТОМАТИК МАЪЛУМОТ ЧИҚАРИШ (Сиз айтган қисм)
        st.markdown(f"### 📋 {role_name} учун маълумотнома")
        
        # Базадан маълумотларни оламиз
        laws = run_query("""
            SELECT l.title, l.simple FROM laws l 
            JOIN role_laws rl ON l.id = rl.law_id 
            WHERE rl.role_id=%s""", (role_id,))
        
        tasks = run_query("SELECT task FROM tasks WHERE role_id=%s", (role_id,))

        c1, c2 = st.columns(2)
        with c1:
            st.info("📜 **Тегишли қонунчилик:**")
            if laws:
                for law in laws:
                    st.write(f"✅ **{law[0]}**: {law[1]}")
            else:
                st.write("Маълумот топилмади.")

        with c2:
            st.success("✅ **Асосий вазифаларингиз:**")
            if tasks:
                for task in tasks:
                    st.write(f"🔹 {task[0]}")
            else:
                st.write("Вазифалар киритилмаган.")

        # 3. ҚЎШИМЧА AI ЁРДАМЧИ (Ихтиёрий саволлар учун)
        st.markdown("---")
        st.subheader("🤖 Қўшимча саволлар учун AI ёрдамчи")
        
        if "messages" not in st.session_state:
            st.session_state.messages = []

        for msg in st.session_state.messages:
            st.chat_message(msg["role"]).write(msg["content"])

        user_input = st.chat_input("Қўшимча тушунмаган жойингизни сўранг...")

        if user_input:
            st.chat_message("user").write(user_input)
            st.session_state.messages.append({"role": "user", "content": user_input})

            # AI учун контекст тайёрлаймиз
            prompt = f"Лавозим: {role_name}. Қонунлар: {laws}. Вазифалар: {tasks}. Савол: {user_input}"
            
            genai.configure(api_key=st.secrets["GENAI_API_KEY"])
            model = genai.GenerativeModel("gemini-1.5-flash")
            
            try:
                response = model.generate_content(prompt)
                st.chat_message("assistant").write(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except:
                st.warning("AI ҳозирча жавоб бера олмаяпти, лекин юқоридаги маълумотлар базадан олинди.")

else:
    st.warning("Базада ташкилотлар топилмади.")
