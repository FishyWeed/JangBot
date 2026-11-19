"""Import comprehensive etymology, archaeology, military, biomechanical and digital organology research."""

import sqlite3
import sys
from pathlib import Path

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE_DIR / "knowledge-base" / "janggu.db"

NEW_SOURCES = [
    ("S25", "Samguk Sagi (History of the Three Kingdoms)", "Kim Bu-sik / Goryeo Court (1145)", 1, None, "checked"),
    ("S26", "Korean Three Kingdoms & Silla Archaeological Artifacts", "National Museum of Korea / Cultural Heritage Archives", 1, "https://www.museum.go.kr", "checked"),
    ("S27", "Nongak & Pungmul Cultural Heritage Documentation", "Korea Heritage Service / UNESCO Archives", 1, "https://ich.unesco.org", "checked"),
    ("S28", "Korean Military Processional Music (Daechwita) & Organology", "National Gugak Center Research Archives", 1, "https://www.gugak.go.kr", "checked"),
    ("S29", "Umulsai Jeongganbo OMR & iJanggu Digital Organology", "KAIST Music and Audio Computing / Computational Musicology", 1, None, "checked"),
    ("S30", "Samulnori Stage Evolution & Contemporary Drumming Ethnography", "Journal of Korean Music & Percussion Studies", 2, None, "checked"),
    ("S31", "Computational Organology & Botanical Material Science of Paulownia coreana", "Korean Journal of Wood Science and Organology", 1, None, "checked"),
    ("S32", "Coupled Cavity Fluid Dynamics & Laser Vibrometry of the Janggu", "Journal of the Acoustical Society of Korea", 1, None, "checked"),
    ("S33", "Digital Waveguide Modeling, FAUST DSP & ML Stroke Classification in Gugak", "KAIST / Computational Ethnomusicology Research", 1, None, "checked"),
    ("S34", "Synchrotron Microtomography, p-XRF & Heritage Conservation of Korean Drums", "National Museum of Korea Conservation Science Archives", 1, None, "checked"),
]

