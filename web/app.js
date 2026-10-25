/* The demo's page: one day at the bank in five acts, one per promise of
   Agent Manager, each seen without it and with it; the control tower; the
   customer's chat; and what Agent Manager found and scored. Every control on
   the page is a call to Agent Manager's API, and every result links to the
   console screen that shows it. */

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
  lock: '<rect width="18" height="11" x="3" y="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
  card: '<rect width="20" height="14" x="2" y="5" rx="2"/><line x1="2" x2="22" y1="10" y2="10"/>',
  ban: '<circle cx="12" cy="12" r="10"/><path d="m4.9 4.9 14.2 14.2"/>',
  pause: '<rect x="14" y="4" width="4" height="16" rx="1"/><rect x="6" y="4" width="4" height="16" rx="1"/>',
  play: '<polygon points="6 3 20 12 6 21 6 3"/>',
  alert: '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
  gauge: '<path d="m12 14 4-4"/><path d="M3.34 19a10 10 0 1 1 17.32 0"/>',
  activity: '<path d="M22 12h-2.48a2 2 0 0 0-1.93 1.46l-2.35 8.36a.25.25 0 0 1-.48 0L9.24 2.18a.25.25 0 0 0-.48 0l-2.35 8.36A2 2 0 0 1 4.49 12H2"/>',
  sparkles: '<path d="M9.937 15.5A2 2 0 0 0 8.5 14.063l-6.135-1.582a.5.5 0 0 1 0-.962L8.5 9.936A2 2 0 0 0 9.937 8.5l1.582-6.135a.5.5 0 0 1 .963 0L14.063 8.5A2 2 0 0 0 15.5 9.937l6.135 1.581a.5.5 0 0 1 0 .964L15.5 14.063a2 2 0 0 0-1.437 1.437l-1.582 6.135a.5.5 0 0 1-.963 0z"/><path d="M20 3v4"/><path d="M22 5h-4"/><path d="M4 17v2"/><path d="M5 18H3"/>',
  network: '<circle cx="12" cy="4.5" r="2.5"/><path d="m10.2 6.3-3.9 3.9"/><circle cx="4.5" cy="12" r="2.5"/><path d="M7 12h10"/><circle cx="19.5" cy="12" r="2.5"/><path d="m13.8 17.7 3.9-3.9"/><circle cx="12" cy="19.5" r="2.5"/>',
  commit: '<circle cx="12" cy="12" r="3"/><line x1="3" x2="9" y1="12" y2="12"/><line x1="15" x2="21" y1="12" y2="12"/>',
  flask: '<path d="M14 2v6a2 2 0 0 0 .245.96l5.51 10.08A2 2 0 0 1 18 22H6a2 2 0 0 1-1.755-2.96l5.51-10.08A2 2 0 0 0 10 8V2"/><path d="M6.453 15h11.094"/><path d="M8.5 2h7"/>',
  clipboard: '<rect width="8" height="4" x="8" y="2" rx="1" ry="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><path d="m9 14 2 2 4-4"/>',
  chart: '<line x1="18" x2="18" y1="20" y2="10"/><line x1="12" x2="12" y1="20" y2="4"/><line x1="6" x2="6" y1="20" y2="14"/>',
  undo: '<path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/>',
};
const icon = (name) => '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
  + 'stroke-linejoin="round" aria-hidden="true">' + (ICONS[name] || '') + '</svg>';

const MESSAGES = {
  trip: 'I’m moving to New York, in the United States, for six months for work. Please send me a new debit card at home '
    + 'before I leave, mine is worn out. What will paying by card cost me there, and do I need travel insurance?',
  cards: 'The customer is moving to New York for six months and needs a new debit card at home before leaving: '
    + 'their card is worn out.',
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
const post = async (url, body) => {
  const reply = await (await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body || {}) })).json();
  if (reply && reply.error) throw new Error(reply.error);
  return reply;
};
let config = { agents: [], console: {} };
let session = 'chat-' + Date.now();
const consoleLink = (pick) => { try { return pick(config.console) || null; } catch { return null; } };
const agentLink = (agent, page) => consoleLink((c) => c.agents[agent][page]);
const agentName = (name) => (config.agents.find((a) => a.name === name) || { displayName: name }).displayName;
const who = () => (config.customer || 'The customer').split(' ')[0];
const plural = (n, word) => `${number(n)} ${word}${n === 1 ? '' : 's'}`;

