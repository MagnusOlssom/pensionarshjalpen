# Pensionärshjälpen

Hemsida för Pensionärshjälpen – telefonhjälp för äldre med det digitala.

## Idén med designen: en sak i taget

- Ingen meny, inga popup-rutor, inga kakor (cookies), ingen spårning, inga rörelser.
- Det enda man kan trycka på är stora och står ensamma.
- På mobil: en stor grön knapp som ringer. På dator: numret i stor text (en ring-länk där öppnar bara förvirrande "Öppna FaceTime?"-rutor).
- Undersidorna nås via Google, via "Läs mer" längst ner och via "Alla ämnen". Varje undersida har samma ring-ruta överst och nederst.
- Typsnittet Atkinson Hyperlegible är gjort för personer med nedsatt syn. Det ligger i repot, så sidan pratar inte med Google Fonts.

## Ändra innehåll

1. Redigera eller lägg till en fil i `content/` (en fil = en undersida, filnamnet blir adressen).
2. Kör `python3 build.py` – den bygger om allt till `docs/`.
3. Committa och pusha. GitHub Pages publicerar `docs/`.

Telefonnummer och adress ändras högst upp i `build.py`.

## När domänen är köpt

1. Sätt `SITE_URL = "https://pensionärshjälpen.se (skrivs xn--pensionrshjlpen-6kbe.se i CNAME-filen)"` i `build.py`.
2. Lägg en fil `src/CNAME` med raden `pensionärshjälpen.se (skrivs xn--pensionrshjlpen-6kbe.se i CNAME-filen)` och kör `python3 build.py`.
3. Peka domänens DNS mot GitHub Pages och slå på "Enforce HTTPS" under repots Settings → Pages.

`research/research.md` innehåller underlaget (statistik, källor, sökfraser).
