"""
Generator identyfikacji wizualnej marki compound.pl (scripts/generate_brand_assets.py)
Tworzy:
1. assets/brand/logo-mark.svg & logo-mark-1024.png — Wektorowy sygnet (ikona)
2. assets/brand/logo-vector.svg & logo-horizontal-1920.png — Pełne poziome logo wektorowe SVG
3. assets/brand/avatar-profile.svg & avatar-profile-1080.png — Profilowe 1080x1080 px (Instagram, Gmail, X, LinkedIn)
4. assets/brand/avatar-gmail-circle.svg & avatar-gmail-circle-512.png — Okrągłe profilowe 512x512 px (Gmail / Google)
5. assets/brand/banner-social.svg & banner-social-1500x500.png — Baner w tle (X/Twitter, LinkedIn, YouTube)
6. assets/brand/poster-promo.svg & poster-instagram-1080x1350.png — Plakat / grafika na Instagram / Social Media
"""

import os
import fitz  # PyMuPDF

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRAND_DIR = os.path.join(BASE_DIR, "assets", "brand")
os.makedirs(BRAND_DIR, exist_ok=True)

# 1. Sygnet wektorowy SVG (kwadrat z bursztynową krzywą procentu składanego)
LOGO_MARK_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
  <rect width="512" height="512" rx="116" fill="#0E121A"/>
  <rect x="10" y="10" width="492" height="492" rx="106" fill="none" stroke="#E8A33D" stroke-opacity="0.30" stroke-width="4"/>
  <!-- Siatka analityczna w tle -->
  <line x1="96" y1="384" x2="416" y2="384" stroke="#ffffff" stroke-opacity="0.07" stroke-width="3"/>
  <line x1="96" y1="288" x2="416" y2="288" stroke="#ffffff" stroke-opacity="0.06" stroke-width="3" stroke-dasharray="10 10"/>
  <line x1="96" y1="192" x2="416" y2="192" stroke="#ffffff" stroke-opacity="0.06" stroke-width="3" stroke-dasharray="10 10"/>
  <!-- Poświata pod krzywą -->
  <path d="M 108 376 C 220 368, 296 290, 396 124" fill="none" stroke="#E8A33D" stroke-opacity="0.20" stroke-width="64" stroke-linecap="round"/>
  <!-- Krzywa wykładnicza (Procent Składany) -->
  <path d="M 108 376 C 220 368, 296 290, 396 124" fill="none" stroke="#E8A33D" stroke-width="38" stroke-linecap="round"/>
  <!-- Punkt szczytowy (kropka wzrostu) -->
  <circle cx="396" cy="124" r="24" fill="#34D399"/>
</svg>
"""

# 2. Pełne logo wektorowe SVG (poziome)
LOGO_VECTOR_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 980 280" width="980" height="280">
  <rect width="980" height="280" rx="36" fill="#0B0D12"/>
  <rect x="4" y="4" width="972" height="272" rx="32" fill="none" stroke="#ffffff" stroke-opacity="0.07" stroke-width="2"/>
  <!-- Ikona po lewej -->
  <g transform="translate(56, 52)">
    <rect width="176" height="176" rx="42" fill="#131722" stroke="#E8A33D" stroke-opacity="0.40" stroke-width="3"/>
    <path d="M 38 130 C 78 126, 104 98, 136 42" fill="none" stroke="#E8A33D" stroke-opacity="0.20" stroke-width="26" stroke-linecap="round"/>
    <path d="M 38 130 C 78 126, 104 98, 136 42" fill="none" stroke="#E8A33D" stroke-width="15" stroke-linecap="round"/>
    <circle cx="136" cy="42" r="9" fill="#34D399"/>
  </g>
  <!-- Logotyp tekstowy -->
  <text x="272" y="156" font-family="Helvetica Neue, Arial, sans-serif" font-size="96" font-weight="700" fill="#EDEDE9">compound</text>
  <text x="766" y="156" font-family="Courier New, monospace" font-size="56" font-weight="700" fill="#E8A33D">.pl</text>
  <text x="276" y="206" font-family="Helvetica Neue, Arial, sans-serif" font-size="22" font-weight="500" fill="#8B92A1" letter-spacing="4">RYNKI · GOSPODARKA · KAPITAŁ</text>
</svg>
"""