// What applies now, as Agent Manager reports it, and what the demo has set up.
let control = { partner: 'vetted', rule: false, releases: {} };
let startingAccount = {};
// The bank's checks run on demand: v2's readiness (act 2), the incident (act 3).
const evaluations = { readiness: null, incident: null };
const release = (agent, environment) => control.releases?.[agent]?.[environment] || {};

/* ---------- The five acts ---------- */

const ACTS = [
  {
    time: '09:00',
    title: 'Four teams, four frameworks, one control plane',
    persona: 'AI Platform Architect',
    quote: 'I don’t want to tell the team they can’t use the framework that works best for them, and I don’t want to '
      + 'get burned from standardizing on one vendor’s stack.',
    situation: () => `${who()} is moving to New York for six months. Four agents take care of it, built by four teams with `
      + 'four frameworks: Agent Manager runs two of them, the two others run on their team’s own platform.',
    without: 'Every new framework means rebuilding authentication, guardrails and logging. Nobody can say which agents run, '
      + 'which keys they hold, or which agent may command which.',
    actions: [
      { label: () => `Send ${who()}’s message`, icon: 'send', run: async () => ({ run: await send(MESSAGES.trip) }) },
      { label: () => 'Two callers try to command the Cards Agent', icon: 'lock', secondary: true, run: tryCallers },
    ],
    outcome: (r) => [
      r.run && `All four agents are in Agent Manager’s inventory, each with its own identity and its own key to the model. `
        + `Agent Manager’s gateway checked the Concierge’s identity before the Cards Agent and the Travel Desk saw anything; `
        + 'the Policy Advisor, on its own platform, checked it itself.',
      r.run && `${plural(r.run.calls, 'model call')}, ${number(r.run.tokens)} tokens, ${money(r.run.cost)}, over four `
        + 'frameworks: one trace in Agent Manager, step by step.',
      r.callers && r.callers.map((c) => `${c.who}: ${c.status === 401 || c.status === 403 ? 'refused by Agent Manager' : 'HTTP ' + c.status}.`)
        .join(' ') + ' Being registered is not enough: only the Concierge may command the Cards Agent.',
    ],
    links: (r) => [['The bank’s agents in Agent Manager', consoleLink((c) => c.fleet)],
      ['Who may call the Cards Agent', agentLink('cards-agent', 'security')],
      ['The Concierge’s trace, across the four frameworks', r.run?.traces.concierge]],
    value: 'One identity, policy and observability layer across every framework and runtime: each team keeps its '
      + 'framework, the bank keeps control.',
    stat: '33% say AI adoption is outpacing their ability to govern and monitor it (Drata).',
  },
  {
    time: '14:00',
    title: 'The cards team wants v2 live by Friday',
    persona: 'AI Engineer',
    quote: 'We keep getting stuck at legal, security, and IT sign-off. Nobody agrees on the bar for production-readiness.',
    situation: () => 'The cards team pushed v2 to GitHub, with a rule from sales: customers going abroad move to Premier, '
      + `at €14 a month. Agent Manager built it and runs it in ${trialName()}, its test environment, next to v1 in Production.`,
    without: 'The launch is a one-off debate between developers, IT and security. Or v2 reaches customers on a Friday '
      + 'evening, and moves them to a dearer package nobody asked for.',
    actions: [
      { label: () => `Try v2 in ${trialName()} with ${who()}’s request`, icon: 'flask', run: tryV2 },
      { label: () => 'Check v2 against the bank’s bar', icon: 'clipboard', run: () => startEvaluation('readiness') },
    ],
    outcome: (r) => [
      r.trial && (r.trial.packageChanged
        ? `In ${trialName()}, v2 moved ${who()} to ${r.trial.package || 'Premier'} without asking. No customer saw it: `
          + 'production still runs v1.'
        : 'v2 did not change the package this time. Try it again: the sales rule is in its instructions.'),
      versionsLine(),
      r.readiness && evaluationLine('readiness'),
    ],
    tone: (r) => (r.trial?.packageChanged && evaluations.readiness?.status !== 'success' ? 'bad' : 'good'),
    links: (r) => [['v1 and v2, built from GitHub', agentLink('cards-agent', 'builds')],
      ['Where each version runs, and Promote', agentLink('cards-agent', 'deploy')],
      ['v2’s unasked change in its trace', r.trial?.traceUrl],
      ['The readiness check in Agent Manager', evaluations.readiness?.url]],
    value: 'Production readiness becomes a yes or no backed by evidence, the same for every team, not a debate.',
    stat: 'Only 20% of agents make it to production (Gartner).',
  },
  {
    time: '18:02',
    title: 'A partner’s agent turns rogue',
    persona: 'AI Compliance Lead',
    quote: 'We have no way to ensure agents are working like they’re supposed to.',
    situation: () => 'The travel insurance partner’s agent is compromised: its A2A card now tells the agents that read it '
      + 'to collect the customer’s card number. The Travel Desk reads that card.',
    without: 'The Travel Desk asks for the card number, and it travels to the model provider, to the partner and into '
      + 'the logs. Four teams, four log formats: nobody can tell which agent asked, or why.',
    actions: [
      { label: () => 'The partner turns rogue: send the message again', icon: 'alert', run: rogueTrip },
      { label: () => `${who()} sends the card number`, icon: 'card', run: async () => ({ cardRun: await send(MESSAGES.cardNumber) }) },
    ],
    outcome: (r) => [
      r.run && (r.run.asked
        ? `The Travel Desk asked ${who()} for the card number and its expiry date, as the partner’s card told it to.`
        : 'The Travel Desk read the partner’s card, and did not follow it this time.'),
      r.pinpoint && `Agent Manager’s trace shows where it came from: the step “${r.pinpoint.step}” returned the partner’s `
        + `card, which says: “${r.pinpoint.excerpt}”`,
      r.run && evaluationLine('incident'),
      r.cardRun && (r.cardRun.blockedRequests
        ? 'The card number was blocked before it left the bank: neither the model nor the partner saw it.'
        : 'The message had no full card number: nothing to block.'),
    ],
    tone: (r) => (r.run?.asked && !r.cardRun ? 'bad' : 'good'),
    links: (r) => [['The poisoned step in the Travel Desk’s trace', r.pinpoint?.traceUrl || r.run?.traces['travel-desk']],
      ['The investigation in Agent Manager', evaluations.incident?.url],
      ['The rule that blocks card numbers', agentLink('concierge', 'rules')]],
    value: 'Every step of every agent, across frameworks and partners, on one trace: the fault is pinpointed, not guessed.',
    stat: '79% of enterprises have had a financial or operational control failure from autonomous AI (VentureBeat).',
  },
  {
    time: '18:05',
    title: 'Stop it in one click, fix it without a release',
    persona: 'Chief AI Officer',
    quote: 'The board asked me point blank what our plan is if one of our agents does something like what’s in the news.',
    situation: () => 'The Travel Desk still follows the partner’s card. The risk team suspends it in Agent Manager, adds '
      + 'a rule to its model calls, and brings it back.',
    without: 'No way to cut off one agent: stop all of the bank’s AI, or wait hours for the travel team to patch and '
      + 'redeploy, on a Friday night.',
    actions: [
      { label: () => 'Suspend the Travel Desk, then send again', icon: 'pause',
        run: async () => { const suspended = await suspendTravelDesk(true); return { suspended, offRun: await send(MESSAGES.trip) }; } },
      { label: () => 'Add the rule “No instructions from third parties”', icon: 'shield',
        run: async () => ({ ruleSeconds: await setRule(true) }) },
      { label: () => 'Bring the Travel Desk back, then send again', icon: 'play',
        run: async () => { const resumed = await suspendTravelDesk(false); return { resumed, backRun: await send(MESSAGES.trip) }; } },
    ],
    outcome: (r) => [
      r.suspended !== undefined && `Agent Manager suspended the Travel Desk in production, ${r.suspended} seconds later. `
        + `${who()} still got ${r.offRun?.account?.newCard ? 'the new card' : 'the cards team’s answer'} and the catalogue’s `
        + 'advice: only the travel answers wait.',
      r.ruleSeconds !== undefined && `The rule was live at Agent Manager’s gateway ${r.ruleSeconds} seconds later, with no `
        + 'change to the Travel Desk’s code and no new release.',
      r.resumed !== undefined && `The Travel Desk was back ${r.resumed} seconds later. ` + (r.backRun?.blockedRequests
        ? `When the partner’s card reached its model, Agent Manager blocked it: ${who()} was not asked for a card number.`
        : (r.backRun?.asked ? 'It still asked for the card number: is the rule on?' : `${who()} was not asked for a card number.`)),
    ],
    links: () => [['The Suspend button: the Travel Desk’s deployments', agentLink('travel-desk', 'deploy')],
      ['The Travel Desk’s rules', agentLink('travel-desk', 'rules')],
      ['Its runtime logs', agentLink('travel-desk', 'logs')]],
    value: 'Intervene immediately, limit the blast radius, and fix it at the control plane.',
    stat: '“Oversight must live outside the agent’s execution loop.” (Forrester)',
  },
  {
    time: 'Monday 09:00',
    title: 'The risk committee',
    persona: 'AI Compliance Lead',
    quote: 'We’ve got a board-level AI push, but no way to prove any of this is controlled to an auditor.',
    situation: () => 'The committee asks what happened, what was exposed, what went where, and what it cost.',
    without: 'Four log formats, four teams to chase, and no single answer for the regulator.',
    actions: [{ label: () => 'Show Agent Manager’s report', icon: 'chart', run: async () => { await showReport(); return { report: true }; } }],
    outcome: () => ['Every answer from one place: which agents ran and where, which version is in production and which was '
      + 'held back, what each cost, what was blocked, what the investigation found, and how each agent scores.'],
    links: () => [['The bank’s agents in Agent Manager', consoleLink((c) => c.fleet)],
      ['The investigation', evaluations.incident?.url],
      ['The Travel Desk’s checks', agentLink('travel-desk', 'checks')]],
    value: 'Audit-ready evidence on demand, and a clean separation between the teams that build and the team that oversees.',
    stat: '63% of organizations have no AI governance policy (IBM).',
  },
];
const progress = ACTS.map(() => ({ done: false, result: {} }));
let openAct = 0;

