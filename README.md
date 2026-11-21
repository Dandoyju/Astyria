# ⚔ Astyria — Compagnon de jeu D&D 5e

Application de gestion de campagne Donjons & Dragons 5e, avec fiches joueurs partageables sécurisées et outils statiques hébergés sur GitHub Pages.

---

## 🗺 Je suis Maître de Jeu

### Démarrage rapide

**Windows** → double-clic sur `lancer.bat`  
**Mac / Linux** → double-clic sur `lancer.sh` (ou `bash lancer.sh` dans un terminal)

Le serveur démarre sur `http://localhost:8000` et le navigateur s'ouvre automatiquement.

### Partager les fiches joueurs

1. Dans **Créer & Gérer**, ouvre un personnage
2. Définis un **mot de passe** dans la section "Lien joueur" (en bas du formulaire)
3. Clique sur **Générer le lien**
4. Envoie le lien à ton joueur (ou montre-lui le QR code)

Le lien pointe vers GitHub Pages — le joueur peut l'ouvrir depuis n'importe quel appareil, même entre les sessions, sans que ton serveur tourne.

**Sécurité** : les données sont chiffrées avec AES-GCM (256 bits, clé dérivée via PBKDF2 avec 200 000 itérations). Même nous ne pouvons pas lire la fiche sans le mot de passe.

---

## 🧙 Je suis Joueur

### Pendant une session

Ton MJ t'a communiqué une adresse IP (ex : `192.168.1.42:8000`). Ouvre-la dans ton navigateur, sur le même réseau Wi-Fi.

### Entre les sessions

Ton MJ t'a envoyé un lien ? Ouvre-le sur **[astyria.github.io](#)**, entre ton mot de passe, et ta fiche s'affiche. Mets la page en favori.

---

## 🌐 Outils disponibles sans serveur (GitHub Pages)

| Outil | URL |
|-------|-----|
| Page d'accueil | `[repo].github.io/astyria/` |
| Fiche personnage | `[repo].github.io/astyria/docs/fiche.html#[chiffré]` |
| Lanceur de dés | `[repo].github.io/astyria/docs/des.html` |
| Référence sorts | `[repo].github.io/astyria/docs/reference/sorts.html` |
| Bestiaire | `[repo].github.io/astyria/docs/reference/monstres.html` |

---

## 📁 Structure du projet

```
astyria/
├── lancer.bat / lancer.sh   ← Démarrage serveur (double-clic)
├── server.py                ← Serveur local Python
├── app/
│   ├── creer.html           ← Interface MJ — gestion de campagne
│   └── jouer.html           ← Interface de session
├── docs/                    ← GitHub Pages (statique)
│   ├── index.html
│   ├── fiche.html           ← Fiche joueur sécurisée
│   ├── des.html             ← Lanceur de dés
│   ├── crypto.js            ← Chiffrement AES-GCM
│   └── reference/
│       ├── sorts.html
│       └── monstres.html
├── data/
│   └── classes_especes.json ← Races et classes D&D
└── campaigns/               ← Données de partie (non versionnées)
```

---

## ⚙ Configuration GitHub Pages

1. Pousse le dépôt sur GitHub
2. `Settings → Pages → Source : main, dossier /docs`
3. Mets à jour `GITHUB_PAGES_BASE` dans `app/creer.html` avec ton URL réelle

---

## 📋 Prérequis

- Python 3.8+ (pour le serveur local)
- Un navigateur moderne (Chrome, Firefox, Safari, Edge)
- Pas de dépendances supplémentaires

---

*Contenu non officiel. Astyria n'est pas affilié à Wizards of the Coast.*  
*Certains contenus sont sous licence [SRD 5.1](https://dnd.wizards.com/resources/systems-reference-document).*
