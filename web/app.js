import { basicSetup } from "codemirror";
import { EditorView, keymap } from "@codemirror/view";
import { Compartment } from "@codemirror/state";
import { indentWithTab } from "@codemirror/commands";
import { indentUnit } from "@codemirror/language";
import { python } from "@codemirror/lang-python";
import { javascript } from "@codemirror/lang-javascript";
import { markdown } from "@codemirror/lang-markdown";
import { marked } from "marked";
import DOMPurify from "dompurify";

const main = document.querySelector("#main");
const $ = (selector) => document.querySelector(selector);
const escape = (value = "") => String(value).replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[char]);
const titles = { coding: "Python & DSA", "system-design": "System design", "ai-systems": "Applied AI", project: "Project defense", debugging: "Debugging", behavioral: "Customer & behavioral", "post-training": "Post-training (optional)", "research-engineering": "Research engineering (optional)" };
let data, currentSession, editor, draftKey, draft, busy = false, renderId = 0, chatPending = false;
let languageSlot = new Compartment();
const editableSlot = new Compartment();

function defaultLesson() {
  return data?.recommended_lesson || data?.lessons[0]?.id || "role-diagnostic";
}

function notice(message = "") {
  $("#notice").textContent = message;
  $("#notice").hidden = !message;
}

