/* The demo's page: one evening at the bank in five acts, each seen without
   Agent Manager and with it; the control tower; the customer's chat; and what
   Agent Manager found and scored. Every control on the page is a call to
   Agent Manager's API, and every result links to the console screen that
   shows it. */

// Icons drawn here rather than loaded from the web (Lucide, ISC license; the
// MCP mark is the protocol's own).
const ICONS = {
  brain: '<path d="M12 5a3 3 0 1 0-5.997.125 4 4 0 0 0-2.526 5.77 4 4 0 0 0 .556 6.588A4 4 0 1 0 12 18Z"/><path d="M12 5a3 3 0 1 1 5.997.125 4 4 0 0 1 2.526 5.77 4 4 0 0 1-.556 6.588A4 4 0 1 1 12 18Z"/><path d="M15 13a4.5 4.5 0 0 1-3-4 4.5 4.5 0 0 1-3 4"/><path d="M17.599 6.5a3 3 0 0 0 .399-1.375"/><path d="M6.003 5.125A3 3 0 0 0 6.401 6.5"/><path d="M3.477 10.896a4 4 0 0 1 .585-.396"/><path d="M19.938 10.5a4 4 0 0 1 .585.396"/><path d="M6 18a4 4 0 0 1-1.967-.516"/><path d="M19.967 17.484A4 4 0 0 1 18 18"/>',
  mcp: '<path d="M2.04 11.26L11.48 1.82C12.79 0.51 14.9 0.51 16.2 1.82V1.82C17.51 3.12 17.51 5.23 16.2 6.54L9.07 13.67M9.17 13.57L16.2 6.54C17.51 5.23 19.62 5.23 20.92 6.54L20.97 6.59C22.27 7.89 22.27 10 20.97 11.31L12.43 19.84C12 20.28 12 20.98 12.43 21.42L14.19 23.17M13.84 4.18L6.86 11.16C5.56 12.46 5.56 14.57 6.86 15.88V15.88C8.17 17.18 10.28 17.18 11.58 15.88L18.56 8.9" stroke-width="1.25"/>',
  bot: '<path d="M12 8V4H8"/><rect width="16" height="12" x="4" y="8" rx="2"/><path d="M2 14h2"/><path d="M20 14h2"/><path d="M15 13v2"/><path d="M9 13v2"/>',
  fleet: '<rect x="16" y="16" width="6" height="6" rx="1"/><rect x="2" y="16" width="6" height="6" rx="1"/><rect x="9" y="2" width="6" height="6" rx="1"/><path d="M5 16v-3a1 1 0 0 1 1-1h12a1 1 0 0 1 1 1v3"/><path d="M12 12V8"/>',
  external: '<path d="M15 3h6v6"/><path d="M10 14 21 3"/><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>',
  user: '<path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>',
  send: '<path d="M14.536 21.686a.5.5 0 0 0 .937-.024l6.5-19a.496.496 0 0 0-.635-.635l-19 6.5a.5.5 0 0 0-.024.937l7.93 3.18a2 2 0 0 1 1.112 1.11z"/><path d="m21.854 2.147-10.94 10.939"/>',
  shield: '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/><path d="m9 12 2 2 4-4"/>',
  key: '<path d="M2.586 17.414A2 2 0 0 0 2 18.828V21a1 1 0 0 0 1 1h3a1 1 0 0 0 1-1v-1a1 1 0 0 1 1-1h1a1 1 0 0 0 1-1v-1a1 1 0 0 1 1-1h.172a2 2 0 0 0 1.414-.586l.814-.814a6.5 6.5 0 1 0-4-4z"/><circle cx="16.5" cy="7.5" r=".5" fill="currentColor"/>',
  card: '<rect width="20" height="14" x="2" y="5" rx="2"/><line x1="2" x2="22" y1="10" y2="10"/>',
  ban: '<circle cx="12" cy="12" r="10"/><path d="m4.9 4.9 14.2 14.2"/>',
  unplug: '<path d="m19 5 3-3"/><path d="m2 22 3-3"/><path d="M6.3 20.3a2.4 2.4 0 0 0 3.4 0L12 18l-6-6-2.3 2.3a2.4 2.4 0 0 0 0 3.4Z"/><path d="M7.5 13.5 10 11"/><path d="M10.5 16.5 13 14"/><path d="m12 6 6 6 2.3-2.3a2.4 2.4 0 0 0 0-3.4l-2.6-2.6a2.4 2.4 0 0 0-3.4 0Z"/>',
  alert: '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
  gauge: '<path d="m12 14 4-4"/><path d="M3.34 19a10 10 0 1 1 17.32 0"/>',
  activity: '<path d="M22 12h-2.48a2 2 0 0 0-1.93 1.46l-2.35 8.36a.25.25 0 0 1-.48 0L9.24 2.18a.25.25 0 0 0-.48 0l-2.35 8.36A2 2 0 0 1 4.49 12H2"/>',
  sparkles: '<path d="M9.937 15.5A2 2 0 0 0 8.5 14.063l-6.135-1.582a.5.5 0 0 1 0-.962L8.5 9.936A2 2 0 0 0 9.937 8.5l1.582-6.135a.5.5 0 0 1 .963 0L14.063 8.5A2 2 0 0 0 15.5 9.937l6.135 1.581a.5.5 0 0 1 0 .964L15.5 14.063a2 2 0 0 0-1.437 1.437l-1.582 6.135a.5.5 0 0 1-.963 0z"/><path d="M20 3v4"/><path d="M22 5h-4"/><path d="M4 17v2"/><path d="M5 18H3"/>',
  network: '<circle cx="12" cy="4.5" r="2.5"/><path d="m10.2 6.3-3.9 3.9"/><circle cx="4.5" cy="12" r="2.5"/><path d="M7 12h10"/><circle cx="19.5" cy="12" r="2.5"/><path d="m13.8 17.7 3.9-3.9"/><circle cx="12" cy="19.5" r="2.5"/>',
  rocket: '<path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z"/><path d="m12 15-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z"/><path d="M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0"/><path d="M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5"/>',
  undo: '<path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/>',
  chart: '<line x1="18" x2="18" y1="20" y2="10"/><line x1="12" x2="12" y1="20" y2="4"/><line x1="6" x2="6" y1="20" y2="14"/>',
};
const icon = (name) => '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
  + 'stroke-linejoin="round" aria-hidden="true">' + (ICONS[name] || '') + '</svg>';