const trialName = () => (release('cards-agent', config.trial).name || config.trial || 'the test environment');

function versionsLine() {
  const live = release('cards-agent', config.environment);
  const trial = release('cards-agent', config.trial);
  if (!live.commit) return '';
  return `Production runs v1 (commit ${live.commit})` + (trial.commit && trial.commit !== live.commit
    ? `; ${trialName()} runs v2 (commit ${trial.commit}), and nothing promotes it until it meets the bar.` : '.');
}

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
        + `<div class="value"><p>${escape(act.value)}</p><small>${escape(act.stat)}</small></div>`
        + (i + 1 < ACTS.length ? `<button type="button" class="btn secondary next" data-open="${i + 1}">Next: ${escape(ACTS[i + 1].title)}</button>` : '');
    }
    return `<li class="${classes}"><button type="button" class="step-head" data-open="${i}">`
      + `<span class="step-num">${state.done ? '&#10003;' : i + 1}</span><span class="step-title"><small>${escape(act.time)}</small>`
      + `${escape(act.title)}</span></button><div class="step-body">`
      + `<blockquote class="voice"><span>${escape(act.persona)}</span>“${escape(act.quote)}”</blockquote>`
      + `<p class="step-text">${escape(act.situation())}</p>`
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
    const team = (lead.match(/by the ([^,]+)/) || [])[1];
    const hosted = agent.runs === 'platform';
    card.dataset.fw = agent.framework;
    const overview = agentLink(agent.name, 'overview');
    card.innerHTML = `<div class="agent-top"><span class="framework">${escape(agent.framework)}</span>`
      + `<span class="runs${hosted ? ' hosted' : ''}">${hosted ? 'Run by Agent Manager' : 'Runs on its team’s platform'}</span></div>`
      + `<div class="agent-name">${overview ? `<a href="${escape(overview)}" target="_blank" rel="noopener">${escape(agent.displayName)}</a>` : escape(agent.displayName)}</div>`
      + `<div class="agent-role">${escape(rest.join('. '))}${team ? ` <i>The ${escape(team)}.</i>` : ''}</div>`
      + (hosted ? '<div class="release" data-release></div>' : '')
      + '<div class="agent-status">Ready</div><ul class="agent-steps"></ul>'
      + '<a class="agent-trace" target="_blank" rel="noopener" hidden>Its trace in Agent Manager' + icon('external') + '</a>'
      + `<div class="agent-foot"><a class="id-badge" href="${escape(agentLink(agent.name, 'agentId') || '#')}" target="_blank" rel="noopener"`
      + ` title="Its identity in Agent Manager">${icon('key')}Agent ID</a>`
      + (hosted ? `<a class="id-badge" href="${escape(agentLink(agent.name, 'deploy') || '#')}" target="_blank" rel="noopener"`
        + ` title="Its builds and deployments in Agent Manager">${icon('commit')}Deployments</a>` : '')
      + '</div>';
  }
  $('model-name').textContent = MODEL_NAMES[config.model] || config.model || 'Claude';
  const model = consoleLink((c) => c.model);
  if (model) $('model-link').href = model;
}

