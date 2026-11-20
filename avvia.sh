#!/bin/bash
# Lanciato dall'app. Alla prima esecuzione installa i componenti, poi avvia la trascrizione.
NOME="${1:-Conferenza}"
APP_DIR="$(cd "$(dirname "$0")" && pwd)"
SUP="$HOME/Library/Application Support/TrascrizioneLive"
VENV="$SUP/venv"
mkdir -p "$SUP/bozze"
clear
echo "TRASCRIZIONE LIVE"
echo "========================================"
if [ ! -x "$VENV/bin/python" ]; then
  PY=""
  for p in /opt/homebrew/bin/python3.11 /usr/local/bin/python3.11 "$(command -v python3.11 2>/dev/null)"; do
    if [ -n "$p" ] && [ -x "$p" ]; then PY="$p"; break; fi
  done
  if [ -z "$PY" ]; then
    echo "Python 3.11 non trovato. Installalo con: brew install python@3.11"
    read -r -p "Premi Invio per chiudere..."
    exit 1
  fi
  echo "Prima esecuzione: installo i componenti (alcuni minuti)..."
  if ! { "$PY" -m venv "$VENV" && "$VENV/bin/pip" install --upgrade pip && \
         "$VENV/bin/pip" install faster-whisper sounddevice silero-vad numpy torch python-docx; }; then
    echo "Installazione fallita. Controlla i messaggi sopra."
    read -r -p "Premi Invio per chiudere..."
    exit 1
  fi
fi
if ! "$VENV/bin/python" -c "import parakeet_mlx, qwen3_asr_mlx, mlx" >/dev/null 2>&1; then
  echo "Installo i motori di trascrizione (Qwen3-ASR, Parakeet)..."
  "$VENV/bin/pip" install parakeet-mlx qwen3-asr-mlx soundfile || {
    echo "Installazione di parakeet-mlx fallita. Controlla i messaggi sopra."
    read -r -p "Premi Invio per chiudere..."
    exit 1
  }
fi
# Finestra separata con i comandi, così la finestra della trascrizione resta pulita
LEGENDA="$SUP/legenda.command"
cat > "$LEGENDA" <<'TXT'
#!/bin/bash
clear
echo "TRASCRIZIONE LIVE - COMANDI"
echo "========================================"
echo ""
echo "  Barra spaziatrice    accende / spegne il microfono"
echo "                       (spento = pausa: il programma non ascolta)"
echo ""
echo "  Ctrl+C               termina la conferenza e apre"
echo "                       la finestra per salvare il file .docx"
echo ""
echo "  Salvataggio          scegli nella finestra dove salvare"
echo "                       il file .docx"
echo ""
echo "  Bozza di sicurezza   ~/Library/Application Support/"
echo "                       TrascrizioneLive/bozze/"
echo ""
echo "  Per chiudere questa finestra premi Invio"
read -r _
TXT
chmod +x "$LEGENDA"
open -a Terminal "$LEGENDA"
"$VENV/bin/python" "$APP_DIR/live_transcribe.py" --nome "$NOME" --bozze "$SUP/bozze" --motore "${LDO_MOTORE:-auto}"
echo
read -r -p "Premi Invio per chiudere la finestra..."
