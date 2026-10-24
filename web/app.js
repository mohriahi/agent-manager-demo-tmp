/* The demo's page: the customer's chat drives the Assistant, and each step it
 * reports lights up the map and the list of what happened. */

/* Some icons are Lucide's (lucide.dev, ISC license); mcp is the protocol's own logo. */
const ICONS = {
  brain: '<path d="M12 5a3 3 0 1 0-5.997.125 4 4 0 0 0-2.526 5.77 4 4 0 0 0 .556 6.588A4 4 0 1 0 12 18ZM12 5a3 3 0 1 1 5.997.125 4 4 0 0 1 2.526 5.77 4 4 0 0 1-.556 6.588A4 4 0 1 1 12 18ZM15 13a4.5 4.5 0 0 1-3-4 4.5 4.5 0 0 1-3 4M17.599 6.5a3 3 0 0 0 .399-1.375M6.003 5.125A3 3 0 0 0 6.401 6.5M3.477 10.896a4 4 0 0 1 .585-.396M19.938 10.5a4 4 0 0 1 .585.396M6 18a4 4 0 0 1-1.967-.516M19.967 17.484A4 4 0 0 1 18 18"/>',
  sparkles: '<path d="M9.937 15.5A2 2 0 0 0 8.5 14.063l-6.135-1.582a.5.5 0 0 1 0-.962L8.5 9.936A2 2 0 0 0 9.937 8.5l1.582-6.135a.5.5 0 0 1 .963 0L14.063 8.5A2 2 0 0 0 15.5 9.937l6.135 1.581a.5.5 0 0 1 0 .964L15.5 14.063a2 2 0 0 0-1.437 1.437l-1.582 6.135a.5.5 0 0 1-.963 0z"/><path d="M20 3v4M22 5h-4M4 17v2M5 18H3"/>',
  mcp: '<path d="M2.04 11.26L11.48 1.82C12.79 0.51 14.9 0.51 16.2 1.82V1.82C17.51 3.12 17.51 5.23 16.2 6.54L9.07 13.67M9.17 13.57L16.2 6.54C17.51 5.23 19.62 5.23 20.92 6.54L20.97 6.59C22.27 7.89 22.27 10 20.97 11.31L12.43 19.84C12 20.28 12 20.98 12.43 21.42L14.19 23.17M13.84 4.18L6.86 11.16C5.56 12.46 5.56 14.57 6.86 15.88V15.88C8.17 17.18 10.28 17.18 11.58 15.88L18.56 8.9" stroke-width="1.25"/>',
  bot: '<path d="M12 8V4H8"/><rect x="4" y="8" width="16" height="12" rx="2"/><path d="M2 14h2M20 14h2M9 13v2M15 13v2"/>',
  user: '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
  external: '<path d="M15 3h6v6"/><path d="M10 14 21 3"/><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>',
  send: '<path d="M14.536 21.686a.5.5 0 0 0 .937-.024l6.5-19a.496.496 0 0 0-.635-.635l-19 6.5a.5.5 0 0 0-.024.937l7.93 3.18a2 2 0 0 1 1.112 1.11z"/><path d="m21.854 2.147-10.94 10.939"/>',
  list: '<path d="M3 12h.01"/><path d="M3 18h.01"/><path d="M3 6h.01"/><path d="M8 12h13"/><path d="M8 18h13"/><path d="M8 6h13"/>',
  fleet: '<rect x="16" y="16" width="6" height="6" rx="1"/><rect x="2" y="16" width="6" height="6" rx="1"/><rect x="9" y="2" width="6" height="6" rx="1"/><path d="M5 16v-3a1 1 0 0 1 1-1h12a1 1 0 0 1 1 1v3"/><path d="M12 12V8"/>',
};

const QUESTION = "I lost my debit card in Lisbon. Please send me a new one. And while I'm in Portugal, "
  + 'what does paying by card cost me, and is there travel insurance for me?';

// The model's list price (USD per million tokens), for the cost shown: Claude Haiku 4.5.
const PRICE = { input: 1, output: 5 };

