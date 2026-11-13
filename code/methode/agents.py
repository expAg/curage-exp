"""Prototype de la couche neuronale et de la couche de contrôle : quatre agents LLM orchestrés avec LangChain
sur les CFs sélectionnés par κ, puis rétention.

    pip install -r code/requirements.txt
    export GOOGLE_API_KEY=...
    python code/methode/agents.py sortie_agents.json

Les consignes sont celles envoyées aux agents à l'itération 1 (donnees/methode_llm/echanges_agents_iteration_1.json).
"""
import json
import os
import re
import sys

from langchain_core.messages import AIMessage, HumanMessage

from contexte import DONNEES, charger
from fermetures import Contexte, classer, indices
from selection import selectionner

MODELE = 'gemini-3.5-flash-lite'
LOT = 100                 # versions par appel
RELANCES = 2
SEUIL_RETENTION = 0.5
FORMAT = ('Réponds par un objet JSON {"concepts": [...]}, une entrée par concept (ou par version), '
          'repérée par son numéro dans « index ».')
SUITE = 'Voici la suite des concepts, du n° {a} au n° {b}. Mêmes consignes, même forme de réponse.'
REANNOTATION = ('Certains de ces concepts ont été modifiés. Voici leurs nouvelles versions : '
                'réannote-les, mêmes consignes, même forme de réponse.')
INTENSION = ("Intension propre, les attributs communs à tous ces objets que le réseau ne déclare ni sur le terme initial "
             "ni sur ses genres, donc ceux qui distinguent ce groupe, une paire relation:valeur par ligne :")


def consignes():
    fil = json.load(open(os.path.join(DONNEES, 'methode_llm', 'echanges_agents_iteration_1.json'), encoding='utf-8'))['agents']
    out = {}
    for agent, appels in fil.items():
        p = appels[0]['prompt']
        p = p[:p.find('\nAnnexe')] if '\nAnnexe' in p else p
        out[agent] = p.replace('{{documentation jdm}}', appels[0].get('documentation_relations') or '').strip()
    return out


def adapter(texte, nb):
    texte = re.sub(r'Ils sont \d+, numérotés de 1 à \d+', f'Ils sont {nb}, numérotés de 1 à {nb}', texte)
    return re.sub(r'du n° 1 au n° \d+', f'du n° 1 au n° {nb}', texte)


def bloc(titre, v):
    return f'{titre}\nExtension, les objets :\n' + '\n'.join('- ' + o for o in v['X']) \
        + f'\n{INTENSION}\n' + '\n'.join('- ' + a for a in v['Y'])


def annexe(versions, de=1):
    a = de + len(versions) - 1
    return f'Annexe — les {len(versions)} concepts, du n° {de} au n° {a}.\n\n' + \
        '\n\n'.join(bloc(f'Concept {i}', v) for i, v in enumerate(versions, de))


def lire(texte):
    m = re.search(r'\{.*\}', texte, re.S)
    try:
        return {str(e.get('index')): e for e in json.loads(m.group(0)).get('concepts', [])}
    except Exception:
        return {}


def converser(llm, fil, message, attendus):
    """Un appel dans la conversation de l'agent, puis des relances pour les entrées manquantes."""
    fil.append(HumanMessage(message))
    fil.append(AIMessage(llm.invoke(fil).content))
    lus = lire(fil[-1].content)
    for _ in range(RELANCES):
        manque = [k for k in attendus if k not in lus]
        if not manque:
            break
        fil.append(HumanMessage('Rends au même format, et eux seuls, les concepts n° ' + ', '.join(manque) + '.'))
        fil.append(AIMessage(llm.invoke(fil).content))
        lus.update(lire(fil[-1].content))
    return lus


def amender(v, variante):
    x, y = list(v['X']), list(v['Y'])
    for op in variante.get('operations', []):
        cible = x if op.get('cible') == 'objet' else y
        if op.get('action') == 'ajouter' and op.get('valeur') not in cible:
            cible.append(op.get('valeur'))
        elif op.get('action') == 'supprimer' and op.get('valeur') in cible:
            cible.remove(op.get('valeur'))
    return {'X': x, 'Y': y, 'amende': True}


