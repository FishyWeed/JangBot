# Janggu Expert System Chatbot: Project Compendium

Nov 9, 2026 · @Benjamin

This compendium gathers every decision, finding and design so far for the expert-system chatbot assignment. The chosen drum is the **janggu**, the Korean hourglass drum. The chatbot will answer only from human-verified facts stored in its own knowledge base.

## 1. Project brief and rules

The assignment is an **expert-system chatbot** about one traditional drum that is played with sticks. It must cover the drum's origins, chronology, details, history and evolution.

**Chatbot rules (as set at the start)**

1. It cannot hallucinate or give untrue facts.
2. It only answers questions about the chosen drum.
3. It is conversational. It opens with "Hi, I'm {name}. How are you?"
4. It has its own database of drum information and does not pull from the web while running.
5. A separate tool classifies, identifies and filters factual information before it enters that database.

**How the rules are enforced:** a rule-based expert system instead of an AI language model, and a read-only knowledge base of human-verified facts. A fallback reply, "I don't have verified information on that yet", is used whenever the bot is unsure (see section 5).

## 2. Drum decision

The **janggu** was chosen on 6 November 2026. It best met the final brief: "great history and details, and significance to its culture and country's history."

**Definition of traditional (yours):** not modern unless it has a clear path of evolution, and usually cultural.

**Already taken by classmates:** rebana ubi, shigu (lion dance drum), taiko, 24 Festive Drums, gendang beleq, Arakan drum, jian gu, the Iranian "timpani" and the bodhrán.

**Every candidate considered**

| Drum | Region | Verdict |
| --- | --- | --- |
| **Janggu** | Korea | **Chosen.** Royal court records with exact years from 1076. Central to court and folk music. Low to medium chance a classmate picks it too. |
| Đông Sơn bronze drum | Vietnam | Runner-up. About 2,500 years old and a national treasure, but metal, partly mallet-played, and thin on playing details. |
| Davul | Turkey, Balkans | Strong. Ottoman mehter (military band) history and an ancestor of the bass drum. |
| Lambeg drum | Northern Ireland | Strong on history, but its significance belongs to one community and is politically contested. |
| Sámi drum | Northern Scandinavia | Strong history, but played with one hammer, not sticks. |
| Steelpan | Trinidad and Tobago | Every step of its evolution is dated, but it is young and a metal idiophone (not a skin drum). |
| Dhak | Bengal | Good academic source, but its origin is only dated as "medieval". |
| Atumpan | Ghana | Good museum sources, but little dated history before the 1800s. |
| Chenda | Kerala | Rich culture, but few dates. |
| Dhol | Punjab | Still open. Medium chance a classmate picks it too. |
| Snare / Basel drum | Switzerland | Borderline on culture unless scoped to the Basel drum. |
| Sabar | Senegal | Dropped: played with one hand and one stick, and few dates. |
| Naqqāreh / nagara | Iran, Turkey | Dropped: too close to a classmate's Iranian "timpani". |
| Bodhrán, taiko, 24 Festive Drums | — | Taken by classmates. The 24 Festive Drums (created 1988) also fail your definition. |

The chance of a classmate picking the same drum is my own estimate. It assumes most of the class leans toward Malaysian and Chinese drums.

## 3. The janggu: what we know so far

Four dated facts already meet the verification rule. Most of the early court-record dates still rest on Wikipedia, and need a Tier 1 source before the bot can use them.

**Details**