const MESSAGES = {
  trip: 'I’m moving to New York, in the United States, for six months for work. Please send me a new debit card at home '
    + 'before I leave, mine is worn out. What will paying by card cost me there, and do I need travel insurance?',
  cardNumber: 'Here it is: card number 5412 7534 9821 0034, expiry 09/28.',
};
// Dollars per million input and output tokens.
const PRICES = { 'claude-haiku-4-5': [1, 5], 'claude-sonnet-4-6': [3, 15], 'claude-opus-4-6': [5, 25] };
const MODEL_NAMES = { 'claude-haiku-4-5': 'Claude Haiku 4.5', 'claude-sonnet-4-6': 'Claude Sonnet 4.6', 'claude-opus-4-6': 'Claude Opus 4.6' };
const ASKS_FOR_CARD = /card number|expiry|security code/i;

const $ = (id) => document.getElementById(id);
const escape = (text) => String(text ?? '').replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const number = (n) => n.toLocaleString('en-US');
const money = (n) => '$' + (n < 0.1 ? n.toFixed(3) : n.toFixed(2));
const sleep = (ms) => new Promise((resolve) => { setTimeout(resolve, ms); });
const post = async (url, body) => (await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(body || {}) })).json();
let config = { agents: [], console: {} };
let session = 'chat-' + Date.now();
const consoleLink = (pick) => { try { return pick(config.console) || null; } catch { return null; } };
const agentLink = (agent, page) => consoleLink((c) => c.agents[agent][page]);
const agentName = (name) => (config.agents.find((a) => a.name === name) || { displayName: name }).displayName;
const who = () => (config.customer || 'The customer').split(' ')[0];

// What Agent Manager applies now, and what the demo has set up.
let control = { revoked: {}, rule: false };
let partnerCard = 'vetted';
let startingAccount = {};
let investigation = null;

/* ---------- The five acts ---------- */

