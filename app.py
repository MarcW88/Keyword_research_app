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

# Détection de langue
try:
    from langdetect import detect, DetectorFactory
    DetectorFactory.seed = 0  # Pour des résultats reproductibles
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False

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

def detect_keyword_language(keyword):
    """Détecte la langue d'un keyword avec langdetect"""
    if not LANGDETECT_AVAILABLE:
        return None
    try:
        # langdetect retourne 'nl', 'fr', 'en', 'de', etc.
        lang = detect(keyword)
        return lang
    except:
        return None

def filter_by_language(keywords, target_lang_code):
    """
    Filtre les keywords par langue de manière programmatique.
    target_lang_code: 'nl' pour néerlandais, 'fr' pour français
    Retourne: (keywords_ok, keywords_wrong_lang)
    """
    if not LANGDETECT_AVAILABLE:
        return keywords, []
    
    keywords_ok = []
    keywords_wrong_lang = []
    
    # Mots ambigus qui existent dans plusieurs langues (garder toujours)
    ambiguous_words = {'etf', 'index', 'test', 'bank', 'pension', 'pensions', 'obligation', 'obligations', 
                       'donation', 'indices', 'apple', 'blackrock', 'morningstar', 'usufruit', 'rallye'}
    
    for kw in keywords:
        kw_lower = kw.lower().strip()
        
        # Mots ambigus ou noms propres/marques -> garder
        if kw_lower in ambiguous_words:
            keywords_ok.append(kw)
            continue
            
        try:
            detected = detect(kw)
            # Accepter la langue cible + anglais (souvent utilisé dans le business)
            if detected == target_lang_code or detected == 'en':
                keywords_ok.append(kw)
            else:
                keywords_wrong_lang.append((kw, detected))
        except:
            # En cas d'erreur de détection (mot trop court), garder le keyword
            keywords_ok.append(kw)
    
    return keywords_ok, keywords_wrong_lang

def analyze_site_context(site_domain, jina_key=None):
    """Analyse le site client avec Jina pour extraire le contexte business"""
    site_url = f"https://www.{site_domain.replace('www.', '')}"
    content = fetch_page_with_jina(site_url, jina_key)
    
    if not content:
        # Essayer sans www
        site_url = f"https://{site_domain.replace('www.', '')}"
        content = fetch_page_with_jina(site_url, jina_key)
    
    return content

def extract_business_context(site_content, site_domain, claude_api_key, kickoff_content=None):
    """Utilise Claude pour extraire un résumé structuré du business à partir du contenu scrapé et du kickoff"""
    try:
        client = anthropic.Anthropic(api_key=claude_api_key)
        
        # Section kickoff si disponible
        kickoff_section = ""
        if kickoff_content:
            kickoff_section = f"""
DOCUMENT DE KICKOFF (objectifs business du client):
{kickoff_content[:4000]}

Ce document contient les objectifs stratégiques du client. Utilise-le pour comprendre:
- Les priorités business
- Les thèmes à cibler en priorité
- Ce qui est hors-scope
"""
        
        prompt = f"""Analyse ces informations et extrais le contexte business pour le SEO.

{kickoff_section}

CONTENU DU SITE {site_domain}:
{site_content[:5000] if site_content else "Non disponible"}

Réponds UNIQUEMENT avec ce JSON (pas de texte avant/après):
{{
    "business_type": "description courte du type de business (ex: 'gestion de patrimoine', 'e-commerce mode', 'SaaS B2B')",
    "main_products_services": ["liste des produits/services principaux"],
    "target_audience": "description de la cible",
    "business_objectives": ["objectifs business extraits du kickoff si disponible"],
    "relevant_themes": ["liste de 10-15 thèmes SEO pertinents pour ce business"],
    "irrelevant_themes": ["liste de thèmes qui seraient hors-sujet"],
    "competitor_type": "type de concurrents à exclure (ex: 'banques traditionnelles', 'grandes surfaces')"
}}"""

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        match = re.search(r'\{[\s\S]*\}', response.content[0].text)
        if match:
            return json.loads(match.group())
        return None
    except Exception as e:
        st.error(f"Erreur extraction contexte: {e}")
        return None