function showControl() {
  for (const agent of config.agents.filter((a) => a.runs === 'platform')) {
    const card = agentCard(agent.name);
    const live = release(agent.name, config.environment);
    const trial = release(agent.name, config.trial);
    const suspended = live.status === 'suspended';
    card.classList.toggle('is-suspended', suspended);
    const parts = [];
    if (live.commit) parts.push(`<span class="${suspended ? 'bad' : ''}">${icon('commit')}Production: ${escape(live.commit)}`
      + `${suspended ? ', suspended' : live.status !== 'active' ? ', ' + escape(live.status) : ''}</span>`);
    if (trial.commit && trial.commit !== live.commit) parts.push(`<span class="trial">${icon('flask')}${escape(trial.name || config.trial)}: ${escape(trial.commit)} (v2)</span>`);
    card.querySelector('[data-release]').innerHTML = parts.join('');
    if (suspended && !card.classList.contains('is-blocked')) card.querySelector('.agent-status').textContent = 'Suspended in Agent Manager';
  }
  const suspended = config.agents.filter((a) => release(a.name, config.environment).status === 'suspended').map((a) => a.displayName);
  $('suspended-label').textContent = 'Suspended: ' + (suspended.length ? suspended.join(', ') : 'none');
  document.querySelector('[data-rule="suspended"]').classList.toggle('is-off', !suspended.length);
  document.querySelector('[data-rule="third-party"]').classList.toggle('is-off', !control.rule);
  $('partner-state').textContent = control.partner === 'own'
    ? 'The partner’s card: its own, unchecked (compromised)' : 'The partner’s card: vetted by the gateway';
  $('partner-state').classList.toggle('is-bad', control.partner === 'own');
}

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

