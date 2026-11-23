/* 文字起こし・読み上げ（日本語は収録音声、英語は端末の声） */
(() => {
  const data = (() => { try { return JSON.parse(document.getElementById('transcript').textContent); } catch (e) { return null; } })();
  const btn = document.getElementById('listen-toggle');
  if (!data || !btn) return;
  const store = { get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }, set(k, v) { try { localStorage.setItem(k, v); } catch (e) {} } };
  const LBL = { ja: { title: '題', narr: '語り', say: 'セリフ' }, en: { title: 'Title', narr: 'Narration', say: 'Speech' } };
  let lang = store.get('saku:tr-lang') === 'en' ? 'en' : 'ja';
  let auto = store.get('saku:tr-auto') !== '0';
  let pages = [0, 0], playing = false, audio = null, queue = [], qi = 0, waitTurn = false;
  const synth = window.speechSynthesis;

  const panel = document.createElement('aside');
  panel.className = 'tr-panel'; panel.hidden = true; panel.setAttribute('aria-label', '文字起こし');
  panel.innerHTML =
    '<div class="tr-head"><strong class="tr-page"></strong>' +
    '<span class="tr-lang"><button type="button" data-l="ja">日本語</button><button type="button" data-l="en">EN</button></span>' +
    '<button type="button" class="tr-play"><span class="tr-ic">▶</span><span class="tr-pl">聞く</span></button>' +
    '<label class="tr-auto"><input type="checkbox"> <span>自動めくり</span></label>' +
    '<button type="button" class="tr-txt" aria-pressed="true">文字</button>' +
    '<button type="button" class="tr-close" aria-label="閉じる">×</button></div>' +
    '<p class="tr-sub" aria-live="polite"></p><ol class="tr-lines"></ol><p class="tr-credit"></p>';
  document.body.appendChild(panel);
  const $ = s => panel.querySelector(s);
  const autoBox = $('.tr-auto input'); autoBox.checked = auto;

  function linesFor() {
    const out = [];
    for (let p = pages[0]; p <= pages[1]; p++) (data.pages[String(p + 1)] || []).forEach(l => out.push(Object.assign({ page: p }, l)));
    return out;
  }
  function render() {
    const ls = linesFor();
    const pg = pages[0] === pages[1] ? pages[0] + 1 : (pages[0] + 1) + '-' + (pages[1] + 1);
    $('.tr-page').textContent = lang === 'ja' ? pg + 'ページ' : 'Page ' + pg;
    $('.tr-pl').textContent = playing ? (lang === 'ja' ? '止める' : 'Stop') : (lang === 'ja' ? '聞く' : 'Listen');
    $('.tr-ic').textContent = playing ? '■' : '▶';
    $('.tr-auto span').textContent = lang === 'ja' ? '自動めくり' : 'Auto';
    panel.querySelectorAll('.tr-lang button').forEach(b => b.setAttribute('aria-pressed', b.dataset.l === lang));
    const ol = $('.tr-lines'); ol.replaceChildren();
    if (!ls.length) {
      const li = document.createElement('li'); li.className = 'tr-empty';
      li.textContent = lang === 'ja' ? 'このページの文字起こしは準備中です' : 'Transcript coming soon for this page.';
      ol.appendChild(li);
    }
    ls.forEach((l, i) => {
      const li = document.createElement('li'); li.dataset.i = i; li.className = 'k-' + l.kind + (l.noread ? ' noread' : '');
      const tx = document.createElement('span'); tx.className = 'tr-tx'; const t = l[lang] || l.ja;
      tx.textContent = l.kind === 'say' && lang === 'ja' ? '「' + t + '」' : t;
      li.append(tx); ol.appendChild(li);
    });
    $('.tr-play').disabled = !ls.some(l => !l.noread);
    $('.tr-credit').textContent = lang === 'ja' ? '音声：' + data.voice_credit : 'Voice: your device';
  }
  function mark(i) { const sub = $('.tr-sub'); const ls = linesFor(); sub.textContent = i >= 0 && ls[i] ? (ls[i][lang] || ls[i].ja) : ''; panel.querySelectorAll('.tr-lines li').forEach(li => { const on = Number(li.dataset.i) === i; li.classList.toggle('reading', on); if (on) li.scrollIntoView({ block: 'nearest', behavior: 'smooth' }); }); }
  function stop() {
    playing = false; waitTurn = false; queue = [];
    if (audio) { audio.pause(); audio = null; }
    if (synth) synth.cancel();
    mark(-1); render();
  }
  function enVoice() {
    const v = (synth ? synth.getVoices() : []).filter(x => /^en/i.test(x.lang));
    const fem = /Samantha|Ava|Allison|Susan|Zira|Aria|Jenny|Karen|Moira|Tessa|Serena|Victoria|Joanna|Emma|Michelle|Libby|Sonia|Female|Google US English/i;
    const q = x => (/Natural|Neural/i.test(x.name) ? 4 : /Premium|Enhanced/i.test(x.name) ? 3 : /Online|Google/i.test(x.name) ? 2 : 0) + (fem.test(x.name) && !/Male/.test(x.name) ? 5 : 0);
    return v.sort((a, b) => q(b) - q(a))[0] || null;
  }
  function step() {
    if (!playing) return;
    if (qi >= queue.length) {
      mark(-1);
      const nextHas = data.pages[String(pages[1] + 2)];
      if (auto && nextHas) { waitTurn = true; document.dispatchEvent(new CustomEvent('saku:next')); }
      else stop();
      return;
    }
    const it = queue[qi++]; mark(it.i);
    const done = () => setTimeout(step, 300);
    if (lang === 'ja') {
      if (!it.l.audio) { step(); return; }
      audio = new Audio(it.l.audio); audio.onended = done; audio.onerror = done;
      const p = audio.play(); if (p && p.catch) p.catch(stop);
    } else {
      if (!synth) { stop(); return; }
      const u = new SpeechSynthesisUtterance((it.l.en_say || it.l.en).replace(/…/g, ', ').replace(/^[,\s]+/, ''));
      u.lang = 'en-US'; const v = enVoice(); if (v) u.voice = v;
      u.rate = it.l.kind === 'title' ? .9 : .95; if (/!!/.test(it.l.en)) { u.pitch = 1.08; u.rate = 1.03; }
      u.onend = done; u.onerror = done; synth.speak(u);
    }
  }
  function play() {
    const ls = linesFor();
    queue = ls.map((l, i) => ({ l, i })).filter(x => !x.l.noread);
    qi = 0; playing = true; render(); step();
  }
  document.addEventListener('saku:page', e => {
    const same = pages[0] === e.detail.start && pages[1] === e.detail.end;
    pages = [e.detail.start, e.detail.end];
    if (same && !waitTurn) return;
    if (playing && waitTurn) { waitTurn = false; if (audio) audio.pause(); if (synth) synth.cancel(); setTimeout(play, 350); }
    else if (playing) stop();
    render();
  });
  function fit() {
    const side = innerWidth > innerHeight && showText; document.documentElement.style.setProperty('--trh', panel.hidden || side ? '0px' : panel.offsetHeight + 'px');
    window.dispatchEvent(new Event('resize'));
  }
  if (window.ResizeObserver) new ResizeObserver(() => { if (!panel.hidden) fit(); }).observe(panel);
  btn.addEventListener('click', () => {
    panel.hidden = !panel.hidden; btn.setAttribute('aria-pressed', !panel.hidden);
    document.body.classList.toggle('tr-open', !panel.hidden);
    store.set('saku:tr-open', panel.hidden ? '0' : '1'); if (panel.hidden) stop(); fit();
  });
  $('.tr-close').onclick = () => btn.click();
  $('.tr-play').onclick = () => (playing ? stop() : play());
  panel.querySelectorAll('.tr-lang button').forEach(b => b.onclick = () => { lang = b.dataset.l; store.set('saku:tr-lang', lang); stop(); applyText(); });
  let showText = store.get('saku:tr-text') !== '0';
  const txtBtn = $('.tr-txt');
  function applyText() { panel.classList.toggle('no-text', !showText); document.body.classList.toggle('tr-notext', !showText); txtBtn.setAttribute('aria-pressed', showText); txtBtn.textContent = lang === 'ja' ? '文字' : 'Text'; fit(); }
  txtBtn.onclick = () => { showText = !showText; store.set('saku:tr-text', showText ? '1' : '0'); applyText(); };
  autoBox.onchange = () => { auto = autoBox.checked; store.set('saku:tr-auto', auto ? '1' : '0'); };
  const c = document.getElementById('counter');
  if (c) { const m = c.textContent.match(/^(\d+)(?:-(\d+))?/); if (m) pages = [Number(m[1]) - 1, Number(m[2] || m[1]) - 1]; }
  applyText();
  if (store.get('saku:tr-open') === '1') btn.click();
  render();
})();