def filter_with_claude_v2(keywords, site_domain, language_code, claude_api_key, competitors_list=None, business_context=None, site_content=None):
    """Filtre les keywords avec le contexte business structuré - version améliorée"""
    try:
        client = anthropic.Anthropic(api_key=claude_api_key)
        kw_list = keywords[:500]
        
        # Construire la liste des marques à exclure
        competitor_brands = []
        if competitors_list:
            for comp in competitors_list:
                brand = comp.replace('.be', '').replace('.nl', '').replace('.com', '').replace('.fr', '').replace('www.', '')
                if brand:
                    competitor_brands.append(brand)
        
        # Langue cible
        lang_name = "néerlandais" if language_code == "nl" else "français"
        other_lang = "français" if language_code == "nl" else "néerlandais"
        
        # Construire le contexte business
        context_section = ""
        if business_context:
            objectives = business_context.get('business_objectives', [])
            objectives_str = ', '.join(objectives[:5]) if objectives else 'Non définis'
            
            context_section = f"""
CONTEXTE BUSINESS EXTRAIT DU SITE ET DU KICKOFF:
- Type de business: {business_context.get('business_type', 'N/A')}
- Produits/Services: {', '.join(business_context.get('main_products_services', [])[:10])}
- Cible: {business_context.get('target_audience', 'N/A')}
- 🎯 OBJECTIFS BUSINESS: {objectives_str}
- Thèmes pertinents: {', '.join(business_context.get('relevant_themes', [])[:15])}
- Thèmes hors-sujet: {', '.join(business_context.get('irrelevant_themes', [])[:10])}
- Type de concurrents: {business_context.get('competitor_type', 'N/A')}

IMPORTANT: Les objectifs business sont prioritaires. Garde tous les keywords qui peuvent contribuer à ces objectifs.
"""
        elif site_content:
            context_section = f"""
CONTENU DU SITE (extrait):
{site_content[:3000]}
"""
        
        prompt = f"""Tu es un expert SEO. Filtre cette liste de keywords pour {site_domain}.

{context_section}

LANGUE CIBLE: {lang_name} ({language_code})

KEYWORDS À ANALYSER ({len(kw_list)}):
{json.dumps(kw_list, ensure_ascii=False)}

MARQUES CONCURRENTES À EXCLURE:
{json.dumps(competitor_brands, ensure_ascii=False)}

RÈGLES - EXCLURE UNIQUEMENT:
1. Keywords contenant une marque concurrente listée ci-dessus
2. Keywords TOTALEMENT hors-sujet par rapport au business (utilise le contexte ci-dessus)

NOTE: Ne filtre PAS par langue - c'est géré séparément par un outil de détection automatique.

RÈGLES - GARDER (TRÈS IMPORTANT):
1. TOUS les keywords liés de près ou de loin au business
2. Keywords transactionnels et informationnels
3. Keywords ambigus ou dont tu n'es pas sûr → GARDE-LES
4. Keywords en anglais si pertinents pour le business

⚠️ SOIS EXTRÊMEMENT CONSERVATEUR. Garde 90%+ des keywords.
En cas de doute, GARDE TOUJOURS le keyword.

JSON uniquement:
{{"relevant": ["kw1", "kw2", ...], "filtered_out": {{"competitor_brands": [...], "off_topic": [...]}}}}"""

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

def filter_with_claude(keywords, site_domain, language_code, claude_api_key, competitors_list=None, site_context=None):
    """Filtre les keywords non pertinents via Claude - version legacy"""
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
    
    st.divider()
    st.markdown("### 📄 Document Kickoff")
    st.caption("Upload ton document de kickoff pour un filtrage plus précis")
    
    kickoff_file = st.file_uploader("Document kickoff", type=['txt', 'pdf', 'docx', 'md'], key="kickoff_upload")
    kickoff_text = st.text_area("Ou colle les objectifs business ici", height=100, key="kickoff_text", 
                                 placeholder="Ex: Objectif: augmenter les leads pour les services de gestion de patrimoine...")
    
    # Stocker le contenu du kickoff
    if kickoff_file:
        try:
            if kickoff_file.name.endswith('.txt') or kickoff_file.name.endswith('.md'):
                st.session_state.kickoff_content = kickoff_file.read().decode('utf-8')
            elif kickoff_file.name.endswith('.pdf'):
                # Pour PDF, on lit le texte brut (simplifié)
                st.session_state.kickoff_content = kickoff_file.read().decode('utf-8', errors='ignore')
            else:
                st.session_state.kickoff_content = kickoff_file.read().decode('utf-8', errors='ignore')
            st.success(f"✅ Kickoff chargé ({len(st.session_state.kickoff_content)} caractères)")
        except Exception as e:
            st.error(f"Erreur lecture: {e}")
    elif kickoff_text:
        st.session_state.kickoff_content = kickoff_text
    
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