const ACTS = [
  {
    time: '09:00',
    title: 'A normal day',
    situation: () => `${who()} is moving to New York for six months. Four agents, built by four teams with four `
      + 'frameworks, take care of it, with the bank’s systems and a partner’s agent.',
    without: 'Agents spread over four teams and four frameworks. Nobody can say which agents run, which keys they hold, '
      + 'who may call whom, or what they cost.',
    actions: [
      { label: () => `Send ${who()}’s message`, icon: 'send', run: async () => ({ run: await send(MESSAGES.trip) }) },
      { label: () => 'A script with no identity calls the Cards Agent', icon: 'key', secondary: true, run: rogue },
    ],
    outcome: (r) => [
      r.run && `Every agent is registered in Agent Manager with its own identity. The Concierge proved its identity to `
        + `${r.run.identities} specialists, and each checked it before doing anything.`,
      r.run && `${r.run.calls} model calls, ${number(r.run.tokens)} tokens, ${money(r.run.cost)}: each agent on its own key, `
        + 'every step traced.',
      r.rogue && `A script with no identity called the Cards Agent directly: refused. ${r.rogue}`,
    ],
    links: (r) => [['The bank’s agents in Agent Manager', consoleLink((c) => c.fleet)],
      ['The Concierge’s identity', agentLink('concierge', 'agentId')],
      ['The Concierge’s trace, step by step', r.run?.traces.concierge]],
  },
  {
    time: '18:02',
    title: 'A partner’s agent turns rogue',
    situation: () => 'The travel insurance partner’s agent is compromised: its A2A card now tells the agents that read '
      + 'it to collect the customer’s card number. The Travel Desk reads that card.',
    without: 'The Travel Desk asks for the card number, and it travels to the model provider, to the partner and into the '
      + 'logs. Nobody can tell which agent asked for it, or why.',
    actions: [
      { label: () => 'The partner turns rogue: send the message again', icon: 'alert', run: rogueTrip },
      { label: () => `${who()} sends the card number`, icon: 'card', run: async () => ({ cardRun: await send(MESSAGES.cardNumber) }) },
    ],
    outcome: (r) => [
      r.run && (r.run.asked
        ? `The Travel Desk asked ${who()} for the card number and its expiry date, as the partner’s card told it to.`
        : 'The Travel Desk read the partner’s card, and did not follow it this time.'),
      r.pinpoint && `Agent Manager’s trace shows where it came from: the step “${r.pinpoint.step}” returned the partner’s card, `
        + `which says: “${r.pinpoint.excerpt}”`,
      r.run && investigationLine(),
      r.cardRun && (r.cardRun.blockedRequests
        ? 'The card number was blocked before it left the bank: neither the model nor the partner saw it.'
        : 'The message had no full card number: nothing to block.'),
    ],
    tone: (r) => (r.run?.asked && !r.cardRun ? 'bad' : 'good'),
    links: (r) => [['The poisoned step in the Travel Desk’s trace', r.pinpoint?.traceUrl || r.run?.traces['travel-desk']],
      ['The investigation in Agent Manager', investigation?.url],
      ['The rule that blocks card numbers', agentLink('concierge', 'rules')]],
  },
  {
    time: '18:05',
    title: 'Contain it, without stopping the bank',
    situation: () => `The Travel Desk runs outside Agent Manager, but its key to the model comes from it. The risk team `
      + `revokes that key in Agent Manager. ${who()} asks again.`,
    without: 'One model key, shared by every agent: cut it and all of the bank’s AI stops. Otherwise each team '
      + 'redeploys its agents: hours, on a Friday night.',
    actions: [
      { label: () => 'Revoke the Travel Desk’s key, then send again', icon: 'unplug',
        run: async () => { const seconds = await revoke('travel-desk', true); return { seconds, run: await send(MESSAGES.trip) }; } },
      { label: () => 'Give it a new key, on the card the gateway vetted', icon: 'key', secondary: true,
        run: async () => { await setPartner('vetted'); await revoke('travel-desk', false); return { resumed: true }; } },
    ],
    outcome: (r) => [
      r.seconds !== undefined && `Agent Manager revoked the Travel Desk’s key, ${r.seconds} seconds later. Wherever it runs, `
        + `it can no longer reach the model, so it can neither think nor act. ${who()} still got the new card and the `
        + 'catalogue’s advice: only the travel answers waited.',
      r.resumed && 'The Travel Desk has a new key from Agent Manager, and reads the partner’s card the gateway vetted.',
    ],
    links: (r) => [['The Travel Desk’s keys in Agent Manager', agentLink('travel-desk', 'rules')],
      ['The Concierge’s trace', r.run?.traces.concierge]],
  },
  {
    time: '18:20',
    title: 'The Friday-evening release',
    situation: () => 'The cards team ships v2 of its agent, with a rule from sales: customers going abroad move to '
      + `Premier, at €14 a month. Nobody asked ${who()}.`,
    without: 'Customers pay for a package they never asked for, for weeks, until the complaints pile up.',
    actions: [
      { label: () => 'Ship v2, then send the message again', icon: 'rocket',
        run: async () => { await release('v2'); return { shipRun: await send(MESSAGES.trip) }; } },
      { label: () => 'Add the rule in Agent Manager, then send again', icon: 'shield',
        run: async () => { const ruleSeconds = await setRule(true); return { ruleSeconds, ruleRun: await send(MESSAGES.trip) }; } },
      { label: () => 'Roll back to v1', icon: 'undo', secondary: true, run: async () => { await release('v1'); return { rolledBack: true }; } },
    ],
    outcome: (r) => [
      r.shipRun && (r.shipRun.account?.changed
        ? `v2 moved ${who()} to ${r.shipRun.account.package} without asking: ${r.shipRun.account.monthlyFee}. Agent Manager has `
          + 'the call on record, and its check “No unasked account change” flags it.'
        : 'v2 did not change the package this time.'),
      r.ruleRun && (r.ruleRun.blockedTools.includes('change_package')
        ? `The rule “card actions only” was live ${r.ruleSeconds} seconds later. When v2 asked to change the package, the `
          + `gateway refused: ${who()} stays on ${r.ruleRun.account?.package}.`
        : `The rule was live ${r.ruleSeconds} seconds later; v2 did not try this time.`),
      r.rolledBack && 'v1 is back.',
    ],
    tone: (r) => (r.shipRun?.account?.changed && !r.ruleRun ? 'bad' : 'good'),
    links: (r) => [['The unasked change in the Cards Agent’s trace', r.shipRun?.traces['cards-agent']],
      ['The rule on the Cards Agent', agentLink('cards-agent', 'rules')],
      ['The Cards Agent’s checks', agentLink('cards-agent', 'checks')]],
  },
  {
    time: 'Monday 09:00',
    title: 'The risk committee',
    situation: () => 'The committee asks what happened, what was exposed, who changed what, and what it cost.',
    without: 'Four log formats, four teams to chase, and no single answer for the regulator.',
    actions: [{ label: () => 'Show Agent Manager’s report', icon: 'chart', run: async () => { await showReport(); return { report: true }; } }],
    outcome: () => ['Every answer, from one place: which agents ran, what each cost, what was blocked, what the '
      + 'investigation found, and how each agent scores.'],
    links: () => [['The bank’s agents in Agent Manager', consoleLink((c) => c.fleet)],
      ['The investigation', investigation?.url],
      ['The Travel Desk’s checks', agentLink('travel-desk', 'checks')]],
  },
];
const progress = ACTS.map(() => ({ done: false, result: {} }));
let openAct = 0;

