# Documentation - Keyword Research Tool

## Vue d'ensemble

Cet outil permet de realiser une recherche de mots-cles SEO complete, structuree autour du document de kickoff client. Chaque etape construit progressivement une liste de mots-cles pertinents, categorises et alignes avec les objectifs business.

---

## Etape 0 - Charger une analyse existante (optionnel)

Cette etape permet de reprendre une analyse precedente. Si vous avez deja exporte un fichier Excel lors d'une session anterieure, vous pouvez le recharger ici pour continuer le travail sans repartir de zero. Le systeme detecte automatiquement les colonnes presentes (mots-cles, volumes, categories) et restaure l'etat de l'analyse.

**Quand l'utiliser:** Lorsque vous souhaitez completer une analyse existante, ajouter de nouvelles categories, ou relancer certaines etapes sur une base deja travaillee.

---

## Etape 1 - Contexte business

Cette etape est fondamentale car elle definit le cadre de toute l'analyse. Vous devez fournir deux elements:

**Le document de kickoff:** Il s'agit du brief client contenant les objectifs business, la cible, les produits/services, et les priorites strategiques. Ce document sera analyse par Claude pour extraire les themes pertinents et comprendre ce qui est dans le scope ou hors scope de l'analyse.

**Le crawl du site:** L'outil utilise Jina pour recuperer le contenu de la page d'accueil du site client. Ce contenu permet de comprendre le vocabulaire utilise, les services mis en avant, et le positionnement actuel du site.

**Resultat:** Un contexte business structure comprenant le type de business, la cible, les produits/services, les objectifs, et les themes pertinents. Ce contexte sera utilise pour generer des categories alignees avec le kickoff.

---

## Etape 2 - Extraction site client

Cette etape recupere les mots-cles sur lesquels le site client est deja positionne dans Google. L'API DataForSEO interroge la base de donnees de positionnement et retourne les mots-cles ou le site apparait dans les resultats de recherche.

**Utilite:** Identifier les mots-cles existants permet de ne pas les oublier dans l'analyse et de comprendre le positionnement actuel. Ces mots-cles peuvent aussi reveler des opportunites d'amelioration (positions 5-20 a pousser en top 3).

**Parametres:** Vous pouvez definir le nombre maximum de mots-cles a extraire. Les mots-cles sont tries par volume de recherche decroissant.

---

## Etape 3 - Extraction concurrents

Cette etape fonctionne comme l'etape 2, mais pour les sites concurrents definis dans la sidebar. Pour chaque concurrent, l'outil recupere les mots-cles sur lesquels il est positionne.

**Utilite:** Decouvrir des mots-cles que les concurrents ciblent mais que le client n'a pas encore adresses. Cela permet d'identifier des opportunites et des gaps dans la strategie de contenu actuelle.

**Attention:** Les mots-cles des concurrents ne sont pas tous pertinents pour le client. Ils seront filtres par langue et pourront etre tries manuellement apres export.

---

## Etape 4 - Categories

Cette etape est centrale dans le workflow. Claude analyse le document de kickoff et le contexte business pour generer des categories de mots-cles. Ces categories sont des themes generiques (1-3 mots) qui representent les differents aspects du business.

**Exemples de categories pour un gestionnaire de patrimoine:** "ETF investissement", "gestion patrimoine", "epargne pension", "frais courtage", "profil risque".

**Selection manuelle:** Apres generation, vous voyez la liste complete des categories avec leur volume de recherche. Vous pouvez deselectionner les categories non pertinentes avant de valider. Seules les categories validees seront utilisees pour l'expansion.

**Pourquoi c'est important:** Les categories definissent la structure de votre analyse. Chaque mot-cle trouve lors de l'expansion sera tague avec sa categorie d'origine, ce qui facilite le tri et l'analyse dans Excel.

---

## Etape 5 - Expansion par categorie

Pour chaque categorie validee a l'etape 4, l'outil interroge l'API Google Ads pour trouver les mots-cles lies. L'API retourne des mots-cles que les utilisateurs recherchent reellement et qui sont semantiquement proches de la categorie.

**Fonctionnement:** La categorie "ETF investissement" peut generer des mots-cles comme "investir en ETF", "meilleur ETF 2024", "ETF ou actions", "comment acheter des ETF", etc.

