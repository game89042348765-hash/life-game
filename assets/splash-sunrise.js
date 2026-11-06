/* Sunrise is an optional UI introduction; it never reads or writes game progress. */
(() => {
  'use strict';
  const KEY = 'lifegame-sunrise-v1';
  const mode = document.getElementById('lg-sunrise-mode');
  const replay = document.getElementById('lg-sunrise-replay');
  const status = document.getElementById('lg-sunrise-status');
  const sounds = document.getElementById('sound-enabled');
  if (!mode || !replay || !status || !sounds) return;
  const today = () => {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
  };
  let readable = true;
  function readPrefs() {
    try {
      const raw = localStorage.getItem(KEY);
      if (raw === null) return {mode:'daily',lastShownDay:null};
      const data = JSON.parse(raw);
      if (!data || !['daily','always','off'].includes(data.mode) ||
          (data.lastShownDay !== null && !/^\d{4}-\d{2}-\d{2}$/.test(data.lastShownDay))) throw new Error('Invalid preference');
      return {mode:data.mode,lastShownDay:data.lastShownDay};
    } catch {
      readable = false;
      status.textContent = 'Не удалось прочитать настройку. Заставку можно посмотреть вручную.';
      return {mode:'off',lastShownDay:null};
    }
  }
  let prefs = readPrefs();
  mode.value = prefs.mode;
  function save(next) {
    try {
      localStorage.setItem(KEY, JSON.stringify(next));
      prefs = next; readable = true; mode.value = prefs.mode;
      return true;
    } catch {
      status.textContent = 'Не удалось сохранить настройку. Попробуй ещё раз.';
      return false;
    }
  }
  const splash = document.createElement('dialog');
  splash.className = 'lg-sunrise';
  splash.setAttribute('aria-label','Заставка LifeGame. Больше жизни. В каждом дне.');
  splash.innerHTML = ` <div class="lg-sunrise-ambient-back"></div>
 <div class="lg-sunrise-frame">
  <div class="lg-sunrise-poster"></div>
  <div class="lg-sunrise-top-veil"></div>
  <div class="lg-sunrise-sun-glow"></div>
  <svg class="lg-sunrise-ring" viewBox="0 0 941 1672" aria-hidden="true" preserveAspectRatio="none">
   <circle cx="468" cy="641" r="459"></circle>
  </svg>
  <div class="lg-sunrise-horizon-flare"></div>
  <div class="lg-sunrise-embers" aria-hidden="true"><i class="lg-sunrise-ember" style="--x:94%;--y:21%;--delay:-3.02s;--dur:2.64s;--s:4px"></i>
<i class="lg-sunrise-ember" style="--x:62%;--y:35%;--delay:1.26s;--dur:2.13s;--s:2px"></i>
<i class="lg-sunrise-ember" style="--x:25%;--y:31%;--delay:-2.03s;--dur:2.42s;--s:4px"></i>
<i class="lg-sunrise-ember" style="--x:85%;--y:26%;--delay:-1.67s;--dur:3.66s;--s:3px"></i>
<i class="lg-sunrise-ember" style="--x:75%;--y:18%;--delay:-3.08s;--dur:4.2s;--s:5px"></i>
<i class="lg-sunrise-ember" style="--x:77%;--y:32%;--delay:0.24s;--dur:4.27s;--s:4px"></i>
<i class="lg-sunrise-ember" style="--x:64%;--y:52%;--delay:-1.17s;--dur:2.28s;--s:5px"></i>
<i class="lg-sunrise-ember" style="--x:22%;--y:54%;--delay:-1.98s;--dur:2.5s;--s:5px"></i>
<i class="lg-sunrise-ember" style="--x:66%;--y:31%;--delay:-1.06s;--dur:2.83s;--s:2px"></i>
<i class="lg-sunrise-ember" style="--x:38%;--y:20%;--delay:-1.06s;--dur:3.37s;--s:2px"></i>
<i class="lg-sunrise-ember" style="--x:95%;--y:26%;--delay:-2.45s;--dur:3.54s;--s:2px"></i>
<i class="lg-sunrise-ember" style="--x:71%;--y:36%;--delay:-2.26s;--dur:2.15s;--s:2px"></i>
<i class="lg-sunrise-ember" style="--x:21%;--y:41%;--delay:-1.04s;--dur:2.16s;--s:2px"></i>
<i class="lg-sunrise-ember" style="--x:87%;--y:48%;--delay:-2.39s;--dur:2.13s;--s:4px"></i>
<i class="lg-sunrise-ember" style="--x:55%;--y:75%;--delay:-0.4s;--dur:2.89s;--s:4px"></i>
<i class="lg-sunrise-ember" style="--x:80%;--y:19%;--delay:0.9s;--dur:3.03s;--s:3px"></i>
<i class="lg-sunrise-ember" style="--x:23%;--y:50%;--delay:1.29s;--dur:2.69s;--s:4px"></i>
<i class="lg-sunrise-ember" style="--x:71%;--y:40%;--delay:0.15s;--dur:3.97s;--s:4px"></i>
<i class="lg-sunrise-ember" style="--x:14%;--y:51%;--delay:-1.07s;--dur:3.3s;--s:2px"></i>
<i class="lg-sunrise-ember" style="--x:94%;--y:41%;--delay:-2.21s;--dur:2.27s;--s:4px"></i>
<i class="lg-sunrise-ember" style="--x:47%;--y:47%;--delay:-1.36s;--dur:3.18s;--s:5px"></i>
<i class="lg-sunrise-ember" style="--x:67%;--y:59%;--delay:-1.31s;--dur:3.76s;--s:3px"></i>
<i class="lg-sunrise-ember" style="--x:85%;--y:31%;--delay:-0.24s;--dur:3.1s;--s:4px"></i>
<i class="lg-sunrise-ember" style="--x:64%;--y:68%;--delay:-2.61s;--dur:2.82s;--s:3px"></i>
<i class="lg-sunrise-ember" style="--x:58%;--y:23%;--delay:-0.37s;--dur:2.68s;--s:3px"></i>
<i class="lg-sunrise-ember" style="--x:96%;--y:61%;--delay:0.46s;--dur:3.77s;--s:4px"></i>
<i class="lg-sunrise-ember" style="--x:32%;--y:25%;--delay:-3.23s;--dur:3.61s;--s:2px"></i>
<i class="lg-sunrise-ember" style="--x:58%;--y:61%;--delay:1.46s;--dur:4.23s;--s:4px"></i>
<i class="lg-sunrise-ember" style="--x:48%;--y:26%;--delay:0.18s;--dur:3.89s;--s:5px"></i>
<i class="lg-sunrise-ember" style="--x:90%;--y:76%;--delay:-0.9s;--dur:2.22s;--s:5px"></i></div>
  <div class="lg-sunrise-light-sweep"></div>
  <div class="lg-sunrise-bar-eraser"></div>
  <div class="lg-sunrise-loading" aria-hidden="true"><div class="lg-sunrise-loading-fill"></div></div>
 </div>
    <div class="lg-sunrise-controls">
      <button type="button" data-sunrise="skip" autofocus>Пропустить</button>
      <button type="button" data-sunrise="sound" hidden>Включить звук</button>
    </div>
    <button type="button" class="lg-sunrise-disable" data-sunrise="disable">Не показывать при запуске</button>`;
  document.body.append(splash);
  const enableSound = splash.querySelector('[data-sunrise="sound"]');
  let active = false, pending = false, closeTimer, previousFocus;
  let audio = null, played = false;
  const voices = [];
  let imageReady;
  function artReady() {
    if (!imageReady) imageReady = new Promise((resolve,reject) => {
      const img = new Image();
      img.onload = resolve; img.onerror = reject;
      img.src = new URL('images/sunrise-splash.jpg', document.currentScript?.src || new URL('assets/splash-sunrise.js',document.baseURI)).href;
    });
    return imageReady;
  }
  function soundOn() { return sounds.checked && !sounds.disabled; }
  function stopAudio() {
    for (const [osc,gain] of voices.splice(0)) {
      gain.disconnect();
      try { osc.stop(); } catch { /* already ended */ }
    }
    if (audio) { const old = audio; audio = null; old.close().catch(() => {}); }
    played = false;
  }
  function syncSoundButton() {
    enableSound.hidden = !soundOn() || !audio || audio.state === 'running';
  }
  function playNotes() {
    if (!active || played || !soundOn() || !audio || audio.state !== 'running') return;
    played = true;
    const now = audio.currentTime;
    // A soft, short ascending chord; no downloaded audio or external API.
    [196,293.66,392,523.25].forEach((frequency,i) => {
      const osc = audio.createOscillator(), gain = audio.createGain();
      osc.type = 'sine'; osc.frequency.value = frequency;
      const at = now + i * .23;
      gain.gain.setValueAtTime(0,at);
      gain.gain.linearRampToValueAtTime(.045,at+.12);
      gain.gain.exponentialRampToValueAtTime(.0001,at+1.35);
      osc.connect(gain); gain.connect(audio.destination);
      voices.push([osc,gain]); osc.start(at); osc.stop(at+1.45);
    });
    syncSoundButton();
  }
  function requestSound() {
    if (!soundOn()) return;
    try {
      const Audio = window.AudioContext || window.webkitAudioContext;
      if (!Audio) return;
      if (!audio) audio = new Audio();
      if (audio.state === 'suspended') audio.resume().then(() => { playNotes(); syncSoundButton(); }).catch(() => {});
      playNotes(); syncSoundButton();
    } catch { syncSoundButton(); }
  }
  function finish() {
    clearTimeout(closeTimer);
    active = false;
    stopAudio();
    splash.classList.remove('is-playing');
    if (splash.open) splash.close();
    document.documentElement.classList.remove('lg-sunrise-open');
    if (previousFocus?.isConnected) previousFocus.focus({preventScroll:true});
  }
  async function show(manual = false) {
    if (active || pending) return;
    pending = true;
    // Keep this request inside the manual click's user activation.
    if (manual) requestSound();
    try {
      await artReady();
      if (document.hidden) { stopAudio(); return; }
      if (!manual) {
        prefs = readPrefs(); mode.value = prefs.mode;
        if (!readable || prefs.mode === 'off' || (prefs.mode === 'daily' && prefs.lastShownDay === today())) return;
        if (!document.getElementById('save-warning')?.hidden) return;
        if (!save({...prefs,lastShownDay:today()})) return;
      }
      previousFocus = document.activeElement;
      splash.showModal();
      active = true;
      document.documentElement.classList.add('lg-sunrise-open');
      splash.classList.add('is-playing');
      requestSound(); playNotes(); syncSoundButton();
      closeTimer = setTimeout(finish,4500);
    } catch {
      status.textContent = 'Не удалось открыть заставку. Приложение доступно как обычно.';
      finish();
      imageReady = null;
    } finally { pending = false; }
  }
  splash.querySelector('[data-sunrise="skip"]').addEventListener('click',finish);
  enableSound.addEventListener('click',requestSound);
  splash.querySelector('[data-sunrise="disable"]').addEventListener('click',() => {
    if (save({...prefs,mode:'off'})) { status.textContent = 'Автопоказ выключен. Ручной просмотр доступен.'; finish(); }
    else splash.querySelector('[data-sunrise="disable"]').textContent = 'Не удалось сохранить · повторить';
  });
  splash.addEventListener('cancel',e => { e.preventDefault(); finish(); });
  splash.addEventListener('close',() => { if (active) finish(); });
  splash.addEventListener('animationend',e => { if (e.target === splash && e.animationName === 'lg-sunrise-splash-exit') finish(); });
  mode.addEventListener('change',() => {
    if (save({...prefs,mode:mode.value})) status.textContent = prefs.mode === 'off' ? 'Автопоказ выключен. Ручной просмотр доступен.' : 'Режим показа сохранён.';
    else mode.value = prefs.mode;
  });
  replay.addEventListener('click',() => show(true));
  sounds.addEventListener('change',() => { if (!soundOn()) stopAudio(); syncSoundButton(); });
  document.addEventListener('visibilitychange',() => { if (document.hidden && active) finish(); });
  window.addEventListener('pagehide',finish);
  window.addEventListener('popstate',() => { if (active) finish(); });
  window.addEventListener('storage',e => {
    if (e.key === KEY || e.key === null) {
      prefs = readPrefs(); mode.value = prefs.mode;
      if (prefs.mode === 'off' && active) finish();
    }
    if (!soundOn()) stopAudio();
  });
  show();
})();