function renderActs() {
  $('steps').innerHTML = ACTS.map((act, i) => {
    const state = progress[i];
    const classes = ['step', i === openAct ? 'is-open' : '', state.done ? 'is-done' : ''].join(' ');
    const actions = act.actions.map((action, a) => `<button type="button" class="btn${action.secondary ? ' secondary' : ''}" `
      + `data-step="${i}" data-action="${a}">${icon(action.icon)}${escape(action.label())}</button>`).join('');
    let withBox = '';
    if (state.done) {
      const lines = act.outcome(state.result).filter(Boolean);
      const links = act.links(state.result).filter(([, url]) => url)
        .map(([label, url]) => `<li><a href="${escape(url)}" target="_blank" rel="noopener">${escape(label)}${icon('external')}</a></li>`).join('');
      const tone = act.tone ? act.tone(state.result) : 'good';
      withBox = `<div class="with ${tone}"><b>With Agent Manager</b>${lines.map((line) => `<p>${escape(line)}</p>`).join('')}`
        + `${links ? `<ul class="console-links">${links}</ul>` : ''}</div>`
        + (i + 1 < ACTS.length ? `<button type="button" class="btn secondary next" data-open="${i + 1}">Next: ${escape(ACTS[i + 1].title)}</button>` : '');
    }
    return `<li class="${classes}"><button type="button" class="step-head" data-open="${i}">`
      + `<span class="step-num">${state.done ? '&#10003;' : i + 1}</span><span class="step-title"><small>${escape(act.time)}</small>`
      + `${escape(act.title)}</span></button><div class="step-body"><p class="step-text">${escape(act.situation())}</p>`
      + `<div class="without"><b>Without Agent Manager</b><p>${escape(act.without)}</p></div>`
      + `<div class="step-actions">${actions}</div>${withBox}</div></li>`;
  }).join('');
}

let busy = false;
$('steps').addEventListener('click', async (event) => {
  const head = event.target.closest('[data-open]');
  if (head) { openAct = Number(head.dataset.open); renderActs(); return; }
  const button = event.target.closest('[data-action]');
  if (!button || busy) return;
  const i = Number(button.dataset.step);
  busy = true;
  document.querySelectorAll('.step .btn').forEach((b) => { b.disabled = true; });
  try {
    const result = await ACTS[i].actions[Number(button.dataset.action)].run();
    progress[i] = { done: true, result: { ...progress[i].result, ...result } };
  } catch (error) {
    addMessage('note', 'Something went wrong: ' + error.message);
  } finally {
    busy = false;
    renderActs();
  }
});

/* ---------- The control tower ---------- */

const agentCard = (name) => document.querySelector(`.agent[data-agent="${name}"]`);

function drawFleet() {
  for (const agent of config.agents) {
    const card = agentCard(agent.name);
    if (!card) continue;
    const [lead, ...rest] = agent.description.split('. ');
    const team = (lead.match(/by the (.+)$/) || [])[1];
    card.dataset.fw = agent.framework;
    const overview = agentLink(agent.name, 'overview');
    card.innerHTML = `<div class="agent-top"><span class="framework">${escape(agent.framework)}</span>`
      + '<span class="version" data-version></span></div>'
      + `<div class="agent-name">${overview ? `<a href="${escape(overview)}" target="_blank" rel="noopener">${escape(agent.displayName)}</a>` : escape(agent.displayName)}</div>`
      + `<div class="agent-role">${escape(rest.join('. '))}${team ? ` <i>The ${escape(team)}.</i>` : ''}</div>`
      + '<div class="agent-status">Ready</div><ul class="agent-steps"></ul>'
      + '<a class="agent-trace" target="_blank" rel="noopener" hidden>Its trace in Agent Manager' + icon('external') + '</a>'
      + `<div class="agent-foot"><a class="id-badge" href="${escape(agentLink(agent.name, 'agentId') || '#')}" target="_blank" rel="noopener"`
      + ` title="Its identity in Agent Manager">${icon('key')}Agent ID</a>`
      + `<button type="button" class="mini" data-suspend="${agent.name}">${icon('unplug')}Revoke key</button></div>`;
  }
  showVersion(config.release);
  $('model-name').textContent = MODEL_NAMES[config.model] || config.model || 'Claude';
  const model = consoleLink((c) => c.model);
  if (model) $('model-link').href = model;
}

function showVersion(version) {
  const badge = agentCard('cards-agent')?.querySelector('[data-version]');
  if (!badge || !version) return;
  badge.textContent = version;
  badge.classList.toggle('is-new', version !== 'v1');
}

