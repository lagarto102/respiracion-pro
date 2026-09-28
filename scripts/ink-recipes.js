/* Recetas de las texturas "papel y tinta" (de la maqueta del 28.09.2026).
   No se cargan en la app: scripts/render-textures.py las ejecuta en Chromium y
   guarda el resultado en img/ como imágenes. Así el móvil no tiene que calcular
   filtros SVG (feTurbulence, feDisplacementMap...) mientras se respira.
   OJO: E y center() se repiten en index.html para trazar el pincel; si cambias
   la forma del ensō aquí, cámbiala también allí y vuelve a generar img/. */

function mulberry32(a){return function(){a|=0;a=a+0x6D2B79F5|0;let t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296}}
function smooth(arr,passes){let a=arr.slice();for(let p=0;p<passes;p++){const b=a.slice();for(let i=0;i<a.length;i++){b[i]=(a[Math.max(0,i-1)]+2*a[i]+a[Math.min(a.length-1,i+1)])/4}a=b}return a}
const f2 = n => n.toFixed(2);

/* el ensō: empieza arriba, a las 12 (277° − 7° de giro = 270°) y gira como las agujas del reloj */
const E = {cx:150, cy:150, R:106, start:277, sweep:332, rot:-7, N:420};
function center(t){
  const ang = (E.start + E.sweep * t) * Math.PI / 180;
  const wob = 2.4 * Math.sin(2 * Math.PI * t * 1.1 + 0.6) + 1.1 * Math.sin(2 * Math.PI * t * 3.3 + 2.0);
  const lift = t > 0.88 ? (t - 0.88) * 22 : 0;
  const r = E.R + wob + lift;
  const x0 = r * 1.018 * Math.cos(ang), y0 = r * 0.982 * Math.sin(ang);
  const c = Math.cos(E.rot * Math.PI / 180), s = Math.sin(E.rot * Math.PI / 180);
  return [E.cx + x0 * c - y0 * s, E.cy + x0 * s + y0 * c];
}
function width(t){
  if (t < 0.035) return 11 + (t / 0.035) * 9;
  if (t < 0.25) return 20 - (t - 0.035) / 0.215 * 2.5;
  if (t < 0.7) return 17.5 - (t - 0.25) / 0.45 * 5;
  const u = Math.min(1, (t - 0.7) / 0.3);
  return 12.5 * Math.pow(Math.max(0, 1 - u), 1.4) + 0.7;
}
function buildEnso(seed){
  const rand = mulberry32(seed), N = E.N, pts = [], wid = [], nor = [];
  for (let i = 0; i <= N; i++){ pts.push(center(i / N)); wid.push(width(i / N)); }
  for (let i = 0; i <= N; i++){
    const a = pts[Math.max(0, i - 1)], b = pts[Math.min(N, i + 1)];
    const tx = b[0] - a[0], ty = b[1] - a[1], l = Math.hypot(tx, ty) || 1;
    nor.push([-ty / l, tx / l]);
  }
  const eo = smooth(Array.from({length:N + 1}, () => rand() * 2 - 1), 5);
  const ei = smooth(Array.from({length:N + 1}, () => rand() * 2 - 1), 5);
  const out = [], inn = [];
  for (let i = 0; i <= N; i++){
    const t = i / N, [x, y] = pts[i], [nx, ny] = nor[i], h = wid[i] / 2;
    const amp = 0.55 + (t > 0.66 ? (t - 0.66) * 4.5 : 0);
    const o = Math.max(0.25, h + eo[i] * amp), n = Math.max(0.25, h + ei[i] * amp);
    out.push([x + nx * o, y + ny * o]); inn.push([x - nx * n, y - ny * n]);
  }
  const ring = 'M' + out.map(p => f2(p[0]) + ' ' + f2(p[1])).join('L') + 'L' + inn.reverse().map(p => f2(p[0]) + ' ' + f2(p[1])).join('L') + 'Z';
  const [x0, y0] = pts[0], [x1, y1] = pts[6], ang = Math.atan2(y1 - y0, x1 - x0);
  const hx = x0 - Math.cos(ang) * 1.5, hy = y0 - Math.sin(ang) * 1.5;
  const head = `<ellipse cx="${f2(hx)}" cy="${f2(hy)}" rx="8.8" ry="10.6" transform="rotate(${f2(ang * 180 / Math.PI)} ${f2(hx)} ${f2(hy)})"/>`;
  const lane = (l, t0, t1) => {
    let d = ''; const i1 = Math.min(N, Math.floor(t1 * N));
    for (let i = Math.floor(t0 * N); i <= i1; i += 2){
      const [x, y] = pts[i], [nx, ny] = nor[i], h = wid[i] / 2;
      d += (d ? 'L' : 'M') + f2(x + nx * l * h) + ' ' + f2(y + ny * l * h);
    }
    return d;
  };
  const streaks = [];
  for (let k = 0; k < 9; k++) streaks.push({d:lane((rand() * 2 - 1) * 0.82, 0.62 + rand() * 0.28, 1), w:0.35 + rand() * 0.5});
  for (let k = 0; k < 8; k++){ const t0 = 0.1 + rand() * 0.5; streaks.push({d:lane((rand() * 2 - 1) * 0.75, t0, t0 + 0.03 + rand() * 0.1), w:0.25 + rand() * 0.3}); }
  return {ring, head, streaks};
}
function ensoSVG(ink, g, px){
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 300" width="${px}" height="${px}"><defs>
<filter id="ink" x="-6%" y="-6%" width="112%" height="112%" color-interpolation-filters="sRGB">
<feTurbulence type="fractalNoise" baseFrequency="0.03" numOctaves="3" seed="7" result="t"/>
<feColorMatrix in="t" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 1.1 0.38" result="a"/>
<feComposite in="SourceGraphic" in2="a" operator="in" result="shade"/>
<feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" seed="3" result="n"/>
<feDisplacementMap in="shade" in2="n" scale="2.6" xChannelSelector="R" yChannelSelector="G"/></filter>
<filter id="bleed" x="-6%" y="-6%" width="112%" height="112%"><feGaussianBlur stdDeviation="1.8"/></filter>
<filter id="fray" x="-6%" y="-6%" width="112%" height="112%"><feTurbulence type="fractalNoise" baseFrequency="0.6" numOctaves="1" seed="5" result="n"/><feDisplacementMap in="SourceGraphic" in2="n" scale="1.6" xChannelSelector="R" yChannelSelector="G"/></filter>
<mask id="dry" maskUnits="userSpaceOnUse" x="0" y="0" width="300" height="300"><rect width="300" height="300" fill="#fff"/>
<g fill="none" stroke="#000" stroke-linecap="round" filter="url(#fray)">${g.streaks.map(s => `<path d="${s.d}" stroke-width="${f2(s.w)}"/>`).join('')}</g></mask>
</defs>
<g opacity="0.2" filter="url(#bleed)" fill="${ink}"><path d="${g.ring}"/></g>
<g mask="url(#dry)"><g filter="url(#ink)" fill="${ink}"><path d="${g.ring}"/>${g.head}</g></g>
</svg>`;
}
function washSVG(ink, px){                               /* aguada de tinta que respira */
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="${px}" height="${px}"><defs>
<radialGradient id="g" cx="50%" cy="50%" r="50%">
<stop offset="0" stop-color="${ink}" stop-opacity=".2"/><stop offset=".55" stop-color="${ink}" stop-opacity=".14"/>
<stop offset=".84" stop-color="${ink}" stop-opacity=".13"/><stop offset=".95" stop-color="${ink}" stop-opacity=".27"/>
<stop offset="1" stop-color="${ink}" stop-opacity="0"/></radialGradient>
<filter id="f" x="-12%" y="-12%" width="124%" height="124%" color-interpolation-filters="sRGB">
<feTurbulence type="fractalNoise" baseFrequency=".02" numOctaves="3" seed="4" result="n"/>
<feDisplacementMap in="SourceGraphic" in2="n" scale="18" xChannelSelector="R" yChannelSelector="G" result="d"/>
<feTurbulence type="fractalNoise" baseFrequency=".45" numOctaves="2" seed="9" result="gr"/>
<feColorMatrix in="gr" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 .9 .55" result="ga"/>
<feComposite in="d" in2="ga" operator="in" result="c"/><feGaussianBlur in="c" stdDeviation=".6"/></filter>
</defs><circle cx="100" cy="100" r="84" fill="url(#g)" filter="url(#f)"/></svg>`;
}
/* grano del papel (claro) y de la tinta (oscuro); se funden con el color de fondo */
function grainSVG(look, px){
  const a = look === 'tinta' ? '0 0 0 0 .92  0 0 0 0 .89  0 0 0 0 .8  .5 0 0 0 -.28' : '0 0 0 0 .4  0 0 0 0 .36  0 0 0 0 .28  .9 0 0 0 -.42';
  const b = look === 'tinta' ? '0 0 0 0 .6  0 0 0 0 .58  0 0 0 0 .5  .18 0 0 0 -.07' : '0 0 0 0 .62  0 0 0 0 .57  0 0 0 0 .47  .55 0 0 0 -.22';
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 360 360" width="${px}" height="${px}"><filter id="a" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency=".78" numOctaves="3" stitchTiles="stitch"/><feColorMatrix values="${a}"/></filter><filter id="b" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency=".011" numOctaves="3" stitchTiles="stitch"/><feColorMatrix values="${b}"/></filter><rect width="100%" height="100%" filter="url(#b)"/><rect width="100%" height="100%" filter="url(#a)"/></svg>`;
}