async function api(path, body) {
  const response = await fetch(path, {
    method: body === undefined ? "GET" : "POST",
    headers: body === undefined ? {} : { "Content-Type": "application/json", "X-Grey-Token": data.token },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || "The request failed. Please retry.");
  return result;
}

function setBusy(value, text = "Working…") {
  busy = value;
  $("#busy").hidden = !value;
  $("#busy-text").textContent = text;
  main.setAttribute("aria-busy", String(value));
  document.querySelectorAll("button, input, select, textarea").forEach((element) => {
    if (value) { if (element.dataset.wasDisabled === undefined) element.dataset.wasDisabled = String(element.disabled); element.disabled = true; }
    else if (element.dataset.wasDisabled !== undefined) {
      element.disabled = element.dataset.wasDisabled === "true";
      delete element.dataset.wasDisabled;
    }
  });
  if (editor) editor.dispatch({ effects: editableSlot.reconfigure(EditorView.editable.of(!value)) });
}

async function run(label, operation) {
  if (busy || chatPending) { notice("Wait for the current reply before starting another action."); return; }
  notice();
  setBusy(true, label);
  try { await operation(); }
  catch (error) { notice(error.message); }
  finally { setBusy(false); }
}

async function refresh() {
  data = await api("/api/bootstrap");
  renderSidebar();
}

function renderSidebar() {
  let group = "";
  $("#course-nav").innerHTML = data.lessons.map((lesson, index) => {
    let heading = "";
    if (lesson.stage !== group) { group = lesson.stage; heading = `<div class="course-group">${escape(group)}</div>`; }
    const done = lesson.checkpoint?.passed && lesson.completed;
    return `${heading}<a class="course-link" href="#/learn/${lesson.id}" data-lesson="${lesson.id}"><span class="course-number">${done ? "✓" : String(index + 1).padStart(2, "0")}</span><span>${escape(lesson.title)}</span></a>`;
  }).join("");
  $("#provider-info").textContent = `${data.provider} · ${data.model} · ${data.effort}`;
  $("#mobile-lesson").innerHTML = data.lessons.map((lesson) => `<option value="${lesson.id}">${escape(lesson.title)}</option>`).join("");
  $("#mobile-lesson").onchange = (event) => { location.hash = `#/learn/${event.target.value}`; };
}

function cleanMarkdown(text) {
  return DOMPurify.sanitize(marked.parse(text || ""), { USE_PROFILES: { html: true }, FORBID_TAGS: ["img", "input", "form", "style"], FORBID_ATTR: ["style"] });
}

async function diagrams(root) {
  const nodes = [...root.querySelectorAll("pre:has(code.language-mermaid)")];
  if (!nodes.length) return;
  try {
    const { default: mermaid } = await import("mermaid");
    mermaid.initialize({ startOnLoad: false, securityLevel: "strict", theme: "neutral", suppressErrorRendering: true });
    for (const pre of nodes) {
      if (!pre.isConnected) continue;
      const source = pre.textContent;
      const holder = document.createElement("div");
      holder.className = "mermaid";
      holder.textContent = source;
      pre.replaceWith(holder);
      try { await mermaid.run({ nodes: [holder] }); }
      catch { holder.replaceWith(pre); const hint = document.createElement("p"); hint.className = "footnote"; hint.textContent = "Diagram could not be rendered. Check its Mermaid syntax."; pre.after(hint); }
    }
  } catch { /* Source remains readable when diagram loading fails. */ }
}

function pageHead(eyebrow, title, subtitle = "", action = "") {
  return `<div class="page-head"><div><div class="eyebrow">${escape(eyebrow)}</div><h1>${escape(title)}</h1>${subtitle ? `<p class="page-subtitle">${escape(subtitle)}</p>` : ""}</div>${action}</div>`;
}

function resetView() {
  if (editor) { editor.destroy(); editor = null; }
  draftKey = null;
  document.querySelectorAll(".active").forEach((el) => el.classList.remove("active"));
}

async function route() {
  const id = ++renderId;
  const parts = location.hash.split("?")[0].replace(/^#\/?/, "").split("/");
  const view = parts[0] || "learn";
  resetView();
  main.innerHTML = '<div class="loading-state">Loading…</div>';
  $(`[data-nav="${view === "session" ? "sessions" : view}"]`)?.classList.add("active");
  try {
    if (view === "learn") {
      const lessonId = parts[1] || defaultLesson();
      const lesson = await api(`/api/lessons/${encodeURIComponent(lessonId)}`);
      if (id !== renderId) return;
      renderLesson(lesson, parts[2] || "read");
    } else if (view === "session") {
      const state = await api(`/api/sessions/${encodeURIComponent(parts[1])}`);
      if (id !== renderId) return;
      currentSession = state;
      renderSession(state, parts[2]);
    } else if (view === "practice") renderPractice();
    else if (view === "readiness") renderReadiness();
    else if (view === "sessions") renderSessions();
    else throw new Error("Page not found. Choose a lesson from the sidebar.");
    if (busy) setBusy(true, $("#busy-text").textContent);
    main.querySelectorAll(".article").forEach((article) => { void diagrams(article); });
  } catch (error) {
    main.innerHTML = `<div class="paper"><h2>Unable to open this page</h2><p>${escape(error.message)}</p><a class="button secondary" href="#/learn">Back to lessons</a></div>`;
  }
}

function renderLesson(lesson, tab) {
  const status = data.lessons.find((item) => item.id === lesson.id);
  $("#mobile-lesson").value = lesson.id;
  $(`[data-lesson="${lesson.id}"]`)?.classList.add("active");
  $("#breadcrumb").textContent = `${lesson.stage} / ${titles[lesson.track]}`;
  const required = data.lessons.filter((item) => item.required);
  const count = required.filter((item) => item.checkpoint?.passed).length;
  const actionLabel = status.active_session ? "Resume exercises" : status.completed ? "Practice again" : "Start exercises";
  main.innerHTML = pageHead(lesson.stage, lesson.title, `${lesson.minutes} min · Guide, knowledge check, two exercises`) + `
    <nav class="tabs" aria-label="Lesson sections"><a class="${tab === "read" ? "active" : ""}" href="#/learn/${lesson.id}">Learn</a><a class="${tab === "check" ? "active" : ""}" href="#/learn/${lesson.id}/check">Knowledge check${status.checkpoint?.passed ? " ✓" : ""}</a></nav>
    <div class="learn-layout"><div id="lesson-content"></div><aside class="side-stack">
      <section class="side-card"><h3>What you’ll learn</h3><ul class="objectives">${lesson.objectives.map((item) => `<li>${escape(item)}</li>`).join("")}</ul><button class="button full" id="start-exercises">${actionLabel} <span aria-hidden="true">→</span></button><p class="footnote">Exercise feedback uses your selected model.</p></section>
      ${lesson.prerequisites.length ? `<section class="side-card"><h3>Prerequisites</h3><ul>${lesson.prerequisites.map((id) => `<li><a href="#/learn/${id}">${escape(data.lessons.find((item) => item.id === id).title)}</a></li>`).join("")}</ul></section>` : ""}
      <section class="side-card"><h3>Your progress</h3><div class="side-number">${count}<span class="side-label"> / ${required.length}</span></div><div class="side-label">required checks passed</div><div class="progress-bar"><span style="width:${count / required.length * 100}%"></span></div><a class="text-link" href="#/learn">Continue learning →</a></section>
    </aside></div>`;
  $("#start-exercises").onclick = () => run("Opening exercises…", async () => {
    if (status.active_session) { location.hash = `#/session/${status.active_session}`; return; }
    const state = await api("/api/sessions", { mode: "training", lesson_id: lesson.id });
    await api(`/api/sessions/${state.id}/next`, {});
    await refresh();
    location.hash = `#/session/${state.id}`;
  });
  if (tab === "check") renderCheck(lesson, status.checkpoint);
  else {
    $("#lesson-content").innerHTML = `<article class="paper article">${cleanMarkdown(lesson.guide)}</article><div class="answer-actions"><span class="muted">Ready to check your understanding?</span><a class="button secondary" href="#/learn/${lesson.id}/check">Take the knowledge check →</a></div>`;
    $("#lesson-content .article h1")?.remove();
  }
}

function renderCheck(lesson, result) {
  $("#lesson-content").innerHTML = `<form id="check-form"><div class="paper" style="margin-bottom:24px"><h2>Check your understanding</h2><p class="muted">Choose an answer for each question. Aim for at least 80%; you can revisit the guide and retry.</p>${result ? `<span class="tag ${result.passed ? "good" : "warm"}">Last attempt: ${result.score}% · ${result.passed ? "Passed" : "Keep learning"}</span>` : ""}</div>
    ${lesson.checks.map((check, index) => `<fieldset class="checkpoint"><legend>${index + 1}. ${escape(check.question)}</legend>${check.options.map((option, value) => `<label class="option"><input type="radio" name="check-${index}" value="${value}" required ${result?.results[index]?.selected === value ? "checked" : ""}><span>${escape(option)}</span></label>`).join("")}${result ? `<div class="check-result ${result.results[index].correct ? "correct" : "incorrect"}"><strong>${result.results[index].correct ? "Correct" : "Review this concept"}</strong><br>${escape(result.results[index].explanation)}</div>` : ""}</fieldset>`).join("")}
    <div class="button-row"><button class="button" type="submit">${result ? "Check again" : "Check answers"}</button><a class="button secondary" href="#/learn/${lesson.id}">Back to guide</a></div></form>`;
  $("#check-form").onsubmit = (event) => {
    event.preventDefault();
    const answers = lesson.checks.map((_, index) => Number(new FormData(event.target).get(`check-${index}`)));
    void run("Checking answers…", async () => {
      const result = await api(`/api/checkpoints/${lesson.id}`, { answers });
      await refresh();
      renderLesson(lesson, "check");
      $("#lesson-content").scrollIntoView({ block: "start", behavior: "smooth" });
    });
  };
}

function renderPractice() {
  $("#breadcrumb").textContent = "Independent practice";
  main.innerHTML = pageHead("PUT IT INTO PRACTICE", "Your next interview starts here", "Try fresh questions without a worked example, or run a mock with feedback held until the end.") + `
    <div class="learn-layout"><form id="practice-form" class="paper"><h2>Configure a session</h2><div class="form-grid"><div class="field"><label for="track">Track</label><select id="track">${data.tracks.map((track) => `<option value="${track}">${titles[track]}</option>`).join("")}<option value="all">All six core tracks</option></select></div><div class="field"><label for="mode">Mode</label><select id="mode"><option value="practice">Practice — feedback after each answer</option><option value="mock">Mock — feedback at the end</option></select></div><div class="field"><label for="turns">Questions per track</label><select id="turns"><option value="2">2 questions</option><option value="1">1 question</option><option value="3">3 questions</option><option value="4">4 questions</option></select></div></div><button class="button" type="submit">Start session →</button><p class="footnote">Generates fresh questions using ${escape(data.provider)}. Code is reviewed, not executed.</p></form><aside class="side-card"><h3>Before you start</h3><p class="muted">Can you explain the basics and solve a new problem without hints?</p><a class="text-link" href="#/readiness">Review your evidence →</a></aside></div>`;
  const selected = new URLSearchParams(location.hash.split("?")[1]).get("track");
  if (data.tracks.includes(selected)) $("#track").value = selected;
  $("#practice-form").onsubmit = (event) => {
    event.preventDefault();
    const tracks = $("#track").value === "all" ? data.tracks.slice(0, 6) : [$("#track").value];
    const body = { mode: $("#mode").value, tracks, turns: Number($("#turns").value) };
    void run("Creating your session…", async () => {
      const state = await api("/api/sessions", body);
      await refresh();
      location.hash = `#/session/${state.id}`;
    });
  };
}

function renderReadiness() {
  $("#breadcrumb").textContent = "Readiness";
  main.innerHTML = pageHead("EVIDENCE, NOT JUST COMPLETION", "Are you ready for the simulator?", "Knowledge checks build the foundation. Fresh, unassisted answers show whether you can apply it.") + `
    <div class="cards">${data.readiness.map((item) => `<section class="paper readiness-card"><h2>${titles[item.track]}</h2><span class="tag ${item.status === "Ready for a mock" ? "good" : ""}">${item.status}</span><div class="metric-line"><span>Knowledge checks</span><strong>${item.checks_passed} / ${item.checks_total}</strong></div><div class="metric-line"><span>Recent independent attempts</span><strong>${item.independent_attempts} / 2</strong></div><div class="metric-line"><span>Recent scores</span><strong>${item.recent_scores.length ? item.recent_scores.join(", ") : "Not assessed"}</strong></div><a class="button secondary" href="${item.status === "Continue learning" ? `#/learn/${data.lessons.find((l) => l.track === item.track && (l.required || item.track === "post-training" || item.track === "research-engineering") && !l.checkpoint?.passed)?.id || item.track}` : `#/practice?track=${item.track}`}">${item.status === "Continue learning" ? "Continue learning" : "Start independent practice"} →</a></section>`).join("")}</div>
    <div class="paper" style="margin-top:24px"><h3>How readiness is calculated</h3><p>Pass each required knowledge check for a core track (at least 80%); optional tracks use their own checks. Then score at least 75/100 on each of your two most recent unassisted first attempts, with every rubric dimension at least 2/4 and no low-confidence review. Guided exercises, hints and revisions do not count as independent evidence. Active mock grades remain hidden.</p><p class="footnote">These are practice milestones, not a hiring prediction or certification. You can start the simulator at any time.</p></div>`;
}

function renderSessions() {
  $("#breadcrumb").textContent = "Saved sessions";
  main.innerHTML = pageHead("PICK UP WHERE YOU LEFT OFF", "Your sessions") + `<div class="paper">${data.sessions.length ? data.sessions.map((s) => `<div class="session-row"><div><strong>${escape(s.title)}</strong><small>${escape(s.mode)} · ${new Date(s.created_at).toLocaleDateString()} · ${s.completed ? "Complete" : "In progress"}</small></div><a class="button secondary small" href="#/session/${s.id}">${s.completed ? "View" : "Resume"}</a></div>`).join("") : `<div class="empty"><h2>No sessions yet</h2><a class="button" href="#/learn">Start diagnostic →</a></div>`}</div>`;
}

function renderSession(state, tab) {
  const training = state.mode === "training";
  const q = state.questions.at(-1);
  const attempt = q?.attempts.at(-1);
  const total = state.tracks.length * state.turns_per_round;
  const title = state.lesson?.title || titles[q?.track || state.tracks[0]];
  $("#breadcrumb").textContent = `${training ? "Guided exercises" : state.mode === "mock" ? "Mock interview" : "Independent practice"} / ${state.id}`;
  if (state.lesson) {
    $(`[data-lesson="${state.lesson.id}"]`)?.classList.add("active");
    $("#mobile-lesson").value = state.lesson.id;
  }
  main.innerHTML = pageHead(training ? "APPLY WHAT YOU LEARNED" : "INTERVIEW SIMULATOR", title, state.completed_at ? "Session complete" : `${training ? "Exercise" : "Question"} ${state.questions.length || 1} of ${total}`,
    '<a class="button secondary" href="#/sessions">Save & leave</a>') + `<div id="session-content"></div>`;
  if (state.completed_at) {
    $("#session-content").innerHTML = `<div class="paper"><h2>Session complete</h2><p class="muted">${training ? "Your exercises have been reviewed. Take the knowledge check or try a fresh practice question next." : "Review the evidence and choose your next practice focus."}</p><div class="button-row"><a class="button" href="${training ? `#/learn/${state.lesson.id}/check` : "#/readiness"}">${training ? "Knowledge check" : "View readiness"} →</a><a class="button secondary" href="#/practice">Independent practice</a></div></div>${state.questions.map((entry, index) => `<section class="paper" style="margin-top:22px"><h2>${index + 1}. ${escape(entry.question.title)}</h2>${feedbackHTML(entry.attempts.at(-1))}<details><summary>Your submitted answer</summary><div class="article">${cleanMarkdown(entry.attempts.at(-1)?.answer)}</div></details></section>`).join("")}`;
    return;
  }
  if (!q) {
    $("#session-content").innerHTML = `<section class="paper"><h2>Session ready</h2><p class="muted">Generate your first question when you’re ready.</p><button class="button" id="next-question">Generate question →</button></section>`;
    $("#next-question").onclick = () => performSession("next", {}, "Generating your question…");
    return;
  }
  if (tab === "lesson" && training) {
    $("#session-content").innerHTML = `<nav class="tabs"><a class="active" href="#/session/${state.id}/lesson">Guide</a><a href="#/session/${state.id}">Exercise</a></nav><article class="paper article">${cleanMarkdown(state.lesson.guide)}</article>`;
    return;
  }
  if (attempt && (tab !== "revise" || !attempt.graded || state.mode === "mock")) {
    const last = state.questions.length === total;
    const pending = !attempt.graded;
    $("#session-content").innerHTML = `<div class="paper"><h2>${escape(q.question.title)}</h2>${pending ? '<p>Your answer is saved. Its review has not completed.</p>' : state.feedback_locked ? '<p>Answer recorded. Feedback unlocks when the mock is complete.</p>' : feedbackHTML(attempt)}<div class="button-row" style="margin-top:22px">${pending ? '<button class="button" id="retry-grade">Retry review</button>' : `<button class="button" id="continue-session">${last ? "Finish session" : training ? "Next exercise" : "Next question"} →</button>${state.mode !== "mock" ? `<a class="button secondary" href="#/session/${state.id}/revise">Revise answer</a>` : ""}`}<a class="button secondary" href="#/sessions">Pause</a></div><details><summary>Your submitted answer</summary><div class="article">${cleanMarkdown(attempt.answer)}</div></details></div>`;
    if (pending) $("#retry-grade").onclick = () => performSession("grade", {}, "Reviewing your saved answer…");
    else $("#continue-session").onclick = () => performSession(last ? "finish" : "next", {}, last ? "Finishing session…" : "Opening the next question…");
    return;
  }
  if (tab === "revise" && state.mode === "mock") { location.hash = `#/session/${state.id}`; return; }
  const coding = q.track === "coding" || Boolean(q.question.starter_code);
  const design = q.track === "system-design";
  const useEditor = coding || design;
  $("#session-content").innerHTML = `<div class="workspace"><section class="paper question-pane"><div class="tags" style="margin:0 0 14px"><span class="tag">${q.question.minutes} min suggested</span><span class="tag">${training ? "Guided practice" : "Level " + q.difficulty}</span></div><h2>${escape(q.question.title)}</h2><div class="article">${cleanMarkdown(q.question.prompt)}</div>${q.question.constraints.length ? `<h3>Constraints</h3><ul>${q.question.constraints.map((item) => `<li>${escape(item)}</li>`).join("")}</ul>` : ""}<h3>Success criteria</h3><ul>${q.question.acceptance_checks.map((item) => `<li>${escape(item)}</li>`).join("")}</ul>${training ? `<a class="text-link" href="#/session/${state.id}/lesson">Read the lesson →</a>` : ""}</section><section><form id="answer-form">${useEditor ? `<div class="editor-panel"><div class="editor-toolbar"><label class="editor-label" for="editor-language">${coding ? "Your code" : "Design answer"}</label><select id="editor-language" aria-label="Editor language">${coding ? '<option value="python">Python</option><option value="javascript">JavaScript</option>' : '<option value="markdown">Markdown / Mermaid</option>'}</select><button class="button secondary small" type="button" id="reset-starter">Reset ${coding ? "starter" : "draft"}</button></div><div id="code-editor"></div><div class="editor-footer"><span>${coding ? "Tab to indent · Ctrl+/ to comment · Esc then Tab to leave" : "Markdown + Mermaid diagram support"}</span><span>Not executed</span></div></div>${coding ? '<div class="field"><label for="explanation">Reasoning & tests</label><textarea id="explanation" placeholder="Explain your approach, complexity and test cases."></textarea></div>' : '<div class="button-row" style="margin-top:14px"><button class="button secondary small" type="button" id="preview-design">Preview answer & diagram</button></div><div id="design-preview" class="paper article preview-panel" hidden></div>'}` : '<div class="field" style="margin-top:0"><label for="written-answer">Your answer</label><textarea id="written-answer" class="long" placeholder="State your assumptions, reasoning and evidence."></textarea></div>'}
      <div class="field"><label for="answer-file">Import an answer file</label><input id="answer-file" class="file-input" type="file" accept=".py,.js,.ts,.md,.txt,.json,.sql"></div><div class="answer-actions"><button class="button" type="submit">${tab === "revise" ? "Submit revision" : "Submit for review"} →</button><span class="draft-status" id="draft-status">Draft saved in this browser</span></div></form></section></div>`;
  setupAnswer(state, { coding, design, useEditor, revise: tab === "revise" });
  
}

function feedbackHTML(attempt) {
  if (!attempt?.evaluation) return "";
  const e = attempt.evaluation;
  return `<div class="feedback-score"><div class="score">${attempt.score}<span> / 100</span></div><div><strong>Answer review</strong><div class="muted">${attempt.assisted ? "Guided / assisted" : "Unassisted"} · ${escape(e.confidence)} confidence</div></div></div><div class="rubric">${e.dimensions.map((d) => `<div class="rubric-item"><strong>${escape(d.name)}<span>${d.score}/4</span></strong><p>${escape(d.evidence)}</p><p><b>Next:</b> ${escape(d.improvement)}</p></div>`).join("")}</div><div class="feedback-columns"><div><h3>What worked</h3><ul>${e.strengths.map((s) => `<li>${escape(s)}</li>`).join("")}</ul></div><div><h3>Keep practicing</h3><ul>${e.gaps.map((s) => `<li>${escape(s)}</li>`).join("")}</ul></div></div><div class="article" style="padding:0"><h3>Learn from this attempt</h3>${cleanMarkdown(e.lesson)}<h3>Try next</h3>${cleanMarkdown(e.exercise)}</div>`;
}

function languageExtension(language) {
  return language === "javascript" ? javascript() : language === "markdown" ? markdown() : python();
}

function setupAnswer(state, options) {
  const q = state.questions.at(-1);
  const previous = q.attempts.at(-1)?.answer || "";
  const fence = previous.match(/^```(\w*)\n([\s\S]*?)\n```\n?([\s\S]*)$/);
  const starter = q.question.starter_code || (options.design ? "## Requirements\n\n\n## Architecture\n\n```mermaid\nflowchart LR\n    Client --> API\n```\n\n## Capacity & tradeoffs\n\n\n## Failure handling\n\n" : "");
  draftKey = `grey:${data.draft_namespace}:${state.id}:${state.questions.length}`;
  draft = { code: options.revise ? (fence ? fence[2] : previous) : starter, explanation: fence?.[3]?.trim() || "", answer: previous, language: options.design ? "markdown" : "python" };
  try { const stored = JSON.parse(localStorage.getItem(draftKey)); if (stored && typeof stored === "object") draft = { ...draft, ...stored }; }
  catch { notice("Browser draft storage is unavailable. Submitted answers are still saved by the app."); }
  if (options.useEditor) {
    if (!["python", "javascript", "markdown"].includes(draft.language)) draft.language = "python";
    if (options.design) draft.language = "markdown";
    $("#editor-language").value = draft.language;
    languageSlot = new Compartment();
    editor = new EditorView({ doc: draft.code, parent: $("#code-editor"), extensions: [
      basicSetup, keymap.of([indentWithTab]), indentUnit.of("    "),
      languageSlot.of(languageExtension(draft.language)), editableSlot.of(EditorView.editable.of(true)),
      EditorView.contentAttributes.of({ "aria-label": options.coding ? "Code answer editor" : "Markdown design editor", spellcheck: "false" }),
      EditorView.updateListener.of((update) => { if (update.docChanged) { draft.code = update.state.doc.toString(); saveDraft(); } }),
    ] });
    $("#editor-language").onchange = (event) => { draft.language = event.target.value; editor.dispatch({ effects: languageSlot.reconfigure(languageExtension(draft.language)) }); saveDraft(); };
    $("#reset-starter").onclick = () => { if (confirm("Replace your current editor contents with the starter?")) editor.dispatch({ changes: { from: 0, to: editor.state.doc.length, insert: starter } }); };
    if (options.coding) {
      $("#explanation").value = draft.explanation;
      $("#explanation").oninput = (event) => { draft.explanation = event.target.value; saveDraft(); };
    } else $("#preview-design").onclick = () => { const preview = $("#design-preview"); preview.hidden = false; preview.innerHTML = cleanMarkdown(editor.state.doc.toString()); void diagrams(preview); };
  } else {
    $("#written-answer").value = draft.answer;
    $("#written-answer").oninput = (event) => { draft.answer = event.target.value; saveDraft(); };
  }
  $("#answer-file").onchange = async (event) => {
    const file = event.target.files[0];
    if (!file) return;
    if (file.size > 240000) { notice("Answer file is too large (maximum 240 KB)."); return; }
    if (!confirm("Replace the current answer with this file?")) return;
    const value = await file.text();
    if (editor) editor.dispatch({ changes: { from: 0, to: editor.state.doc.length, insert: value } });
    else { draft.answer = value; $("#written-answer").value = value; saveDraft(); }
  };
  $("#answer-form").onsubmit = (event) => {
    event.preventDefault();
    const content = options.useEditor ? editor.state.doc.toString() : draft.answer;
    if (!content.trim()) { notice("Write an answer before submitting."); return; }
    const answer = options.coding ? `\`\`\`${draft.language}\n${content}\n\`\`\`\n\n${draft.explanation}` : content;
    if (answer.length > 60000) { notice("Answer is too long (maximum 60,000 characters)."); return; }
    saveDraft();
    void performSession("answer", { answer, revise: options.revise }, "Submitting your answer and requesting review…");
  };
}

function saveDraft() {
  try { localStorage.setItem(draftKey, JSON.stringify(draft)); if ($("#draft-status")) $("#draft-status").textContent = "Draft saved in this browser"; }
  catch { if ($("#draft-status")) $("#draft-status").textContent = "Draft not saved — copy your answer before leaving"; }
}

function performSession(action, body, label) {
  const sid = currentSession.id;
  return run(label, async () => {
    try {
      currentSession = await api(`/api/sessions/${sid}/${action}`, body);
      await refresh();
      if (location.hash !== `#/session/${sid}`) location.hash = `#/session/${sid}`;
      else await route();
    } catch (error) {
      // A failed review may have already committed the answer; show the retry state.
      try { await refresh(); currentSession = await api(`/api/sessions/${sid}`); resetView(); renderSession(currentSession); }
      catch { /* Preserve the original error and existing draft if the server went away. */ }
      throw error;
    }
  });
}

document.addEventListener("click", (event) => {
  if (event.target.closest(".skip-link")) { event.preventDefault(); main.focus(); main.scrollIntoView(); }
  if (busy && event.target.closest("a")) event.preventDefault();
});
window.addEventListener("hashchange", () => { notice(); void route(); });
window.addEventListener("beforeunload", (event) => { if (busy || chatPending) { event.preventDefault(); event.returnValue = ""; } });

try {
  await refresh();
  await route();
} catch (error) {
  notice(error.message);
  main.innerHTML = '<div class="paper"><h2>Workspace unavailable</h2><p>Keep the terminal running and reload this page.</p></div>';
}


// The tutor lives outside the routed page so navigation never discards the chat.
const chat = document.createElement("aside");
chat.id = "ai-tutor";
chat.setAttribute("aria-label", "AI tutor");
chat.innerHTML = `<button class="button tutor-launch" id="chat-open" aria-expanded="false" aria-controls="chat-panel">✦ Ask your tutor</button>
<section id="chat-panel" class="chat-panel" hidden><header class="chat-header"><div><strong>Your AI tutor</strong><div id="chat-context" class="footnote"></div></div><button type="button" id="chat-close" aria-label="Minimize tutor">−</button></header>
<div id="chat-messages" class="chat-messages" role="log" aria-label="Tutor conversation"></div>
<div id="chat-status" class="chat-status" role="status"></div>
<form id="chat-form"><label class="chat-label" for="chat-question">Ask a question</label><textarea id="chat-question" rows="3" maxlength="6000" placeholder="Ask about Python, system design, or this lesson…" required></textarea><div class="chat-actions"><span class="footnote">${escape(data?.tutor_model || "Configured model")} · ${escape(data?.tutor_effort || "default")}</span><button class="button" id="chat-send" type="submit">Send ↑</button></div></form></section>`;
document.body.append(chat);
const chatInput = $("#chat-question");
const chatStorageKey = `grey:tutor-draft:${data?.draft_namespace || location.origin}`;
try { chatInput.value = localStorage.getItem(chatStorageKey) || ""; } catch { /* Storage is optional. */ }
chatInput.oninput = () => { try { localStorage.setItem(chatStorageKey, chatInput.value); } catch { /* Keep the input usable. */ } };
function chatContext() {
  const parts = location.hash.split("?")[0].replace(/^#\/?/, "").split("/");
  if (parts[0] === "learn") return { lesson_id: parts[1] || defaultLesson() };
  if (parts[0] === "session") return { session_id: parts[1] };
  if (!parts[0]) return { lesson_id: defaultLesson() };
  return {};
}
function updateChatContext() {
  const context = chatContext();
  const lesson = data?.lessons.find((item) => item.id === context.lesson_id);
  const session = data?.sessions.find((item) => item.id === context.session_id);
  $("#chat-context").textContent = session?.mode === "mock" && !session.completed ? "Mock: requirements only" : session?.mode === "practice" && !session.completed ? "Practice: help counts as assisted" : lesson?.title || session?.title || "General learning";
}
async function showChatMessages(messages) {
  const container = $("#chat-messages");
  container.innerHTML = messages.length ? messages.map((item) => `<div class="chat-turn"><div class="chat-user">${escape(item.message)}</div><div class="chat-context-label">${escape(item.context)}</div><div class="chat-reply article">${cleanMarkdown(item.reply)}</div></div>`).join("") : '<div class="chat-empty">What would you like to understand?</div>';
  await diagrams(container);
  container.scrollTop = container.scrollHeight;
}
$("#chat-open").onclick = async () => {
  $("#chat-panel").hidden = false;
  $("#chat-open").hidden = true;
  $("#chat-open").setAttribute("aria-expanded", "true");
  updateChatContext();
  chatInput.focus();
  if (!chatPending) {
    try { await showChatMessages((await api("/api/tutor")).messages); }
    catch (error) { $("#chat-status").textContent = error.message; }
  }
};
$("#chat-close").onclick = () => {
  $("#chat-panel").hidden = true;
  $("#chat-open").hidden = false;
  $("#chat-open").setAttribute("aria-expanded", "false");
  $("#chat-open").focus();
};
$("#chat-form").onsubmit = async (event) => {
  event.preventDefault();
  if (chatPending || busy || !chatInput.value.trim()) return;
  const message = chatInput.value.trim();
  const context = chatContext();
  chatPending = true;
  $("#chat-send").disabled = true;
  chatInput.readOnly = true;
  $("#chat-status").textContent = "Your tutor is thinking…";
  try {
    const response = await api("/api/tutor", { message, ...context });
    chatInput.value = "";
    chatInput.oninput();
    await showChatMessages(response.messages);
    $("#chat-status").textContent = "";
  } catch (error) { $("#chat-status").textContent = error.message + " Your question is kept; send it again to retry."; }
  finally {
    chatPending = false;
    $("#chat-send").disabled = false;
    chatInput.readOnly = false;
    chatInput.focus();
  }
};
chatInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) { event.preventDefault(); $("#chat-form").requestSubmit(); }
});
window.addEventListener("hashchange", updateChatContext);
updateChatContext();
