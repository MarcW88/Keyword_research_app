# 🔍 Keyword Research App
# Analyse sémantique guidée — Streamlit

import streamlit as st
import pandas as pd
import requests
import json
import base64
import time
import re
from io import BytesIO
import anthropic

st.set_page_config(
    page_title="Keyword Research",
    page_icon="🔍",
    layout="wide"
)

# API Keys from Streamlit secrets
DATAFORSEO_LOGIN = st.secrets.get("DATAFORSEO_LOGIN", "")
DATAFORSEO_PASSWORD = st.secrets.get("DATAFORSEO_PASSWORD", "")
# Claude key split in 3 parts for security
CLAUDE_API_KEY = st.secrets.get("CLAUDE_API_KEY_1", "") + st.secrets.get("CLAUDE_API_KEY_2", "") + st.secrets.get("CLAUDE_API_KEY_3", "")
JINA_API_KEY = st.secrets.get("JINA_API_KEY", "")

# =============================================================================
# CUSTOM CSS — CHARTE GRAPHIQUE PASTEL
# =============================================================================
st.markdown("""
<style>
/* Fond principal - vert pastel très clair */
.stApp {
    background-color: #F8F9FB;
}

/* Sidebar - pêche pastel */
[data-testid="stSidebar"] {
    background-color: #FDF2EB;
    border-right: 1px solid #E8E8E8;
}

/* Headers - gris foncé */
h1, h2, h3 {
    color: #3A3A3A !important;
    font-weight: 600 !important;
}

/* Cards style pour les expanders */
[data-testid="stExpander"] {
    background-color: #FFFFFF;
    border: 1px solid #E8E8E8;
    border-radius: 8px;
    box-shadow: none;
    margin-bottom: 8px;
}

[data-testid="stExpander"] > div:first-child {
    border-radius: 8px;
}

/* Info boxes - jaune pastel */
.stAlert > div {
    background-color: #FFFFDD !important;
    border: 1px solid #FCFBAA !important;
    border-radius: 6px;
}

/* Success boxes - vert pastel */
.stSuccess > div {
    background-color: #EEFADE !important;
    border: 1px solid #B7D8B2 !important;
}

/* Boutons style pastel */
.stButton > button {
    background-color: #B7D8B2 !important;
    color: #3A3A3A !important;
    border: none !important;
    border-radius: 6px !important;
    font-weight: 500 !important;
    padding: 0.5rem 1rem !important;
    transition: all 0.2s ease !important;
}

.stButton > button:hover {
    background-color: #A3C7E7 !important;
    box-shadow: 0 2px 8px rgba(163, 199, 231, 0.3) !important;
}

/* Metrics - fond blanc, bordure subtile */
[data-testid="stMetric"] {
    background-color: #FFFFFF;
    padding: 12px;
    border-radius: 6px;
    border: 1px solid #E8E8E8;
}

[data-testid="stMetricValue"] {
    color: #3A3A3A !important;
    font-weight: 600 !important;
}

/* DataFrames */
[data-testid="stDataFrame"] {
    border-radius: 6px;
    overflow: hidden;
}

/* Tabs - style pastel */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background-color: transparent;
}

.stTabs [data-baseweb="tab"] {
    background-color: #FFFFFF;
    border-radius: 6px;
    border: 1px solid #E8E8E8;
    padding: 8px 16px;
    color: #3A3A3A;
}

.stTabs [aria-selected="true"] {
    background-color: #DAE8F8 !important;
    border-color: #A3C7E7 !important;
}

/* Progress bar - bleu pastel */
.stProgress > div > div {
    background-color: #A3C7E7 !important;
}

/* Badges de priorité - tons pastel */
.priority-high {
    background-color: #F8C6C6;
    color: #3A3A3A;
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 500;
}

.priority-medium {
    background-color: #FCFBAA;
    color: #3A3A3A;
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 500;
}

.priority-low {
    background-color: #B7D8B2;
    color: #3A3A3A;
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 500;
}

/* Dividers */
hr {
    border-color: #E8E8E8 !important;
}

/* Input fields - style épuré */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stTextArea > div > div > textarea {
    border-radius: 6px !important;
    border-color: #E8E8E8 !important;
    background-color: #FFFFFF !important;
}

.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus {
    border-color: #A3C7E7 !important;
    box-shadow: 0 0 0 2px rgba(163, 199, 231, 0.2) !important;
}

/* Selectbox */
.stSelectbox > div > div {
    border-radius: 6px !important;
}

/* Multiselect */
.stMultiSelect > div > div {
    border-radius: 6px !important;
}
</style>
""", unsafe_allow_html=True)

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================
def priority_badge(priority):
    """Retourne un badge HTML coloré selon la priorité - tons pastel"""
    colors = {
        'HIGH': ('#F8C6C6', '#3A3A3A'),
        'HIGH - Opp': ('#F8C6C6', '#3A3A3A'),
        'MEDIUM': ('#FCFBAA', '#3A3A3A'),
        'LOW': ('#B7D8B2', '#3A3A3A'),
    }
    bg, text = colors.get(priority, ('#E8E8E8', '#3A3A3A'))
    return f'<span style="background-color:{bg}; color:{text}; padding:2px 8px; border-radius:12px; font-size:11px; font-weight:500;">{priority}</span>'

def show_stats_cards(df):
    """Affiche les stats dans des cards stylées"""
    cols = st.columns(4)
    with cols[0]:
        st.metric("📝 Keywords", len(df))
    with cols[1]:
        if 'volume' in df.columns:
            st.metric("📈 Volume total", f"{df['volume'].sum():,.0f}")
    with cols[2]:
        if 'client_pos' in df.columns:
            ranked = df['client_pos'].notna().sum()
            st.metric("🎯 Client ranké", f"{ranked}/{len(df)}")
    with cols[3]:
        if 'has_ai_overview' in df.columns:
            ai = (df['has_ai_overview'] == True).sum()
            st.metric("🤖 AI Overview", ai)

# =============================================================================
# SESSION STATE INIT
# =============================================================================
if 'df_master' not in st.session_state:
    st.session_state.df_master = pd.DataFrame()
if 'step' not in st.session_state:
    st.session_state.step = 0
if 'config_saved' not in st.session_state:
    st.session_state.config_saved = True  # Auto-saved by default

# =============================================================================
# API FUNCTIONS
# =============================================================================
def get_auth_header(login, password):
    creds = f"{login}:{password}"
    return {
        'Authorization': f'Basic {base64.b64encode(creds.encode()).decode()}',
        'Content-Type': 'application/json'
    }

def get_location_config(language):
    loc_map = {
        "be_nl": {"code": 2056, "lang": "nl"},
        "be_fr": {"code": 2056, "lang": "fr"},
        "fr": {"code": 2250, "lang": "fr"},
        "nl": {"code": 2528, "lang": "nl"},
    }
    return loc_map.get(language, {"code": 2056, "lang": "nl"})

def fetch_volumes(keywords, login, password, location_code, language_code):
    """Fetch search volumes via DataForSEO"""
    all_results = {}
    batch_size = 700
    batches = [keywords[i:i+batch_size] for i in range(0, len(keywords), batch_size)]
    
    progress = st.progress(0)
    for i, batch in enumerate(batches):
        try:
            r = requests.post(
                "https://api.dataforseo.com/v3/keywords_data/google_ads/search_volume/live",
                headers=get_auth_header(login, password),
                json=[{"keywords": batch, "location_code": location_code, "language_code": language_code}],
                timeout=120
            )
            data = r.json()
            if data.get('status_code') == 20000:
                for item in (data.get('tasks', [{}])[0].get('result', []) or []):
                    kw = item.get('keyword', '')
                    all_results[kw] = {
                        'volume': item.get('search_volume') or 0,
                        'cpc': item.get('cpc') or 0.0,
                        'competition': item.get('competition') or ''
                    }
        except Exception as e:
            st.warning(f"Batch {i+1} error: {e}")
        progress.progress((i + 1) / len(batches))
        if i < len(batches) - 1:
            time.sleep(1)
    progress.empty()
    return all_results

