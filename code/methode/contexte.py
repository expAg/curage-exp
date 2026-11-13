import json
import os

DONNEES = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'donnees')
CONTEXTE = os.path.join(DONNEES, 'contexte_formel', 'contexte_formel.json')


def charger():
    """Les cinq contextes formels, un par itération : objets, attributs « relation:cible », incidence (un ensemble
    d'attributs par objet), pour chaque attribut s'il est déclaré sur le terme initial ou sur ses classes, et les
    termes créés aux itérations précédentes présents comme objets."""
    contextes = []
    for c in json.load(open(CONTEXTE, encoding='utf-8'))['iterations']:
        attributs = [a['relation'] + ':' + a['cible'] for a in c['attributs']]
        incidence = [set() for _ in c['objets']]
        for o, a, *_ in c['incidences']:
            incidence[o].add(a)
        contextes.append((c['objets'], attributs, incidence, [a['declare_sur_classe'] for a in c['attributs']], c['termes_crees']))
    return contextes


if __name__ == '__main__':
    for k, (objets, attributs, incidence, _, _) in enumerate(charger(), 1):
        print(f'itération {k} : {len(objets)} objets, {len(attributs)} attributs, {sum(map(len, incidence))} incidences')
