"""Idempotent migration and validation script for JangBot's verified semantic network."""

import json
import sqlite3
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

BASE_DIR = Path(__file__).resolve().parent.parent.parent
SCHEMA_PATH = BASE_DIR / "knowledge-base" / "schema.sql"
DEFAULT_DB_PATH = BASE_DIR / "knowledge-base" / "janggu.db"

# (id, label, korean_name, node_type, category, summary, aliases)
CONCEPT_NODES: List[Tuple[str, str, Optional[str], str, str, str, List[str]]] = [
    # Instruments
    ("janggu", "Janggu", "장구", "instrument", "construction", "Double-headed Korean hourglass drum (~66 cm long) with asymmetric hides and wooden body.", ["janggu", "janggo", "changgo", "chang-go", "hourglass drum", "seyogo", "장구", "장고", "세요고"]),
    ("idakka", "Indian Idakka", None, "instrument", "origin", "Ancient Indian hourglass drum forming the Silk Road ancestral predecessor of the janggu.", ["idakka", "edakka", "indian idakka"]),
    ("yogo", "Yogo Waist Drum", "요고", "instrument", "origin", "Compact Silla-period waist drum adapted from the Indian idakka.", ["yogo", "waist drum", "요고"]),
    ("galgo", "Galgo", "갈고", "instrument", "chronology", "Related court hourglass drum with symmetrical skins played with two thin sticks.", ["galgo", "갈고"]),
    ("sajanggu", "Celadon Sajanggu", "사장구", "instrument", "chronology", "Goryeo-dynasty ceramic-bodied celadon janggu with inlaid sanggam craftsmanship.", ["sajanggu", "celadon janggu", "ceramic janggu", "celadon sajanggu", "사장구"]),
    ("yonggo", "Yonggo Barrel Drum", "용고", "instrument", "cultural_use", "Dragon-painted single-timbre barrel drum used for Daechwita military signaling commands.", ["yonggo", "war drum", "barrel drum", "용고"]),
    ("ijanggu", "iJanggu", None, "instrument", "evolution", "Hybrid janggu mounting piezoelectric sensors onto natural membranes for physical modeling synthesis.", ["ijanggu", "hybrid janggu", "piezo janggu"]),
    ("synthetic_janggu", "Synthetic FRP/Mylar Janggu", None, "instrument", "evolution", "Modern 21st-century weather-resistant janggu using FRP shells and Mylar heads.", ["synthetic janggu", "plastic janggu", "fiberglass janggu"]),
    ("ajaeng", "Ajaeng", "아쟁", "instrument", "cultural_use", "Traditional Korean bowed string instrument whose microtonal sigimsae bends guide janggu tuning.", ["ajaeng", "아쟁"]),
    ("piri", "Piri", "피리", "instrument", "cultural_use", "Traditional Korean double-reed bamboo oboe accompanied with microtonal pitch cohesion.", ["piri", "피리"]),
    ("pipa", "Five-Stringed Pipa", None, "instrument", "origin", "Central Asian lute depicted beside waisted drums in 5th-century Goguryeo tomb murals.", ["pipa", "five-stringed pipa"]),

    # Components
    ("ullimtong", "Ullimtong (Resonator Body)", "울림통", "component", "construction", "Hollowed single-block wooden hourglass resonator shell (58–66 cm long).", ["ullimtong", "resonator body", "wooden body", "drum body", "drum shell", "body", "shell", "울림통"]),
    ("jorongmok", "Jorongmok (Central Waist)", "조롱목", "component", "construction", "Narrow central waist tube regulating airflow and acting as an acoustic choke between chambers.", ["jorongmok", "narrow waist", "central waist", "waist", "middle tube", "central tube", "조롱목"]),
    ("gungpyeon", "Gungpyeon (Left Bass Head)", "궁편", "component", "construction", "Thick left drumhead (36–46 cm) producing deep, resonant bass tones.", ["gungpyeon", "bukpyeon", "left head", "left side", "bass head", "bass side", "thick head", "궁편", "북편"]),
    ("chaepyeon", "Chaepyeon (Right Treble Head)", "채편", "component", "construction", "Thin right drumhead (35–45 cm) producing sharp, bright treble transients.", ["chaepyeon", "right head", "right side", "treble head", "treble side", "thin head", "채편"]),
    ("joimjul", "Joimjul (Tension Cords)", "조임줄", "component", "construction", "Continuous V-shaped lacing cords connecting both drumheads across the hourglass shell.", ["joimjul", "tension cords", "cords", "lacing", "ropes", "v-shaped cords", "조임줄", "부편"]),
    ("joigae", "Joigae (Tuning Wedges)", "조이개", "component", "construction", "Movable leather or wooden wedges sliding along joimjul cords to tighten or loosen pitch.", ["joigae", "tuning wedges", "leather wedges", "wedges", "sliding wedges", "조이개"]),
    ("bokpan", "Bokpan (Center Strike Zone)", "복판", "component", "playing_technique", "Center strike zone of the drumhead exciting the deep (0,1) fundamental mode.", ["bokpan", "center strike zone", "center of the head", "복판"]),
    ("byeonjuk", "Byeonjuk (Rim Strike Zone)", "변죽", "component", "playing_technique", "Outer rim strike zone suppressing the (0,1) fundamental for a crisp court tack.", ["byeonjuk", "rim strike zone", "rim edge", "outer rim", "변죽"]),
    ("floating_hoops", "Floating Cord-Laced Hoops", None, "component", "construction", "Metal/wooden hoops suspended by cords rather than rigid clamps to extend membrane decay.", ["floating hoops", "metal hoops", "hoops", "cord-laced hoops"]),

    # Materials
    ("paulownia_coreana", "Paulownia coreana Wood", "오동나무", "material", "construction", "Low-density (260–340 kg/m3) Korean Paulownia hardwood from 30+ year mountain trees.", ["paulownia", "paulownia coreana", "paulownia wood", "오동나무"]),
    ("cowhide", "Cowhide", None, "material", "construction", "Thick cattle leather stretched on the left gungpyeon head for low bass resonance.", ["cowhide", "cow skin", "cow hide"]),
    ("deerskin", "Deerskin", None, "material", "construction", "Thick deer hide alternatively used on the 36–46 cm left bass head (gungpyeon).", ["deerskin", "deer skin", "deer hide"]),
    ("horsehide", "Horsehide", None, "material", "construction", "Thin horse leather stretched on the right chaepyeon head for sharp treble attack.", ["horsehide", "horse skin", "horse hide"]),
    ("doghide", "Doghide", None, "material", "construction", "Thin dog leather alternatively used on the 35–45 cm right treble head (chaepyeon).", ["doghide", "dogskin", "dog skin", "dog hide"]),
    ("bamboo", "Bamboo", None, "material", "playing_technique", "Flexible bamboo (strip and boiled root) used to fashion both yeolchae and gungchae.", ["bamboo", "bamboo root"]),
    ("celadon_ceramic", "Celadon Ceramic", None, "material", "evolution", "Glazed Goryeo ceramic clay with sanggam/bisaek inlay used for luxury sajanggu shells.", ["celadon", "ceramic", "celadon ceramic", "bisaek"]),
    ("hide_glue_isinglass", "Hide Glue & Sturgeon Isinglass", None, "material", "construction", "Traditional 60°C crystalline-hard protein adhesives avoiding damping synthetic PVA resins.", ["isinglass", "hide glue", "fish glue", "sturgeon isinglass"]),
    ("ottchil_lacquer", "Ottchil Urushi Lacquer", "옻칠", "material", "construction", "Traditional tree-sap urushi coating lowering wood hygroscopicity and boosting cavity Q-factor.", ["ottchil", "urushi", "lacquer", "ottchil lacquer", "옻칠"]),
    ("frp_shell", "Fiberglass-Reinforced Plastic (FRP)", None, "material", "evolution", "Weather-resistant synthetic composite shell material used on modern practice janggu.", ["frp", "fiberglass", "fiberglass-reinforced plastic"]),
    ("mylar_head", "Synthetic Mylar Head", None, "material", "evolution", "Humidity-resistant synthetic drumhead film used on modern school and outdoor janggu.", ["mylar", "synthetic head", "plastic head"]),

    # Implements
    ("yeolchae", "Yeolchae (Bamboo Whip)", "열채", "implement", "playing_technique", "Thin, flexible right-hand bamboo stick snapping sharp treble accents off chaepyeon.", ["yeolchae", "bamboo stick", "whip stick", "thin stick", "right stick", "열채"]),
    ("gungchae", "Gungchae (Bass Mallet)", "궁채", "implement", "playing_technique", "Round hardwood/antler mallet on a bamboo root swung in the left hand for booming bass.", ["gungchae", "mallet", "bass stick", "left stick", "round stick", "궁채"]),
    ("bare_left_hand", "Bare Left Palm", None, "implement", "playing_technique", "Unassisted left palm or fingertips striking gungpyeon for restrained court Jeongak dynamics.", ["bare palm", "bare left hand", "left hand", "bare hand"]),
    ("sangmo", "Sangmo Ribbon Hat", "상모", "implement", "cultural_use", "Spinning ribbon hat worn by pungmul and seoljanggu drummers during kinetic choreography.", ["sangmo", "ribbon hat", "상모"]),

    # Techniques & Strokes
    ("deong", "Deong Stroke", "덩", "technique_stroke", "playing_technique", "Simultaneous left and right strike anchoring primary rhythmic downbeats.", ["deong", "덩"]),
    ("gung", "Gung Stroke", "궁", "technique_stroke", "playing_technique", "Deep left-hand bass strike on gungpyeon producing high-Q low resonance.", ["gung", "궁"]),
    ("tta", "Tta Stroke", "따", "technique_stroke", "playing_technique", "Crisp right-hand treble strike on chaepyeon with broadband onset energy.", ["tta", "따"]),
    ("gideok", "Gi-deok Stroke", "기덕", "technique_stroke", "playing_technique", "Rapid right-hand whip flam grace note ornamenting treble phrasing.", ["gideok", "gi-deok", "flam", "기덕"]),
    ("jjak", "Kkol / Jjak Rimshot", "짝", "technique_stroke", "playing_technique", "Sharp rimshot strike catching treble edge skin against the hoop.", ["jjak", "kkol", "rimshot", "짝"]),
    ("nakdong_scorching", "Nakdong Iron Scorching", "낙동", "technique_stroke", "construction", "Fire-scorching Paulownia wood above 1000°C to seal pores, cross-link cellulose and boost Q-factor.", ["nakdong", "scorching", "fire scorching", "flame scorching", "낙동"]),
    ("tap_tuning", "Graduated Tap-Tuning", None, "technique_stroke", "construction", "Carving graduated shell wall thickness by ear to suppress asymmetrical wolf tones.", ["tap-tuning", "tap tuning", "graduated wall hollowing"]),
    ("natural_hide_curing", "Natural Radial Hide Curing", None, "technique_stroke", "construction", "Micron shaving, soaking and natural curing aligning collagen fibers radially for viscoelasticity.", ["hide curing", "natural curing", "tanning", "collagen alignment"]),
    ("class_3_lever", "Class 3 Lever Biomechanics", None, "technique_stroke", "playing_technique", "Gross wrist and forearm lever mechanics powering left-hand gungchae bass arcs.", ["class 3 lever", "lever"]),
    ("finger_fulcrum", "Localized Finger Fulcrum", None, "technique_stroke", "playing_technique", "Fine-motor finger pivot driving rapid right-hand yeolchae whips.", ["finger fulcrum", "fulcrum"]),

    # Rhythms
    ("jangdan", "Jangdan Rhythmic Cycles", "장단", "rhythm", "cultural_use", "Traditional Korean named rhythmic time cycles shaping tempo, meter and dramatic mood.", ["jangdan", "rhythmic cycles", "rhythms", "장단"]),
    ("jinyangjo", "Jinyangjo (24-Beat)", "진양조", "rhythm", "cultural_use", "Slowest 24-beat rhythmic cycle conveying sorrow, dignity and tragic Pansori scenes.", ["jinyangjo", "진양조"]),
    ("jungmori", "Jungmori (12-Beat)", "중모리", "rhythm", "cultural_use", "Moderate 12-beat walking cycle used for lyrical storytelling and beginner coordination.", ["jungmori", "중모리"]),
    ("jungjungmori", "Jungjungmori (12-Beat)", "중중모리", "rhythm", "cultural_use", "Lilting 12-beat cycle used for cheerful storytelling and spirited folk dances.", ["jungjungmori", "중중모리"]),
    ("jajinmori", "Jajinmori (12/8 Urgent)", "자진모리", "rhythm", "cultural_use", "Rapid 12-beat (12/8) cycle scoring urgent action and battles like Jeokbyeokga.", ["jajinmori", "자진모리"]),
    ("hwimori", "Hwimori (4-Beat Sprint)", "휘모리", "rhythm", "cultural_use", "Fastest standard 4-beat cycle driving performances to a breathless climax.", ["hwimori", "휘모리"]),
    ("gutgeori", "Gutgeori (12-Beat Swing)", "굿거리", "rhythm", "cultural_use", "Syncopated 12-beat swinging cycle central to folk dance, shamanic rites and Sanjo.", ["gutgeori", "굿거리"]),
    ("eonmori", "Eonmori (10-Beat Asymmetric)", "엇모리", "rhythm", "cultural_use", "Asymmetric 10-beat (3+2+3+2) cycle signaling mysterious, supernatural or heroic figures.", ["eonmori", "엇모리"]),
    ("chuimsae", "Chuimsae Vocal Cries", "추임새", "rhythm", "cultural_use", "Spontaneous vocal cheers such as 'Eolssigu!' and 'Jota!' steering live pacing and energy.", ["chuimsae", "eolssigu", "jota", "vocal cries", "추임새"]),
    ("sigimsae", "Sigimsae Vocal/Melodic Ornaments", "시김새", "rhythm", "cultural_use", "Microtonal pitch bends and vocal/melodic ornaments framed by jangdan and wedge tuning.", ["sigimsae", "시김새"]),

    # Genres & Traditions
    ("jeongak", "Jeongak Royal Court Music", "정악", "genre_tradition", "cultural_use", "Seated royal court ceremonial music emphasizing Neo-Confucian poise and restrained rim taps.", ["jeongak", "court music", "royal court music", "aak", "정악"]),
    ("nongak_pungmul", "Nongak / Pungmul Folk Band", "농악 / 풍물", "genre_tradition", "cultural_use", "Ambulatory community drumming, harvest celebration and ritual dance tradition.", ["nongak", "pungmul", "farmers music", "folk music", "농악", "풍물"]),
    ("samulnori", "Samulnori Quartet", "사물놀이", "genre_tradition", "evolution", "Seated four-instrument percussion quartet (janggu, buk, jing, kkwaenggwari) founded in 1978.", ["samulnori", "samul nori", "사물놀이"]),
    ("pansori", "Pansori Vocal Storytelling", "판소리", "genre_tradition", "cultural_use", "Traditional Korean narrative singing accompanied by jangdan timing and chuimsae cues.", ["pansori", "판소리"]),
    ("sanjo", "Sanjo Solo Instrumental", "산조", "genre_tradition", "cultural_use", "Expressive solo instrumental genre unfolding across progressively accelerating jangdan cycles.", ["sanjo", "산조"]),
    ("shamanic_ritual", "Shamanic Rituals (Musok / Gut)", "무속 / 굿", "genre_tradition", "cultural_use", "Traditional Korean spiritual ceremonies accompanied by swinging Gutgeori and janggu rhythms.", ["shamanic ritual", "shamanic rituals", "shamanism", "musok", "gut"]),
    ("daechwita", "Daechwita Military Procession", "대취타", "genre_tradition", "cultural_use", "Royal military signaling band that marched with the yonggo barrel drum rather than the janggu.", ["daechwita", "military band", "military procession", "대취타"]),
    ("janggu_dance", "Janggu Dance Choreography", "장구춤", "genre_tradition", "chronology", "Strapped-drum traditional dance adapted for modern international theater stages in the 1930s.", ["janggu dance", "stage dance", "장구춤"]),
    ("seoljanggu", "Seoljanggu Lead Drummer", "설장구", "genre_tradition", "cultural_use", "Lead drummer directing pungmul tempo changes and sangmo hat choreography.", ["seoljanggu", "설장구"]),
    ("gaeinjanggunori", "Gaeinjanggunori Solo Art", "개인장구놀이", "genre_tradition", "cultural_use", "Virtuosic solo janggu performance form elevated by Honam Udo master Kim Byeong-seop.", ["gaeinjanggunori", "solo janggu"]),
    ("jeokbyeokga", "Jeokbyeokga (Song of the Red Cliffs)", "적벽가", "genre_tradition", "cultural_use", "Pansori epic depicting naval battle scenes scored with fast 12/8 Jajinmori.", ["jeokbyeokga", "song of the red cliffs", "적벽가"]),

    # Acoustic & Scientific Concepts
    ("acoustic_choke", "Mechanical Acoustic Choke", None, "acoustic_concept", "construction", "Airflow constriction in jorongmok coupling bass resonance while preventing treble damping.", ["acoustic choke", "choke"]),
    ("bessel_modes", "Circular Bessel Vibration Modes", None, "acoustic_concept", "construction", "Inharmonic membrane overtones governed by Bessel function zeros J_m(k_mn r).", ["bessel", "bessel modes", "inharmonic overtones", "wave equation", "overtones"]),
    ("helmholtz_resonator", "Coupled Helmholtz Resonator", None, "acoustic_concept", "construction", "Dual-chamber cavity model where jorongmok inertance prevents phase cancellation.", ["helmholtz", "helmholtz resonator", "inertance"]),
    ("wolf_tones", "Asymmetrical Wolf Tones", None, "acoustic_concept", "construction", "Harsh unwanted cavity resonances carved out during graduated wall tap-tuning.", ["wolf tones", "wolf tone"]),
    ("q_factor", "High Acoustic Q-Factor", None, "acoustic_concept", "construction", "Enhanced internal wave reflection and lower hygroscopicity from nakdong and ottchil.", ["q-factor", "q factor", "hygroscopicity"]),
    ("microtonal_tuning", "Microtonal Ensemble Tuning", None, "acoustic_concept", "cultural_use", "Flexible wedge and hand-pressure tuning rejecting rigid A=440Hz equal temperament.", ["microtonal tuning", "microtonal", "440hz", "equal temperament"]),
    ("hornbostel_211_242", "Hornbostel-Sachs 211.242", None, "acoustic_concept", "construction", "Organological classification designating a double-headed, waisted hourglass membranophone.", ["hornbostel-sachs", "hornbostel", "211.242"]),
    ("tyloses_filter", "Tyloses Acoustic Low-Pass Filter", None, "acoustic_concept", "construction", "Earlywood vessel tyloses (165–289 μm) acting as natural internal low-pass acoustic filters.", ["tyloses", "earlywood", "latewood"]),
    ("g_fibers", "Tension Wood G-Fibers", None, "acoustic_concept", "construction", "Gelatinous wood fibers (up to 65.1% crystallinity, 19.9–39.3 MPa) resisting wedge compression.", ["g-fibers", "g-fiber", "tension wood", "crystallinity"]),

    # Historical Records & Artifacts
    ("goryeosa", "Goryeosa (1076 AD)", "고려사", "historical_record", "chronology", "Official History of Goryeo logging the earliest court post janggu-opsa in 1076 AD.", ["goryeosa", "history of goryeo", "고려사"]),
    ("janggu_opsa", "Janggu-opsa Court Instructor", "장구업사", "historical_record", "chronology", "Earliest documented state janggu instructor title (1076 AD, King Munjong).", ["janggu-opsa", "janggu instructor"]),
    ("akhak_gwebeom", "Akhak Gwebeom (1493)", "악학궤범", "historical_record", "chronology", "Joseon Canon of Music codifying asymmetric janggu construction vs. symmetrical galgo.", ["akhak gwebeom", "canon of music", "manual of musicology", "악학궤범"]),
    ("jeongganbo", "Jeongganbo Grid Notation (1447)", "정간보", "historical_record", "chronology", "15th-century spatial 2D grid score recording exact durations and janggu strokes across gak columns.", ["jeongganbo", "grid notation", "gak", "정간보"]),
    ("goguryeo_murals", "5th-Century Goguryeo Tomb Murals", None, "historical_record", "origin", "Anak No. 3, Deokheung-ri (c. 408 CE), Susan-ri and Palcheong-ri murals showing waisted drums.", ["goguryeo murals", "anak", "deokheung-ri", "susan-ri", "palcheong-ri", "murals"]),
    ("geumdong_daehyangno", "Baekje Geumdong Daehyangno", "백제금동대향로", "historical_record", "origin", "Great Gilt-Bronze Incense Burner excavated in Buyeo featuring a relief waisted-drum player.", ["geumdong daehyangno", "incense burner", "baekje incense burner"]),
    ("sangwonsa_bell", "Sangwonsa Bronze Bell", "상원사 동종", "historical_record", "origin", "Unified Silla temple bell bearing relief carvings of musicians playing the seyogo.", ["sangwonsa", "sangwonsa bell"]),
    ("seongdeok_bell", "King Seongdeok Bell (771 CE)", "성덕대왕신종", "historical_record", "origin", "771 CE Unified Silla bronze bell embossed with celestial seyogo musicians.", ["seongdeok bell", "king seongdeok bell"]),
    ("met_changgo", "19th-Century Joseon Changgo", None, "historical_record", "chronology", "Preserved 1800s Korean changgo held in The Metropolitan Museum of Art collection.", ["met changgo", "19th-century changgo"]),
    ("duksu_1726", "Celadon Sajanggu Duksu 1726", "덕수 1726", "historical_record", "evolution", "Goryeo bisaek inlaid celadon sajanggu fired at ~1,150°C in Gangjin kilns.", ["duksu 1726", "duksu"]),
    ("unesco_nongak", "UNESCO Intangible Heritage (2014)", None, "historical_record", "chronology", "2014 UNESCO inscription recognizing Nongak community drumming, dance and rituals.", ["unesco", "unesco nongak", "intangible heritage"]),

    # People, Institutions & Modern Science/Tech
    ("king_yejong", "King Yejong of Goryeo", "예종", "person_institution_tech", "chronology", "Goryeo monarch whose 1114 AD Song Dynasty instrument import standardized hourglass proportions.", ["king yejong", "yejong"]),
    ("king_sejong", "King Sejong the Great", "세종대왕", "person_institution_tech", "chronology", "15th-century Joseon monarch who created the Jeongganbo 2D grid notation system.", ["king sejong", "sejong"]),
    ("seong_hyeon", "Seong Hyeon", "성현", "person_institution_tech", "chronology", "Joseon scholar who compiled the 1493 Akhak Gwebeom treatise.", ["seong hyeon"]),
    ("choi_seung_hee", "Choi Seung-hee", "최승희", "person_institution_tech", "chronology", "1930s pioneering dancer who brought janggu dance choreography to international stages.", ["choi seung-hee", "choi seung hee"]),
    ("kim_deok_soo", "Kim Deok-soo", "김덕수", "person_institution_tech", "evolution", "Master percussionist who co-founded the seated Samulnori quartet in 1978.", ["kim deok-soo", "kim duk-soo"]),
    ("kim_byeong_seop", "Kim Byeong-seop", "김병섭", "person_institution_tech", "cultural_use", "Honam Udo seoljanggu master (1921–1987) who elevated solo gaeinjanggunori repertoire.", ["kim byeong-seop"]),
    ("danbinaerin_han", "Danbinaerin Han", None, "person_institution_tech", "evolution", "KAIST researcher who led the Umulsai OMR digitization of Jeongganbo drum scores.", ["danbinaerin han"]),
    ("eumseongseo", "Eumseongseo (651 CE)", "음성서", "person_institution_tech", "origin", "Silla royal music bureau established in 651 CE as recorded in the Samguk Sagi.", ["eumseongseo"]),
    ("jangagwon", "Jangagwon Royal Music Bureau", "장악원", "person_institution_tech", "chronology", "Joseon royal court music institution whose lineage continues in the National Gugak Center.", ["jangagwon"]),
    ("national_gugak_center", "National Gugak Center (1951)", "국립국악원", "person_institution_tech", "chronology", "Seoul institution founded in 1951 continuing royal Jangagwon court music heritage.", ["national gugak center", "ngc"]),
    ("national_museum_korea", "National Museum of Korea", "국립중앙박물관", "person_institution_tech", "chronology", "Seoul museum preserving Goryeo celadon sajanggu treasures including Duksu 1726.", ["national museum of korea"]),
    ("met_museum", "The Metropolitan Museum of Art", None, "person_institution_tech", "chronology", "New York museum housing a preserved 19th-century Korean changgo.", ["met museum", "the met", "metropolitan museum"]),
    ("gangjin_kilns", "Gangjin Celadon Kilns", "강진 가마", "person_institution_tech", "evolution", "Historic Goryeo ceramic kilns firing bisaek celadon sajanggu around 1,150°C.", ["gangjin", "gangjin kilns"]),
    ("kaist_umulsai", "KAIST Umulsai OMR System", "우물사이", "person_institution_tech", "evolution", "Optical Music Recognition system digitizing Jeongganbo scores using EBNF and JSON rules.", ["umulsai", "kaist", "omr"]),
    ("jeongganbo_ebnf", "Jeongganbo EBNF Formal Grammar", None, "person_institution_tech", "chronology", "Formal grammar (Score ::= Gak+, Jeonggan ::= Stroke|SubJeonggan|Rest) enabling digital swing/rubato.", ["ebnf", "formal grammar", "subjeonggan"]),
    ("sldv", "3D Scanning Laser Doppler Vibrometry (SLDV)", None, "person_institution_tech", "construction", "Non-contact laser vibrometry mapping circular Bessel modes and spotting misaligned joigae.", ["sldv", "vibrometry", "laser doppler"]),
    ("tmm", "Transfer Matrix Modeling (TMM)", None, "person_institution_tech", "construction", "Acoustic cavity impedance modeling treating ullimtong and jorongmok as a coupled Helmholtz resonator.", ["tmm", "transfer matrix"]),
    ("melcnn_mert", "MelCNN & MERT-v1 Transcription", None, "person_institution_tech", "evolution", "Spectrogram CNN and 95M-parameter MERT-v1 models classifying tta onset smears vs. gung peaks.", ["melcnn", "mert", "mert-v1", "f0cnn", "rmvpe"]),
    ("fdtd_faust", "FAUST 2D FDTD Waveguide Mesh", None, "person_institution_tech", "evolution", "CFL-stable 2D FDTD digital waveguide simulation of dual membranes running on Bela boards.", ["faust", "fdtd", "dwm", "bela", "pure data", "cfl"]),
    ("sr_uct", "Synchrotron X-ray Microtomography (SR-μCT)", None, "person_institution_tech", "chronology", "Non-destructive CT and dendrochronology imaging inspecting internal dowels, glue and wood rings.", ["sr-uct", "microtomography", "ct scan", "dendrochronology"]),
    ("p_xrf", "Portable X-ray Fluorescence (p-XRF)", None, "person_institution_tech", "chronology", "Non-destructive chemical analysis identifying antique ottchil metals and PEG consolidants.", ["p-xrf", "xrf", "peg"]),
    ("photogrammetry_3d", "3D Photogrammetry Archiving", None, "person_institution_tech", "evolution", "Digital twin scanning and 20°C / 50–55% RH conservation protecting antique janggu shells.", ["photogrammetry", "conservation", "digital twins"]),
    ("roka_bands", "Republic of Korea Army (ROKA) Bands", None, "person_institution_tech", "cultural_use", "Modern South Korean military bands featuring the janggu in ceremonial stage concerts.", ["roka", "roka bands", "army bands"]),
]