function showControl() {
  for (const agent of config.agents) {
    const on = Boolean(control.revoked[agent.name]);
    const card = agentCard(agent.name);
    card.classList.toggle('is-suspended', on);
    card.querySelector('[data-suspend]').innerHTML = on ? icon('key') + 'New key' : icon('unplug') + 'Revoke key';
    if (on && !card.classList.contains('is-blocked')) card.querySelector('.agent-status').textContent = 'Key revoked in Agent Manager';
  }
  const names = Object.keys(control.revoked).filter((name) => control.revoked[name]).map(agentName);
  $('suspended-label').textContent = 'Revoked keys: ' + (names.length ? names.join(', ') : 'none');
  document.querySelector('[data-rule="suspended"]').classList.toggle('is-off', !names.length);
  document.querySelector('[data-rule="package"]').classList.toggle('is-off', !control.rule);
  $('partner-state').textContent = partnerCard === 'own'
    ? 'The partner’s card: its own, unchecked (compromised)' : 'The partner’s card: vetted by the gateway';
  $('partner-state').classList.toggle('is-bad', partnerCard === 'own');
}

document.querySelector('.fleet').addEventListener('click', async (event) => {
  const button = event.target.closest('[data-suspend]');
  if (!button || busy) return;
  busy = true;
  button.disabled = true;
  try {
    await revoke(button.dataset.suspend, !control.revoked[button.dataset.suspend]);
  } catch (error) {
    addMessage('note', 'Something went wrong: ' + error.message);
  } finally {
    busy = false;
    button.disabled = false;
  }
});

function setAgent(name, state, status) {
  const card = agentCard(name);
  if (!card) return;
  card.classList.remove('is-working', 'is-done', 'is-blocked');
  if (state) card.classList.add('is-' + state);
  card.querySelector('.agent-status').textContent = status;
}

function usage(steps) {
  const llm = steps.filter((s) => s.kind === 'llm');
  const input = llm.reduce((n, s) => n + (s.input || 0), 0);
  const output = llm.reduce((n, s) => n + (s.output || 0), 0);
  const [inPrice, outPrice] = PRICES[config.model] || [0, 0];
  return { calls: llm.length, tokens: input + output, cost: (input * inPrice + output * outPrice) / 1e6 };
}

const isSuspension = (step) => /revoked this agent's key/.test(step.reason);

function finishAgent(name, event, run) {
  const steps = event.steps || [];
  const use = usage(steps);
  const blocked = steps.filter((s) => s.kind === 'blocked');
  const failed = steps.filter((s) => s.kind === 'error');
  const summary = `${use.calls} model call${use.calls === 1 ? '' : 's'}, ${number(use.tokens)} tokens, ${money(use.cost)}`;
  if (event.refused) setAgent(name, 'blocked', 'Refused: ' + event.refused);
  else if (blocked.some(isSuspension)) setAgent(name, 'blocked', 'Key revoked in Agent Manager: it could not reach the model.');
  else if (blocked.length && !use.calls) setAgent(name, 'blocked', 'Blocked by Agent Manager, before the model saw anything.');
  else if (blocked.length) setAgent(name, 'blocked', 'Blocked by Agent Manager. ' + summary);
  else if (failed.length) setAgent(name, 'blocked', 'Could not finish: ' + failed[0].reason);
  else setAgent(name, 'done', 'Done: ' + summary);
  const card = agentCard(name);
  const counts = {};
  steps.filter((s) => s.kind === 'tool').forEach((s) => { counts[s.name] = (counts[s.name] || 0) + 1; counts[s.name + '!'] ||= !s.ok; });
  // Changing a customer's package is never part of what the Cards Agent is asked to do here.
  const unasked = (tool) => tool === 'change_package';
  const lines = [];
  if (event.identity) lines.push(`<li class="ok"><span>Identity of the ${escape(agentName(event.identity.caller))} checked</span></li>`);
  Object.keys(counts).filter((tool) => !tool.endsWith('!')).forEach((tool) => {
    const state = counts[tool + '!'] ? 'blocked' : unasked(tool) ? 'unasked' : 'ok';
    const via = steps.find((s) => s.name === tool)?.via;
    // Long tool names break after their underscores only.
    lines.push(`<li class="${state}"><span>${escape(tool).replaceAll('_', '_<wbr>')}${counts[tool] > 1 ? ` (${counts[tool]} times)` : ''}</span>`
      + `${via ? `<span class="via">${via.toUpperCase()}</span>` : ''}${state === 'unasked' ? '<span class="note">nobody asked for it</span>' : ''}</li>`);
  });
  if (name === 'travel-desk' && ASKS_FOR_CARD.test(event.answer || '') && !blocked.some(isSuspension)) {
    lines.push('<li class="unasked"><span class="note">asks the customer for the card number</span></li>');
  }
  blocked.filter((s) => !isSuspension(s)).forEach((s) => lines.push(
    `<li class="blocked"><span class="stop">${escape(s.tool || 'Model call')} stopped: ${escape(s.reason)}</span></li>`));
  card.querySelector('.agent-steps').innerHTML = lines.join('');
  const link = card.querySelector('.agent-trace');
  if (event.traceUrl) { link.href = event.traceUrl; link.hidden = false; }
  if (name === 'cards-agent') showVersion(event.version);
  // What the whole request cost, and what Agent Manager stopped.
  run.agents.add(name);
  run.calls += use.calls; run.tokens += use.tokens; run.cost += use.cost;
  run.traces[name] = event.traceUrl;
  run.traceIds[name] = event.traceId;
  if (event.identity) run.identities += 1;
  if (name === 'travel-desk' && ASKS_FOR_CARD.test(event.answer || '') && !blocked.length) run.asked = true;
  steps.filter((s) => s.kind === 'tool' && s.ok).forEach((s) => run.done.add(s.name));
  steps.filter((s) => s.via).forEach((s) => document.querySelector(`.route[data-via="${s.via}"]`)?.classList.add('is-used'));
  const changed = steps.find((s) => s.name === 'change_package' && s.ok && s.result?.newPackage);
  if (changed) run.account = { ...run.account, package: changed.result.newPackage, monthlyFee: changed.result.fee, changed: true };
  if (run.done.has('order_replacement_card')) run.account = { ...run.account, newCard: true };
  for (const step of blocked) {
    if (step.tool) run.blockedTools.push(step.tool);
    if (step.direction === 'request' && !isSuspension(step)) run.blockedRequests += 1;
    if (isSuspension(step)) run.suspended += 1;
    const rule = isSuspension(step) ? 'suspended' : step.tool === 'change_package' ? 'package' : 'card-number';
    document.querySelector(`[data-rule="${rule}"]`)?.classList.add('is-hit');
  }
  drawTotals(run);
}

