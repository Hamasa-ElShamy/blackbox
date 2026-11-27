# BlackBox design system

Read this before changing the site (`docs/index.html`). Add no new directions.

- Direction: engineering graph paper. Warm paper background with a 32px grid, hard 1.5px ink borders, a flat offset shadow on the main panel, one yellow highlight on a single word of the headline.
- Colour: ink `#10201f`, paper `#f4f1e8`, accent teal `#0b5d57`, highlight `#f2c94c`. The hex map uses one colour per field kind (timestamp amber, decimal teal, whole number blue, text rose, constant grey, header dark grey). Every map cell keeps AA contrast with its text.
- Type: Space Grotesk for text and headings, JetBrains Mono for bytes and code, Cairo for Arabic.
- Light page only. Arabic-first: the AR/EN toggle sets `lang` and `dir`; the map, tables and code stay LTR on purpose.
- Motion: small hover lift on buttons, off under `prefers-reduced-motion`.
- Targets: buttons are at least 44px high. The map scrolls inside its own box; no page overflow at 360px (measured live at 360, 768 and 1440).
- Honesty: the page states that results are guesses, shows the measured accuracy, and never shows a number that was not measured.
- Known gap: text created after a language switch (the "Guess (high)" line) is built in English.