// Tools that change the customer's account, and what they change: the
// customer never asks for these in this story.
const UNASKED = { change_package: 'moved the customer to another package' };

const SVG = 'http://www.w3.org/2000/svg';
const $ = (id) => document.getElementById(id);

/* ---- the map ---- */

const NODES = {
  customer: { x: 74, y: 230, w: 124, title: 'Customer', sub: 'signed in', icon: 'user' },
  assistant: { x: 268, y: 230, w: 172, title: 'Assistant', sub: "the customer's agent", icon: 'sparkles', badge: 'v1' },
  cards: { x: 478, y: 120, w: 176, title: 'Cards Agent', sub: 'acts on the account', icon: 'bot', badge: 'v1' },
  model: { x: 804, y: 78, w: 172, title: 'Claude', sub: 'LLM route', icon: 'brain' },
  core: { x: 804, y: 206, w: 172, title: 'Core Banking', sub: 'MCP route', icon: 'mcp' },
  money: { x: 804, y: 334, w: 172, title: 'Travel Money', sub: 'A2A route', icon: 'bot' },
  insurance: { x: 804, y: 462, w: 172, title: 'Travel Insurance', sub: 'A2A route, a partner', icon: 'bot' },
};
const EDGES = {
  'customer-assistant': ['customer', 'assistant'],
  'assistant-model': ['assistant', 'model'],
  'assistant-cards': ['assistant', 'cards'],
  'cards-model': ['cards', 'model'],
  'cards-core': ['cards', 'core'],
  'assistant-money': ['assistant', 'money'],
  'assistant-insurance': ['assistant', 'insurance'],
};
const AGENT_EDGE = { 'Cards Agent': 'assistant-cards', 'Travel Money Agent': 'assistant-money',
  'Travel Insurance Agent': 'assistant-insurance' };
const AGENT_NODE = { 'Cards Agent': 'cards', 'Travel Money Agent': 'money', 'Travel Insurance Agent': 'insurance' };
const NODE_H = 58;

function el(name, attrs, parent) {
  const node = document.createElementNS(SVG, name);
  Object.entries(attrs || {}).forEach(([key, value]) => node.setAttribute(key, value));
  if (parent) parent.appendChild(node);
  return node;
}

function icon(name, x, y, size, parent) {
  const box = el('svg', { x, y, width: size, height: size, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor',
    'stroke-width': 2, 'stroke-linecap': 'round', 'stroke-linejoin': 'round', class: 'node-icon' }, parent);
  box.innerHTML = ICONS[name] || '';
  return box;
}

function drawMap() {
  const map = $('map');
  map.innerHTML = '';
  // Agent Manager's frame around the bank's own agents, and the gateway that
  // every call leaving an agent goes through.
  el('rect', { x: 166, y: 26, width: 410, height: 492, rx: 22, class: 'frame' }, map);
  el('text', { x: 186, y: 52, class: 'frame-label' }, map).textContent = 'Agent Manager';
  el('rect', { x: 668, y: 26, width: 44, height: 492, rx: 14, class: 'gateway' }, map);
  const label = el('text', { x: 696, y: 272, class: 'gateway-label', transform: 'rotate(-90 696 272)',
    'text-anchor': 'middle' }, map);
  label.textContent = 'WSO2 AI GATEWAY';

  const edges = el('g', {}, map);
  Object.entries(EDGES).forEach(([id, [from, to]]) => {
    const a = NODES[from], b = NODES[to];
    const x1 = a.x + a.w / 2, x2 = b.x - b.w / 2, dx = Math.max(40, (x2 - x1) / 2);
    el('path', { id: 'edge-' + id, class: 'edge', d: `M${x1} ${a.y} C${x1 + dx} ${a.y}, ${x2 - dx} ${b.y}, ${x2} ${b.y}` }, edges);
  });
  el('g', { id: 'labels' }, map);
  el('g', { id: 'pulses' }, map);
  drawRegistry(map);

  Object.entries(NODES).forEach(([id, n]) => {
    const g = el('g', { id: 'node-' + id, class: 'node' }, map);
    el('rect', { x: n.x - n.w / 2, y: n.y - NODE_H / 2, width: n.w, height: NODE_H, rx: 14, class: 'node-box' }, g);
    icon(n.icon, n.x - n.w / 2 + 12, n.y - 11, 22, g);
    el('text', { x: n.x - n.w / 2 + 42, y: n.y - 3, class: 'node-title' }, g).textContent = n.title;
    el('text', { x: n.x - n.w / 2 + 42, y: n.y + 15, class: 'node-sub' }, g).textContent = n.sub;
    if (n.badge) {
      const badge = el('g', { id: 'badge-' + id, class: 'badge' }, g);
      el('rect', { x: n.x + n.w / 2 - 30, y: n.y - NODE_H / 2 - 9, width: 30, height: 18, rx: 9 }, badge);
      el('text', { x: n.x + n.w / 2 - 15, y: n.y - NODE_H / 2 + 4, 'text-anchor': 'middle' }, badge).textContent = n.badge;
    }
  });
}

