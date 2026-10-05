const form = document.querySelector("#decision-form");
const lookupForm = document.querySelector("#lookup-form");
const resultPanel = document.querySelector("#result-panel");
const resultStatus = document.querySelector("#result-status");
const resultContent = document.querySelector("#result-content");
const toast = document.querySelector("#toast");
let toastTimeout;

document.querySelector("#today-label").textContent = new Intl.DateTimeFormat("en", {
  weekday: "short",
  month: "short",
  day: "numeric",
}).format(new Date());

function showToast(message) {
  toast.textContent = message;
  toast.classList.add("visible");
  window.clearTimeout(toastTimeout);
  toastTimeout = window.setTimeout(() => toast.classList.remove("visible"), 3200);
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: { "Content-Type": "application/json", ...options.headers },
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = typeof payload.detail === "string" ? payload.detail : "The request could not be completed.";
    throw new Error(detail);
  }
  return payload;
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[character]);
}

function setStatus(status) {
  resultStatus.textContent = status.replaceAll("_", " ");
  resultStatus.className = "status-badge";
  if (status === "PENDING_APPROVAL") resultStatus.classList.add("pending");
  if (status === "REJECTED" || status === "ROLLED_BACK") resultStatus.classList.add(status.toLowerCase().replace("_", "-"));
}

function metric(label, value) {
  return `<div class="result-metric"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`;
}

function renderDecision(response) {
  const result = response.decision ?? response.result ?? {};
  const request = response.request ?? {};
  const status = response.status ?? "COMPLETED";
  const id = response.decision_id;
  setStatus(status);

  const summary = result.recommendation
    ? `<p class="recommendation">${escapeHtml(result.recommendation)}</p>`
    : `<p class="recommendation">${escapeHtml(request.category ? `Decision for ${request.category}` : "Decision details loaded")}</p>`;
  const metrics = result.recommendation ? `<div class="result-metrics">
    ${metric("REVENUE LIFT", `${Number(result.expected_revenue_lift_pct ?? 0).toFixed(1)}%`)}
    ${metric("MARGIN DELTA", `${Number(result.expected_margin_delta_pct ?? 0).toFixed(1)}%`)}
    ${metric("ASSORTMENT", result.assortment?.action ?? "—")}
    ${metric("GUARDRAILS", result.guardrails_passed ? "PASSED" : "REVIEW")}
  </div>` : "";

  const recommendations = result.assortment || result.promotion ? `<div class="result-block"><h3>RECOMMENDATION DETAIL</h3><div class="recommendation-grid">
    ${result.assortment ? `<article class="recommendation-card"><span>ASSORTMENT · ${escapeHtml(result.assortment.risk ?? "")}</span><strong>${escapeHtml(result.assortment.action)}</strong><p>${escapeHtml(result.assortment.rationale)}</p></article>` : ""}
    ${result.promotion ? `<article class="recommendation-card"><span>PROMOTION · ${escapeHtml(result.promotion.risk ?? "")}</span><strong>${escapeHtml(result.promotion.action)} · ${Number(result.promotion.discount_pct ?? 0).toFixed(1)}% off</strong><p>${escapeHtml(result.promotion.rationale)}</p></article>` : ""}
  </div></div>` : "";

  const citations = Array.isArray(result.citations) && result.citations.length ? `<div class="result-block"><h3>EVIDENCE</h3><div class="citation-list">${result.citations.map((citation) => `<div class="citation-item"><span>${escapeHtml(citation.title)}</span><small>${escapeHtml(citation.source_type)} · ${Number(citation.relevance ?? 0).toFixed(2)}</small></div>`).join("")}</div></div>` : "";
  let controls = "";
  if (status === "PENDING_APPROVAL" && response.approval_id) {
    controls = `<form class="approval-actions" id="approval-form" data-approval-id="${escapeHtml(response.approval_id)}">
      <label>Approver<input name="approver" required minlength="2" value="Jordan Davis" /></label>
      <label>Review note<input name="comment" maxlength="1000" placeholder="Optional context" /></label>
      <button class="action-button approve-button" name="approved" value="true" type="submit">Approve decision</button>
      <button class="action-button reject-button" name="approved" value="false" type="submit">Reject</button>
    </form>`;
  } else if (status === "APPROVED") {
    controls = `<form class="approval-actions" id="rollback-form" data-decision-id="${escapeHtml(id)}"><label>Rollback reason<input name="reason" required minlength="5" maxlength="1000" placeholder="Why should this decision be rolled back?" /></label><input type="hidden" name="actor" value="Jordan Davis" /><button class="action-button rollback-button" type="submit">Roll back decision</button></form>`;
  }

  resultContent.innerHTML = `${id ? `<div class="result-id">ID ${escapeHtml(id)} <button class="copy-id" type="button" data-copy="${escapeHtml(id)}">Copy ID</button></div>` : ""}${summary}${metrics}${recommendations}${citations}${result.approval_reason ? `<div class="result-block"><h3>APPROVAL REASON</h3><p class="lookup-hint">${escapeHtml(result.approval_reason)}</p></div>` : ""}${controls}`;
  resultPanel.hidden = false;
  resultPanel.scrollIntoView({ behavior: "smooth", block: "start" });
}