def curer(llm, cfs, sur_classe):
    """cfs : [{'X': [objets], 'Y': [attributs]}]. Rend les termes retenus et les conversations."""
    C = consignes()
    fils = {a: [] for a in C}
    nb, tous = len(cfs), [str(i) for i in range(1, len(cfs) + 1)]

    # annotateur : l'intension complète
    ann = converser(llm, fils['annotateur'], adapter(C['annotateur'], nb) + '\n\n' + FORMAT + '\n\n' + annexe(cfs), tous)
    # les autres agents : l'intension propre, plus les traits déclarés sur les classes jugés constitutifs
    vues = []
    for i, cf in enumerate(cfs, 1):
        statut = {a.get('attribut'): a.get('statut') for a in ann.get(str(i), {}).get('attributs', [])}
        vues.append({'X': cf['X'], 'Y': [a for a in cf['Y'] if not sur_classe[a] or statut.get(a) == 'constitutif'],
                     'amende': False})

    amd = converser(llm, fils['amendeur'], adapter(C['amendeur'], nb) + '\n\n' + FORMAT + '\n\n' + annexe(vues), tous)
    versions = [[v] + [amender(v, var) for var in amd.get(str(i), {}).get('variantes', []) if var.get('operations')]
                for i, v in enumerate(vues, 1)]

    modifiees = [(i, v) for i, vs in enumerate(versions, 1) for v in vs[1:]]
    if modifiees:
        converser(llm, fils['annotateur'], REANNOTATION + '\n\n' + '\n\n'.join(bloc(f'Concept {i}', v) for i, v in modifiees),
                  [str(i) for i, _ in modifiees])

    # juge : toutes les versions d'un CF dans le même appel, au plus LOT versions par appel
    notes, lot, premier = {}, [], True
    for i, vs in enumerate(versions, 1):
        lot.append((i, vs))
        suivant = versions[i] if i < nb else None
        if suivant is None or sum(len(v) for _, v in lot) + len(suivant) > LOT:
            texte = '\n\n'.join(f'Concept {j}, en {len(v)} versions :\n\n' + '\n\n'.join(
                bloc(f'Version {n}', w) for n, w in enumerate(v, 1)) for j, v in lot)
            tete = adapter(C['juge'], len(lot)) if premier else SUITE.format(a=lot[0][0], b=lot[-1][0])
            notes.update(converser(llm, fils['juge'], tete + '\n\n' + FORMAT + '\n\n' + texte,
                                   [f'{j}.{n}' for j, v in lot for n in range(1, len(v) + 1)]))
            lot, premier = [], False

    meilleures = []
    for i, vs in enumerate(versions, 1):
        note, n = max((notes.get(f'{i}.{n}', {}).get('score', 0), n) for n in range(1, len(vs) + 1))
        meilleures.append((vs[n - 1], note))

    noms = converser(llm, fils['nommeur'], adapter(C['nommeur'], nb) + '\n\n' + FORMAT + '\n\n'
                     + annexe([v for v, _ in meilleures]), tous)

    # rétention : la meilleure version, si sa note dépasse le seuil et qu'elle a un nom
    retenus = []
    for i, (v, note) in enumerate(meilleures, 1):
        proposes = sorted(noms.get(str(i), {}).get('noms', []), key=lambda p: -p.get('score', 0))
        if note > SEUIL_RETENTION and proposes:
            retenus.append({'cf': i, 'nom': proposes[0]['nom'], 'note_du_juge': note, **v})
    conversations = {a: [{'role': 'envoyé' if isinstance(m, HumanMessage) else 'réponse', 'texte': m.content} for m in f]
                     for a, f in fils.items()}
    return retenus, conversations


if __name__ == '__main__':
    from langchain_google_genai import ChatGoogleGenerativeAI
    objets, attributs, incidence, sur_classe, termes = charger()[0]
    ctx = Contexte(objets, attributs, incidence, termes)
    _, _, _, emergents = classer(ctx)
    cfs = [{'X': [objets[o] for o in indices(x)], 'Y': [attributs[a] for a in indices(y)]}
           for _, x, y in selectionner(ctx, emergents, sur_classe)]
    classe = {attributs[a]: sur_classe[a] for a in range(len(attributs))}
    retenus, conversations = curer(ChatGoogleGenerativeAI(model=MODELE), cfs, classe)
    sortie = sys.argv[1] if len(sys.argv) > 1 else 'sortie_agents.json'
    json.dump({'retenus': retenus, 'conversations': conversations}, open(sortie, 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print(len(retenus), 'termes retenus sur', len(cfs), 'CFs')
