import os
import json
import re
import socket
import shutil
from http.server import SimpleHTTPRequestHandler, HTTPServer

PORT = 8000
CAMPAIGNS_DIR = 'campaigns'

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def slugify(name):
    slug = name.lower()
    slug = re.sub(r'[àáâãäå]', 'a', slug)
    slug = re.sub(r'[èéêë]', 'e', slug)
    slug = re.sub(r'[ìíîï]', 'i', slug)
    slug = re.sub(r'[òóôõö]', 'o', slug)
    slug = re.sub(r'[ùúûü]', 'u', slug)
    slug = re.sub(r'[ç]', 'c', slug)
    slug = re.sub(r'[^a-z0-9]', '_', slug)
    slug = re.sub(r'_+', '_', slug).strip('_')
    return slug or 'campagne'

class JDRRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

    def log_message(self, format, *args):
        pass  # Silence les logs HTTP de base

    def do_GET(self):
        if self.path == '/api/campaigns' or self.path.startswith('/api/campaigns?'):
            self.handle_list_campaigns()
        else:
            super().do_GET()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_POST(self):
        path = self.path.split('?')[0]

        # POST /api/campaigns → créer une campagne
        if path == '/api/campaigns':
            self.handle_create_campaign()

        # POST /api/campaigns/{id}/... → actions sur une campagne
        elif path.startswith('/api/campaigns/'):
            parts = path[len('/api/campaigns/'):].split('/')
            if len(parts) < 2:
                self.send_error(400, "Endpoint incomplet")
                return
            campaign_id = parts[0]
            action = '/'.join(parts[1:])
            self.handle_campaign_action(campaign_id, action)
        else:
            self.send_error(404, "Endpoint introuvable")

    # ── Listage des campagnes ────────────────────────────────────────
    def handle_list_campaigns(self):
        campaigns = []
        if os.path.isdir(CAMPAIGNS_DIR):
            for cid in sorted(os.listdir(CAMPAIGNS_DIR)):
                meta_path = os.path.join(CAMPAIGNS_DIR, cid, 'meta.json')
                if os.path.isfile(meta_path):
                    with open(meta_path, 'r', encoding='utf-8') as f:
                        campaigns.append(json.load(f))
        self.json_response(200, campaigns)

    # ── Création d'une campagne ──────────────────────────────────────
    def handle_create_campaign(self):
        data = self.read_json_body()
        if not data:
            return
        name = data.get('name', '').strip()
        if not name:
            self.send_error(400, "Nom de campagne requis")
            return

        base = slugify(name)
        cid = base
        i = 2
        while os.path.exists(os.path.join(CAMPAIGNS_DIR, cid)):
            cid = f"{base}_{i}"; i += 1

        campaign_path = os.path.join(CAMPAIGNS_DIR, cid)
        os.makedirs(os.path.join(campaign_path, 'personnages'), exist_ok=True)
        os.makedirs(os.path.join(campaign_path, 'cartes'), exist_ok=True)
        os.makedirs(os.path.join(campaign_path, 'bibliotheque'), exist_ok=True)
        os.makedirs(os.path.join(campaign_path, 'background'), exist_ok=True)

        meta = { 'id': cid, 'name': name, 'description': data.get('description', ''), 'createdAt': data.get('createdAt', '') }
        self.write_json(os.path.join(campaign_path, 'meta.json'), meta)
        self.write_json(os.path.join(campaign_path, 'personnages', 'liste.json'), [])
        self.write_json(os.path.join(campaign_path, 'cartes', 'cartes.json'), [])
        self.write_json(os.path.join(campaign_path, 'bibliotheque', 'bibliotheque.json'), [])
        self.write_json(os.path.join(campaign_path, 'pnj.json'), [])

        print(f"  ✨ Campagne créée : {name} [{cid}]")
        self.json_response(200, meta)

    # ── Actions sur une campagne ─────────────────────────────────────
    def handle_campaign_action(self, cid, action):
        campaign_path = os.path.join(CAMPAIGNS_DIR, cid)
        if not os.path.isdir(campaign_path):
            self.send_error(404, f"Campagne '{cid}' introuvable")
            return

        data = self.read_json_body()
        if data is None:
            return

        # Mise à jour des métadonnées
        if action == 'update-meta':
            meta_path = os.path.join(campaign_path, 'meta.json')
            existing = {}
            if os.path.isfile(meta_path):
                with open(meta_path, 'r', encoding='utf-8') as f:
                    existing = json.load(f)
            existing.update({ k: v for k, v in data.items() if k != 'id' })
            self.write_json(meta_path, existing)
            print(f"  📝 Meta mise à jour : {cid}")
            self.json_response(200, {"status": "ok"})

        # Sauvegarder un personnage joueur
        elif action == 'save-character':
            char_id = data.get('id')
            if not char_id:
                self.send_error(400, "ID personnage manquant"); return
            char_dir = os.path.join(campaign_path, 'personnages', char_id)
            os.makedirs(char_dir, exist_ok=True)
            self.write_json(os.path.join(char_dir, 'info.json'), data)
            # Mettre à jour liste.json
            liste_path = os.path.join(campaign_path, 'personnages', 'liste.json')
            liste = self.read_json_file(liste_path, [])
            if char_id not in liste:
                liste.append(char_id)
                self.write_json(liste_path, liste)
            print(f"  ⚡ [{cid}] Personnage sauvegardé : {char_id}")
            self.json_response(200, {"status": "ok"})

        # Supprimer un personnage joueur
        elif action == 'delete-character':
            char_id = data.get('id')
            if not char_id:
                self.send_error(400, "ID personnage manquant"); return
            char_dir = os.path.join(campaign_path, 'personnages', char_id)
            if os.path.isdir(char_dir):
                shutil.rmtree(char_dir)
            liste_path = os.path.join(campaign_path, 'personnages', 'liste.json')
            liste = self.read_json_file(liste_path, [])
            if char_id in liste:
                liste.remove(char_id)
                self.write_json(liste_path, liste)
            print(f"  🗑️  [{cid}] Personnage supprimé : {char_id}")
            self.json_response(200, {"status": "ok"})

        # Sauvegarder les PNJ / Monstres (tableau complet)
        elif action == 'save-pnj':
            self.write_json(os.path.join(campaign_path, 'pnj.json'), data)
            print(f"  👹 [{cid}] PNJ sauvegardés")
            self.json_response(200, {"status": "ok"})

        # Sauvegarder les cartes
        elif action == 'save-maps':
            self.write_json(os.path.join(campaign_path, 'cartes', 'cartes.json'), data)
            print(f"  🗺️  [{cid}] Cartes sauvegardées")
            self.json_response(200, {"status": "ok"})

        # Sauvegarder la bibliothèque
        elif action == 'save-bibliotheque':
            self.write_json(os.path.join(campaign_path, 'bibliotheque', 'bibliotheque.json'), data)
            print(f"  📚 [{cid}] Bibliothèque sauvegardée")
            self.json_response(200, {"status": "ok"})

        # Upload d'une image (base64)
        elif action == 'upload-image':
            filename = data.get('filename', 'image.png')
            subfolder = data.get('subfolder', 'cartes')
            b64 = data.get('data', '')
            if not b64:
                self.send_error(400, "Données image manquantes"); return
            import base64
            folder = os.path.join(campaign_path, subfolder)
            os.makedirs(folder, exist_ok=True)
            filepath = os.path.join(folder, filename)
            img_data = base64.b64decode(b64.split(',')[-1])
            with open(filepath, 'wb') as f:
                f.write(img_data)
            relative_path = f"campaigns/{cid}/{subfolder}/{filename}"
            print(f"  🖼️  [{cid}] Image uploadée : {relative_path}")
            self.json_response(200, {"status": "ok", "path": relative_path})

        # Supprimer la campagne entière
        elif action == 'delete':
            shutil.rmtree(campaign_path)
            print(f"  🗑️  Campagne supprimée : {cid}")
            self.json_response(200, {"status": "ok"})

        else:
            self.send_error(404, f"Action inconnue : {action}")

    # ── Helpers ──────────────────────────────────────────────────────
    def read_json_body(self):
        try:
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length)
            return json.loads(body.decode('utf-8'))
        except Exception as e:
            self.send_error(400, f"JSON invalide : {e}")
            return None

    def read_json_file(self, path, default):
        if os.path.isfile(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return default

    def write_json(self, path, data):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def json_response(self, code, data):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

# ── Démarrage ────────────────────────────────────────────────────────
if __name__ == '__main__':
    os.makedirs(CAMPAIGNS_DIR, exist_ok=True)
    local_ip = get_local_ip()

    print("=" * 65)
    print("         SERVEUR ASTYRIA — MULTI-CAMPAGNES — DÉMARRÉ          ")
    print("=" * 65)
    print(f"\n  IP Réseau Local : {local_ip}:{PORT}")
    print(f"\n  CRÉATEUR DE CAMPAGNES (MJ) :")
    print(f"    → http://{local_ip}:{PORT}/app/creer.html")
    print(f"\n  JOUER (sélection de campagne) :")
    print(f"    → http://{local_ip}:{PORT}/app/jouer.html")
    print(f"\n  CAMPAGNES EXISTANTES :")

    if os.path.isdir(CAMPAIGNS_DIR):
        found = False
        for cid in sorted(os.listdir(CAMPAIGNS_DIR)):
            meta_path = os.path.join(CAMPAIGNS_DIR, cid, 'meta.json')
            if os.path.isfile(meta_path):
                with open(meta_path, 'r', encoding='utf-8') as f:
                    meta = json.load(f)
                print(f"    • {meta.get('name', cid):<25} → http://{local_ip}:{PORT}/app/jouer.html?campaign={cid}&role=mj")
                found = True
        if not found:
            print("    (aucune campagne — utilisez creer.html pour en créer une)")

    print("\n" + "=" * 65 + "\n")

    server = HTTPServer(('0.0.0.0', PORT), JDRRequestHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServeur arrêté.")