async function loadHealth() {
  const dot = document.querySelector("#connection-dot");
  const title = document.querySelector("#connection-title");
  const detail = document.querySelector("#connection-detail");
  try {
    await api("/health");
    dot.classList.add("online");
    title.textContent = "API connected";
    detail.textContent = "Decision engine reachable";
  } catch {
    dot.classList.add("offline");
    title.textContent = "API unavailable";
    detail.textContent = "Check the backend service";
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!form.reportValidity()) return;
  const button = form.querySelector("button[type='submit']");
  button.disabled = true;
  button.querySelector(".button-label").textContent = "Analyzing category…";
  try {
    const values = new FormData(form);
    const response = await api("/v1/decisions", {
      method: "POST",
      body: JSON.stringify({
        category: values.get("category").trim(),
        objective: values.get("objective").trim(),
        store_cluster: values.get("store_cluster").trim(),
        horizon_days: Number(values.get("horizon_days")),
        requested_by: values.get("requested_by").trim(),
        constraints: {
          max_discount_pct: Number(values.get("max_discount_pct")),
          min_margin_pct: Number(values.get("min_margin_pct")),
          min_inventory_days: 7,
        },
      }),
    });
    renderDecision(response);
    showToast(response.status === "PENDING_APPROVAL" ? "Recommendation ready for human approval." : "Recommendation generated.");
  } catch (error) {
    showToast(error.message);
  } finally {
    button.disabled = false;
    button.querySelector(".button-label").textContent = "Generate recommendation";
  }
});

lookupForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const id = new FormData(lookupForm).get("decision_id").trim();
  if (!id) return;
  try {
    const response = await api(`/v1/decisions/${encodeURIComponent(id)}`);
    renderDecision(response);
  } catch (error) {
    showToast(error.message);
  }
});

resultContent.addEventListener("click", async (event) => {
  const button = event.target.closest("[data-copy]");
  if (!button) return;
  try {
    await navigator.clipboard.writeText(button.dataset.copy);
    showToast("Decision ID copied.");
  } catch {
    showToast("Could not access clipboard.");
  }
});

resultContent.addEventListener("submit", async (event) => {
  event.preventDefault();
  const currentForm = event.target;
  const values = new FormData(currentForm);
  try {
    if (currentForm.id === "approval-form") {
      const submitter = event.submitter;
      const response = await api(`/v1/approvals/${encodeURIComponent(currentForm.dataset.approvalId)}`, {
        method: "POST",
        body: JSON.stringify({
          approved: submitter.value === "true",
          approver: values.get("approver").trim(),
          comment: values.get("comment").trim() || null,
        }),
      });
      renderDecision(response);
      showToast(response.status === "APPROVED" ? "Decision approved." : "Decision rejected.");
    } else if (currentForm.id === "rollback-form") {
      const response = await api(`/v1/decisions/${encodeURIComponent(currentForm.dataset.decisionId)}/rollback`, {
        method: "POST",
        body: JSON.stringify({ actor: values.get("actor"), reason: values.get("reason").trim() }),
      });
      renderDecision(response);
      showToast("Decision rolled back.");
    }
  } catch (error) {
    showToast(error.message);
  }
});

loadHealth();