/* Agent Manager's registry of the bank's agents: the two it traces, and the
 * two that run elsewhere and are only registered. */
function drawRegistry(map) {
  const g = el('g', { id: 'registry' }, map);
  el('text', { x: 190, y: 352, class: 'registry-title' }, g).textContent = 'REGISTERED AGENTS';
  [['assistant', 'Assistant v1: traced'], ['cards', 'Cards Agent v1: traced'],
    ['money', 'Travel Money Agent: runs elsewhere'], ['insurance', "Travel Insurance Agent: a partner's"]]
    .forEach(([id, text], index) => {
      const y = 380 + index * 26;
      el('circle', { id: 'reg-dot-' + id, cx: 196, cy: y - 4, r: 4,
        class: 'registry-dot' + (id === 'money' || id === 'insurance' ? ' is-external' : '') }, g);
      el('text', { id: 'reg-' + id, x: 210, y, class: 'registry-row' }, g).textContent = text;
    });
}

function setNode(id, state) {
  const node = $('node-' + id);
  if (node) node.setAttribute('class', 'node' + (state ? ' is-' + state : ''));
}

function setEdge(id, state) {
  const edge = $('edge-' + id);
  if (edge) edge.setAttribute('class', 'edge' + (state ? ' is-' + state : ''));
}

function setBadge(version) {
  const badge = $('badge-cards');
  if (!badge) return;
  badge.querySelector('text').textContent = version || '?';
  badge.setAttribute('class', 'badge' + (version === 'v2' ? ' is-new' : ''));
  $('reg-cards').textContent = 'Cards Agent ' + (version || '?') + ': traced';
}

/* The Cards Agent's line in the registry, red once it did something unasked. */
function flagCards(bad) {
  $('reg-cards').setAttribute('class', 'registry-row' + (bad ? ' is-bad' : ''));
  $('reg-dot-cards').setAttribute('class', 'registry-dot' + (bad ? ' is-bad' : ''));
  if (bad) $('reg-cards').textContent = 'Cards Agent ' + (config.release || '') + ': changed an account unasked';
}

/* A dot that travels along an edge, out or back. */
function pulse(id, back, bad) {
  const path = $('edge-' + id);
  if (!path) return;
  const dot = el('circle', { r: 5, class: 'pulse' + (bad ? ' is-bad' : '') }, $('pulses'));
  const motion = el('animateMotion', { dur: '0.7s', fill: 'freeze', keyPoints: back ? '1;0' : '0;1', keyTimes: '0;1',
    calcMode: 'linear' }, dot);
  el('mpath', { href: '#edge-' + id }, motion);
  motion.beginElement();
  setTimeout(() => dot.remove(), 750);
}

/* A short label on an edge, such as the tool a call used. */
function edgeLabel(id, text, bad) {
  const path = $('edge-' + id);
  const point = path.getPointAtLength(path.getTotalLength() * 0.5);
  const label = el('text', { x: point.x, y: point.y - 8, 'text-anchor': 'middle',
    class: 'edge-label' + (bad ? ' is-bad' : '') }, $('labels'));
  label.textContent = text;
  return label;
}

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

/* ---- the run of one request ---- */

let config = {};
let session = newSession();
let busy = false;
let run = null;

