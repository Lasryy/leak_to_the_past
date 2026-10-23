# Leak To The Past : portage JavaScript pour GitHub Pages

## Séparation des sources

| Branche | Rôle |
| --- | --- |
| `master` | Jeu original Python + Pygame, README public |
| `port/javascript` | Portage JavaScript pur, source de la démo navigateur |
| `webversion` | Sortie statique générée automatiquement, servie par GitHub Pages |

Le portage JavaScript n'a pas besoin d'être fusionné dans master.
L'ancienne publication Pygbag sur master a été désactivée.
La PR initiale ciblant master doit être fermée sans fusion.

## Paramètres GitHub Pages

Dans `Settings → Pages → Build and deployment` :
- Source : **Deploy from a branch**
- Branch : **webversion**
- Folder : **/(root)**
- Cliquer sur **Save**

Adresse attendue : https://lasryy.github.io/leak_to_the_past/

Attention : le réglage Pages lui-même est manuel.
Le workflow ne le modifie pas.

## Publication autonome

Chaque push sur `port/javascript` déclenche
`.github/workflows/deploy-browser.yml`. Il vérifie la syntaxe,
exécute les tests, construit le site dans `dist/`, puis pousse
uniquement le contenu de `dist/` vers `webversion`.

La compilation se fait sans CDN ni WebAssembly : JS natif,
Canvas 2D et HTMLAudio.

Un push sur `master` lance seulement le contrôle syntaxique Python
et ne publie jamais Pygbag ni le portage JavaScript.

## Tester localement

Prérequis : Node 22+ et Python 3 facultatif pour le serveur HTTP.

```sh
git switch port/javascript
npm run check
cd dist
python -m http.server 8000
```

Ouvrir http://localhost:8000. Ne pas utiliser `file://`.

## Contrôles

- ZQSD / WASD / flèches : déplacement
- Clic gauche lorsque le personnage est immobile : tir
- Espace : commencer/rejouer
- + / - : volume général (raccourci clavier)
- Curseurs Musique et SFX : volumes indépendants, mémorisés localement
- Précédent / Suivant : choisir une des six musiques OGG
- La piste suivante est lancée automatiquement à la fin d'une musique

## Limites et vérifications manuelles

Vérifier une partie réelle sur Chrome, Edge et Firefox avant
de considérer la fidélité validée. Comparer avec le jeu Python :
progression des ennemis à 30/60/90/120 s, collisions, recharge
avec sacrifice d'un cœur, effets visuels, sons, game over.

La conversion reproduit les principales mécaniques, mais le brouillard
Canvas et les flashes des ennemis ne sont pas pixel-identiques à Pygame.
Pas d'interface tactile prévue dans le projet original.

Les tests automatisés vérifient la logique et la construction ; ils ne
remplacent pas les essais interactifs sur de vrais navigateurs.
