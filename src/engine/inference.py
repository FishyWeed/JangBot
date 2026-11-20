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
            if not selected_facts:
                selected_facts = [f for f in self.repository.get_verified_facts() if f["id"] == "F06"]
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
            cultural_facts = self.repository.get_verified_facts("cultural_use")
            named_jangdans = [
                k for k in ("jinyangjo", "jungmori", "jungjungmori", "jajinmori", "hwimori", "gutgeori", "eonmori")
                if k in entities
            ]
            single_jangdan = named_jangdans[0] if len(named_jangdans) == 1 else None
            if "chuimsae" in entities:
                selected_facts = [f for f in cultural_facts if f["id"] == "F28"]
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
            elif single_jangdan == "jinyangjo":
                selected_facts = [f for f in cultural_facts if f["id"] == "F21"]
                reply_text = compose_variation(
                    "rule::jangdan_jinyangjo",
                    (
                        "Slow down your breathing and step into Jinyangjo—the widest, most patient cycle in traditional Korean drumming. Stretching across 24 slow beats, it carries deep sorrow, longing and quiet aristocratic dignity, giving Pansori singers and Sanjo soloists room to bend a single note across a whole span of memory.",
                        "At the calmest, heaviest end of the jangdan spectrum sits 24-beat Jinyangjo. In tragic Pansori scenes and stately Sanjo openings, every strike leaves generous space in the air so grief and noble restraint can settle over the room.",
                    ),
                    (
                        "Want to pick up the pace into walking 12-beat Jungmori or swinging Gutgeori next?",
                        "Should we leap all the way to the opposite extreme—blazing 4-beat Hwimori?",
                    ),
                    session=session,
                    separator=" ",
                )
                session.set_pending_offer({"type": "slow_or_fast_rhythms", "slow_done": True})
            elif single_jangdan == "jungmori":
                selected_facts = [f for f in cultural_facts if f["id"] == "F22"]
                reply_text = compose_variation(
                    "rule::jangdan_jungmori",
                    (
                        "Jungmori walks forward like a storyteller striding down a quiet country road. Moving in a steady, lyrical 12-beat pulse, it anchors narrative Pansori stretches and gives beginners enough breathing room to land a clean Deong downbeat without rushing either hand.",
                        "Set at a moderate 12-beat walking pace, Jungmori balances calm narrative flow with clear structural downbeats—making it both a pillar of lyrical storytelling and the classic starting cycle for new janggu students.",
                    ),
                    (
                        "Want to hear how Jungjungmori brightens that same 12-beat road, or jump into Gutgeori's dance swing?",
                        "Should we look at the five strokes that build Jungmori, or step up into faster folk cycles?",
                    ),
                    session=session,
                    separator=" ",
                )
                session.set_pending_offer({"type": "beginner_rhythms"})
            elif single_jangdan == "jungjungmori":
                selected_facts = [f for f in cultural_facts if f["id"] == "F23"]
                reply_text = compose_variation(
                    "rule::jangdan_jungjungmori",
                    (
                        "Pick up the lantern and lighten your step—Jungjungmori takes a 12-beat pulse and infuses it with playful, graceful bounce. Performers reach for it whenever a tale turns lively, witty or celebratory, letting dance-like phrasing lift the entire room.",
                        "Brighter and livelier than walking Jungmori, 12-beat Jungjungmori carries cheerful momentum tailored for spirited dance passages and lighthearted storytelling scenes.",
                    ),
                    (
                        "Want to compare that cheerful bounce with Gutgeori's village dance swing or crooked 10-beat Eonmori?",
                        "Should we jump into shamanic Gutgeori or urgent battle-paced Jajinmori next?",
                    ),
                    session=session,
                    separator=" ",
                )
                session.set_pending_offer({"type": "slow_or_fast_rhythms"})
            elif single_jangdan == "gutgeori":
                selected_facts = [f for f in cultural_facts if f["id"] == "F26"]
                reply_text = compose_variation(
                    "rule::jangdan_gutgeori",
                    (
                        "Nothing gets shoulders swaying in a Korean courtyard faster than Gutgeori. Built on a lilting, syncopated 12-beat swing, it bridges lively folk dances and shamanic ritual gatherings—pulling players and spectators alike into an infectious communal bounce.",
                        "Across folk dance and shamanic rites alike, 12-beat Gutgeori brings an unmistakable rolling groove—anchored by a crisp Deong downbeat and lifted by playful syncopation across the thin right head.",
                    ),
                    (
                        "Want to contrast Gutgeori's smooth swing with asymmetric 10-beat Eonmori or blazing Hwimori?",
                        "Curious how chuimsae shouts like 'Eolssigu!' energize a Gutgeori groove live on stage?",
                    ),
                    session=session,
                    separator=" ",
                )
                session.set_pending_offer({"type": "chuimsae_offer"})
            elif single_jangdan == "eonmori":
                selected_facts = [f for f in cultural_facts if f["id"] == "F27"]
                reply_text = compose_variation(
                    "rule::jangdan_eonmori",
                    (
                        "Just when your ears expect neat 12-beat symmetry, Eonmori tilts the floor beneath you. Built on an asymmetric 10-beat grouping of 3+2+3+2, its off-kilter pulse conjures mystery, heroic entrances and supernatural tension in Pansori drama.",
                        "Eonmori stands out immediately for its crooked 10-beat architecture (3+2+3+2). Whenever a mysterious figure, spirit or bold hero enters a dramatic scene, that asymmetric lilt warns listeners something uncanny is unfolding.",
                    ),
                    (
                        "Want to charge straight into urgent 12-beat Jajinmori battle energy next, or slow down to Jinyangjo?",
                        "Should we compare Eonmori's asymmetric 10-beat tension with blazing 4-beat Hwimori?",
                    ),
                    session=session,
                    separator=" ",
                )
                session.set_pending_offer({"type": "slow_or_fast_rhythms", "slow_done": True})
            elif single_jangdan == "jajinmori":
                selected_facts = [f for f in cultural_facts if f["id"] in {"F24", "F36"}]
                reply_text = compose_variation(
                    "rule::jangdan_jajinmori",
                    (
                        "When the plot breaks into a sprint, the drummer shifts straight into Jajinmori—a fast, urgent 12/8 cycle brimming with tension and action. In Pansori masterpieces like Jeokbyeokga (Song of the Red Cliffs), Jajinmori paints the clash of naval battle without needing a single real war drum.",
                        "Driven by brisk, relentless 12-beat propulsion, Jajinmori scores high-stakes chases, comic flurries and wartime scenes such as the famed naval battle in Jeokbyeokga.",
                    ),
                    (
                        "Want to push even faster into the 4-beat sprint of Hwimori, or hear why real military Daechwita marched with the yonggo instead?",
                        "Should we compare Jajinmori's urgency with blazing 4-beat Hwimori next?",
                    ),
                    session=session,
                    separator=" ",
                )
                session.set_pending_offer({"type": "slow_or_fast_rhythms", "slow_done": True})
            elif single_jangdan == "hwimori":
                selected_facts = [f for f in cultural_facts if f["id"] == "F25"]
                reply_text = compose_variation(
                    "rule::jangdan_hwimori",
                    (
                        "Picture the final breathless minutes of a village festival or Samulnori showcase—that whirlwind is Hwimori. Compressing rhythm into a blazing 4-beat gallop, drummers whip rapid syncopated accents faster and faster until the whole room hits peak climax.",
                        "Hwimori is the full-throttle sprint of traditional jangdan cycles: four urgent beats hurtling forward in dazzling, accelerated strikes that bring performances to a triumphant finale.",
                    ),
                    (
                        "Want to catch your breath on the exact opposite end with slow 24-beat Jinyangjo?",
                        "Should we look at the flexible bamboo yeolchae wrist whip that makes Hwimori speeds possible?",
                    ),
                    session=session,
                    separator=" ",
                )
                session.set_pending_offer({"type": "slow_or_fast_rhythms", "fast_done": True})
            else:
                selected_facts = [f for f in cultural_facts if f["id"] in {"F21", "F22", "F24", "F25", "F26", "F27"}]
                reply_text = compose_variation(
                    "rule::jangdan_list",
                    (
                        (
                            "Think of Korean jangdan cycles like seven shifting chapters in a musical story. A tragic Pansori lament opens gently over slow, breathing 24-beat Jinyangjo filled with deep sorrow and aristocratic dignity, then eases forward into calm 12-beat Jungmori like a steady walk down a road before springing into buoyant Jungjungmori.\n\n"
                            "Out in village dance or shamanic ritual, players lean into swinging 12-beat Gutgeori, or tilt into the uncanny 3+2+3+2 pulse of 10-beat Eonmori whenever spirits or heroes arrive. And when battle or climax erupts, rapid 12-beat Jajinmori drives the chase until blazing 4-beat Hwimori leaves the room breathless."
                        ),
                        (
                            "Walk through a full Korean performance and you hear seven jangdan moods shaping every scene along the way. Storytellers lean on expansive 24-beat Jinyangjo for heartbreaking reflection, shift into calm 12-beat Jungmori for lyrical storytelling and lift the room with playful Jungjungmori.\n\n"
                            "From there, swinging 12-beat Gutgeori sweeps dancers onto their feet in folk and shamanic rites, crooked 10-beat Eonmori (3+2+3+2) signals mysterious heroes, urgent 12-beat Jajinmori charges through battle action and explosive 4-beat Hwimori crowns the climax."
                        ),
                        (
                            "Every Korean piece rides on a named jangdan cycle tailored to its human mood—stretching out in solemn 24-beat Jinyangjo for grief, stepping comfortably across 12-beat Jungmori walking tempo, bouncing through cheerful Jungjungmori and swaying to 12-beat Gutgeori folk swing, before turning mysterious in asymmetric 10-beat Eonmori (3+2+3+2), racing with urgent 12-beat Jajinmori and peaking in fearless 4-beat Hwimori."
                        ),
                    ),
                    (
                        "Which chapter of rhythm—slow sorrowful Jinyangjo, swinging Gutgeori or blazing Hwimori—sounds closest to what you want to hear next?",
                        "Any single cycle among those seven stories you want to explore closely?",
                        "Want to step inside one of these tempos—from walking Jungmori to Hwimori's sprint?",
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
                        "Even the instrument's oldest names tell two quick stories about how Koreans saw and played it. Long ago, chroniclers called it the seyogo (細腰鼓)—literally the 'slim waist drum'—because its pinched wooden silhouette caught the eye first.\n\n"
                        "Later, speakers paired the Sino-Korean characters for 'stick' (杖) and 'drum' (鼓) into janggo (장고 / 杖鼓), or janggu, putting the focus on the thin sticks striking both skins."
                    ),
                    (
                        "Two classical names hand down the story of the drum's shape and play style: the earlier title seyogo (細腰鼓, meaning 'slim waist drum') points right at its narrowed midsection, whereas janggu / janggo (장고 / 杖鼓) links the Sino-Korean words for 'stick' (杖) and 'drum' (鼓) to celebrate stick-driven drumming."
                    ),
                    (
                        "Trace the drum's Korean names backward and two vivid images emerge—first, the physical outline captured by seyogo (細腰鼓, 'slim waist drum'), and second, the motion of a drummer's hands preserved in janggu or janggo (장고 / 杖鼓), combining 'stick' (杖) with 'drum' (鼓)."
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
                            "Picture a conservator holding a fragile Joseon or Goryeo janggu—cutting into old wood would ruin it, so museum science reads its story without opening a single joint. Using Synchrotron X-ray Microtomography (SR-μCT) and CT scans, researchers peer straight through centuries-old timber to discover concealed dowels, historical animal-glue repairs and micro-fractures while reading earlywood and latewood growth rings via dendrochronology.\n\n"
                            "Outside the shell, portable X-ray Fluorescence (p-XRF) traces heavy metals in antique ottchil lacquer and catches damaging prior PEG consolidants. To stop swelling or jorongmok cracks, galleries hold climate equilibrium near 20°C and 50 to 55% relative humidity while capturing 3D photogrammetry twins—even preserving delicate National Museum Goryeo bisaek celadon sajanggu Duksu 1726 fired around 1,150°C at Gangjin kilns."
                        ),
                        (
                            "Without touching a saw to fragile artifacts, conservators uncover centuries of craftsmanship through imaging and chemistry: SR-μCT and cylindrical CT reveal hidden internal dowels, antique glue fixes and dendrochronology ring histories, while p-XRF maps antique ottchil pigments and past Polyethylene Glycol (PEG) treatments. Inside climate rooms held steady at 20°C and 50–55% relative humidity to prevent jorongmok micro-fracturing, museums build 3D photogrammetry digital twins—safeguarding treasures like Goryeo celadon sajanggu Duksu 1726 from Gangjin's ~1,150°C kilns."
                        ),
                        (
                            "Forensic conservation turns historic instruments into readable time capsules: Synchrotron X-ray Microtomography (SR-μCT) and climate-ring dendrochronology inspect concealed joinery non-destructively while p-XRF identifies authentic ottchil metals and older PEG consolidants, backed by 3D photogrammetric replicas and calm 20°C / 50–55% humidity vaults protecting both wooden janggu bodies and Goryeo bisaek celadon Duksu 1726 (~1,150°C Gangjin firing)."
                        ),
                    ),
                    (
                        "Want to hear the botanical story of Paulownia coreana wood before it even enters a workshop?",
                        "Curious why Goryeo celadon sajanggu stayed in chambers while wood took over the folk road?",
                        "Should we explore nakdong iron scorching or antique animal-glue joinery next?",
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
                            "Think of Jeongganbo EBNF as translating King Sejong's 15th-century ink grid into a script a computer can breathe with. Where a traditional musician looks down columns of squares, KAIST's Umulsai project formalizes that layout cleanly—defining `Score ::= Gak+`, `Gak ::= Jeonggan+`, `Jeonggan ::= (Stroke | SubJeonggan | Rest)`, `SubJeonggan ::= Stroke Stroke | Stroke Rest`, with `Stroke ::= 'Deong' | 'Gung' | 'Tta' | 'Gideok' | 'Jjak'` and `Rest ::= '△' | '-'`.\n\n"
                            "By stretching or nudging the duration inside those SubJeonggan tokens, software can recreate living human swing and rubato rather than stiff robotic clicks—pairing neatly with MelCNN classifiers that recognize crisp tta onset smears beside high-Q gung bass peaks."
                        ),
                        (
                            "Back in 1447, King Sejong arranged beats in visual square columns called gak; modern digital engraving systems like Umulsai retell that geometry as formal EBNF rules (`Score ::= Gak+`, `Gak ::= Jeonggan+`, `Jeonggan ::= (Stroke | SubJeonggan | Rest)`, `SubJeonggan ::= Stroke Stroke | Stroke Rest`, strokes `Deong`/`Gung`/`Tta`/`Gideok`/`Jjak` and rests `△`/`-`). Scaling SubJeonggan time lets machines mimic subtle performance swing and rubato alongside MelCNN recognition of tta smears versus high-Q gung strikes."
                        ),
                        (
                            "To bridge Joseon paper scores and modern software, EBNF rules trace columns from `Score ::= Gak+` down through `Jeonggan ::= Stroke | SubJeonggan | Rest`, where adjusting `SubJeonggan` subdivisions encodes genuine human rubato and swing—working alongside MelCNN spectrogram models that tell sharp tta onset smears apart from resonant high-Q gung peaks."
                        ),
                    ),
                    (
                        "Want to hear how digital acoustics software simulates the drum's membranes in FAUST next?",
                        "Curious how Jeongganbo columns follow microtonal pitch beside instruments like ajaeng and piri?",
                        "Should we jump into 2D FDTD waveguide synthesis on Bela boards or trace Umulsai OMR?",
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
                            "Bringing an ancient wooden drum into modern code meant solving two separate puzzles. First, percussion strikes do not glide across vocal melodies like singing sigimsae tracked by F0CNN and RMVPE—instead, crisp tta hits splatter vertical energy while gung beats leave focused low-frequency high-Q peaks. So researchers train transient MelCNN, hybrid CNN/RNN and 95M-parameter MERT-v1 models on piezo and accelerometer streams, grading transcription with Macro F1 and Event F1/IoU metrics.\n\n"
                            "Meanwhile, synthesis engineers build a virtual skin out of FAUST FDTD Digital Waveguide Meshes obeying CFL stability—advancing grid pressure as `p(i,j,n+1) = 0.5*(p(i-1,j,n)+p(i+1,j,n)+p(i,j-1,n)+p(i,j+1,n)) - p(i,j,n-1)` against hoop and joimjul boundary tension coupled to a 1D cavity guide—while the hybrid iJanggu hides piezo pickups inside the Paulownia shell or beneath bukpyeon to drive real-time Bela boards running Pure Data or FAUST without MIDI latency."
                        ),
                        (
                            "Modern digital organology follows the drummer's hands from skin strike straight to synthesis code: where vocal software uses F0CNN/RMVPE for singing ornaments, janggu systems rely on MelCNN and MERT-v1 (95M) to separate broadband tta smears from resonant gung peaks (scored via Macro F1 and Event F1/IoU). On physical synthesis, CFL-stable 2D FDTD waveguide meshes in FAUST (`p(i,j,n+1) = 0.5*(neighbors) - p(i,j,n-1)`) connect two virtual hides over a 1D cavity while iJanggu mounts piezo mics inside Paulownia shells or under bukpyeon straight into Bela microcontrollers (Pure Data / FAUST) with zero MIDI lag."
                        ),
                        (
                            "From piezoelectric shell and under-bukpyeon sensors feeding Bela boards (Pure Data / FAUST) to eliminate MIDI delay, up through FAUST 2D FDTD Digital Waveguide Meshes updating rectilinear grids under CFL limits alongside MERT-v1 (95M) and MelCNN models distinguishing sharp tta smears from gung peaks, computational musicology lets the physical janggu speak directly inside code."
                        ),
                    ),
                    (
                        "Want to step inside museum conservation next—seeing how SR-μCT and p-XRF study ancient shells?",
                        "Curious about how KAIST's Jeongganbo EBNF grammar turns old notation into playable scores?",
                        "Should we explore 3D Vibrometry (SLDV) laser scans of real vibrating hides next?",
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
                            "When engineers tried putting the janggu into the digital age, they quickly saw that flat capacitive electronic drum pads killed what makes the drum come alive: the rebound of horsehide and flex of a bamboo stick. So the hybrid iJanggu takes a different route—tucking piezoelectric contact sensors directly onto natural membranes so every subtle touch drives physical modeling synthesis in real time.\n\n"
                            "Across on the preservation front at KAIST, Danbinaerin Han led the Umulsai optical music recognition (OMR) system, applying EBNF grammars and JSON rules to translate old Jeongganbo drum scores into living digital records."
                        ),
                        (
                            "Rather than flattening the instrument onto lifeless capacitive electronic pads, the iJanggu wires piezoelectric pickups onto authentic skins so acoustic vibration sparks physical modeling synthesis while keeping real tactile rebound intact. At KAIST, Danbinaerin Han's Umulsai OMR software decodes traditional Jeongganbo scores via EBNF grammars and JSON layout rules."
                        ),
                        (
                            "Two modern innovations carry craft heritage into computing: the iJanggu steps past stiff capacitive electronic drum pads by mounting piezo contact sensors straight onto real janggu skins for physical modeling synthesis, while KAIST's Umulsai OMR project led by Danbinaerin Han parses Jeongganbo manuscripts using EBNF grammars and JSON rules."
                        ),
                    ),
                    (
                        "Want to look at weather-resistant FRP/Mylar school drums next, or dive into circular membrane physics?",
                        "Curious about FRP/Mylar school instruments or Bessel-mode acoustics next?",
                        "Should we inspect modern synthetic drumheads or natural Paulownia workshop crafting next?",
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
                            "The story of how the janggu evolved keeps moving between royal chambers, village fields, modern stages and engineering labs. After Three Kingdoms waist drums and fragile 13th-century Goryeo celadon sajanggu vessels gave way to durable carved wood on the folk road, Kim Deok-soo launched Samulnori in 1978, distilling ambulatory pungmul bands into a seated quartet where modern female drummers also reshaped performance energy with fierce kinetic gestures.\n\n"
                            "By the 21st century, classrooms adopted humidity-proof fiberglass (FRP) shells and Mylar heads alongside wooden drums—though purists still prefer wood and natural hide overtones—while KAIST's Umulsai OMR software and the piezo-equipped iJanggu carried traditional drumming into digital synthesis."
                        ),
                        (
                            "Over centuries the drum reinvented itself without losing its hourglass soul: heavy Goryeo ceramic sajanggu chamber pieces yielded to carved wood for outdoor dances, Kim Deok-soo launched Samulnori in 1978 (with female stage drummers reshaping its athletic kinetics), school programs adopted synthetic fiberglass FRP shells and Mylar heads for harsh humidity despite purists preferring Paulownia wood, and digital tools from Umulsai OMR to the piezoelectric iJanggu carried it into contemporary computation."
                        ),
                        (
                            "Modernization reshaped the janggu in stages—from porcelain sajanggu chambers to portable wood, from Samulnori's 1978 seated concert transformation under Kim Deok-soo and energetic modern female stage performers, to weatherproof 21st-century FRP/Mylar drums beside classic wooden ones and lab breakthroughs like KAIST's Umulsai OMR and the sensor-equipped iJanggu."
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
                        "Korean military marches (Daechwita) excluded the janggu in favor of the resonant yonggo barrel drum so single-toned orders carried clearly without dual high-and-low timbre interference obscuring commands.\n\n"
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
                            "Walk into Korea's oldest tombs and temples and you see waisted drums carved centuries before anyone wrote down the word janggu. By lantern light in Goguryeo mural tombs—Anak No. 3, Deokheung-ri from around 408 CE, Susan-ri and Palcheong-ri—painted court players beat waisted drums side by side with five-stringed pipas from Central Asia.\n\n"
                            "Travel south to Baekje in Buyeo and you find a miniature musician cast in high relief playing a waisted drum atop the Great Gilt-Bronze Incense Burner (Geumdong Daehyangno). Later in Unified Silla, the Samguk Sagi chronicles the creation of the royal Eumseongseo music office in 651 CE, while bronze reliefs on the Sangwonsa and 771 CE King Seongdeok bells still show celestial musicians playing the seyogo."
                        ),
                        (
                            "Stone murals, bronze incense burners and ancient temple bells tell the story together across the Three Kingdoms and Silla: fifth-century Goguryeo tombs—Anak No. 3, Deokheung-ri (c. 408 CE), Susan-ri and Palcheong-ri—depict waist drums next to imported pipas; Baekje artisans cast a waisted drummer onto Buyeo's Geumdong Daehyangno bronze incense burner; and Unified Silla recorded the 651 CE Eumseongseo music bureau while embossing seyogo reliefs across the Sangwonsa and 771 CE King Seongdeok bronze bells."
                        ),
                        (
                            "Before paper treatises survived, Korean artisans left three kinds of physical witnesses: painted Goguryeo tomb players (Deokheung-ri c. 408 CE, Anak No. 3, Susan-ri and Palcheong-ri) keeping time beside five-stringed pipas, Baekje's relief drummer on the Geumdong Daehyangno incense burner excavated in Buyeo and Unified Silla's 651 CE Eumseongseo court bureau paired with seyogo musicians cast onto Sangwonsa and King Seongdeok (771 CE) bells."
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
            elif "akhak_gwebeom" in entities or "galgo" in entities:
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
            elif "jeongganbo" in entities:
                all_v = self.repository.get_verified_facts()
                selected_facts = [f for f in all_v if f["id"] in {"F29", "F55", "F63"}]
                reply_text = compose_variation(
                    "rule::chron_jeongganbo",
                    (
                        "In the 15th century (around 1447 AD), King Sejong the Great gave Korean rhythm something astonishingly ahead of its time: Jeongganbo, a spatial 2D grid notation where each square cell (jeonggan) captures exact beat duration alongside dedicated janggu stroke symbols. Read top-to-bottom and right-to-left across gak columns, it preserved living rhythmic timing centuries before modern DAW grids—and today even powers KAIST's Umulsai EBNF grammar.",
                        "Before King Sejong devised Jeongganbo in the 15th century (1447), drummers passed every cadence purely by ear and hand. His 2D grid matrix assigned one jeonggan box per unit of time across vertical gak columns, recording both duration and exact janggu strokes on paper.",
                    ),
                    (
                        "Want to see how Seong Hyeon's 1493 Akhak Gwebeom later codified the drum's hides, or how KAIST formalized Jeongganbo in EBNF?",
                        "Curious how modern software turns those 15th-century Jeongganbo cells into digital EBNF notation?",
                    ),
                    session=session,
                    separator=" ",
                )
            elif "choi_seung_hee" in entities:
                selected_facts = [f for f in all_chronology if f["id"] == "F08"]
                reply_text = compose_variation(
                    "rule::chron_choi",
                    (
                        "During the 1930s, pioneering modern dancer Choi Seung-hee carried the janggu far beyond courtyard festivals and onto international theater stages. Strapping the hourglass drum across her torso, she fused traditional percussion and dynamic choreography so audiences overseas witnessed the janggu as a kinetic solo stage art.",
                        "In the 1930s, trailblazing choreographer Choi Seung-hee transformed janggu dance into a celebrated international stage performance—turning traditional strapped-drum movement into a signature emblem of modern Korean choreography.",
                    ),
                    (
                        "Want to step forward to 1951 when Seoul founded the National Gugak Center, or explore solo Seoljanggu drumming?",
                        "Should we look at how the National Gugak Center or UNESCO later safeguarded these living traditions?",
                    ),
                    session=session,
                    separator=" ",
                )
            elif "ngc_jangagwon" in entities:
                selected_facts = [f for f in all_chronology if f["id"] in {"F09", "F15"}]
                reply_text = compose_variation(
                    "rule::chron_ngc",
                    (
                        "Founded in 1951 in the midst of turbulent modern history, the National Gugak Center in Seoul carried forward the unbroken institutional lineage of Joseon's royal Jangagwon music bureau. Inside its halls, classical court Jeongak and standardized janggu repertoire codified back in the 1493 Akhak Gwebeom stayed alive for new generations.",
                        "When the National Gugak Center opened in 1951, it preserved the direct institutional heritage of the Joseon dynasty's royal Jangagwon—keeping ancestral court janggu techniques and repertoire intact from palace ceremony into modern concert halls.",
                    ),
                    (
                        "Want to contrast that court lineage with UNESCO-recognized Nongak community drumming or Choi Seung-hee's 1930s stage dance?",
                        "Curious how court Jeongak posture compares with rural village folk drumming?",
                    ),
                    session=session,
                    separator=" ",
                )
                session.set_pending_offer({"type": "court_or_folk"})
            elif "met_museum" in entities:
                selected_facts = [f for f in self.repository.get_verified_facts() if f["id"] == "F11"]
                reply_text = compose_variation(
                    "rule::chron_met",
                    (
                        "Far across the ocean in New York, The Metropolitan Museum of Art preserves a 19th-century (1800s) Joseon-era changgo—complete with its hourglass shell, lacing and ceremonial craftsmanship—standing as a tangible bridge between late-Joseon workshops and global museum collections.",
                        "A preserved 19th-century Joseon changgo now rests in The Metropolitan Museum of Art, giving modern researchers and visitors an intact physical witness to how late-Joseon craftsmen proportioned and laced the drum.",
                    ),
                    (
                        "Want to hear how modern museum conservators scan antique janggu shells with X-ray microtomography and photogrammetry?",
                        "Curious about the even older 13th-century Goryeo celadon sajanggu preserved in Seoul's National Museum of Korea?",
                    ),
                    session=session,
                    separator=" ",
                )
            elif "unesco" in entities:
                all_v = self.repository.get_verified_facts() + self.repository.get_disputed_facts()
                selected_facts = [f for f in all_v if f["id"] in {"F07", "F40"}]
                reply_text = compose_variation(
                    "rule::chron_unesco",
                    (
                        "In 2014, UNESCO inscribed Nongak—Korea's community band music, dance and village rituals powered by the janggu—onto the Representative List of the Intangible Cultural Heritage of Humanity. Even today, that official 'nongak' title sparks thoughtful discussion alongside 'pungmul', championed since the 1980s minjung movement to honor its deeper communal and shamanic spirit.",
                        "UNESCO's 2014 inscription of Nongak recognized the janggu-driven community band tradition as Intangible Cultural Heritage of Humanity—bringing global visibility to both its harvest celebrations and the living scholarly conversation between the names 'nongak' and 'pungmul'.",
                    ),
                    (
                        "Want to hear about the lead Seoljanggu player who commands those village bands, or how Nongak differs from court Jeongak?",
                        "Curious how village folk technique compares with seated royal court playing?",
                    ),
                    session=session,
                    separator=" ",
                )
                session.set_pending_offer({"type": "court_or_folk"})
            else:
                selected_facts = all_chronology
                reply_text = compose_variation(
                    "rule::chron_default",
                    (
                        (
                            "Imagine following one hourglass drum through nearly a thousand years of Korean history. Our earliest written glimpse arrives in 1076 AD, when the Goryeosa chronicles first name an official court teacher called the janggu-opsa. Only decades later in 1114 AD, King Yejong receives imported court instruments from Song Dynasty China, setting the classic hourglass proportions—while by the 1200s, Goryeo potters even glaze emerald celadon sajanggu vessels like the treasure preserved today in the National Museum of Korea.\n\n"
                            "During Joseon times, scholars wrote that oral art down: in the 15th century (around 1447 AD), King Sejong devised the Jeongganbo 2D grid notation giving the janggu its own column, and in 1493 AD Seong Hyeon compiled the Akhak Gwebeom to lock in its asymmetric leather hides and tell it cleanly apart from the symmetrical galgo. An 1800s (19th-century) court drum even crossed oceans into The Metropolitan Museum of Art—and in modern memory, Choi Seung-hee carried janggu dance onto global stages in the 1930s, Seoul founded the National Gugak Center in 1951 AD to preserve the old royal Jangagwon lineage, and UNESCO inscribed Nongak community band drumming as World Heritage in 2014 AD."
                        ),
                        (
                            "Open Korea's surviving archives in order and a living human story unfolds from palace halls to global concert stages. It begins inside Goryeo courts with a teacher post—janggu-opsa in the 1076 AD Goryeosa—followed by King Yejong's 1114 AD Song Dynasty instrument import and the 1200s celadon sajanggu drums housed at the National Museum of Korea.\n\n"
                            "Fifteenth-century Joseon masters then gave the drum its grammar and blueprint: King Sejong's 1447 (15th-century) Jeongganbo grid notation gave strokes an exact place on paper, and Seong Hyeon's 1493 AD Akhak Gwebeom formally separated the asymmetric janggu from the symmetrical galgo. Centuries after an 1800s Joseon drum reached The Metropolitan Museum of Art, 1930s dancer Choi Seung-hee choreographed it for international theaters, Seoul's 1951 National Gugak Center carried the royal Jangagwon tradition out of war, and UNESCO celebrated Nongak drumming on its heritage list in 2014 AD."
                        ),
                        (
                            "If you trace the janggu as three passing eras of Korean memory, Goryeo comes first: royal chronicles naming janggu-opsa teachers in 1076 AD (Goryeosa), King Yejong welcoming Song instruments in 1114 AD and ceramic artisans shaping 1200s celadon sajanggu drums now kept at the National Museum of Korea.\n\n"
                            "Joseon scholars took the pen next—King Sejong inventing 15th-century (1447) Jeongganbo grid notation and Seong Hyeon authoring the 1493 AD Akhak Gwebeom to distinguish the drum from the galgo—leaving physical heirs like an 1800s court changgo at The Metropolitan Museum of Art before Choi Seung-hee's 1930s stage choreography, the 1951 National Gugak Center continuing royal Jangagwon heritage and UNESCO's 2014 Nongak recognition brought the drum into modern life."
                        ),
                    ),
                    (
                        "Which chapter of that thousand-year story would you like me to zoom in on next?",
                        "Want to step back into one particular court chronicle, celadon kiln or modern revival?",
                        "Where in that timeline should we linger—Goryeo palaces, Sejong's workshop or 20th-century stages?",
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
                            "Watch where a drummer aims his stick and you can almost tell without looking whether he learned in a royal palace or a farm festival. Strike dead center on the bokpan and the whole membrane blooms with deep fundamental resonance—perfect for outdoor folk volume. Move the thin bamboo yeolchae out toward the rim edge called byeonjuk, and that heavy fundamental suddenly quiets down, leaving a crisp, dry 'tack' favored in serene court Jeongak."
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
                            "Before touching a page of music, every student learns to speak five classic strokes with his hands. Strike both drumheads together on the big downbeat and you hear Deong (덩). Let the left hand carry the low boom alone and it speaks Gung (궁), while a clean tap in the right treble center answers Tta (따). Flick a rapid two-note whip grace ahead of a beat for Gi-deok (기덕), and catch edge skin against wooden hoop for a slicing Kkol or Jjak (짝) rimshot."
                        ),
                        (
                            "Five signature strokes organize janggu phrasing—Deong (덩) striking both heads in unison, Gung (궁) driving left bass, Tta (따) cracking the right center, Gi-deok (기덕) fluttering as a fast treble flam and Kkol / Jjak (짝) snapping sharp against the hoop rim."
                        ),
                        (
                            "Think of traditional phrasing like a five-word spoken language on skin: Deong (덩) unites both heads on major accents, Gung (궁) drops left-side bass, Tta (따) punches crisp treble center strikes, Gi-deok (기덕) spins light grace flams and Kkol / Jjak (짝) cuts bright across the rim."
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
                        "Strike either head and the janggu launches an invisible tug-of-war of waves and trapped air. Because its circular drumheads obey the 2D polar wave equation with wave speed c = sqrt(tau / rho_s) and Bessel functions J_m(k_mn r), tapping near the rim (byeonjuk) suppresses the (0,1) fundamental while lifting asymmetric modes (m >= 1)—and because heavy cowhide slows bass waves below thin horsehide (c_left << c_right), the heads never phase-align and instead bloom with inharmonic overtones.\n\n"
                        "Physicists even bounce non-contact 3D Scanning Laser Doppler Vibrometry (SLDV) beams off vibrating hides to watch (1,1) and (2,1) chaepyeon shapes and spot misaligned joigae wedges. Inside the shell, Transfer Matrix Modeling (TMM, Z = j*omega*rho_0*L_eff/A, [p1; V1] = T_n T_c [p3; V3]) treats the hourglass jorongmok waist as acoustic inertance between chambers—giving chaepyeon fast horizontal Attack/Decay transients beside bukpyeon's omnidirectional prolonged Release."
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
                            "The story of a fine janggu starts high on a rocky mountain slope long before a chisel ever touches wood. Korean Paulownia coreana grows so light that its oven-dry density sits around 260 to 340 kg/m³ with a steady tangential-to-radial (T/R) shrinkage ratio of 1.4 to 2.0—letting village drummers dance with it strapped to their chest without cracking.\n\n"
                            "Look through a microscope inside that wood and you see why it sings: wide 165–289 μm earlywood vessels (next to 55–149 μm latewood pores) are partly plugged by tyloses acting like natural low-pass acoustic filters, while thick tension wood gelatinous fibers (G-fibers reaching up to 65.1% crystallinity, ~6.5 nm width and 19.9–39.3 MPa compressive strength) keep the slim hollowed shell from buckling under heavy wedge tension—and let dendrochronology map growth rings back to specific Joseon rainfall decades."
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
                            "Step into a traditional drum maker's workshop and you smell fire, urushi tree sap and warming hide glue rather than modern factory resin. While synthetic PVA glues damp kinetic vibrations, masters heat animal hide glue or sturgeon bladder isinglass to a careful 60°C (140°F) so it dries crystalline hard at every joint.\n\n"
                            "Next, they glide iron heated past 1000°C over the grain in nakdong scorching and coat it with ottchil urushi lacquer—cross-linking cellulose so moisture stays out and cavity waves bounce cleanly to lift the Q-factor. As artisans hollow the 58–66 cm shell thicker around the waist and thinner toward bearing edges, they tap the wood with ear tuned close, carving out harsh wolf tones while letting floating cord-laced hoops extend each stroke's sustain."
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
                session.set_pending_offer({"type": "hides_comparison"})
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
                session.set_pending_offer({"type": "tuning_or_acoustics"})
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
                session.set_pending_offer({"type": "tuning_or_acoustics"})
            elif "gungpyeon" in entities or "chaepyeon" in entities:
                selected_facts = [f for f in all_construction if f["id"] in {"F02", "F43", "F30"}]
                reply_text = compose_variation(
                    "rule::const_heads",
                    (
                        (
                            "Korean makers built Yin and Yang right into the drum's two leather faces, turning one frame into two opposite voices. On the left side sits the slightly wider gungpyeon (around 36 to 46 cm across), stretched with thick cowhide or deerskin whose higher areal mass density slows wave travel into a warm, grounded bass boom.\n\n"
                            "Look across at the slightly smaller right face—the chaepyeon at roughly 35 to 45 cm—and thin horsehide or doghide waits there instead, tightened to snap back with a biting treble crack."
                        ),
                        (
                            "Traditional janggu skins balance thick bass mass against thin treble snap across opposite sides (36 to 46 cm vs. 35 to 45 cm): on the left (gungpyeon), heavy cowhide or deerskin increases areal mass density for warm low resonance, while on the right (chaepyeon), thin horsehide or doghide projects crisp treble attacks—embodying harmonic Yin-Yang duality."
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
                session.set_pending_offer({"type": "sticks_or_strokes"})
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
                            "In a Pansori performance, there is only one singer, one drummer and an unfolded fan—yet the janggu turns that tiny stage into an entire world, cradling vocal sigimsae ornaments and chuimsae shouts. When the story settles into heartbreak, the drummer stretches out into slow 24-beat Jinyangjo to give grief space to breathe; when heroes clash in wartime scenes like the famous naval battle in Jeokbyeokga (Song of the Red Cliffs), his sticks surge straight into fast 12/8 Jajinmori to race along with the fight."
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
                            "Even the name of Korea's village drumming tradition carries a story of disagreement between old books and living protesters. Institutional records—stretching from scholar An Yu-sin's 1657 writing to South Korea's 1966 Cultural Asset No. 11 and UNESCO's 2014 listing—officially call it 'nongak' (farmers' music).\n\n"
                            "Yet during the 1980s minjung cultural movement, activists and ethnomusicologists pushed back and rallied around 'pungmul' instead, arguing the colonial farming label hid its deeper shamanic rituals and communal spirit. Out in either procession, the lead seoljanggu player still steps to the front, spinning his sangmo hat ribbon while cueing tempo changes and solo runs."
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
            elif "jongmyo" in entities:
                selected_facts = [f for f in self.repository.get_verified_facts() if f["id"] in {"F04", "F06"}]
                reply_text = compose_variation(
                    "rule::cult_jongmyo",
                    (
                        "Inside royal ancestral shrines during Jongmyo Jeryeak, the janggu steps out of festival exuberance and into stately Neo-Confucian restraint. Musicians sit cross-legged on woven mats, tapping the rim edge gently with the bamboo yeolchae while the bare left palm cushions solemn cowhide bass tones that anchor the ceremonial orchestra.",
                        "For Jongmyo Jeryeak royal ancestral rites, court Jeongak drummers perform seated with deliberate poise—pairing soft bare-palm bass strokes on the left head with crisp rim taps on the right to honor ancestral formality.",
                    ),
                    (
                        "Want to contrast that solemn ancestral rite with lively countryside Nongak festivals?",
                        "Curious how the National Gugak Center carries that royal court repertoire forward today?",
                    ),
                    session=session,
                    separator=" ",
                )
                session.set_pending_offer({"type": "court_or_folk", "court_done": True})
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
