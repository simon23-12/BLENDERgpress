// Inhalte der Annotationen und Arbeitsschritte (Deutsch, Sek. I – Geschichte).
// parts: Namensmuster der Blender-Objekte (Picking + Hervorhebung)
// markers/focus: { anchor: 'ANCHOR_…' } = leerer Knoten aus Blender (wandert mit bewegten Teilen mit)

export const GROUPS = [
  { label: 'Die Presse', ids: ['gestell', 'spindel', 'bengel', 'tiegel', 'karren', 'kurbel', 'fundament', 'deckel', 'raehmchen'] },
  { label: 'Satz & Farbe', ids: ['letter', 'setzkasten', 'winkelhaken', 'form', 'ballen', 'farbe', 'papier'] },
  { label: 'Ergebnis', ids: ['bogen', 'rubrik', 'b42'] },
];

export const ANNOTATIONS = [
  {
    id: 'gestell',
    title: 'Pressengestell',
    kicker: 'Rahmen aus Eichenholz',
    color: '#d9a066',
    parts: ['^Wange_', '^Schwelle_', '^Strebe_', '^Krone$', '^Winter$', '^Keil_Kopf', '^Bruecke$'],
    markers: [{ anchor: 'ANCHOR_Gestell', label: 'Gestell' }],
    focus: { anchor: 'ANCHOR_Gestell', distance: 28 },
    text:
      'Gutenberg erfand die Presse nicht neu: Er übernahm die Bauweise der Spindelpressen, mit denen man damals Wein kelterte oder Papier entwässerte. ' +
      'Zwei senkrechte Wangen tragen Kopf, Brücke und Laufbahn. Das schwere Holzgestell muss den Druck beim Ziehen aufnehmen, ohne nachzugeben.',
    facts: [
      ['Höhe', '≈ 2 m'],
      ['Material', 'Eichenholz, Eisenteile'],
      ['Vorbild', 'Wein- und Papierpresse'],
      ['Kopf / Brücke', 'Querbalken, verkeilt'],
    ],
  },
  {
    id: 'spindel',
    title: 'Spindel',
    kicker: 'Schraube · Kraftwandler',
    color: '#f0c27a',
    parts: ['^Spindel', '^Kopf_Mutter', '^Kopf$'],
    markers: [{ anchor: 'ANCHOR_Spindel', label: 'Spindel' }],
    focus: { anchor: 'ANCHOR_Spindel', distance: 9 },
    live: 'bar',
    text:
      'Die Spindel ist eine dicke Schraube, die in einer Mutter im Kopf der Presse läuft. Dreht man sie, bewegt sie sich nach unten. ' +
      'Eine kleine Drehung am langen Bengel wird so in einen kurzen, aber sehr kräftigen Druck nach unten umgewandelt.',
    facts: [
      ['Drehung pro Druck', '≈ ¼ Umdrehung'],
      ['Weg nach unten', '≈ 1 cm (hier überzeichnet)'],
      ['Prinzip', 'schiefe Ebene, aufgewickelt'],
      ['Gewinde', 'Holz, später Messing/Eisen'],
    ],
  },
  {
    id: 'bengel',
    title: 'Bengel',
    kicker: 'Hebel · Pressbengel',
    color: '#ffb35c',
    parts: ['^Bengel'],
    markers: [{ anchor: 'ANCHOR_Bengel', label: 'Bengel' }],
    focus: { anchor: 'ANCHOR_Bengel', distance: 8 },
    live: 'bar',
    text:
      'Der Drucker zieht den eisernen Bengel kräftig zu sich heran. Je länger der Hebel, desto weniger Kraft braucht er (Hebelgesetz). ' +
      'Zusammen mit der Spindel entsteht so eine Presskraft von etwa einer Tonne – genug, um die Farbe gleichmäßig auf das Papier zu bringen.',
    facts: [
      ['Länge', '≈ 0,9 m'],
      ['Zugkraft des Druckers', '≈ 300 N'],
      ['Presskraft (Schätzung)', '≈ 10 kN ≈ 1 t'],
      ['Schwenkwinkel', '≈ 80°'],
    ],
  },
  {
    id: 'tiegel',
    title: 'Tiegel',
    kicker: 'Druckplatte',
    color: '#c98b4e',
    parts: ['^Tiegel', '^Buechse'],
    markers: [{ anchor: 'ANCHOR_Tiegel', label: 'Tiegel' }],
    focus: { anchor: 'ANCHOR_Tiegel', distance: 9 },
    text:
      'Der Tiegel ist eine flache, harte Platte. Er hängt an der Büchse, die in der Brücke geführt wird, damit er sich nicht mitdreht. ' +
      'Beim Druck senkt er sich und presst Deckel, Papier und Lettern überall gleich stark zusammen.',
    facts: [
      ['Fläche', '≈ 40 × 34 cm'],
      ['Führung', 'Büchse in der Brücke'],
      ['Bewegung', 'nur auf und ab'],
    ],
  },
  {
    id: 'karren',
    title: 'Karren & Laufbahn',
    kicker: 'Schlitten',
    color: '#b8875a',
    parts: ['^Karren_', '^Sarg_', '^Bahn_'],
    markers: [{ anchor: 'ANCHOR_Karren', label: 'Karren' }, { anchor: 'ANCHOR_Bahn', label: 'Laufbahn' }],
    focus: { anchor: 'ANCHOR_Karren', distance: 14 },
    live: 'car',
    text:
      'Auf dem Karren liegt die Druckform. Er gleitet auf eisernen Schienen: heraus zum Einfärben und Einlegen des Papiers, hinein unter den Tiegel zum Drucken.',
    facts: [
      ['Fahrweg', '≈ 70 cm'],
      ['Antrieb', 'Kurbel mit Riemen'],
      ['Schienen', 'Eisen auf Holzbalken'],
    ],
  },
  {
    id: 'kurbel',
    title: 'Kurbel',
    kicker: 'Antrieb des Karrens',
    color: '#9fb2c8',
    parts: ['^Kurbel'],
    markers: [{ anchor: 'ANCHOR_Kurbel', label: 'Kurbel' }],
    focus: { anchor: 'ANCHOR_Kurbel', distance: 7 },
    live: 'car',
    text:
      'Über eine Trommel und Lederriemen zieht die Kurbel den Karren hinein und wieder heraus. So muss der Drucker die schwere Form nicht schieben.',
    facts: [
      ['Trommel', 'Ø ≈ 11 cm'],
      ['Umdrehungen je Fahrt', '≈ 2'],
    ],
  },
  {
    id: 'fundament',
    title: 'Fundament',
    kicker: 'Druckstein',
    color: '#c9c3b8',
    parts: ['^Fundament'],
    markers: [{ anchor: 'ANCHOR_Fundament', label: 'Fundament' }],
    focus: { anchor: 'ANCHOR_Fundament', distance: 8 },
    text:
      'Eine vollkommen ebene Steinplatte im Karren. Nur auf einer ebenen Unterlage stehen alle Lettern gleich hoch – sonst drucken manche zu stark und andere gar nicht.',
    facts: [
      ['Material', 'Marmor oder Kalkstein'],
      ['Aufgabe', 'ebene, harte Unterlage'],
    ],
  },
  {
    id: 'deckel',
    title: 'Deckel',
    kicker: 'Rahmen mit Pergament',
    color: '#e8cf9a',
    parts: ['^Deckel'],
    markers: [{ anchor: 'ANCHOR_Deckel', label: 'Deckel' }],
    focus: { anchor: 'ANCHOR_Deckel', distance: 8 },
    text:
      'Ein klappbarer Rahmen, mit Pergament bespannt. Der Bogen wird darauf an zwei Nadeln (Punkturen) ausgerichtet, damit Vorder- und Rückseite später genau übereinander passen. ' +
      'Eine weiche Zwischenlage gleicht kleine Unebenheiten aus.',
    facts: [
      ['Bespannung', 'Pergament'],
      ['Ausrichtung', 'Punkturen (Nadeln)'],
      ['Gelenk', 'am äußeren Ende des Karrens'],
    ],
  },
  {
    id: 'raehmchen',
    title: 'Rähmchen',
    kicker: 'Maske',
    color: '#f4e2b8',
    parts: ['^Raehmchen'],
    markers: [{ anchor: 'ANCHOR_Raehmchen', label: 'Rähmchen' }],
    focus: { anchor: 'ANCHOR_Raehmchen', distance: 8 },
    text:
      'Das Rähmchen klappt über den Bogen und hält ihn fest. Sein Fenster ist so groß wie der Text – der Rand des Papiers bleibt sauber, auch wenn Schließrahmen und Stege etwas Farbe abbekommen.',
    facts: [
      ['Aufgabe', 'Bogen halten, Ränder schützen'],
      ['Material', 'Pergament auf Eisenrahmen'],
    ],
  },
  {
    id: 'letter',
    title: 'Die bewegliche Letter',
    kicker: 'Gutenbergs Erfindung',
    color: '#c4ccd6',
    parts: ['^Letter_'],
    markers: [
      { anchor: 'ANCHOR_Letter_Bild', label: 'Bild (spiegelverkehrt)', to: 6.4 },
      { anchor: 'ANCHOR_Letter_Signatur', label: 'Signatur (Kerbe)', to: 6.4 },
      { anchor: 'ANCHOR_Letter_Fuss', label: 'Kegel', to: 6.4 },
    ],
    focus: { anchor: 'ANCHOR_Letter', distance: 1.6, moving: true },
    text:
      'Jeder Buchstabe ist ein eigener Metallkörper (Kegel) mit dem erhabenen, spiegelverkehrten Schriftbild obendrauf. Gegossen wurden die Lettern im Handgießinstrument: ' +
      'Ein Stahlstempel prägt die Form des Buchstabens in eine Kupfer-Matrize, die dann beliebig oft mit flüssigem Metall ausgegossen wird. ' +
      'Alle Lettern sind gleich hoch – nur so drucken sie gleichmäßig. An der Kerbe (Signatur) erkennt der Setzer ertastend, wie herum die Letter liegt.',
    facts: [
      ['Metall', 'Blei, Zinn, Antimon'],
      ['Schmelzpunkt', '≈ 250 °C'],
      ['Zeichen der B42', '≈ 290 (mit Ligaturen, Kürzeln)'],
      ['Schrift', 'gebrochene Schrift (Textura)'],
      ['Hier', '≈ 3× vergrößert'],
    ],
  },
  {
    id: 'setzkasten',
    title: 'Setzkasten',
    kicker: 'Vorrat an Lettern',
    color: '#d7a46a',
    parts: ['^Setzkasten', '^Pult_'],
    markers: [{ anchor: 'ANCHOR_Setzkasten', label: 'Setzkasten' }],
    focus: { anchor: 'ANCHOR_Setzkasten', distance: 6 },
    text:
      'Jedes Zeichen hat sein eigenes Fach, häufige Buchstaben liegen nah beim Setzer in größeren Fächern. Der Setzer greift, ohne hinzusehen. ' +
      'Später lagen die Großbuchstaben im oberen Kasten – daher kommen die englischen Wörter „upper case“ und „lower case“.',
    facts: [
      ['Fächer hier', '14 × 7'],
      ['Vorrat einer Werkstatt', 'zehntausende Lettern'],
    ],
  },
  {
    id: 'winkelhaken',
    title: 'Winkelhaken',
    kicker: 'Werkzeug des Setzers',
    color: '#aab8c6',
    parts: ['^Winkelhaken'],
    markers: [{ anchor: 'ANCHOR_Winkelhaken', label: 'Winkelhaken' }],
    focus: { anchor: 'ANCHOR_Winkelhaken', distance: 4.5 },
    live: 'sorts',
    text:
      'In diesem Metallwinkel reiht der Setzer die Lettern zu einer Zeile. Mit Leerstücken unterschiedlicher Breite (Ausschluss) bringt er jede Zeile auf genau dieselbe Länge – ' +
      'so entsteht der gleichmäßige Blocksatz, für den die Gutenberg-Bibel berühmt ist.',
    facts: [
      ['Zeilenbreite', 'fest eingestellt'],
      ['Ausschluss', 'nicht druckende Leerstücke'],
      ['Satzrichtung', 'spiegelverkehrt'],
    ],
  },
  {
    id: 'form',
    title: 'Druckform',
    kicker: 'Satz im Schließrahmen',
    color: '#e3b45b',
    parts: ['^Zeile_', '^Ausschluss', '^Schliessrahmen', '^Steg_', '^Keil_Form', '^Druckform'],
    markers: [{ anchor: 'ANCHOR_Form', label: 'Druckform' }],
    focus: { anchor: 'ANCHOR_Form', distance: 6 },
    live: 'sorts',
    text:
      'Zeile für Zeile entsteht eine Seite. Ein eiserner Rahmen hält sie zusammen; Holzstege und Keile pressen die Lettern so fest, dass man die Form anheben kann, ohne dass ein Buchstabe herausfällt. ' +
      'Links oben bleibt Platz frei: Dort wird später die große Anfangsinitiale von Hand gemalt. Nach dem Druck werden die Lettern wieder abgelegt und für neue Seiten verwendet.',
    facts: [
      ['Zeilen hier', '10'],
      ['B42', '2 Spalten × 42 Zeilen'],
      ['Lettern pro Seite (B42)', '≈ 2.700'],
      ['Befestigung', 'Stege und Keile'],
    ],
  },
  {
    id: 'ballen',
    title: 'Druckerballen',
    kicker: 'Farbauftrag',
    color: '#a5714a',
    parts: ['^Ballen_'],
    markers: [{ anchor: 'ANCHOR_Ballen', label: 'Druckerballen' }],
    focus: { anchor: 'ANCHOR_Ballen', distance: 5, moving: true },
    text:
      'Lederkissen, mit Rosshaar oder Wolle gefüllt, auf einem Holzgriff. Der Ballenmeister nimmt mit ihnen Farbe auf, verreibt sie, bis sie gleichmäßig verteilt ist, und tupft sie auf die Lettern.',
    facts: [
      ['Bezug', 'Leder'],
      ['Füllung', 'Rosshaar oder Wolle'],
      ['Bedienung', 'zwei Ballen gleichzeitig'],
    ],
  },
  {
    id: 'farbe',
    title: 'Druckerschwärze',
    kicker: 'Farbe auf Ölbasis',
    color: '#8e9aa8',
    parts: ['^Farbtisch', '^Farbstein', '^Farbe_'],
    markers: [{ anchor: 'ANCHOR_Farbtisch', label: 'Farbstein' }],
    focus: { anchor: 'ANCHOR_Farbtisch', distance: 5 },
    text:
      'Wasserfarbe perlt von Metall ab. Gutenberg nutzte deshalb eine zähe Farbe aus Ruß und gekochtem Leinöl (Firnis), ähnlich den Ölfarben der Maler. ' +
      'Untersuchungen zeigen in seiner Druckerschwärze auch Metalle wie Kupfer und Blei – sie glänzt bis heute tiefschwarz.',
    facts: [
      ['Pigment', 'Ruß'],
      ['Bindemittel', 'Leinölfirnis'],
      ['Besonderheit', 'enthält Metallanteile'],
    ],
  },
  {
    id: 'papier',
    title: 'Papier',
    kicker: 'Lumpenpapier aus Italien',
    color: '#efe6cf',
    parts: ['^Papierstapel', '^Bogen_Lose', '^Papierbank'],
    markers: [{ anchor: 'ANCHOR_Papier', label: 'Papier' }],
    focus: { anchor: 'ANCHOR_Papier', distance: 7 },
    text:
      'Papier wurde aus Leinen- und Hanflumpen geschöpft und aus Italien eingeführt. Vor dem Druck feuchtete man es an – dann nimmt es die Farbe besser auf. ' +
      'Ein Teil der Gutenberg-Bibeln wurde auf teurem Pergament (Tierhaut) gedruckt.',
    facts: [
      ['Rohstoff', 'Leinen- und Hanflumpen'],
      ['Herkunft', 'Italien'],
      ['Vor dem Druck', 'angefeuchtet'],
    ],
  },
  {
    id: 'bogen',
    title: 'Der gedruckte Bogen',
    kicker: 'Seitenrichtig!',
    color: '#fff1d0',
    parts: ['^Bogen_Gedruckt', '^Bogen_Deckel', '^Druckstapel'],
    markers: [{ anchor: 'ANCHOR_Bogen', label: 'Druckbogen', from: 51.7, to: 57.8 }],
    focus: { anchor: 'ANCHOR_Bogen', distance: 6, moving: true },
    text:
      'Die spiegelverkehrte Form ergibt einen seitenrichtigen Abdruck. Hier steht der Anfang der Bibel auf Latein: „Im Anfang schuf Gott Himmel und Erde …“ (Genesis 1). ' +
      'Jeder Bogen wurde nach dem Trocknen auf der Rückseite bedruckt, gefaltet und mit anderen zu Lagen zusammengelegt.',
    facts: [
      ['Text', 'Genesis 1,1–7 (Vulgata)'],
      ['Sprache', 'Latein'],
      ['Danach', 'trocknen, Rückseite drucken, falten'],
    ],
  },
  {
    id: 'rubrik',
    title: 'Rubrikator',
    kicker: 'Handarbeit nach dem Druck',
    color: '#d9493f',
    parts: [],
    markers: [{ anchor: 'ANCHOR_Druckstapel', label: 'Initiale von Hand', from: 57.8 }],
    focus: { anchor: 'ANCHOR_Druckstapel', distance: 5 },
    text:
      'Rote Überschriften und große, farbige Anfangsbuchstaben (Initialen) wurden nach dem Druck von Hand eingefügt – wie in den handgeschriebenen Büchern, die die Käufer gewohnt waren. ' +
      'Weil jede Werkstatt anders verzierte, ist jedes Exemplar der Gutenberg-Bibel ein Einzelstück.',
    facts: [
      ['Farben', 'Rot, Blau, teils Gold'],
      ['Wer?', 'Rubrikatoren und Buchmaler'],
    ],
  },
  {
    id: 'b42',
    title: 'Die Gutenberg-Bibel',
    kicker: 'B42 · Mainz 1452–1454',
    color: '#e3b45b',
    parts: [],
    markers: [{ anchor: 'ANCHOR_Druckstapel', label: 'Gutenberg-Bibel', to: 57.8 }],
    focus: { anchor: 'ANCHOR_Druckstapel', distance: 9 },
    text:
      'Johannes Gutenberg (um 1400–1468) druckte in Mainz das erste große Buch mit beweglichen Lettern. Statt einer Bibel in ein bis drei Jahren Schreibarbeit entstanden in etwa drei Jahren rund 180 Exemplare. ' +
      'Der Buchdruck machte Bücher billiger und Wissen schneller verbreitbar – eine Voraussetzung für Reformation, Wissenschaft und Zeitungen.',
    facts: [
      ['Exemplare', '≈ 180'],
      ['davon auf Pergament', '≈ 30–45'],
      ['Umfang', '1.282 Seiten, 2 Bände'],
      ['Zeilen je Spalte', '42 (daher „B42“)'],
      ['Erhalten', '49 Exemplare (21 vollständig)'],
    ],
  },
];