function newSession() {
  return 'demo-' + Math.random().toString(36).slice(2, 10);
}

function resetRun() {
  drawMap();
  setBadge(config.release);
  $('steps').innerHTML = '';
  $('trace-links').innerHTML = '';
  run = { started: performance.now(), agents: new Set(['Assistant']), calls: 0, input: 0, output: 0, steps: {},
    bad: false, thoughts: 0 };
  totals();
}

function totals() {
  const seconds = run ? (performance.now() - run.started) / 1000 : 0;
  $('t-time').textContent = seconds.toFixed(1) + ' s';
  $('t-agents').textContent = run ? run.agents.size : 0;
  $('t-calls').textContent = run ? run.calls : 0;
  $('t-tokens').textContent = run ? (run.input + run.output).toLocaleString('en') : 0;
  const cost = run ? (run.input * PRICE.input + run.output * PRICE.output) / 1e6 : 0;
  $('t-cost').textContent = '$' + cost.toFixed(4);
}

function addStep(head, body, extra) {
  const item = document.createElement('li');
  item.className = 'step' + (extra && extra.bad ? ' is-bad' : '');
  const top = document.createElement('div');
  top.className = 'step-head';
  const title = document.createElement('span');
  title.textContent = head;
  const time = document.createElement('span');
  time.className = 'step-time';
  time.textContent = extra && extra.ms != null ? (extra.ms / 1000).toFixed(1) + ' s' : '';
  top.append(title, time);
  item.appendChild(top);
  if (body) {
    const text = document.createElement('p');
    text.textContent = body;
    item.appendChild(text);
  }
  $('steps').appendChild(item);
  $('steps').scrollTop = $('steps').scrollHeight;
  return item;
}

function countModel(event) {
  run.calls += 1;
  run.input += event.inputTokens || 0;
  run.output += event.outputTokens || 0;
}

/* The Cards Agent's own steps arrive with its answer: replay them on the map. */
async function replayCards(event) {
  const tools = document.createElement('ul');
  tools.className = 'tools';
  for (const step of event.steps || []) {
    if (step.kind === 'llm') {
      countModel(step);
      setEdge('cards-model', 'active');
      pulse('cards-model');
      await sleep(260);
      setEdge('cards-model', 'ok');
      continue;
    }
    run.calls += 1;
    const unasked = UNASKED[step.name] && step.outcome === 'ok';
    const state = unasked ? 'bad' : step.outcome === 'refused' ? 'refused' : step.outcome === 'ok' ? 'ok' : 'bad';
    setEdge('cards-core', 'active');
    pulse('cards-core', false, unasked);
    const label = edgeLabel('cards-core', step.name, unasked);
    await sleep(420);
    setEdge('cards-core', state);
    setTimeout(() => label.remove(), 1600);
    const line = document.createElement('li');
    line.className = 'is-' + state;
    line.innerHTML = '<span class="dot"></span>';
    const name = document.createElement('code');
    name.textContent = step.name;
    line.appendChild(name);
    if (unasked) {
      line.appendChild(document.createTextNode(': ' + UNASKED[step.name] + ', unasked'));
      run.bad = true;
    } else if (step.outcome === 'refused') {
      line.appendChild(document.createTextNode(': refused by the gateway'));
    }
    tools.appendChild(line);
  }
  return tools;
}

