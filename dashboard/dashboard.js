// EDIT THESE: your GitHub org/user and repo name
const OWNER = "your-github-username";
const REPO = "quant-mc-simulator";

const API_URL = `https://api.github.com/repos/${OWNER}/${REPO}/commits?per_page=100`;

async function loadCommits() {
  const statusEl = document.getElementById("status");
  try {
    const res = await fetch(API_URL);
    if (!res.ok) {
      throw new Error(`GitHub API returned ${res.status}. Check OWNER/REPO in dashboard.js, or you've hit the unauthenticated rate limit (60 req/hr).`);
    }
    const commits = await res.json();
    statusEl.textContent = `Loaded ${commits.length} commits from ${OWNER}/${REPO}`;
    statusEl.classList.remove("error");

    renderAuthorBars(commits);
    renderTimeline(commits);
    renderCommitList(commits);
  } catch (err) {
    statusEl.textContent = `Error: ${err.message}`;
    statusEl.classList.add("error");
  }
}

function renderAuthorBars(commits) {
  const counts = {};
  commits.forEach((c) => {
    const name = c.commit?.author?.name || "unknown";
    counts[name] = (counts[name] || 0) + 1;
  });

  const max = Math.max(...Object.values(counts), 1);
  const container = document.getElementById("authorBars");
  container.innerHTML = "";

  Object.entries(counts)
    .sort((a, b) => b[1] - a[1])
    .forEach(([name, count]) => {
      const row = document.createElement("div");
      row.className = "author-row";
      row.innerHTML = `
        <div class="author-name">${escapeHtml(name)}</div>
        <div class="author-bar-track">
          <div class="author-bar-fill" style="width:${(count / max) * 100}%"></div>
        </div>
        <div class="author-count">${count}</div>
      `;
      container.appendChild(row);
    });
}

function renderTimeline(commits) {
  const counts = {};
  commits.forEach((c) => {
    const date = (c.commit?.author?.date || "").slice(0, 10);
    if (!date) return;
    counts[date] = (counts[date] || 0) + 1;
  });

  const dates = Object.keys(counts).sort();
  const values = dates.map((d) => counts[d]);

  const canvas = document.getElementById("timelineChart");
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  if (dates.length === 0) return;

  const max = Math.max(...values, 1);
  const padding = 30;
  const w = canvas.width - padding * 2;
  const h = canvas.height - padding * 2;
  const barWidth = w / dates.length;

  ctx.fillStyle = "#4f7cff";
  values.forEach((v, i) => {
    const barHeight = (v / max) * h;
    const x = padding + i * barWidth;
    const y = canvas.height - padding - barHeight;
    ctx.fillRect(x, y, barWidth * 0.7, barHeight);
  });

  // axis line
  ctx.strokeStyle = "#2a2d3a";
  ctx.beginPath();
  ctx.moveTo(padding, canvas.height - padding);
  ctx.lineTo(canvas.width - padding, canvas.height - padding);
  ctx.stroke();

  // date labels (first, middle, last only — avoid clutter)
  ctx.fillStyle = "#9aa0ac";
  ctx.font = "10px system-ui";
  [0, Math.floor(dates.length / 2), dates.length - 1].forEach((i) => {
    if (i < 0 || i >= dates.length) return;
    ctx.fillText(dates[i], padding + i * barWidth, canvas.height - 10);
  });
}

function renderCommitList(commits) {
  const list = document.getElementById("commitList");
  list.innerHTML = "";

  commits.slice(0, 25).forEach((c) => {
    const li = document.createElement("li");
    const msg = (c.commit?.message || "").split("\n")[0];
    const author = c.commit?.author?.name || "unknown";
    const date = (c.commit?.author?.date || "").slice(0, 10);
    li.innerHTML = `
      <div class="msg">${escapeHtml(msg)}</div>
      <div class="meta">${escapeHtml(author)} · ${date}</div>
    `;
    list.appendChild(li);
  });
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

loadCommits();
