# Leak To The Past : version navigateur JavaScript

Ce port vit sur la branche port/javascript. Le jeu Python d'origine, la branche master
et le site webversion ne sont pas modifies tant que la PR n'est pas fusionnee.

## Architecture

- JavaScript ES modules + HTML Canvas 2D + HTMLAudio
- Pas de dependance npm, de CDN, de moteur externe ou de WebAssembly
- Resolution interne 1280 x 720 (adaptee par CSS a la taille disponible)
- Fichiers source dans web/ et ressources Python reutilisees depuis assets/
- Build de publication autonome dans dist/

## Commandes

Prérequis : Node.js 22+.

    npm test
    npm run check
    npm run build

Pour essayer le build sur votre machine :

    cd dist
    python -m http.server 8000

Ouvrir http://localhost:8000, pas un fichier HTML ouvert avec file://.

## Contrôles

- ZQSD / WASD / fleches : deplacement en 8 directions
- Clic gauche : tir uniquement lorsque le personnage est immobile
- Espace : demarrer / recommencer
- + et - : volume

## Publication GitHub Pages

Le workflow verify-javascript.yml s'execute sur les commits de port/javascript,
sans publier le jeu. Apres validation manuelle et fusion sur master, deploy.yml
teste le code, construit dist/, puis publie sur la branche webversion.

Conserver la source GitHub Pages actuelle (webversion) dans les reglages du depot.
Les chemins d'assets sont relatifs et supportent le sous-chemin /leak_to_the_past/.

## Parite et validations

Sont portes : six types d'ennemis, progres temporel, IA bleu et violet, degats,
collision sprites/mask, score, regeneration d'ennemis, trois coeurs,
blood-reload, drops, flaques, anims 8 directions, HUD, sons OGG, musique,
camera, brouillard et menus.

Avant fusion : comparer une partie Python et JavaScript a froid, tester
Chrome/Firefox/Edge et verifier la console. Les effets du brouillard
(SDL BLEND_RGBA_SUB) et flash blanc (SDL BLEND_ADD) ont un rendu Canvas
approximatif. Les variations de hasard peuvent differer. Aucun test
complet en navigateur n'est encore declare comme reussi.

Le port ne vise pas le tactile : les controles de depart sont clavier/souris.
