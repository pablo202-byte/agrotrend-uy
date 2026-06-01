import streamlit as st
import pandas as pd
import tweepy
import re

# Configuración de la página de la app
st.set_page_config(page_title="AgroTrend Uruguay PRO", page_icon="🌾", layout="wide")

# --- 🔒 SISTEMA DE LLAVES SEGURAS PARA LA NUBE 🔒 ---
# La app lee las credenciales desde el panel oculto de "Secrets" en Streamlit
try:
    API_KEY = st.secrets["API_KEY"]
    API_KEY_SECRET = st.secrets["API_KEY_SECRET"]
    ACCESS_TOKEN = st.secrets["ACCESS_TOKEN"]
    ACCESS_TOKEN_SECRET = st.secrets["ACCESS_TOKEN_SECRET"]
except Exception:
    st.error("⚠️ Error: No se encontraron las llaves en los 'Secrets' de Streamlit. Por favor, configuralas en el panel de control de la app.")
    API_KEY = API_KEY_SECRET = ACCESS_TOKEN = ACCESS_TOKEN_SECRET = None

# Conexión oficial con la API v2 de X
@st.cache_resource
def inicializar_twitter(k, ks, t, ts):
    if not all([k, ks, t, ts]):
        return None
    try:
        client = tweepy.Client(
            consumer_key=k,
            consumer_secret=ks,
            access_token=t,
            access_token_secret=ts
        )
        return client
    except Exception as e:
        st.error(f"Error de autenticación con X: {e}")
        return None

client = inicializar_twitter(API_KEY, API_KEY_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

# --- 🧮 LÓGICA DE CONVERSIÓN AGRÍCOLA ---
def extraer_numero(texto):
    """Detecta números en el cuerpo del tweet para procesar conversiones"""
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
    
    # Parámetros internacionales de conversión por tipo de grano
    factores_kg = {"soja": 67.25, "maíz": 62.77, "maiz": 62.77, "trigo": 67.25}
    factores_tn = {"soja": 0.02721, "maíz": 0.0254, "maiz": 0.0254, "trigo": 0.02721}
    
    f_kg = factores_kg.get(cultivo.lower(), 65.0)
    f_tn = factores_tn.get(cultivo.lower(), 0.026)

    # Conversión 1: Rinde por área (bu/acre -> kg/ha)
    if any(u in texto_lower for u in ["bu/acre", "bushels per acre", "bpa"]):
        if num:
            kg_ha = num * f_kg
            return f"🔄 **Traducción de rinde para Uruguay:** {num} bu/acre ≈ **{kg_ha:.0f} kg/ha**"
    
    # Conversión 2: Volumen general de mercado (bushels -> Toneladas)
    elif "bushels" in texto_lower or "bu " in texto_lower:
        if num:
            toneladas = num * f_tn
            return f"🔄 **Traducción de volumen para Uruguay:** {num:,.0f} bushels ≈ **{toneladas:,.0f} toneladas**"
            
    return None

# --- 🖥️ INTERFAZ DE USUARIO ---
st.title("🌾 AgroTrend Uruguay — Módulo PRO Activo")
st.markdown("### Buscador en Vivo y Detector de Engagement Global en X")
st.markdown("---")

# Panel lateral de control
st.sidebar.header("🔍 Parámetros del Radar")
cultivo_sel = st.sidebar.selectbox("Seleccioná el cultivo a monitorear:", ["Soja", "Maíz", "Trigo"])
st.sidebar.caption("La app buscará posts globales en inglés (mercados de referencia) y traducirá las métricas automáticamente.")

# Armado de la query optimizada para el sector
query_dict = {
    "Soja": "soybean OR soybeans (yield OR market OR weather OR bpa) -is:retweet lang:en",
    "Maíz": "corn OR maize (yield OR market OR weather OR bpa) -is:retweet lang:en",
    "Trigo": "wheat (yield OR market OR weather OR bpa) -is:retweet lang:en"
}

if st.sidebar.button("🔥 Escanear Redes en Tiempo Real"):
    if client is None:
        st.error("La API no está inicializada correctamente. Verifica tus llaves de Secrets.")
    else:
        with st.spinner("Conectando con la base de datos de X..."):
            try:
                # Consulta en vivo utilizando tu cuenta Pro de X
                tweets = client.search_recent_tweets(
                    query=query_dict[cultivo_sel],
                    max_results=15,
                    tweet_fields=['public_metrics', 'created_at', 'id']
                )
                
                if tweets.data:
                    lista_tweets = []
                    for t in tweets.data:
                        metrics = t.public_metrics
                        vistas = metrics.get('impression_count', 0)
                        likes = metrics.get('like_count', 0)
                        reposts = metrics.get('retweet_count', 0)
                        
                        # Algoritmo de calor ponderado (vistas + interacciones de alto valor)
                        hot_score = vistas + (likes * 10) + (reposts * 20)
                        
                        lista_tweets.append({
                            "texto": t.text,
                            "vistas": vistas,
                            "likes": likes,
                            "reposts": reposts,
                            "score": hot_score,
                            "id": t.id
                        })
                    
                    # Ordenamos por los posts con más impacto y viralidad
                    df = pd.DataFrame(lista_tweets).sort_values(by="score", ascending=False)
                    
                    for index, row in df.iterrows():
                        with st.container():
                            col1, col2 = st.columns([3, 1])
                            
                            with col1:
                                st.markdown(f"🔹 {row['texto']}")
                                
                                # Muestra equivalencia métrica si detecta unidades americanas
                                traduccion = convertir_unidades(row['texto'], cultivo_sel)
                                if traduccion:
                                    st.info(traduccion)
                                
                                # Generación de estrategia de contenido para tus productores
                                st.success(
                                    f"💡 **Sugerencia de informe/posteo rápido para Uruguay:**\n\n"
                                    f"*Mundo Agro: Monitoreando tendencias globales vemos alta interacción sobre los rumbos del mercado internacional de {cultivo_sel.lower()}. "
                                    f"Los datos de afuera nos indican volatilidad. Clave seguir de cerca las primas locales e ir evaluando cierres parciales de precio. ¿Cómo vienen planificando sus coberturas?*"
                                )
                                
                            with col2:
                                st.metric(label="🔥 Hot Score", value=f"{row['score']:,}")
                                st.caption(f"👀 Vistas: {row['vistas']:,}\n\n❤️ Likes: {row['likes']} | 🔁 Reposts: {row['reposts']}")
                                st.link_button("🔗 Ver original en X", f"https://x.com/twitter/status/{row['id']}")
                            
                            st.markdown("---")
                else:
                    st.info("No se encontraron publicaciones recientes bajo esos criterios. Probá modificando el cultivo.")
                    
            except Exception as err:
                st.error(f"Error en la consulta en vivo de X: {err}")
