// Approximate x/y positions for each city on a 1200×800 canvas,
// laid out to match the TTR Europe board geography.

export interface CityCoord {
  x: number;
  y: number;
}

export const CITY_COORDS: Record<string, CityCoord> = {
  // British Isles
  Edinburgh:     { x: 240,  y:  95 },
  London:        { x: 240,  y: 190 },

  // Iberian Peninsula
  Lisboa:        { x:  20,  y: 450 },
  Cadiz:         { x:  50,  y: 525 },
  Madrid:        { x: 110,  y: 465 },
  Pamplona:      { x: 150,  y: 415 },
  Barcelona:     { x: 220,  y: 475 },

  // France
  Dieppe:        { x: 230,  y: 250 },
  Brest:         { x: 155,  y: 270 },
  Paris:         { x: 250,  y: 305 },
  Marseille:     { x: 285,  y: 445 },

  // Benelux / Germany
  Amsterdam:     { x: 315,  y: 200 },
  Bruxelles:     { x: 300,  y: 250 },
  Frankfurt:     { x: 350,  y: 290 },
  Essen:         { x: 375,  y: 225 },
  Munchen:       { x: 410,  y: 345 },
  Zurich:        { x: 350,  y: 367 },

  // Scandinavia
  Kobenhavn:     { x: 420,  y: 160 },
  Stockholm:     { x: 537,  y:  70 },
  Petrograd:     { x: 710,  y:  52 },

  // Central Europe
  Berlin:        { x: 448,  y: 235 },
  Danzig:        { x: 539,  y: 200 },
  Warszawa:      { x: 578,  y: 250 },
  Wien:          { x: 485,  y: 355 },
  Budapest:      { x: 540,  y: 385 },

  // Italy
  Venezia:       { x: 415,  y: 415 },
  Roma:          { x: 405,  y: 510 },
  Brindisi:      { x: 510,  y: 560 },
  Palermo:       { x: 410,  y: 605 },

  // Balkans
  Zagrab:        { x: 475,  y: 425 },
  Sarajevo:      { x: 515,  y: 470 },
  Sofia:         { x: 615,  y: 510 },
  Athina:        { x: 600,  y: 580 },
  Smyrna:        { x: 690,  y: 605 },
  Bucuresti:     { x: 660,  y: 462 },
  Constantinople:{ x: 730,  y: 545 },
  Angora:        { x: 775,  y: 580 },
  Erzurum:       { x: 950,  y: 550 },
  Sevastopol:    { x: 805,  y: 440 },
  Sochi:         { x: 915,  y: 440 },
  Rostov:        { x: 910,  y: 350 },
  Kharkov:       { x: 832,  y: 310 },

  // Eastern Europe
  Kyiv:          { x: 735,  y: 315 },
  Smolensk:      { x: 755,  y: 180 },
  Wilno:         { x: 640,  y: 185 },
  Riga:          { x: 625,  y: 130 },
  Moskva:        { x: 860,  y: 135 },
};

export const CITY_NAMES = Object.keys(CITY_COORDS).sort();