# 3. Avatar profilowy 1080x1080 (Instagram, X, LinkedIn, Gmail)
AVATAR_SQUARE_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1080 1080" width="1080" height="1080">
  <rect width="1080" height="1080" fill="#0B0D12"/>
  <!-- Okrąg prowadzący pod kadrowanie okrągłe na Gmailu/IG -->
  <circle cx="540" cy="540" r="470" fill="#0F131C" stroke="#E8A33D" stroke-opacity="0.22" stroke-width="4"/>
  <!-- Karta sygnetu -->
  <rect x="260" y="190" width="560" height="480" rx="105" fill="#141925" stroke="#E8A33D" stroke-opacity="0.32" stroke-width="4"/>
  <!-- Linie siatki -->
  <line x1="340" y1="560" x2="740" y2="560" stroke="#ffffff" stroke-opacity="0.08" stroke-width="4"/>
  <line x1="340" y1="430" x2="740" y2="430" stroke="#ffffff" stroke-opacity="0.07" stroke-width="4" stroke-dasharray="12 12"/>
  <line x1="340" y1="300" x2="740" y2="300" stroke="#ffffff" stroke-opacity="0.07" stroke-width="4" stroke-dasharray="12 12"/>
  <!-- Poświata i krzywa wykładnicza -->
  <path d="M 350 550 C 495 538, 590 430, 715 260" fill="none" stroke="#E8A33D" stroke-opacity="0.18" stroke-width="84" stroke-linecap="round"/>
  <path d="M 350 550 C 495 538, 590 430, 715 260" fill="none" stroke="#E8A33D" stroke-width="48" stroke-linecap="round"/>
  <circle cx="715" cy="260" r="32" fill="#34D399"/>
  <!-- Nazwa marki pod sygnetem (idealnie wyśrodkowana bez nakładania) -->
  <text x="485" y="795" text-anchor="middle" font-family="Helvetica Neue, Arial, sans-serif" font-size="82" font-weight="700" fill="#EDEDE9">compound</text>
  <text x="752" y="795" text-anchor="middle" font-family="Courier New, monospace" font-size="64" font-weight="700" fill="#E8A33D">.pl</text>
  <text x="540" y="862" text-anchor="middle" font-family="Helvetica Neue, Arial, sans-serif" font-size="24" font-weight="600" fill="#8B92A1" letter-spacing="6">MARKET INTELLIGENCE</text>
</svg>
"""

# 4. Okrągły Avatar Gmail / Google Workspace 512x512
AVATAR_CIRCLE_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
  <circle cx="256" cy="256" r="248" fill="#0E121A" stroke="#E8A33D" stroke-opacity="0.45" stroke-width="8"/>
  <line x1="120" y1="360" x2="392" y2="360" stroke="#ffffff" stroke-opacity="0.08" stroke-width="3"/>
  <line x1="120" y1="260" x2="392" y2="260" stroke="#ffffff" stroke-opacity="0.08" stroke-width="3" stroke-dasharray="8 8"/>
  <path d="M 130 350 C 225 342, 290 270, 376 136" fill="none" stroke="#E8A33D" stroke-opacity="0.20" stroke-width="62" stroke-linecap="round"/>
  <path d="M 130 350 C 225 342, 290 270, 376 136" fill="none" stroke="#E8A33D" stroke-width="36" stroke-linecap="round"/>
  <circle cx="376" cy="136" r="22" fill="#34D399"/>
</svg>
"""

