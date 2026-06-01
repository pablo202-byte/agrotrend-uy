import streamlit as st
import pandas as pd
import re
import random

# Configuración de la página de la app
st.set_page_config(page_title="AgroTrend Uruguay", page_icon="🌾", layout="wide")

# --- 🧮 LÓGICA DE CONVERSIÓN AGRÍCOLA ---
def extraer_numero(texto):
    numeros = re.findall(r'\b\d+(?:[\.,]\d+)?\b', texto)
    if numeros:
        num_str = numeros[0].replace(',', '')
        try:
            return float(num_str)
        except ValueError:
            return None
    return None

def convertir_unidades(texto, cultivo):
    texto_lower = texto.lower()
    num = extraer_numero(texto)
    
    factores_kg = {"soja": 67.25, "maíz": 62.77, "trigo": 67.25}
    factores_tn = {"soja": 0.02721, "maíz": 0.0254, "trigo": 0.02721}
    
    f_kg = factores_kg.get(cultivo.lower(), 65.0)
    f_tn = factores_tn.get(cultivo.lower(), 0.026)

    if any(u in texto_lower for u in ["bu/acre", "bushels per acre", "bpa"]):
        if num:
            kg_ha = num * f_kg
            return f"🔄 **Traducción de rinde para Uruguay:** {num} bu/acre ≈ **{kg_ha:.0f} kg/ha**"
    elif "bushels" in texto_lower or "bu " in texto_lower:
        if num:
            toneladas = num * f_tn
            return f"🔄 **Traducción de volumen para Uruguay:** {num:,.0f} bushels ≈ **{toneladas:,.0f} toneladas**"
    return None

# --- 📊 BASE DE DATOS AGRÍCOLA SIMULADA ---
TWEETS_MOCK = {
    "Soja": [
        {"texto": "USDA reports Midwest soybean yields hitting an impressive 62 bu/acre despite early July dryness.", "vistas": 45200, "likes": 340, "reposts": 52},
        {"texto": "Soybean market updates: China buying 120,000 bushels of US new crop. Prices holding steady at Chicago.", "vistas": 12800, "likes": 95, "reposts": 14},
        {"texto": "Weather alert: Heavy rainfall across Mato Grosso stalling the final stages of soybean harvest.", "vistas": 28400, "likes": 190, "reposts": 41}
    ],
    "Maíz": [
        {"texto": "Corn yields looking variable in Illinois. Some fields checking at 190 bpa, others dropping to 155 bu/acre.", "vistas": 38100, "likes": 220, "reposts": 33},
        {"texto": "Chicago Board of Trade: Corn futures slide 2% as export demand weakens globally.", "vistas": 15400, "likes": 110, "reposts": 19},
        {"texto": "Flash drought concerns in Iowa could slash corn production by 15 million bushels this season.", "vistas": 52000, "likes": 420, "reposts": 88}
    ],
    "Trigo": [
        {"texto": "HRW Wheat harvest reveals disappointing test weights. Average yields close to 38 bu/acre in Kansas.", "vistas": 21000, "likes": 145, "reposts": 22},
        {"texto": "Global wheat supply tightens as European crop estimates face another downgrade due to wet spring.", "vistas": 31500, "likes": 280, "reposts": 64},
        {"texto": "Egypt tenders for 60,000 bushels of milling wheat. Black Sea origins expected to dominate the bids.", "vistas": 9400, "likes": 65, "reposts": 8}
    ]
}

# --- 🖥️ INTERFAZ DE USUARIO ---
st.title("🌾 AgroTrend Uruguay — Tracker Inteligente")
st.markdown("### Detector de Tendencias y Engagement Global")
st.markdown("---")

st.sidebar.header("🔍 Parámetros del Radar")
cultivo_sel = st.sidebar.selectbox("Seleccioná el cultivo a monitorear:", ["Soja", "Maíz", "Trigo"])

if st.sidebar.button("🔥 Escanear Redes en Tiempo Real"):
    with st.spinner("Analizando engagement y convirtiendo métricas..."):
        # Traemos los datos simulados según el cultivo seleccionado
        datos = TWEETS_MOCK[cultivo_sel]
        
        lista_tweets = []
        for t in datos:
            # Ponderamos el score sumando interacciones simuladas
            hot_score = t["vistas"] + (t["likes"] * 10) + (t["reposts"] * 20)
            
            lista_tweets.append({
                "texto": t["texto"],
                "vistas": t["vistas"],
                "likes": t["likes"],
                "reposts": t["reposts"],
                "score": hot_score
            })
            
        df = pd.DataFrame(lista_tweets).sort_values(by="score", ascending=False)
        
        for index, row in df.iterrows():
            with st.container():
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"🔹 *{row['texto']}*")
                    
                    traduccion = convertir_unidades(row['texto'], cultivo_sel)
                    if traduccion:
                        st.info(traduccion)
                    
                    st.success(
                        f"💡 **Informe sugerido para tus productores en Uruguay:**\n\n"
                        f"\"Estimados, el monitor global detecta fuerte movimiento sobre {cultivo_sel.lower()}. "
                        f"Afuera se habla de: '{row['texto'][:60]}...'. Traducido a nuestras unidades, esto marca una referencia clave. "
                        f"Afecta directamente los presupuestos locales. Sugerimos analizar coberturas.\""
                    )
                    
                with col2:
                    st.metric(label="🔥 Hot Score", value=f"{row['score']:,}")
                    st.caption(f"👀 Vistas: {row['vistas']:,}\n\n❤️ Likes: {row['likes']} | 🔁 Reposts: {row['reposts']}")
                
                st.markdown("---")