function finishAgent(name, event, run) {
  const steps = event.steps || [];
  const use = usage(steps);
  const blocked = steps.filter((s) => s.kind === 'blocked');
  const failed = steps.filter((s) => s.kind === 'error');
  const summary = `${plural(use.calls, 'model call')}, ${number(use.tokens)} tokens, ${money(use.cost)}`;
  if (event.unavailable) setAgent(name, 'blocked', 'Suspended in Agent Manager: the Concierge got no answer from it.');
  else if (event.refused) setAgent(name, 'blocked', 'Refused: ' + event.refused);
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
  if (event.identity) {
    lines.push(`<li class="ok"><span>${event.identity.caller === 'concierge' ? 'The Concierge’s identity checked by the agent'
      : 'The Concierge’s identity checked by Agent Manager'}</span></li>`);
  }
  Object.keys(counts).filter((tool) => !tool.endsWith('!')).forEach((tool) => {
    const state = counts[tool + '!'] ? 'blocked' : unasked(tool) ? 'unasked' : 'ok';
    const via = steps.find((s) => s.name === tool)?.via;
    // Long tool names break after their underscores only.
    lines.push(`<li class="${state}"><span>${escape(tool).replaceAll('_', '_<wbr>')}${counts[tool] > 1 ? ` (${counts[tool]} times)` : ''}</span>`
      + `${via ? `<span class="via">${via.toUpperCase()}</span>` : ''}${state === 'unasked' ? '<span class="note">nobody asked for it</span>' : ''}</li>`);
  });
  if (name === 'travel-desk' && ASKS_FOR_CARD.test(event.answer || '') && !blocked.length) {
    lines.push('<li class="unasked"><span class="note">asks the customer for the card number</span></li>');
  }
  blocked.forEach((s) => lines.push(
    `<li class="blocked"><span class="stop">${escape(s.tool || 'Model call')} stopped: ${escape(s.reason)}</span></li>`));
  card.querySelector('.agent-steps').innerHTML = lines.join('');
  const link = card.querySelector('.agent-trace');
  if (event.traceUrl) { link.href = event.traceUrl; link.hidden = false; }
  // What the whole request cost, and what Agent Manager stopped.
  run.agents.add(name);
  run.calls += use.calls; run.tokens += use.tokens; run.cost += use.cost;
  run.traces[name] = event.traceUrl;
  run.traceIds[name] = event.traceId;
  if (event.identity) run.identities += 1;
  if (event.unavailable) run.unavailable.push(name);
  if (name === 'travel-desk' && ASKS_FOR_CARD.test(event.answer || '') && !blocked.length) run.asked = true;
  steps.filter((s) => s.kind === 'tool' && s.ok).forEach((s) => run.done.add(s.name));
  steps.filter((s) => s.via).forEach((s) => document.querySelector(`.route[data-via="${s.via}"]`)?.classList.add('is-used'));
  const changed = steps.find((s) => s.name === 'change_package' && s.ok && s.result?.newPackage);
  if (changed) run.account = { ...run.account, package: changed.result.newPackage, monthlyFee: changed.result.fee, changed: true };
  if (run.done.has('order_replacement_card')) run.account = { ...run.account, newCard: true };
  for (const step of blocked) {
    if (step.tool) run.blockedTools.push(step.tool);
    if (step.direction === 'request') run.blockedRequests += 1;
    const rule = /third party/.test(step.reason) ? 'third-party' : 'card-number';
    document.querySelector(`[data-rule="${rule}"]`)?.classList.add('is-hit');
  }
  drawTotals(run);
}