# 5. Baner w tle 1500x500 (X/Twitter, LinkedIn, YouTube, Facebook)
BANNER_SOCIAL_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1500 500" width="1500" height="500">
  <rect width="1500" height="500" fill="#0B0D12"/>

  <!-- Siatka analityczna po prawej stronie -->
  <g opacity="0.16">
    <line x1="850" y1="80" x2="1420" y2="80" stroke="#ffffff" stroke-width="1"/>
    <line x1="850" y1="170" x2="1420" y2="170" stroke="#ffffff" stroke-width="1" stroke-dasharray="6 6"/>
    <line x1="850" y1="260" x2="1420" y2="260" stroke="#ffffff" stroke-width="1" stroke-dasharray="6 6"/>
    <line x1="850" y1="350" x2="1420" y2="350" stroke="#ffffff" stroke-width="1" stroke-dasharray="6 6"/>
    <line x1="850" y1="420" x2="1420" y2="420" stroke="#ffffff" stroke-width="1.5"/>
  </g>

  <!-- Duża bursztynowa krzywa wzrostu po prawej -->
  <path d="M 880 400 C 1060 392, 1210 300, 1380 105" fill="none" stroke="#E8A33D" stroke-opacity="0.18" stroke-width="32" stroke-linecap="round"/>
  <path d="M 880 400 C 1060 392, 1210 300, 1380 105" fill="none" stroke="#E8A33D" stroke-width="14" stroke-linecap="round"/>
  <circle cx="1380" cy="105" r="13" fill="#34D399"/>

  <!-- Pigułki notowań na wykresie -->
  <g transform="translate(940, 105)">
    <rect width="220" height="46" rx="23" fill="#141822" stroke="#E8A33D" stroke-opacity="0.35" stroke-width="1.5"/>
    <text x="24" y="29" font-family="Courier New, monospace" font-size="18" font-weight="700" fill="#EDEDE9">WIG20</text>
    <text x="118" y="29" font-family="Courier New, monospace" font-size="18" font-weight="700" fill="#34D399">+1.42%</text>
  </g>
  <g transform="translate(1145, 295)">
    <rect width="230" height="46" rx="23" fill="#141822" stroke="#ffffff" stroke-opacity="0.15" stroke-width="1.5"/>
    <text x="24" y="29" font-family="Courier New, monospace" font-size="18" font-weight="700" fill="#8B92A1">USD/PLN</text>
    <text x="126" y="29" font-family="Courier New, monospace" font-size="18" font-weight="700" fill="#E8A33D">3.9526</text>
  </g>

  <!-- Lewa kolumna: Logo + Hasło przewodnie -->
  <g transform="translate(96, 105)">
    <rect width="88" height="88" rx="22" fill="#141822" stroke="#E8A33D" stroke-opacity="0.50" stroke-width="2.5"/>
    <path d="M 18 65 C 38 63, 52 48, 68 20" fill="none" stroke="#E8A33D" stroke-width="9" stroke-linecap="round"/>
    <circle cx="68" cy="20" r="6" fill="#34D399"/>
    <text x="112" y="62" font-family="Helvetica Neue, Arial, sans-serif" font-size="62" font-weight="700" fill="#EDEDE9">compound</text>
    <text x="432" y="62" font-family="Courier New, monospace" font-size="44" font-weight="700" fill="#E8A33D">.pl</text>
  </g>

  <text x="96" y="268" font-family="Helvetica Neue, Arial, sans-serif" font-size="34" font-weight="600" fill="#EDEDE9">Rynki, gospodarka i świat — bez szumu i clickbaitu.</text>
  <text x="96" y="318" font-family="Helvetica Neue, Arial, sans-serif" font-size="22" font-weight="400" fill="#8B92A1">Twarde dane NBP i GPW · Synteza faktograficzna · Wolnorynkowe spojrzenie</text>

  <!-- Pigułki działów na dole -->
  <g transform="translate(96, 365)">
    <rect x="0" y="0" width="145" height="40" rx="20" fill="#141822" stroke="#E8A33D" stroke-opacity="0.45"/>
    <text x="72" y="25" text-anchor="middle" font-family="Helvetica Neue, Arial, sans-serif" font-size="15" font-weight="700" fill="#E8A33D">RYNKI &amp; GPW</text>

    <rect x="160" y="0" width="165" height="40" rx="20" fill="#141822" stroke="#ffffff" stroke-opacity="0.12"/>
    <text x="242" y="25" text-anchor="middle" font-family="Helvetica Neue, Arial, sans-serif" font-size="15" font-weight="600" fill="#EDEDE9">TABELE KURSÓW</text>

    <rect x="340" y="0" width="155" height="40" rx="20" fill="#141822" stroke="#ffffff" stroke-opacity="0.12"/>
    <text x="417" y="25" text-anchor="middle" font-family="Helvetica Neue, Arial, sans-serif" font-size="15" font-weight="600" fill="#EDEDE9">MAKRO &amp; TECH</text>

    <rect x="510" y="0" width="165" height="40" rx="20" fill="#141822" stroke="#ffffff" stroke-opacity="0.12"/>
    <text x="592" y="25" text-anchor="middle" font-family="Helvetica Neue, Arial, sans-serif" font-size="15" font-weight="600" fill="#EDEDE9">ŚWIAT &amp; SPORT</text>
  </g>
