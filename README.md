
# ⚔ ASTYRIA — Compagnon de Table pour Jeux de Rôle

> Application web locale pour la gestion de campagnes de jeu de rôle.  
> Fonctionne entièrement en réseau local — aucune connexion internet requise.

---

## ═══ LANCEMENT DU SERVEUR ═══

### Prérequis

- Python 3.7 ou supérieur
- Un navigateur moderne (Chrome, Firefox, Edge)

### Démarrer

**Sur macOS / Linux**
```bash
./lancer.sh
# ou
python3 server.py
```

**Sur Windows**
```
lancer.bat
# ou
python server.py
```

**Port personnalisé** (défaut : 8000)
```bash
python3 server.py 9000
```

Le terminal affiche les adresses d'accès au démarrage :

```
Accès local   : http://localhost:8000
Accès réseau  : http://192.168.x.x:8000
Interface MJ  : http://192.168.x.x:8000?role=mj
```

Les joueurs accèdent depuis leur téléphone ou ordinateur via l'adresse réseau.

---

## ═══ RÔLES ═══

### Maître de Jeu

Accès via `?role=mj` dans l'URL.  
Authentification par mot de passe à la première connexion.

### Joueur

Accès via un QR code généré dans la fiche MJ, ou directement via :
```
http://192.168.x.x:8000?campaign=<id>&char=<id>
```

---

## ═══ INTERFACE MJ ═══

### Campagnes

- Créer, sélectionner et supprimer des campagnes depuis le panneau latéral
- Chaque campagne est indépendante (personnages, bibliothèque, PNJ, cartes)

### Fiche personnage (vue MJ)

Chaque personnage est affiché sous forme de carte déroulante.

| Section | Contenu |
|---|---|
| **Santé** | Barre HP avec boutons +/-1 / +/-5 |
| **Bourse** | Pièces d'or, d'argent et de bronze — ajustables |
| **Objets** | Inventaire avec compteur si plusieurs exemplaires |
| **Capacités** | Compétences spéciales du personnage |
| **Sorts** | Sorts avec emplacements disponibles |
| **Quêtes** | Objectifs en cours |

**Renouveler les sorts** : un bouton `↺ Renouveler` apparaît dans la section Sorts. Il remet tous les emplacements à zéro pour ce personnage. Le bouton devient violet quand des sorts ont été utilisés.

**Glisser-déposer** : n'importe quel objet de la bibliothèque peut être glissé directement sur la fiche d'un personnage. L'objet est classé automatiquement dans la bonne section selon son type.

### Bibliothèque MJ

Panneau latéral droit.  
Filtres disponibles : Tout / Objets / Capacités / Sorts / Quêtes  
Recherche par nom ou description.  
Les éléments de la bibliothèque peuvent être glissés sur les fiches.

### PNJ

Création et affichage de personnages non joueurs, visibles en mode joueur si le MJ le décide.

### Cartes

Importation d'images de cartes. Sélection de la carte active visible par les joueurs.

---

## ═══ INTERFACE JOUEUR ═══

La vue joueur est en lecture seule, mise à jour automatiquement toutes les 2 secondes.

### Onglets disponibles

**Fiche** — Caractéristiques principales  
Traits (For, Dex, Con, Int, Sag, Cha), points de compétence, Classe d'Armure, description du personnage.

**Quêtes** — Objectifs actifs

**Équip.** — Inventaire et bourse  
Les objets en plusieurs exemplaires affichent un badge `×N`.  
La bourse est visible si le MJ y a ajouté des pièces.

**Capacités** — Compétences et sorts  
- Les capacités sont listées avec leur description dépliable
- Les sorts affichent leurs emplacements sous forme de points  
- Bouton **Lancer** quand un sort est disponible  
- Sort épuisé (tous les emplacements utilisés) : carte grisée, label *épuisé*, bouton masqué

**Cartes** — Carte de la zone courante, définie par le MJ

---

## ═══ BIBLIOTHÈQUE ═══

Fichier global : `bibliotheque/bibliotheque.json`  
Chaque campagne peut aussi avoir sa propre bibliothèque locale dans `campaigns/<id>/bibliotheque/`.

Format d'un objet :
```json
{
  "name": "Épée longue",
  "type": "inventory",
  "description": "Une lame à deux tranchants, équilibrée pour le combat."
}
```

Format d'un sort :
```json
{
  "name": "Boule de feu",
  "type": "spells",
  "level": 3,
  "slots": 2,
  "description": "Projette une sphère enflammée de 6m de rayon."
}
```

Types disponibles : `inventory` · `skills` · `spells` · `quests`

---

## ═══ STRUCTURE DES FICHIERS ═══

```
Astyria_merged/
├── index.html              Application complète (interface + logique)
├── server.py               Serveur HTTP local avec API REST
├── lancer.sh               Script de lancement macOS/Linux
├── lancer.bat              Script de lancement Windows
├── bibliotheque/
│   └── bibliotheque.json   Bibliothèque globale partagée entre campagnes
└── campaigns/
    └── <campaign_id>/
        ├── personnages/
        │   └── <char_id>/
        │       └── info.json   Données complètes du personnage
        ├── pnj.json            PNJ de la campagne
        ├── cartes/
        │   └── cartes.json     Références aux cartes importées
        └── bibliotheque/
            └── bibliotheque.json  Bibliothèque locale (optionnelle)
```

---

## ═══ DONNÉES D'UN PERSONNAGE ═══

Le fichier `info.json` contient l'ensemble des données d'un personnage :

```json
{
  "id": "nom_du_personnage",
  "name": "Nom affiché",
  "class": "Classe (Niveau N)",
  "avatar": "url ou chemin vers l'image",
  "ca": 14,
  "description": "Biographie ou notes.",
  "bars": [{ "id": "hp", "name": "Santé", "current": 30, "max": 30, "color": "..." }],
  "traits": [{ "name": "Force", "value": 14 }],
  "skillPoints": [{ "name": "Acrobaties", "value": 3 }],
  "wallet": { "gold": 10, "silver": 5, "bronze": 0 },
  "inventory": [{ "name": "Torche", "description": "Éclaire 6m." }],
  "skills":    [{ "name": "Esquive", "description": "..." }],
  "quests":    [{ "name": "Trouver l'artefact", "description": "..." }],
  "spells": [{
    "name": "Soin", "level": 1, "slots": 3,
    "usedSlots": 0, "available": true,
    "description": "Restaure 1d8+mod PV."
  }]
}
```

Seul le champ `bars[0]` est affiché comme barre de vie. Les barres supplémentaires sont ignorées dans l'interface.

---

## ═══ NOTES TECHNIQUES ═══

- Toutes les données sont sauvegardées en JSON sur le disque local, sans base de données
- Le MJ peut ouvrir plusieurs fiches simultanément ; l'état déroulé est préservé lors des mises à jour
- Les modifications du MJ (HP, bourse, sorts) sont sauvegardées à la volée sans rechargement de page
- La vue joueur se synchronise toutes les 2 secondes ; les descriptions dépliées restent ouvertes entre deux synchronisations
- La vue MJ se synchronise toutes les 5 secondes ; les sorts utilisés par les joueurs apparaissent grisés sans action requise du MJ