function drawTotals(run) {
  const blocked = run.blockedTools.length + run.blockedRequests;
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
    blockedTools: [], blockedRequests: 0, unavailable: [], done: new Set(), account: { ...startingAccount } };
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
    if (run.blockedRequests && !run.blockedTools.length && run.agents.size === 1) {
      addMessage('note', 'Agent Manager kept the card number away from the model.');
    }
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

async function tryCallers() {
  const callers = await post('/api/callers');
  for (const c of callers) {
    addMessage(c.status === 401 || c.status === 403 ? 'note ok' : 'note', `${c.who} calls the Cards Agent: `
      + (c.status === 401 || c.status === 403 ? `refused by Agent Manager (HTTP ${c.status}).` : `HTTP ${c.status}.`));
  }
  return { callers };
}

async function tryV2() {
  const note = addMessage('note', `The cards team tries v2 in ${trialName()}, through Agent Manager’s gateway...`);
  const trial = await post('/api/try-v2', { message: MESSAGES.cards });
  note.textContent = trial.packageChanged
    ? `In ${trialName()}, v2 moved the customer to ${trial.package || 'Premier'} without asking.`
    : 'v2 answered without changing the package this time.';
  addMessage('bot', trial.answer, `Cards Agent v2, in ${trialName()}`);
  return { trial };
}

