"""Inference engine evaluating production rules and generating non-repeating prose."""

from typing import Any, Dict, List, Optional
from src.knowledge.repository import KnowledgeRepository
from src.engine.explainer import Explainer
from src.memory.session import SessionMemory
from src.dialogue.variations import compose_variation, pick_variation


class InferenceEngine:
    """Forward-chaining rule engine generating varied, verified conversational responses."""

    def __init__(self, repository: KnowledgeRepository):
        self.repository = repository
        self.explainer = Explainer(repository)

    def evaluate(
        self,
        intent: Optional[str],
        entities: Dict[str, str],
        confidence: float,
        session: SessionMemory,
    ) -> Dict[str, Any]:
        """Evaluate rules and generate non-repeating responses backed by verified facts."""
        if intent == "ask_source_explanation":
            explanation = self.explainer.explain_facts(session.last_fact_ids, session=session)
            return {
                "status": "answered",
                "text": explanation,
                "fact_ids": session.last_fact_ids,
                "confidence": confidence,
            }

        selected_facts: List[Dict[str, Any]] = []
        reply_text = ""

        if intent == "conversational_acknowledgment":
            selected_facts = [f for f in self.repository.get_verified_facts() if f["id"] in session.last_fact_ids]
            reply_text = compose_variation(
                "rule::acknowledgment",
                (
                    "Glad that caught your interest—the janggu sits at the center of Korean court and folk traditions.",
                    "There is a lot to appreciate in how one hourglass drum anchors so many Korean genres.",
                    "Happy to keep digging into it—the janggu weaves through both ceremonial halls and rural festivals.",
                ),
                (
                    "We could examine the five core strokes, the acoustic waist choke or the jangdan time cycles next. Which direction?",
                    "Where would you like to steer next: stroke technique, chamber acoustics or traditional rhythms?",
                    "Feel free to pick a next thread—its carved body, hand techniques or rhythmic patterns.",
                    "What part of the instrument would you like to unpack from here?",
                ),
                session=session,
                separator=" ",
            )
            session.set_pending_offer({"type": "general_followup"})

        elif intent == "ask_difficulty":
            selected_facts = [f for f in self.repository.get_verified_facts() if f["id"] in {"F04", "F05", "F19", "F22"}]
            reply_text = compose_variation(
                "rule::ask_difficulty",
                (
                    (
                        "Learning the janggu brings a real coordination puzzle because both hands do opposite mechanical jobs: "
                        "the right hand whips a springy bamboo yeolchae for sharp treble snaps while the left drives bass resonance with a weighted gungchae mallet or bare palm (often while marching and dancing in folk settings)."
                    ),
                    (
                        "The main hurdle for newcomers is independent hand motion. Your right wrist flicks the slender yeolchae stick on treble skin while your left hand controls deeper bass hits with the gungchae mallet or open palm—plus folk musicians play standing and moving."
                    ),
                    (
                        "It takes focused practice mainly because left and right techniques follow separate physics: delicate bamboo-whip strokes on the treble head (yeolchae) paired against weighted gungchae strokes or bare-palm bass hits on the left."
                    ),
                ),
                (
                    "Most players start with a calm Jungmori pattern before stepping up to rapid cycles like Hwimori—want to hear about beginner rhythms?",
                    "Teachers usually ease learners in via steady Jungmori cycles before chasing fast climax patterns like Hwimori. Should we look at beginner rhythms next?",
                    "Starting on unhurried Jungmori helps lock coordination before fast patterns such as Hwimori; would you like a walkthrough of entry-level rhythms?",
                ),
                session=session,
                separator=" ",
            )
            session.set_pending_offer({"type": "beginner_rhythms"})

        elif intent == "ask_favorite":
            selected_facts = [f for f in self.repository.get_verified_facts() if f["id"] in {"F21", "F25", "F26"}]
            reply_text = compose_variation(
                "rule::ask_favorite",
                (
                    "Among traditional cycles, 12-beat Gutgeori stands out for its infectious syncopated dance swing, whereas 4-beat Hwimori chases pure momentum by accelerating straight into an explosive climax.",
                    "Ask percussionists their standout pick and many point to Gutgeori—a bouncy 12-beat folk groove—or Hwimori, a rapid 4-beat pattern that pushes tempo relentlessly to a peak.",
                    "Two contrasting cycles show off the drum best: buoyant 12-beat Gutgeori in folk dances and shamanic music, and blistering 4-beat Hwimori racing toward a festival climax.",
                ),
                (
                    "Want to contrast that energy with expansive 24-beat patterns like Jinyangjo, or explore more festival grooves?",
                    "Curious to compare slow dignified cycles like Jinyangjo against fast festival patterns?",
                    "Should we inspect solemn slow cycles like Jinyangjo or stick with high-tempo festival rhythms?",
                ),
                session=session,
                separator=" ",
            )
            session.set_pending_offer({"type": "slow_or_fast_rhythms"})

        elif intent == "ask_modern_popularity":
            selected_facts = [f for f in self.repository.get_verified_facts() if f["id"] in {"F06", "F07"}]
            reply_text = compose_variation(
                "rule::ask_modern_popularity",
                (
                    (
                        "Very much so—the drum remains active from conservatories to concert stages worldwide. "
                        "In 1978, master Kim Duk-soo launched Samul nori, propelling Korean percussion to international halls, while today the janggu is taught in Korean schools, performed in National Gugak ensembles and featured in Nongak's 2014 UNESCO inscription."
                    ),
                    (
                        "Far from fading into museum displays, the janggu saw a huge modern wave after Samulnori formed under Kim Duk-soo in 1978. Schools across Korea teach it, National Gugak groups perform on it and UNESCO recognized community Nongak drumming in 2014."
                    ),
                    (
                        "Modern audiences know the janggu largely thanks to Samulnori's 1978 concert debut under Kim Duk-soo, alongside school music curricula, Gugak orchestras and UNESCO's 2014 Intangible Heritage listing for Nongak."
                    ),
                ),
                (
                    "Have you seen a live Korean percussion concert yet, or would you like to explore how it is built?",
                    "Curious how the modern stage sound compares with older court traditions?",
                    "Would you care to hear more about Samulnori's setup or the instrument's construction?",
                ),
                session=session,
                separator=" ",
            )

        elif "jangdan" in entities or (intent == "ask_cultural_significance" and any(k in entities for k in ["chuimsae", "jangdan"])):
            if "chuimsae" in entities:
                selected_facts = [f for f in self.repository.get_verified_facts("cultural_use") if f["id"] == "F28"]
                reply_text = compose_variation(
                    "rule::chuimsae",
                    (
                        "Vocal calls shouted during Korean performances are called chuimsae—spontaneous cheers like 'Eolssigu!' (Right on!) and 'Jota!' (Wonderful!) exchanged between drummers, vocalists and listeners to lift energy and mark tempo shifts.",
                        "Chuimsae are interactive cries of encouragement such as 'Eolssigu!' and 'Jota!' thrown into live performance. Rather than interrupting, they bond audience with musicians and steer momentum across rhythmic transitions.",
                        "When listeners or accompanists call out 'Eolssigu!' (Right on!) and 'Jota!' (Wonderful!), those vocal cues are chuimsae—building mutual excitement and guiding tempo flow between drummer and performer.",
                    ),
                    (
                        "Want to pair those shouts with the jangdan rhythmic cycles underneath them?",
                        "Should we explore the main jangdan patterns that invite chuimsae cheers?",
                        "Curious which rhythmic cycles most often spark those vocal calls?",
                    ),
                    session=session,
                    separator=" ",
                )
            else:
                selected_facts = [f for f in self.repository.get_verified_facts("cultural_use") if f["id"] in {"F21", "F22", "F24", "F25", "F26", "F27"}]
                reply_text = compose_variation(
                    "rule::jangdan_list",
                    (
                        (
                            "Korean jangdan ('long-short' cycles) define each piece's pace and emotion:\n"
                            "- Jinyangjo: Slowest 24-beat pattern carrying deep sorrow and aristocratic dignity.\n"
                            "- Jungmori: Calm 12-beat walking tempo suited to lyrical storytelling.\n"
                            "- Jungjungmori: Bouncing 12-beat groove with a bright, lilting feel.\n"
                            "- Jajinmori: Urgent, brisk 12-beat drive for action and battle scenes.\n"
                            "- Hwimori: Blistering 4-beat pattern racing into a climax.\n"
                            "- Gutgeori: Swinging 12-beat rhythm central to folk dance and shamanic ritual.\n"
                            "- Eonmori: Asymmetric 10-beat cycle (3+2+3+2) for heroic or uncanny passages."
                        ),
                        (
                            "Seven foundational jangdan cycles span the tempo spectrum:\n"
                            "- Slow to walking: Jinyangjo (24-beat tragic/dignified breadth), Jungmori (steady 12-beat walking pulse) and Jungjungmori (cheerful 12-beat bounce).\n"
                            "- Swinging & asymmetric: Gutgeori (syncopated 12-beat folk dance swing) and Eonmori (3+2+3+2 10-beat heroic tilt).\n"
                            "- Fast & climactic: Jajinmori (brisk 12-beat action cycle) and Hwimori (fastest 4-beat climax)."
                        ),
                        (
                            "Every piece rides on a named jangdan cycle tailored to its mood—from expansive 24-beat Jinyangjo for grief, calm 12-beat Jungmori walking meter, buoyant Jungjungmori and syncopated 12-beat Gutgeori folk swing, all the way to asymmetric 10-beat Eonmori (3+2+3+2), fast 12-beat Jajinmori and explosive 4-beat Hwimori."
                        ),
                    ),
                    (
                        "Which of those rhythmic moods would you like to dig into first?",
                        "Any particular cycle among the seven you want to practice or inspect closer?",
                        "Want to zoom in on one of these tempos—from Jinyangjo's calm breadth to Hwimori's speed?",
                    ),
                    session=session,
                    separator="\n\n",
                )

        elif intent == "ask_etymology":
            selected_facts = self.repository.get_verified_facts("etymology")
            reply_text = compose_variation(
                "rule::ask_etymology",
                (
                    (
                        "Historically, its names capture both play technique and hourglass geometry:\n"
                        "- Janggu / Janggo (장고 / 杖鼓): Combines Hanja characters for 'stick' (杖) and 'drum' (鼓), pointing to mallet/whip excitation.\n"
                        "- Seyogo (細腰鼓): An earlier label literally meaning 'slim waist drum', highlighting the pinched midsection."
                    ),
                    (
                        "Two classical names tell the story of the instrument: janggu (written janggo 장고 / 杖鼓 in Sino-Korean characters for 'stick' 杖 and 'drum' 鼓) highlights how sticks excite the skins, while the older term seyogo (細腰鼓) means 'slim waist drum' after its hourglass silhouette."
                    ),
                    (
                        "The drum's nomenclature breaks into two descriptors:\n"
                        "1. Seyogo (細腰鼓, 'slim waist drum'), used in early records for its slender center tube.\n"
                        "2. Janggu / Janggo (장고 / 杖鼓), pairing 'stick' (杖) + 'drum' (鼓) to emphasize stick-struck percussion."
                    ),
                ),
                (
                    "Want to trace its Silk Road migration or jump into how court and folk ensembles used it?",
                    "Curious about how those names show up in Silla temple bells and early royal chronicles?",
                    "Should we check its archaeological roots or contrast court music with village festivals next?",
                ),
                session=session,
                separator="\n\n",
            )
            session.set_pending_offer({"type": "court_or_folk"})

        elif intent == "ask_evolution":
            evo_facts = self.repository.get_verified_facts("evolution")
            if "conservation" in entities:
                all_chron = self.repository.get_verified_facts("chronology")
                selected_facts = [f for f in all_chron if f["id"] in {"F58", "F10"}] + [f for f in evo_facts if f["id"] == "F59"]
                reply_text = compose_variation(
                    "rule::evo_conservation",
                    (
                        (
                            "Museum conservation protects fragile drums through non-destructive forensics and strict climate equilibrium:\n"
                            "- Imaging & dendrochronology: Synchrotron X-ray Microtomography (SR-μCT) and CT scans inspect hidden dowels, animal-glue repairs and earlywood/latewood ring widths for Joseon-era dating without dismantling the shell.\n"
                            "- Chemical forensics: Portable X-ray Fluorescence (p-XRF) checks heavy metals in antique ottchil lacquer and identifies damaging prior PEG consolidants.\n"
                            "- Climate & 3D archiving: Institutions maintain 20°C and 50 to 55% relative humidity to avert jorongmok micro-fracturing, archive shapes via 3D photogrammetry and catalog treasures like National Museum Goryeo sajanggu Duksu 1726 (bisaek celadon fired around 1,150°C at Gangjin kilns)."
                        ),
                        (
                            "Non-destructive science keeps historic janggu intact: SR-μCT and cylindrical CT reveal concealed internal joinery, wood dowels and dendrochronology ring histories, while p-XRF spots ottchil lacquer pigments and past Polyethylene Glycol (PEG) treatments. To stop hygroscopic swelling or jorongmok micro-fracturing, museums hold 20°C and 50–55% relative humidity and capture 3D photogrammetry digital twins—including National Museum Goryeo celadon sajanggu Duksu 1726 from the ~1,150°C Gangjin kilns."
                        ),
                        (
                            "Forensic conservation combines Synchrotron X-ray Microtomography (SR-μCT) and ring-width dendrochronology with p-XRF elemental analysis (detecting ottchil metals and PEG consolidants), 3D photogrammetric replicas and climate stabilization near 20°C / 50–55% relative humidity—safeguarding wooden chambers as well as Goryeo bisaek celadon sajanggu Duksu 1726 fired near 1,150°C in Gangjin."
                        ),
                    ),
                    (
                        "Want to examine the micro-anatomy of Paulownia coreana wood next?",
                        "Curious why Goryeo celadon sajanggu yielded to carved wood for mobile dances?",
                        "Should we explore nakdong scorching or traditional animal-glue joinery next?",
                    ),
                    session=session,
                    separator="\n\n",
                )
            elif "ebnf_grammar" in entities:
                all_chron = self.repository.get_verified_facts("chronology")
                selected_facts = [f for f in all_chron if f["id"] in {"F63", "F29"}] + [f for f in evo_facts if f["id"] in {"F47", "F56"}]
                reply_text = compose_variation(
                    "rule::evo_ebnf",
                    (
                        (
                            "Jeongganbo computational grammars define a plaintext EBNF structure for synthetic playback and optical engraving (Umulsai):\n"
                            "- Score ::= Gak+, Gak ::= Jeonggan+, Jeonggan ::= (Stroke | SubJeonggan | Rest)\n"
                            "- SubJeonggan ::= Stroke Stroke | Stroke Rest, Stroke ::= 'Deong' | 'Gung' | 'Tta' | 'Gideok' | 'Jjak', Rest ::= '△' | '-'\n"
                            "By adjusting temporal values on SubJeonggan cells, algorithms interpolate expressive micro-timing swing and rubato—complementing MelCNN classifiers tracking sharp tta onset smears and high-Q gung resonance peaks."
                        ),
                        (
                            "Formalizing King Sejong's 1447 grid, Jeongganbo EBNF defines Score ::= Gak+ -> Gak ::= Jeonggan+ -> SubJeonggan ::= Stroke Stroke | Stroke Rest across Stroke tokens ('Deong', 'Gung', 'Tta', 'Gideok', 'Jjak') and Rest symbols ('△' | '-'). SubJeonggan duration scaling models human swing and rubato, pairing cleanly with MelCNN onset-smear vs. high-Q gung stroke detection."
                        ),
                        (
                            "Plaintext EBNF production rules (Score ::= Gak+, Gak ::= Jeonggan+, Jeonggan ::= Stroke | SubJeonggan | Rest with SubJeonggan allowing swing/rubato micro-timing) power algorithmic score conversion in KAIST's Umulsai, alongside MelCNN spectrogram recognition distinguishing broadband tta onset smears from high-Q gung peaks."
                        ),
                    ),
                    (
                        "Want to look at FDTD waveguide meshes or how Jeongganbo gak columns are tuned microtonally?",
                        "Curious how KAIST's Umulsai pairs EBNF grammars with JSON layout rules?",
                        "Should we examine 2D FDTD membrane synthesis on Bela microcontrollers next?",
                    ),
                    session=session,
                    separator="\n\n",
                )
            elif "ml_dsp" in entities:
                selected_facts = [f for f in evo_facts if f["id"] in {"F56", "F57", "F64", "F47", "F48"}]
                reply_text = compose_variation(
                    "rule::evo_ml_dsp",
                    (
                        (
                            "Computational organology models and analyzes the janggu across three digital pipelines:\n"
                            "- Stroke classification ML: Transient Mel-spectrogram CNNs (MelCNN), hybrid CNN/RNNs and fine-tuned MERT-v1 (95M parameters) distinguish broadband tta onset smears from high-Q gung peaks over piezo/accelerometer streams via Macro F1 and Event F1/IoU (distinct from F0CNN/RMVPE for vocal sigimsae).\n"
                            "- FDTD / Digital Waveguide Mesh (DWM): Coded in FAUST under CFL stability conditions coupled to a 1D shell guide, rectilinear membrane updates follow p(i,j,n+1) = 0.5*(p(i-1,j,n)+p(i+1,j,n)+p(i,j-1,n)+p(i,j+1,n)) - p(i,j,n-1) with hoop compliance and joimjul boundary tension.\n"
                            "- Hardware iJanggu & Umulsai: Embedded piezo contact mics mounted inside the Paulownia shell or beneath the bukpyeon feed Bela boards running Pure Data or FAUST without MIDI latency."
                        ),
                        (
                            "Modern audio computing pairs transient ML transcription with physically modeled DSP:\n"
                            "Because percussion strikes yield sharp tta onset smears and low-Q/high-Q gung peaks rather than vocal F0 curves tracked by F0CNN/RMVPE, models apply MelCNN, CNN/RNN and MERT-v1 (95M) with Macro F1 and Event F1/IoU metrics. Meanwhile, FAUST physical synthesis runs CFL-stable 2D FDTD Digital Waveguide Meshes [p(i,j,n+1) = 0.5*(neighbors) - p(i,j,n-1)] coupled to a 1D cavity, powered by iJanggu piezo pickups inside the shell or beneath bukpyeon directly into Bela (Pure Data / FAUST) without MIDI latency."
                        ),
                        (
                            "From MERT-v1 (95M) and MelCNN spectrogram stroke transcription to real-time FAUST FDTD Digital Waveguide Meshes—updating p(i,j,n+1) = 0.5*(p(i-1,j,n)+p(i+1,j,n)+p(i,j-1,n)+p(i,j+1,n)) - p(i,j,n-1) under CFL limits with hoop and joimjul boundary compliance—hardware iJanggu units route piezo pickups placed inside the Paulownia shell or beneath bukpyeon into Bela boards running Pure Data or FAUST."
                        ),
                    ),
                    (
                        "Want to inspect the Jeongganbo EBNF grammar or museum forensic imaging (SR-μCT / p-XRF)?",
                        "Curious how 3D Vibrometry (SLDV) and TMM fluid models validate the cavity waves?",
                        "Should we explore MelCNN spectrogram vs. vocal F0CNN distinctions or museum conservation next?",
                    ),
                    session=session,
                    separator="\n\n",
                )
            elif "sajanggu" in entities:
                all_chron = self.repository.get_verified_facts("chronology")
                selected_facts = [f for f in all_chron if f["id"] == "F10"] + [f for f in evo_facts if f["id"] == "F49"]
                reply_text = compose_variation(
                    "rule::evo_sajanggu",
                    (
                        (
                            "In the Goryeo era (918-1392), potters crafted celadon ceramic bodies (sajanggu) decorated with inlaid sanggam motifs whose rigid walls gave bright reflective resonance—preserved today at the National Museum of Korea.\n\n"
                            "Even so, ceramic drums proved heavy and fragile during rigorous ambulatory dances, keeping sajanggu in stationary chamber settings while carved wood became standard everywhere else."
                        ),
                        (
                            "Goryeo celadon sajanggu bodies paired inlaid sanggam aesthetics with clear acoustic reflection inside rigid porcelain walls (surviving in the National Museum of Korea). Because porcelain was heavy and prone to breaking on the move, mobile folk musicians standardized wooden bodies and left celadon to aristocratic chamber music."
                        ),
                        (
                            "Although 13th-century Goryeo celadon sajanggu drums offered vivid visual craftsmanship and crisp ceramic acoustics, extreme weight and fragility ruled them out for outdoor processional dancing—leaving carved timber as the enduring standard."
                        ),
                    ),
                    (
                        "Want to look at how artisans cure and scorch those wooden shells instead?",
                        "Curious what kind of timber replaced ceramic bodies permanently?",
                        "Should we examine the acoustic choke and Paulownia construction next?",
                    ),
                    session=session,
                    separator="\n\n",
                )
            elif "ijanggu" in entities:
                selected_facts = [f for f in evo_facts if f["id"] in {"F47", "F48"}]
                reply_text = compose_variation(
                    "rule::evo_ijanggu",
                    (
                        (
                            "Two landmark research efforts connect traditional janggu heritage to modern computing:\n"
                            "- Umulsai (KAIST, led by Danbinaerin Han): Optical music recognition (OMR) software applying EBNF grammars and JSON rules to digitize traditional Jeongganbo scores.\n"
                            "- iJanggu: Rather than using flat capacitive electronic drum pads that lose stick rebound and feel, iJanggu mounts piezoelectric contact sensors onto natural hides to drive physical modeling synthesis."
                        ),
                        (
                            "Digital organology touches both score preservation and electronic performance:\n"
                            "On the notation side, Danbinaerin Han's Umulsai OMR toolkit at KAIST translates Jeongganbo drum grids via EBNF grammars and JSON rules. On the hardware side, the iJanggu attaches piezo contact sensors to genuine animal skins—capturing natural tactile play that flat capacitive electronic drum pads miss, driving physical modeling synthesis."
                        ),
                        (
                            "Modern engineers extended the janggu computationally without replacing its touch: the iJanggu instruments natural skins with piezoelectric pickups for physical modeling synthesis (outperforming stiff capacitive electronic pads), while KAIST's Umulsai OMR system led by Danbinaerin Han parses Jeongganbo scores with EBNF grammars and JSON rules."
                        ),
                    ),
                    (
                        "Want to compare synthetic Mylar/FRP practice drums next, or look at circular membrane physics?",
                        "Curious about FRP/Mylar school instruments or Bessel-mode acoustics next?",
                        "Should we inspect modern synthetic drumheads or the mechanics of wooden drums?",
                    ),
                    session=session,
                    separator="\n\n",
                )
            else:
                selected_facts = evo_facts
                reply_text = compose_variation(
                    "rule::evo_default",
                    (
                        (
                            "From Three Kingdoms waist drums and fragile 13th-century Goryeo celadon sajanggu vessels replaced by carved wood, the instrument kept evolving across four modern shifts:\n"
                            "- 1978 Samulnori: Kim Deok-soo adapted outdoor pungmul into indoor quartets, later joined by female drummers transforming kinetic stage movement.\n"
                            "- 21st-century materials: Fiberglass-reinforced plastic (FRP) shells and synthetic Mylar heads withstand school humidity, though purists miss natural wood and hide overtones.\n"
                            "- Computational musicology: KAIST's Umulsai OMR software digitizes Jeongganbo notation while the piezo-equipped iJanggu links acoustic skins to physical synthesis."
                        ),
                        (
                            "Across centuries the janggu moved from Silla waist drums and heavy Goryeo ceramic sajanggu chamber pieces (eventually giving way to lighter wood) into contemporary stages and labs:\n"
                            "Kim Deok-soo's 1978 Samulnori brought village rhythms indoors (with women later reshaping its dynamic stage gestures); FRP fiberglass shells and Mylar heads serve durable school use; and KAIST's Umulsai OMR software alongside the piezoelectric iJanggu bring the drum into digital synthesis."
                        ),
                        (
                            "Modernization reshaped the janggu on stage, in workshops and inside software labs—spanning Samulnori's 1978 concert transformation under Kim Deok-soo (and evolving kinetic styles by female drummers), humidity-proof 21st-century FRP/Mylar models versus traditional wood, and digital projects like Umulsai OMR plus the sensor-equipped iJanggu (after ceramic sajanggu gave way to wooden bodies)."
                        ),
                    ),
                    (
                        "Which chapter of that evolution would you like to inspect closely?",
                        "Curious to drill down into FRP/Mylar synthetics, Samulnori history or digital iJanggu tech?",
                        "Where should we zoom in—synthetic materials, Samulnori choreography or digital preservation?",
                    ),
                    session=session,
                    separator="\n\n",
                )

        elif intent == "ask_military_role":
            cultural_facts = self.repository.get_verified_facts("cultural_use")
            selected_facts = [f for f in cultural_facts if f["id"] in {"F36", "F37", "F39", "F24"}]
            reply_text = compose_variation(
                "rule::ask_military",
                (
                    (
                        "Traditional military signaling intentionally excluded the janggu from battlefield Daechwita processions.\n\n"
                        "Instead, royal military bands marched behind the loud single-timbre yonggo barrel drum for clear metronomic commands, avoiding the janggu because its contrasting high and low head pitches risked obscuring urgent battlefield orders.\n\n"
                        "In later eras, though, modern Republic of Korea Army (ROKA) bands sometimes feature it in ceremonial stage concerts, and Pansori vocal storytelling depicts fierce battles through the rapid 12/8 Jajinmori cycle—famously the naval battle in Jeokbyeokga."
                    ),
                    (
                        "On active pre-modern battlefields, Korean Daechwita signaling ensembles excluded the janggu and used the booming yonggo barrel drum instead—since the janggu's dual high and low timbres could blur clear rhythmic commands.\n\n"
                        "Two exceptions connect it to military culture today: contemporary ROKA army bands bring it out for ceremonial stage concerts, while Pansori narrators portray dramatic battles (such as Jeokbyeokga) over the fast 12/8 Jajinmori beat."
                    ),
                    (
                        "Korean military marches (Daechwita) skipped the janggu in favor of the resonant yonggo barrel drum so single-toned orders carried clearly without dual high-and-low timbre interference obscuring commands.\n\n"
                        "That said, modern South Korean ROKA military bands do feature the janggu on ceremonial concert stages, and Pansori uses its brisk 12/8 Jajinmori groove to dramatize wartime clashes like Jeokbyeokga."
                    ),
                ),
                (
                    "Want to look closer at Pansori's Jajinmori battle rhythm or civilian processional roles?",
                    "Curious how its royal court duties contrasted with outdoor village processions?",
                    "Should we check out Jajinmori storytelling or explore court versus folk usage next?",
                ),
                session=session,
                separator="\n\n",
            )
            session.set_pending_offer({"type": "court_or_folk"})

        elif intent == "ask_origin":
            origin_facts = self.repository.get_verified_facts("origin")
            chronology_facts = self.repository.get_verified_facts("chronology")
            selected_facts = origin_facts + [f for f in chronology_facts if f["id"] in {"F13", "F14"}]
            if "archaeology" in entities:
                selected_facts = [f for f in origin_facts if f["id"] in {"F33", "F34", "F35"}]
                reply_text = compose_variation(
                    "rule::origin_archaeology",
                    (
                        (
                            "Early archaeological finds trace hourglass drums across all Three Kingdoms and Unified Silla:\n"
                            "- Goguryeo: Murals in Anak No. 3, Deokheung-ri (c. 408 CE), Susan-ri and Palcheong-ri show waist drums alongside five-stringed pipas.\n"
                            "- Baekje: Buyeo's Great Gilt-Bronze Incense Burner (Geumdong Daehyangno) casts a musician playing a waisted drum in relief.\n"
                            "- Unified Silla: The Samguk Sagi documents the 651 CE Eumseongseo music office, while the Sangwonsa and King Seongdeok (771 CE) bronze bells bear seyogo reliefs."
                        ),
                        (
                            "Tomb art, metalwork and temple bells preserve concrete visual proof of early Korean waist drums:\n"
                            "Fifth-century Goguryeo tombs—Anak No. 3, Deokheung-ri (c. 408 CE), Susan-ri and Palcheong-ri—pair waist-drum players with imported pipas; Baekje artisans sculpted one atop the Geumdong Daehyangno incense burner in Buyeo; and Unified Silla records note the 651 CE Eumseongseo office alongside seyogo reliefs on the Sangwonsa and 771 CE King Seongdeok bells."
                        ),
                        (
                            "Across ancient Korea, waist drums appear in stone paint, bronze casting and state annals:\n"
                            "- Goguryeo murals (c. 408 CE Deokheung-ri, Anak No. 3, Susan-ri, Palcheong-ri) depict cross-cultural court musicians with pipas and waist drums.\n"
                            "- Baekje's Geumdong Daehyangno bronze incense burner from Buyeo includes a relief hourglass drummer.\n"
                            "- Silla established Eumseongseo in 651 CE (Samguk Sagi) and etched seyogo celestial players on Sangwonsa and King Seongdeok bells (771 CE)."
                        ),
                    ),
                    (
                        "Want to follow how Goryeo and Joseon chronicles formalized the drum afterward?",
                        "Curious how it moved from Silla artifacts into Goryeo court texts and Song-era standardization?",
                        "Should we trace its path from Silla bronze reliefs to Goryeo standardization next?",
                    ),
                    session=session,
                    separator="\n\n",
                )
            else:
                reply_text = compose_variation(
                    "rule::ask_origin",
                    (
                        (
                            "Trace the janggu to its roots and you follow Silk Road cultural exchange back to the ancient Indian idakka, which migrated eastward and entered Korea during Silla times as the smaller yogo waist drum—echoed across 5th-century Goguryeo tomb paintings (Deokheung-ri, c. 408 CE), Baekje's gilded incense burner and Silla bronze temple bells.\n\n"
                            "Written records crystalize under Goryeo: the Goryeosa logs the official instructor post janggu-opsa in 1076 AD, and King Yejong's 1114 import of Song Dynasty court instruments set the larger modern hourglass shape."
                        ),
                        (
                            "Archaeology and Silk Road history trace the janggu back to India's ancient idakka hourglass drum, adapted into Korea's smaller yogo before appearing in Goguryeo murals (like Deokheung-ri, c. 408 CE), Baekje bronze relief work and Silla bells.\n\n"
                            "During the Goryeo dynasty, the Goryeosa records the court post janggu-opsa by 1076 AD, and King Yejong imported Song Chinese instruments in 1114—locking in the familiar full hourglass proportions."
                        ),
                        (
                            "Its lineage stretches from the Indian idakka eastward along Silk Road corridors into Korea's Silla-era yogo waist drum, documented visually on Goguryeo murals (c. 408 CE Deokheung-ri), Baekje's bronze incense burner and Silla bells.\n\n"
                            "Formal standardization followed in Goryeo chronicles: the Goryeosa notes a janggu-opsa court instructor in 1076 AD prior to King Yejong's 1114 Song Dynasty court instrument import."
                        ),
                    ),
                    (
                        "Would you like to look at how the drum shaped royal court music versus rural village festivals?",
                        "From there, want to see how it worked in court ceremonies versus countryside village celebrations?",
                        "Curious whether you want to explore its royal court tradition or its village folk festival life next?",
                    ),
                    session=session,
                    separator="\n\n",
                )
                session.set_pending_offer({"type": "court_or_folk"})

        elif intent == "ask_chronology":
            all_chronology = self.repository.get_verified_facts("chronology")
            if "sajanggu" in entities:
                evo_facts = self.repository.get_verified_facts("evolution")
                selected_facts = [f for f in all_chronology if f["id"] == "F10"] + [f for f in evo_facts if f["id"] == "F49"]
                reply_text = compose_variation(
                    "rule::chron_sajanggu",
                    (
                        "Preserved today in the National Museum of Korea, 13th-century Goryeo celadon sajanggu drums showcase inlaid sanggam craftsmanship and reflective ceramic walls suited to quiet aristocratic chamber music—yet their fragility and heavy weight meant carved wood won out for ambulatory folk performance.",
                        "During the Goryeo dynasty, potters fired celadon ceramic janggu bodies (sajanggu) inlaid with sanggam crane and flower patterns, now housed in the National Museum of Korea. Though acoustically bright in court chambers, ceramic bodies proved too fragile and heavy compared to durable wood.",
                        "A rare Goryeo celadon sajanggu in the National Museum of Korea highlights how luxury ceramic drums briefly thrived for chamber acoustics before their weight and fragility yielded permanently to carved Paulownia wood.",
                    ),
                    (
                        "Want to look at why Paulownia wood replaced ceramic shells in detail?",
                        "Curious about the Akhak Gwebeom treatise that later codified wooden drum proportions?",
                        "Should we explore other Joseon and Goryeo historical landmarks next?",
                    ),
                    session=session,
                    separator=" ",
                )
            elif "akhak_gwebeom" in entities:
                selected_facts = [f for f in all_chronology if f["id"] == "F15"]
                reply_text = compose_variation(
                    "rule::chron_akhak",
                    (
                        "Compiled in 1493 by court scholar Seong Hyeon, the Akhak Gwebeom (Canon of Music) standardized the janggu's asymmetric heads and tuning setup—explicitly separating it from the galgo, a related court hourglass drum with symmetrical skins played with two thin sticks.",
                        "Seong Hyeon's 1493 musicological treatise Akhak Gwebeom formally codified the janggu's asymmetric construction metrics and distinguished it structurally from the symmetrical-headed, two-sticked galgo.",
                        "Published under Joseon patronage in 1493 by Seong Hyeon, the Akhak Gwebeom established exact structural rules for the asymmetric janggu while contrasting it with the symmetrical galgo.",
                    ),
                    (
                        "Want to look closer at Joseon institutions like the Jangagwon or King Sejong's Jeongganbo notation?",
                        "Should we trace how royal court institutions preserved this lineage into the modern era?",
                        "Curious what other Goryeo or Joseon manuscripts mention the janggu?",
                    ),
                    session=session,
                    separator=" ",
                )
            elif "goryeosa" in entities:
                selected_facts = [f for f in all_chronology if f["id"] == "F13"]
                reply_text = compose_variation(
                    "rule::chron_goryeosa",
                    (
                        "The official History of Goryeo (Goryeosa) supplies Korea's earliest named state post for the instrument: janggu-opsa (court janggu instructor), recorded in 1076 AD under King Munjong.",
                        "Dating to 1076 AD during King Munjong's reign, the Goryeosa documents the court title janggu-opsa—confirming formal state instruction on the drum over nine centuries ago.",
                        "In 1076 AD (King Munjong's era), the Goryeosa chronicles list the title janggu-opsa, marking the earliest surviving official written post tied to janggu teaching.",
                    ),
                    (
                        "Want to rewind earlier to see how it entered Silla Korea along the Silk Road?",
                        "Curious about the earlier Silla waist drum ancestors before Goryeo?",
                        "Should we trace its Silla and Three Kingdoms predecessors next?",
                    ),
                    session=session,
                    separator=" ",
                )
                session.set_pending_offer({"type": "silla_evolution"})
            else:
                selected_facts = all_chronology
                reply_text = compose_variation(
                    "rule::chron_default",
                    (
                        (
                            "Major milestones mark the janggu's documented timeline in Korea:\n"
                            "- 1076 AD: Goryeosa records the instructor post janggu-opsa.\n"
                            "- 1114 AD: King Yejong imports Song Dynasty instruments, codifying hourglass proportions.\n"
                            "- 1200s (Goryeo): Celadon sajanggu drums crafted, now at the National Museum of Korea.\n"
                            "- 1447 / 15th C.: King Sejong creates Jeongganbo 2D grid notation including a janggu line.\n"
                            "- 1493 AD: Seong Hyeon's Akhak Gwebeom codifies asymmetric hides vs. the symmetrical galgo.\n"
                            "- 1800s: Preserved 19th-century Joseon drum now housed at The Metropolitan Museum of Art.\n"
                            "- 1930s: Choi Seung-hee stages international janggu dance choreography.\n"
                            "- 1951 AD: National Gugak Center founded in Seoul, extending the royal Jangagwon lineage.\n"
                            "- 2014 AD: UNESCO inscribes Nongak community band drumming as Intangible Heritage."
                        ),
                        (
                            "Key turning points anchor nearly a millennium of records:\n"
                            "From the Goryeosa's 1076 AD janggu-opsa title, King Yejong's 1114 Song import and 13th-century National Museum celadon sajanggu, through King Sejong's 15th-century (1447) Jeongganbo grid notation and Seong Hyeon's 1493 Akhak Gwebeom (separating it from the galgo), down to a 19th-century (1800s) Joseon drum at The Metropolitan Museum of Art, Choi Seung-hee's 1930s stage dance, the 1951 National Gugak Center (continuing royal Jangagwon heritage) and UNESCO's 2014 Nongak recognition."
                        ),
                        (
                            "Historians track the janggu across nine landmark chapters:\n"
                            "Goryeo state records (1076 janggu-opsa in Goryeosa; 1114 Song instrument imports; 1200s celadon sajanggu at the National Museum of Korea), Joseon codification (King Sejong's 1447 Jeongganbo notation; Seong Hyeon's 1493 Akhak Gwebeom vs. galgo; an 1800s court drum at The Metropolitan Museum of Art), and modern heritage (1930s Choi Seung-hee choreography; 1951 National Gugak Center / Jangagwon continuity; 2014 UNESCO Nongak listing)."
                        ),
                    ),
                    (
                        "Which era or historical manuscript would you like to unpack in detail?",
                        "Any single date or artifact on that timeline you want to zoom in on?",
                        "Curious to explore one of those periods closer—Goryeo ceramics, Joseon notation or modern heritage?",
                    ),
                    session=session,
                    separator="\n\n",
                )

        elif intent == "ask_playing_technique":
            all_techniques = self.repository.get_verified_facts("playing_technique")
            if "bokpan" in entities:
                selected_facts = [f for f in all_techniques if f["id"] in {"F45", "F46"}]
                reply_text = compose_variation(
                    "rule::tech_bokpan",
                    (
                        (
                            "Two target zones on each drumhead deliver dramatically different acoustics:\n"
                            "- Bokpan (center): Excitement across the center projects deep fundamental resonance ideal for bass punch and folk power.\n"
                            "- Byeonjuk (outer rim zone): Suppresses fundamental low overtones to isolate a crisp, high-frequency 'tack' snap, preferred by the right-hand yeolchae in court Jeongak."
                        ),
                        (
                            "Striking the center (bokpan) vs. the outer rim (byeonjuk) shifts overtone balance cleanly: bokpan triggers the deep fundamental tone needed in loud folk playing, whereas tapping byeonjuk damps the fundamental so the right-hand yeolchae yields a clean, dry 'tack' prized in refined court Jeongak."
                        ),
                        (
                            "Depending on genre, players aim for either the bokpan center or the byeonjuk rim margin: center bokpan hits maximize resonant fundamental bass, while court Jeongak players whip the byeonjuk edge with the yeolchae to produce a restrained, articulated high 'tack'."
                        ),
                    ),
                    (
                        "Want to look at the five named strokes (Deong, Gung, Tta, Gi-deok, Jjak) or the sticks themselves next?",
                        "Should we review how those zones tie into the five basic strokes next?",
                        "Curious how the yeolchae and gungchae are designed for those strike zones?",
                    ),
                    session=session,
                    separator="\n\n",
                )
                session.set_pending_offer({"type": "sticks_or_strokes"})
            elif "strokes" in entities:
                selected_facts = [f for f in all_techniques if f["id"] == "F20"]
                reply_text = compose_variation(
                    "rule::tech_strokes",
                    (
                        (
                            "Traditional janggu drumming rests on five foundational strokes:\n"
                            "- Deong (덩): Simultaneous strike on both heads anchoring the accent.\n"
                            "- Gung (궁): Deep bass hit on the left head.\n"
                            "- Tta (따): Crisp center tap on the right treble skin.\n"
                            "- Gi-deok (기덕): Rapid two-note grace flam on the treble head.\n"
                            "- Kkol / Jjak (짝): Cutting rimshot catching outer membrane and wooden hoop."
                        ),
                        (
                            "Five signature strokes organize janggu phrasing—Deong (덩) striking both heads in unison, Gung (궁) driving left bass, Tta (따) cracking the right center, Gi-deok (기덕) fluttering as a fast treble flam and Kkol / Jjak (짝) snapping sharp against the hoop rim."
                        ),
                        (
                            "Every complex rhythm breaks down into five basic moves:\n"
                            "1. Deong (덩): Both heads together.\n"
                            "2. Gung (궁): Left-head bass stroke.\n"
                            "3. Tta (따): Right-head center crack.\n"
                            "4. Gi-deok (기덕): Quick treble flam.\n"
                            "5. Kkol / Jjak (짝): Piercing edge rimshot."
                        ),
                    ),
                    (
                        "Want to see how these five strokes combine inside traditional rhythmic patterns?",
                        "Should we explore which jangdan patterns build on Deong, Gung and Tta next?",
                        "Curious how beginners start linking these strikes into full cycles?",
                    ),
                    session=session,
                    separator="\n\n",
                )
            elif "microtonal_tuning" in entities:
                selected_facts = [f for f in all_techniques if f["id"] in {"F54", "F19"}]
                reply_text = compose_variation(
                    "rule::tech_biomechanics",
                    (
                        "Each hand operates on a distinct biomechanical lever: the left-hand gungchae mallet acts as a heavy Class 3 lever powered from a base fulcrum via gross wrist and forearm motion to move dense bukpyeon cowhide, whereas the slender right yeolchae relies on a localized finger fulcrum for fast fine-motor whips against the thin chaepyeon skin.",
                        "Physically, the drummer pairs a gross-motor Class 3 lever on the left—swinging the gungchae mallet from its base fulcrum via forearm momentum—with a tight finger-fulcrum whip using the tapered yeolchae on the right. As a result, chaepyeon sends rapid directional horizontal transients while bukpyeon radiates omnidirectionally with a prolonged release.",
                        "Grip biomechanics match each membrane's inertia: a wrist-and-forearm Class 3 lever drives the padded gungchae mallet into cowhide bass, while localized finger flexion whips the flexible yeolchae for sharp treble—producing directional chaepyeon attacks against prolonged omnidirectional bukpyeon decay.",
                    ),
                    (
                        "Want to see how those forces excite specific Bessel modes on center versus rim?",
                        "Curious how Transfer Matrix fluid modeling analyzes air inside the jorongmok?",
                        "Should we examine the five foundational stroke names next?",
                    ),
                    session=session,
                    separator=" ",
                )
            else:
                selected_facts = all_techniques
                reply_text = compose_variation(
                    "rule::tech_default",
                    (
                        (
                            "How you strike the janggu shifts sharply between court and folk settings.\n\n"
                            "In seated court Jeongak, the right hand taps the rim edge (byeonjuk) with the thin bamboo yeolchae while the bare palm or fingers gently sound the left head. In vigorous folk traditions like Pungmul and Samulnori, players whip the yeolchae on the right while swinging the left-hand gungchae mallet in sweeping circular arcs.\n\n"
                            "Both styles share five named strokes: Deong (together), Gung (bass), Tta (treble), Gi-deok (flam) and Jjak (rimshot)."
                        ),
                        (
                            "Technique splits into refined court restraint versus sweeping outdoor power.\n\n"
                            "Court Jeongak pairs bare-palm left bass touches with delicate right-hand yeolchae taps along the byeonjuk edge. Folk genres (Pungmul and Samulnori) use two sticks instead: flexible bamboo yeolchae strikes paired with wide, sweeping circular arcs of the left gungchae mallet.\n\n"
                            "Across both worlds, rhythms combine five core strokes—Deong, Gung, Tta, Gi-deok and Jjak."
                        ),
                        (
                            "Whether seated or leaping, technique balances opposing hand motions around five core strokes (Deong, Gung, Tta, Gi-deok, Jjak): court Jeongak taps the byeonjuk rim lightly with the bamboo yeolchae and bare palm, while folk Pungmul and Samulnori whip the yeolchae on the right alongside sweeping circular arcs from the left-hand gungchae mallet."
                        ),
                    ),
                    (
                        "Want a closer breakdown of the sticks themselves or the five stroke sounds?",
                        "Should we zoom in next on yeolchae and gungchae construction, or stroke-zone acoustics?",
                        "Curious how each stick is crafted or how those five strokes notationally work?",
                    ),
                    session=session,
                    separator="\n\n",
                )
                session.set_pending_offer({"type": "sticks_or_strokes"})

        elif intent == "ask_acoustics":
            all_construction = self.repository.get_verified_facts("construction")
            selected_facts = [f for f in all_construction if f["id"] in {"F17", "F30", "F53", "F61", "F62", "F02", "F03", "F43"}]
            reply_text = compose_variation(
                "rule::ask_acoustics",
                (
                    (
                        "Non-linear wave and fluid acoustics shape every note on the janggu:\n"
                        "- Wave equation & Bessel modes: Circular drumheads follow the 2D polar wave equation with c = sqrt(tau / rho_s) and Bessel functions J_m(k_mn r). Edge-striking byeonjuk suppresses the (0,1) fundamental and excites asymmetric (m >= 1) modes, while high-density cowhide keeps c_left << c_right so heads never phase-align—yielding inharmonic overtones.\n"
                        "- 3D SLDV & TMM Helmholtz cavity: Non-contact 3D Scanning Laser Doppler Vibrometry (SLDV) reflects lasers off skins to image (1,1)/(2,1) modes and spot misaligned joigae wedges, while Transfer Matrix Modeling computes impedance Z = j*omega*rho_0*L_eff/A ([p1; V1] = T_n T_c [p3; V3]) across chambers (compliance C_a) and jorongmok (inertance L_a).\n"
                        "- ADSR & directional radiation: Chaepyeon delivers fast Attack/Decay with near-zero Sustain beaming horizontally, whereas bukpyeon radiates omnidirectionally with a prolonged Release."
                    ),
                    (
                        "Physically, the janggu links asymmetric Bessel-function membranes (c = sqrt(tau / rho_s), J_m(k_mn r), keeping c_left << c_right without phase alignment) across a coupled Helmholtz TMM neck (Z = j*omega*rho_0*L_eff/A, [p1; V1] = T_n T_c [p3; V3]). Non-contact 3D SLDV laser vibrometry captures (0,1) bokpan center fundamentals versus higher asymmetric (m >= 1) byeonjuk modes like (1,1)/(2,1) and diagnoses misaligned joigae tension—while chaepyeon snaps fast Attack/Decay horizontally and bukpyeon swells omnidirectionally over a long Release."
                    ),
                    (
                        "From 2D polar wave propagation [c = sqrt(tau / rho_s)] and inharmonic Bessel functions J_m(k_mn r) (where edge strikes suppress (0,1) and lift asymmetric m >= 1 modes, with c_left << c_right preventing phase alignment) to TMM cavity inertance [Z = j*omega*rho_0*L_eff/A] verified by non-contact SLDV laser velocity scans, the drum's acoustic choke prevents phase cancellation on one hand and closed-pipe dullness on the other—yielding razor-sharp directional chaepyeon ADSR transients beside prolonged omnidirectional bukpyeon release."
                    ),
                ),
                (
                    "Want to look into how FAUST models these meshes numerically, or how nakdong scorching alters Q-factor?",
                    "Curious how Paulownia porosity contributes to boundary layer damping inside the cavity?",
                    "Should we check out mechanical cord tuning, Paulownia anatomy or FDTD synthesis next?",
                ),
                session=session,
                separator="\n\n",
            )
            session.set_pending_offer({"type": "tuning_or_acoustics"})

        elif intent == "ask_construction":
            all_construction = self.repository.get_verified_facts("construction")
            if "hide_curing" in entities:
                selected_facts = [f for f in all_construction if f["id"] in {"F60", "F02", "F43"}]
                reply_text = compose_variation(
                    "rule::const_hide_curing",
                    (
                        "Rather than using harsh chemical tanning like Western orchestral drums, Korean makers shave cowhide/deerskin (36–46 cm) and horsehide/doghide (35–45 cm) to micron tolerances, soak them to extract excess proteins and cure them naturally to align collagen fibers radially—preserving viscoelasticity under intense bamboo mallet strikes.",
                        "Traditional Korean hide preparation avoids chemical tanning: skins are precision-shaved to micron thickness tolerances, soaked to wash out surplus proteins and naturally cured so collagen fibers orient radially, preserving elastic resilience (viscoelasticity) against high-force yeolchae and gungchae impacts.",
                        "Unlike chemically tanned Western drumheads, traditional janggu hides stay viscoelastic through mechanical shaving to micron tolerances, soaking away spare proteins and radial collagen-fiber alignment during natural curing.",
                    ),
                    (
                        "Want to compare how cowhide versus horsehide shifts membrane wave speed next?",
                        "Curious how animal glues like sturgeon isinglass bond the wooden shell?",
                        "Should we look at Paulownia coreana wood properties or SLDV acoustics next?",
                    ),
                    session=session,
                    separator=" ",
                )
            elif "wood_anatomy" in entities:
                selected_facts = [f for f in all_construction if f["id"] in {"F50", "F16", "F43"}]
                reply_text = compose_variation(
                    "rule::const_wood_anatomy",
                    (
                        (
                            "Micro-anatomically, Korean Paulownia coreana delivers rare stiffness per gram for an ambulatory drum:\n"
                            "- Density & stability: Oven-dry density of 260 to 340 kg/m³ and a tangential-to-radial (T/R) shrinkage ratio of 1.4 to 2.0 resist cracking under cord tension.\n"
                            "- Porosity & acoustic filtering: Ring-porous earlywood vessels measure 165–289 μm versus 55–149 μm latewood, while internal tyloses block vessels and function as natural low-pass acoustic filters.\n"
                            "- Tension wood G-fibers: Thick gelatinous fibers reach up to 65.1% crystallinity (~6.5 nm width, 19.9–39.3 MPa compressive strength), letting thin carved walls handle joigae tuning stress—and ring patterns permit dendrochronology dating."
                        ),
                        (
                            "Material science explains why Paulownia coreana dominates hollow ullimtong carving: measuring only 260–340 kg/m³ oven-dry with a stable 1.4–2.0 T/R shrinkage ratio, it contains wide 165–289 μm earlywood vessels (55–149 μm latewood) partly plugged by tyloses acting as low-pass filters. Tension wood G-fibers (~65.1% crystallinity, 6.5 nm crystallites, 19.9–39.3 MPa strength) prevent buckling under high membrane tension, while ring-width mapping anchors dendrochronological dating."
                        ),
                        (
                            "Botanical anatomy gives Paulownia coreana (density ~260–340 kg/m³, T/R shrinkage 1.4–2.0) both portability and compressive resilience: gelatinous tension wood G-fibers (up to 65.1% crystallinity, ~6.5 nm crystallites, 19.9–39.3 MPa) withstand wedge tension without collapse, while tyloses spanning 165–289 μm earlywood and 55–149 μm latewood vessels damp boundary friction as a natural low-pass acoustic filter."
                        ),
                    ),
                    (
                        "Want to look at how artisans glue seams (isinglass) and finish shells (nakdong/ottchil)?",
                        "Curious how hollowing thickness, wolf tones and floating hoops shape projection?",
                        "Should we explore surface scorching (nakdong) or tap-tuning methods next?",
                    ),
                    session=session,
                    separator="\n\n",
                )
            elif "surface_finish" in entities:
                selected_facts = [f for f in all_construction if f["id"] in {"F51", "F52", "F16"}]
                reply_text = compose_variation(
                    "rule::const_surface_finish",
                    (
                        (
                            "Traditional finishing combines crystalline protein adhesives, high-heat surface curing and acoustic carving checks:\n"
                            "- Adhesives: Artisans apply hot hide glue or sturgeon bladder fish glue (isinglass) around 60°C (140°F)—drying to crystalline hardness unlike viscoelastic synthetic PVA glues that damp kinetic transfer.\n"
                            "- Surface impedance: Nakdong (iron scorching >1000°C) and ottchil (urushi lacquer) cross-link surface cellulose to cut moisture absorption while forming a reflective layer that boosts cavity Q-factor.\n"
                            "- Fabrication & wolf tones: Hollowing a 58–66 cm log with graduated walls (thick near the waist, thinner at bearing edges) uses artisan tap-tuning to purge dissonant wolf tones, paired with floating cord hoops to extend decay."
                        ),
                        (
                            "Rather than damping synthetic PVA resins, masters bond joints with 60°C (140°F) animal hide glue or sturgeon isinglass (drying crystalline hard) and apply >1000°C nakdong scorching plus ottchil urushi lacquer—cross-linking wood cellulose to lower hygroscopicity and reflect high-frequency cavity waves for higher Q-factor. Graduated wall hollowing (58–66 cm shell) is tap-tuned against asymmetrical wolf tones, with floating joimjul hoops extending sustain."
                        ),
                        (
                            "From joinery to surface lacquer, traditional makers optimize resonance at every interface: crystal-hard animal hide or sturgeon isinglass glue (prepared at 140°F / 60°C) transfers impulse without PVA viscoelastic losses, while >1000°C nakdong scorching and ottchil lacquer seal pores to elevate Q-factor alongside graduated tap-tuned walls free of wolf tones."
                        ),
                    ),
                    (
                        "Want to look closer at Paulownia coreana cellular G-fibers and tyloses anatomy?",
                        "Curious how those tapered walls connect to the floating joimjul tuning cord geometry?",
                        "Should we examine the two contrasting drumhead hides or SLDV acoustic modes next?",
                    ),
                    session=session,
                    separator="\n\n",
                )
            elif "hornbostel" in entities:
                selected_facts = [f for f in all_construction if f["id"] == "F11"]
                reply_text = pick_variation(
                    "rule::const_hornbostel",
                    (
                        "In the Hornbostel-Sachs organology taxonomy, the janggu is classified as 211.242—a double-headed, waisted, hourglass-shaped membranophone.",
                        "Organologists assign the janggu code 211.242 under the Hornbostel-Sachs system, denoting a double-skin, waisted hourglass membranophone.",
                        "Under Hornbostel-Sachs instrument classification, the janggu falls cleanly under 211.242 (double-headed, waisted hourglass membranophone).",
                    ),
                    session=session,
                )
            elif "synthetic" in entities:
                evo_facts = self.repository.get_verified_facts("evolution")
                selected_facts = [f for f in evo_facts if f["id"] == "F44"] + [f for f in all_construction if f["id"] == "F16"]
                reply_text = compose_variation(
                    "rule::const_synthetic",
                    (
                        "21st-century practice models combine fiberglass-reinforced plastic (FRP) shells and synthetic Mylar heads so schools and outdoor ensembles avoid weather warping from humidity and temperature shifts—though traditional purists still prefer aged Paulownia wood (ullimtong) and animal hide for warmer inharmonic overtones.",
                        "Synthetic FRP fiberglass bodies and Mylar drumheads shine in school classrooms and humid outdoor venues where wood might swell. Even so, experienced players note they trade away the warm, complex inharmonic overtone bloom of cured Paulownia ullimtong shells and natural hides.",
                        "Modern fiberglass (FRP) shells and Mylar synthetic skins hold tuning steadier across harsh humidity and temperature swings, making them popular for students; purists, however, favor aged Paulownia wood and natural leather for tonal warmth and overtone complexity.",
                    ),
                    (
                        "Want to look into how traditional artisans season wooden shells or tune cords?",
                        "Curious why natural cowhide and horsehide vibrate differently from Mylar?",
                        "Should we check out Paulownia wood crafting or mechanical wedge tuning next?",
                    ),
                    session=session,
                    separator=" ",
                )
            elif "joimjul" in entities or "joigae" in entities:
                selected_facts = [f for f in all_construction if f["id"] == "F18"]
                reply_text = compose_variation(
                    "rule::const_joimjul",
                    (
                        "Continuous V-shaped tension cords (joimjul) pull both heads toward the waist, clasped by sliding leather or wooden wedges called joigae. Sliding wedges toward the right head pinches the cords tighter to raise tension and pitch; nudging them left releases slack. Because one continuous lacing joins both heads, tuning either side subtly shifts the opposite head too.",
                        "Both drumheads share continuous V-laced cords (joimjul) controlled by movable leather wedges (joigae). Push wedges right to pinch the V-lacing and sharpen pitch, or pull left to loosen tension—and because both sides sit on one continuous lace, tightening one head gently alters the other head as well.",
                        "Tuning requires no metal bolts: movable leather wedges (joigae) pinch along continuous V-shaped joimjul cords. Moving wedges rightward raises pitch while moving left drops it, and because one shared lacing links both hoops, adjusting either side nudges tension across both heads.",
                    ),
                    (
                        "Want to compare the cowhide and horsehide heads those cords stretch across?",
                        "Curious why both heads respond together acoustically when you shift those wedges?",
                        "Should we look at the two contrasting drumhead hides next?",
                    ),
                    session=session,
                    separator=" ",
                )
            elif "ullimtong" in entities:
                selected_facts = [f for f in all_construction if f["id"] in {"F16", "F43"}]
                reply_text = compose_variation(
                    "rule::const_ullimtong",
                    (
                        "Craftspeople turn the hourglass resonator body (ullimtong) out of a single solid log of Paulownia coreana—seeking 30-plus-year trees grown in harsh rocky mountain soil for dense grain. The hollowed trunk ages naturally for two to three years before its interior is fire-scorched to seal wood pores against moisture.",
                        "Rather than gluing thin wooden slats, makers hollow the ullimtong out of one Paulownia tree (typically 30+ years old from lean, rocky mountain slopes), season it for two to three years and scorch the inside cavity with fire to harden fibers and lock out moisture.",
                        "Artisans build each ullimtong from a single block of aged Paulownia wood sourced from 30-plus-year mountain trees on rocky soil—curing the carved shell two to three years and scorching the interior hollow so moisture cannot easily penetrate the wood pores.",
                    ),
                    (
                        "Want to look next at the contrasting hides stretched across its ends or the narrow central waist?",
                        "Curious why that waist tube is carved so narrow in the middle?",
                        "Should we inspect how the two skins or the acoustic waist choke work?",
                    ),
                    session=session,
                    separator=" ",
                )
            elif "jorongmok" in entities:
                selected_facts = [f for f in all_construction if f["id"] in {"F03", "F17"}]
                reply_text = compose_variation(
                    "rule::const_jorongmok",
                    (
                        "At the center sits the narrowed neck tube called the jorongmok, engineered as an acoustic choke: it lets low bass air pressure couple across both bowls while preventing the thick bass skin from damping crisp treble resonance.",
                        "That slim central waist—the jorongmok—functions as a natural acoustic choke. Low frequencies resonate smoothly between the two chambers, yet sharp high-frequency treble overtones remain isolated rather than damped.",
                        "Called the jorongmok, the narrow wooden neck keeps high-frequency treble strokes sparkling and un-damped while linking low-frequency pressure resonance across the two hourglass chambers.",
                    ),
                    (
                        "Want to check out how the V-shaped cords tune pitch, or how both drumheads are skinned?",
                        "Curious about the asymmetric hides mounted on either side of that waist?",
                        "Should we look at the tuning wedges or the cowhide/horsehide skins next?",
                    ),
                    session=session,
                    separator=" ",
                )
            elif "gungpyeon" in entities or "chaepyeon" in entities:
                selected_facts = [f for f in all_construction if f["id"] in {"F02", "F43", "F30"}]
                reply_text = compose_variation(
                    "rule::const_heads",
                    (
                        (
                            "The drum's two faces pair deliberate contrasts in skin density, thickness and diameter (symbolizing Yin and Yang):\n"
                            "- Left head (gungpyeon, usually 36 to 46 cm across): Thick cowhide or deerskin—higher areal mass density slows membrane wave speed for deep bass pitch.\n"
                            "- Right head (chaepyeon, usually 35 to 45 cm across): Thin horsehide or doghide—tight, light responsiveness for stinging treble crack."
                        ),
                        (
                            "Traditional janggu skins balance thick bass mass against thin treble snap across opposite sides (36 to 46 cm vs. 35 to 45 cm):\n"
                            "On the left (gungpyeon), heavy cowhide or deerskin increases areal mass density for warm low resonance; on the right (chaepyeon), thin horsehide or doghide projects crisp treble attacks—embodying harmonic Yin-Yang duality."
                        ),
                        (
                            "Asymmetric leather selection shapes both sides: the 36 to 46 cm left head (gungpyeon) mounts dense cowhide or deerskin for deep bass wave behavior, whereas the slightly smaller 35 to 45 cm right head (chaepyeon) uses taut horsehide or doghide for bright high-pitched cut."
                        ),
                    ),
                    (
                        "Want to examine the contrasting sticks used on each side, or how sliding wedges tune them?",
                        "Curious how joigae wedges tighten these shared laces, or how mallets strike each hide?",
                        "Should we look at tuning cords next or contrast yeolchae and gungchae sticks?",
                    ),
                    session=session,
                    separator="\n\n",
                )
            else:
                selected_facts = [f for f in all_construction if f["id"] in {"F01", "F02", "F16", "F17", "F18"}]
                reply_text = compose_variation(
                    "rule::const_default",
                    (
                        (
                            "Standing roughly 66 cm long, the hourglass janggu pairs carefully asymmetric materials:\n\n"
                            "A hollowed Paulownia wood body (ullimtong)—cured two to three years and interior-scorched—holds a narrow central waist (jorongmok) acting as an acoustic choke. "
                            "Its thick cowhide left head (gungpyeon) anchors deep bass against thin horsehide or doghide treble skin on the right (chaepyeon), laced by V-shaped cords (joimjul) and sliding leather wedges (joigae)."
                        ),
                        (
                            "A standard wooden janggu measures approximately 66 cm end to end and merges four structural elements: "
                            "an aged, fire-scorched Paulownia body (ullimtong); a narrow central choke tube (jorongmok) keeping bass from damping treble; asymmetric cowhide bass (left) and thin horsehide/doghide treble (right) heads; and sliding joigae wedges riding continuous V-shaped joimjul tension cords."
                        ),
                        (
                            "Built around an asymmetric ~66 cm hourglass wooden shell, the janggu connects thick cowhide on the left to crisp horsehide or doghide on the right over a single-piece Paulownia body (ullimtong, aged 2–3 years with a scorched interior). The narrow jorongmok waist stops treble damping while continuous joimjul ropes and joigae wedges manage surface tension."
                        ),
                    ),
                    (
                        "Which piece of construction catches your eye most—wood curing, drumheads, waist acoustics or cords?",
                        "Would you like to zoom into the Paulownia shell, the opposing hides or the wedge tuning system?",
                        "Where should we focus closer on craftsmanship?",
                    ),
                    session=session,
                    separator="\n\n",
                )

        elif intent == "ask_cultural_significance":
            all_cultural = self.repository.get_verified_facts("cultural_use")
            disputed_cultural = self.repository.get_disputed_facts("cultural_use")
            if "microtonal_tuning" in entities:
                all_chron = self.repository.get_verified_facts("chronology")
                selected_facts = [f for f in all_cultural if f["id"] == "F55"] + [f for f in all_chron if f["id"] == "F29"]
                reply_text = compose_variation(
                    "rule::cult_microtonal",
                    (
                        (
                            "Instead of locking to Western A=440Hz equal temperament, janggu drummers slide joigae wedges and modulate hand pressure so bass resonance matches microtonal sigimsae bends on melodic instruments like the ajaeng or piri.\n\n"
                            "Those cycles are documented in King Sejong's 1447 Jeongganbo grid (one jeonggan cell per beat), read top-to-bottom and right-to-left across gak columns."
                        ),
                        (
                            "Korean ensemble pitch rejects rigid A=440Hz equal temperament: drummers tune joigae wedges and press into membranes to match microtonal sigimsae vibrato on instruments such as ajaeng and piri. Traditional scores use King Sejong's 1447 Jeongganbo mensural grid—column-oriented (gak) cells read top-to-bottom, right-to-left."
                        ),
                        (
                            "Through wedge adjustment (joigae) and subtle strike pressure modulation, the drum blends microtonally with pitch-bending instruments like piri and ajaeng rather than A=440Hz temperament, guided historically by King Sejong's 1447 Jeongganbo spatial columns (gak) read top-to-bottom and right-to-left."
                        ),
                    ),
                    (
                        "Want to look at how KAIST's Umulsai EBNF formal grammar digitizes Jeongganbo scores?",
                        "Curious about the asymmetric jangdan meters written into those grid columns?",
                        "Should we explore the seven jangdan time cycles or digital OMR tools next?",
                    ),
                    session=session,
                    separator="\n\n",
                )
            elif "pansori" in entities:
                selected_facts = [f for f in all_cultural if f["id"] in {"F39", "F24", "F21", "F28"}]
                reply_text = compose_variation(
                    "rule::cult_pansori",
                    (
                        (
                            "In Pansori narrative drama, jangdan patterns supply the rhythmic canvas around vocal sigimsae ornaments and chuimsae interaction:\n"
                            "- Jajinmori (fast 12/8): Drives urgent battle scenes, including naval clashes in Jeokbyeokga (Song of the Red Cliffs).\n"
                            "- Jinyangjo (slow 24-beat): Carries profound grief and solemn dramatic weight."
                        ),
                        (
                            "Alongside vocal sigimsae embellishments and chuimsae interjections, Pansori uses specific jangdan grooves to match narrative stakes—notably fast 12/8 Jajinmori for high-intensity battles like Jeokbyeokga's naval conflict, contrasted with unhurried 24-beat Jinyangjo for tragic laments."
                        ),
                        (
                            "During Pansori storytelling, rhythmic pacing frames every dramatic scene alongside vocal ornaments (sigimsae) and chuimsae cheers: 12/8 Jajinmori underscores fast battle action (famous in Jeokbyeokga), whereas 24-beat Jinyangjo expands sorrowful moments."
                        ),
                    ),
                    (
                        "Want to hear how those rhythms look in folk dances and shamanic rituals too?",
                        "Curious about other jangdan patterns across traditional genres?",
                        "Should we review the remaining jangdan cycles outside Pansori?",
                    ),
                    session=session,
                    separator="\n\n",
                )
            elif "nongak_pungmul" in entities and disputed_cultural:
                selected_facts = [f for f in all_cultural if f["id"] in {"F06", "F38"}] + disputed_cultural
                reply_text = compose_variation(
                    "rule::cult_nongak_pungmul",
                    (
                        (
                            "Scholars and sources disagree on whether to call the folk percussion tradition 'nongak' or 'pungmul':\n\n"
                            "- Institutional records—from An Yu-sin's 1657 text to South Korea's 1966 Asset No. 11 and UNESCO's 2014 listing—officially use 'nongak' (farmers' music).\n"
                            "- Since the 1980s minjung cultural movement, activists and ethnomusicologists have favored 'pungmul' to foreground shamanic rituals and communal village agency rather than colonial agricultural framing.\n\n"
                            "In processions, the lead seoljanggu player guides tempo transitions, sangmo hat spinning and solo display."
                        ),
                        (
                            "Two terms appear side by side with active debate in Korean scholarship (`nongak` vs. `pungmul`), showing clear disagreement:\n\n"
                            "Official heritage designations—spanning An Yu-sin's 1657 mention, South Korea's 1966 Cultural Asset No. 11 and the 2014 UNESCO registration—say 'nongak'. Meanwhile, 1980s minjung-era researchers prefer 'pungmul' to emphasize shamanic ritual life and civic community instead of colonial-era farming labels.\n\n"
                            "Within these bands, the lead seoljanggu coordinates tempo shifts, sangmo ribbon choreography and solo passages."
                        ),
                        (
                            "Terminology remains disputed in Korean ethnomusicology because institutional documents and modern critics weigh different histories:\n\n"
                            "Historical and state files (An Yu-sin in 1657, 1966 Asset No. 11, 2014 UNESCO listing) stick with 'nongak', while minjung-movement scholars since the 1980s champion 'pungmul' to reject colonial farming framing and restore focus on shamanic community roots—featuring lead seoljanggu soloists with spinning sangmo hats."
                        ),
                    ),
                    (
                        "Want to look next at how outdoor folk playing compares with seated royal court ensembles?",
                        "Should we compare folk village drumming with formal court music next?",
                        "Curious whether you prefer diving into royal court tradition or village folk practice next?",
                    ),
                    session=session,
                    separator="\n\n",
                )
                session.set_pending_offer({"type": "court_or_folk"})
            elif "seoljanggu" in entities:
                selected_facts = [f for f in all_cultural if f["id"] in {"F38", "F65", "F06"}]
                reply_text = compose_variation(
                    "rule::cult_seoljanggu",
                    (
                        "Within civilian pungmul troupes, the seoljanggu is the lead drummer directing ensemble tempo shifts alongside spinning sangmo ribbon-hat choreography. Honam Udo master Kim Byeong-seop (1921-1987) elevated that leadership into solo gaeinjanggunori performance, while in modern staged Samulnori ethnographers note women drummers adopting forceful kinetic postures ('masculinization of women drummers') to build legitimacy alongside historically male Namsadang lineages.",
                        "Acting as rhythmic conductor and featured dancer, the seoljanggu guides pacing transitions and sangmo hat spins in village pungmul bands—turned into intricate solo repertoire (gaeinjanggunori) by Honam Udo master Kim Byeong-seop (1921-1987). Contrasting quiet court Jeongak/Aak score reading, contemporary staged Samulnori also highlights female drummers embracing aggressive Namsadang-derived kinetic movements.",
                        "Leading pungmul formations on the field, the seoljanggu commands tempo changes and sangmo ribbon choreography; Honam Udo master Kim Byeong-seop (1921-1987) codified solo gaeinjanggunori phrasing, contrasting court Jeongak/Aak restraint while modern Samulnori stages reflect intense physical postures adopted by both men and women percussionists.",
                    ),
                    (
                        "Want to look at the five janggu strokes or the jangdan patterns they perform?",
                        "Curious how seoljanggu players swing the mallets or which rhythms they improvise on?",
                        "Should we cover folk rhythm cycles next or the sticks themselves?",
                    ),
                    session=session,
                    separator=" ",
                )
            else:
                selected_facts = [f for f in all_cultural if f["id"] in {"F06", "F21", "F28"}]
                reply_text = compose_variation(
                    "rule::cult_default",
                    (
                        "Almost no traditional Korean genre leaves out the janggu—it anchors refined court music (Jeongak), solo Sanjo recitals, shamanic rituals and vibrant farmers' folk festivals (Nongak / Pungmul), uniting melodic pacing and ensemble groove.",
                        "Whether backing serene court rites, expressive Sanjo instrumentals, shamanic gut ceremonies or boisterous rural Nongak / Pungmul folk festivals, the janggu functions as the rhythmic center of Korean traditional music.",
                        "Across Korea's musical landscape—royal banquets, shaman rituals, intimate Sanjo solos and rural folk festivals (Nongak / Pungmul)—the janggu keeps ensemble timing cohesive and emotionally expressive.",
                    ),
                    (
                        "Want to focus next on village folk roles or explore the rhythmic jangdan patterns themselves?",
                        "Should we look closer at folk drumming traditions or break down its core rhythms?",
                        "Curious whether you want to inspect court versus village contexts or its seven main jangdan cycles?",
                    ),
                    session=session,
                    separator=" ",
                )

        if not selected_facts:
            fallback_msg = pick_variation(
                "rule::fallback",
                (
                    "I don't have verified information on that yet.",
                    "I don't have verified information on that yet—try asking about the janggu's history, construction, acoustics or jangdan rhythms.",
                    "I don't have verified information on that yet, as my knowledge base sticks strictly to verified Korean janggu sources.",
                ),
                session=session,
            )
            return {
                "status": "fallback",
                "text": fallback_msg,
                "fact_ids": [],
                "confidence": confidence,
            }

        fact_ids = [f["id"] for f in selected_facts]
        session.set_topic(intent or "general", fact_ids)

        return {
            "status": "answered",
            "text": reply_text or " ".join(f["statement"] for f in selected_facts),
            "fact_ids": fact_ids,
            "confidence": confidence,
        }