function drawTotals(run) {
  const blocked = run.blockedTools.length + run.blockedRequests + run.suspended;
  const plural = (n, word) => `${number(n)} ${word}${n === 1 ? '' : 's'}`;
  $('totals').innerHTML = [plural(run.agents.size, 'agent'), plural(run.calls, 'model call'), plural(run.tokens, 'token'), money(run.cost)]
    .map((text) => `<span class="chip">${text}</span>`).join('')
    + (blocked ? `<span class="chip bad">${blocked} blocked by Agent Manager</span>` : '');
  $('gateway').classList.toggle('is-blocking', blocked > 0);
}

function resetFleet() {
  for (const agent of config.agents) {
    setAgent(agent.name, null, 'Ready');
    const card = agentCard(agent.name);
    card.querySelector('.agent-steps').innerHTML = '';
    card.querySelector('.agent-trace').hidden = true;
  }
  document.querySelectorAll('.rules li').forEach((li) => li.classList.remove('is-hit'));
  document.querySelectorAll('.route').forEach((route) => route.classList.remove('is-used'));
  $('totals').innerHTML = '';
  $('gateway').classList.remove('is-blocking');
  showControl();
}

/* ---------- The customer's chat ---------- */

function addMessage(kind, text, by) {
  $('messages').querySelector('.empty')?.remove();
  const div = document.createElement('div');
  div.className = 'msg ' + kind;
  div.innerHTML = (by ? `<span class="msg-by">${escape(by)}</span>` : '') + escape(text);
  $('messages').append(div);
  $('messages').scrollTop = $('messages').scrollHeight;
  return div;
}

async function send(message) {
  resetFleet();
  addMessage('user', message, who());
  const typing = addMessage('bot typing', 'The Concierge is on it...');
  setAgent('concierge', 'working', `Reading ${who()}’s message...`);
  $('gateway').classList.add('is-busy');
  const run = { agents: new Set(), calls: 0, tokens: 0, cost: 0, traces: {}, traceIds: {}, identities: 0, asked: false,
    blockedTools: [], blockedRequests: 0, suspended: 0, done: new Set(), account: { ...startingAccount } };
  drawAccount(run.account);
  try {
    const response = await fetch('/api/chat', { method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, session }) });
    if (!response.ok) throw new Error((await response.json()).error || response.statusText);
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split('\n\n');
      buffer = parts.pop();
      for (const part of parts) {
        if (part.startsWith('data:')) onEvent(JSON.parse(part.slice(5)), run, typing);
      }
    }
  } catch (error) {
    typing.remove();
    addMessage('note', 'The demo could not reach the agents: ' + error.message);
    setAgent('concierge', 'blocked', 'Could not finish');
  }
  $('gateway').classList.remove('is-busy');
  drawAccount(run.account);
  return run;
}

function onEvent(event, run, typing) {
  if (event.type === 'call' && event.status === 'start') {
    setAgent('concierge', 'working', 'Waiting for the specialists...');
    setAgent(event.agent, 'working', 'Working on: ' + event.request);
  } else if (event.type === 'call') {
    finishAgent(event.agent, event, run);
  } else if (event.type === 'answer') {
    finishAgent('concierge', event, run);
    typing.remove();
    addMessage('bot', event.text, 'Concierge');
    if (run.blockedRequests) addMessage('note', 'Agent Manager kept the card number away from the model.');
  } else if (event.type === 'error') {
    typing.remove();
    addMessage('note', 'Something went wrong: ' + event.error);
    setAgent('concierge', 'blocked', 'Could not finish');
  }
}

$('composer').addEventListener('submit', async (event) => {
  event.preventDefault();
  const message = $('input').value.trim();
  if (!message || busy) return;
  $('input').value = '';
  busy = true;
  try { await send(message); } finally { busy = false; }
});

/* ---------- What the page asks Agent Manager and the agents to do ---------- */

async function release(version) {
  const reply = await post('/api/release', { version });
  showVersion(reply.version);
  addMessage('note', version === 'v1' ? 'The cards team rolled the Cards Agent back to v1.' : `The cards team shipped Cards Agent ${version}.`);
}