# =============================================================================
# WORKFLOW PRINCIPAL
# =============================================================================
st.markdown("""
### Analyse de mots-cles
Suivez les etapes dans l'ordre pour une recherche de mots-cles exhaustive.
""")

# ----- CHARGER FICHIER EXISTANT (optionnel) -----
with st.expander("**Charger une analyse existante (optionnel)**"):
    st.markdown("""
    Si vous avez deja effectue une analyse precedente, vous pouvez charger le fichier Excel 
    pour continuer le travail. Sinon, passez directement a l'etape 1.
    """)
    
    col1, col2 = st.columns([3, 1])
    with col1:
        uploaded = st.file_uploader("Charger fichier Excel", type=['xlsx'], key="upload_existing")
        if uploaded:
            df_loaded = pd.read_excel(uploaded)
            df_loaded.columns = df_loaded.columns.str.strip()
            if 'Keyword' in df_loaded.columns:
                df_loaded = df_loaded.rename(columns={'Keyword': 'keyword'})
            st.session_state.df_master = df_loaded
            st.success(f"{len(df_loaded)} mots-cles charges")
            
            stats_col1, stats_col2, stats_col3 = st.columns(3)
            with stats_col1:
                st.metric("Mots-cles", len(df_loaded))
            with stats_col2:
                if 'volume' in df_loaded.columns:
                    st.metric("Volume total", f"{df_loaded['volume'].sum():,.0f}")
            with stats_col3:
                if 'category' in df_loaded.columns:
                    cats = df_loaded['category'].nunique()
                    st.metric("Categories", cats)
    
    with col2:
        if st.button("Reinitialiser", use_container_width=True):
            st.session_state.df_master = pd.DataFrame()
            st.success("Liste videe")


