import streamlit as st
import psycopg2
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
import time

# --- САҲИФА СОЗЛАМАЛАРИ ---
st.set_page_config(page_title="Gov Genie AI - Lex.uz Integration", layout="wide")

# --- AI ВА БАЗА УЛАНИШИ ---
genai.configure(api_key=st.secrets["GENAI_API_KEY"])
model = genai.GenerativeModel("gemini-1.5-flash")

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
        return []

# --- LEX.UZ АВТОМАТ ҚИДИРУВ ФУНКЦИЯСИ ---
def fetch_lex_uz(search_term):
    """Lex.uz сайтидан янги ҳужжатларни қидиради"""
    try:
        # Қидирув ҳаволаси (Ижтимоий соҳага оид)
        search_url = f"https://lex.uz/search/nat?query={search_term}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(search_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Сайтдаги ҳужжат номлари ва линкларини олиш (классик Lex.uz структураси)
            links = soup.select('.lex_list_title a')[:3] # Энг янги 3 тасини оламиз
            results = []
            for link in links:
                results.append(f"{link.text.strip()} (Линк: https://lex.uz{link.get('href')})")
            return "\n".join(results) if results else "Янги ҳужжатлар топилмади."
        return "Lex.uz га уланиш имконсиз бўлди."
    except:
        return "Қидирувда техник хатолик юз берди."

# --- ИНТЕРФЕЙС ---
st.title("🧞 Gov Genie AI: Lex.uz Авто-Таҳлил")
st.markdown("---")

# 1. ТАШКИЛОТ ВА ЛАВОЗИМ
orgs = run_query("SELECT id, name FROM organizations")
if orgs:
    org_dict = {name: id for id, name in orgs}
    c1, c2 = st.columns(2)
    with c1:
        org_name = st.selectbox("🏢 Ташкилот", list(org_dict.keys()))
    
    roles = run_query("SELECT id, name FROM
