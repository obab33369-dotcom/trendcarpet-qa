import os
import json
import hatshop_server

workspace_dir = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\Trendcarpet_Interiors"
onedrive_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\26-08-28-Hatshop-Black-River pt1-x"

with open(os.path.join(workspace_dir, "hatshop_ui.html"), "r", encoding="utf-8") as f:
    html = f.read()

batches = hatshop_server.load_batches()
batch = batches[0]
products = hatshop_server.scan_batch_products(batch)

for p in products:
    for variant_key, shot_list in p["variants"].items():
        for s in shot_list:
            s["url"] = s["rel_path"]

products_json = json.dumps(products, ensure_ascii=False)

standalone_script = """
    const EMBEDDED_PRODUCTS = """ + products_json + """;
    state.isStandalone = true;

    async function initBatches() {
      state.batches = [{ id: 'standalone', name: '""" + batch["name"] + """', category: '""" + batch["category"] + """' }];
      state.currentBatchId = 'standalone';
      state.products = EMBEDDED_PRODUCTS;
      try {
        const localSaved = localStorage.getItem('hatshop_reviews');
        if (localSaved) state.reviews = JSON.parse(localSaved);
      } catch(e) {}
      populateSourceSelector();
      renderAngleGrid();
      renderProductSidebar();
      renderProductView();
      populateDropdowns();
      renderReportTable();
      renderSubToolbar();
      updateQAStats();
    }

    async function saveReviewToServer(productId, data) {
      if (!ensureReviewerName()) return;
      data.reviewer = state.reviewer;
      data.updatedAt = new Date().toISOString();
      state.reviews[productId] = data;
      try {
        localStorage.setItem('hatshop_reviews', JSON.stringify(state.reviews));
      } catch(e) {}
      updateQAStats();
      renderReportTable();
      showToast('Sparat lokalt! Klicka på "Spara/Ladda ner JSON" i protokollet för att dela din fil.');
    }
"""

html_standalone = html.replace("async function initBatches() {", standalone_script + "\n    async function _old_initBatches() {")

target_file = os.path.join(onedrive_dir, "Granskning_Hatshop_Black_River.html")
with open(target_file, "w", encoding="utf-8") as f:
    f.write(html_standalone)

print(f"Successfully updated standalone HTML at: {target_file}")
