# 🔍 Keyword Research App

Application Streamlit pour l'analyse sémantique guidée.

## Installation

```bash
cd keyword_research_app
pip install -r requirements.txt
```

## Lancement

```bash
streamlit run app.py
```

## Workflows

### 🟢 Analyse 1 — Nouvelle recherche
1. Configure le site client, langue, concurrents dans la sidebar
2. Sauvegarde la config
3. Extrait les keywords du site client
4. Extrait les keywords des concurrents
5. Récupère les volumes
6. Filtre par volume minimum
7. Analyse SERP (positions + AI Overview)
8. Exporte en Excel

### 🔄 Analyse 2 — Complément
1. Charge un fichier Excel existant
2. Ajoute des keywords manuellement ou via extraction
3. Récupère volumes/SERP uniquement pour les nouveaux
4. Exporte le fichier mis à jour

## APIs requises

- **DataForSEO** : volumes, extraction, SERP
- **Claude** (optionnel) : filtrage intelligent, catégorisation