**Tag automatique:** Chaque mot-cle trouve est automatiquement tague avec sa categorie d'origine. Cela permet de savoir d'ou vient chaque mot-cle et de filtrer par theme dans Excel.

**Filtre volume:** Seuls les mots-cles avec un volume de recherche minimum (10 par defaut) sont conserves pour eviter de polluer la liste avec des termes jamais recherches.

**Lien avec le kickoff:** L'expansion est liee au kickoff indirectement via les categories. Les categories sont generees a partir du kickoff, donc les mots-cles expandus restent dans le perimetre defini. Cependant, l'API Google Ads peut retourner des mots-cles tangentiels qui necessitent un tri manuel.

---

## Etape 6 - Recuperer les volumes

Cette etape complete les donnees de volume pour tous les mots-cles qui n'en ont pas encore. L'API Google Ads retourne le volume de recherche mensuel moyen et le CPC (cout par clic) pour chaque mot-cle.

**Utilite:** Le volume permet de prioriser les mots-cles. Un mot-cle avec 10 000 recherches mensuelles a plus de potentiel qu'un mot-cle avec 50 recherches. Le CPC donne une indication de la valeur commerciale du mot-cle.

**Traitement par batch:** Pour les grandes listes, les mots-cles sont traites par lots de 700 pour respecter les limites de l'API.

---

## Etape 7 - Filtrage

Cette etape nettoie la liste en supprimant les mots-cles non pertinents selon deux criteres:

**Filtrage par volume:** Supprime les mots-cles dont le volume est inferieur au seuil defini. Cela permet d'eliminer les termes trop niches ou les erreurs de frappe.

**Filtrage par langue:** Utilise la librairie langdetect pour identifier la langue de chaque mot-cle. Les mots-cles dans la mauvaise langue (ex: neerlandais quand on cible le francais) sont signales et peuvent etre supprimes. Les mots ambigus (termes techniques, marques) sont conserves.

**Pas de filtrage semantique automatique:** Le filtrage par pertinence thematique n'est pas automatise car il est difficile a faire de maniere fiable. Vous gardez le controle total sur ce qui est pertinent ou non via le tri manuel dans Excel.

---

## Etape 8 - Categorisation

Si des mots-cles n'ont pas encore de categorie (ceux venant des etapes 2 et 3), cette etape permet de les categoriser automatiquement via Claude. Le systeme analyse chaque mot-cle et l'assigne a une categorie existante ou en cree une nouvelle.

**Note:** Les mots-cles issus de l'expansion (etape 5) ont deja une categorie. Cette etape concerne principalement les mots-cles extraits du site client et des concurrents.

---

## Etape 9 - SERP et AI Overview

Cette etape analyse les resultats de recherche Google pour les mots-cles selectionnes. Pour chaque mot-cle, l'outil verifie:

**Position du client:** Ou se situe le site client dans les resultats organiques.

**Positions des concurrents:** Ou se situent les concurrents definis.

**Presence AI Overview:** Si Google affiche une reponse IA pour ce mot-cle, et si le client est cite dans cette reponse.

**Utilite:** Identifier les opportunites (mots-cles ou le client n'est pas present mais les concurrents oui) et les menaces (mots-cles avec AI Overview qui peuvent reduire le CTR).

---

## Export

L'export genere un fichier Excel contenant tous les mots-cles avec leurs donnees:
- Mot-cle
- Volume de recherche
- CPC
- Categorie
- Source (site client, concurrent, expansion)
- Position client (si analysee)
- Presence AI Overview (si analysee)

**Conseil:** Utilisez les filtres Excel sur la colonne "categorie" pour analyser theme par theme et identifier les priorites.

---

## Bonnes pratiques

1. **Commencez toujours par l'etape 1** avec un kickoff bien redige. La qualite de l'analyse depend de la qualite du brief initial.

2. **Selectionnez soigneusement les categories** a l'etape 4. Moins de categories mais plus pertinentes vaut mieux que beaucoup de categories generiques.

3. **Le tri final se fait dans Excel.** L'outil collecte et structure les donnees, mais c'est vous qui connaissez le client et pouvez juger de la pertinence finale.

4. **Sauvegardez regulierement** en exportant votre fichier Excel. Vous pourrez le recharger a l'etape 0 pour continuer plus tard.