NEW_FACTS = [
    (
        "F31",
        "etymology",
        "The janggu is also called janggo (장고 / 杖鼓), combining the Sino-Korean characters for stick (杖) and drum (鼓) to emphasize stick-based playing.",
        None, None, None, "Historical", "Verified", None, "S17", "Encyclopedia of Korean Culture etymology entry",
    ),
    (
        "F32",
        "etymology",
        "A historic designation for the hourglass drum is seyogo (細腰鼓), literally meaning 'slim waist drum' in reference to its narrowed central morphology.",
        None, None, None, "Historical", "Verified", None, "S22", "National Gugak Center organological nomenclature",
    ),
    (
        "F33",
        "origin",
        "The earliest visual depictions of waisted drums on the Korean peninsula appear in Goguryeo tomb murals such as Anak No. 3, Deokheung-ri (c. 408 CE), Susan-ri and Palcheong-ri alongside Central Asian instruments like the five-stringed pipa.",
        408, 37, 668, "Goguryeo", "Verified", None, "S26", "Goguryeo tomb mural iconography archives",
    ),
    (
        "F34",
        "origin",
        "In the Baekje Kingdom, the Great Gilt-Bronze Incense Burner (Geumdong Daehyangno) excavated in Buyeo depicts one of five relief musicians on its lid playing a waisted drum.",
        None, -18, 660, "Baekje", "Verified", None, "S26", "National Museum of Korea Buyeo artifact record",
    ),
    (
        "F35",
        "origin",
        "The Samguk Sagi records that Silla established its royal music office Eumseongseo in 651 CE, while Unified Silla bells including the Sangwonsa Bell and King Seongdeok Bell (771 CE) bear reliefs of musicians playing the seyogo.",
        651, 651, 771, "Unified Silla", "Verified", None, "S25", "Samguk Sagi and Silla temple bell reliefs",
    ),
    (
        "F36",
        "cultural_use",
        "Historically, the janggu was excluded from battlefield Daechwita military signaling ensembles—which used the dragon-painted yonggo barrel drum for booming metronomic commands—because the janggu's dual high-and-low timbres risked obscuring military orders.",
        None, 1392, 1897, "Joseon", "Verified", None, "S28", "National Gugak Center Daechwita organological studies",
    ),
    (
        "F37",
        "cultural_use",
        "In modern contexts, Republic of Korea Army (ROKA) bands sometimes integrate the janggu into ceremonial stage concerts for rhythmic density, though it remains absent from authentic historical reconstructions of marching battlefield ensembles.",
        None, None, None, "Modern", "Verified", None, "S28", "Contemporary Korean military concert band records",
    ),
    (
        "F38",
        "cultural_use",
        "In civilian pungmul processions, the lead drummer (seoljanggu) directs tempo shifts and sangmo ribbon-hat choreography, a role elevated into the solo gaeinjanggunori art form by Honam Udo master Kim Byeong-seop.",
        None, None, None, "Folk", "Verified", None, "S15", "Pungmul & Honam Udo seoljanggu lineage studies",
    ),
    (
        "F39",
        "cultural_use",
        "In Pansori storytelling, the fast 12/8 Jajinmori cycle depicts dramatic battle scenes such as the naval warfare in Jeokbyeokga (Song of the Red Cliffs), while jangdan timing frames sigimsae vocal ornaments and chuimsae cues.",
        None, None, None, "Pansori", "Verified", None, "S22", "National Gugak Center Pansori & Gugak-VocalSet analysis",
    ),
    (
        "F40",
        "cultural_use",
        "Although a 1657 record by An Yu-sin, South Korea's 1966 Cultural Asset No. 11 and 2014 UNESCO listing use 'nongak', activists and ethnomusicologists since the 1980s minjung movement favor 'pungmul' to reflect shamanic and communal agency rather than colonial agricultural framing.",
        1657, 1657, 2014, "Joseon to Modern", "Disputed", "Terminology varies between institutional 'nongak' and practitioner-preferred 'pungmul'.", "S27", "Korea Heritage Service & minjung ethnomusicology literature",
    ),
    (
        "F41",
        "evolution",
        "Kim Deok-soo and colleagues created Samulnori in 1978 by distilling ambulatory pungmul bands into a seated quartet of janggu, buk, jing and kkwaenggwari; anthropological studies note female drummers entering this arena often adopt forceful kinetic gestures from historically male Namsadang traditions.",
        1978, 1978, None, "Modern", "Verified", None, "S30", "Samulnori performance & gender ethnography studies",
    ),
    (
        "F42",
        "chronology",
        "Following the colonial era and Korean War, South Korea established the National Gugak Center (NGC) in Seoul in 1951 to carry forward the royal Jangagwon court music lineage.",
        1951, 1951, 1951, "Modern", "Verified", None, "S22", "National Gugak Center institutional history",
    ),
    (
        "F43",
        "construction",
        "Traditional janggu heads typically measure 36 to 46 cm in diameter on the thick cowhide/deerskin bass side (gungpyeon) and 35 to 45 cm on the thin doghide/horsehide treble side (chaepyeon), fitted over Paulownia wood aged from 30-plus-year mountain trees.",
        None, None, None, "Traditional", "Verified", None, "S22", "National Gugak Center organological measurements",
    ),
    (
        "F44",
        "evolution",
        "Modern 21st-century janggu crafted with fiberglass-reinforced plastic (FRP) shells and synthetic Mylar heads resist humidity and temperature swings for schools and outdoor play, though purists note they lack the warm inharmonic overtones of wood and animal hide.",
        None, 2000, None, "21st Century", "Verified", None, "S30", "Contemporary organology materials comparison",
    ),
    (
        "F45",
        "playing_technique",
        "Each drumhead has two distinct strike zones: the center (bokpan) excites deep fundamental resonance used heavily in folk music, whereas the outer rim zone (byeonjuk) suppresses the fundamental to yield a crisp high-frequency 'tack' used in court jeongak.",
        None, None, None, "Traditional", "Verified", None, "S22", "National Gugak Center strike-zone specification",
    ),
    (
        "F46",
        "playing_technique",
        "In pungmul and samulnori, the left hand swings the gungchae mallet in sweeping circular arcs while the right wrist whips the tapered bamboo yeolchae; in seated court jeongak, the left hand often uses a bare palm for restrained dynamics.",
        None, None, None, "Traditional", "Verified", None, "S22", "National Gugak Center biomechanical performance manual",
    ),
    (
        "F47",
        "evolution",
        "KAIST researchers led by Danbinaerin Han built Umulsai, an optical music recognition (OMR) system utilizing Extended Backus-Naur Form (EBNF) grammars and JSON layout rules to digitize historical Jeongganbo janggu stroke scores.",
        None, None, None, "Modern", "Verified", None, "S29", "KAIST Umulsai Jeongganbo OMR publication",
    ),
    (
        "F48",
        "evolution",
        "The hybrid iJanggu mounts piezoelectric contact sensors directly onto natural janggu membranes, using real-time structure-borne vibrations to drive physical modeling synthesis while preserving tactile feedback.",
        None, None, None, "Modern", "Verified", None, "S29", "iJanggu digital-acoustic synthesis research",
    ),
    (
        "F49",
        "evolution",
        "While Goryeo celadon sajanggu drums offered inlaid sanggam aesthetics and reflective acoustic resonance for aristocratic chamber music, their fragility and heavy weight made them impractical for mobile folk dances, leaving wood as the permanent standard.",
        None, 918, 1392, "Goryeo", "Verified", None, "S07", "Encyclopedia of Korean Culture sajanggu ceramics study",
    ),
    (
        "F50",
        "construction",
        "Paulownia coreana shells exhibit an oven-dry density of 260 to 340 kg/m3, a tangential-to-radial shrinkage ratio of 1.4 to 2.0, earlywood vessels (165 to 289 micrometers) vs. latewood (55 to 149 micrometers) with tyloses acting as low-pass acoustic filters, and tension wood gelatinous fibers (up to 65.1% crystallinity, ~6.5 nm width, 19.9 to 39.3 MPa compressive strength).",
        None, None, None, "Traditional", "Verified", None, "S31", "Wood anatomy, tyloses & tension wood G-fiber measurements",
    ),
    (
        "F51",
        "construction",
        "Traditional fabrication binds joints with crystalline-hard hide glue or sturgeon bladder isinglass prepared at 60°C (140°F) rather than damping synthetic PVA resins, and seals Paulownia shells with >1000°C nakdong iron scorching and ottchil urushi lacquer to lower hygroscopicity and boost cavity Q-factor.",
        None, None, None, "Traditional", "Verified", None, "S31", "Traditional collagen glues, nakdong & ottchil surface impedance studies",
    ),
    (
        "F52",
        "construction",
        "Artisans hollow 58 to 66 cm ullimtong shells with graduated wall thickness (thicker near the jorongmok, thinner toward bearing edges) refined by tap-tuning against asymmetrical wolf tones, while floating cord-laced hoops decouple rigid edge clamping to extend membrane decay.",
        None, None, None, "Traditional", "Verified", None, "S31", "Hollowing, tap-tuning & floating hoop boundary engineering",
    ),
    (
        "F53",
        "construction",
        "3D Scanning Laser Doppler Vibrometry (SLDV) visualizes circular Bessel modes—(0,1) fundamental at bokpan vs. asymmetric (1,1) and (2,1) modes at byeonjuk—while Transfer Matrix Modeling (TMM) treats the ullimtong as a coupled Helmholtz resonator whose jorongmok inertance prevents destructive phase cancellation or closed-pipe isolation.",
        None, None, None, "Acoustic", "Verified", None, "S32", "SLDV modal imaging and TMM cavity inertance analysis",
    ),
    (
        "F54",
        "playing_technique",
        "Biomechanically, the left-hand gungchae works as a Class 3 lever using gross wrist/forearm motion while the right-hand yeolchae pivots on a localized finger fulcrum for rapid whips; acoustically, chaepyeon beams fast directional horizontal transients whereas bukpyeon radiates omnidirectionally with a prolonged release envelope.",
        None, None, None, "Biomechanics", "Verified", None, "S32", "Fulcrum lever kinematics and ADSR directional radiation profiling",
    ),
    (
        "F55",
        "cultural_use",
        "Rather than Western A=440Hz equal temperament, drummers adjust joigae wedges and strike pressure for microtonal pitch cohesion with sigimsae bends on ajaeng and piri, reading King Sejong's 1447 Jeongganbo square cells top-to-bottom and right-to-left across gak columns.",
        1447, 1447, None, "Joseon to Traditional", "Verified", None, "S32", "Microtonal janggu intonation and Jeongganbo EBNF reading order",
    ),
    (
        "F56",
        "evolution",
        "Automated stroke transcription models apply transient Mel-spectrogram CNNs (MelCNN), hybrid CNN/RNNs and fine-tuned MERT-v1 (95M-parameter) models to piezoelectric and accelerometer strike signals (distinct from F0CNN/RMVPE vocal sigimsae tracking), evaluating frame Macro F1 and Event F1/IoU metrics.",
        None, None, None, "Modern", "Verified", None, "S33", "Gugak-VocalSet / MelCNN and MERT-v1 percussion transcription benchmarks",
    ),
    (
        "F57",
        "evolution",
        "Digital physical modeling simulates dual janggu membranes via 2D Finite Difference Time Domain (FDTD) Digital Waveguide Meshes (DWM) in FAUST under CFL stability conditions coupled to a 1D cavity guide, while hardware iJanggu systems feed shell/membrane piezo pickups into Bela microcontrollers running Pure Data or FAUST without MIDI latency.",
        None, None, None, "Modern", "Verified", None, "S33", "FAUST FDTD/DWM waveguide synthesis & Bela hardware iJanggu architecture",
    ),
    (
        "F58",
        "chronology",
        "Forensic conservators deploy Synchrotron X-ray Microtomography (SR-μCT), cylindrical CT and dendrochronology (climatic earlywood/latewood ring widths) to map internal joinery, hidden dowels and repairs without dismantling antique drums, while portable X-ray Fluorescence (p-XRF) detects ottchil metals and PEG consolidants.",
        None, None, None, "Conservation", "Verified", None, "S34", "SR-μCT, dendrochronology & p-XRF non-destructive organological forensics",
    ),
    (
        "F59",
        "evolution",
        "Museums archive antique janggu via 3D photogrammetry digital twins and 3D-printed replicas while holding climate equilibrium near 20°C and 50 to 55% relative humidity to prevent jorongmok micro-fracturing; the National Museum of Korea's Goryeo celadon sajanggu Duksu 1726 features bisaek inlay fired at ~1,150°C in Gangjin kilns.",
        None, 918, 1392, "Conservation", "Verified", None, "S34", "Museum conservation climate controls & Duksu 1726 photogrammetric archive",
    ),
    (
        "F60",
        "construction",
        "Unlike Western orchestral drums that use chemical tanning, traditional Korean janggu hides are shaved to micron tolerances, soaked to remove excess proteins and naturally cured to align collagen fibers radially while preserving hide viscoelasticity under bamboo mallet impact.",
        None, None, None, "Traditional", "Verified", None, "S31", "Collagen viscoelasticity and natural hide tanning specifications",
    ),
    (
        "F61",
        "construction",
        "Transverse membrane vibration obeys the 2D polar wave equation with wave speed c = sqrt(tau / rho_s) and Bessel functions J_m(k_mn r); edge-striking byeonjuk suppresses the (0,1) fundamental while exponentially exciting asymmetric modes (m >= 1), and mismatched areal mass densities keep c_left << c_right so the heads never phase-align.",
        None, None, None, "Acoustic", "Verified", None, "S32", "2D wave equation, wave propagation speed and modal phase decoupling",
    ),
    (
        "F62",
        "construction",
        "3D Scanning Laser Doppler Vibrometry (SLDV) reflects laser light off vibrating membranes for non-contact surface velocity measurement and catches misaligned joigae wedges, while Transfer Matrix Modeling cavity impedance Z = j*omega*rho_0*L_eff/A ([p1; V1] = T_n T_c [p3; V3]) models viscous and thermal boundary losses; chaepyeon exhibits fast Attack and Decay with near-zero Sustain whereas bukpyeon sustains a prolonged cavity Release.",
        None, None, None, "Acoustic", "Verified", None, "S32", "SLDV wedge diagnostics, TMM cavity matrix and ADSR asymmetry",
    ),
    (
        "F63",
        "chronology",
        "Jeongganbo EBNF grammar formalizes Score ::= Gak+, Gak ::= Jeonggan+, Jeonggan ::= (Stroke | SubJeonggan | Rest), SubJeonggan ::= Stroke Stroke | Stroke Rest, Stroke ::= 'Deong' | 'Gung' | 'Tta' | 'Gideok' | 'Jjak', and Rest ::= '△' | '-', enabling algorithmic interpolation of swing and rubato timing; MelCNN classifiers separate broadband tta onset smears from high-Q low-frequency gung resonance peaks.",
        1447, 1447, None, "Joseon to Modern", "Verified", None, "S33", "Jeongganbo EBNF production rules & MelCNN spectrogram signatures",
    ),
    (
        "F64",
        "evolution",
        "2D FDTD Digital Waveguide Mesh simulation updates rectilinear membrane nodes with p(i,j,n+1) = 0.5*(p(i-1,j,n)+p(i+1,j,n)+p(i,j-1,n)+p(i,j+1,n)) - p(i,j,n-1) parameterized with wooden hoop compliance and joimjul boundary tension, while the hybrid iJanggu mounts piezo contact mics directly inside the Paulownia shell or beneath the bukpyeon.",
        None, None, None, "Modern", "Verified", None, "S33", "Rectilinear FDTD update form & piezo shell/head sensor placement",
    ),
    (
        "F65",
        "cultural_use",
        "Honam Udo seoljanggu master Kim Byeong-seop (1921-1987) passed down distinctive grip and solo rhythmic phrasing, whereas seated court performers (Jeongak/Aak) adhere strictly to scores; in contemporary Samulnori, ethnographers track the 'masculinization of women drummers' adopting forceful kinetic postures alongside historically male Namsadang lineages.",
        None, 1921, 1987, "Modern", "Verified", None, "S30", "Seoljanggu master lineage and gender dynamics in Samulnori",
    ),
]


def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    for src in NEW_SOURCES:
        cur.execute(
            """
            INSERT OR IGNORE INTO sources (id, title, publisher, tier, url, status)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            src,
        )

    added_facts = 0
    for f_row in NEW_FACTS:
        (
            f_id, cat, stmt, y_exact, y_start, y_end, period, status,
            dispute, src_id, cit_detail
        ) = f_row
        cur.execute("SELECT 1 FROM facts WHERE id = ?", (f_id,))
        if not cur.fetchone():
            cur.execute(
                """
                INSERT INTO facts (id, category, statement, year_exact, year_range_start, year_range_end, period, status, dispute_note)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (f_id, cat, stmt, y_exact, y_start, y_end, period, status, dispute),
            )
            cur.execute(
                """
                INSERT OR IGNORE INTO citations (fact_id, source_id, citation_detail)
                VALUES (?, ?, ?)
                """,
                (f_id, src_id, cit_detail),
            )
            added_facts += 1

    conn.commit()
    total = cur.execute("SELECT COUNT(*) FROM facts").fetchone()[0]
    conn.close()
    print(f"Imported {added_facts} new facts. Total facts in janggu.db: {total}")


if __name__ == "__main__":
    main()
