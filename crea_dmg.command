#!/bin/bash
# Da eseguire sul Mac, una volta. Crea l'app e il file LDO_Trascrizione_Live.dmg.
cd "$(dirname "$0")" || exit 1
BUILD="$PWD/build"
APP="$BUILD/LDO Trascrizione Live.app"
DMG="$PWD/LDO_Trascrizione_Live.dmg"
rm -rf "$BUILD" "$DMG"; mkdir -p "$BUILD"
osacompile -o "$APP" "LDO Trascrizione Live.applescript" || { echo "Errore nella creazione dell'app"; read -r -p "Invio..."; exit 1; }
cp avvia.sh live_transcribe.py "$APP/Contents/Resources/"
chmod +x "$APP/Contents/Resources/avvia.sh"
if [ -f icona.png ]; then
  ICONSET="$BUILD/icona.iconset"; mkdir -p "$ICONSET"
  for s in 16 32 128 256 512; do
    sips -z $s $s icona.png --out "$ICONSET/icon_${s}x${s}.png" >/dev/null
    sips -z $((s*2)) $((s*2)) icona.png --out "$ICONSET/icon_${s}x${s}@2x.png" >/dev/null
  done
  iconutil -c icns "$ICONSET" -o "$APP/Contents/Resources/applet.icns"
fi
# osacompile mette un'icona predefinita in Assets.car e la cita in CFBundleIconName: macOS la preferisce
# ad applet.icns, quindi l'icona personalizzata non si vede. La togliamo e rifirmiamo l'app.
rm -f "$APP/Contents/Resources/Assets.car"
/usr/libexec/PlistBuddy -c "Delete :CFBundleIconName" "$APP/Contents/Info.plist" 2>/dev/null
codesign --force --deep --sign - "$APP" 2>/dev/null
touch "$APP"
xattr -cr "$APP" 2>/dev/null
STAGE="$BUILD/dmg"; mkdir -p "$STAGE"
cp -R "$APP" "$STAGE/"; ln -s /Applications "$STAGE/Applicazioni"
hdiutil create -volname "LDO Trascrizione Live" -srcfolder "$STAGE" -ov -format UDZO "$DMG" && echo "Creato: $DMG"
read -r -p "Invio per chiudere..."
