"""
Compound (compound.pl) — Moduł Analiz Fundamentalnych Długoterminowych (long_term_analyses.py)
Odpowiedzialny za:
1. Dostarczanie przekrojowych, edukacyjno-analitycznych profili największych spółek z GPW oraz rynków światowych
   w horyzoncie długoterminowym (Long-Term: 3–10 lat) — np. XTB, Dino Polska, Kruk, Grupa Kęty, Budimex, PKO BP,
   PZU, CD Projekt, KGHM, Orlen, NVIDIA, Microsoft.
2. Prezentację modelowych koszyków alokacji kapitału ("W co i dlaczego alokuje się kapitał na lata")
   wraz z uzasadnieniem makroekonomicznym, fosą konkurencyjną (Moat), katalizatorami oraz czynnikami ryzyka.
3. Pełną zgodność regulacyjną z KNF / Rozporządzeniem MAR (charakter wyłącznie informacyjno-edukacyjny,
   zestawienie szans i ryzyk bez rekomendacji kupna/sprzedaży).
"""


def build_model_portfolios():
    """
    Zwraca 3 edukacyjne koszyki alokacji kapitału na długi termin (Long-Term),
    wyjaśniające dlaczego inwestorzy długoterminowi wybierają poszczególne klasy aktywów dzisiaj.
    """
    return [
        {
            "id": "basket-gpw-compounders",
            "badge": "Strategia 1 · GPW Dywidendy & Wzrost (IKE / IKZE)",
            "title": "Polscy Liderzy Procentu Składanego i Dywidend",
            "horizon": "Horyzont: 5–10 lat",
            "profile": "Dywidenda + Reinwestycja Zysków",
            "why_today": (
                "Polska gospodarka utrzymuje jeden z najwyższych temp wzrostu PKB w Unii Europejskiej, "
                "a wyceny czołowych spółek z GPW (wskaźniki C/Z na poziomie 7–14x) pozostają z istotnym "
                "dyskontem wobec rynków zachodnich przy wysokich stopach dywidendy (5–10% rocznie)."
            ),
            "allocation": [
                {"name": "XTB (Fintech & Broker)", "weight": "25%", "role": "Silnik wzrostu klientów i wysoka dywidenda z zysków gotówkowych"},
                {"name": "Dino Polska / Kruk SA", "weight": "25%", "role": "Skalowanie biznesu i reinwestycja kapitału przy wysokim ROE"},
                {"name": "PKO BP / Grupa PZU", "weight": "25%", "role": "Filar finansowy generujący regularne przepływy dywidendowe"},
                {"name": "Grupa Kęty / Budimex", "weight": "25%", "role": "Ekspozycja na przemysł, infrastrukturę i wieloletnie portfele zamówień"},
            ],
            "key_advantage": "Wykorzystanie konta IKE/IKZE pozwala reinwestować 100% dywidend od polskich spółek bez 19% podatku Belki.",
        },
        {
            "id": "basket-global-moat",
            "badge": "Strategia 2 · Globalna Fosa Technologiczna (Wall Street)",
            "title": "Światowe Monopole Infrastruktury Cyfrowej i AI",
            "horizon": "Horyzont: 5–15 lat",
            "profile": "Globalny Wzrost & Wysoka Marża",
            "why_today": (
                "Transformacja chmurowa i sztuczna inteligencja wymagają bilionowych nakładów kapitałowych (CAPEX), "
                "które trafiają bezpośrednio do wąskiej grupy dostawców sprzętu, chmury i oprogramowania "
                "posiadających globalny efekt sieciowy i marże operacyjne powyżej 35–55%."
            ),
            "allocation": [
                {"name": "Microsoft / Alphabet", "weight": "35%", "role": "Powtarzalne przychody subskrypcyjne B2B i chmura obliczeniowa"},
                {"name": "NVIDIA / Sektor Półprzewodników", "weight": "25%", "role": "Infrastruktura obliczeniowa dla centrów danych AI"},
                {"name": "Szeroki Indeks S&P 500 (ETF)", "weight": "25%", "role": "Automatyzacja ekspozycji na 500 największych korporacji USA"},
                {"name": "Gotówka USD / Krótkoterminowe Obligacje", "weight": "15%", "role": "Bufor płynnościowy na wypadek korekt rynkowych"},
            ],
            "key_advantage": "Ekspozycja na dolara (USD) oraz firmy o najwyższych na świecie zwrotach z zainwestowanego kapitału (ROIC).",
        },
        {
            "id": "basket-real-assets",
            "badge": "Strategia 3 · Twarde Aktywa & Ochrona Siły Nabywczej",
            "title": "Surowce Strategiczne, Energia i Tarcza Antyinflacyjna",
            "horizon": "Horyzont: 3–10 lat",
            "profile": "Ochrona Kapitału & Realne Aktywa",
            "why_today": (
                "W otoczeniu podwyższonego zadłużenia państw, napięć geopolitycznych oraz rosnącego zapotrzebowania "
                "na energię i miedź (sieci przesyłowe, elektromobilność, centra danych), realne aktywa stanowią "
                "naturalne zabezpieczenie przed utratą siły nabywczej pieniądza fiducjarnego."
            ),
            "allocation": [
                {"name": "Złoto Inwestycyjne (XAU)", "weight": "30%", "role": "Rezerwowe aktywo banków centralnych bez ryzyka emitenta"},
                {"name": "Obligacje Skarbowe Indeksowane Inflacją", "weight": "30%", "role": "Stabilizator portfela gwarantujący marżę ponad CPI"},
                {"name": "KGHM Polska Miedź / Surowce", "weight": "20%", "role": "Ekspozycja na strategiczną miedź i srebro"},
                {"name": "Orlen / Sektor Energetyczny", "weight": "20%", "role": "Niska wycena C/Z i regularne przepływy z infrastruktury paliwowo-energetycznej"},
            ],
            "key_advantage": "Niska korelacja ze spółkami technologicznymi i ochrona realnej wartości majątku w czasie kryzysów.",
        },
    ]