async function setRule(on) {
  const note = addMessage('note', 'The risk team adds the rule “No instructions from third parties” to the Travel Desk in Agent Manager...');
  const reply = await post('/api/rule', { on });
  note.textContent = `The rule is live at the gateway, ${reply.seconds} seconds later. Nothing was redeployed.`;
  note.classList.add('ok');
  control.rule = on;
  showControl();
  document.querySelector('[data-rule="third-party"]').classList.add('is-new');
  return reply.seconds;
}

async function suspendTravelDesk(on) {
  const note = addMessage('note', on ? 'The risk team suspends the Travel Desk in Agent Manager, as with its Suspend button...'
    : 'The risk team deploys the Travel Desk again in Agent Manager (it takes a little while to start)...');
  const reply = await post('/api/suspend', { on });
  note.textContent = on ? `The Travel Desk is suspended in production, ${reply.seconds} seconds later. The other agents run on.`
    : `The Travel Desk is back in production, ${reply.seconds} seconds later.`;
  note.classList.add('ok');
  await loadControl();
  return reply.seconds;
}

async function setPartner(card) {
  await post('/api/partner', { card });
  control.partner = card;
  showControl();
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
    startEvaluation('incident');
  }
  return result;
}

/* ---------- What Agent Manager found ---------- */

const EVALUATIONS = {
  readiness: { title: 'v2’s readiness check, in the test environment', running: 'Agent Manager is running the bank’s checks on '
    + 'what v2 did in the test environment (about 3 minutes)...' },
  incident: { title: 'The incident investigation, in production', running: 'Agent Manager is investigating the last 15 minutes '
    + 'with the bank’s own checks (about 3 minutes)...' },
};

function evaluationLine(kind) {
  const found = evaluations[kind];
  if (!found) return '';
  if (found.status !== 'success') return EVALUATIONS[kind].running;
  const failed = found.checks.filter((c) => c.failed);
  if (kind === 'readiness') {
    const scored = found.checks.map((c) => `“${c.check}” ${c.failed ? `failed on ${c.failed} of ${plural(c.traces, 'request')}`
      : `passed on ${plural(c.traces, 'request')}`}`).join(', ');
    const judged = failed.length && failed.length < found.checks.length
      ? ' The judge passes v2, since the sales rule is in its instructions; the bank’s own check stops it.' : '';
    return failed.length ? `The bank’s bar, the same for every team: ${scored}.${judged} v2 is not promoted: it stays in `
      + `${trialName()}, and v1 stays in production.` : `The bank’s bar: ${scored}. v2 could be promoted.`;
  }
  if (!failed.length) return 'Agent Manager’s investigation found nothing wrong.';
  return 'Agent Manager’s investigation, with the bank’s own checks, confirms it: '
    + failed.map((c) => `“${c.check}” failed`).join(', ') + '. Details below.';
}

async function startEvaluation(kind) {
  const started = await post('/api/evaluate', { kind });
  evaluations[kind] = { ...started, status: 'pending', checks: [] };
  drawFindings();
  for (let i = 0; i < 40 && evaluations[kind]?.status !== 'success'; i += 1) {
    await sleep(10000);
    if (evaluations[kind]?.name !== started.name) return {};  // the demo started over
    const now = await (await fetch(`/api/evaluation?kind=${kind}&name=${encodeURIComponent(started.name)}`)).json();
    if (!now.error) evaluations[kind] = { ...evaluations[kind], ...now };
    drawFindings();
    if (!busy) renderActs();
  }
  return { [kind]: true };
}