def extract_keywords_from_site(domain, login, password, location_code, language_code, limit=100):
    """Extract ranked keywords from a domain"""
    try:
        r = requests.post(
            "https://api.dataforseo.com/v3/dataforseo_labs/google/ranked_keywords/live",
            headers=get_auth_header(login, password),
            json=[{
                "target": domain,
                "location_code": location_code,
                "language_code": language_code,
                "limit": limit,
                "order_by": ["keyword_data.keyword_info.search_volume,desc"]
            }],
            timeout=90
        )
        data = r.json()
        if data.get('status_code') != 20000:
            return []
        items = data.get('tasks', [{}])[0].get('result', [{}])[0].get('items', []) or []
        return [item.get('keyword_data', {}).get('keyword', '') for item in items[:limit]]
    except:
        return []

def fetch_page_with_jina(url, jina_key=None):
    """Récupère le contenu d'une page via Jina Reader"""
    if jina_key is None:
        jina_key = JINA_API_KEY
    try:
        r = requests.get(f"https://r.jina.ai/{url}",
            headers={"Authorization": f"Bearer {jina_key}", "X-Return-Format": "markdown"}, timeout=60)
        return r.text[:15000] if r.status_code == 200 else None
    except:
        return None

def generate_claude_seeds(site_content, existing_keywords, num_seeds, language_code, claude_api_key):
    """Génère des seeds via Claude en analysant le contenu du site"""
    try:
        client = anthropic.Anthropic(api_key=claude_api_key)
        prompt = f"""Expert SEO. Analyse ce site et génère des idées de keywords.

Contenu du site:
{site_content[:5000]}

Keywords existants (à ne pas répéter): {json.dumps(existing_keywords[:30], ensure_ascii=False)}

Génère {num_seeds} NOUVEAUX keywords courts (2-4 mots) en {language_code}.
Mix transactionnel + informationnel. Pertinents pour ce business.

Réponds UNIQUEMENT en JSON: {{"keywords": ["kw1", "kw2", ...]}}"""

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )
        match = re.search(r'\{[\s\S]*\}', response.content[0].text)
        if match:
            return json.loads(match.group()).get('keywords', [])
        return []
    except Exception as e:
        st.error(f"Erreur Claude: {e}")
        return []

def analyze_site_context(site_domain, jina_key=None):
    """Analyse le site client avec Jina pour extraire le contexte business"""
    site_url = f"https://www.{site_domain.replace('www.', '')}"
    content = fetch_page_with_jina(site_url, jina_key)
    
    if not content:
        # Essayer sans www
        site_url = f"https://{site_domain.replace('www.', '')}"
        content = fetch_page_with_jina(site_url, jina_key)
    
    return content

def filter_with_claude(keywords, site_domain, language_code, claude_api_key, competitors_list=None, site_context=None):
    """Filtre les keywords non pertinents via Claude - version dynamique basée sur le contexte du site"""
    try:
        client = anthropic.Anthropic(api_key=claude_api_key)
        kw_list = keywords[:500]
        
        # Construire la liste des marques à exclure basée sur les concurrents
        competitor_brands = []
        if competitors_list:
            for comp in competitors_list:
                # Extraire le nom de marque du domaine (ex: vika.be -> vika)
                brand = comp.replace('.be', '').replace('.nl', '').replace('.com', '').replace('.fr', '').replace('www.', '')
                if brand:
                    competitor_brands.append(brand)
        
        # Langue cible en texte clair
        lang_name = "néerlandais" if language_code == "nl" else "français"
        other_lang = "français" if language_code == "nl" else "néerlandais"
        
        # Contexte du site (si disponible)
        context_section = ""
        if site_context:
            context_section = f"""
CONTENU DU SITE CLIENT (extrait via scraping):
{site_context[:4000]}

Utilise ce contenu pour comprendre:
- Quel est le business du client (produits/services vendus)
- Quels thèmes sont pertinents pour ce site
- Quel vocabulaire est utilisé
"""
        else:
            context_section = f"""
NOTE: Le contenu du site n'a pas pu être récupéré. Base-toi uniquement sur le nom de domaine {site_domain} pour deviner le business.
"""
        
        prompt = f"""Tu es un expert SEO. Tu dois filtrer une liste de keywords pour le site {site_domain}.

{context_section}

LANGUE CIBLE: {lang_name} ({language_code})

LISTE DES KEYWORDS À ANALYSER:
{json.dumps(kw_list, ensure_ascii=False)}

MARQUES CONCURRENTES À EXCLURE (extraites des domaines concurrents):
{json.dumps(competitor_brands, ensure_ascii=False)}

RÈGLES DE FILTRAGE - EXCLURE:
1. **Marques concurrentes**: Tout keyword contenant une marque concurrente listée ci-dessus
2. **Grandes marques retail connues**: ikea, leroy merlin, brico, gamma, hubo, action, aldi, lidl, colruyt, amazon, bol.com, coolblue
3. **Mauvaise langue**: Keywords en {other_lang} alors que la cible est {lang_name}. Attention: certains mots peuvent exister dans les deux langues, dans ce cas GARDE-les.
4. **Villes/régions trop spécifiques**: Keywords avec noms de villes belges/françaises/néerlandaises SAUF si le keyword reste pertinent sans la ville
5. **Hors-sujet évident**: Keywords qui n'ont CLAIREMENT aucun rapport avec le business du site (basé sur le contenu scrapé)

RÈGLES DE FILTRAGE - GARDER (IMPORTANT):
1. Keywords génériques liés au business du client
2. Keywords transactionnels (kopen, bestellen, prijs, prix, acheter, commander)
3. Keywords informationnels (hoe, wat, welke, comment, quel, pourquoi)
4. Keywords sur les produits/services même indirectement liés
5. Keywords longue traîne pertinents

⚠️ TRÈS IMPORTANT: Sois TRÈS CONSERVATEUR. En cas de doute, GARDE TOUJOURS le keyword. 
Il vaut mieux garder un keyword potentiellement non-pertinent que supprimer un keyword pertinent.
Ne filtre QUE les keywords qui sont CLAIREMENT hors-sujet ou brandés concurrents.

Réponds UNIQUEMENT avec ce JSON (pas de texte avant/après):
{{"relevant": ["kw1", "kw2", ...], "filtered_out": {{"competitor_brands": ["..."], "wrong_language": ["..."], "locations": ["..."], "off_topic": ["..."]}}}}"""

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=16000,
            messages=[{"role": "user", "content": prompt}]
        )
        match = re.search(r'\{[\s\S]*\}', response.content[0].text)
        if match:
            return json.loads(match.group())
        return {"relevant": keywords, "filtered_out": {}}
    except Exception as e:
        st.error(f"Erreur Claude: {e}")
        return {"relevant": keywords, "filtered_out": {}}

def generate_theme_keywords(themes, keywords_per_theme, language_code, claude_api_key):
    """Génère des keywords par thématique via Claude"""
    try:
        client = anthropic.Anthropic(api_key=claude_api_key)
        prompt = f"""Expert SEO. Génère des keywords de recherche en {language_code}.
Thématiques: {json.dumps(themes, ensure_ascii=False)}
Pour chaque thème, génère {keywords_per_theme} keywords variés (transactionnel + informationnel, 2-4 mots).
JSON: {{"theme1": ["kw1", ...], "theme2": [...]}}"""
        
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=8000,
            messages=[{"role": "user", "content": prompt}]
        )
        match = re.search(r'\{[\s\S]*\}', response.content[0].text)
        if match:
            return json.loads(match.group())
        return {}
    except Exception as e:
        st.error(f"Erreur Claude: {e}")
        return {}

