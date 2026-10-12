import * as THREE from 'three';
import { createViewer, $, de, ramp, LOW } from './core.js';
import { ANNOTATIONS, GROUPS, PHASES } from './content.js';

// Blender (Z up, −Y vorne) → three.js (Y up, +Z vorne)
const B = (x, y, z) => new THREE.Vector3(x, z, -y);

const _v = new THREE.Vector3();
let TL, inkMats = [], tympanPaper = null, printedTex = null, rubricTex = null, stackTopMat = null, printedMat = null;
let line1 = [];

const viewer = createViewer({
  model: 'models/gpress.glb',
  timeline: 'models/timeline.json',
  content: { ANNOTATIONS, GROUPS, PHASES },
  bg: '#0a0f18',
  fog: 0.0105,
  exposure: 1.05,
  envIntensity: 0.32,
  fov: 36,
  near: 0.05,
  far: 400,
  minDistance: 0.8,
  maxDistance: 80,
  unit: 0.1,
  gtao: { radius: 0.9, thickness: 1.2, distanceExponent: 1.4 },
  bloom: [0.16, 0.45, 0.94],

  lights(ctx) {
    const { scene } = ctx;
    scene.add(new THREE.HemisphereLight(0xd8e4ff, 0x2a1a10, 0.55));
    // warm "window" light from the front left
    const key = new THREE.DirectionalLight(0xffe2bd, 2.6);
    key.position.copy(B(-16, -22, 30));
    key.target.position.copy(B(0, -3, 6));
    key.castShadow = true;
    key.shadow.mapSize.set(LOW ? 1024 : 2048, LOW ? 1024 : 2048);
    Object.assign(key.shadow.camera, { left: -20, right: 20, top: 20, bottom: -20, near: 1, far: 90 });
    key.shadow.bias = -0.0004;
    key.shadow.normalBias = 0.03;
    scene.add(key, key.target);
    const rim = new THREE.DirectionalLight(0x8fb8ff, 0.9);
    rim.position.copy(B(18, 16, 14));
    scene.add(rim);
    // candle-like warm point near the composing station
    const candle = new THREE.PointLight(0xffb066, 6, 14, 1.6);
    candle.position.copy(B(-11, -8, 13));
    scene.add(candle);
    return { key };
  },

  home() {
    const a = innerWidth / innerHeight;
    const dist = a >= 1.2 ? 30 : a >= 0.8 ? 36 : 46;
    return { target: B(0, -3, 7.5), offset: new THREE.Vector3(1.0, 0.55, 1.25).setLength(dist) };
  },

  followGoal(ctx, t, out) {
    const { worldPos } = ctx;
    const ph = ctx.state.phases.find((p) => t >= p.from && t < p.to)?.key;
    switch (ph) {
      case 'letter': return worldPos('ANCHOR_Letter', out);
      case 'setzen': return worldPos('Winkelhaken', out).add(_v.set(0, 0.25, 0));
      case 'form': return worldPos(line1[20] || 'Letter_20', out);
      case 'einfaerben': return worldPos('Schliessrahmen', out);
      case 'papier': return worldPos('ANCHOR_Deckel', out).lerp(worldPos('Schliessrahmen', _v), 0.4);
      case 'einfahren':
      case 'drucken':
      case 'ausfahren': return worldPos('Schliessrahmen', out).add(_v.set(0, 1.2, 0));
      case 'bogen': return worldPos('Bogen_Gedruckt', out);
      case 'rubrik': return worldPos('Druckstapel_Oben', out);
      default: return out.copy(B(0, -3, 7.5));
    }
  },

  phaseView(ctx, key) {
    const V = {
      letter: [[0.35, 0.45, 1], 1.3],
      setzen: [[0.3, 0.95, 1], 5.5],
      form: [[0.7, 0.9, 1], 8],
      einfaerben: [[1, 1.05, 0.3], 8],
      papier: [[1, 0.85, 0.12], 12],
      einfahren: [[1, 0.5, 0.95], 24],
      drucken: [[1, 0.32, 0.75], 15],
      ausfahren: [[1, 0.6, 1], 20],
      bogen: [[0.08, 0.12, 1], 7.5],
      rubrik: [[0.05, 1, 0.4], 6],
    }[key];
    return V && { dir: new THREE.Vector3(...V[0]), dist: V[1] };
  },

  material(ctx, mesh) {
    const m = mesh.material;
    if (!m) return;
    if (m.name === 'Letter_Bild') inkMats.push(m);
    if (/^Bogen|^Druckstapel_Oben/.test(mesh.name) || /^Bogen/.test(mesh.parent?.name)) {
      mesh.material = m.clone();
      mesh.material.side = THREE.DoubleSide;
      backDim(mesh.material);
      if (mesh.name.startsWith('Bogen_Deckel')) tympanPaper = mesh.material;
      if (mesh.name.startsWith('Bogen_Gedruckt')) printedMat = mesh.material;
      if (mesh.name.startsWith('Druckstapel_Oben')) stackTopMat = mesh.material;
    }
  },

  onSetup(ctx) {
    TL = ctx.TL;
    for (let k = 0; ctx.nodes[`Letter_${String(k).padStart(2, '0')}`]; k++) line1.push(`Letter_${String(k).padStart(2, '0')}`);
    printedTex = printedMat?.map || null;
    if (printedTex) printedTex.anisotropy = 8;
    rubricTex = new THREE.TextureLoader().load('models/bogen_rubr.jpg', (tx) => {
      tx.flipY = false;
      tx.colorSpace = THREE.SRGBColorSpace;
      tx.anisotropy = 8;
      tx.needsUpdate = true;
    });
    // remember the clean metal colour of the type face
    for (const m of inkMats) m.userData.base = { color: m.color.clone(), metalness: m.metalness, roughness: m.roughness };
  },

  onUpdate(ctx) {
    const t = ctx.state.t;
    // ink on the type faces
    const k = ramp(t, TL.ink[0], TL.ink[1]);
    for (const m of inkMats) {
      const b = m.userData.base;
      m.color.copy(b.color).lerp(INK, k);
      m.metalness = b.metalness + (0.15 - b.metalness) * k;
      m.roughness = b.roughness + (0.22 - b.roughness) * k;
    }
    // the sheet on the tympan becomes printed at the moment of impression
    if (tympanPaper && printedTex) {
      const want = t >= TL.print ? printedTex : null;
      if (tympanPaper.map !== want) { tympanPaper.map = want; tympanPaper.color.set(want ? '#ffffff' : PAPER); tympanPaper.needsUpdate = true; }
    }
    // rubricator paints the initial
    const r = ramp(t, TL.rubric[0], TL.rubric[1]);
    for (const m of [printedMat, stackTopMat]) {
      if (!m || !rubricTex) continue;
      const want = r > 0.5 ? rubricTex : printedTex;
      if (m.map !== want) { m.map = want; m.needsUpdate = true; }
    }
  },

  onUI(ctx) {
    const t = ctx.state.t;
    const s = sortsInForme(t);
    $('tSorts').textContent = de(s);
    $('tSheets').textContent = t >= TL.print ? '1' : '0';
    const bar = barDeg(ctx);
    $('rBar').textContent = `${de(Math.abs(bar))}°`;
    $('rForce').textContent = `${de(force(bar), 1)} kN`;
    $('rCar').textContent = carText(ctx);
    $('rSlow').textContent = ctx.state.speed === 1 ? 'Echtzeit' : `${de(ctx.state.speed, 2).replace(/,?0+$/, '')}×`;
  },

  liveText(ctx, kind, t) {
    if (kind === 'bar') {
      const d = barDeg(ctx);
      return `<b>Bengel</b> · ${de(Math.abs(d))}° gezogen<br><b>Presskraft (geschätzt)</b> · ${de(force(d), 1)} kN`;
    }
    if (kind === 'car') return `<b>Karren</b> · ${carText(ctx)}`;
    if (kind === 'sorts') {
      const n = setCount(t);
      return `<b>Im Winkelhaken</b> · ${n} von ${TL.type.line1} Lettern (Zeile 1)<br><b>In der Form</b> · ${de(sortsInForme(t))} von ${de(TL.type.sorts)}`;
    }
    return '';
  },
});