def build_long_term_analyses(live_ticker=None):
    """
    Zwraca szczegółowe analizy fundamentalne 12 kluczowych spółek (GPW + Świat) pod kątem
    inwestowania długoterminowego (Long-Term), wzbogacone o aktualne kursy z paska notowań.
    """
    price_map = {}
    if live_ticker:
        for item in live_ticker:
            price_map[item.get("symbol", "")] = item

    def _get_quote(sym, default_price, default_change):
        if sym in price_map:
            return price_map[sym]["price"], price_map[sym]["change"], price_map[sym]["is_positive"]
        return default_price, default_change, default_change.startswith("+")

    raw_companies = [
        {
            "id": "analiza-xtb",
            "ticker": "XTB",
            "exchange": "GPW: XTB",
            "name": "XTB SA (X-Trade Brokers)",
            "group": "gpw_growth",
            "sector": "Fintech & Dom Maklerski",
            "horizon": "Long-Term (3–8 lat)",
            "style_badge": "Wzrost + Wysoka Dywidenda",
            "default_price": "68.40 zł",
            "default_change": "+1.45%",
            "image_url": "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?auto=format&fit=crop&w=1000&q=80",
            "fundamental_metrics": [
                "ROE: ~35–42%",
                "Polityka dywidendy: 50–100% zysku",
                "Baza klientów: >1,2 mln",
                "Zadłużenie: Brak długu netto",
            ],
            "headline": "Europejski lider fintech z polskim rodowodem: skalowalne pozyskiwanie klientów i wysoka konwersja zysku na gotówkę",
            "why_worth_attention": [
                "Transformacja z brokera aktywnego handlu w kompleksową europejską super-aplikację inwestycyjną (akcje, ETF-y, plany inwestycyjne, oprocentowanie wolnych środków oraz konta IKE/IKZE).",
                "Rekordowe tempo akwizycji nowych klientów (setki tysięcy nowych rachunków rocznie w Polsce, Europie Zachodniej, na Bliskim Wschodzie i w Ameryce Łacińskiej), co buduje trwałą bazę przychodową na lata.",
                "Model biznesowy o niskim zapotrzebowaniu na kapitał rzeczowy pozwala wypłacać akcjonariuszom od 50% do nawet 75% wypracowanego zysku netto w formie corocznej dywidendy przy jednoczesnym finansowaniu ekspansji.",
            ],
            "why_now": (
                "Wprowadzenie kont emerytalnych IKE/IKZE oraz planów pasywnych przyciąga do XTB kapitał długoterminowy, "
                "który stabilizuje przychody spółki niezależnie od krótkoterminowej zmienności rynkowej."
            ),
            "deep_dive_paragraphs": [
                "Model operacyjny XTB opiera się na własnej, autorskiej technologii transakcyjnej (xStation), dzięki czemu spółka nie płaci zewnętrznym dostawcom licencji od rosnącego wolumenu obrotu. Każdy kolejny tysiąc aktywnych użytkowników podnosi dźwignię operacyjną firmy.",
                "Z perspektywy inwestora długoterminowego kluczowa jest struktura bilansu: XTB utrzymuje wysokie nadwyżki gotówkowe i kapitałowe, co przekłada się na regularne, wysokie dywidendy (często dające 6–9% stopy dywidendy) przy jednoczesnym wzroście skali działalności.",
                "Rozшиrzenie oferty o produkty wielowalutowe i rachunki emerytalne sprawia, że XTB staje się pierwszym wyborem dla nowego pokolenia inwestorów indywidualnych w całym regionie CEE i UE.",
            ],
            "risk_factors": [
                "Uzależnienie części kwartalnych przychodów od zmienności na rynkach surowców, indeksów i walut.",
                "Ryzyko regulacyjne na poszczególnych rynkach Unii Europejskiej (np. ograniczenia marketingowe jak w Hiszpanii).",
            ],
        },
        {
            "id": "analiza-dino",
            "ticker": "DINO",
            "exchange": "GPW: DNP",
            "name": "Dino Polska SA",
            "group": "gpw_growth",
            "sector": "Handel Detaliczny & Nieruchomości",
            "horizon": "Long-Term (5–10 lat)",
            "style_badge": "Czysty Procent Składany",
            "default_price": "394.50 zł",
            "default_change": "+0.85%",
            "image_url": "https://images.unsplash.com/photo-1542838132-92c53300491e?auto=format&fit=crop&w=1000&q=80",
            "fundamental_metrics": [
                "Sieć: >2 500 sklepów",
                "Reinwestycja zysku: 100%",
                "Model: Własność gruntów",
                "Zintegrowany zakład mięsny Agro-Rydzyna",
            ],
            "headline": "Klasyczny „compounder” na GPW: reinwestycja 100% przepływów pieniężnych w budowę własnej sieci sklepów",
            "why_worth_attention": [
                "Unikalny model biznesowy: w przeciwieństwie do konkurencji wynajmującej lokale, Dino kupuje grunty na własność i buduje wystandaryzowane markety blisko miejsca zamieszkania klientów w mniejszych miejscowościach i na obrzeżach miast.",
                "Pionowa integracja łańcucha dostaw (własne centra dystrybucyjne oraz zakłady mięsne Agro-Rydzyna) zapewnia pełną kontrolę nad jakością świeżych produktów i chroni marżę brutto.",
                "Spółka nie wypłaca dywidendy, lecz reinwestuje każdą zarobioną złotówkę w otwieranie kolejnych kilkuset sklepów rocznie, co historycznie generowało ponadprzeciętny wzrost wartości wewnętrznej przedsiębiorstwa.",
            ],
            "why_now": (
                "Rosnące realne wynagrodzenia konsumentów w Polsce oraz spadająca presja kosztowa energii (własne instalacje fotowoltaiczne na dachach marketów Dino) wspierają odbudowę marży EBITDA w kolejnych latach."
            ),
            "deep_dive_paragraphs": [
                "Dino Polska jest podręcznikowym przykładem działania procentu składanego w gospodarce realnej. Powtarzalny format sklepu o powierzchni ok. 400 m² pozwala na szybkie i przewidywalne skalowanie sieci w województwach o niższym nasyceniu (szczególnie wschodnia i północna Polska).",
                "Własność nieruchomości sprawia, że spółka nie jest narażona na indeksację czynszów najmu w euro, co w długim terminie daje jej trwałą przewagę kosztową nad sieciami opartymi na franczyzie lub wynajmie.",
                "Nawet po osiągnięciu docelowego nasycenia rynku w Polsce za kilka lat, spadek nakładów inwestycyjnych (CAPEX) na nowe otwarcia uwolni ogromne wolne przepływy pieniężne (Free Cash Flow).",
            ],
            "risk_factors": [
                "Wojna cenowa pomiędzy największymi sieciami dyskontowymi w Polsce wywierająca presję na marżę handlową.",
                "Wzrost kosztów pracy (płaca minimalna) wymagający ciągłego wzrostu sprzedaży porównywalnej (LFL).",
            ],
        },
        {
            "id": "analiza-kruk",
            "ticker": "KRUK",
            "exchange": "GPW: KRU",
            "name": "Kruk SA",
            "group": "gpw_growth",
            "sector": "Zarządzanie Wierzytelnościami",
            "horizon": "Long-Term (4–8 lat)",
            "style_badge": "Ekspansja Międzynarodowa + Dywidenda",
            "default_price": "438.00 zł",
            "default_change": "+0.92%",
            "image_url": "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?auto=format&fit=crop&w=1000&q=80",
            "fundamental_metrics": [
                "ROE: ~24–26%",
                "Rynki: PL, Włochy, Hiszpania, Rumunia, Francja",
                "Dywidenda: Wypłacana nieprzerwanie od 10 lat",
                "Lider rynku CEE & Południa UE",
            ],
            "headline": "Międzynarodowy czempion z Wrocławia: zaawansowana analityka danych i polubowna spłata wierzytelności w Europie",
            "why_worth_attention": [
                "Kruk przestał być spółką lokalną — ponad połowa nowych inwestycji w portfele wierzytelności realizowana jest na dużych rynkach strefy euro (Włochy, Hiszpania, Francja) oraz w Rumunii.",
                "Przewaga konkurencyjna oparta na 25-letnich zbiorach danych statystycznych i modelach wyceny portfeli długów, dzięki czemu realne wpłaty od dłużników regularnie przewyższają konserwatywne prognozy księgowe.",
                "Rzadkie połączenie szybkiego wzrostu skali biznesu z regularnym dzieleniem się zyskiem z akcjonariuszami (ponad dekada nieprzerwanych wypłat dywidendy).",
            ],
            "why_now": (
                "Banki komercyjne w Europie regularnie czyszczą bilanse ze spisanych kredytów konsumenckich, zapewniając Krukowi szeroką podaż nowych portfeli wierzytelności po atrakcyjnych stopach zwrotu (IRR)."
            ),
            "deep_dive_paragraphs": [
                "Kluczem do sukcesu Kruka było wdrożenie strategii ugodowej — traktowanie osoby zadłużonej jak klienta i rozkładanie zobowiązań na niskie, możliwe do udźwignięcia raty za pośrednictwem platform samoobsługowych online.",
                "Ekspansja we Włoszech i Hiszpanii otworzyła przed spółką rynek wielokrotnie większy niż Polska, a wysoka automatyzacja procesów operacyjnych pozwala skalować odzyski bez proporcjonalnego wzrostu zatrudnienia.",
            ],
            "risk_factors": [
                "Wysoki udział finansowania dłużnego (obligacje i kredyty bankowe) niezbędnego do zakupu nowych portfeli.",
                "Ryzyko zmian przepisów windykacyjnych i sądowych na rynkach południowoeuropejskich.",
            ],
        },
        {
            "id": "analiza-kety",
            "ticker": "KĘTY",
            "exchange": "GPW: KTY",
            "name": "Grupa Kęty SA",
            "group": "dividend",
            "sector": "Przemysł & Przetwórstwo Aluminium",
            "horizon": "Long-Term (5–10 lat)",
            "style_badge": "Arystokrata Dywidendowy GPW",
            "default_price": "782.00 zł",
            "default_change": "+0.54%",
            "image_url": "https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?auto=format&fit=crop&w=1000&q=80",
            "fundamental_metrics": [
                "Wypłata dywidendy: 60–85% zysku netto",
                "Historia dywidend: >20 lat z rzędu",
                "3 filary: Wyroby Wyciskane, Systemy Alu, Opakowania",
                "Silny eksport do UE",
            ],
            "headline": "Wzór ładu korporacyjnego na GPW: ponad dwie dekady nieprzerwanych dywidend i nowoczesny przemysł",
            "why_worth_attention": [
                "Jedna z najbardziej przewidywalnych i transparentnych spółek przemysłowych w Europie Środkowej, zarządzana z ogromnym poszanowaniem kapitału akcjonariuszy (w tym OFE i inwestorów indywidualnych).",
                "Dywersyfikacja na 3 komplementarne segmenty (Systemy Aluminiowe dla budownictwa, Wyroby Wyciskane dla przemysłu/motoryzacji oraz Opakowania Giętkie dla sektora spożywczego) stabilizuje wyniki w różnych fazach cyklu.",
                "Aluminium jest kluczowym surowcem transformacji energetycznej i termomodernizacji budynków w całej Unii Europejskiej (możliwość nieskończonego recyklingu przy niskim zużyciu energii).",
            ],
            "why_now": (
                "Programy termomodernizacji budynków w UE oraz ożywienie w budownictwie energooszczędnym bezpośrednio napędzają popyt na zaawansowane systemy fasadowe i okienne marki Aluprof (należącej do Grupy Kęty)."
            ),
            "deep_dive_paragraphs": [
                "Grupa Kęty udowadnia, że produkcja przemysłowa w Polsce może konkurować w Europie Zachodniej jakością, automatyzacją i zaawansowaniem inżynieryjnym, a nie wyłącznie kosztami pracy.",
                "Dla inwestora budującego portfel rentierski na lata, Kęty stanowią rzadki na polskim rynku przykład spółki, która regularnie realizuje lub przekracza swoje wieloletnie strategie finansowe, wypłacając wysokie dywidendy w dwóch transzach rocznie.",
            ],
            "risk_factors": [
                "Wrażliwość na wahania koniunktury przemysłowej w Niemczech i strefie euro oraz ceny energii i aluminium.",
            ],
        },
        {
            "id": "analiza-budimex",
            "ticker": "BUDIMEX",
            "exchange": "GPW: BDX",
            "name": "Budimex SA",
            "group": "dividend",
            "sector": "Infrastruktura, Kolej & Energetyka",
            "horizon": "Long-Term (4–8 lat)",
            "style_badge": "Lider Infrastruktury + Dywidenda",
            "default_price": "564.00 zł",
            "default_change": "+1.12%",
            "image_url": "https://images.unsplash.com/photo-1541888946425-d81bb19240f5?auto=format&fit=crop&w=1000&q=80",
            "fundamental_metrics": [
                "Portfel zamówień: >15 mld zł",
                "Pozycja gotówkowa netto: Dodatnia",
                "Dywidenda: Regularnie do 80–100% zysku",
                "Ekspansja: Polska, Czechy, Słowacja, Kraje Bałtyckie",
            ],
            "headline": "Główny beneficjent wieloletnich inwestycji infrastrukturalnych, kolejowych, obronnych i energetycznych w regionie",
            "why_worth_attention": [
                "Największy generalny wykonawca w Polsce z rekordowym portfelem zamówień gwarantującym pełne obłożenie pracą na najbliższe 3–4 lata.",
                "W przeciwieństwie do wielu mniejszych firm budowlanych, Budimex charakteryzuje się żelazną dyscypliną kosztową, selekcją rentownych kontraktów oraz nadwyżką gotówki netto na bilansie.",
                "Nowe strumienie wzrostu: budowa kolei dużych prędkości, infrastruktury obronnej/wojskowej, morskich i lądowych sieci energetycznych oraz wejście w segment odnawialnych źródeł energii i centrów danych.",
            ],
            "why_now": (
                "Kumulacja środków z KPO, nowej perspektywy unijnej oraz budżetu obronnego i energetycznego Polski uruchamia największą falę przetargów infrastrukturalnych dekady."
            ),
            "deep_dive_paragraphs": [
                "Budimex od lat wyróżnia się w branży budowlanej ponadprzeciętną marżą operacyjną oraz zdolnością do generowania gotówki dzięki zaliczkom kontraktowym i efektywnemu zarządzaniu kapitałem obrotowym.",
                "Dodatkowo ekspansja na rynki sąsiednie (Czechy, Słowacja, udział w projekcie Rail Baltica na Łotwie i w Estonii) uniezależnia spółkę od jednego zamawiającego.",
            ],
            "risk_factors": [
                "Ryzyko gwałtownych skoków cen materiałów budowlanych i podwykonawstwa przy kontraktach długoterminowych.",
            ],
        },
        {
            "id": "analiza-pkobp",
            "ticker": "PKO BP",
            "exchange": "GPW: PKO",
            "name": "PKO Bank Polski SA",
            "group": "dividend",
            "sector": "Bankowość Uniwersalna",
            "horizon": "Long-Term (3–10 lat)",
            "style_badge": "Fundament WIG20 & Dywidendy",
            "default_price": "59.84 zł",
            "default_change": "+1.18%",
            "image_url": "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=1000&q=80",
            "fundamental_metrics": [
                "ROE: ~18–20%",
                "Aktywa: >500 mld zł (#1 w CEE)",
                "Koszt finansowania: Najniższy na rynku",
                "Wysoki potencjał dywidendowy",
            ],
            "headline": "Największa instytucja finansowa Europy Środkowo-Wschodniej i barometr polskiej gospodarki",
            "why_worth_attention": [
                "Niekwestionowany lider depozytów detalicznych w Polsce (ponad 12 mln klientów i aplikacja IKO), co zapewnia bankowi najtańszy koszt finansowania na rynku i wysoką marżę odsetkową (NIM).",
                "Wraz z wygasaniem rezerw na historyczne kredyty frankowe (CHF), ogromna zdolność generowania kapitału własnego przekłada się bezpośrednio na wypłaty dywidend i zaliczek dywidendowych.",
                "Główny podmiot finansujący transformację energetyczną, inwestycje przedsiębiorstw oraz rynek kredytów hipotecznych w Polsce.",
            ],
            "why_now": (
                "Utrzymujące się dodatnie realne stopy procentowe w Polsce oraz przyspieszenie akcji kredytowej dla firm wspierają powtarzalny wynik odsetkowy i prowizyjny na poziomie wielu miliardów złotych rocznie."
            ),
            "deep_dive_paragraphs": [
                "Skala PKO BP tworzy potężną fosę kosztową i technologiczną — bank może inwestować setki milionów złotych rocznie w cyberbezpieczeństwo, chmurę i automatyzację AI, rozkładając ten koszt na największą bazę klientów w kraju.",
                "Dla inwestorów zagranicznych i krajowych funduszy PKO BP stanowi podstawowy instrument ekspozycji na wzrost polskiego PKB.",
            ],
            "risk_factors": [
                "Wrażliwość wyniku odsetkowego na przyszłe cykle obniżek stóp procentowych NBP.",
                "Obecność Skarbu Państwa w akcjonariacie (ryzyko decyzji politycznych i podatkowych wobec sektora).",
            ],
        },
        {
            "id": "analiza-pzu",
            "ticker": "PZU",
            "exchange": "GPW: PZU",
            "name": "Grupa PZU SA",
            "group": "dividend",
            "sector": "Ubezpieczenia, Zdrowie & Bankowość",
            "horizon": "Long-Term (5–10 lat)",
            "style_badge": "Królowa Polskich Dywidend",
            "default_price": "48.12 zł",
            "default_change": "+0.55%",
            "image_url": "https://images.unsplash.com/photo-1450101499163-c8848c66ca85?auto=format&fit=crop&w=1000&q=80",
            "fundamental_metrics": [
                "Stopa dywidendy: Historycznie 6–9%",
                "Wypłacalność Solvency II: >200%",
                "Aktywa: Ubezpieczenia + Pekao + Alior + PZU Zdrowie",
                "ROE: ~17–19%",
            ],
            "headline": "Największy konglomerat finansowo-ubezpieczeniowy w regionie generujący ponadprzeciętny strumień gotówki",
            "why_worth_attention": [
                "Dominująca pozycja w ubezpieczeniach majątkowych i życiowych w Polsce z siecią dystrybucji, której zbudowanie od zera przez zagraniczną konkurencję jest praktycznie niemożliwe.",
                "Ogromny portfel inwestycyjny lokowany w bezpiecznych obligacjach skarbowych pracuje na wysokich rentownościach, generując stabilny dochód lokacyjny niezależnie od koniunktury giełdowej.",
                "Dynamiczny rozwój filaru prywatnej opieki medycznej (PZU Zdrowie) oraz zarządzania aktywami (TFI PZU, PPK) odpowiada na trendy demograficzne polskiego społeczeństwa.",
            ],
            "why_now": (
                "Niska wycena wskaźnikowa (C/Z poniżej 9x) w połączeniu z wysokim współczynnikiem wypłacalności Solvency II sprawia, że PZU pozostaje jednym z najchętniej wybieranych fundamentów portfeli dywidendowych IKE."
            ),
            "deep_dive_paragraphs": [
                "PZU to w praktyce dwa silniki zysku w jednej akcji: tradycyjny biznes ubezpieczeniowy (gdzie składka wpływa z góry, zanim pojawią się wypłaty odszkodowań — tzw. ubezpieczeniowy float, z którego słynie Berkshire Hathaway Warrena Buffetta) oraz znaczące pakiety akcji w Banku Pekao i Alior Banku.",
            ],
            "risk_factors": [
                "Zjawiska pogodowe o charakterze katastroficznym (powodzie, przymrozki) podnoszące szkodowość w danym roku.",
                "Wpływ zmian zarządczych powiązanych ze Skarbem Państwa.",
            ],
        },
        {
            "id": "analiza-cdprojekt",
            "ticker": "CD PROJEKT",
            "exchange": "GPW: CDR",
            "name": "CD Projekt SA",
            "group": "gpw_growth",
            "sector": "Globalny Gaming & Własność Intelektualna (IP)",
            "horizon": "Long-Term (4–8 lat)",
            "style_badge": "Globalny Eksport & Silne IP",
            "default_price": "172.40 zł",
            "default_change": "+1.20%",
            "image_url": "https://images.unsplash.com/photo-1511512578047-dfb367046420?auto=format&fit=crop&w=1000&q=80",
            "fundamental_metrics": [
                "Przychody z eksportu: >95%",
                "Bilans: Ponad 1 mld zł gotówki i obligacji",
                "Główne franczyzy: Wiedźmin & Cyberpunk",
                "Marża brutto na sprzedaży cyfrowej: >75%",
            ],
            "headline": "Polski właściciel globalnych franczyz rozrywkowych o wieloletnim cyklu monetyzacji (Wiedźmin & Cyberpunk)",
            "why_worth_attention": [
                "Własność dwóch rozpoznawalnych na całym świecie marek popkulturowych (IP), które zarabiają przez wiele lat po premierze dzięki dystrybucji cyfrowej (Steam, PlayStation, Xbox), serialom, komiksom i dodatkom.",
                "Przejście na silnik Unreal Engine 5 pozwala studiu prowadzić równolegle kilka projektów (nowa trylogia Wiedźmina – Projekt Polaris, sequel Cyberpunka – Projekt Orion w Bostonie) przy mniejszym ryzyku technologicznym.",
                "Ponad 95% przychodów generowanych jest w walutach obcych (głównie USD i EUR), a koszty ponoszone są w dużej części w PLN.",
            ],
            "why_now": (
                "Wejście projektu Polaris (nowa odsłona sagi wiedźmińskiej) w fazę pełnej produkcji rozpoczyna wieloletni cykl budowania wartości przed kolejnymi globalnymi premierami."
            ),
            "deep_dive_paragraphs": [
                "W branży gier wideo najcenniejszym aktywem jest trwałe IP (własność intelektualna). Katalog tzw. back-catalogu (Wiedźmin 3 oraz Cyberpunk 2077 wraz z dodatkiem Widmo Wolności) generuje dla CD Projektu setki milionów złotych czystego przepływu pieniężnego nawet w latach bez dużej premiery.",
            ],
            "risk_factors": [
                "Długie cykle produkcyjne gier AAA (4–6 lat) i wrażliwość kursu na odbiór premier przez graczy.",
            ],
        },
        {
            "id": "analiza-kghm",
            "ticker": "KGHM",
            "exchange": "GPW: KGH",
            "name": "KGHM Polska Miedź SA",
            "group": "dividend",
            "sector": "Surowce Strategiczne (Miedź & Srebro)",
            "horizon": "Long-Term (5–10 lat)",
            "style_badge": "Surowce dla AI & Transformacji",
            "default_price": "146.20 zł",
            "default_change": "+1.52%",
            "image_url": "https://images.unsplash.com/photo-1578328819058-b69f3a3b0f6b?auto=format&fit=crop&w=1000&q=80",
            "fundamental_metrics": [
                "Pozycja: Czołowy producent miedzi i #2 producent srebra na świecie",
                "Aktywa: Polska, Chile (Sierra Gorda), Kanada, USA",
                "Kluczowy surowiec dla sieci elektroenergetycznych i centrów danych",
            ],
            "headline": "Strategiczny producent miedzi i srebra: fundament elektryfikacji gospodarki i rozbudowy centrów danych AI",
            "why_worth_attention": [
                "Bez miedzi nie ma transformacji energetycznej, samochodów elektrycznych, nowoczesnych sieci przesyłowych ani energochłonnych centrów danych AI — a uruchomienie nowej kopalni miedzi na świecie trwa średnio 12–15 lat.",
                "KGHM jest jednocześnie jednym z dwóch największych producentów srebra na świecie, co daje inwestorowi naturalną dźwignię na hossę na rynku metali szlachetnych i przemysłowych.",
                "Złoża w bezpiecznej jurysdykcji w Polsce uzupełnione są aktywami zagranicznymi w Ameryce Północnej i Chile.",
            ],
            "why_now": (
                "Strukturalny deficyt podaży miedzi prognozowany na lata 2026–2035 przy rosnącym popycie ze strony sektora energetycznego i technologicznego wspiera długoterminowe notowania surowca."
            ),
            "deep_dive_paragraphs": [
                "Inwestowanie w KGHM w długim terminie to ekspozycja na twarde aktywa materialne, których nie da się dodrukować. W okresach globalnej inflacji surowcowej przychody spółki denominowane w dolarach amerykańskich (USD) dynamicznie rosną.",
            ],
            "risk_factors": [
                "Wysoki koszt wydobycia głębinowego w Polsce oraz obciążenie podatkiem od wydobycia niektórych kopalin.",
                "Cykliczność światowych cen miedzi uzależniona od popytu z gospodarki USA i Chin.",
            ],
        },
        {
            "id": "analiza-orlen",
            "ticker": "ORLEN",
            "exchange": "GPW: PKN",
            "name": "Orlen SA",
            "group": "dividend",
            "sector": "Multienergetyka, Paliwa, Gaz & OZE",
            "horizon": "Long-Term (4–10 lat)",
            "style_badge": "Wartość (Value) + Gwarantowana Dywidenda",
            "default_price": "63.45 zł",
            "default_change": "-0.35%",
            "image_url": "https://images.unsplash.com/photo-1473341304170-971dccb5ac1e?auto=format&fit=crop&w=1000&q=80",
            "fundamental_metrics": [
                "Polityka dywidendowa: Rosnąca co roku kwota na akcję",
                "Wycena: Niski wskaźnik C/WK (~0,5x) i EV/EBITDA",
                "Segmenty: Rafineria, Gaz, Energetyka, Detal, Petrochemia",
            ],
            "headline": "Największy koncern multienergetyczny w regionie CEE z progresywną polityką dywidendową",
            "why_worth_attention": [
                "Połączenie aktywów rafineryjnych, gazowych (PGNiG), energetycznych (Energa) i detalicznych tworzy zdywersyfikowany organizm generujący dziesiątki miliardów złotych przepływów operacyjnych EBITDA rocznie.",
                "Jasna, wieloletnia polityka dywidendowa zakładająca systematyczny wzrost wypłacanej dywidendy na jedną akcję rok do roku.",
                "Bardzo niska wycena rynkowa względem wartości księgowej majątku infrastrukturalnego (sieci przesyłowe, elektrownie, terminale, tysiące stacji paliw w 7 krajach Europy).",
            ],
            "why_now": (
                "Uporządkowanie programu inwestycyjnego (CAPEX) oraz koncentracja na najbardziej rentownych projektach gazowych, morskich farmach wiatrowych i sieciach dystrybucyjnych poprawia zwrot z kapitału."
            ),
            "deep_dive_paragraphs": [
                "Dla długoterminowego inwestora typu Value (poszukującego niedowartościowanych aktywów płacących wysoką dywidendę), Orlen oferuje jedną z najwyższych stóp dywidendy wśród dużych spółek europejskich przy umiarkowanym zadłużeniu netto.",
            ],
            "risk_factors": [
                "Zmienność marż rafineryjnych i petrochemicznych oraz duże potrzeby kapitałowe na transformację energetyczną.",
            ],
        },
        {
            "id": "analiza-nvidia",
            "ticker": "NVIDIA",
            "exchange": "NASDAQ: NVDA",
            "name": "NVIDIA Corporation",
            "group": "global_giants",
            "sector": "Półprzewodniki & Infrastruktura AI",
            "horizon": "Long-Term (5–10 lat)",
            "style_badge": "Globalny Lider Technologii AI",
            "default_price": "$138.60",
            "default_change": "+1.85%",
            "image_url": "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1000&q=80",
            "fundamental_metrics": [
                "Marża brutto: ~73–75%",
                "Udział w rynku akceleratorów AI: >80%",
                "Fosa oprogramowania: Ekosystem CUDA (>5 mln deweloperów)",
            ],
            "headline": "Fundament rewolucji obliczeniowej: połączenie architektury układów GPU z zamkniętym ekosystemem oprogramowania CUDA",
            "why_worth_attention": [
                "Prawdziwą fosą konkurencyjną NVIDII nie są wyłącznie same chipy, lecz rozwijana od blisko 20 lat warstwa oprogramowania CUDA, biblioteki sieciowe (Mellanox/InfiniBand) oraz pełne systemy serwerowe.",
                "Największe firmy świata (Microsoft, Alphabet, Meta, Amazon, Oracle) traktują zakup klastrów obliczeniowych NVIDII jako strategiczną konieczność utrzymania pozycji konkurencyjnej.",
                "Roczna kadencja wydawania nowych architektur (Hopper → Blackwell → Rubin) utrzymuje dystans technologiczny nad konkurencją i pozwala generować marże niespotykane wcześniej w branży sprzętowej.",
            ],
            "why_now": (
                "Przejście branży AI z fazy samego trenowania modeli do masowego wnioskowania (inference), agentów AI, robotyki przemysłowej i autonomii otwiera drugą, długoterminową falę popytu na moc obliczeniową."
            ),
            "deep_dive_paragraphs": [
                "W historii technologii każda nowa era (komputery PC, internet, smartfony, chmura, a dziś sztuczna inteligencja) wyłaniała dostawcę kluczowej infrastruktury zbierającego największą rentę technologiczną. NVIDIA zajmuje tę pozycję w warstwie obliczeń akcelerowanych.",
            ],
            "risk_factors": [
                "Wysoka wycena wskaźnikowa oraz ryzyko cyklicznego spowolnienia wydatków kapitałowych (CAPEX) przez gigantów chmurowych.",
                "Ograniczenia eksportowe i napięcia geopolityczne wokół Tajwanu (TSMC).",
            ],
        },
        {
            "id": "analiza-microsoft",
            "ticker": "MICROSOFT",
            "exchange": "NASDAQ: MSFT",
            "name": "Microsoft Corporation",
            "group": "global_giants",
            "sector": "Chmura Obliczeniowa, Software B2B & AI",
            "horizon": "Long-Term (5–15 lat)",
            "style_badge": "Globalny Filar Jakości (Rating AAA)",
            "default_price": "$426.40",
            "default_change": "+0.74%",
            "image_url": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=1000&q=80",
            "fundamental_metrics": [
                "Rating kredytowy: AAA (wyższy niż obligacje USA)",
                "Marża operacyjna: >43%",
                "Filary: Azure, Microsoft 365, Windows, LinkedIn, GitHub",
            ],
            "headline": "Najbardziej zdywersyfikowany ekosystem oprogramowania dla biznesu na świecie o gigantycznych kosztach zmiany dostawcy",
            "why_worth_attention": [
                "Niezwykle wysokie koszty zmiany dostawcy (Switching Costs): miliony przedsiębiorstw, banków i instytucji na całym świecie opierają codzienną pracę na ekosystemie Windows, Office 365, Teams i chmurze Azure.",
                "Model subskrypcyjny zapewnia przewidywalne, powtarzalne przepływy pieniężne (ARR) odporne na spowolnienia gospodarcze.",
                "Bezpośrednia monetyzacja sztucznej inteligencji zarówno na poziomie infrastruktury chmurowej (Azure AI), jak i na poziomie aplikacji biurowych oraz narzędzi dla programistów (GitHub Copilot).",
            ],
            "why_now": (
                "Rosnąca adopcja rozwiązań chmurowych i automatyzacji AI w sektorze korporacyjnym pozwala spółce systematycznie podnosić średni przychód na użytkownika biznesowego (ARPU) oraz co roku zwiększać dywidendę i skup akcji własnych."
            ),
            "deep_dive_paragraphs": [
                "Microsoft jest jedną z zaledwie dwóch korporacji na świecie posiadających najwyższy możliwy rating wiarygodności kredytowej AAA. Dla inwestora długoterminowego oznacza to połączenie bezpieczeństwa bilansu z dwucyfrowym wzrostem zysku na akcję (EPS).",
            ],
            "risk_factors": [
                "Wysokie wieloletnie nakłady kapitałowe na budowę centrów danych i energetyki obciążające krótkoterminowo amortyzację.",
            ],
        },
    ]

    for comp in raw_companies:
        p_str, c_str, is_pos = _get_quote(comp["ticker"], comp["default_price"], comp["default_change"])
        comp["price"] = p_str
        comp["change"] = c_str
        comp["is_positive"] = is_pos

    return raw_companies