</svg>
"""

# 6. Plakat promocyjny na Instagram / Social Media (1080x1350 px)
POSTER_PROMO_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1080 1350" width="1080" height="1350">
  <rect width="1080" height="1350" fill="#0B0D12"/>
  <rect x="36" y="36" width="1008" height="1278" rx="44" fill="none" stroke="#ffffff" stroke-opacity="0.08" stroke-width="2"/>

  <!-- Górny pasek marki -->
  <g transform="translate(96, 96)">
    <rect width="80" height="80" rx="22" fill="#141822" stroke="#E8A33D" stroke-opacity="0.55" stroke-width="2.5"/>
    <path d="M 16 58 C 36 56, 48 42, 62 18" fill="none" stroke="#E8A33D" stroke-width="8" stroke-linecap="round"/>
    <circle cx="62" cy="18" r="5.5" fill="#34D399"/>
    <text x="102" y="56" font-family="Helvetica Neue, Arial, sans-serif" font-size="52" font-weight="700" fill="#EDEDE9">compound</text>
    <text x="374" y="56" font-family="Courier New, monospace" font-size="38" font-weight="700" fill="#E8A33D">.pl</text>
  </g>

  <!-- Główne hasło -->
  <text x="96" y="290" font-family="Helvetica Neue, Arial, sans-serif" font-size="68" font-weight="700" fill="#EDEDE9">Inwestuj w oparciu</text>
  <text x="96" y="372" font-family="Helvetica Neue, Arial, sans-serif" font-size="68" font-weight="700" fill="#E8A33D">o twarde fakty,</text>
  <text x="96" y="454" font-family="Helvetica Neue, Arial, sans-serif" font-size="68" font-weight="700" fill="#EDEDE9">nie emocje.</text>

  <text x="96" y="525" font-family="Helvetica Neue, Arial, sans-serif" font-size="27" font-weight="400" fill="#8B92A1">Nowoczesny portal informacyjno-analityczny dla inwestorów.</text>

  <!-- Karta podglądu interfejsu w centrum plakatu -->
  <g transform="translate(96, 585)">
    <rect width="888" height="470" rx="36" fill="#141822" stroke="#ffffff" stroke-opacity="0.10" stroke-width="2"/>
    
    <!-- Pasek w karcie -->
    <rect x="42" y="42" width="190" height="38" rx="19" fill="#1E2433"/>
    <text x="137" y="67" text-anchor="middle" font-family="Helvetica Neue, Arial, sans-serif" font-size="15" font-weight="700" fill="#E8A33D">KLUCZOWE FAKTY</text>
    <text x="846" y="67" text-anchor="end" font-family="Courier New, monospace" font-size="18" fill="#8B92A1">LIVE · GPW &amp; NBP</text>

    <!-- Przykładowy nagłówek w karcie -->
    <text x="42" y="135" font-family="Helvetica Neue, Arial, sans-serif" font-size="32" font-weight="700" fill="#EDEDE9">Synteza rynku w 3 konkretnych punktach</text>

    <!-- 3 punkty -->
    <circle cx="54" cy="192" r="6" fill="#E8A33D"/>
    <text x="78" y="200" font-family="Helvetica Neue, Arial, sans-serif" font-size="23" fill="#B8BFCE">Zero clickbaitu, reklam i pustych spekulacji medialnych.</text>

    <circle cx="54" cy="252" r="6" fill="#34D399"/>
    <text x="78" y="260" font-family="Helvetica Neue, Arial, sans-serif" font-size="23" fill="#B8BFCE">Notowania GPW, tabele kursów NBP, surowce i krypto na żywo.</text>

    <circle cx="54" cy="312" r="6" fill="#7DD3FC"/>
    <text x="78" y="320" font-family="Helvetica Neue, Arial, sans-serif" font-size="23" fill="#B8BFCE">Kalkulator procentu składanego i przelicznik walutowy.</text>

    <!-- Dolne pigułki wskaźników -->
    <g transform="translate(42, 372)">
      <rect x="0" y="0" width="230" height="54" rx="27" fill="#0B0D12" stroke="#ffffff" stroke-opacity="0.08"/>
      <text x="115" y="34" text-anchor="middle" font-family="Courier New, monospace" font-size="20" font-weight="700" fill="#34D399">WIG20 +0.78%</text>

      <rect x="250" y="0" width="245" height="54" rx="27" fill="#0B0D12" stroke="#ffffff" stroke-opacity="0.08"/>
      <text x="372" y="34" text-anchor="middle" font-family="Courier New, monospace" font-size="20" font-weight="700" fill="#E8A33D">USD/PLN 3.9526</text>

      <rect x="515" y="0" width="285" height="54" rx="27" fill="#0B0D12" stroke="#ffffff" stroke-opacity="0.08"/>
      <text x="657" y="34" text-anchor="middle" font-family="Courier New, monospace" font-size="20" font-weight="700" fill="#7DD3FC">BTC/USD $77,820</text>
    </g>
  </g>

  <!-- Stopka plakatu -->
  <rect x="96" y="1135" width="888" height="100" rx="50" fill="#E8A33D"/>
  <text x="540" y="1197" text-anchor="middle" font-family="Helvetica Neue, Arial, sans-serif" font-size="34" font-weight="700" fill="#0B0D12">Sprawdź codzienny brief na compound.pl</text>
</svg>
"""