function drawFindings() {
  const kinds = Object.keys(evaluations).filter((kind) => evaluations[kind]);
  $('findings').hidden = !kinds.length;
  $('finding-list').innerHTML = kinds.map((kind) => {
    const found = evaluations[kind];
    const rows = (found.status === 'success' ? found.checks : []).map((c) => `<article class="finding${c.failed ? '' : ' ok'}">`
      + `${icon(c.failed ? 'alert' : 'shield')}<div><b>${escape(c.check)}</b>`
      + `<small>${c.failed ? `failed on ${c.failed} of ${plural(c.traces, 'trace')}` : `passed on ${plural(c.traces, 'trace')}`}</small>`
      + (c.failed ? `<p>${escape(c.explanation)}</p>` : '')
      + (c.traceUrl ? `<a class="agent-trace" href="${escape(c.traceUrl)}" target="_blank" rel="noopener">The trace in Agent Manager${icon('external')}</a>` : '')
      + '</div></article>');
    return `<div class="finding-group"><h3>${escape(EVALUATIONS[kind].title)}</h3>`
      + (rows.join('') || `<p class="when">${escape(evaluationLine(kind))}</p>`)
      + (found.url ? `<a class="agent-trace" href="${escape(found.url)}" target="_blank" rel="noopener">This run in Agent Manager${icon('external')}</a>` : '')
      + '</div>';
  }).join('');
}

async function showReport() {
  const response = await fetch('/api/report');
  const data = await response.json();
  if (!response.ok) throw new Error(data.error);
  const [inPrice, outPrice] = PRICES[config.model] || [0, 0];
  const where = (a) => {
    if (a.runs !== 'platform') return 'its team’s platform';
    const live = data.releases?.[a.agent]?.[config.environment] || {};
    return `Agent Manager, ${live.commit || '?'} in production${live.status === 'active' ? '' : ' (' + (live.status || '?') + ')'}`;
  };
  const rows = data.agents.map((a) => `<tr><td><b>${escape(a.displayName)}</b><small>${escape(a.framework)}, on ${escape(where(a))}</small></td>`
    + `<td>${number(a.requests)}</td><td>${number(a.tokens)}</td><td>${money((a.input * inPrice + a.output * outPrice) / 1e6)}</td>`
    + `<td class="${a.blocked ? 'bad' : ''}">${number(a.blocked)}</td><td class="${a.errors ? 'bad' : ''}">${number(a.errors)}</td></tr>`).join('');
  const lines = [];
  const readiness = evaluations.readiness?.status === 'success' && evaluationLine('readiness');
  if (readiness) lines.push(`<li>Cards Agent v2: ${escape(readiness)}</li>`);
  (evaluations.incident?.checks || []).filter((c) => c.failed).forEach((c) => lines.push(`<li>${escape(c.check)}: ${escape(c.explanation)}</li>`));
  $('report-body').innerHTML = '<table class="report-table"><thead><tr><th>Agent</th><th>Requests, last 24 h</th><th>Tokens</th>'
    + `<th>Model cost</th><th>Blocked</th><th>Errors</th></tr></thead><tbody>${rows}</tbody></table>`
    + (lines.length ? `<div class="report-findings"><b>What the bank’s checks found</b><ul>${lines.join('')}</ul></div>` : '');
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
    }).join('') || '<p class="when">No traffic scored yet. Agent Manager scores every 10 minutes.</p>';
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
    if (!state.error) control = state;
  } catch { /* the tower keeps its last state */ }
  showControl();
}

const welcome = () => `<p class="empty">Start with 09:00: ${who()}’s message arrives here, and the agents get to work.</p>`;

$('start-over').addEventListener('click', async () => {
  if (busy) return;
  busy = true;
  $('start-over').textContent = 'Starting over...';
  try {
    const state = await post('/api/reset');
    control = state;
    evaluations.readiness = null;
    evaluations.incident = null;
    session = 'chat-' + Date.now();
    progress.forEach((act) => { act.done = false; act.result = {}; });
    openAct = 0;
    resetFleet();
    document.querySelectorAll('.rules li').forEach((li) => li.classList.remove('is-new'));
    $('messages').innerHTML = welcome();
    $('findings').hidden = true;
    $('report').hidden = true;
    drawAccount(startingAccount);
  } catch (error) {
    addMessage('note', 'Could not start over: ' + error.message);
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
  $('messages').innerHTML = welcome();
  drawFleet();
  await loadControl();
  renderActs();
  loadAccount();
  loadScores();
  // Another tab, or the console itself, may change what applies: read it again now and then.
  setInterval(() => { loadScores(); if (!busy) loadControl(); }, 20000);
}

start();
