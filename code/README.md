# Code

Prototype d'implémentation, à partir des fichiers de `donnees/`. Python 3.10 ou plus. 
pour `methode/agents.py`, les dépendances (requirements.txt) doivent être installées.

## Méthode

| Fichier | Lancement | Résultat attendu |
|---|---|---|
| `methode/contexte.py` | `python code/methode/contexte.py` | les cinq contextes ; itération 1 : 79 objets, 1 244 attributs, 3 679 incidences |
| `methode/fermetures.py` | `python code/methode/fermetures.py` | itération 1 : 14 691 concepts formels, dont 14 525 d'au moins 2 objets et 2 attributs, 102 lexicalisés, 14 423 émergents ; de même pour les itérations 2 à 5 |
| `methode/selection.py` | `python code/methode/selection.py [itération]` | les 100 CFs émergents de plus forte valeur de κ |
| `methode/agents.py` | `python code/methode/agents.py sortie_agents.json` | les termes retenus et les conversations des quatre agents |

`agents.py` demande `pip install -r code/requirements.txt` et une clé dans `GOOGLE_API_KEY`. Les prompts sont ceux de `donnees/methode_llm/echanges_agents_iteration_1.json`. 
Les réponses d'un LLM variant d'un appel à l'autre, les résultats ne sont pas reproductibles. Les réponses obtenues lors de l'expérience sont dans `donnees/methode_llm/`.

## Expérimentation

| Fichier | Lancement | Résultat |
|---|---|---|
| `experimentation/accord.py` | `python code/experimentation/accord.py` | kappa de Fleiss : 0,22 (nommage), 0,05 (pertinence) |
| `experimentation/figures.js` | affiché par `index.html` | figures 2, 3 et 4 |
