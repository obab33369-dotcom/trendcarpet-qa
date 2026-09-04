# Reforma Turboflow Room Renders Sorting Guide

This document preserves the knowledge, logic, and workflow for sorting Midjourney room renders into product-specific folders. It serves as a permanent reference "thread" for future agents and manual operators.

---

## 📌 Context & Sökvägar

*   **Projektmapp:** `c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow`
*   **Källmapp (Standard/Widescreen):** `C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow`
*   **Källmapp (Kvadratisk/Square):** `C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\första omgången fyrkantiga`
*   **Målmapp för sorterat resultat:** `C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\Reforma-interiörer-26-06`
*   **Referensbilder (Askås-beskurna):**
    *   Källa 1: `C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_cropped_full\artiklar`
    *   Källa 2: `C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\missed-products-upload\artiklar`

---

## ⚠️ Det grundläggande problemet: Indexkrockar

Eftersom bilderna har genererats i olika omgångar (Batch 1, Batch 2, Full Catalog) börjar numreringen av bild-prompterna om från `1` i varje omgång. Detta gör att samma startnummer i filnamnet refererar till helt olika produkter:
*   **Index 93** i **Batch 1** = `Bäddsoffa Kap Verde Beige` (soffa i vardagsrum).
*   **Index 93** i **Batch 2** = `Matbord Luma Runt 115cm Valnöt` (matbord i matsal).

Om man enbart sorterar baserat på startsiffran kommer matbordet att hamna i soffmappen, vilket ser tokigt ut för kunden.

---

## 🛠️ Lösningen: Suffix-differens (Database Routing)

Filnamnen har formen:
`{lead_idx}-architectural-digest-style-{style_num}.png`
(Ibland med `style-` eller `styl-`).

Genom att räkna ut skillnaden `diff = lead_idx - style_num` kan vi med 100% precision avgöra vilken databas filen tillhör:

1.  **Batch 1 (diff == 0):**
    Exempel: `093-architectural-digest-style-093.png` -> `093 - 93 = 0`.
    *Slås upp i:* `rooms_turboflow_batch1.json` (eller `rooms_turboflow.json`).
2.  **Batch 2 (diff ∈ [46, 76, 92, 174, 248, 262, 326, 354, 382, 389, 436, 576, 593] och lead_idx ≤ 692):**
    Exempel: `093-architectural-digest-style-017.png` -> `093 - 17 = 76`.
    *Slås upp i:* `rooms_turboflow_batch2.json`.
3.  **Full Catalog (Alla andra differenser):**
    *Slås upp i:* `rooms_turboflow_full_catalog.json`.

Denna logik är implementerad i `organize_interiors.py` och garanterar att varje rendering hamnar i rätt produktmapp.

---

## 🏷️ Manuella Produkt-Overrides

Några produkter saknar direkta träffar i databaserna eller behöver styras till specifika SKU:er. Skriptet hanterar dessa manuellt:
*   **Newcastle:** `NEWCASTLE-BLACK` (Bokhylla Newcastle Svart) - använder en lokal referensbild från `batch1_images`.
*   **Cardoba:** `H000022821` (Sidobord Cardoba Natur)
*   **Istria:** `76375` (Sängbord Istria Natur)
*   **Blåvik:** `23101-natur` (Byrå Blåvik - Natur)
*   **Cadiz:** `CADIZ-DESK` (Skrivbord Cadiz - Natur)
*   **Torekov:**
    *   Valnöt: `2251-1 Walnut` (Sidobord Torekov - Ljus Valnöt)
    *   Ek: `2251-1 Oak` (Sidobord Torekov Ek)
    *   Natur/Skåp: `TOREKOV-CABINET` (Skåp Torekov - Natur)

---

## 🏃 Hur man kör sorteringen och granskningen

1.  **Kör Sorteringsskriptet:**
    Kopierar alla rumsbilder till rätt mappar på OneDrive och lägger till studio-referensbilderna under namnet `00_REFERENCE_{SKU}.jpg` (eller `.png`):
    ```bash
    python organize_interiors.py
    ```
    *Obs: Skriptet använder `exist_ok=True` och raderar ALDRIG mappar för att förhindra synkroniseringsfel i OneDrive.*

2.  **Generera Granskningsvyn (Dashboard):**
    Genererar en lokal, interaktiv HTML-sida där du kan se alla mappar sida-vid-sida:
    ```bash
    python generate_review_dashboard.py
    ```
    Öppna sedan filen:
    [visual_review.html](file:///C:/Users/AndronikLindgren/OneDrive%20-%20CaMa%20Gruppen%20AB/Pictures/turboflow/Reforma-interi%C3%B6rer-26-06/visual_review.html)
    i valfri webbläsare för att kontrollera att allt är 100% korrekt.
