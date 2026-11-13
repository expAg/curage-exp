def bits(ensemble):
    m = 0
    for i in ensemble:
        m |= 1 << i
    return m


def compte(m):
    return bin(m).count('1')


def indices(m):
    while m:
        b = m & -m
        yield b.bit_length() - 1
        m ^= b


class Contexte:
    def __init__(self, objets, attributs, incidence, termes_crees=()):
        self.n, self.m = len(objets), len(attributs)
        self.ligne = [bits(r) for r in incidence]                     # attributs de chaque objet
        self.colonne = [0] * self.m                                    # objets de chaque attribut
        for o, r in enumerate(incidence):
            for a in r:
                self.colonne[a] |= 1 << o
        self.attributs = attributs
        rang = {o: i for i, o in enumerate(objets)}
        # colonnes r_isa:t : (extension, l'objet nommé t s'il existe, sa ligne)
        self.isa = []
        for a, x in enumerate(attributs):
            if x.startswith('r_isa:'):
                i = rang.get(x[6:])
                self.isa.append((self.colonne[a], 1 << i if i is not None else 0, self.ligne[i] if i is not None else None))
        # termes créés aux itérations précédentes, présents comme objets : leurs objets, termes créés dépliés
        self.crees = {rang[t] for t in termes_crees if t in rang}
        self.porteurs = {soi.bit_length() - 1: xa & ~soi for xa, soi, _ in self.isa if soi}
        self._plats = {}

    def intension(self, ext):
        y = (1 << self.m) - 1
        for o in indices(ext):
            y &= self.ligne[o]
        return y

    def extension(self, y):
        x = (1 << self.n) - 1
        for a in indices(y):
            x &= self.colonne[a]
        return x

    def fermeture(self, ext):
        return self.extension(self.intension(ext))

    def plats(self, masque, vus=frozenset()):
        out = 0
        for j in indices(masque):
            if j in self.crees and j in self.porteurs and j not in vus:
                if j not in self._plats:
                    self._plats[j] = self.plats(self.porteurs[j], vus | {j})
                out |= self._plats[j]
            else:
                out |= 1 << j
        return out


def next_closure(ctx):
    """Tous les concepts formels (X, Y), dans l'ordre lectique des extensions (Ganter, 2010)."""
    x = ctx.fermeture(0)
    while True:
        yield x, ctx.intension(x)
        for i in range(ctx.n - 1, -1, -1):
            bit = 1 << i
            if x & bit:
                continue
            bas = x & (bit - 1)
            y = ctx.fermeture(bas | bit)
            if y & (bit - 1) == bas:
                x = y
                break
        else:
            return


def lexicalise(ctx, x, y):
    """(X, Y) est lexicalisé si un attribut r_isa:t a exactement X pour extension (l'objet nommé t, s'il existe,
    compté ou non), ou si (X, Y) n'est qu'un terme créé t : Y est la ligne de t, et les autres objets de X,
    termes créés dépliés, couvrent exactement les objets de t."""
    for xa, soi, ligne in ctx.isa:
        if xa & ~soi == x & ~soi:
            return True
        if soi and soi.bit_length() - 1 in ctx.crees and x & soi and not (x & ~soi & ~xa) and y == ligne \
                and ctx.plats(x & ~soi) == ctx.plats(xa & ~soi):
            return True
    return False


def classer(ctx):
    tous, candidats, lexicalises, emergents = [], [], [], []
    for x, y in next_closure(ctx):
        tous.append((x, y))
        if compte(x) >= 2 and compte(y) >= 2:
            candidats.append((x, y))
            (lexicalises if lexicalise(ctx, x, y) else emergents).append((x, y))
    return tous, candidats, lexicalises, emergents


if __name__ == '__main__':
    from contexte import charger
    for k, (objets, attributs, incidence, _, termes) in enumerate(charger(), 1):
        tous, candidats, lexicalises, emergents = classer(Contexte(objets, attributs, incidence, termes))
        print(f'itération {k} : {len(tous)} concepts formels, dont {len(candidats)} d\'au moins 2 objets et 2 attributs : '
              f'{len(lexicalises)} lexicalisés, {len(emergents)} émergents')