# (subject_id, predicate, object_id, fact_id, qualifier)
SEMANTIC_RELATIONS: List[Tuple[str, str, str, str, Optional[str]]] = [
    # Core classification & structure
    ("janggu", "classified_as", "hornbostel_211_242", "F11", "Double-headed waisted hourglass membranophone"),
    ("janggu", "has_part", "ullimtong", "F01", "~66 cm wooden hourglass resonator"),
    ("janggu", "has_part", "ullimtong", "F16", "Single-block carved Paulownia shell"),
    ("janggu", "has_part", "jorongmok", "F03", "Narrow central waist tube"),
    ("janggu", "has_part", "jorongmok", "F32", "Historic name seyogo (細腰鼓) highlights slim waist morphology"),
    ("janggu", "played_with", "yeolchae", "F31", "Etymology janggo (杖鼓) pairs stick and drum"),
    ("ullimtong", "has_part", "jorongmok", "F03", "Central tube connecting the two sound chambers"),
    ("ullimtong", "has_part", "jorongmok", "F52", "Graduated wall thicker near jorongmok"),
    ("janggu", "has_part", "gungpyeon", "F02", "Thick left bass head"),
    ("janggu", "has_part", "chaepyeon", "F02", "Thin right treble head"),
    ("janggu", "has_part", "joimjul", "F18", "Continuous V-shaped tension cords"),
    ("janggu", "has_part", "joigae", "F18", "Sliding leather or wood wedges"),
    ("janggu", "has_part", "floating_hoops", "F01", "Skin heads mounted on cord-tensioned hoops"),
    ("janggu", "has_part", "floating_hoops", "F52", "Decouples rigid clamping to extend decay"),
    ("gungpyeon", "has_part", "bokpan", "F45", "Center strike zone"),
    ("chaepyeon", "has_part", "bokpan", "F45", "Center strike zone"),
    ("chaepyeon", "has_part", "byeonjuk", "F45", "Outer rim strike zone"),

    # Materials & craftsmanship
    ("ullimtong", "made_of", "paulownia_coreana", "F16", "Single block cured 2-3 years"),
    ("ullimtong", "made_of", "paulownia_coreana", "F43", "30-plus-year mountain trees"),
    ("paulownia_coreana", "has_part", "tyloses_filter", "F50", "Earlywood vessels 165-289 micrometers"),
    ("paulownia_coreana", "has_part", "g_fibers", "F50", "Up to 65.1% crystallinity, 19.9-39.3 MPa"),
    ("ullimtong", "finished_with", "hide_glue_isinglass", "F51", "Prepared at 60°C for crystalline-hard joints"),
    ("ullimtong", "finished_with", "nakdong_scorching", "F51", "Iron scorching above 1000°C"),
    ("ullimtong", "finished_with", "ottchil_lacquer", "F51", "Urushi coating sealing cellulose pores"),
    ("nakdong_scorching", "produces", "q_factor", "F51", "Lowers hygroscopicity and boosts cavity Q-factor"),
    ("ottchil_lacquer", "produces", "q_factor", "F51", "Reflects cavity waves and boosts Q-factor"),
    ("ullimtong", "tuned_by", "tap_tuning", "F52", "Graduated wall thickness 58-66 cm"),
    ("tap_tuning", "prevents", "wolf_tones", "F52", "Eliminates asymmetrical cavity wolf tones"),
    ("gungpyeon", "made_of", "cowhide", "F02", "Thick hide for low bass tones"),
    ("gungpyeon", "made_of", "deerskin", "F43", "36-46 cm bass diameter"),
    ("chaepyeon", "made_of", "horsehide", "F02", "Thin hide for high treble tones"),
    ("chaepyeon", "made_of", "doghide", "F02", "Thin hide for high treble tones"),
    ("chaepyeon", "made_of", "doghide", "F43", "35-45 cm treble diameter"),
    ("gungpyeon", "finished_with", "natural_hide_curing", "F60", "Shaved to micron tolerances, collagen aligned radially"),
    ("chaepyeon", "finished_with", "natural_hide_curing", "F60", "Preserves viscoelasticity without chemical tanning"),
    ("gungpyeon", "tuned_by", "joimjul", "F18", "Continuous V-shaped lacing"),
    ("chaepyeon", "tuned_by", "joimjul", "F18", "Continuous V-shaped lacing"),
    ("joimjul", "tuned_by", "joigae", "F18", "Sliding wedges tighten or loosen head tension"),
    ("joigae", "produces", "microtonal_tuning", "F55", "Adjusts bass resonance for ajaeng and piri sigimsae"),
    ("synthetic_janggu", "made_of", "frp_shell", "F44", "Humidity-resistant composite shell"),
    ("synthetic_janggu", "made_of", "mylar_head", "F44", "Weather-resistant synthetic membrane"),
    ("sajanggu", "made_of", "celadon_ceramic", "F49", "Inlaid sanggam ceramic body for chamber acoustics"),

    # Acoustics & physics
    ("jorongmok", "acts_as", "acoustic_choke", "F17", "Prevents high-frequency treble damping while coupling bass"),
    ("ullimtong", "acts_as", "helmholtz_resonator", "F53", "Coupled dual-chamber cavity resonator"),
    ("gungpyeon", "produces", "bessel_modes", "F30", "Circular membrane inharmonic overtones"),
    ("chaepyeon", "produces", "bessel_modes", "F30", "Circular membrane inharmonic overtones"),
    ("byeonjuk", "produces", "bessel_modes", "F61", "Suppresses (0,1) and excites asymmetric (1,1)/(2,1) modes"),
    ("bessel_modes", "measured_or_modeled_by", "sldv", "F53", "Non-contact 3D laser surface velocity imaging"),
    ("joigae", "measured_or_modeled_by", "sldv", "F62", "Diagnoses misaligned tuning wedges"),
    ("helmholtz_resonator", "measured_or_modeled_by", "tmm", "F53", "Models jorongmok inertance and phase balance"),
    ("jorongmok", "measured_or_modeled_by", "tmm", "F62", "Cavity impedance Z = j*omega*rho_0*L_eff/A"),

    # Implements, strokes & biomechanics
    ("yeolchae", "made_of", "bamboo", "F04", "Thin flexible bamboo whip"),
    ("yeolchae", "made_of", "bamboo", "F19", "Flexible bamboo whip for treble head"),
    ("gungchae", "made_of", "bamboo", "F19", "Hardwood mallet on a bamboo root"),
    ("janggu", "played_with", "yeolchae", "F19", "Right-hand treble whip"),
    ("janggu", "played_with", "gungchae", "F19", "Left-hand bass mallet"),
    ("janggu", "played_with", "bare_left_hand", "F04", "Seated court Jeongak left-hand touch"),
    ("yeolchae", "strikes", "chaepyeon", "F04", "Right treble drumhead"),
    ("yeolchae", "strikes", "byeonjuk", "F45", "Crisp rim tack in court Jeongak"),
    ("gungchae", "strikes", "gungpyeon", "F05", "Left bass drumhead in folk music"),
    ("bare_left_hand", "strikes", "gungpyeon", "F04", "Restrained bass pulse in court Jeongak"),
    ("gungchae", "acts_as", "class_3_lever", "F54", "Gross wrist/forearm arc motion"),
    ("yeolchae", "acts_as", "finger_fulcrum", "F54", "Localized finger pivot for fast whips"),
    ("janggu", "produces", "deong", "F20", "Simultaneous strike"),
    ("janggu", "produces", "gung", "F20", "Left bass strike"),
    ("janggu", "produces", "tta", "F20", "Right treble strike"),
    ("janggu", "produces", "gideok", "F20", "Flam grace note"),
    ("janggu", "produces", "jjak", "F20", "Sharp rimshot"),

    # Rhythms & cultural traditions
    ("janggu", "uses_rhythm", "jangdan", "F21", "Traditional Korean named rhythmic cycles"),
    ("jangdan", "has_part", "jinyangjo", "F21", "Slowest 24-beat cycle"),
    ("jangdan", "has_part", "jungmori", "F22", "Moderate 12-beat walking cycle"),
    ("jangdan", "has_part", "jungjungmori", "F23", "Lilting 12-beat cycle"),
    ("jangdan", "has_part", "jajinmori", "F24", "Rapid 12/8 cycle"),
    ("jangdan", "has_part", "hwimori", "F25", "Fastest 4-beat climax cycle"),
    ("jangdan", "has_part", "gutgeori", "F26", "Syncopated 12-beat swing"),
    ("jangdan", "has_part", "eonmori", "F27", "Asymmetric 10-beat (3+2+3+2)"),
    ("janggu", "used_in", "jeongak", "F06", "Royal court classical music"),
    ("janggu", "used_in", "nongak_pungmul", "F06", "Rural farmers' band folk tradition"),
    ("janggu", "used_in", "shamanic_ritual", "F06", "Traditional Korean shamanic rites"),
    ("janggu", "used_in", "janggu_dance", "F06", "Traditional and stage drum dances"),
    ("janggu", "used_in", "pansori", "F39", "Vocal narrative storytelling accompaniment"),
    ("janggu", "used_in", "sanjo", "F26", "Solo instrumental genre"),
    ("janggu", "used_in", "samulnori", "F41", "1978 seated percussion quartet"),
    ("janggu", "used_in", "roka_bands", "F37", "Modern ceremonial stage concerts"),
    ("janggu", "excluded_from", "daechwita", "F36", "Dual timbres risked obscuring battlefield commands"),
    ("daechwita", "played_with", "yonggo", "F36", "Single-timbre barrel drum for metronomic orders"),
    ("jeongak", "played_with", "yeolchae", "F04", "Right-hand rim taps"),
    ("jeongak", "played_with", "bare_left_hand", "F04", "Restrained bare-palm bass"),
    ("nongak_pungmul", "played_with", "yeolchae", "F05", "Two-stick outdoor folk projection"),
    ("nongak_pungmul", "played_with", "gungchae", "F05", "Sweeping left-hand mallet arcs"),
    ("samulnori", "played_with", "gungchae", "F46", "Circular left-hand mallet sweeps"),
    ("samulnori", "played_with", "yeolchae", "F46", "Tapered bamboo whip"),
    ("pansori", "uses_rhythm", "jinyangjo", "F21", "Tragic scenes and profound sorrow"),
    ("pansori", "uses_rhythm", "jajinmori", "F39", "Dramatic battle scenes like Jeokbyeokga"),
    ("jeokbyeokga", "uses_rhythm", "jajinmori", "F39", "Naval warfare scene in Pansori"),
    ("pansori", "uses_rhythm", "chuimsae", "F28", "Spontaneous vocal cues ('Eolssigu!', 'Jota!')"),
    ("pansori", "uses_rhythm", "sigimsae", "F39", "Vocal ornaments framed by jangdan timing"),
    ("shamanic_ritual", "uses_rhythm", "gutgeori", "F26", "Swinging 12-beat ritual groove"),
    ("sanjo", "uses_rhythm", "gutgeori", "F26", "Instrumental Sanjo swing"),
    ("nongak_pungmul", "uses_rhythm", "jungjungmori", "F23", "Energetic folk dances"),
    ("seoljanggu", "leads_or_directs", "nongak_pungmul", "F38", "Directs tempo shifts and sangmo choreography"),
    ("seoljanggu", "played_with", "sangmo", "F38", "Spinning ribbon-hat choreography"),
    ("gaeinjanggunori", "created_by", "kim_byeong_seop", "F38", "Honam Udo solo seoljanggu lineage"),
    ("seoljanggu", "documented_in", "kim_byeong_seop", "F65", "Honam Udo master (1921-1987)"),
    ("microtonal_tuning", "used_in", "ajaeng", "F55", "Pitch cohesion with ajaeng sigimsae bends"),
    ("microtonal_tuning", "used_in", "piri", "F55", "Pitch cohesion with piri sigimsae bends"),

    # Origins, archaeology & historical chronology
    ("idakka", "evolved_into", "yogo", "F12", "Introduced along Silk Road during Silla period"),
    ("yogo", "evolved_into", "janggu", "F12", "Developed into the Korean hourglass janggu"),
    ("yogo", "depicted_in", "goguryeo_murals", "F33", "Anak No. 3, Deokheung-ri (c. 408 CE), Susan-ri, Palcheong-ri"),
    ("pipa", "depicted_in", "goguryeo_murals", "F33", "Central Asian lute beside waisted drums"),
    ("yogo", "depicted_in", "geumdong_daehyangno", "F34", "Baekje relief musician in Buyeo"),
    ("janggu", "depicted_in", "sangwonsa_bell", "F35", "Unified Silla seyogo relief carving"),
    ("janggu", "depicted_in", "seongdeok_bell", "F35", "771 CE Unified Silla seyogo relief"),
    ("eumseongseo", "documented_in", "sangwonsa_bell", "F35", "Unified Silla royal music heritage (651 CE bureau)"),
    ("janggu", "documented_in", "goryeosa", "F13", "Earliest official post janggu-opsa in 1076 AD"),
    ("janggu_opsa", "documented_in", "goryeosa", "F13", "1076 AD under King Munjong"),
    ("janggu", "standardized_by", "king_yejong", "F14", "1114 AD Song Dynasty court instrument import"),
    ("janggu", "documented_in", "akhak_gwebeom", "F15", "1493 codification of asymmetric hides"),
    ("akhak_gwebeom", "created_by", "seong_hyeon", "F15", "1493 Joseon Canon of Music"),
    ("janggu", "distinguished_from", "galgo", "F15", "Asymmetric hides vs. symmetrical two-stick galgo"),
    ("jeongganbo", "created_by", "king_sejong", "F29", "15th-century (1447) spatial 2D grid matrix"),
    ("janggu", "documented_in", "jeongganbo", "F29", "Dedicated janggu stroke mnemonic column"),
    ("sajanggu", "preserved_at", "national_museum_korea", "F10", "Goryeo celadon ceramic janggu"),
    ("duksu_1726", "preserved_at", "national_museum_korea", "F59", "Bisaek inlaid Goryeo celadon sajanggu"),
    ("duksu_1726", "created_by", "gangjin_kilns", "F59", "Fired at ~1,150°C"),
    ("met_changgo", "preserved_at", "met_museum", "F09", "Preserved 19th-century Korean changgo"),
    ("janggu_dance", "standardized_by", "choi_seung_hee", "F08", "1930s modern international stage choreography"),
    ("jangagwon", "evolved_into", "national_gugak_center", "F42", "Founded in Seoul in 1951"),
    ("nongak_pungmul", "evolved_into", "samulnori", "F41", "Distilled into seated quartet in 1978"),
    ("samulnori", "created_by", "kim_deok_soo", "F41", "Founded in 1978"),
    ("nongak_pungmul", "documented_in", "unesco_nongak", "F07", "2014 UNESCO Representative List inscription"),

    # Digital humanities, DSP & forensic conservation
    ("jeongganbo", "digitized_by", "kaist_umulsai", "F47", "Optical Music Recognition with EBNF and JSON"),
    ("kaist_umulsai", "created_by", "danbinaerin_han", "F47", "KAIST OMR research team"),
    ("kaist_umulsai", "measured_or_modeled_by", "jeongganbo_ebnf", "F47", "Formal grammar for Jeongganbo stroke scores"),
    ("jeongganbo_ebnf", "documented_in", "deong", "F63", "Formalizes Deong, Gung, Tta, Gideok, Jjak strokes"),
    ("tta", "measured_or_modeled_by", "melcnn_mert", "F63", "Separates broadband tta smears from gung peaks"),
    ("gung", "measured_or_modeled_by", "melcnn_mert", "F56", "Transient MelCNN & MERT-v1 stroke transcription"),
    ("janggu", "measured_or_modeled_by", "fdtd_faust", "F57", "CFL-stable 2D FDTD waveguide mesh coupled to 1D cavity"),
    ("joimjul", "measured_or_modeled_by", "fdtd_faust", "F64", "Boundary tension parameter in 2D FDTD mesh"),
    ("ijanggu", "measured_or_modeled_by", "fdtd_faust", "F57", "Piezo pickups driving Bela boards in real time"),
    ("ijanggu", "has_part", "ullimtong", "F64", "Piezo contact mics mounted inside Paulownia shell"),
    ("ijanggu", "has_part", "chaepyeon", "F48", "Piezoelectric contact sensors mounted onto natural membranes"),
    ("ullimtong", "measured_or_modeled_by", "sr_uct", "F58", "Non-destructive CT and dendrochronology ring imaging"),
    ("ottchil_lacquer", "measured_or_modeled_by", "p_xrf", "F58", "Detects antique ottchil metals and PEG consolidants"),
    ("janggu", "digitized_by", "photogrammetry_3d", "F59", "3D digital twins and 20°C / 50-55% RH conservation"),
]