export const PHASES = {
  letter: {
    title: 'Die bewegliche Letter',
    text: 'Herzstück der Erfindung: Jeder Buchstabe ist ein eigener kleiner Metallkörper. Das Schriftbild steht erhaben und spiegelverkehrt obendrauf – die Lettern lassen sich immer wieder neu kombinieren.',
  },
  setzen: {
    title: 'Setzen',
    text: 'Der Setzer nimmt Letter für Letter aus den Fächern des Setzkastens und reiht sie im Winkelhaken zu einer Zeile. Leerstücke bringen jede Zeile auf genau dieselbe Breite.',
  },
  form: {
    title: 'Die Druckform entsteht',
    text: 'Die fertige Zeile kommt in die Druckform. Zeile für Zeile entsteht eine Seite, die im Schließrahmen mit Holzstegen und Keilen festgeklemmt wird.',
  },
  einfaerben: {
    title: 'Einfärben',
    text: 'Mit zwei Druckerballen nimmt der Ballenmeister Druckerschwärze vom Farbstein, verreibt sie und tupft sie gleichmäßig auf die Lettern.',
  },
  papier: {
    title: 'Papier einlegen',
    text: 'Ein angefeuchteter Bogen kommt auf den Deckel. Das Rähmchen klappt darüber und hält ihn, dann wird der Deckel auf die Druckform geklappt.',
  },
  einfahren: {
    title: 'Einfahren',
    text: 'Mit der Kurbel zieht der Drucker den Karren auf der Laufbahn unter den Tiegel.',
  },
  drucken: {
    title: 'Der Druck',
    text: 'Ein kräftiger Zug am Bengel dreht die Spindel. Sie drückt den Tiegel nach unten und presst Papier und Lettern aufeinander – die Farbe geht auf das Papier über.',
  },
  ausfahren: {
    title: 'Ausfahren',
    text: 'Bengel zurück, Karren heraus, Deckel und Rähmchen auf. Für jeden weiteren Abzug wird die Form neu eingefärbt.',
  },
  bogen: {
    title: 'Der fertige Bogen',
    text: 'Aus der spiegelverkehrten Form wird ein seitenrichtiger Druck. Zwei Drucker schafften einige hundert Abzüge am Tag – ein Schreiber brauchte für eine ganze Bibel Jahre.',
  },
  rubrik: {
    title: 'Von Hand vollendet',
    text: 'Die große Initiale und rote Überschriften malten Rubrikatoren nachträglich von Hand. Darum gleicht kein Exemplar der Gutenberg-Bibel genau dem anderen.',
  },
};
