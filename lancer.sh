#!/usr/bin/env bash
set -e

echo ""
echo "  ╔═══════════════════════════════════╗"
echo "  ║          ASTYRIA — D&D 5e         ║"
echo "  ║      Lancement du serveur MJ      ║"
echo "  ╚═══════════════════════════════════╝"
echo ""

# Vérification Python
if ! command -v python3 &>/dev/null; then
    echo "[ERREUR] Python 3 n'est pas installé."
    echo "Sur Mac : brew install python3"
    echo "Sur Linux : sudo apt install python3"
    exit 1
fi

# Ouvrir le navigateur après le démarrage
(sleep 1.5 && {
    URL="http://localhost:8000/app/creer.html"
    if command -v xdg-open &>/dev/null; then
        xdg-open "$URL"
    elif command -v open &>/dev/null; then
        open "$URL"
    fi
}) &

echo "Démarrage du serveur sur http://localhost:8000"
echo "Appuyez sur Ctrl+C pour arrêter."
echo ""

# Se placer à la racine du projet
cd "$(dirname "$0")"
python3 server.py
