#!/bin/bash
MARKER="$HOME/.config/.pulsaros-wallpaper-applied"
if [ -f "$MARKER" ]; then
    exit 0
fi

until qdbus org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript 'print("ready")' &>/dev/null; do
    sleep 0.5
done

plasma-apply-wallpaperimage /usr/share/wallpapers/PulsarYellow/contents/images/3840x2160.png

touch "$MARKER"