const INK = new THREE.Color('#0d0d10');
const PAPER = new THREE.Color('#efe7d3');

// the side of the sheet that did not touch the type shows the print only faintly (show-through)
function backDim(mat) {
  mat.onBeforeCompile = (sh) => {
    sh.fragmentShader = sh.fragmentShader.replace(
      '#include <map_fragment>',
      `#include <map_fragment>
       if (!gl_FrontFacing) diffuseColor.rgb = mix(diffuseColor.rgb, vec3(0.86, 0.82, 0.72), 0.86);`,
    );
  };
  mat.customProgramCacheKey = () => 'backdim';
}

// composing schedule (mirrors build_gpress.py)
function setCount(t) {
  const N = TL.type.line1, T0 = 6.4, T1 = 15.0, FLY = 0.85;
  if (t < 5.8) return 0;
  let n = 1;
  for (let k = 1; k < N; k++) if (t >= T0 + (k - 1) * (T1 - T0 - FLY) / Math.max(1, N - 2) + FLY) n++;
  return n;
}
function sortsInForme(t) {
  return TL.type.sorts - TL.type.line1 + (t >= 20.3 ? TL.type.line1 : 0);
}
function barDeg(ctx) {
  const q = ctx.nodes.Spindel?.quaternion;
  if (!q) return 0;
  return THREE.MathUtils.radToDeg(2 * Math.atan2(q.y, q.w));
}
// rough estimate: 300 N pull on a 0.85 m bar, 5.5 cm thread pitch, ~35 % efficiency; only near full pull
function force(deg) {
  const k = ramp(Math.abs(deg), 55, 80);
  return k * (2 * Math.PI * 300 * 0.85 / 0.055 * 0.35) / 1000;
}
function carText(ctx) {
  const n = ctx.nodes.Karren;
  if (!n) return '—';
  const travel = TL.carriage.travel_dm;
  const yBl = -n.position.z;                 // Blender Y
  const inside = (yBl - (-7.5)) / travel;    // 0 = ausgefahren, 1 = eingefahren
  if (inside < 0.02) return 'ausgefahren';
  if (inside > 0.98) return 'unter dem Tiegel';
  return `${de(inside * travel * 10)} cm eingefahren`;
}

window.__gpress = viewer;
