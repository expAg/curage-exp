// Figures 2, 3 et 4 de l'article.
// Figure 2 : score du juge final moyen des termes retenus, par itération (donnees/resultats/termes_retenus.json) :
//   moyenne des termes créés à l'itération, moyenne cumulée de tous les retenus, et moyenne des 100 meilleurs
//   retenus jusqu'à l'itération, avec une bande d'un écart type.
// Figures 3 et 4 : précisions du nommage et de la pertinence (donnees/evaluation/precisions_humains.json).
// Utilise les fonctions de la page (esc, fmt, table, load, VIEWS).

const MK = {carre:(x,y)=>`<rect x="${x-4}" y="${y-4}" width="8" height="8" rx="1"/>`,
  triangle:(x,y)=>`<path d="M${x},${y-5} L${x+5},${y+4} L${x-5},${y+4} Z"/>`,
  losange:(x,y)=>`<path d="M${x},${y-5.5} L${x+5.5},${y} L${x},${y+5.5} L${x-5.5},${y} Z"/>`};
function figure({titre, source, xs, xlab, ylab, ymin, ymax, yticks, fmtY, series}){
  const W = 520, H = 290, m = {l:48, r:58, t:12, b:44}, w = W - m.l - m.r, h = H - m.t - m.b;
  const X = i => m.l + i * w / (xs.length - 1), Y = v => m.t + h - (v - ymin) / (ymax - ymin) * h;
  let g = yticks.map(t => `<line x1="${m.l}" x2="${m.l+w}" y1="${Y(t)}" y2="${Y(t)}" stroke="var(--grid)"/><text x="${m.l-8}" y="${Y(t)+4}" text-anchor="end">${fmtY(t)}</text>`).join('');
  g += xs.map((x,i) => `<text x="${X(i)}" y="${m.t+h+18}" text-anchor="middle">${esc(x)}</text>`).join('');
  g += `<text x="${m.l+w/2}" y="${H-6}" text-anchor="middle">${esc(xlab)}</text><text transform="translate(12,${m.t+h/2}) rotate(-90)" text-anchor="middle">${esc(ylab)}</text>`;
  for (const s of series) if (s.bande) {
    const haut = s.bande[1].map((v,i) => (i ? 'L' : 'M') + X(i) + ',' + Y(v)).join(' ');
    const bas = s.bande[0].map((v,i) => [i,v]).reverse().map(([i,v]) => 'L' + X(i) + ',' + Y(v)).join(' ');
    g += `<path d="${haut} ${bas} Z" fill="var(${s.c})" opacity="0.12"/>`; }
  for (const s of series) {
    g += `<path d="${s.v.map((v,i) => (i ? 'L' : 'M') + X(i) + ',' + Y(v)).join(' ')}" fill="none" stroke="var(${s.c})" stroke-width="2" ${s.tirets ? 'stroke-dasharray="5 4"' : ''}/>`;
    g += `<g fill="var(${s.c})" stroke="var(--bg)" stroke-width="2">${s.v.map((v,i) => MK[s.m](X(i), Y(v))).join('')}</g>`; }
  // étiquettes de fin de série, écartées si elles se chevauchent
  const n = xs.length - 1, fin = series.map(s => ({s, y: Y(s.v[n]) + 4})).sort((a,b) => a.y - b.y);
  for (let k = 1; k < fin.length; k++) if (fin[k].y - fin[k-1].y < 12) fin[k].y = fin[k-1].y + 12;
  g += fin.map(f => `<text x="${X(n)+9}" y="${f.y}" style="fill:var(--ink)">${fmtY(f.s.v[n], true)}</text>`).join('');
  g += `<line class="cx" x1="0" x2="0" y1="${m.t}" y2="${m.t+h}" stroke="var(--faint)" stroke-dasharray="2 3" visibility="hidden"/>`;
  const pas = w / (xs.length - 1);
  g += xs.map((x,i) => `<rect class="hit" data-i="${i}" x="${X(i) - pas/2}" y="${m.t}" width="${pas}" height="${h}" fill="transparent"/>`).join('');
  const lg = series.map(s => `<span><svg viewBox="0 0 22 10"><line x1="1" x2="21" y1="5" y2="5" stroke="var(${s.c})" stroke-width="2" ${s.tirets ? 'stroke-dasharray="4 3"' : ''}/><g fill="var(${s.c})">${MK[s.m](11,5)}</g></svg>${esc(s.nom)}${s.bande ? ', bande : un écart type' : ''}</span>`).join('');
  const tab = `<details><summary>valeurs</summary>${table([xlab, ...series.map(s => s.nom)], xs.map((x,i) => [x, ...series.map(s => fmtY(s.v[i], true))]), [0, ...series.map(() => 1)], {compte:false, h:240})}</details>`;
  return `<div class="fig"><h2>${esc(titre)}</h2><div class="src">${esc(source)}</div><div class="lg">${lg}</div><svg viewBox="0 0 ${W} ${H}" data-xlab="${esc(xlab)}" role="img" aria-label="${esc(titre)}">${g}</svg>${tab}</div>`;
}
function survol(el, xs, series, fmtY){
  el.querySelectorAll('.fig').forEach((f, k) => {
    const svg = f.querySelector(':scope > svg'), cx = svg.querySelector('.cx'), S = series[k], tip = $('#tip');
    svg.querySelectorAll('.hit').forEach(r => {
      r.onmousemove = e => { const i = +r.dataset.i, x = +r.getAttribute('x') + +r.getAttribute('width') / 2;
        cx.setAttribute('x1', x); cx.setAttribute('x2', x); cx.setAttribute('visibility', 'visible');
        tip.innerHTML = `<b>${svg.dataset.xlab} ${esc(xs[k][i])}</b><br>` + S.map(s => `${esc(s.nom)} : ${fmtY[k](s.v[i], true)}`).join('<br>');
        tip.style.display = 'block'; tip.style.left = (e.clientX + 12) + 'px'; tip.style.top = (e.clientY + 12) + 'px'; };
      r.onmouseleave = () => { tip.style.display = 'none'; cx.setAttribute('visibility', 'hidden'); }; }); });
}
VIEWS.figures = async () => {
  const T = await load('termes'), ev = await load('evaluation'), p = ev.precisions, its = [1,2,3,4,5];
  const moy = a => a.reduce((x,y) => x + y, 0) / a.length, et = a => { const m = moy(a); return Math.sqrt(moy(a.map(x => (x - m) ** 2))); };
  const sc = t => t.score_final, cum = k => T.filter(t => t.iteration <= k).map(sc), top = k => cum(k).sort((a,b) => b - a).slice(0, 100);
  const f2 = [
    {nom:'100 meilleurs retenus', c:'--s2', m:'carre', tirets:true, v:its.map(k => moy(top(k))),
     bande:[its.map(k => moy(top(k)) - et(top(k))), its.map(k => moy(top(k)) + et(top(k)))]},
    {nom:'retenus à l\'itération', c:'--s1', m:'losange', v:its.map(k => moy(T.filter(t => t.iteration === k).map(sc)))},
    {nom:'tous les retenus', c:'--s3', m:'triangle', v:its.map(k => moy(cum(k)))}];
  const pr = (n, pe, mo) => [{nom:'nommage', c:'--s1', m:'carre', v:n}, {nom:'pertinence', c:'--s2', m:'triangle', v:pe}, {nom:'moyenne', c:'--s3', m:'losange', v:mo}];
  const f3 = pr(p.par_score_nommage, p.par_score_pertinence, p.par_score_moyenne);
  const f4 = pr(p.par_iteration_nommage, p.par_iteration_pertinence, p.par_iteration_moyenne);
  const note = v => fmt(Math.round(v * 100 + 1e-6) / 100, 2), pct = (v, l) => l ? v + ' %' : String(v);
  const X2 = its.map(String), X3 = p.classes_score;
  $('#main').innerHTML = `<div class="figs">`
    + figure({titre:'Figure 2 · Score du juge final moyen des termes retenus, par itération', source:'calculé à partir de donnees/resultats/termes_retenus.json, code dans code/experimentation/figures.js',
              xs:X2, xlab:'itération', ylab:'score du juge final moyen', ymin:0.60, ymax:0.90, yticks:[0.60,0.65,0.70,0.75,0.80,0.85,0.90], fmtY:note, series:f2})
    + figure({titre:'Figure 3 · Précisions du nommage et de la pertinence, par score du juge final', source:'données dans donnees/evaluation/fiche_annotation_anonymisee.xlsx',
              xs:X3, xlab:'score du juge final', ylab:'précision (%)', ymin:0, ymax:100, yticks:[0,25,50,75,100], fmtY:pct, series:f3})
    + figure({titre:'Figure 4 · Précisions du nommage et de la pertinence, par itération', source:'données dans donnees/evaluation/fiche_annotation_anonymisee.xlsx',
              xs:X2, xlab:'itération où le terme est créé', ylab:'précision (%)', ymin:0, ymax:100, yticks:[0,25,50,75,100], fmtY:pct, series:f4})
    + `</div>`;
  survol($('#main'), [X2, X3, X2], [f2, f3, f4], [note, pct, pct]);
};
