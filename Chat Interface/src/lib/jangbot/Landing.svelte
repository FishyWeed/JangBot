<script>
  import Mascot from './Mascot.svelte';
  import Logo from './Logo.svelte';
  import Icon from './Icon.svelte';
  import Scene from './Scene.svelte';
  import RainLayer from './RainLayer.svelte';
  import Danbi from './Danbi.svelte';

  /**
   * Landing page: a rainy night at the hanok. Optionally pass `mascotSrc` to display a custom raster/SVG asset.
   * @type {{ onstart?: () => void, mascotSrc?: string, mascotAlt?: string }}
   */
  let { onstart, mascotSrc, mascotAlt = 'Danbi, the janggu mascot' } = $props();

  const states = /** @type {const} */ ([['idle', 'Idle', 'Waiting quietly'], ['thinking', 'Thinking', 'Looking it up…'], ['speaking', 'Speaking', 'Answering']]);
  const moods = /** @type {const} */ ([['wave', 'Hello', '안녕!'], ['umbrella', 'Rainy walk', '우산 아래'], ['read', 'Looking it up', '찾아보는 중'], ['lantern', 'Night light', '청사초롱'], ['bow', 'Thank you', '감사합니다'], ['sleep', 'Resting', '쿨쿨']]);
</script>

<div class="jb-app">
<div class="jb jb-land">
  <div style="position:relative">
    <nav class="jb-land__nav">
      <Logo href="/" />
      <div class="jb-land__links">
        <a href="#danbi">Meet Danbi</a>
        <a href="#sticks">The sticks</a>
        <button type="button" class="jb-btn jb-btn--outline" style="height:40px" onclick={onstart}>Start chatting <Icon name="arrowRight" size={16} /></button>
      </div>
    </nav>
    <header class="jb-hero">
      <div class="jb-hero__scene"><Scene name="hanokNight" /></div>
      <div class="jb-hero__veil"></div>
      <div class="jb-hero__copy">
        <div class="jb-hero__rain"><RainLayer /></div>
        <div class="jb-hero__copy-inner">
          <span class="jb-hero__eyebrow"><b lang="ko">장구</b>Janggu expert system</span>
          <h1>Listen to the rain. Learn the janggu.<span class="ko" lang="ko">빗소리 따라, 장구 이야기</span></h1>
          <p class="jb-hero__lead">Danbi is a small drum with a quiet voice. Ask him about the janggu’s history, its parts and its rhythms. Every answer comes with a verified source.</p>
          <div class="jb-hero__ctas">
            <button type="button" class="jb-btn jb-btn--primary jb-btn--lg" onclick={onstart}><Icon name="messageCircle" size={18} />Start chatting with Danbi</button>
            <a class="jb-btn jb-btn--outline" href="#danbi">Meet Danbi</a>
          </div>
        </div>
      </div>
      <div class="jb-hero__divider" aria-hidden="true"><Scene name="giwaBand" class="jb-giwa" /></div>
      <div class="jb-hero__stage">
        <div class="jb-hero__mobile-scene"><Scene name="hanokNight" /></div>
        <div class="jb-hero__danbi"><Danbi pose="lantern" /></div>
      </div>
    </header>
  </div>
  <Scene name="giwaBand" class="jb-giwa" />

  <section class="jb-sec" id="danbi">
    <div class="jb-sec__head">
      <span class="jb-point">POINT 01</span>
      <h2>Meet Danbi · <span lang="ko">단비를 소개해요</span></h2>
      <p>Our mascot is a little janggu who keeps time in the rain. He reacts while you chat: calm when idle, swaying while he thinks, drumming as he answers.</p>
    </div>
    <div class="jb-showcase">
      <div class="jb-slot">
        {#if mascotSrc}
          <img class="jb-slot__img" src={mascotSrc} alt={mascotAlt} />
        {:else}
          <div class="jb-slot__fig"><Danbi pose="drumming" /></div>
        {/if}
      </div>
      <div class="jb-namecard">
        <h3 lang="ko">단비 <span class="jb-namecard__roman">[dan-bi]</span></h3>
        <p><span class="jb-mark">Danbi</span> means “sweet rain”: the welcome rain that arrives right when it’s needed. That’s how answers should feel.</p>
        <p class="jb-namecard__muted">Red lacquer body, hanji drum heads, blue hoops and a lantern-amber waist band.</p>
        <div class="jb-states">
          {#each states as [s, name, note]}
            <div class="jb-state"><Mascot size={52} state={s} /><b>{name}</b><span>{note}</span></div>
          {/each}
        </div>
      </div>
    </div>
    <div class="jb-moods">
      {#each moods as [pose, name, ko]}
        <div class="jb-mood"><div class="jb-mood__fig"><Danbi {pose} /></div><b>{name}</b><span lang="ko">{ko}</span></div>
      {/each}
    </div>
  </section>

  <section class="jb-sec jb-sec--panel" id="sticks">
    <div class="jb-sec__head">
      <span class="jb-point">POINT 02</span>
      <h2>Two sticks, two voices · <span lang="ko">궁채와 열채</span></h2>
      <p>The janggu is played with a different stick in each hand.</p>
    </div>
    <div class="jb-sticks">
      <div class="jb-sticks__art"><Danbi pose="sticks" /></div>
      <div class="jb-sticks__copy">
        <h3><span lang="ko">궁채</span> · Gungchae</h3>
        <p>A mallet with a round head, held in the left hand. It gives the deep, round strokes: <span lang="ko">쿵</span>.</p>
        <h3><span lang="ko">열채</span> · Yeolchae</h3>
        <p>A thin strip of bamboo, held in the right hand. It gives the sharp, quick strokes: <span lang="ko">덕</span> and <span lang="ko">기덕</span>.</p>
        <p>Strike both heads together and you get <span lang="ko">덩</span>. Danbi, being a janggu, plays them on his own head.</p>
      </div>
    </div>
  </section>

  <section class="jb-sec">
    <div class="jb-sec__head">
      <span class="jb-point">POINT 03</span>
      <h2>Why chat with Danbi?</h2>
      <p>Three things that make JangBot different from a search box.</p>
    </div>
    <div class="jb-features">
      <div class="jb-feature">
        <span class="jb-point jb-point--blue">01 · <span lang="ko">출처</span></span>
        <h3>Verified sources</h3>
        <p>Every fact Danbi uses carries an ID you can open, with its publisher and trust tier.</p>
        <div class="jb-feature__demo"><span class="jb-cite__toggle"><Icon name="bookOpen" size={14} /><span>2 verified sources</span><span class="jb-cite__ids">JG-014 · JG-022</span></span></div>
      </div>
      <div class="jb-feature">
        <span class="jb-point jb-point--yellow">02 · <span lang="ko">기억</span></span>
        <h3>Memory per profile</h3>
        <p>Each chat profile keeps its own memory, so a beginner’s chat and a performer’s chat never mix.</p>
        <div class="jb-feature__demo"><div class="jb-status"><span class="jb-status__dot"></span><span class="jb-status__state">Online</span><span class="jb-status__sep">·</span><span>Isolated profile memory</span></div></div>
      </div>
      <div class="jb-feature">
        <span class="jb-point jb-point--peach">03 · <span lang="ko">시작</span></span>
        <h3>Easy to start</h3>
        <p>Not sure what to ask? Tap a starter prompt and Danbi takes it from there.</p>
        <div class="jb-feature__demo jb-feature__chips"><span class="jb-chip">What is a janggu?</span><span class="jb-chip">Gutgeori rhythm</span></div>
      </div>
    </div>
  </section>

  <Scene name="mountainMist" class="jb-band" />

  <section class="jb-cta">
    <div class="jb-cta__sign"><Scene name="signboard" /></div>
    <div>
      <h2>When it rains, Danbi plays.<em lang="ko">비가 오면, 단비가 노래해요.</em></h2>
      <p>Free to use. No sign-up needed for your first chat.</p>
      <button type="button" class="jb-btn jb-btn--primary jb-btn--lg" onclick={onstart}><Icon name="messageCircle" size={18} />Start chatting</button>
    </div>
  </section>
  <footer class="jb-foot">
    <Scene name="giwaBand" />
    <div class="jb-foot__text">JangBot · <span lang="ko">장봇</span> — a janggu expert system</div>
  </footer>
</div>
</div>