def build_semantic_network(db_path: Path = DEFAULT_DB_PATH) -> Dict[str, int]:
    """Create schema tables if missing, upsert verified nodes/relations and validate zero unverified edges."""
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.executescript(schema_sql)

        # Pre-validate that every relation fact_id is Verified and cited
        verified_rows = conn.execute("SELECT id FROM facts WHERE status = 'Verified'").fetchall()
        verified_ids = {r["id"] for r in verified_rows}
        cited_rows = conn.execute("SELECT DISTINCT fact_id FROM citations").fetchall()
        cited_ids = {r["fact_id"] for r in cited_rows}
        node_ids = {n[0] for n in CONCEPT_NODES}

        for subj, pred, obj, fid, _qual in SEMANTIC_RELATIONS:
            if subj not in node_ids:
                raise ValueError(f"Unknown subject node '{subj}' in relation ({subj}, {pred}, {obj}, {fid})")
            if obj not in node_ids:
                raise ValueError(f"Unknown object node '{obj}' in relation ({subj}, {pred}, {obj}, {fid})")
            if fid not in verified_ids:
                raise ValueError(f"Unverified or missing fact_id '{fid}' in relation ({subj}, {pred}, {obj})")
            if fid not in cited_ids:
                raise ValueError(f"Uncited fact_id '{fid}' in relation ({subj}, {pred}, {obj})")

        with conn:
            conn.execute("DELETE FROM semantic_relations")
            conn.execute("DELETE FROM concept_nodes")

            conn.executemany(
                """
                INSERT INTO concept_nodes (id, label, korean_name, node_type, category, summary, aliases)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (nid, label, kr, ntype, cat, summary, json.dumps(aliases, ensure_ascii=False))
                    for nid, label, kr, ntype, cat, summary, aliases in CONCEPT_NODES
                ],
            )
            conn.executemany(
                """
                INSERT OR IGNORE INTO semantic_relations (subject_id, predicate, object_id, fact_id, qualifier)
                VALUES (?, ?, ?, ?, ?)
                """,
                SEMANTIC_RELATIONS,
            )

        # Final SQL-level integrity audit
        bad_edges = conn.execute(
            """
            SELECT r.id, r.subject_id, r.predicate, r.object_id, r.fact_id
            FROM semantic_relations r
            LEFT JOIN facts f ON r.fact_id = f.id
            LEFT JOIN (SELECT DISTINCT fact_id FROM citations) c ON r.fact_id = c.fact_id
            WHERE f.id IS NULL OR f.status != 'Verified' OR c.fact_id IS NULL
            """
        ).fetchall()
        if bad_edges:
            raise RuntimeError(f"Found {len(bad_edges)} unverified or uncited semantic edges.")

        node_count = conn.execute("SELECT COUNT(*) FROM concept_nodes").fetchone()[0]
        edge_count = conn.execute("SELECT COUNT(*) FROM semantic_relations").fetchone()[0]
        covered_facts = conn.execute("SELECT COUNT(DISTINCT fact_id) FROM semantic_relations").fetchone()[0]
        return {
            "nodes": node_count,
            "edges": edge_count,
            "covered_verified_facts": covered_facts,
            "total_verified_facts": len(verified_ids),
        }
    finally:
        conn.close()


if __name__ == "__main__":
    if sys.stdout.encoding != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    stats = build_semantic_network()
    print(
        f"[OK] Semantic network built: {stats['nodes']} nodes, {stats['edges']} verified edges "
        f"covering {stats['covered_verified_facts']}/{stats['total_verified_facts']} verified facts."
    )
