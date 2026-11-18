#!/bin/bash
# Copia "LDO Trascrizione Live" in ~/Applications. Eseguire dopo crea_dmg.command.
cd "$(dirname "$0")" || exit 1
SRC="build/LDO Trascrizione Live.app"
mkdir -p "$HOME/Applications"
rm -rf "$HOME/Applications/Trascrizione Live.app" "$HOME/Applications/LDO Trascrizione Live.app"
cp -R "$SRC" "$HOME/Applications/" && xattr -cr "$HOME/Applications/LDO Trascrizione Live.app" 2>/dev/null
echo "Installata in ~/Applications. Aprila dal Launchpad o dal Finder."
read -r -p "Invio per chiudere..."
