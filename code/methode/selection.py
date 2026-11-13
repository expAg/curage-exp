import math

from fermetures import compte, indices

RELATIONS_DOMAINE = ('r_domain', 'r_has_topic')
PENALITE_DOMAINE = 0.25   # trait qui situe un vocabulaire sans décrire l'objet
PENALITE_CLASSE = 0.5     # trait déclaré sur le terme initial ou sur ses classes
TAILLE = 100


def specificite(ctx, a, sur_classe):
    """p(m) = log(n / |{m}'|), pénalisée."""
    p = math.log(ctx.n / compte(ctx.colonne[a]))
    if ctx.attributs[a].split(':', 1)[0] in RELATIONS_DOMAINE:
        p *= PENALITE_DOMAINE
    if sur_classe[a]:
        p *= PENALITE_CLASSE
    return p


def kappa(ctx, x, y, sur_classe):
    """κ(X, Y) = 1/|Y| · Σ_{m ∈ Y} p(m) / log(n / |X|)."""
    haut = math.log(ctx.n / compte(x))
    if haut == 0:
        return 0.0
    return sum(specificite(ctx, a, sur_classe) for a in indices(y)) / compte(y) / haut


def selectionner(ctx, emergents, sur_classe, taille=TAILLE):
    notes = [(kappa(ctx, x, y, sur_classe), x, y) for x, y in emergents]
    notes.sort(key=lambda t: -t[0])
    return notes[:taille]


if __name__ == '__main__':
    import sys
    from contexte import charger
    from fermetures import Contexte, classer
    k = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    objets, attributs, incidence, sur_classe, termes = charger()[k - 1]
    ctx = Contexte(objets, attributs, incidence, termes)
    for rang, (kappa_, x, y) in enumerate(selectionner(ctx, classer(ctx)[3], sur_classe), 1):
        print(f'{rang:4d}  κ = {kappa_:.3f}  ' + ', '.join(objets[o] for o in indices(x)))