def categorize_with_claude(keywords, site_domain, claude_api_key):
    """Catégorise les keywords via Claude"""
    try:
        client = anthropic.Anthropic(api_key=claude_api_key)
        kw_list = [{"kw": kw} for kw in keywords[:400]]
        
        prompt = f"""Cluster ces keywords pour {site_domain} par catégorie.
Keywords: {json.dumps(kw_list, ensure_ascii=False)}
JSON: {{"categories": {{"Catégorie1": ["kw1", "kw2", ...], "Catégorie2": [...]}}}}"""
        
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=8000,
            messages=[{"role": "user", "content": prompt}]
        )
        match = re.search(r'\{[\s\S]*\}', response.content[0].text)
        if match:
            result = json.loads(match.group())
            return result.get('categories', {})
        return {}
    except Exception as e:
        st.error(f"Erreur Claude: {e}")
        return {}

def get_related_keywords(keyword, login, password, location_code, language_code, limit=30):
    """Keywords liés via Google Ads API"""
    try:
        r = requests.post("https://api.dataforseo.com/v3/keywords_data/google_ads/keywords_for_keywords/live",
            headers=get_auth_header(login, password),
            json=[{"location_code": location_code, "language_code": language_code,
                "keywords": [keyword.lower().strip()]}], timeout=60)
        data = r.json()
        if data.get('status_code') != 20000:
            return []
        return [{'keyword': item.get('keyword', ''), 'volume': item.get('search_volume', 0) or 0}
                for item in (data.get('tasks', [{}])[0].get('result', []) or [])[:limit]]
    except:
        return []

def analyze_serp(keyword, login, password, location_code, language_code, client_domains, competitors):
    """Analyze SERP for a keyword"""
    output = {
        'keyword': keyword,
        'client_pos': None,
        'client_url': '',
        'has_ai_overview': False,
        'client_in_ai': False,
    }
    for c in competitors:
        output[f'{c}_pos'] = None

    try:
        r = requests.post(
            "https://api.dataforseo.com/v3/serp/google/organic/live/advanced",
            headers=get_auth_header(login, password),
            json=[{
                "keyword": keyword,
                "location_code": location_code,
                "language_code": language_code,
                "device": "desktop",
                "depth": 100,
                "load_async_ai_overview": True,
                "expand_ai_overview": True
            }],
            timeout=90
        )
        data = r.json()
        if data.get('status_code') != 20000:
            return output

        task = data.get('tasks', [{}])[0]
        result = task.get('result', [None])[0]
        if not result:
            return output

        items = result.get('items', []) or []
        item_types = result.get('item_types', []) or []

        for item in items:
            if item.get('type') == 'organic':
                domain = (item.get('domain') or '').lower().replace('www.', '')
                pos = item.get('rank_absolute', 0)
                url = item.get('url', '')

                if output['client_pos'] is None:
                    if any(cd.lower() in domain for cd in client_domains):
                        output['client_pos'] = pos
                        output['client_url'] = url

                for comp in competitors:
                    col = f'{comp}_pos'
                    if output[col] is None:
                        if comp.lower().replace('www.', '') in domain:
                            output[col] = pos

        output['has_ai_overview'] = 'ai_overview' in item_types
        return output
    except:
        return output

# =============================================================================
# SIDEBAR — CONFIG
# =============================================================================
with st.sidebar:
    st.header("⚙️ Configuration")
    
    site = st.text_input("Site client", value="dedecker.be")
    language = st.selectbox("Marché", ["be_nl", "be_fr", "fr", "nl"], index=0)
    competitors_input = st.text_area(
        "Concurrents (1 par ligne)",
        value="vika.be\ndsmkeukens.be\ndovykeukens.be\ndiapal.be\nilwa.be"
    )
    
    # Auto-save config on every change
    st.session_state.site = site
    st.session_state.language = language
    st.session_state.competitors = [c.strip() for c in competitors_input.split('\n') if c.strip()]
    st.session_state.dataforseo_login = DATAFORSEO_LOGIN
    st.session_state.dataforseo_password = DATAFORSEO_PASSWORD
    st.session_state.claude_api_key = CLAUDE_API_KEY
    loc = get_location_config(language)
    st.session_state.location_code = loc["code"]
    st.session_state.language_code = loc["lang"]
    st.session_state.client_domains = [site.replace("www.", ""), f"www.{site.replace('www.', '')}"]

# =============================================================================
# MAIN
# =============================================================================
# Header stylé - tons pastel
st.markdown("""
<div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
    <div style="background: linear-gradient(135deg, #B7D8B2 0%, #A3C7E7 100%); 
                width: 44px; height: 44px; border-radius: 10px; 
                display: flex; align-items: center; justify-content: center;
                font-size: 22px;">
        🔍
    </div>
    <div>
        <h1 style="margin: 0; font-size: 24px; color: #3A3A3A;">Keyword Research</h1>
        <p style="margin: 0; color: #8A8A8A; font-size: 13px;">Analyse sémantique guidée</p>
    </div>
</div>
""", unsafe_allow_html=True)

# Tabs pour les différents workflows
tab1, tab2, tab3 = st.tabs(["🟢 Analyse 1 — Nouvelle", "🔄 Analyse 2 — Complément", "⚡ Outils"])

