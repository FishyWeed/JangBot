"""Conversational follow-up and pending offer resolution."""

from typing import Any, Dict, List, Optional, Tuple
from src.memory.session import SessionMemory
from src.dialogue.variations import compose_variation, pick_variation


class FollowUpHandler:
    """Resolve user replies to prior bot offers and questions."""

    AFFIRMATIONS = {
        "yes", "yeah", "yep", "yup", "sure", "ok", "okay", "please",
        "go ahead", "tell me", "both", "tell me both", "why not", "definitely",
        "of course", "y", "yea", "yes please", "sure thing", "sounds good",
        "tell me more", "explain", "i would like that", "yes i would", "sure do"
    }

    NEGATIONS = {
        "no", "nope", "nah", "not really", "neither", "none", "pass",
        "cancel", "stop", "something else", "no thanks", "no thank you"
    }

    @classmethod
    def can_handle(cls, text: str, session: SessionMemory) -> bool:
        """Check if user text is an answer to a pending bot offer."""
        if not session.pending_offer:
            return False

        clean = text.lower().strip()

        # Explicit source explanation or proof queries should never be handled as offer responses
        if any(w in clean for w in ["source", "sources", "cite", "citation", "citations", "prove", "evidence"]):
            return False
        if clean.startswith("how do you know") or clean.startswith("where did you"):
            return False

        if clean in cls.AFFIRMATIONS or clean in cls.NEGATIONS:
            return True

        offer_type = session.pending_offer.get("type")

        # Conversational continuation shorthands
        words = set(clean.split())
        continuation_words = {"tell", "explain", "more", "details", "elaborate", "sure", "yes", "please", "go ahead"}
        if len(words) <= 5 and (words & continuation_words):
            if offer_type in {
                "court_or_folk", "court_vs_folk_technique", "sticks_or_strokes",
                "tuning_or_acoustics", "beginner_rhythms", "chuimsae_offer",
                "tuning_or_construction", "silla_evolution", "general_followup"
            }:
                return True

        if offer_type == "court_or_folk":
            return any(w in clean for w in ["court", "royal", "folk", "village", "festival", "festivals", "first", "second", "1", "2", "both"])
        elif offer_type == "court_vs_folk_technique":
            return any(w in clean for w in ["technique", "techniques", "playing", "play", "court", "folk", "differ", "difference", "how", "first", "second", "1", "2", "both"])
        elif offer_type == "sticks_or_strokes":
            return any(w in clean for w in ["stick", "sticks", "stroke", "strokes", "mallet", "whip", "yeolchae", "gungchae", "sound", "sounds", "first", "second", "1", "2", "both"])
        elif offer_type == "tuning_or_acoustics":
            return any(w in clean for w in ["tuning", "tune", "cords", "wedge", "joimjul", "joigae", "acoustic", "acoustics", "science", "choke", "jorongmok", "first", "second", "1", "2", "both"])
        elif offer_type == "beginner_rhythms":
            return any(w in clean for w in ["rhythm", "rhythms", "jangdan", "beat", "beats", "jungmori", "hwimori", "gutgeori", "first", "second", "1", "2", "both"])
        elif offer_type == "chuimsae_offer":
            return any(w in clean for w in ["shout", "shouts", "chuimsae", "eolssigu", "jota", "vocal", "audience", "rhythm", "both"])
        elif offer_type == "tuning_or_construction":
            return any(w in clean for w in ["tuning", "tune", "cord", "cords", "wedge", "wedges", "construction", "wood", "paulownia", "body", "both"])
        elif offer_type == "general_followup":
            return True

        return False

    @classmethod
    def resolve(cls, text: str, session: SessionMemory) -> Tuple[str, List[str]]:
        """Resolve pending offer into varied, non-repeating conversational responses and fact IDs."""
        offer = session.pending_offer or {}
        offer_type = offer.get("type", "general_followup")
        clean = text.lower().strip()

        # Handle negation
        if clean in cls.NEGATIONS:
            session.clear_pending_offer()
            reply = compose_variation(
                "followup::negation",
                (
                    "No problem at all. Whenever you feel like shifting gears, we can look at the drum's Paulownia wood build, two-hand coordination or jangdan cycles.",
                    "Fair enough! Feel free to steer us toward its craftsmanship, stroke techniques or rhythmic patterns instead.",
                    "Understood—we can leave that thread there and move to janggu construction, acoustics or playing posture.",
                ),
                (
                    "What direction sounds best next?",
                    "Where would you like to take the conversation from here?",
                    "Which topic would you prefer to ask about?",
                    "Just let me know what angle of the janggu catches your interest.",
                ),
                session=session,
            )
            return reply, session.last_fact_ids

        # 1. Handle court_or_folk offer
        if offer_type == "court_or_folk":
            session.clear_pending_offer()
            wants_court = any(w in clean for w in ["court", "royal", "first", "1"])
            wants_folk = any(w in clean for w in ["folk", "village", "festival", "festivals", "second", "2"])

            if wants_court and not wants_folk:
                reply = compose_variation(
                    "followup::court_only",
                    (
                        "In royal court music (Jeongak), musicians sat cross-legged on the floor and played the janggu with measured restraint. It anchored state banquets and ancestral rites such as Jongmyo Jeryeak, keeping a steady pulse aligned with Neo-Confucian decorum.",
                        "Court Jeongak performances placed the janggu in a seated role, supporting ancestral rituals like Jongmyo Jeryeak and palace banquets. Rather than heavy syncopation, drummers maintained calm, dignified pacing suited to formal court ceremony.",
                        "Inside the palace, Jeongak drummers performed seated on woven mats, guiding court banquets and royal ancestral rites (Jongmyo Jeryeak). Avoiding showy syncopation kept the rhythm poised and restrained.",
                    ),
                    (
                        "Would you like to compare that with its rural folk role next?",
                        "Want to contrast royal court etiquette with how village folk bands played it?",
                        "Should we explore the lively folk tradition next?",
                        "Curious how village festivals used the exact same drum differently?",
                    ),
                    session=session,
                    separator="\n\n",
                )
                session.set_pending_offer({"type": "court_or_folk", "court_done": True})
                return reply, ["F04", "F06"]

            if wants_folk and not wants_court:
                reply = compose_variation(
                    "followup::folk_only",
                    (
                        "In countryside farming villages, the janggu powered Nongak (farmers' band music). Wearing the drum on a shoulder strap, players marched, spun and danced while driving loud, energetic beats for harvests, village blessings and ritual protection.",
                        "Outside the palace walls, Nongak and Pungmul musicians slung the janggu across their torsos with a sash. Moving through village festivals and fields, drummers combined acrobatic leaps with booming rhythms to accompany farmers' labor and harvest celebrations.",
                        "Rural farmers' bands (Nongak) turned the janggu into a mobile centerpiece—drummers strapped it across the chest to march, dance and project rhythmic energy across harvests and communal village rites.",
                    ),
                    (
                        "Want to compare that folk style with the seated royal court tradition, or inspect the jangdan patterns they played?",
                        "Would you care to hear about formal court music next, or dive into village rhythmic cycles?",
                        "Should we look at royal Jeongak accompaniment next, or jump straight into those folk rhythms?",
                        "Which sounds more interesting next—the seated court tradition or the rhythm patterns?",
                    ),
                    session=session,
                    separator="\n\n",
                )
                session.set_pending_offer({"type": "court_or_folk", "folk_done": True})
                return reply, ["F05", "F07"]

            # User said "yes", "both", or affirmed without choosing one
            reply = compose_variation(
                "followup::court_and_folk",
                (
                    (
                        "Royal courts and farming villages put the exact same hourglass drum to sharply contrasting uses.\n\n"
                        "At court (Jeongak), drummers sat cross-legged to maintain a dignified, steady pulse for state banquets and ancestral rites such as Jongmyo Jeryeak.\n\n"
                        "In village festivals (Nongak and Pungmul), players slung the instrument on a shoulder strap, leaping and marching across fields with syncopated beats to rally farm work and harvest celebrations."
                    ),
                    (
                        "Depending on the social setting, the janggu led two very different musical lives.\n\n"
                        "In aristocratic court ensembles (Jeongak), seated performers anchored banquets and ancestral ceremonies like Jongmyo Jeryeak with restrained, solemn timing.\n\n"
                        "Out in rural communities (Nongak and Pungmul), drummers wore the drum upright while dancing and parading, firing off loud, syncopated rhythms for agricultural work and harvest festivals."
                    ),
                    (
                        "History gave the janggu a seated life inside the palace and an athletic life in the countryside.\n\n"
                        "During Jeongak court ceremonies and royal rituals like Jongmyo Jeryeak, cross-legged musicians supplied measured, ceremonial poise.\n\n"
                        "Meanwhile, in Nongak and Pungmul village traditions, drummers strapped the drum across their shoulders to march, spin and drive celebratory harvest rhythms."
                    ),
                ),
                (
                    "Should we look at how the actual playing technique separates court music from folk music?",
                    "Would you care to see how hand technique and posture differ between those two styles?",
                    "Want to compare the playing technique used in court Jeongak versus village folk bands?",
                    "Curious how the drummer's hands and sticks change between court and village settings?",
                ),
                session=session,
                separator="\n\n",
            )
            session.set_pending_offer({"type": "court_vs_folk_technique"})
            return reply, ["F04", "F05", "F06", "F07"]

        # 2. Handle court_vs_folk_technique offer
        if offer_type == "court_vs_folk_technique":
            session.clear_pending_offer()
            reply = compose_variation(
                "followup::court_vs_folk_technique",
                (
                    (
                        "Posture, left-hand touch and dynamic projection set the two techniques apart.\n\n"
                        "In court Jeongak, performers sit cross-legged (jwa-sik) on a mat: the right hand taps the slender bamboo yeolchae lightly, while the left bare palm or fingertips strike thick cowhide for a subdued pulse matching palace etiquette.\n\n"
                        "In folk Nongak and Pungmul, players perform standing (ip-sik) with a sash strap: the right hand whips the flexible yeolchae while the left swings the hooked gungchae mallet for booming bass projection outdoors."
                    ),
                    (
                        "You can spot the difference between a court player and a folk drummer from their stance and left hand alone.\n\n"
                        "Seated cross-legged in Jeongak (jwa-sik), the left hand uses bare fingers or palm instead of a mallet, balancing gentle yeolchae taps on the right head for Confucian ceremony.\n\n"
                        "Standing in folk festivals (ip-sik), Nongak and Pungmul players grip the root-capped gungchae mallet in the left hand while whipping the right-side yeolchae across open outdoor crowds."
                    ),
                    (
                        "Court refinement and outdoor folk energy call for opposite hand mechanics.\n\n"
                        "During seated Jeongak performance (jwa-sik), only the right hand holds the bamboo yeolchae while the bare left palm cushions soft cowhide bass tones.\n\n"
                        "When standing or leaping in folk Nongak and Pungmul (ip-sik), both hands wield sticks—whipping the treble yeolchae on the right and swinging the gungchae mallet on the left."
                    ),
                ),
                (
                    "Want a closer look at the yeolchae and gungchae sticks themselves, or the five core strokes they produce?",
                    "Should we inspect the construction of the two sticks next, or go over the five foundational strokes?",
                    "Where next—would you like details on the yeolchae and gungchae mallets, or the five strokes drummers master?",
                    "Curious how those two sticks are shaped, or how the five stroke sounds work?",
                ),
                session=session,
                separator="\n\n",
            )
            session.set_pending_offer({"type": "sticks_or_strokes"})
            return reply, ["F04", "F05", "F19", "F20"]

        # 3. Handle sticks_or_strokes offer
        if offer_type == "sticks_or_strokes":
            session.clear_pending_offer()
            wants_strokes = any(w in clean for w in ["stroke", "strokes", "second", "2"])
            wants_sticks = any(w in clean for w in ["stick", "sticks", "mallet", "first", "1", "yeolchae", "gungchae"])

            if wants_strokes and not wants_sticks:
                reply = compose_variation(
                    "followup::strokes",
                    (
                        (
                            "Janggu notation and pedagogy revolve around five core strokes:\n"
                            "- Deong (덩): Both heads struck together to mark the primary downbeat.\n"
                            "- Gung (궁): Bass strike on the left cowhide head.\n"
                            "- Tta (따): Crisp center hit on the right treble head.\n"
                            "- Gi-deok (기덕): Rapid grace-note flam with the whip stick.\n"
                            "- Kkol / Jjak (짝): Piercing slap against the rim and wooden hoop."
                        ),
                        (
                            "Drummers build every rhythmic pattern out of five signature strokes:\n"
                            "- Deong (덩): Simultaneous strike on bass and treble heads.\n"
                            "- Gung (궁): Deep solo hit on the left membrane.\n"
                            "- Tta (따): Sharp center tap on the right membrane.\n"
                            "- Gi-deok (기덕): Quick double-tap flam on the treble side.\n"
                            "- Kkol / Jjak (짝): High rimshot across edge skin and wood."
                        ),
                        (
                            "Everything in a janggu performance maps back to five named strikes—Deong (덩) hitting both heads in unison, Gung (궁) anchoring left-side bass, Tta (따) snapping the right center, Gi-deok (기덕) adding a quick treble flam and Kkol / Jjak (짝) cutting through as a sharp rimshot."
                        ),
                    ),
                    (
                        "Want to see how these five strokes weave into traditional jangdan rhythms?",
                        "Should we look next at how drummers assemble these strikes into rhythmic cycles?",
                        "Curious which beginner jangdan pattern uses these strokes first?",
                        "Where to next—would you like to map these strokes onto traditional rhythm cycles?",
                    ),
                    session=session,
                    separator="\n\n",
                )
                session.set_pending_offer({"type": "beginner_rhythms"})
                return reply, ["F20"]

            reply = compose_variation(
                "followup::sticks",
                (
                    (
                        "Each hand uses an implement shaped for its membrane:\n"
                        "- Right hand (yeolchae): A thin, springy bamboo strip engineered to whip sharp treble snaps off thin horsehide.\n"
                        "- Left hand (gungchae): Carved from a boiled bamboo root tipped with dense hardwood or antler to pull warm bass thuds from thick cowhide."
                    ),
                    (
                        "The two sticks match the left/right asymmetry of the drumheads.\n"
                        "Your right hand flexes the lightweight bamboo yeolchae for crisp stinging cracks on treble skin, while your left grips the gungchae mallet—weighted at its bamboo-root tip with hardwood or horn for full bass resonance."
                    ),
                    (
                        "Instead of matched drumsticks, the yeolchae and gungchae work as contrasting partners: the slender bamboo yeolchae whips bright high frequencies from the right head, while the weighted root-headed gungchae mallet drives low resonance from the left."
                    ),
                ),
                (
                    "Want to go over the five named strokes these sticks produce next?",
                    "Curious how the five core strokes sound when you combine these implements?",
                    "Should we cover the five foundational strokes (Deong through Jjak) next?",
                    "Would you like to hear how drummers articulate the five basic strokes with them?",
                ),
                session=session,
                separator="\n\n",
            )
            session.set_pending_offer({"type": "sticks_or_strokes", "sticks_done": True})
            return reply, ["F04", "F05", "F19"]

        # 4. Handle tuning_or_acoustics offer
        if offer_type == "tuning_or_acoustics":
            session.clear_pending_offer()
            wants_acoustics = any(w in clean for w in ["acoustic", "acoustics", "science", "choke", "second", "2"])
            if wants_acoustics:
                reply = compose_variation(
                    "followup::acoustics",
                    (
                        "The narrowed central neck (jorongmok) acts as a mechanical acoustic choke: low-frequency air pressure couples smoothly between the two chambers to sustain bass bloom, while high-frequency treble cracks stay crisp instead of being damped by the heavier head. On top of that, circular hides vibrate according to Bessel function zeros, yielding rich inharmonic overtones rather than integer Western harmonics.",
                        "Inside the hourglass shell, the tight jorongmok waist prevents the thick bass skin from muting the thin treble skin while still linking low-end cavity resonance. Because tensioned circular membranes follow Bessel-mode physics, their overtone spectrum stays inharmonic—giving the janggu its warm, percussive bite.",
                        "Two physical effects define the janggu's sound: first, the jorongmok waist functions as an acoustic choke coupling low frequencies while isolating fast treble transients; second, Bessel-function membrane vibrations produce inharmonic overtones rather than fixed pitch harmonics.",
                    ),
                    (
                        "Want to look at how the cords and leather wedges tune those membrane pitches?",
                        "Should we check out the mechanical joimjul cord and joigae wedge tuning system next?",
                        "Curious how sliding wedges adjust pitch across both heads?",
                        "Would you like to move on to how drummers tighten and tune the skins?",
                    ),
                    session=session,
                    separator=" ",
                )
                session.set_pending_offer({"type": "tuning_or_acoustics", "acoustics_done": True})
                return reply, ["F17", "F30"]

            reply = compose_variation(
                "followup::tuning",
                (
                    "Continuous V-shaped tension cords (joimjul) zig-zag between both drumhead hoops, gripped by movable leather or wood wedges called joigae. Pushing the joigae rightward pinches the V-strands together to tighten head tension and raise pitch; nudging them left releases tension and lowers pitch.",
                    "Tuning happens mechanically without screws or lugs: sliding leather joigae clamps along the V-laced joimjul cords pulls the laces closer to sharpen treble pitch (sliding right) or eases slack to deepen tone (sliding left).",
                    "Both membranes connect via continuous V-shaped joimjul lacing fitted with sliding joigae wedges. Shifting those wedges toward the treble side squeezes the cords to pitch the drum higher, while sliding them back left softens membrane tension.",
                ),
                (
                    "Want to compare the two contrasting animal hides those cords hold together?",
                    "Should we unpack why cowhide and horsehide are paired on opposite heads next?",
                    "Curious how the left cowhide head and right horsehide head differ acoustically?",
                    "Would you like to examine the two asymmetric drumhead skins next?",
                ),
                session=session,
                separator=" ",
            )
            session.set_pending_offer({"type": "tuning_or_acoustics", "tuning_done": True})
            return reply, ["F02", "F18"]

        # 5. Handle beginner_rhythms offer
        if offer_type == "beginner_rhythms":
            session.clear_pending_offer()
            reply = compose_variation(
                "followup::beginner_rhythms",
                (
                    "Most newcomers begin on Jungmori, a calm 12-beat walking pulse that leaves room to land Deong cleanly on beat 1 and balance Gung and Tta between beats. Once muscle memory settles, students progress to Gutgeori's lilting 12-beat swing and eventually the rapid 4-beat sprint of Hwimori.",
                    "Jungmori is the standard starting point: its relaxed 12-beat walking tempo lets you practice coordinating simultaneous Deong downbeats with alternating Gung and Tta answers. From there, players step up into Gutgeori's buoyant swing before tackling Hwimori's relentless speed.",
                    "Instructors usually introduce the 12-beat Jungmori pattern first so learners can keep right and left hands independent without rushing. Later stages introduce Gutgeori's swaying triple feel and fast climax rhythms like Hwimori.",
                ),
                (
                    "Want to know what those lively vocal shouts (chuimsae) drummers trade during rhythms mean?",
                    "Should we cover the traditional vocal cries called chuimsae that animate these cycles?",
                    "Curious how vocal shouts (chuimsae) interact with a rhythm section live on stage?",
                    "Would you like to hear about chuimsae cheers next?",
                ),
                session=session,
                separator=" ",
            )
            session.set_pending_offer({"type": "chuimsae_offer"})
            return reply, ["F21", "F22", "F25", "F28"]

        # 6. Handle chuimsae_offer
        if offer_type == "chuimsae_offer":
            session.clear_pending_offer()
            reply = compose_variation(
                "followup::chuimsae",
                (
                    "Chuimsae are live vocal interjections—like 'Eolssigu!' (Right on!) and 'Jota!' (Wonderful!)—exchanged by drummers, singers and listeners mid-piece. Rather than distracting from the beat, they steer tempo surges and pull audience and performer into a single loop.",
                    "In Korean traditional performance, chuimsae shouts bridge player and crowd. Timed cries such as 'Eolssigu!' or 'Jota!' punctually reward expressive phrasing, push dynamic energy higher and cue shifts across jangdan passages.",
                    "Drummers and audiences punctuate performances with spontaneous chuimsae calls—phrases like 'Eolssigu!' and 'Jota!'—which validate tight rhythmic timing, elevate momentum and signal pacing transitions.",
                ),
                (
                    "From here we could check out the hollowed Paulownia wood shell or the mechanical tuning wedges—which sounds good?",
                    "Want to look under the hood at the Paulownia resonator body or the joigae tuning cords next?",
                    "Should we turn next to the wooden ullimtong craftsmanship or how the tension wedges tune it?",
                    "Which side of craftsmanship catches your eye next: the Paulownia shell or the tuning hardware?",
                ),
                session=session,
                separator=" ",
            )
            session.set_pending_offer({"type": "tuning_or_construction"})
            return reply, ["F28"]

        # 7. Handle tuning_or_construction offer
        if offer_type == "tuning_or_construction":
            session.clear_pending_offer()
            wants_tuning = any(w in clean for w in ["tuning", "tune", "cord", "cords", "wedge", "wedges"])
            if wants_tuning:
                reply = compose_variation(
                    "followup::tuning_construction_tune",
                    (
                        "Sliding joigae wedges sit directly on the V-laced joimjul tension cords connecting both drumheads. Nudging wedges right pinches the cords tighter to elevate pitch, while shifting them left releases tension.",
                        "Rather than turning metal tension rods, janggu players slide joigae wedges along V-shaped joimjul ropes—rightward to sharpen tension and leftward to loosen pitch.",
                        "Tension is tuned mechanically by joigae wedges riding the V-shaped joimjul cords: pull toward the treble side to raise pitch or slide back left to drop it.",
                    ),
                    (
                        "Want to look at how artisans carve the Paulownia wood body itself?",
                        "Should we explore how the Paulownia ullimtong shell is cured and scorched?",
                        "Curious why instrument makers scorch the inside of the Paulownia wood chamber?",
                    ),
                    session=session,
                    separator=" ",
                )
                return reply, ["F18"]

            reply = compose_variation(
                "followup::tuning_construction_wood",
                (
                    "Instrument makers hollow the resonator body (ullimtong) from a single block of Paulownia coreana timber—favoring 30-plus-year trees from harsh mountain ridges—then cure it two to three years and scorch the interior hollow with fire to seal pores against moisture.",
                    "Instead of bent staves, the ullimtong shell is lathed out of solid Paulownia wood seasoned for two to three years. Artisans flame-scorch the inner wall afterward to toughen the grain and resist humidity changes.",
                    "A single trunk of aged Paulownia wood forms the entire ullimtong resonator. After two to three years of natural curing, craftsmen apply a fire-scorched interior finish so moisture swings stay out of the timber.",
                ),
                (
                    "Curious how the tuning cords anchor both skin heads onto this wooden body?",
                    "Would you like to hear how V-shaped cords lace both drumheads over this shell?",
                    "Want to inspect the joimjul cord and wedge mechanism next?",
                ),
                session=session,
                separator=" ",
            )
            return reply, ["F16"]

        # 8. Handle slow_or_fast_rhythms offer
        if offer_type == "slow_or_fast_rhythms":
            session.clear_pending_offer()
            wants_fast = any(w in clean for w in ["fast", "festival", "hwimori", "gutgeori", "second", "2"])
            if wants_fast:
                reply = compose_variation(
                    "followup::fast_rhythms",
                    (
                        "Hwimori compresses energy into a blazing 4-beat festival pattern where rapid, syncopated strikes accelerate until the peak climax. By contrast, Gutgeori unfolds across an infectious 12-beat lilting swing tailor-made for social dance.",
                        "If you love fast folk drumming, Hwimori delivers an urgent 4-beat gallop that pushes tempo relentlessly to the finish line, whereas Gutgeori gives you a groovy 12-beat swing common across village dances.",
                        "On the lively end of the repertoire, 4-beat Hwimori drives furious climactic rolls, while 12-beat Gutgeori brings that buoyant triple-meter bounce audiences associate with folk dance.",
                    ),
                    (
                        "Want to compare those festival speeds with the slow court-style Jinyangjo cycle?",
                        "Should we look at the meditative 24-beat Jinyangjo pattern next?",
                        "Curious how slow, expansive rhythms like Jinyangjo pace court or tragic music?",
                    ),
                    session=session,
                    separator=" ",
                )
                return reply, ["F25", "F26"]

            reply = compose_variation(
                "followup::slow_rhythms",
                (
                    "At the slowest end stands Jinyangjo, an expansive 24-beat cycle breathing at a broad, solemn pace. In Pansori vocal drama, singers turn to Jinyangjo to carry grief, longing and weighty reflection.",
                    "Jinyangjo stretches across 24 slow, unhurried beats, giving instrumentalists and Pansori narrators spacious room to shape deep sorrow and noble gravity.",
                    "Spanning 24 broad beats per measure, Jinyangjo sets the calmest, heaviest atmosphere in traditional repertory—widely reserved for tragic scenes and dignified court or Sanjo passages.",
                ),
                (
                    "Want to flip over to high-speed climax patterns like Hwimori next?",
                    "Should we check out the faster festival rhythms that build kinetic excitement?",
                    "Ready to explore how faster rhythms accelerate energy after Jinyangjo?",
                ),
                session=session,
                separator=" ",
            )
            return reply, ["F21"]

        # 9. Handle silla_evolution offer
        if offer_type == "silla_evolution":
            session.clear_pending_offer()
            reply = compose_variation(
                "followup::silla_evolution",
                (
                    (
                        "Long before Goryeo texts appear, waisted hourglass drums arrived via Silk Road exchange from the Indian idakka, establishing themselves in the Silla era (57 BC - 935 AD) as the compact yogo waist drum.\n\n"
                        "Centuries later in 1114 AD, Goryeo King Yejong imported Song Dynasty court instruments, expanding and standardizing the hourglass design that developed into today's janggu."
                    ),
                    (
                        "During Silla times (57 BC - 935 AD), Silk Road cultural trade carried the Indian idakka ancestor eastward into Korea as the smaller yogo waist drum.\n\n"
                        "In 1114 AD, King Yejong of Goryeo formally adopted Song Chinese ceremonial instruments at court, cementing the larger hourglass shape we see today."
                    ),
                    (
                        "Trace the lineage back past Goryeo and you reach the Silla-era yogo waist drum (57 BC - 935 AD), derived from the ancient Indian idakka moving along Silk Road routes.\n\n"
                        "Then King Yejong's 1114 AD import of Song Dynasty court instruments codified the full hourglass proportions of the modern instrument."
                    ),
                ),
                (
                    "Want to explore how that standardized drum served royal court music versus rural village festivals?",
                    "Should we look next at its double life inside court banquets and countryside festivals?",
                    "Curious how royal court usage differed from village folk festivals once it was standardized?",
                ),
                session=session,
                separator="\n\n",
            )
            session.set_pending_offer({"type": "court_or_folk"})
            return reply, ["F12", "F13"]

        # Default fallback for affirmative general follow-up
        session.clear_pending_offer()
        reply = compose_variation(
            "followup::general",
            (
                "Let's keep going—we can inspect how the Paulownia ullimtong body is crafted, break down the five core strokes or compare the jangdan rhythmic cycles.",
                "Happy to dig deeper: we can turn to the wood carving and lacing design, map out the five stroke types or explore festival versus court rhythms.",
                "There is plenty more to unpack—material craftsmanship, left-and-right stroke coordination or the seven jangdan time cycles.",
            ),
            (
                "Which one sounds most useful right now?",
                "What would you like to focus on next?",
                "Where should we go from here?",
                "Pick whichever direction catches your interest.",
            ),
            session=session,
            separator=" ",
        )
        return reply, session.last_fact_ids