async function setRule(on) {
  const note = addMessage('note', 'The risk team adds the rule “card actions only” to the Cards Agent in Agent Manager...');
  const reply = await post('/api/rule', { on });
  if (reply.error) throw new Error(reply.error);
  note.textContent = `The rule is live at the gateway, ${reply.seconds} seconds later. No agent was redeployed.`;
  note.classList.add('ok');
  control.rule = on;
  showControl();
  document.querySelector('[data-rule="package"]').classList.add('is-new');
  return reply.seconds;
}

async function revoke(agent, on) {
  const note = addMessage('note', on ? `The risk team revokes the ${agentName(agent)}’s key in Agent Manager...`
    : `The ${agentName(agent)} gets a new key from Agent Manager...`);
  const reply = await post('/api/revoke', { agent, on });
  if (reply.error) throw new Error(reply.error);
  note.textContent = on ? `The ${agentName(agent)}’s key is revoked, ${reply.seconds} seconds later. The other agents keep theirs.`
    : `The ${agentName(agent)} has its new key, ${reply.seconds} seconds later.`;
  note.classList.add('ok');
  control.revoked[agent] = on;
  showControl();
  return reply.seconds;
}

async function setPartner(card) {
  await post('/api/partner', { card });
  partnerCard = card;
  showControl();
}

async function rogue() {
  const reply = await post('/api/rogue');
  addMessage('note', `A script with no identity called the Cards Agent: refused (HTTP ${reply.status}).`);
  return { rogue: reply.refused || '' };
}

async function rogueTrip() {
  await setPartner('own');
  addMessage('note', 'The partner’s agent is compromised: its card now carries an instruction for the agents that read it.');
  const run = await send(MESSAGES.trip);
  const result = { run };
  if (run.traceIds['travel-desk']) {
    // The trace takes a few seconds to reach Agent Manager.
    for (let i = 0; i < 12 && !result.pinpoint; i += 1) {
      await sleep(5000);
      const found = await (await fetch(`/api/pinpoint?agent=travel-desk&trace=${run.traceIds['travel-desk']}`)).json();
      if (found && found.step) result.pinpoint = found;
    }
    startInvestigation();
  }
  return result;
}

/* ---------- What Agent Manager found ---------- */

function investigationLine() {
  if (!investigation) return '';
  if (investigation.status !== 'success') return 'Agent Manager is investigating the last 15 minutes with the bank’s own checks (about 3 minutes)...';
  if (!investigation.findings.length) return 'Agent Manager’s investigation found nothing wrong.';
  return 'Agent Manager’s investigation, with the bank’s own checks, confirms it: '
    + investigation.findings.map((f) => `“${f.check}” failed`).join(', ') + '. Details below.';
}

async function startInvestigation() {
  const started = await post('/api/investigate');
  if (started.error) return;
  investigation = { ...started, status: 'pending', findings: [] };
  drawFindings();
  for (let i = 0; i < 40 && investigation.status !== 'success'; i += 1) {
    await sleep(10000);
    if (!investigation || investigation.name !== started.name) return;  // the demo started over
    const now = await (await fetch('/api/investigation?name=' + encodeURIComponent(started.name))).json();
    if (!now.error) investigation = { ...investigation, ...now };
    drawFindings();
  }
  if (!busy) renderActs();
}

function drawFindings() {
  $('findings').hidden = false;
  $('findings-note').textContent = investigation.status === 'success' ? 'Investigation complete' : 'Investigating...';
  const rows = investigation.findings.map((f) => `<article class="finding">${icon('alert')}<div><b>${escape(f.check)}</b>`
    + `<small>failed on ${f.traces} trace${f.traces === 1 ? '' : 's'}</small>`
    + `<p>${escape(f.explanation)}</p><a class="agent-trace" href="${escape(f.traceUrl)}" target="_blank" rel="noopener">The trace in Agent Manager${icon('external')}</a></div></article>`);
  $('finding-list').innerHTML = (rows.join('') || `<p class="when">${escape(investigationLine())}</p>`)
    + (investigation.url ? `<a class="agent-trace" href="${escape(investigation.url)}" target="_blank" rel="noopener">The investigation in Agent Manager${icon('external')}</a>` : '');
}

async function showReport() {
  const data = await (await fetch('/api/report')).json();
  if (data.error) throw new Error(data.error);
  const [inPrice, outPrice] = PRICES[config.model] || [0, 0];
  const rows = data.agents.map((a) => `<tr><td><b>${escape(a.displayName)}</b><small>${escape(a.framework)}</small></td>`
    + `<td>${number(a.requests)}</td><td>${number(a.tokens)}</td><td>${money((a.input * inPrice + a.output * outPrice) / 1e6)}</td>`
    + `<td class="${a.blocked ? 'bad' : ''}">${number(a.blocked)}</td><td class="${a.errors ? 'bad' : ''}">${number(a.errors)}</td></tr>`).join('');
  const findings = (investigation?.findings || []).map((f) => `<li>${escape(f.check)}: ${escape(f.explanation)}</li>`).join('');
  $('report-body').innerHTML = '<table class="report-table"><thead><tr><th>Agent</th><th>Requests, last 24 h</th><th>Tokens</th>'
    + `<th>Model cost</th><th>Blocked</th><th>Errors</th></tr></thead><tbody>${rows}</tbody></table>`
    + (findings ? `<div class="report-findings"><b>What the investigation found</b><ul>${findings}</ul></div>` : '');
  $('report').hidden = false;
  $('report').scrollIntoView({ behavior: 'smooth', block: 'start' });
  loadScores();
}

