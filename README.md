# Curage neuro-symbolique d’un réseau lexico-sémantique

Sorties de l'expérience décrite dans l'article, à partir du terme initial « plat asiatique ». Chaque donnée est dans `donnees/`.

Ouvrir dans un navigateur, sans serveur ni connexion : `index.html` (données), `code.html` (implémentation : un onglet par fichier, avec lancement, résultat attendu et code).

## Dossiers

| Dossier | Contenu |
|---|---|
| `donnees/parametres_experience.json` | terme initial, modèle, taille des lots, règle de rétention, effectifs par itération |
| `donnees/sous_graphe_jdm/` | les 4 018 relations lues dans JDM pour les 79 objets, et le devenir de chacune au pré-traitement |
| `donnees/contexte_formel/` | les cinq contextes formels, un par itération : objets, attributs, incidences et leur provenance, incidences disparues d'une itération à la suivante |
| `donnees/methode_fca/` | pour chaque itération : comptes des concepts formels, CFs lexicalisés, tous les CFs émergents avec leur κ et les 100 CFs soumis aux agents |
| `donnees/methode_llm/` | échanges de chaque agent à chaque itération (prompts, réponses, relances), contrôle et décisions de rétention par CF, recurage des termes rendus obsolètes après la dernière itération, prompt du juge final |
| `donnees/resultats/` | les 349 termes retenus, avec la note du juge à leur itération et la note du juge final |
| `donnees/evaluation/` | la fiche d'annotation anonymisée (jugements humains) et les précisions. |
| `code/` | implémentation prototype d'implémentation: `methode/` (section 4) et `experimentation/` (section 5), voir `code/LISEZMOI.md` |
| `page/` | copie assemblée des données et du code, lue par `index.html` et `code.html`.|

## Lecture des décisions

À chaque itération, le Juge note la version originale de chaque CF et ses versions amendées. La version la mieux notée est retenue si sa note est strictement supérieure à 0,5. Un CF peut aussi être fusionné avec un autre terme retenu ou rattaché à un terme existant de la ressource. Les termes retenus entrent dans le contexte de l'itération suivante comme objets et comme attributs `r_isa`.

## Évaluation humaine

Chaque terme est jugé par un annotateur, sauf un bloc commun de 40 termes jugés par les quatre. Pour ce bloc, le verdict retenu est celui de la majorité, et les égalités sont exclues du calcul de la précision.
