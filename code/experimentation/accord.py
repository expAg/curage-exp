"""Accord entre les quatre annotateurs : kappa de Fleiss sur le bloc commun
(donnees/evaluation/fiche_annotation_anonymisee.xlsx, une feuille par annotateur)."""
import os
import re
import zipfile
import xml.etree.ElementTree as ET
from collections import defaultdict

FICHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'donnees', 'evaluation',
                     'fiche_annotation_anonymisee.xlsx')
NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
      'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}


def feuilles(chemin):
    """{nom de la feuille: [lignes]}, chaque ligne étant {colonne: valeur}."""
    z = zipfile.ZipFile(chemin)
    chaines = [''.join(t.text or '' for t in si.iter('{%s}t' % NS['m']))
               for si in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('m:si', NS)] \
        if 'xl/sharedStrings.xml' in z.namelist() else []
    cibles = {r.get('Id'): r.get('Target') for r in ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
    out = {}
    for f in ET.fromstring(z.read('xl/workbook.xml')).find('m:sheets', NS):
        cible = cibles[f.get('{%s}id' % NS['r'])].lstrip('/')
        xml = ET.fromstring(z.read(cible if cible.startswith('xl/') else 'xl/' + cible))
        lignes = []
        for row in xml.iter('{%s}row' % NS['m']):
            ligne = {}
            for c in row.findall('m:c', NS):
                v = c.find('m:v', NS)
                texte = c.find('m:is/m:t', NS)
                val = chaines[int(v.text)] if c.get('t') == 's' and v is not None else \
                    texte.text if texte is not None else v.text if v is not None else None
                ligne[re.match(r'[A-Z]+', c.get('r')).group()] = val
            lignes.append(ligne)
        out[f.get('name')] = lignes
    return out


bloc = defaultdict(lambda: {'nommage': [], 'pertinence': []})
for nom, lignes in feuilles(FICHE).items():
    if nom.startswith('Annotateur'):
        for l in lignes[1:]:
            if l.get('G') == 'commun':
                for critere, col in (('nommage', 'C'), ('pertinence', 'E')):
                    if l.get(col) in ('bon', 'pas bon'):
                        bloc[l['A']][critere].append(l[col])


def fleiss(critere):
    accords, bons, total = [], 0, 0
    for jugements in bloc.values():
        v = jugements[critere]
        b, p, n = v.count('bon'), v.count('pas bon'), len(v)
        bons, total = bons + b, total + n
        if n >= 2:
            accords.append((b * (b - 1) + p * (p - 1)) / (n * (n - 1)))
    po = sum(accords) / len(accords)
    pe = (bons / total) ** 2 + (1 - bons / total) ** 2
    return (po - pe) / (1 - pe)


print(f'bloc commun : {len(bloc)} termes')
for critere in ('nommage', 'pertinence'):
    print(f'kappa de Fleiss, {critere} : {fleiss(critere):.2f}')
