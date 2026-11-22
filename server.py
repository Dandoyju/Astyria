#!/usr/bin/env python3
"""
Astyria - Serveur de campagne D&D
Lancez avec: python3 server.py [port]
"""

import json
import os
import sys
import shutil
import socket
import re
import unicodedata
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote
from pathlib import Path

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
CAMPAIGNS_DIR = 'campaigns'


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def slugify(name: str) -> str:
    """Convert a French campaign name to a safe folder slug."""
    nfkd = unicodedata.normalize('NFKD', name)
    ascii_str = nfkd.encode('ASCII', 'ignore').decode('ASCII')
    ascii_str = re.sub(r'[^\w\s-]', '', ascii_str).strip().lower()
    return re.sub(r'[\s_-]+', '_', ascii_str) or 'campagne'


def ensure_campaign_dirs(campaign_id: str):
    base = Path(CAMPAIGNS_DIR) / campaign_id
    for sub in ['personnages', 'cartes', 'bibliotheque']:
        (base / sub).mkdir(parents=True, exist_ok=True)
    cartes_json = base / 'cartes' / 'cartes.json'
    if not cartes_json.exists():
        cartes_json.write_text('[]', encoding='utf-8')
    pnj_json = base / 'pnj.json'
    if not pnj_json.exists():
        pnj_json.write_text('[]', encoding='utf-8')
    bib_json = base / 'bibliotheque' / 'bibliotheque.json'
    if not bib_json.exists():
        bib_json.write_text('[]', encoding='utf-8')
    liste_json = base / 'personnages' / 'liste.json'
    if not liste_json.exists():
        liste_json.write_text('[]', encoding='utf-8')