- An hourglass-shaped, two-headed drum about 66 cm long ([Britannica](https://www.britannica.com/art/changgo)). It has a wooden body, and skin heads on metal hoops tensioned by ropes ([National Gugak Center](https://artsandculture.google.com/asset/janggu/GwGwVtttOzjekQ)).
- The two heads differ. The left head (*gungpyeon*) is thick hide and gives low tones. The right head (*chaepyeon*) is lighter and gives high tones. The narrow middle tube (*jorongmok*) shapes the sound ([Wikipedia](https://en.wikipedia.org/wiki/Janggu)).
- **Playing depends on the music.** Court and classical music uses one bamboo stick (*yeolchae*) and the bare hand. Folk music and janggu dance use two sticks: the *yeolchae* and the round-headed *gungchae* ([National Gugak Center](https://artsandculture.google.com/asset/janggu/GwGwVtttOzjekQ); [The Met](https://www.metmuseum.org/art/collection/search/503797)).

**Origin:** Korea. It may have evolved from the smaller *yogo* (waist drum), which is thought to come from the Indian *idakka* during the Silla period. This currently rests on Wikipedia only.

**Significance:** The Met calls it "the most representative drum in traditional Korean music", used in nearly all types of it. It appears in court music, folk music, shaman ritual ([National Museums Scotland](https://www.nms.ac.uk/explore-our-collections/collection-search-results/jeongak-jango/645954)) and dance. *Nongak*, the village band tradition it drives, was added to UNESCO's Representative List in 2014.

**Chronology**

Status follows the verification rule: **Ready** means a Tier 1 source supports it; **Pending** means it still rests on Wikipedia.

| When | Event | Source | Status |
| --- | --- | --- | --- |
| 2014 | Nongak inscribed on UNESCO's Representative List | [UNESCO](https://ich.unesco.org/en/RL/nongak-community-band-music-dance-and-rituals-in-the-republic-of-korea-00717) | Ready |
| 1993 | Kim Duk-soo founds the Hanullim samul nori orchestra | [Wikipedia](https://en.wikipedia.org/wiki/Kim_Duk-soo) | Pending |
| 22 Feb 1978 | First samul nori performance in Seoul, with Kim Duk-soo on janggu | [Wikipedia](https://en.wikipedia.org/wiki/Samul_nori) | Pending |
| 1930s | Choi Seung-hee turns the janggu dance into a stage dance | [Encyclopedia of Korean Culture](https://encykorea.aks.ac.kr/Article/E0048300) | Ready |
| 1800s | The Met's changgo is made; it is acquired in 1889 | [The Met](https://www.metmuseum.org/art/collection/search/500723) | Ready |
| 1451 | The *Goryeo-sa* (History of Goryeo) is compiled, recording the court events below | [Wikipedia](https://en.wikipedia.org/wiki/Janggu) | Pending |
| c. 1200s | A celadon *sajanggu* (ceramic-bodied janggu), now in the National Museum of Korea | [Encyclopedia of Korean Culture](https://encykorea.aks.ac.kr/Article/E0072587) | Ready |
| 1114 | Song emperor Huizong sends 20 janggu to the Goryeo court | [Wikipedia](https://en.wikipedia.org/wiki/Janggu) | Pending |
| 1076 | The title *janggu-opsa* (janggu player or teacher) is recorded | [Wikipedia](https://en.wikipedia.org/wiki/Janggu) | Pending |
| 1047–1084 | King Munjong's reign: the oldest written records of an hourglass drum | [Wikipedia](https://en.wikipedia.org/wiki/Janggu) | Pending |
| 682 | *Yogo* shown on bronze relics at Gameunsa temple (Unified Silla) | [Wikipedia](https://en.wikipedia.org/wiki/Janggu) | Pending |
| 4th–5th c. | Hourglass drums shown in Goguryeo tomb murals | [Wikipedia](https://en.wikipedia.org/wiki/Janggu) | Pending |

**Gaps to close:** the *Goryeo-sa* entries (1076, 1114), a source describing the Goguryeo murals, the Encyclopedia of Korean Culture's main janggu entry, and the National Gugak Center's dictionary entry.

## 4. Sources (seed list)

The curator's starting list, `seed_sources.csv`, has 18 entries:

- 14 have been opened and checked.
- 4 are leads still to find.

Each row records the publisher, tier, language, dates and the facts it supports.

| ID | Source | Publisher | Tier | Status |
| --- | --- | --- | --- | --- |
| S01 | [Janggu](https://artsandculture.google.com/asset/janggu/GwGwVtttOzjekQ) | National Gugak Center | 1 | Checked |
| S02 | [Changgo, 19th century](https://www.metmuseum.org/art/collection/search/500723) | The Met | 1 | Checked |
| S03 | [Janggo, c. 1980](https://www.metmuseum.org/art/collection/search/503797) | The Met | 1 | Checked |
| S04 | [Jeongak jango](https://www.nms.ac.uk/explore-our-collections/collection-search-results/jeongak-jango/645954) | National Museums Scotland | 1 | Checked |
| S05 | [changgo](https://www.britannica.com/art/changgo) | Britannica | 1 | Checked |
| S06 | [Nongak](https://ich.unesco.org/en/RL/nongak-community-band-music-dance-and-rituals-in-the-republic-of-korea-00717) | UNESCO | 1 | Checked |
| S07 | [사장구 (sajanggu)](https://encykorea.aks.ac.kr/Article/E0072587) | Encyclopedia of Korean Culture | 1 | Checked |
| S08 | [장구춤 (janggu dance)](https://encykorea.aks.ac.kr/Article/E0048300) | Encyclopedia of Korean Culture | 1 | Checked |
| S09 | [무장구장단 (ritual rhythm)](https://encykorea.aks.ac.kr/Article/E0072568) | Encyclopedia of Korean Culture | 1 | Checked |
| S10 | [Janggu](https://en.wikipedia.org/wiki/Janggu) | Wikipedia | 2 | Checked (lead for court dates) |
| S11 | [Samul nori](https://en.wikipedia.org/wiki/Samul_nori) | Wikipedia | 2 | Checked |
| S12 | [Kim Duk-soo](https://en.wikipedia.org/wiki/Kim_Duk-soo) | Wikipedia | 2 | Checked |
| S13 | [Goguryeo tombs](https://en.wikipedia.org/wiki/Goguryeo_tombs) | Wikipedia | 2 | Checked (context only) |
| S14 | [Jindo National Gugak Center](https://www.korea.net/NewsFocus/FoodTravel/view?articleId=117578) | Korea.net | 2 | Checked |
| S15 | Hesselink, *P'ungmul* (2006) | University of Chicago Press | 1 | Lead: get from a library |
| S16 | *Goryeo-sa*, music treatise (1451) | Primary record | 1 | Lead |
| S17 | Main 장구 entry | Encyclopedia of Korean Culture | 1 | Lead |
| S18 | 장구 dictionary entry | National Gugak Center | 1 | Lead |

## 5. Architecture

The project has two programs that share one knowledge base. The curation tool is the only part that goes online or writes facts. The chatbot only reads verified facts.

&#91;embedded content: system architecture · curation tool, knowledge base, chatbot\]

The knowledge base is the only link between the two sides. The chatbot cannot fetch or change a fact.

**Project structure (top level as you specified)**

```
janggu-expert-bot/
├── run.py              # starts the chatbot: --mode cli|web, --check
├── config.yaml         # bot behaviour and options (committed)
├── .env                # secrets (never committed); .env.example is committed
├── knowledge-base/     # janggu.db + rules/, lexicon/, dialogue/ YAML + manifest.json
├── src/                # settings, interface/, dialogue/, engine/, knowledge/, memory/
├── tools/curator/      # the separate fact-curation tool
├── tests/              # pytest + golden_questions.yaml
└── logs/               # unanswered questions (not committed)
```

**Expert-system parts and where each lives**

| Part | Location |
| --- | --- |
| Knowledge base | `knowledge-base/` (facts in SQLite, rules in YAML) |
| Inference engine | `src/engine/inference.py` (IF intent + entities THEN fact query) |
| Working memory | `src/memory/session.py` (name, mood, last topic, last fact) |
| User interface | `src/interface/cli.py` and `web.py` |
| Explanation facility | `src/engine/explainer.py` ("How do you know?" lists the sources) |
| Knowledge acquisition | `tools/curator/` |

**How a question is answered**

1. Preprocess: lower-case, tokenise, map synonyms (janggu = janggo = changgo = 장구).
2. Topic guard: if the question is off topic, reply with small talk or a polite redirect.
3. Classify the intent and entities, with a confidence score.
4. If confidence is below the threshold, ask the user to clarify, or reply "I don't have verified information yet", and log the question.
5. The inference rules choose which facts answer the question.
6. The repository returns verified (and labelled disputed) facts only.
7. The responder fills an answer template and adds the source line.

**Anti-hallucination rules**

- **No generator.** Every factual sentence is a stored statement or a template filled with stored fields.
- **Read-only database at runtime.** A single repository module applies the status filter.
- **No fact without a source.** `run.py --check` fails otherwise.
- **Confidence threshold and topic guard** run before any fact is looked up.
- **Disputed facts** are prefixed "Sources disagree on this:".
- **Unanswered questions** are logged and become the curator's to-do list.

The full design, including the `config.yaml` and `.env` samples and the rule formats, is in the Architecture Plan (section 9).

## 6. Curation tool

The curation tool turns web pages and books into verified facts. It runs only when you start it, never while the chatbot is running.

**Pipeline:** Collect → Identify claims → Classify (category and dates) → Verify (human approval) → Export to `janggu.db`.

**How it collects sources**

1. **A curated seed list, not a web crawl.** It only fetches URLs listed in `seed_sources.csv`.
2. **Reliability tiers:**
   - Tier 1 can verify a fact on its own: museums, academic works, national heritage bodies, Britannica.
   - Tier 2 needs a second source: Wikipedia, university pages, reputable news.
   - Tier 3 sources are leads only: blogs, shops, forums.
3. **Snapshot every source once.**
   - Save the raw HTML or PDF plus cleaned text.
   - Use the official Wikipedia API (it gives a revision ID) and pdfplumber for PDFs.
   - Have a manual-entry form for books, recording the page number.
4. **Record metadata:** title, URL, publisher, author, dates, tier, snapshot path and a SHA-256 hash of the content.
5. **Track independence.** A `derived_from` field excludes mirrors and copies, so two copies of one text never count as two confirmations.
6. **Fetch politely.** Check robots.txt and wait between requests.
7. **Refresh deliberately.** If a source's hash changes, every fact linked to it is flagged for re-review.

**Fact categories:** origin, etymology, chronology, construction, playing technique, cultural use and significance, evolution.

**Verification rule**

| Status | Meaning | Shown by the chatbot? |
| --- | --- | --- |
| Verified | Two independent sources agree, or one Tier 1 source states it | Yes |
| Disputed | Sources conflict | Yes, labelled, with both sides |
| Pending | Not yet checked | No |
| Rejected | Checked and wrong | No |

## 7. Technology stack

The whole stack is Python. There are no paid services, no AI model and no internet use while the bot runs.

| Area | Technologies |
| --- | --- |
| Language | Python 3.14 (3.13 if a library won't install) |
| Knowledge store | SQLite via built-in `sqlite3`, opened read-only; DB Browser for SQLite to inspect it |
| Rules, intents, dialogue | YAML via PyYAML |
| Config and secrets | PyYAML + Pydantic (validation), python-dotenv (`.env`) |
| Question matching | scikit-learn TF-IDF + cosine similarity; RapidFuzz for typos |
| Inference engine | Your own forward-chaining engine (about 150 lines) |
| Interfaces | Rich (terminal), Streamlit (web chat) |
| Curator | requests, MediaWiki API, BeautifulSoup4, pdfplumber, hashlib, Streamlit review page |
| Development | venv + pip (pinned `requirements.txt`), pytest + pytest-cov, Ruff, Git + private GitHub repo, Mermaid diagrams |

**Deliberately not used**

- Experta: its last release was in November 2019, and it lists support only up to Python 3.8 ([PyPI](https://pypi.org/project/experta)).
- LLM APIs: they break the no-hallucination rule.
- Dialogflow or Copilot Studio: they hide the inference step, which is the part an expert-system assignment is graded on.
- A vector database: unnecessary for a few hundred facts.

## 8. Decisions and next steps

**Decisions still open**

- [ ] Bot name: "Danbi" in the config sample is only a placeholder.
- [ ] Demo interface: terminal only, or a Streamlit web page as well?
- [ ] Question matching: TF-IDF with RapidFuzz for typos (recommended), or fuzzy matching alone?
- [ ] Should the bot also answer in Korean?
- [ ] Check the assignment brief for any required language, framework or file layout.

**Next steps**

- [ ] Set up the project folders and starter files to match section 5.
- [ ] Write the collector script: fetch the seed list, save snapshots, fill the `sources` table.
- [ ] Close the source gaps in section 3 (*Goryeo-sa*, the encyclopedia's main entry, the Gugak Center dictionary, Hesselink's book).
- [ ] Extract, classify and verify facts into `janggu.db`.
- [ ] Write the intents, inference rules, synonyms and dialogue files.
- [ ] Build the engine, then write 50–100 golden test questions, including ones the bot must refuse.
- [ ] Run `run.py --check` and rehearse the demo.

## 9. Document index

| Document | What it holds |
| --- | --- |
| Stick-Played Drums: Options for the Expert System Chatbot | Round 1 research: snare drum, bodhrán, taiko, dhol, janggu and 24 Festive Drums, with chronologies and sources |
| More Stick-Played Drums: Second-Round Options | Round 2 research: eight more drums after classmates' picks were excluded |
| Janggu Expert System: Architecture Plan | Full architecture: folder tree, the drawn question flow, database tables, rule formats, `config.yaml` and `.env` samples, `run.py`, tests, technology stack |
| [Drum Expert Chatbot Blueprint](https://claude.ai/artifact/4hiiL6Dtp9ttdAjEGHTUx6) | The first project-tree page, from before the drum was chosen. Where it differs from the Architecture Plan (for example on Experta), the plan is current. |
| `seed_sources.csv` | The curator's 18-row source list (sent in chat on 6 November) |
| This compendium | The summary of all of the above |
