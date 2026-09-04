import os
import subprocess
import sys

# Ensure UTF-8 output
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Prepare the prompt
prompt = """nej jag vill att --model opus tar ställning till de invändingarn du har, jag vill att du skickar med info om vår dators kapacitet/systemet samt vad vi behöver uträtta/vilke svårigeheterna är rörande skuggor och avklippta möbler osv om det behövs skickas igen- sedan avvaktar vi svar från arkitekten

Ovanstående är instruktionen från användaren. 

Dessutom ska du veta följande:
1. Agenten Antigravity (en Gemini-agent) glömmer bort vem som är arkitekten och försöker spela rollen som arkitekt genom att starta egna subagenter (som den felaktigt döper till "opus" eller "systems_architect"). 
2. Vi frågar dig (den riktiga Claude Opus 4.8 via CLI på max deep think) om arkitekturen måste uppdateras för att hantera våra problem.
3. Vänligen förbjud uttryckligen Antigravity från att kalla sina egna subagenter för "opus" eller "arkitekter" i framtiden för att undvika denna förvirring.

Här är informationen om vår dators kapacitet och systemet:
- OS: Windows 11 (PowerShell)
- GPU: NVIDIA RTX 3000 Ada Generation Laptop GPU (8GB VRAM)
- CUDA: PyTorch 2.6.0+cu124, CUDA 12.4
- Kontext: Körs lokalt på en utvecklardator (laptop).

Här är vad vi behöver uträtta och vilka svårigheterna är rörande skuggor och avklippta möbler:
1. Trasiga golvskuggor (Shadow Clipping & Edge Fading):
   - De naturliga skuggorna klipps av i kanterna på ett fult, pixligt eller avhugget sätt.
   - Orsak 1: Beskärningsmarginalerna (crop padding) i composition.py är för trånga (40px horisontellt, 20px vertikalt).
   - Orsak 2: Canvas border feathering (feather_width = 80 i composition.py) bleker gradvis ut allt i de yttersta 80px av den 2000x2000px stora canvasen till vitt, vilket klipper av mjuka skuggor som sträcker sig utåt.
2. Felaktig padding/vita marginaler på närbilder (Zoom-vyer):
   - Närbilder (t.ex. på stolsits eller ben) hamnar centrerade på en enorm vit yta med tjocka vita marginaler.
   - Orsak: Curation-steget i Stage 1 klassificerar zoom-vyer. Heuristiken "margin-touch" (om bilden rör vid kanterna) beror på bbox_db. Men bbox_db skapas först i Stage 2 (SAM3). Detta skapar ett moment-22 för nya SKU:er där zoom-bilderna klassificeras som vanliga studio-vyer (is_zoom_view = False) och sparas i classification_cache.json. När Stage 3 (Composition) körs, används den felaktiga cachen och tvingar närbilden att behandlas som en studio full-view (centrerad i en stor vit box).

Invändningar mot att migrera till en full Celery/Redis och GPU-baserad Florence-2 målavskiljning:
- VRAM-begränsningar: Att köra SAM3 (3.4GB) och Florence-2 (0.8GB) samtidigt på en GPU med 8GB VRAM riskerar CUDA OOM-krascher om flera processer eller Celery-workers körs samtidigt. En sekventiell GPU-process är mycket säkrare.
- Windows-kompatibilitet: Redis och Celery är krångliga och instabila att köra nativt på Windows. En lokal ProcessPoolExecutor på CPU för Stage 3 fungerar perfekt utan extra bakgrundstjänster.

Vänligen ta ställning till dessa invändningar, problem och ge din arkitektoniska bedömning samt konkreta rekommendationer för hur vi ska lösa detta i vår pipeline."""

# Build env
env = os.environ.copy()
env["CLAUDE_CODE_EFFORT_LEVEL"] = "max"
if "ANTHROPIC_API_KEY" in env:
    del env["ANTHROPIC_API_KEY"]

# Run the ask_claude script via python
cmd = [
    sys.executable,
    os.path.join("scripts", "ask_claude.py"),
    prompt,
    "--task-id", "task-439",
    "--model", "opus"
]

print("Launching Claude Opus 4.8 via scripts/ask_claude.py...")
res = subprocess.run(
    cmd,
    env=env,
    capture_output=True,
    text=True,
    encoding='utf-8'
)

print(f"Exit code: {res.returncode}")
if res.stdout:
    print("\n=== STDOUT ===")
    print(res.stdout)
if res.stderr:
    print("\n=== STDERR ===")
    print(res.stderr)