def save_svg_and_png(svg_content, svg_filename, png_filename=None, scale=2.0):
    svg_path = os.path.join(BRAND_DIR, svg_filename)
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(svg_content.strip())
    print(f"[OK] Zapisano wektor SVG: {svg_path}")

    if png_filename:
        png_path = os.path.join(BRAND_DIR, png_filename)
        doc = fitz.open(stream=svg_content.encode("utf-8"), filetype="svg")
        page = doc[0]
        pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=True)
        pix.save(png_path)
        doc.close()
        print(f"[OK] Wyrenderowano PNG ({pix.width}x{pix.height} px): {png_path}")


if __name__ == "__main__":
    save_svg_and_png(LOGO_MARK_SVG, "logo-mark.svg", "logo-mark-1024.png", scale=2.0)
    save_svg_and_png(LOGO_VECTOR_SVG, "logo-vector.svg", "logo-horizontal-1920.png", scale=2.0)
    save_svg_and_png(AVATAR_SQUARE_SVG, "avatar-profile.svg", "avatar-profile-1080.png", scale=1.0)
    save_svg_and_png(AVATAR_CIRCLE_SVG, "avatar-gmail-circle.svg", "avatar-gmail-circle-512.png", scale=1.0)
    save_svg_and_png(BANNER_SOCIAL_SVG, "banner-social.svg", "banner-social-1500x500.png", scale=1.0)
    save_svg_and_png(POSTER_PROMO_SVG, "poster-promo.svg", "poster-instagram-1080x1350.png", scale=1.0)