# =============================================================================
# TAB 1 — ANALYSE 1 (Nouvelle recherche complète)
# =============================================================================
with tab1:
    st.markdown("""
    ### 🟢 Première analyse complète
    Chaque étape a ses paramètres. Lance-les dans l'ordre.
    """)
    
    if True:  # Config auto-saved, always show steps
        # ----- ÉTAPE 1 : EXTRACTION SITE -----
        with st.expander("**1️⃣ Extraction Site Client**", expanded=True):
            st.info("📖 **Quoi ?** Récupère les keywords sur lesquels ton site est déjà positionné dans Google (via DataForSEO Labs API).\n\n**Pourquoi ?** C'est ta base — les keywords où tu as déjà une présence.")
            
            col1, col2 = st.columns([2, 1])
            with col1:
                extract_site_limit = st.number_input("Keywords à extraire", value=100, min_value=10, max_value=1000, key="extract_site")
            with col2:
                st.metric("Coût estimé", f"~€{extract_site_limit * 0.002:.2f}")
            
            if st.button("🔍 Extraire du site client", key="btn_extract_site", use_container_width=True):
                progress = st.progress(0, text="Connexion à DataForSEO...")
                progress.progress(30, text=f"Extraction {st.session_state.site}...")
                
                kws = extract_keywords_from_site(
                    st.session_state.site,
                    st.session_state.dataforseo_login,
                    st.session_state.dataforseo_password,
                    st.session_state.location_code,
                    st.session_state.language_code,
                    extract_site_limit
                )
                progress.progress(100, text="Terminé!")
                time.sleep(0.5)
                progress.empty()
                
                if kws:
                    new_df = pd.DataFrame({'keyword': kws, 'source': 'client_site'})
                    st.session_state.df_master = pd.concat([st.session_state.df_master, new_df]).drop_duplicates(subset='keyword')
                    st.success(f"✅ {len(kws)} keywords extraits | Total: {len(st.session_state.df_master)}")
                    
                    # Aperçu output
                    st.markdown("**📋 Aperçu (10 premiers) :**")
                    st.dataframe(pd.DataFrame({'keyword': kws[:10]}), use_container_width=True, hide_index=True)
                else:
                    st.warning("Aucun keyword trouvé pour ce domaine")
        
        # ----- ÉTAPE 2 : EXTRACTION CONCURRENTS -----
        with st.expander("**2️⃣ Extraction Concurrents**"):
            st.info("📖 **Quoi ?** Récupère les keywords sur lesquels tes concurrents sont positionnés.\n\n**Pourquoi ?** Découvrir des opportunités que tu n'as pas encore exploitées.")
            
            col1, col2 = st.columns([2, 1])
            with col1:
                extract_comp_limit = st.number_input("Keywords par concurrent", value=100, min_value=10, max_value=500, key="extract_comp")
                competitors_to_extract = st.multiselect(
                    "Concurrents à analyser",
                    options=st.session_state.competitors,
                    default=st.session_state.competitors
                )
            with col2:
                total_comp = len(competitors_to_extract) * extract_comp_limit
                st.metric("Keywords estimés", f"~{total_comp}")
                st.metric("Coût estimé", f"~€{total_comp * 0.002:.2f}")
            
            if st.button("🔍 Extraire des concurrents", key="btn_extract_comp", use_container_width=True):
                all_kws = []
                status = st.empty()
                progress = st.progress(0)
                
                for i, comp in enumerate(competitors_to_extract):
                    status.text(f"📥 Extraction {comp}...")
                    kws = extract_keywords_from_site(
                        comp,
                        st.session_state.dataforseo_login,
                        st.session_state.dataforseo_password,
                        st.session_state.location_code,
                        st.session_state.language_code,
                        extract_comp_limit
                    )
                    all_kws.extend([{'keyword': kw, 'source': f'competitor:{comp}'} for kw in kws])
                    progress.progress((i + 1) / len(competitors_to_extract))
                    time.sleep(0.5)
                
                progress.empty()
                status.empty()
                
                if all_kws:
                    new_df = pd.DataFrame(all_kws)
                    before = len(st.session_state.df_master)
                    st.session_state.df_master = pd.concat([st.session_state.df_master, new_df]).drop_duplicates(subset='keyword')
                    added = len(st.session_state.df_master) - before
                    st.success(f"✅ {added} nouveaux keywords | Total: {len(st.session_state.df_master)}")
                    
                    # Aperçu par concurrent
                    st.markdown("**📋 Aperçu par concurrent :**")
                    preview_df = pd.DataFrame(all_kws)
                    st.dataframe(preview_df.groupby('source').size().reset_index(name='count'), use_container_width=True, hide_index=True)
                    st.dataframe(preview_df.head(10), use_container_width=True, hide_index=True)
                else:
                    st.warning("Aucun keyword trouvé")
        
        # ----- ÉTAPE 3 : SEEDS CLAUDE -----
        with st.expander("**3️⃣ Seeds Claude (IA)**"):
            st.info("📖 **Quoi ?** Claude analyse le contenu de ton site et génère des idées de keywords pertinentes.\n\n**Pourquoi ?** Trouver des angles que les outils classiques ne détectent pas (intentions, questions, variantes).")
            
            col1, col2 = st.columns([2, 1])
            with col1:
                claude_seeds_count = st.number_input("Nombre de seeds à générer", value=50, min_value=10, max_value=200, key="claude_seeds")
            with col2:
                st.metric("Tokens estimés", f"~{claude_seeds_count * 50}")
            
            if st.button("🤖 Générer seeds avec Claude", key="btn_claude_seeds", use_container_width=True):
                progress = st.progress(0, text="Récupération contenu du site...")
                site_url = f"https://www.{st.session_state.site}"
                site_content = fetch_page_with_jina(site_url)
                
                if not site_content:
                    progress.empty()
                    st.warning("Impossible de récupérer le contenu du site")
                else:
                    progress.progress(30, text="Analyse par Claude...")
                    existing = st.session_state.df_master['keyword'].tolist() if len(st.session_state.df_master) > 0 else []
                    
                    seeds = generate_claude_seeds(
                        site_content,
                        existing,
                        claude_seeds_count,
                        st.session_state.language_code,
                        st.session_state.claude_api_key
                    )
                    progress.progress(70, text="Validation des volumes...")
                    
                    if seeds:
                        # Valider avec volumes
                        vol_data = fetch_volumes(
                            seeds,
                            st.session_state.dataforseo_login,
                            st.session_state.dataforseo_password,
                            st.session_state.location_code,
                            st.session_state.language_code
                        )
                        valid_seeds = [kw for kw in seeds if vol_data.get(kw, {}).get('volume', 0) >= 10]
                        
                        progress.progress(100, text="Terminé!")
                        time.sleep(0.3)
                        progress.empty()
                        
                        if valid_seeds:
                            # Stocker les volumes déjà récupérés pour éviter un double appel
                            new_df = pd.DataFrame({
                                'keyword': valid_seeds, 
                                'source': 'claude_seeds',
                                'volume': [vol_data.get(kw, {}).get('volume', 0) for kw in valid_seeds],
                                'cpc': [vol_data.get(kw, {}).get('cpc', 0.0) for kw in valid_seeds]
                            })
                            before = len(st.session_state.df_master)
                            st.session_state.df_master = pd.concat([st.session_state.df_master, new_df]).drop_duplicates(subset='keyword')
                            added = len(st.session_state.df_master) - before
                            
                            st.success(f"✅ {len(seeds)} générés → {len(valid_seeds)} avec volume | {added} nouveaux ajoutés")
                            st.markdown("**📋 Seeds générés :**")
                            st.dataframe(pd.DataFrame({'keyword': valid_seeds[:15]}), use_container_width=True, hide_index=True)
                        else:
                            st.warning("Aucun seed avec volume suffisant")
                    else:
                        progress.empty()
                        st.warning("Claude n'a pas généré de seeds")
        
        # ----- ÉTAPE 4 : EXPANSION RELATED -----
        with st.expander("**4️⃣ Expansion (Related Keywords)**"):
            st.info("📖 **Quoi ?** Sélectionne les meilleurs keywords (top volume + diversité par cluster) et cherche les keywords liés via Google Ads API.\n\n**Pourquoi ?** Élargir ta liste avec des variantes et synonymes que les utilisateurs recherchent vraiment.")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                expansion_top_volume = st.number_input("Top keywords par volume", value=50, min_value=10, max_value=200, key="exp_top")
            with col2:
                expansion_per_cluster = st.number_input("Keywords par cluster", value=10, min_value=5, max_value=50, key="exp_cluster")
            with col3:
                related_per_keyword = st.number_input("Related par keyword", value=30, min_value=10, max_value=100, key="related_per")
            
            total_seeds = expansion_top_volume + (15 * expansion_per_cluster)
            st.caption(f"📊 Seeds estimés: ~{total_seeds} | Related estimés: ~{total_seeds * related_per_keyword} | Coût: ~€{total_seeds * 0.005:.2f}")
            
            if st.button("🔗 Lancer expansion", key="btn_expansion", use_container_width=True):
                if len(st.session_state.df_master) == 0:
                    st.warning("Lance d'abord l'extraction (étapes 1-3)")
                elif 'volume' not in st.session_state.df_master.columns:
                    st.warning("Lance d'abord l'étape 5 (Volumes) pour avoir les données de volume")
                else:
                    df_with_vol = st.session_state.df_master[st.session_state.df_master['volume'] > 0].copy()
                    
                    if len(df_with_vol) == 0:
                        st.warning("Pas de keywords avec volume")
                    else:
                        # Sélection seeds: top volume + clusters
                        top_seeds = df_with_vol.nlargest(expansion_top_volume, 'volume')['keyword'].tolist()
                        
                        # Clusters par mots communs
                        clusters = {}
                        for kw in df_with_vol['keyword'].tolist():
                            for w in kw.lower().split():
                                if len(w) > 4:
                                    clusters.setdefault(w, []).append(kw)
                        
                        vol_dict = dict(zip(df_with_vol['keyword'], df_with_vol['volume']))
                        cluster_seeds = set()
                        for theme, kws in sorted(clusters.items(), key=lambda x: len(x[1]), reverse=True)[:15]:
                            sorted_kws = sorted(kws, key=lambda k: vol_dict.get(k, 0), reverse=True)
                            cluster_seeds.update(sorted_kws[:expansion_per_cluster])
                        
                        seeds = list(set(top_seeds) | cluster_seeds)
                        st.info(f"� {len(seeds)} seeds sélectionnés (top {expansion_top_volume} + clusters)")
                        
                        # Récupérer related
                        all_related = []
                        progress = st.progress(0)
                        status = st.empty()
                        
                        for i, seed in enumerate(seeds):
                            status.text(f"🔗 {i+1}/{len(seeds)} — {seed[:30]}...")
                            related = get_related_keywords(
                                seed,
                                st.session_state.dataforseo_login,
                                st.session_state.dataforseo_password,
                                st.session_state.location_code,
                                st.session_state.language_code,
                                related_per_keyword
                            )
                            all_related.extend([r['keyword'] for r in related if r['volume'] >= 10])
                            progress.progress((i + 1) / len(seeds))
                            time.sleep(0.3)
                        
                        progress.empty()
                        status.empty()
                        
                        unique_related = list(set(all_related))
                        if unique_related:
                            new_df = pd.DataFrame({'keyword': unique_related, 'source': 'related'})
                            before = len(st.session_state.df_master)
                            st.session_state.df_master = pd.concat([st.session_state.df_master, new_df]).drop_duplicates(subset='keyword')
                            added = len(st.session_state.df_master) - before
                            
                            st.success(f"✅ {len(unique_related)} related uniques | {added} nouveaux ajoutés")
                            st.markdown("**📋 Exemples related :**")
                            st.dataframe(pd.DataFrame({'keyword': unique_related[:15]}), use_container_width=True, hide_index=True)
                        else:
                            st.warning("Aucun related keyword trouvé")
        
        # ----- ÉTAPE 5 : VOLUMES -----
        with st.expander("**5️⃣ Récupérer Volumes**"):
            st.info("📖 **Quoi ?** Récupère le volume de recherche mensuel + CPC pour chaque keyword via Google Ads API.\n\n**Pourquoi ?** Prioriser les keywords avec du potentiel de trafic réel.")
            
            missing_vol = 0
            if len(st.session_state.df_master) > 0 and 'volume' in st.session_state.df_master.columns:
                # Seulement les None, pas les 0 (0 = déjà vérifié, pas de volume)
                missing_vol = st.session_state.df_master['volume'].isna().sum()
            else:
                missing_vol = len(st.session_state.df_master)
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Keywords sans volume", missing_vol)
            with col2:
                st.metric("Coût estimé", f"~€{missing_vol * 0.005:.2f}")
            
            if st.button("📊 Récupérer Volumes", key="btn_volumes", use_container_width=True):
                if len(st.session_state.df_master) == 0:
                    st.warning("Pas de keywords — lance d'abord l'extraction")
                else:
                    # Identifier les keywords sans volume (nouveaux ou jamais traités)
                    if 'volume' not in st.session_state.df_master.columns:
                        st.session_state.df_master['volume'] = None
                        st.session_state.df_master['cpc'] = None
                    
                    # Keywords à traiter = ceux sans volume (None ou jamais défini)
                    mask_missing = st.session_state.df_master['volume'].isna()
                    keywords_to_fetch = st.session_state.df_master[mask_missing]['keyword'].tolist()
                    
                    if len(keywords_to_fetch) == 0:
                        st.info("✅ Tous les keywords ont déjà un volume. Rien à récupérer.")
                    else:
                        status = st.empty()
                        status.text(f"📊 Récupération volumes pour {len(keywords_to_fetch)} keywords...")
                        
                        vol_data = fetch_volumes(
                            keywords_to_fetch,
                            st.session_state.dataforseo_login,
                            st.session_state.dataforseo_password,
                            st.session_state.location_code,
                            st.session_state.language_code
                        )
                        
                        # Mettre à jour uniquement les keywords sans volume
                        for idx, row in st.session_state.df_master[mask_missing].iterrows():
                            kw = row['keyword']
                            st.session_state.df_master.at[idx, 'volume'] = vol_data.get(kw, {}).get('volume', 0)
                            st.session_state.df_master.at[idx, 'cpc'] = vol_data.get(kw, {}).get('cpc', 0.0)
                        
                        status.empty()
                        
                        total_vol = st.session_state.df_master['volume'].sum()
                        with_vol = (st.session_state.df_master['volume'] > 0).sum()
                        st.success(f"✅ {len(keywords_to_fetch)} volumes récupérés — {with_vol}/{len(st.session_state.df_master)} avec volume | Total: {total_vol:,.0f}")
                        
                        # Aperçu top volumes
                        st.markdown("**📋 Top 10 par volume :**")
                        top_vol = st.session_state.df_master.nlargest(10, 'volume')[['keyword', 'volume', 'cpc']]
                        st.dataframe(top_vol, use_container_width=True, hide_index=True)
        
        # ----- ÉTAPE 6 : FILTRAGE -----
        with st.expander("**6️⃣ Filtrage**"):
            st.info("📖 **Quoi ?** Supprime les keywords avec volume trop faible + filtrage intelligent via Claude (marques concurrentes, hors-sujet, autres langues).\n\n**Pourquoi ?** Nettoyer ta liste pour ne garder que les keywords pertinents et actionnables.")
            
            col1, col2 = st.columns(2)
            with col1:
                min_volume = st.number_input("Volume minimum", value=10, min_value=0, key="min_vol")
            with col2:
                if 'volume' in st.session_state.df_master.columns:
                    to_remove = (st.session_state.df_master['volume'] < min_volume).sum()
                    st.metric("À supprimer", to_remove)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🗑️ Filtrer par volume", key="btn_filter_vol", use_container_width=True):
                    if 'volume' in st.session_state.df_master.columns:
                        before = len(st.session_state.df_master)
                        removed_kws = st.session_state.df_master[st.session_state.df_master['volume'] < min_volume]['keyword'].tolist()
                        st.session_state.df_master = st.session_state.df_master[
                            st.session_state.df_master['volume'] >= min_volume
                        ].reset_index(drop=True)
                        removed = before - len(st.session_state.df_master)
                        st.success(f"✅ {removed} supprimés — Reste: {len(st.session_state.df_master)}")
                        
                        if removed > 0:
                            st.markdown("**📋 Exemples supprimés :**")
                            st.code('\n'.join(removed_kws[:10]))
            with col2:
                if st.button("🧹 Filtrage Claude (marques, etc.)", key="btn_filter_claude", use_container_width=True):
                    if len(st.session_state.df_master) == 0:
                        st.warning("Pas de keywords à filtrer")
                    else:
                        keywords = st.session_state.df_master['keyword'].tolist()
                        progress = st.progress(0, text="Scraping du site client avec Jina...")
                        
                        # Scraper le site pour comprendre le business
                        site_context = analyze_site_context(st.session_state.site)
                        
                        progress.progress(30, text="Analyse par Claude...")
                        
                        result = filter_with_claude(
                            keywords,
                            st.session_state.site,
                            st.session_state.language_code,
                            st.session_state.claude_api_key,
                            st.session_state.competitors,
                            site_context  # Passer le contexte du site
                        )
                        progress.progress(100, text="Terminé!")
                        time.sleep(0.3)
                        progress.empty()
                        
                        relevant = result.get('relevant', keywords)
                        filtered_out = result.get('filtered_out', {})
                        
                        before = len(st.session_state.df_master)
                        st.session_state.df_master = st.session_state.df_master[
                            st.session_state.df_master['keyword'].isin(relevant)
                        ].reset_index(drop=True)
                        removed = before - len(st.session_state.df_master)
                        
                        st.success(f"✅ {removed} filtrés — Reste: {len(st.session_state.df_master)}")
                        
                        # Détails par catégorie
                        if filtered_out:
                            st.markdown("**📋 Filtrés par catégorie :**")
                            cat_labels = {
                                'competitor_brands': '🏷️ Marques concurrentes',
                                'wrong_language': '🌍 Mauvaise langue',
                                'locations': '📍 Villes/Locations',
                                'off_topic': '❌ Hors-sujet',
                                'competitors': '🏷️ Concurrents',
                                'other': '❓ Autres'
                            }
                            for cat, items in filtered_out.items():
                                if items and len(items) > 0:
                                    label = cat_labels.get(cat, cat)
                                    st.caption(f"**{label}** ({len(items)}): {', '.join(items[:8])}{'...' if len(items) > 8 else ''}")
        
        # ----- ÉTAPE 6b : CATÉGORISATION (E1) -----
        with st.expander("**6️⃣b Catégorisation Claude**"):
            st.info("📖 **Quoi ?** Claude analyse les keywords et les regroupe par catégorie thématique.\n\n**Pourquoi ?** Organiser ta liste pour prioriser par thème et créer des silos de contenu.")
            
            only_uncategorized = st.checkbox("Uniquement les non-catégorisés", value=True, key="only_uncat")
            
            to_categorize = 0
            if len(st.session_state.df_master) > 0:
                if only_uncategorized and 'category' in st.session_state.df_master.columns:
                    to_categorize = st.session_state.df_master['category'].isna().sum() + (st.session_state.df_master['category'] == '').sum()
                else:
                    to_categorize = len(st.session_state.df_master)
            
            st.metric("Keywords à catégoriser", to_categorize)
            
            if st.button("🏷️ Catégoriser avec Claude", key="btn_categorize", use_container_width=True):
                if len(st.session_state.df_master) == 0:
                    st.warning("Pas de keywords")
                else:
                    if only_uncategorized and 'category' in st.session_state.df_master.columns:
                        kws_to_cat = st.session_state.df_master[
                            st.session_state.df_master['category'].isna() | (st.session_state.df_master['category'] == '')
                        ]['keyword'].tolist()
                    else:
                        kws_to_cat = st.session_state.df_master['keyword'].tolist()
                    
                    if not kws_to_cat:
                        st.success("✅ Tous les keywords sont déjà catégorisés")
                    else:
                        progress = st.progress(0, text="Catégorisation par Claude...")
                        
                        categories = categorize_with_claude(
                            kws_to_cat,
                            st.session_state.site,
                            st.session_state.claude_api_key
                        )
                        progress.progress(100, text="Terminé!")
                        time.sleep(0.3)
                        progress.empty()
                        
                        if categories:
                            # Construire mapping keyword → category
                            kw_cat_map = {}
                            for cat, kws in categories.items():
                                for kw in kws:
                                    kw_str = kw if isinstance(kw, str) else kw.get('kw', '')
                                    kw_cat_map[kw_str.lower()] = cat
                            
                            # Appliquer au master
                            if 'category' not in st.session_state.df_master.columns:
                                st.session_state.df_master['category'] = ''
                            
                            for idx, row in st.session_state.df_master.iterrows():
                                cat = kw_cat_map.get(row['keyword'].lower())
                                if cat:
                                    st.session_state.df_master.at[idx, 'category'] = cat
                            
                            categorized = (st.session_state.df_master['category'].notna() & (st.session_state.df_master['category'] != '')).sum()
                            st.success(f"✅ {categorized}/{len(st.session_state.df_master)} catégorisés")
                            
                            st.markdown("**📋 Catégories :**")
                            for cat, kws in categories.items():
                                st.caption(f"**{cat}**: {len(kws)} keywords")
                        else:
                            st.warning("Erreur de catégorisation")
        
        # ----- ÉTAPE 7 : SERP -----
        with st.expander("**7️⃣ Analyse SERP + AI Overview**"):
            st.info("📖 **Quoi ?** Pour chaque keyword, récupère la position de ton site + concurrents dans les 100 premiers résultats Google, et détecte la présence d'AI Overview.\n\n**Pourquoi ?** Identifier où tu ranks, où sont tes concurrents, et les opportunités de positionnement.")
            
            col1, col2, col3 = st.columns(3)
            
            # Options SERP
            force_rescan = st.checkbox("Force rescan (tout rescanner)", value=False, key="force_rescan")
            
            # Filtre par catégorie
            categories_list = []
            if 'category' in st.session_state.df_master.columns:
                categories_list = st.session_state.df_master['category'].dropna().unique().tolist()
            scan_category = st.selectbox("Filtrer par catégorie", [""] + categories_list, key="scan_cat")
            
            # Compter keywords sans SERP
            df_to_scan = st.session_state.df_master.copy()
            if scan_category:
                df_to_scan = df_to_scan[df_to_scan['category'] == scan_category]
            
            if force_rescan:
                needs_serp = len(df_to_scan)
            else:
                if 'client_pos' in df_to_scan.columns:
                    needs_serp = df_to_scan['client_pos'].isna().sum()
                else:
                    needs_serp = len(df_to_scan)
            
            with col1:
                final_limit = st.number_input("Limite (0 = tous)", value=0, min_value=0, max_value=1000, key="final_limit")
            with col2:
                actual_count = needs_serp if final_limit == 0 else min(final_limit, needs_serp)
                st.metric("Keywords à analyser", actual_count)
            with col3:
                st.metric("Coût estimé", f"~€{actual_count * 0.0075:.2f}")
                st.caption(f"⏱️ ~{actual_count * 1.5 / 60:.0f} min")
            
            if st.button("🎯 Analyser SERP", key="btn_serp", use_container_width=True):
                if len(df_to_scan) == 0:
                    st.warning("Pas de keywords")
                else:
                    # Sélectionner les keywords à scanner
                    if force_rescan:
                        keywords = df_to_scan['keyword'].tolist()
                    else:
                        if 'client_pos' in df_to_scan.columns:
                            keywords = df_to_scan[df_to_scan['client_pos'].isna()]['keyword'].tolist()
                        else:
                            keywords = df_to_scan['keyword'].tolist()
                    
                    if final_limit > 0:
                        keywords = keywords[:final_limit]
                    
                    results = []
                    progress = st.progress(0)
                    status = st.empty()
                    
                    for i, kw in enumerate(keywords):
                        status.text(f"🔍 {i+1}/{len(keywords)} — {kw[:40]}...")
                        result = analyze_serp(
                            kw,
                            st.session_state.dataforseo_login,
                            st.session_state.dataforseo_password,
                            st.session_state.location_code,
                            st.session_state.language_code,
                            st.session_state.client_domains,
                            st.session_state.competitors
                        )
                        results.append(result)
                        progress.progress((i + 1) / len(keywords))
                        time.sleep(1)
                    
                    progress.empty()
                    status.empty()
                    
                    df_serp = pd.DataFrame(results)
                    serp_cols = [c for c in df_serp.columns if c != 'keyword']
                    for col in serp_cols:
                        st.session_state.df_master[col] = st.session_state.df_master['keyword'].map(
                            df_serp.set_index('keyword')[col].to_dict()
                        )
                    
                    # Stats
                    client_ranked = df_serp['client_pos'].notna().sum()
                    ai_count = (df_serp['has_ai_overview'] == True).sum()
                    
                    st.success(f"✅ SERP terminé — Client ranké: {client_ranked}/{len(keywords)} | AI Overview: {ai_count}")
                    
                    # Aperçu résultats
                    st.markdown("**📋 Aperçu positions :**")
                    cols_to_show = ['keyword', 'client_pos'] + [f'{c}_pos' for c in st.session_state.competitors if f'{c}_pos' in df_serp.columns]
                    st.dataframe(df_serp[cols_to_show].head(10), use_container_width=True, hide_index=True)
                    
                    # Stats concurrents
                    st.markdown("**📊 Résumé positions :**")
                    stats = {'Client': client_ranked}
                    for c in st.session_state.competitors:
                        col = f'{c}_pos'
                        if col in df_serp.columns:
                            stats[c] = df_serp[col].notna().sum()
                    st.dataframe(pd.DataFrame([stats]), use_container_width=True, hide_index=True)
        
        # État actuel
        st.divider()
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 16px;">
            <div style="width: 3px; height: 20px; background: linear-gradient(135deg, #B7D8B2 0%, #A3C7E7 100%); border-radius: 2px;"></div>
            <h3 style="margin: 0; color: #3A3A3A;">État actuel</h3>
        </div>
        """, unsafe_allow_html=True)
        
        if len(st.session_state.df_master) > 0:
            show_stats_cards(st.session_state.df_master)
            
            st.dataframe(st.session_state.df_master.head(20), use_container_width=True, hide_index=True)
            
            # Export
            st.subheader("📥 Export")
            buffer = BytesIO()
            st.session_state.df_master.to_excel(buffer, index=False)
            st.download_button(
                "⬇️ Télécharger Excel",
                data=buffer.getvalue(),
                file_name=f"Keywords_{st.session_state.site.replace('.', '_')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.info("Aucun keyword — lance l'extraction pour commencer")

# =============================================================================
# TAB 2 — ANALYSE 2 (Complément)
# =============================================================================
with tab2:
    st.markdown("""
    ### 🔄 Compléter une analyse existante
    **Workflow :** B1 (charger fichier) → C2/C4 (nouveaux concurrents ou thématiques) → D1 (volumes) → D2 (filtrage) → E1 (catégorisation) → F (SERP) → G (export)
    """)
    
    # ----- B1 : CHARGER FICHIER EXISTANT -----
    with st.expander("**B1 — Charger fichier existant**", expanded=True):
        st.info("📖 Charge ton fichier Excel d'une analyse précédente pour y ajouter des keywords.")
        
        uploaded = st.file_uploader("📂 Charger fichier existant", type=['xlsx'], key="upload_complement")
        if uploaded:
            df_loaded = pd.read_excel(uploaded)
            df_loaded.columns = df_loaded.columns.str.strip()
            if 'Keyword' in df_loaded.columns:
                df_loaded = df_loaded.rename(columns={'Keyword': 'keyword'})
            st.session_state.df_master = df_loaded
            st.success(f"✅ {len(df_loaded)} keywords chargés")
            
            # Stats du fichier chargé
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Keywords", len(df_loaded))
            with col2:
                if 'volume' in df_loaded.columns:
                    st.metric("Volume total", f"{df_loaded['volume'].sum():,.0f}")
            with col3:
                if 'category' in df_loaded.columns:
                    cats = df_loaded['category'].nunique()
                    st.metric("Catégories", cats)
            
            st.dataframe(df_loaded.head(5), use_container_width=True, hide_index=True)
    
    # ----- C2 : NOUVEAUX CONCURRENTS -----
    with st.expander("**C2 — Extraction nouveaux concurrents**"):
        st.info("📖 Ajoute des keywords depuis de nouveaux concurrents que tu n'avais pas analysés avant.")
        
        new_competitors = st.text_area("Nouveaux concurrents (1 par ligne)", key="new_comp_tab2", height=80)
        extract_limit_c2 = st.number_input("Keywords par concurrent", value=100, min_value=10, max_value=500, key="extract_c2")
        
        if st.button("🔍 Extraire nouveaux concurrents", key="btn_extract_new_comp", use_container_width=True):
            comp_list = [c.strip() for c in new_competitors.split('\n') if c.strip()]
            if not comp_list:
                st.warning("Ajoute au moins un concurrent")
            else:
                all_kws = []
                progress = st.progress(0)
                for i, comp in enumerate(comp_list):
                    progress.progress((i + 1) / len(comp_list), text=f"📥 {comp}...")
                    kws = extract_keywords_from_site(
                        comp,
                        st.session_state.dataforseo_login,
                        st.session_state.dataforseo_password,
                        st.session_state.location_code,
                        st.session_state.language_code,
                        extract_limit_c2
                    )
                    all_kws.extend([{'keyword': kw, 'source': f'competitor:{comp}'} for kw in kws])
                    time.sleep(0.5)
                progress.empty()
                
                if all_kws:
                    new_df = pd.DataFrame(all_kws)
                    before = len(st.session_state.df_master)
                    st.session_state.df_master = pd.concat([st.session_state.df_master, new_df]).drop_duplicates(subset='keyword')
                    added = len(st.session_state.df_master) - before
                    st.success(f"✅ {len(all_kws)} extraits | {added} nouveaux ajoutés")
    
    # ----- C4 : THÉMATIQUES SPÉCIFIQUES -----
    with st.expander("**C4 — Thématiques spécifiques (Claude)**"):
        st.info("📖 **Quoi ?** Donne des thèmes que tu veux explorer → Claude génère des keywords ciblés pour chaque thème.\n\n**Pourquoi ?** Ajouter des angles spécifiques que l'analyse initiale n'a pas couverts.")
        
        themes_input = st.text_area("Thématiques à explorer (1 par ligne)", value="", key="themes_input_tab2", height=100,
                                     placeholder="Ex:\nkeuken renovatie\nbadkamer inrichting\nmaatwerk interieur")
        col1, col2 = st.columns(2)
        with col1:
            keywords_per_theme = st.number_input("Keywords par thème", value=30, min_value=10, max_value=100, key="kw_per_theme_tab2")
        with col2:
            themes_list = [t.strip() for t in themes_input.split('\n') if t.strip()]
            st.metric("Thèmes", len(themes_list))
        
        if st.button("🎯 Générer par thématiques", key="btn_themes_tab2", use_container_width=True):
            if not themes_list:
                st.warning("Ajoute au moins un thème")
            else:
                progress = st.progress(0, text="Génération par Claude...")
                
                result = generate_theme_keywords(
                    themes_list,
                    keywords_per_theme,
                    st.session_state.language_code,
                    st.session_state.claude_api_key
                )
                progress.progress(50, text="Validation des volumes...")
                
                all_theme_kw = []
                for theme, kws in result.items():
                    all_theme_kw.extend([kw for kw in kws if isinstance(kw, str)])
                
                if all_theme_kw:
                    # Valider volumes
                    vol_data = fetch_volumes(
                        all_theme_kw,
                        st.session_state.dataforseo_login,
                        st.session_state.dataforseo_password,
                        st.session_state.location_code,
                        st.session_state.language_code
                    )
                    valid = [kw for kw in all_theme_kw if vol_data.get(kw, {}).get('volume', 0) >= 10]
                    
                    progress.progress(100, text="Terminé!")
                    time.sleep(0.3)
                    progress.empty()
                    
                    if valid:
                        # Stocker les volumes déjà récupérés pour éviter un double appel
                        new_df = pd.DataFrame({
                            'keyword': valid, 
                            'source': 'theme',
                            'volume': [vol_data.get(kw, {}).get('volume', 0) for kw in valid],
                            'cpc': [vol_data.get(kw, {}).get('cpc', 0.0) for kw in valid]
                        })
                        before = len(st.session_state.df_master)
                        st.session_state.df_master = pd.concat([st.session_state.df_master, new_df]).drop_duplicates(subset='keyword')
                        added = len(st.session_state.df_master) - before
                        
                        st.success(f"✅ {len(all_theme_kw)} générés → {len(valid)} avec volume | {added} nouveaux")
                        st.markdown("**📋 Par thème :**")
                        for theme, kws in result.items():
                            st.caption(f"**{theme}**: {len(kws)} keywords")
                    else:
                        st.warning("Aucun keyword avec volume suffisant")
                else:
                    progress.empty()
                    st.warning("Aucun keyword généré")
    
    # ----- D1 : VOLUMES NOUVEAUX -----
    with st.expander("**D1 — Volumes (nouveaux uniquement)**"):
        st.info("📖 Récupère les volumes uniquement pour les keywords qui n'en ont pas encore (colonne volume = None).")
        
        missing_vol = 0
        if len(st.session_state.df_master) > 0 and 'volume' in st.session_state.df_master.columns:
            # Seulement les None, pas les 0 (0 = déjà vérifié, pas de volume)
            missing_vol = st.session_state.df_master['volume'].isna().sum()
        else:
            missing_vol = len(st.session_state.df_master)
        
        st.metric("Keywords sans volume", missing_vol)
        
        if st.button("📊 Récupérer Volumes manquants", key="btn_vol_tab2", use_container_width=True):
            if missing_vol == 0:
                st.success("✅ Tous les keywords ont déjà un volume (ou ont été vérifiés)")
            else:
                # Filtrer ceux sans volume (None seulement, pas 0)
                if 'volume' in st.session_state.df_master.columns:
                    kws_missing = st.session_state.df_master[
                        st.session_state.df_master['volume'].isna()
                    ]['keyword'].tolist()
                else:
                    kws_missing = st.session_state.df_master['keyword'].tolist()
                
                vol_data = fetch_volumes(
                    kws_missing,
                    st.session_state.dataforseo_login,
                    st.session_state.dataforseo_password,
                    st.session_state.location_code,
                    st.session_state.language_code
                )
                
                if 'volume' not in st.session_state.df_master.columns:
                    st.session_state.df_master['volume'] = 0
                
                for idx, row in st.session_state.df_master.iterrows():
                    if row['keyword'] in kws_missing:
                        st.session_state.df_master.at[idx, 'volume'] = vol_data.get(row['keyword'], {}).get('volume', 0)
                        st.session_state.df_master.at[idx, 'cpc'] = vol_data.get(row['keyword'], {}).get('cpc', 0)
                
                updated = sum(1 for kw in kws_missing if vol_data.get(kw, {}).get('volume', 0) > 0)
                st.success(f"✅ {updated}/{len(kws_missing)} volumes mis à jour")
    
    # ----- E1 : CATÉGORISATION NOUVEAUX -----
    with st.expander("**E1 — Catégoriser les nouveaux**"):
        st.info("📖 Catégorise uniquement les keywords qui n'ont pas encore de catégorie.")
        
        uncategorized = 0
        if len(st.session_state.df_master) > 0:
            if 'category' in st.session_state.df_master.columns:
                uncategorized = st.session_state.df_master['category'].isna().sum() + (st.session_state.df_master['category'] == '').sum()
            else:
                uncategorized = len(st.session_state.df_master)
        
        st.metric("Keywords non catégorisés", uncategorized)
        
        if st.button("🏷️ Catégoriser nouveaux", key="btn_cat_tab2", use_container_width=True):
            if uncategorized == 0:
                st.success("✅ Tous les keywords sont déjà catégorisés")
            else:
                if 'category' in st.session_state.df_master.columns:
                    kws_to_cat = st.session_state.df_master[
                        st.session_state.df_master['category'].isna() | (st.session_state.df_master['category'] == '')
                    ]['keyword'].tolist()
                else:
                    kws_to_cat = st.session_state.df_master['keyword'].tolist()
                
                progress = st.progress(0, text="Catégorisation Claude...")
                categories = categorize_with_claude(kws_to_cat, st.session_state.site, st.session_state.claude_api_key)
                progress.progress(100)
                progress.empty()
                
                if categories:
                    kw_cat_map = {}
                    for cat, kws in categories.items():
                        for kw in kws:
                            kw_str = kw if isinstance(kw, str) else kw.get('kw', '')
                            kw_cat_map[kw_str.lower()] = cat
                    
                    if 'category' not in st.session_state.df_master.columns:
                        st.session_state.df_master['category'] = ''
                    
                    for idx, row in st.session_state.df_master.iterrows():
                        cat = kw_cat_map.get(row['keyword'].lower())
                        if cat:
                            st.session_state.df_master.at[idx, 'category'] = cat
                    
                    st.success(f"✅ {len(kw_cat_map)} keywords catégorisés")
    
    # ----- F : SERP NOUVEAUX -----
    with st.expander("**F — SERP (nouveaux uniquement)**"):
        st.info("📖 Analyse SERP uniquement pour les keywords qui n'ont pas encore de position.")
        
        needs_serp = 0
        if len(st.session_state.df_master) > 0:
            if 'client_pos' in st.session_state.df_master.columns:
                needs_serp = st.session_state.df_master['client_pos'].isna().sum()
            else:
                needs_serp = len(st.session_state.df_master)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Keywords sans SERP", needs_serp)
        with col2:
            st.metric("Coût estimé", f"~€{needs_serp * 0.0075:.2f}")
        
        if st.button("🎯 Analyser SERP nouveaux", key="btn_serp_tab2", use_container_width=True):
            if needs_serp == 0:
                st.success("✅ Tous les keywords ont déjà des données SERP")
            else:
                if 'client_pos' in st.session_state.df_master.columns:
                    kws_to_scan = st.session_state.df_master[
                        st.session_state.df_master['client_pos'].isna()
                    ]['keyword'].tolist()
                else:
                    kws_to_scan = st.session_state.df_master['keyword'].tolist()
                
                results = []
                progress = st.progress(0)
                for i, kw in enumerate(kws_to_scan):
                    progress.progress((i + 1) / len(kws_to_scan), text=f"🔍 {kw[:30]}...")
                    result = analyze_serp(
                        kw,
                        st.session_state.dataforseo_login,
                        st.session_state.dataforseo_password,
                        st.session_state.location_code,
                        st.session_state.language_code,
                        st.session_state.client_domains,
                        st.session_state.competitors
                    )
                    results.append(result)
                    time.sleep(1)
                progress.empty()
                
                df_serp = pd.DataFrame(results)
                serp_cols = [c for c in df_serp.columns if c != 'keyword']
                for col in serp_cols:
                    if col not in st.session_state.df_master.columns:
                        st.session_state.df_master[col] = None
                    for idx, row in st.session_state.df_master.iterrows():
                        if row['keyword'] in df_serp['keyword'].values:
                            val = df_serp[df_serp['keyword'] == row['keyword']][col].values[0]
                            st.session_state.df_master.at[idx, col] = val
                
                client_ranked = df_serp['client_pos'].notna().sum()
                st.success(f"✅ SERP terminé — Client ranké: {client_ranked}/{len(kws_to_scan)}")
    
    # ----- G : EXPORT -----
    st.divider()
    if len(st.session_state.df_master) > 0:
        st.subheader("📥 Export")
        buffer = BytesIO()
        st.session_state.df_master.to_excel(buffer, index=False)
        st.download_button(
            "⬇️ Télécharger Excel (mise à jour)",
            data=buffer.getvalue(),
            file_name=f"Keywords_{st.session_state.site.replace('.', '_')}_updated.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

# =============================================================================
# TAB 3 — OUTILS
# =============================================================================
with tab3:
    st.markdown("### Outils rapides")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🗑️ Reset")
        if st.button("Vider le master", use_container_width=True):
            st.session_state.df_master = pd.DataFrame()
            st.success("✅ Master vidé")
    
    with col2:
        st.subheader("📊 Stats")
        if len(st.session_state.df_master) > 0:
            st.write(f"**Keywords:** {len(st.session_state.df_master)}")
            if 'source' in st.session_state.df_master.columns:
                st.write("**Par source:**")
                st.write(st.session_state.df_master['source'].value_counts())
