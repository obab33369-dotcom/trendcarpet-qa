# Interior Designer AI Automation Studio

Detta är ett exklusivt, högpresterande och automatiserat verktyg för att skapa professionella inredningsbilder baserat på dina egna möbler och stilreferenser. Verktyget körs lokalt på din dator och automatiserar **Google Gemini Advanced (gemini.google.com)** för att utnyttja dina befintliga **Google One AI Ultra credits** och de absolut senaste bildgenereringsmodellerna (t.ex. Gemini Pro/Imagen 4 eller motsvarande avancerade visualizers).

**Helt utan API-nycklar!** Ingen API-nyckel, inget Vertex AI-konto eller betalda credits krävs. Allt körs genom din vanliga webbläsarsession.

## Funktioner

1.  **Helt API-nyckelfri design**: Slipp konfigurera externa utvecklarkonton eller betala för API-anrop. Automatiseringen körs direkt i din vanliga inloggade webbläsarsession på Gemini Advanced.
2.  **Visuell möbelväljare (Workspace Grid)**: Ett modernt, glassmorfiskt webbgränssnitt som automatiskt skannar din lokala mapp, visar dina möbler visuellt och låter dig välja exakt vilka objekt som ska ingå.
3.  **Nativ AI-Kurering via Prompt**: När Playwright laddar upp möbelbilderna och stilreferensen till Gemini Advanced, instruerar prompten Gemini att agera professionell inredningsarkitekt. Gemini analyserar bilderna visuellt, kurerar den perfekta estetiska kombinationen (t.ex. matchar rätt bord med passande stolar, lampa och matta) och genererar en harmonisk interiör.
4.  **Helautomatisk Playwright-motor**: Backend-motorn startar en lokal webbläsare, navigerar till Gemini, laddar upp bilderna, fyller i inredningsinstruktionerna, väntar på bildgenereringen och laddar automatiskt ner de resulterande interiörerna direkt till din lokala `outputs`-mapp!

---

## Förberedelser & Installation

1.  **Installera Python-paket**:
    Installera nödvändiga bibliotek på din dator:
    ```powershell
    pip install -r requirements.txt
    ```

2.  **Installera Playwright-webbläsare**:
    Kör följande kommando för att installera webbläsarna som behövs för automatiseringen:
    ```powershell
    playwright install chromium
    ```

---

## Starta Applikationen

Starta servern med Uvicorn:
```powershell
python -m uvicorn app:app --reload
```

Öppna sedan din webbläsare och navigera till:
👉 **`http://localhost:8000`**

---

## Steg-för-steg användning

1.  **Logga in en gång**:
    Klicka på knappen **"Starta inloggningswebbläsare"** i gränssnittet. Ett synligt Chromium-fönster öppnas. Logga in på ditt Google-konto (där du har ditt Gemini Advanced / Google One AI Ultra-abonnemang). När du ser Gemini-chatten är du redo! Stäng bara fönstret – din inloggningssession sparas säkert och krypteras lokalt i mappen `browser_profile/` för framtida körningar.

2.  **Ange sökvägar & Skanna**:
    *   Ange den absoluta sökvägen till mappen med dina möbler (t.ex. `C:\Users\AndronikLindgren\Documents\Möbler`).
    *   Ange sökvägen till din stilreferensbild (t.ex. `C:\Users\AndronikLindgren\Documents\Stilar\skandinavisk.jpg`).
    *   Klicka på **"Skanna och analysera mappar"**. Dina möbler visas nu i det snygga bildrutnätet!

3.  **Välj möbler**:
    *   Klicka på de möbelbilder i galleriet som du vill använda för genereringen (t.ex. ett matbord, en stol och en lampa).

4.  **Starta batch-generering**:
    *   Granska eller anpassa den inbyggda prompt-mallen efter dina önskemål.
    *   Klicka på **"Starta Automatisering"**.
    *   Luta dig tillbaka! Playwright startar i bakgrunden, laddar upp bilderna, skickar prompten till Gemini Advanced, väntar tills Gemini genererat bilderna och sparar dem automatiskt i din `outputs`-mapp som visas direkt i gränssnittet.