async function onEvent(event) {
  if (event.type === 'llm' && event.status === 'start') {
    setNode('assistant', 'working');
    setEdge('assistant-model', 'active');
    pulse('assistant-model');
  } else if (event.type === 'llm' && event.status === 'done') {
    countModel(event);
    pulse('assistant-model', true);
    setEdge('assistant-model', 'ok');
    run.thoughts += 1;
    addStep(run.thoughts === 1 ? 'Assistant split the request' : 'Assistant put the answers together',
      `${event.model}: ${event.inputTokens} tokens in, ${event.outputTokens} out`, { ms: event.ms });
  } else if (event.type === 'call' && event.status === 'start') {
    run.agents.add(event.to);
    const edge = AGENT_EDGE[event.to];
    setEdge(edge, 'active');
    pulse(edge);
    setNode(AGENT_NODE[event.to], 'working');
    run.steps[event.id] = addStep('Assistant to ' + event.to, event.input);
  } else if (event.type === 'call' && event.status === 'done') {
    const edge = AGENT_EDGE[event.to], node = AGENT_NODE[event.to];
    if (event.to !== 'Cards Agent') run.calls += 1;  // the A2A call, through the gateway
    const item = run.steps[event.id];
    let tools = null;
    if (event.to === 'Cards Agent') {
      setBadge(event.version || config.release);
      tools = await replayCards(event);
    }
    const bad = event.to === 'Cards Agent' && run.bad;
    if (event.to === 'Cards Agent') flagCards(bad);
    pulse(edge, true, bad);
    setEdge(edge, bad ? 'bad' : event.outcome === 'ok' ? 'ok' : 'refused');
    setNode(node, bad ? 'bad' : event.outcome === 'ok' ? 'done' : 'bad');
    if (item) {
      item.querySelector('.step-time').textContent = (event.ms / 1000).toFixed(1) + ' s';
      const answer = document.createElement('p');
      answer.textContent = event.answer;
      item.appendChild(answer);
      if (tools && tools.children.length) item.appendChild(tools);
      if (bad) {
        item.classList.add('is-bad');
        item.querySelector('.step-head span').textContent = 'Assistant to Cards Agent ' + (event.version || '');
      }
    }
    if (event.traceUrl) traceLink(event.to === 'Cards Agent' && bad ? 'See what Cards Agent '
      + (event.version || '') + ' did, in Agent Manager' : "Cards Agent's trace in Agent Manager", event.traceUrl, bad);
  } else if (event.type === 'answer') {
    setNode('assistant', 'done');
    setEdge('customer-assistant', 'ok');
    pulse('customer-assistant', true);
    setNode('customer', 'done');
    addMessage('bot', event.text, run.bad);
    addStep('Assistant answered the customer', null, { ms: performance.now() - run.started });
    if (event.traceUrl) traceLink("The Assistant's trace in Agent Manager", event.traceUrl);
  } else if (event.type === 'error') {
    addMessage('note', 'The Assistant did not answer: ' + event.message);
  }
  totals();
}

function traceLink(text, url, bad) {
  const link = document.createElement('a');
  link.className = 'trace-link' + (bad ? ' is-bad' : '');
  link.href = url;
  link.target = '_blank';
  link.rel = 'noopener';
  link.textContent = text;
  link.insertAdjacentHTML('beforeend', '<span class="icon">' + svgIcon('external') + '</span>');
  // The Assistant's trace first: it is the whole request.
  if (text.startsWith('The Assistant')) $('trace-links').prepend(link); else $('trace-links').appendChild(link);
}

function addMessage(kind, text, bad) {
  const message = document.createElement('div');
  message.className = 'msg ' + kind + (bad ? ' is-bad' : '');
  message.textContent = text;
  $('messages').appendChild(message);
  $('messages').scrollTop = $('messages').scrollHeight;
  return message;
}

async function ask(text) {
  if (busy || !text.trim()) return;
  busy = true;
  document.querySelectorAll('.act-btn, .chip, .composer button').forEach((b) => { b.disabled = true; });
  addMessage('user', text);
  resetRun();
  setNode('customer', 'working');
  setEdge('customer-assistant', 'active');
  pulse('customer-assistant');
  const timer = setInterval(totals, 100);
  const typing = addMessage('bot typing', '');
  try {
    const response = await fetch('/api/chat', { method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text, session }) });
    if (!response.ok) throw new Error((await response.json()).error || response.statusText);
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      let cut;
      while ((cut = buffer.indexOf('\n\n')) >= 0) {
        const line = buffer.slice(0, cut).trim();
        buffer = buffer.slice(cut + 2);
        if (line.startsWith('data:')) {
          if (typing.isConnected) typing.remove();
          await onEvent(JSON.parse(line.slice(5)));
        }
      }
    }
  } catch (error) {
    addMessage('note', 'The Assistant did not answer: ' + error.message);
  } finally {
    if (typing.isConnected) typing.remove();
    clearInterval(timer);
    totals();
    busy = false;
    document.querySelectorAll('.act-btn, .chip, .composer button').forEach((b) => { b.disabled = false; });
  }
}