class AstyriaHandler(SimpleHTTPRequestHandler):

    def log_message(self, format, *args):
        pass  # silence default access log

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', len(body))
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)

    def send_ok(self, msg="ok"):
        self.send_json({"status": "ok", "message": msg})

    def send_error_json(self, code, msg):
        self.send_json({"status": "error", "message": msg}, status=code)

    def read_body(self):
        length = int(self.headers.get('Content-Length', 0))
        return self.rfile.read(length) if length else b''

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip('/')

        if path == '/api/campaigns':
            self.handle_list_campaigns()
        elif path == '/api/server-ip':
            self.send_json({"ip": get_local_ip(), "port": PORT})
        elif path == '/api/global-library':
            # Serve the global library directly via API (same file also served as static)
            lib_path = Path('bibliotheque/bibliotheque.json')
            if lib_path.exists():
                self.send_json(json.loads(lib_path.read_text(encoding='utf-8')))
            else:
                self.send_json([])
        else:
            # Serve static files with no-cache headers
            super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip('/')
        parts = path.strip('/').split('/')

        # POST /api/campaigns  → create
        if parts == ['api', 'campaigns']:
            self.handle_create_campaign()
            return

        # POST /api/campaigns/{id}/...
        if len(parts) >= 4 and parts[0] == 'api' and parts[1] == 'campaigns':
            campaign_id = unquote(parts[2])
            action = '/'.join(parts[3:])
            self.handle_campaign_action(campaign_id, action)
            return

        self.send_error_json(404, "Route not found")

    def handle_list_campaigns(self):
        base = Path(CAMPAIGNS_DIR)
        if not base.exists():
            self.send_json([])
            return
        campaigns = []
        for d in sorted(base.iterdir()):
            if not d.is_dir():
                continue
            meta_file = d / 'meta.json'
            if meta_file.exists():
                try:
                    meta = json.loads(meta_file.read_text(encoding='utf-8'))
                    meta['id'] = d.name
                    campaigns.append(meta)
                except Exception:
                    campaigns.append({'id': d.name, 'name': d.name, 'description': ''})
            else:
                campaigns.append({'id': d.name, 'name': d.name, 'description': ''})
        self.send_json(campaigns)

    def handle_create_campaign(self):
        try:
            data = json.loads(self.read_body())
        except Exception:
            self.send_error_json(400, "Invalid JSON")
            return
        name = data.get('name', '').strip()
        if not name:
            self.send_error_json(400, "Campaign name required")
            return

        # Create unique slug
        base_slug = slugify(name)
        slug = base_slug
        counter = 1
        while (Path(CAMPAIGNS_DIR) / slug).exists():
            slug = f"{base_slug}_{counter}"
            counter += 1

        ensure_campaign_dirs(slug)
        meta = {
            'id': slug,
            'name': name,
            'description': data.get('description', ''),
            'createdAt': data.get('createdAt', '')
        }
        (Path(CAMPAIGNS_DIR) / slug / 'meta.json').write_text(
            json.dumps(meta, ensure_ascii=False, indent=2), encoding='utf-8')
        self.send_json(meta)
        print(f"[Astyria] Campagne créée : {name} → {slug}/")

    def handle_campaign_action(self, campaign_id, action):
        # Sanitize campaign_id (no path traversal)
        if '..' in campaign_id or '/' in campaign_id:
            self.send_error_json(400, "Invalid campaign id")
            return

        base = Path(CAMPAIGNS_DIR) / campaign_id
        if not base.exists() and action not in ('delete',):
            self.send_error_json(404, f"Campaign '{campaign_id}' not found")
            return

        try:
            body = self.read_body()
            data = json.loads(body) if body else {}
        except Exception:
            data = {}

        if action == 'save-character':
            self.save_character(base, data)
        elif action == 'delete-character':
            self.delete_character(base, data)
        elif action == 'save-pnj':
            self.save_json_file(base / 'pnj.json', data)
            self.send_ok("PNJ sauvegardés")
        elif action == 'save-maps':
            self.save_json_file(base / 'cartes' / 'cartes.json', data)
            self.send_ok("Cartes sauvegardées")
        elif action == 'save-bibliotheque':
            self.save_json_file(base / 'bibliotheque' / 'bibliotheque.json', data)
            self.send_ok("Bibliothèque sauvegardée")
        elif action == 'update-meta':
            meta_path = base / 'meta.json'
            existing = {}
            if meta_path.exists():
                try:
                    existing = json.loads(meta_path.read_text(encoding='utf-8'))
                except Exception:
                    pass
            existing.update(data)
            self.save_json_file(meta_path, existing)
            self.send_ok("Méta mise à jour")
        elif action == 'save-global-library':
            lib_path = Path('bibliotheque/bibliotheque.json')
            lib_path.parent.mkdir(exist_ok=True)
            self.save_json_file(lib_path, data)
            self.send_ok("Bibliothèque commune sauvegardée")
        elif action == 'delete':
            if base.exists():
                shutil.rmtree(str(base))
                print(f"[Astyria] Campagne supprimée : {campaign_id}")
            self.send_ok("Campagne supprimée")
        elif action == 'upload-image':
            self.handle_upload_image(base, data)
        else:
            self.send_error_json(404, f"Unknown action: {action}")

    def save_character(self, base: Path, data: dict):
        char_id = data.get('id')
        if not char_id:
            self.send_error_json(400, "Character id required")
            return
        char_dir = base / 'personnages' / char_id
        char_dir.mkdir(parents=True, exist_ok=True)
        (char_dir / 'info.json').write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
        # Update liste.json
        liste_path = base / 'personnages' / 'liste.json'
        liste = []
        if liste_path.exists():
            try:
                liste = json.loads(liste_path.read_text(encoding='utf-8'))
            except Exception:
                pass
        if char_id not in liste:
            liste.append(char_id)
        liste_path.write_text(json.dumps(liste, ensure_ascii=False), encoding='utf-8')
        self.send_ok(f"Personnage '{char_id}' sauvegardé")

    def delete_character(self, base: Path, data: dict):
        char_id = data.get('id')
        if not char_id or '..' in char_id:
            self.send_error_json(400, "Invalid character id")
            return
        char_dir = base / 'personnages' / char_id
        if char_dir.exists():
            shutil.rmtree(str(char_dir))
        # Update liste.json
        liste_path = base / 'personnages' / 'liste.json'
        if liste_path.exists():
            try:
                liste = json.loads(liste_path.read_text(encoding='utf-8'))
                liste = [x for x in liste if x != char_id]
                liste_path.write_text(json.dumps(liste, ensure_ascii=False), encoding='utf-8')
            except Exception:
                pass
        self.send_ok(f"Personnage '{char_id}' supprimé")

    def save_json_file(self, path: Path, data):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

    def handle_upload_image(self, base: Path, data: dict):
        import base64
        filename  = data.get('filename', 'image.png')
        subfolder = data.get('subfolder', 'cartes')
        content   = data.get('content', '')
        if '..' in filename or '/' in filename:
            self.send_error_json(400, "Invalid filename")
            return
        dest_dir = base / subfolder
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / filename
        # Strip data: URI prefix if present
        if ',' in content:
            content = content.split(',', 1)[1]
        try:
            dest.write_bytes(base64.b64decode(content))
            rel_path = f"campaigns/{base.name}/{subfolder}/{filename}"
            self.send_json({"status": "ok", "path": rel_path})
        except Exception as e:
            self.send_error_json(500, str(e))

    def end_headers(self):
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()


if __name__ == '__main__':
    # Ensure campaigns directory exists
    Path(CAMPAIGNS_DIR).mkdir(exist_ok=True)

    local_ip = get_local_ip()
    print("=" * 55)
    print("  🎲  Astyria — Serveur de campagne D&D")
    print("=" * 55)
    print(f"  Accès local   : http://localhost:{PORT}")
    print(f"  Accès réseau  : http://{local_ip}:{PORT}")
    print(f"  Interface MJ  : http://{local_ip}:{PORT}?role=mj")
    print("=" * 55)
    print("  Ctrl+C pour arrêter le serveur")
    print()

    server = HTTPServer(('0.0.0.0', PORT), AstyriaHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[Astyria] Serveur arrêté.")
