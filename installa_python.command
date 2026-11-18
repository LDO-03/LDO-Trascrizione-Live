#!/bin/bash
# Installa Python 3.11 se manca. Chiede la password dell'amministratore del Mac.
echo "Controllo Python 3.11..."
if [ -x /Library/Frameworks/Python.framework/Versions/3.11/bin/python3.11 ] || command -v python3.11 >/dev/null 2>&1; then
  echo "Python 3.11 è già installato."
elif command -v brew >/dev/null 2>&1; then
  echo "Installo Python 3.11 con Homebrew (può richiedere alcuni minuti)..."
  brew install python@3.11
else
  PKG="/tmp/python-3.11.9-macos11.pkg"
  echo "Scarico Python 3.11.9 da python.org..."
  curl -fL -o "$PKG" https://www.python.org/ftp/python/3.11.9/python-3.11.9-macos11.pkg || { echo "Download fallito."; read -r -p "Premi Invio per chiudere..."; exit 1; }
  echo "Installo Python 3.11.9: inserisci la password del Mac quando richiesta."
  sudo installer -pkg "$PKG" -target / || { echo "Installazione fallita."; read -r -p "Premi Invio per chiudere..."; exit 1; }
fi
echo
ls -l /Library/Frameworks/Python.framework/Versions/3.11/bin/python3.11 /usr/local/bin/python3.11 2>/dev/null
echo "Fatto. Ora riapri Trascrizione Live."
read -r -p "Premi Invio per chiudere..."
