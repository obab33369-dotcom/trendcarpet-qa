# REFORMA Project Master Map

## Översikt
Detta projekt konsoliderar alla automationsskript och datafiler för REFORMA. Detta inkluderar:
1. FTP-automation och bildhantering (sortera, skrapa).
2. Automating Furniture Interior (webbskrapning och inredningsdata).

## Mappstruktur
- `/scripts/` - Innehåller alla Python-skript (FTP, parse, fetch, list osv).
- `/data/` - Innehåller rå HTML-kod, JSON-utdrag och skrapad data.
- `/reforma-original-images/` & `/reforma-turboflow/` - Bildkataloger för mediahantering via FTP.
- `/interior-designer-automation/` - Källkod för inredningsautomationen.

## Status
- **Strukturering:** ✅ Slutförd. Alla relevanta filer från rotmappen är inlagda i logiska undermappar.
- **Git-spårning:** Initieras så fort nästa funktion byggs (enligt våra nya regler).

## Miljö & Säkerhet
- Endast lokala miljöer används (`venv`).
- Skripten körs från denna Projects-mapp, men har dynamisk åtkomst till OneDrive/Bilder för media.
