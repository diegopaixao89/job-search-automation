# gerar_icone.py — gera icone.ico para o app Automação de Vagas
import math
from PIL import Image, ImageDraw

def desenhar_icone(size):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    s = size

    # ── Fundo: círculo com gradiente simulado (duas camadas) ─────────────────
    # Sombra externa
    d.ellipse([s*0.04, s*0.06, s*0.96, s*0.98], fill=(8, 14, 26, 200))
    # Fundo principal (azul escuro do app)
    d.ellipse([s*0.02, s*0.02, s*0.98, s*0.98], fill=(13, 21, 39, 255))
    # Brilho interno sutil (arco superior)
    d.ellipse([s*0.06, s*0.06, s*0.94, s*0.94], fill=(17, 29, 53, 255))
    # Borda azul
    d.ellipse([s*0.02, s*0.02, s*0.98, s*0.98],
              outline=(59, 130, 246, 255), width=max(2, int(s*0.03)))

    # ── Maleta / briefcase ───────────────────────────────────────────────────
    # Proporções relativas ao tamanho
    bx1 = s * 0.20
    bx2 = s * 0.80
    by1 = s * 0.38
    by2 = s * 0.78
    br  = max(3, int(s * 0.06))   # raio dos cantos

    # Corpo da maleta
    d.rounded_rectangle([bx1, by1, bx2, by2], radius=br,
                         fill=(37, 99, 235, 255),
                         outline=(96, 165, 250, 255),
                         width=max(1, int(s * 0.025)))

    # Alça da maleta
    hw = s * 0.22   # largura da alça
    hh = s * 0.10   # altura da alça
    hx1 = s/2 - hw/2
    hx2 = s/2 + hw/2
    hy1 = by1 - hh
    hy2 = by1 + s*0.015
    d.rounded_rectangle([hx1, hy1, hx2, hy2],
                         radius=max(2, int(s * 0.04)),
                         fill=(0, 0, 0, 0),
                         outline=(96, 165, 250, 255),
                         width=max(2, int(s * 0.03)))

    # Linha central horizontal da maleta
    ly = (by1 + by2) / 2
    d.rectangle([bx1 + s*0.02, ly - s*0.015,
                 bx2 - s*0.02, ly + s*0.015],
                fill=(30, 58, 95, 255))

    # Fivela central
    fsize = s * 0.09
    fx1 = s/2 - fsize/2
    fx2 = s/2 + fsize/2
    fy1 = ly - fsize/2
    fy2 = ly + fsize/2
    d.rounded_rectangle([fx1, fy1, fx2, fy2],
                         radius=max(1, int(s*0.02)),
                         fill=(96, 165, 250, 255))

    # ── Raio / relâmpago (automação) no canto inferior direito ───────────────
    bolt_points = [
        (s*0.62, s*0.44),
        (s*0.52, s*0.61),
        (s*0.59, s*0.61),
        (s*0.49, s*0.78),
        (s*0.68, s*0.57),
        (s*0.60, s*0.57),
        (s*0.72, s*0.44),
    ]
    d.polygon(bolt_points, fill=(250, 204, 21, 255))   # amarelo dourado
    # contorno fino para dar definição
    d.polygon(bolt_points, outline=(251, 191, 36, 200), width=max(1, int(s*0.015)))

    return img


def gerar():
    tamanhos = [16, 24, 32, 48, 64, 128, 256]
    imgs = [desenhar_icone(t) for t in tamanhos]

    # Salva .ico com todos os tamanhos
    caminho = "icone.ico"
    imgs[0].save(caminho, format="ICO",
                 sizes=[(t, t) for t in tamanhos],
                 append_images=imgs[1:])
    print(f"Icone gerado: {caminho}")

    # Salva PNG 256 para preview
    imgs[-1].save("icone_preview.png")
    print("Preview: icone_preview.png")


if __name__ == "__main__":
    gerar()
