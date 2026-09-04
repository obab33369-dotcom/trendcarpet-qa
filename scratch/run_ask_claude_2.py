import os
import subprocess
import sys

# Ensure UTF-8 output
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Prepare the prompt
prompt = """Här är användarens svar på dina frågor samt instruktioner för kodändringarna:

1. Fråga 1 (GPU-kontention i Stage 3 QA Tier 2) är ditt eget ansvar att besvara som arkitekt (systems_architect). Välj den mest robusta lösningen (t.ex. Alternativ C: inaktivera lokal Florence-QA under CPU-poolen och använd moln-baserad Gemini-tie-breaker, eller den lösning du anser vara bäst) och tillhandahåll koden för den.
2. Fråga 2 (webbshoppens krav på skuggkanter): Skuggan får gärna komma utanför bilden, men den får inte påverkas estetiskt av våra beskärningar. Det får inte se ut som "klippa ut och klistra tillbaka" eftersom det blir fult, utan beskär bilden som den är på ett naturligt sätt. Justera skugg- och bildbehandlingslogiken i composition.py (och decolorization.py) därefter så att skuggan inte drabbas av fula linjer eller avklippta kanter.

Vänligen generera de fullständiga kodändringarna för projektet nu, specifikt för:
- reforma-turboflow/reforma_pipeline/composition.py (skuggpadding, rollover/falloff, feathering, och bevarande av skuggor)
- reforma-turboflow/reforma_pipeline/classification.py (caching av zoom status)
- reforma-turboflow/reforma_pipeline/orchestrator.py (curation zoom check moment-22, Stage 3 zoom override, och eventuell Stage 4 självläkande audit)
- reforma-turboflow/reforma_pipeline/qa_loop.py och qa_checker.py (anpassning av BackgroundPurityError/HaloLeakageError och borttagning av lokal Florence-QA under CPU-poolen)

Ge oss de exakta kodändringarna (diffs eller fullständiga ersättningsblock) så att orkestrator-agenten kan implementera dem direkt i codebase. Skriv svaret på svenska."""

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
    "--model", "opus",
    "--permission-mode", "dontAsk"
]

print("Launching Claude Opus 4.8 via scripts/ask_claude.py for Code Generation...")
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