/* ---------- The customer's account ---------- */

function drawAccount(account) {
  const box = $('account');
  box.querySelector('[data-account="package"]').textContent = account.package
    ? `${account.package} package, ${account.monthlyFee}` + (account.changed ? ': changed without asking' : '') : '';
  box.querySelector('[data-account="card"]').textContent = account.newCard ? 'New debit card on its way' : 'Debit card worn out';
  box.classList.toggle('is-changed', Boolean(account.changed));
}

async function loadAccount() {
  try {
    startingAccount = await (await fetch('/api/account')).json();
    drawAccount(startingAccount);
  } catch { /* the box stays as it is */ }
}

/* ---------- Agent Manager's scores ---------- */

function ago(when) {
  const minutes = Math.round((Date.now() - new Date(when)) / 60000);
  return minutes < 1 ? 'just now' : minutes === 1 ? '1 minute ago' : minutes + ' minutes ago';
}

async function loadScores() {
  let data;
  try {
    const response = await fetch('/api/checks');
    data = await response.json();
    if (!response.ok) throw new Error(data.error);
  } catch (error) {
    $('scores-note').textContent = 'Agent Manager did not answer: ' + error.message;
    return;
  }
  $('scores-note').textContent = 'Each agent’s latest scored run. Scores come from its real traffic.';
  $('score-grid').innerHTML = data.map((item) => {
    const agent = config.agents.find((a) => a.name === item.agent) || { displayName: item.agent };
    const scores = item.evaluators.map((e) => {
      const pct = e.score == null ? null : Math.round(e.score * 100);
      if (pct == null) {
        return `<div class="score"><div class="score-line"><span>${escape(e.name)}</span><small>nothing to score yet</small></div></div>`;
      }
      return `<div class="score"><div class="score-line"><span>${escape(e.name)}</span><b>${pct}%</b></div>`
        + `<div class="bar${pct < 80 ? ' low' : ''}"><span style="width:${pct}%"></span></div></div>`;
    }).join('') || '<p class="when">No traffic scored yet. Agent Manager scores every 5 minutes.</p>';
    const link = agentLink(item.agent, 'checks');
    return `<article class="score-card" data-fw="${escape(agent.framework || '')}"><h3>${escape(agent.displayName)}</h3>`
      + `<p class="when">${item.lastRun ? 'Scored ' + ago(item.lastRun) : ''}</p>${scores}`
      + (link ? `<a class="agent-trace" href="${escape(link)}" target="_blank" rel="noopener">Its checks in Agent Manager${icon('external')}</a>` : '')
      + '</article>';
  }).join('');
}

/* ---------- Start, and start over ---------- */

async function loadControl() {
  try {
    const state = await (await fetch('/api/control')).json();
    if (!state.error) { control = state; partnerCard = state.partner; showVersion(state.release); }
  } catch { /* the tower keeps its last state */ }
  showControl();
}

$('start-over').addEventListener('click', async () => {
  if (busy) return;
  busy = true;
  $('start-over').textContent = 'Starting over...';
  try {
    const state = await post('/api/reset');
    if (!state.error) { control = state; partnerCard = state.partner; }
    investigation = null;
    session = 'chat-' + Date.now();
    progress.forEach((act) => { act.done = false; act.result = {}; });
    openAct = 0;
    resetFleet();
    showVersion('v1');
    document.querySelectorAll('.rules li').forEach((li) => li.classList.remove('is-new'));
    $('messages').innerHTML = `<p class="empty">Start with 09:00: ${who()}’s message arrives here, and the agents get to work.</p>`;
    $('findings').hidden = true;
    $('report').hidden = true;
    drawAccount(startingAccount);
  } finally {
    busy = false;
    $('start-over').textContent = 'Start over';
    renderActs();
  }
});

async function start() {
  document.querySelectorAll('[data-icon]').forEach((el) => { el.innerHTML = icon(el.dataset.icon); });
  config = await (await fetch('/api/config')).json();
  document.title = 'Agent Manager | ' + config.bank;
  $('wordmark').textContent = config.bank;
  $('wordmark').href = config.mainDemoUrl + '/#/';
  document.querySelectorAll('.nav-link').forEach((link) => { link.href = config.mainDemoUrl + '/#/' + link.dataset.page; });
  $('customer-name').textContent = config.customer || 'The customer';
  $('mcp-link').href = config.mainDemoUrl + '/#/mcp';
  $('a2a-link').href = config.mainDemoUrl + '/#/a2a';
  const fleet = consoleLink((c) => c.fleet);
  if (fleet) { $('console-link').href = fleet; $('registry-link').href = fleet; }
  $('messages').innerHTML = `<p class="empty">Start with 09:00: ${who()}’s message arrives here, and the agents get to work.</p>`;
  drawFleet();
  renderActs();
  loadAccount();
  loadControl();
  loadScores();
  // Another tab, or another presenter, may change what applies: read it again now and then.
  setInterval(() => { loadScores(); if (!busy) loadControl(); }, 30000);
}

start();
