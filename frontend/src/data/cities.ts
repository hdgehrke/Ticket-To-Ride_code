// Approximate x/y positions for each city on a 1200×800 canvas,
// laid out to match the TTR Europe board geography.

export interface CityCoord {
  x: number;
  y: number;
}

export const CITY_COORDS: Record<string, CityCoord> = {
  // British Isles
  Edinburgh:     { x: 325,  y:  80 },
  London:        { x: 355,  y: 165 },

  // Iberian Peninsula
  Lisboa:        { x: 195,  y: 435 },
  Cadiz:         { x: 230,  y: 510 },
  Madrid:        { x: 285,  y: 435 },
  Pamplona:      { x: 355,  y: 375 },
  Barcelona:     { x: 415,  y: 420 },

  // France
  Dieppe:        { x: 380,  y: 210 },
  Brest:         { x: 280,  y: 250 },
  Paris:         { x: 395,  y: 265 },
  Marseille:     { x: 440,  y: 390 },

  // Benelux / Germany
  Amsterdam:     { x: 460,  y: 175 },
  Bruxelles:     { x: 435,  y: 225 },
  Frankfurt:     { x: 505,  y: 240 },
  Essen:         { x: 495,  y: 185 },
  Munchen:       { x: 525,  y: 310 },
  Zurich:        { x: 480,  y: 340 },

  // Scandinavia
  Kobenhavn:     { x: 535,  y: 120 },
  Stockholm:     { x: 605,  y:  75 },
  Petrograd:     { x: 750,  y:  65 },

  // Central Europe
  Berlin:        { x: 560,  y: 185 },
  Danzig:        { x: 625,  y: 185 },
  Warszawa:      { x: 665,  y: 240 },
  Wien:          { x: 605,  y: 310 },
  Budapest:      { x: 655,  y: 350 },

  // Italy
  Venezia:       { x: 545,  y: 365 },
  Roma:          { x: 555,  y: 455 },
  Brindisi:      { x: 615,  y: 500 },
  Palermo:       { x: 570,  y: 555 },

  // Balkans
  Zagrab:        { x: 590,  y: 375 },
  Sarajevo:      { x: 635,  y: 420 },
  Sofia:         { x: 700,  y: 450 },
  Athina:        { x: 685,  y: 525 },
  Smyrna:        { x: 800,  y: 520 },
  Bucuresti:     { x: 755,  y: 395 },
  Constantinople:{ x: 800,  y: 460 },
  Angora:        { x: 875,  y: 445 },
  Erzurum:       { x: 965,  y: 430 },
  Sevastopol:    { x: 845,  y: 370 },
  Sochi:         { x: 910,  y: 360 },
  Rostov:        { x: 940,  y: 310 },
  Kharkov:       { x: 860,  y: 270 },

  // Eastern Europe
  Kyiv:          { x: 770,  y: 275 },
  Smolensk:      { x: 785,  y: 205 },
  Wilno:         { x: 730,  y: 185 },
  Riga:          { x: 690,  y: 135 },
  Moskva:        { x: 870,  y: 160 },
};

export const CITY_NAMES = Object.keys(CITY_COORDS).sort();