# ----- ÉTAPE 1 : CONTEXTE BUSINESS -----
with st.expander("**Etape 1 - Contexte business**", expanded=True):
    st.markdown("""
    Cette etape permet de definir le contexte strategique de l'analyse. 
    Le systeme scrape le site client pour comprendre son activite, et utilise 
    le document de kickoff (si fourni) pour identifier les objectifs business 
    et les thematiques prioritaires. Ce contexte sera utilise pour generer 
    des thematiques pertinentes et filtrer les mots-cles non pertinents.
    """)
    
    # Afficher si kickoff est chargé
    if 'kickoff_content' in st.session_state and st.session_state.kickoff_content:
        st.success(f"Document kickoff charge ({len(st.session_state.kickoff_content)} caracteres)")
    else:
        st.caption("Vous pouvez ajouter un document kickoff dans la barre laterale pour ameliorer la pertinence de l'analyse.")
    
    if st.button("Analyser le contexte business", key="btn_context", use_container_width=True):
        progress = st.progress(0, text="Scraping du site client...")
        
        # Scraper le site
        site_content = analyze_site_context(st.session_state.site)
        st.session_state.site_content_raw = site_content
        
        if not site_content and not st.session_state.get('kickoff_content'):
            progress.empty()
            st.error("Impossible de scraper le site et pas de kickoff fourni")
        else:
            progress.progress(50, text="Extraction du contexte business...")
            
            kickoff = st.session_state.get('kickoff_content', None)
            business_context = extract_business_context(
                site_content,
                st.session_state.site,
                st.session_state.claude_api_key,
                kickoff
            )
            st.session_state.business_context = business_context
            
            progress.progress(100, text="Termine")
            progress.empty()
            
            if business_context:
                st.success("Contexte business extrait" + (" (avec kickoff)" if kickoff else ""))
            else:
                st.warning("Contexte non extrait")
    
    # Afficher le contexte si disponible
    if 'business_context' in st.session_state and st.session_state.business_context:
        ctx = st.session_state.business_context
        with st.expander("Contexte business extrait", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Type de business:** {ctx.get('business_type', 'N/A')}")
                st.markdown(f"**Cible:** {ctx.get('target_audience', 'N/A')}")
                st.markdown("**Produits/Services:**")
                for item in ctx.get('main_products_services', [])[:5]:
                    st.caption(f"- {item}")
                if ctx.get('business_objectives'):
                    st.markdown("**Objectifs business:**")
                    for obj in ctx.get('business_objectives', [])[:5]:
                        st.caption(f"- {obj}")
            with col2:
                st.markdown("**Thematiques pertinentes:**")
                for theme in ctx.get('relevant_themes', [])[:8]:
                    st.caption(f"+ {theme}")
                st.markdown("**Thematiques hors-sujet:**")
                for theme in ctx.get('irrelevant_themes', [])[:5]:
                    st.caption(f"- {theme}")
    
    if 'site_content_raw' in st.session_state and st.session_state.site_content_raw:
        with st.expander("Contenu brut scrape"):
            st.text(st.session_state.site_content_raw[:3000] + "...")

# ----- ÉTAPE 2 : EXTRACTION SITE -----
with st.expander("**Etape 2 - Extraction site client**"):
    st.markdown("""
    Cette etape recupere les mots-cles sur lesquels le site client est deja 
    positionne dans Google. Ces donnees proviennent de l'API DataForSEO Labs 
    qui analyse l'index Google. C'est la base de l'analyse car elle montre 
    les positions actuelles du site.
    """)
    
    col1, col2 = st.columns([2, 1])
    with col1:
        extract_site_limit = st.number_input("Nombre de mots-cles a extraire", value=100, min_value=10, max_value=1000, key="extract_site",
                                              help="Plus ce nombre est eleve, plus vous aurez de donnees mais plus le cout sera important.")
    with col2:
        st.metric("Cout estime", f"~{extract_site_limit * 0.002:.2f} EUR")
    
    if st.button("Extraire du site client", key="btn_extract_site", use_container_width=True):
        progress = st.progress(0, text="Connexion a DataForSEO...")
        progress.progress(30, text=f"Extraction {st.session_state.site}...")
        
        kws = extract_keywords_from_site(
            st.session_state.site,
            st.session_state.dataforseo_login,
            st.session_state.dataforseo_password,
            st.session_state.location_code,
            st.session_state.language_code,
            extract_site_limit
        )
        progress.progress(100, text="Termine")
        time.sleep(0.5)
        progress.empty()
        
        if kws:
            new_df = pd.DataFrame({'keyword': kws, 'source': 'client_site'})
            st.session_state.df_master = pd.concat([st.session_state.df_master, new_df]).drop_duplicates(subset='keyword')
            st.success(f"{len(kws)} mots-cles extraits | Total: {len(st.session_state.df_master)}")
            
            st.markdown("**Apercu (10 premiers):**")
            st.dataframe(pd.DataFrame({'keyword': kws[:10]}), use_container_width=True, hide_index=True)
        else:
            st.warning("Aucun mot-cle trouve pour ce domaine")

# ----- ÉTAPE 3 : EXTRACTION CONCURRENTS -----
with st.expander("**Etape 3 - Extraction concurrents**"):
    st.markdown("""
    Cette etape recupere les mots-cles sur lesquels les concurrents sont positionnes. 
    Cela permet de decouvrir des opportunites que le site client n'a pas encore exploitees 
    et d'identifier les thematiques sur lesquelles les concurrents sont actifs.
    """)
    
    col1, col2 = st.columns([2, 1])
    with col1:
        extract_comp_limit = st.number_input("Mots-cles par concurrent", value=100, min_value=10, max_value=500, key="extract_comp",
                                              help="Nombre de mots-cles a extraire pour chaque concurrent. Un nombre plus eleve donne plus de donnees mais augmente le cout.")
        competitors_to_extract = st.multiselect(
            "Concurrents a analyser",
            options=st.session_state.competitors,
            default=st.session_state.competitors
        )
    with col2:
        total_comp = len(competitors_to_extract) * extract_comp_limit
        st.metric("Mots-cles estimes", f"~{total_comp}")
        st.metric("Cout estime", f"~{total_comp * 0.002:.2f} EUR")
    
    if st.button("Extraire des concurrents", key="btn_extract_comp", use_container_width=True):
        all_kws = []
        status = st.empty()
        progress = st.progress(0)
        
        for i, comp in enumerate(competitors_to_extract):
            status.text(f"Extraction {comp}...")
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
            st.success(f"{added} nouveaux mots-cles | Total: {len(st.session_state.df_master)}")
            
            st.markdown("**Apercu par concurrent:**")
            preview_df = pd.DataFrame(all_kws)
            st.dataframe(preview_df.groupby('source').size().reset_index(name='count'), use_container_width=True, hide_index=True)
            st.dataframe(preview_df.head(10), use_container_width=True, hide_index=True)
        else:
            st.warning("Aucun mot-cle trouve")

# ----- ÉTAPE 4 : THÉMATIQUES PRINCIPALES -----
with st.expander("**Etape 4 - Thematiques principales**"):
    st.markdown("""
    Cette etape genere les thematiques principales a cibler, basees sur le contexte 
    business extrait a l'etape 1. Claude analyse le contenu du site, les objectifs 
    du kickoff, et propose des thematiques strategiques alignees avec les priorites 
    du client. Ces thematiques serviront de base pour l'expansion des mots-cles.
    """)
    
    if 'business_context' not in st.session_state:
        st.warning("Lancez d'abord l'etape 1 (Contexte business) pour generer des thematiques pertinentes.")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        claude_seeds_count = st.number_input("Nombre de thematiques a generer", value=50, min_value=10, max_value=200, key="claude_seeds",
                                              help="Nombre de mots-cles thematiques a generer. Ces mots-cles serviront de base pour l'expansion.")
    with col2:
        st.metric("Tokens estimes", f"~{claude_seeds_count * 50}")
    
    if st.button("Generer les thematiques", key="btn_claude_seeds", use_container_width=True):
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
                    
                    st.success(f"{len(seeds)} generes, {len(valid_seeds)} avec volume | {added} nouveaux ajoutes")
                    st.markdown("**Thematiques generees:**")
                    st.dataframe(pd.DataFrame({'keyword': valid_seeds[:15]}), use_container_width=True, hide_index=True)
                else:
                    st.warning("Aucune thematique avec volume suffisant")
            else:
                progress.empty()
                st.warning("Claude n'a pas genere de thematiques")

# ----- ÉTAPE 5 : EXPANSION RELATED -----
with st.expander("**Etape 5 - Expansion (mots-cles lies)**"):
    st.markdown("""
    Cette etape elargit la liste en cherchant les mots-cles lies a ceux deja collectes. 
    Le systeme selectionne les meilleurs mots-cles (par volume et par diversite thematique) 
    et interroge l'API Google Ads pour trouver des variantes et synonymes recherches par les utilisateurs.
    """)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        expansion_top_volume = st.number_input("Top mots-cles par volume", value=50, min_value=10, max_value=200, key="exp_top",
                                                help="Nombre de mots-cles a fort volume a utiliser comme base pour l'expansion.")
    with col2:
        expansion_per_cluster = st.number_input("Mots-cles par cluster", value=10, min_value=5, max_value=50, key="exp_cluster",
                                                 help="Nombre de mots-cles a prendre dans chaque groupe thematique pour assurer la diversite.")
    with col3:
        related_per_keyword = st.number_input("Lies par mot-cle", value=30, min_value=10, max_value=100, key="related_per",
                                               help="Nombre de mots-cles lies a recuperer pour chaque mot-cle de base.")
    
    total_seeds = expansion_top_volume + (15 * expansion_per_cluster)
    st.caption(f"Bases estimees: ~{total_seeds} | Lies estimes: ~{total_seeds * related_per_keyword} | Cout: ~{total_seeds * 0.005:.2f} EUR")
    
    if st.button("Lancer l'expansion", key="btn_expansion", use_container_width=True):
        if len(st.session_state.df_master) == 0:
            st.warning("Lancez d'abord l'extraction (etapes 2-4)")
        elif 'volume' not in st.session_state.df_master.columns:
            st.warning("Lancez d'abord l'etape 6 (Volumes) pour avoir les donnees de volume")
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
                st.info(f"{len(seeds)} mots-cles de base selectionnes (top {expansion_top_volume} + clusters)")
                
                # Récupérer related
                all_related = []
                progress = st.progress(0)
                status = st.empty()
                
                for i, seed in enumerate(seeds):
                    status.text(f"{i+1}/{len(seeds)} - {seed[:30]}...")
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
                    
                    st.success(f"{len(unique_related)} mots-cles lies uniques | {added} nouveaux ajoutes")
                    st.markdown("**Exemples de mots-cles lies:**")
                    st.dataframe(pd.DataFrame({'keyword': unique_related[:15]}), use_container_width=True, hide_index=True)
                else:
                    st.warning("Aucun mot-cle lie trouve")

# ----- ÉTAPE 6 : VOLUMES -----
with st.expander("**Etape 6 - Recuperer les volumes**"):
    st.markdown("""
    Cette etape recupere le volume de recherche mensuel et le CPC (cout par clic) pour chaque 
    mot-cle via l'API Google Ads. Ces donnees permettent de prioriser les mots-cles en fonction 
    de leur potentiel de trafic reel.
    """)
    
    missing_vol = 0
    if len(st.session_state.df_master) > 0 and 'volume' in st.session_state.df_master.columns:
        # Seulement les None, pas les 0 (0 = déjà vérifié, pas de volume)
        missing_vol = st.session_state.df_master['volume'].isna().sum()
    else:
        missing_vol = len(st.session_state.df_master)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Mots-cles sans volume", missing_vol)
    with col2:
        st.metric("Cout estime", f"~{missing_vol * 0.005:.2f} EUR")
    
    if st.button("Recuperer les volumes", key="btn_volumes", use_container_width=True):
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

# ----- ÉTAPE 7 : FILTRAGE -----
with st.expander("**Etape 7 - Filtrage**"):
    st.markdown("""
    Cette etape nettoie la liste en supprimant les mots-cles non pertinents: 
    volume trop faible, mauvaise langue, marques concurrentes ou hors-sujet. 
    Le filtrage par langue utilise une detection automatique pour identifier 
    les mots-cles dans la mauvaise langue.
    """)
    
    # --- FILTRAGE PAR VOLUME (principal) ---
    st.markdown("### Filtrage par volume")
    col1, col2 = st.columns(2)
    with col1:
        min_volume = st.number_input("Volume minimum", value=10, min_value=0, key="min_vol")
    with col2:
        if 'volume' in st.session_state.df_master.columns:
            to_remove = (st.session_state.df_master['volume'] < min_volume).sum()
            st.metric("A supprimer", to_remove)
    
    if st.button("Filtrer par volume", key="btn_filter_vol", use_container_width=True):
        if 'volume' in st.session_state.df_master.columns:
            before = len(st.session_state.df_master)
            removed_kws = st.session_state.df_master[st.session_state.df_master['volume'] < min_volume]['keyword'].tolist()
            st.session_state.df_master = st.session_state.df_master[
                st.session_state.df_master['volume'] >= min_volume
            ].reset_index(drop=True)
            removed = before - len(st.session_state.df_master)
            st.success(f"{removed} supprimes - Reste: {len(st.session_state.df_master)}")
            
            if removed > 0:
                st.markdown("**Exemples supprimes:**")
                st.code('\n'.join(removed_kws[:10]))
    
    st.divider()
    
    # --- ANALYSE DU CONTEXTE BUSINESS ---
    st.markdown("### Analyse du contexte business")
    st.caption("Scrape le site avec Jina et extrait le contexte business pour un filtrage intelligent")
    
    # Afficher si kickoff est chargé
    if 'kickoff_content' in st.session_state and st.session_state.kickoff_content:
        st.success(f"Document kickoff charge ({len(st.session_state.kickoff_content)} caracteres)")
    else:
        st.caption("Vous pouvez ajouter un document kickoff dans la sidebar pour ameliorer le filtrage")
    
    if st.button("Analyser le site client", key="btn_analyze_site", use_container_width=True):
        progress = st.progress(0, text="Scraping du site avec Jina...")
        
        # Scraper le site
        site_content = analyze_site_context(st.session_state.site)
        st.session_state.site_content_raw = site_content
        
        if not site_content and not st.session_state.get('kickoff_content'):
            progress.empty()
            st.error("Impossible de scraper le site et pas de kickoff")
        else:
            progress.progress(50, text="Extraction du contexte business...")
            
            # Extraire le contexte business (avec kickoff si disponible)
            kickoff = st.session_state.get('kickoff_content', None)
            business_context = extract_business_context(
                site_content,
                st.session_state.site,
                st.session_state.claude_api_key,
                kickoff
            )
            st.session_state.business_context = business_context
            
            progress.progress(100, text="Terminé!")
            progress.empty()
            
            if business_context:
                st.success("Contexte business extrait" + (" (avec kickoff)" if kickoff else ""))
            else:
                st.warning("Contexte non extrait, le filtrage utilisera le contenu brut")
    
    # Afficher le contexte si disponible
    if 'business_context' in st.session_state and st.session_state.business_context:
        ctx = st.session_state.business_context
        with st.expander("Contexte business extrait", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Type de business:** {ctx.get('business_type', 'N/A')}")
                st.markdown(f"**Cible:** {ctx.get('target_audience', 'N/A')}")
                st.markdown("**Produits/Services:**")
                for item in ctx.get('main_products_services', [])[:5]:
                    st.caption(f"- {item}")
                if ctx.get('business_objectives'):
                    st.markdown("**Objectifs business:**")
                    for obj in ctx.get('business_objectives', [])[:5]:
                        st.caption(f"- {obj}")
            with col2:
                st.markdown("**Themes pertinents:**")
                for theme in ctx.get('relevant_themes', [])[:8]:
                    st.caption(f"+ {theme}")
                st.markdown("**Themes hors-sujet:**")
                for theme in ctx.get('irrelevant_themes', [])[:5]:
                    st.caption(f"- {theme}")
    
    # Afficher le contenu brut scrapé
    if 'site_content_raw' in st.session_state and st.session_state.site_content_raw:
        with st.expander("Contenu brut scrape par Jina"):
            st.text(st.session_state.site_content_raw[:3000] + "...")
    
    st.divider()
    
    # --- FILTRAGE PAR LANGUE (programmatique) ---
    st.markdown("### Filtrage par langue")
    if LANGDETECT_AVAILABLE:
        st.caption("Detection automatique de la langue avec langdetect")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Analyser les langues", key="btn_analyze_lang", use_container_width=True):
                if len(st.session_state.df_master) == 0:
                    st.warning("Pas de mots-cles")
                else:
                    keywords = st.session_state.df_master['keyword'].tolist()
                    target_lang = st.session_state.language_code  # 'nl' ou 'fr'
                    
                    keywords_ok, keywords_wrong = filter_by_language(keywords, target_lang)
                    
                    st.session_state.lang_filter_preview = {
                        'ok': keywords_ok,
                        'wrong': keywords_wrong
                    }
                    
                    st.info(f"**Analyse**: {len(keywords_ok)} OK | {len(keywords_wrong)} mauvaise langue detectee")
                    
                    if keywords_wrong:
                        with st.expander(f"Mauvaise langue ({len(keywords_wrong)})", expanded=True):
                            for kw, detected_lang in keywords_wrong[:50]:
                                st.caption(f"- `{kw}` -> detecte: **{detected_lang}** (cible: {target_lang})")
        
        with col2:
            if st.button("Supprimer mauvaise langue", key="btn_remove_lang", use_container_width=True):
                if 'lang_filter_preview' not in st.session_state:
                    st.warning("Lancez d'abord l'analyse des langues")
                else:
                    keywords_ok = st.session_state.lang_filter_preview['ok']
                    before = len(st.session_state.df_master)
                    st.session_state.df_master = st.session_state.df_master[
                        st.session_state.df_master['keyword'].isin(keywords_ok)
                    ].reset_index(drop=True)
                    removed = before - len(st.session_state.df_master)
                    st.success(f"{removed} supprimes - Reste: {len(st.session_state.df_master)}")
                    del st.session_state.lang_filter_preview
    else:
        st.warning("langdetect non installe. Installez avec: pip install langdetect")
    
    st.divider()
    
    # --- FILTRAGE CLAUDE ---
    st.markdown("### Filtrage intelligent (marques, hors-sujet)")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Preview filtrage", key="btn_preview_claude", use_container_width=True):
            if len(st.session_state.df_master) == 0:
                st.warning("Pas de keywords")
            elif 'business_context' not in st.session_state:
                st.warning("⚠️ Analyse d'abord le site client!")
            else:
                keywords = st.session_state.df_master['keyword'].tolist()
                progress = st.progress(0, text="Filtrage par Claude...")
                
                # Utiliser le contexte business structuré
                ctx = st.session_state.business_context
                site_content = st.session_state.get('site_content_raw', '')
                
                result = filter_with_claude_v2(
                    keywords,
                    st.session_state.site,
                    st.session_state.language_code,
                    st.session_state.claude_api_key,
                    st.session_state.competitors,
                    ctx,
                    site_content
                )
                progress.progress(100, text="Terminé!")
                progress.empty()
                
                st.session_state.claude_filter_preview = result
                
                filtered_out = result.get('filtered_out', {})
                relevant = result.get('relevant', [])
                total_filtered = len(keywords) - len(relevant)
                
                st.info(f"📋 **Preview**: {total_filtered} keywords seraient supprimés sur {len(keywords)} | **{len(relevant)} gardés**")
                
                # Afficher ce qui est GARDÉ
                with st.expander(f"✅ Keywords GARDÉS ({len(relevant)})", expanded=True):
                    st.code('\n'.join(relevant[:100]))
                    if len(relevant) > 100:
                        st.caption(f"... et {len(relevant) - 100} autres")
                
                # Afficher ce qui est filtré par catégorie
                cat_labels = {
                    'competitor_brands': '🏷️ Marques concurrentes',
                    'wrong_language': '🌍 Mauvaise langue',
                    'locations': '📍 Villes/Locations',
                    'off_topic': '❌ Hors-sujet'
                }
                for cat, items in filtered_out.items():
                    if items and len(items) > 0:
                        label = cat_labels.get(cat, cat)
                        with st.expander(f"{label} ({len(items)})"):
                            st.code('\n'.join(items[:50]))
    
    with col2:
        if st.button("✅ Appliquer le filtrage", key="btn_apply_claude", use_container_width=True):
            if 'claude_filter_preview' not in st.session_state:
                st.warning("Lance d'abord le Preview!")
            else:
                result = st.session_state.claude_filter_preview
                relevant = result.get('relevant', st.session_state.df_master['keyword'].tolist())
                
                before = len(st.session_state.df_master)
                st.session_state.df_master = st.session_state.df_master[
                    st.session_state.df_master['keyword'].isin(relevant)
                ].reset_index(drop=True)
                removed = before - len(st.session_state.df_master)
                
                st.success(f"✅ {removed} filtrés — Reste: {len(st.session_state.df_master)}")
                del st.session_state.claude_filter_preview

# ----- ÉTAPE 8 : CATÉGORISATION -----
with st.expander("**Etape 8 - Categorisation**"):
    st.markdown("""
    Cette etape regroupe les mots-cles par categorie thematique. Claude analyse 
    la liste et propose des regroupements logiques pour organiser le travail 
    et creer des silos de contenu.
    """)
    
    only_uncategorized = st.checkbox("Uniquement les non-catégorisés", value=True, key="only_uncat")
    
    to_categorize = 0
    if len(st.session_state.df_master) > 0:
        if only_uncategorized and 'category' in st.session_state.df_master.columns:
            to_categorize = st.session_state.df_master['category'].isna().sum() + (st.session_state.df_master['category'] == '').sum()
        else:
            to_categorize = len(st.session_state.df_master)
    
    st.metric("Mots-cles a categoriser", to_categorize)
    
    if st.button("Categoriser avec Claude", key="btn_categorize", use_container_width=True):
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
                st.success("Tous les mots-cles sont deja categorises")
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
                    st.success(f"{categorized}/{len(st.session_state.df_master)} categorises")
                    
                    st.markdown("**Categories:**")
                    for cat, kws in categories.items():
                        st.caption(f"**{cat}**: {len(kws)} mots-cles")
                else:
                    st.warning("Erreur de categorisation")

# ----- ÉTAPE 9 : SERP + AI OVERVIEW -----
with st.expander("**Etape 9 - Analyse SERP et AI Overview**"):
    st.markdown("""
    Cette etape analyse les resultats de recherche Google pour chaque mot-cle. 
    Elle recupere la position du site client et des concurrents dans les 100 premiers 
    resultats, et detecte la presence d'AI Overview. Cela permet d'identifier les 
    opportunites de positionnement et les mots-cles ou l'IA de Google est presente.
    """)
    
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
        st.metric("Cout estime", f"~{actual_count * 0.0075:.2f} EUR")
        st.caption(f"Duree estimee: ~{actual_count * 1.5 / 60:.0f} min")
    
    if st.button("Analyser SERP", key="btn_serp", use_container_width=True):
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
                status.text(f"{i+1}/{len(keywords)} - {kw[:40]}...")
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
            
            st.success(f"SERP termine - Client ranke: {client_ranked}/{len(keywords)} | AI Overview: {ai_count}")
            
            # Aperçu résultats
            st.markdown("**Apercu positions:**")
            cols_to_show = ['keyword', 'client_pos'] + [f'{c}_pos' for c in st.session_state.competitors if f'{c}_pos' in df_serp.columns]
            st.dataframe(df_serp[cols_to_show].head(10), use_container_width=True, hide_index=True)
            
            # Stats concurrents
            st.markdown("**Resume positions:**")
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
    <h3 style="margin: 0; color: #3A3A3A;">Etat actuel</h3>
</div>
""", unsafe_allow_html=True)

if len(st.session_state.df_master) > 0:
    show_stats_cards(st.session_state.df_master)
    
    st.dataframe(st.session_state.df_master.head(20), use_container_width=True, hide_index=True)
    
    # Export
    st.subheader("Export")
    buffer = BytesIO()
    st.session_state.df_master.to_excel(buffer, index=False)
    st.download_button(
        "Telecharger Excel",
        data=buffer.getvalue(),
        file_name=f"Keywords_{st.session_state.site.replace('.', '_')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.info("Aucun mot-cle - lancez l'extraction pour commencer")
