#!/usr/bin/env python3
"""Prépare un sprite d'export pour le runtime : redimensionne et encode en WebP.

Un export de DCC arrive en PNG haute définition, souvent bien plus grand que ce
que le jeu affiche. Ce script le ramène à sa taille utile et l'encode au format
runtime par défaut du projet.

Deux points qui ne s'improvisent pas, tous deux mesurés :

  ALPHA PRÉMULTIPLIÉ AU REDIMENSIONNEMENT
  Réduire du RGBA brut fait entrer la couleur des pixels transparents — souvent
  du noir — dans la moyenne des pixels voisins, et cerne le sujet d'un liseré
  sombre. On multiplie donc chaque canal par l'alpha avant, on divise après.

  `exact=True` À L'ENCODAGE
  Sans lui, l'encodeur WebP réécrit librement le RGB sous les pixels
  transparents. Mesuré sur un autre asset du jeu : la luminance moyenne y
  passait de 16 à 81, et cette bouillie bavait dans le filtrage bilinéaire au
  moindre agrandissement, salissant tout le contour.

    python tooling/assets/optimise-sprite.py \\
        --source apps/<app>/static/assets/sprites/x/y.png --width 384

Le fichier source n'est pas supprimé : c'est au dossier `source-assets/` de le
conserver, et au checker d'assets de signaler un doublon runtime.
"""

import argparse
import os

from PIL import Image


def resize_premultiplied(image: Image.Image, size: tuple) -> Image.Image:
    """Réduit sans liseré sombre sur les bords transparents."""
    red, green, blue, alpha = image.split()
    alpha_bytes = alpha.tobytes()

    def premultiply(channel):
        return Image.frombytes(
            "L",
            channel.size,
            bytes((c * a) // 255 for c, a in zip(channel.tobytes(), alpha_bytes)),
        )

    small = Image.merge(
        "RGBA", (premultiply(red), premultiply(green), premultiply(blue), alpha)
    ).resize(size, Image.LANCZOS)

    small_alpha_bytes = small.getchannel("A").tobytes()

    def unpremultiply(channel):
        return Image.frombytes(
            "L",
            channel.size,
            bytes(
                min(255, (c * 255) // a) if a else 0
                for c, a in zip(channel.tobytes(), small_alpha_bytes)
            ),
        )

    return Image.merge(
        "RGBA",
        (
            unpremultiply(small.getchannel("R")),
            unpremultiply(small.getchannel("G")),
            unpremultiply(small.getchannel("B")),
            small.getchannel("A"),
        ),
    )


def main():
    parser = argparse.ArgumentParser(description="Prépare un sprite pour le runtime")
    parser.add_argument("--source", required=True, help="fichier image source")
    parser.add_argument("--width", type=int, required=True, help="largeur cible, en pixels")
    parser.add_argument("--out", help="fichier produit (défaut : source en .webp)")
    parser.add_argument("--quality", type=int, default=92, help="qualité WebP (0-100)")
    args = parser.parse_args()

    image = Image.open(args.source).convert("RGBA")
    height = max(1, round(image.height * args.width / image.width))
    small = resize_premultiplied(image, (args.width, height))

    out = args.out or os.path.splitext(args.source)[0] + ".webp"
    small.save(out, "WEBP", quality=args.quality, method=6, exact=True)

    before = os.path.getsize(args.source) / 1024
    after = os.path.getsize(out) / 1024
    print(
        f"{os.path.basename(args.source):16} {image.width}x{image.height} {before:7.0f} Ko"
        f"  ->  {args.width}x{height} {after:7.0f} Ko   ({after / before * 100:.0f} %)"
    )


if __name__ == "__main__":
    main()
