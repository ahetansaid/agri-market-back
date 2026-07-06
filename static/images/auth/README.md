# Images de fond pour les pages d'authentification

Les pages login / password-reset / activation utilisent un panel visuel
sur la moitie gauche. L'image de fond est referencee par CSS via
`data-bg="<nom>"` dans le template, qui resout vers ce dossier.

## Fichiers attendus

| Nom local              | Theme suggere                  | Pages qui l'utilisent           |
| ---------------------- | ------------------------------ | ------------------------------- |
| `auth-harvest.jpg`     | Recolte / cereales africaines  | login, email_sent, reset complete |
| `auth-livestock.jpg`   | Elevage (vaches, chevres)      | register                        |
| `auth-market.jpg`      | Marche local, etals colores    | (reserve) activation             |
| `auth-field.jpg`       | Champs cultives vue large      | password reset (toutes etapes), activation_invalid |

## Sources recommandees (Pexels — usage commercial libre)

Tape ces requetes sur https://www.pexels.com :

1. **auth-harvest.jpg** :
   - "african farmer harvest"
   - "smallholder farmer Africa"
   - "corn harvest Africa"
   - Exemple : https://www.pexels.com/fr-fr/video/36706953/ (extract une frame)

2. **auth-livestock.jpg** :
   - "African cattle herders"
   - "livestock Sahel"
   - "goat farming Africa"

3. **auth-market.jpg** :
   - "African market women"
   - "produce market West Africa"
   - "local market Ghana / Kenya"

4. **auth-field.jpg** :
   - "African farmland aerial"
   - "cassava field"
   - "rice paddies Africa"

## Format & optimisation recommandes

- Resolution : **1920x2400** (portrait) — l'image est affichee plein
  ecran sur la moitie gauche du viewport
- Format : **WebP** prefere (50% plus petit que JPG), fallback JPG
- Compression : viser **150-250 Ko** par image

Commande ffmpeg / cwebp :

```bash
# JPG -> WebP optimise
cwebp -q 80 -resize 1920 2400 source.jpg -o auth-harvest.webp

# JPG optimise (fallback)
magick source.jpg -resize 1920x2400^ -gravity center -extent 1920x2400 \
       -quality 82 -strip auth-harvest.jpg
```

## Si une image manque

Le CSS contient un fallback gradient vert+ambre qui s'affiche
automatiquement. Le site reste presentable mais perd l'effet
"premium" de la photo.

## Sources alternatives africaines

- https://nappy.co/ — banque photo dediee personnes noires
- https://blackillustrations.com/ — illustrations africaines
- A terme : commissionner un photographe local (~20-30 photos cles)