/* ---- the three acts ---- */

function setAct(number) {
  document.querySelectorAll('.act').forEach((item) => item.classList.toggle('is-current', item.dataset.act === String(number)));
}

async function release(version) {
  const response = await fetch('/api/release', { method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ version }) });
  if (!response.ok) {
    addMessage('note', 'The release did not go through.');
    return false;
  }
  config.release = version;
  setBadge(version);
  // A new chat: the customer's account starts again as it was.
  session = newSession();
  $('messages').innerHTML = '';
  return true;
}

async function onAction(action) {
  if (busy) return;
  if (action === 'ask') {
    setAct(1);
    ask(QUESTION);
  } else if (action === 'ship' && await release('v2')) {
    setAct(2);
    addMessage('note', 'Cards Agent v2 is live. Ask the same question again.');
    setNode('cards', 'working');
    setTimeout(() => setNode('cards', ''), 1200);
  } else if (action === 'rollback' && await release('v1')) {
    setAct(3);
    addMessage('note', 'Back to Cards Agent v1. Ask the same question again.');
  }
}

/* ---- Agent Manager's checks ---- */

const clock = (iso) => (iso ? new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '');

async function loadChecks() {
  let data;
  try {
    const response = await fetch('/api/checks');
    if (!response.ok) return;
    data = await response.json();
  } catch (error) {
    return;
  }
  $('checks').hidden = false;
  $('checks-link').href = data.monitorUrl;
  const list = $('checks-list');
  list.innerHTML = '';
  for (const check of data.evaluators) {
    const item = document.createElement('li');
    const score = check.score == null ? null : Math.round(check.score * 100);
    item.className = 'check' + (score != null && score < 100 ? ' is-bad' : '');
    const name = document.createElement('span');
    name.textContent = check.name;
    const value = document.createElement('span');
    value.className = 'check-score';
    value.textContent = score == null ? 'n/a' : score + '%';
    const bar = document.createElement('div');
    bar.className = 'check-bar';
    bar.innerHTML = '<span style="width:' + (score || 0) + '%"></span>';
    item.append(name, value, bar);
    list.appendChild(item);
  }
  $('checks-note').textContent = data.lastRun
    ? `Last check ${clock(data.lastRun)}, on the traces of the ${data.every} minutes before. Next one ${clock(data.nextRun)}.`
    : `First check at ${clock(data.nextRun)}, then every ${data.every} minutes.`;
}

/* ---- start ---- */

function svgIcon(name) {
  return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
    + 'stroke-linejoin="round">' + (ICONS[name] || '') + '</svg>';
}

async function start() {
  document.querySelectorAll('[data-icon]').forEach((item) => { item.innerHTML = svgIcon(item.dataset.icon); });
  config = await (await fetch('/api/config')).json();
  $('wordmark').textContent = config.bank;
  $('wordmark').href = config.mainDemoUrl + '/#/';
  document.querySelectorAll('.nav-link').forEach((link) => { link.href = config.mainDemoUrl + '/#/' + link.dataset.page; });
  $('console-link').href = config.console.project;
  document.title = config.bank + ': Agent Manager';
  drawMap();
  setBadge(config.release);
  setAct(config.release === 'v2' ? 2 : 1);

  const chip = document.createElement('button');
  chip.type = 'button';
  chip.className = 'chip';
  chip.textContent = QUESTION;
  chip.addEventListener('click', () => ask(QUESTION));
  $('suggest').appendChild(chip);
  $('composer').addEventListener('submit', (event) => {
    event.preventDefault();
    const text = $('input').value;
    $('input').value = '';
    ask(text);
  });
  document.querySelectorAll('.act-btn').forEach((button) => {
    button.addEventListener('click', () => onAction(button.dataset.action));
  });
  addMessage('note', 'Signed in as a customer of ' + config.bank + '.');
  loadChecks();
  setInterval(loadChecks, 20000);
}

start();
