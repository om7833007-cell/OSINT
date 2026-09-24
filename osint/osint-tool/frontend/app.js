const API_BASE = "http://localhost:8000";

document.getElementById("search-btn").addEventListener("click", runSearch);

async function runSearch() {
  const target = document.getElementById("target-input").value.trim();
  const purpose = document.getElementById("purpose-input").value.trim();

  if (!target) return alert("Enter a target first.");
  if (!purpose) return alert("Please enter a purpose for this search.");

  document.getElementById("results-panel").innerHTML = "<p>Starting search...</p>";
  document.getElementById("flags-panel").innerHTML = "";

  let res;
  try {
    res = await fetch(`${API_BASE}/api/search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ target, purpose }),
    });
  } catch (err) {
    document.getElementById("results-panel").innerHTML =
      `<p>Could not reach the backend. Is it running at ${API_BASE}?</p>`;
    return;
  }

  if (!res.ok) {
    const err = await res.json();
    document.getElementById("results-panel").innerHTML = `<p>Error: ${err.detail}</p>`;
    return;
  }

  const { job_id } = await res.json();
  pollJob(job_id);
}

async function pollJob(jobId) {
  const poll = async () => {
    const res = await fetch(`${API_BASE}/api/search/${jobId}`);
    const job = await res.json();
    renderResults(job);

    if (job.status !== "done") {
      setTimeout(poll, 1200);
    }
  };
  poll();
}

function renderResults(job) {
  const panel = document.getElementById("results-panel");
  panel.innerHTML = "";

  for (const [moduleName, data] of Object.entries(job.results)) {
    const card = document.createElement("div");
    card.className = "result-card";
    card.innerHTML = `<h3>${moduleName}</h3><pre>${escapeHtml(JSON.stringify(data, null, 2))}</pre>`;
    panel.appendChild(card);

    if (moduleName === "geolocation" && !data.error) {
      plotLocation(data);
    }
  }

  const flagsPanel = document.getElementById("flags-panel");
  flagsPanel.innerHTML = "";
  (job.flags || []).forEach(f => {
    const card = document.createElement("div");
    card.className = "flag-card";
    card.innerHTML = `<strong>${f.type}</strong> (confidence: ${f.confidence})<br>${f.detail}`;
    flagsPanel.appendChild(card);
  });

  if (job.status === "done" && Object.keys(job.results).length === 0) {
    panel.innerHTML = "<p>No modules ran for this target type.</p>";
  }
}

function escapeHtml(str) {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}
