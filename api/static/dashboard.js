Chart.defaults.font.family = "Inter, system-ui, sans-serif";
Chart.defaults.font.size = 11;
Chart.defaults.color = "#64748b";
Chart.defaults.borderColor = "rgba(0,0,0,0.06)";
Chart.defaults.plugins.legend.labels.boxWidth = 8;
Chart.defaults.plugins.legend.labels.boxHeight = 8;
Chart.defaults.plugins.legend.labels.padding = 16;
Chart.defaults.plugins.legend.labels.usePointStyle = true;

const COLORS = {
  blue: "#2563eb",
  green: "#16a34a",
  orange: "#ea580c",
  red: "#dc2626",
  gray: "#94a3b8",
  bluePalette: ["#1d4ed8", "#2563eb", "#3b82f6", "#60a5fa", "#93c5fd"],
  sentimentColors: ["#16a34a", "#94a3b8", "#dc2626"],
  urgencyColors: ["#16a34a", "#ea580c", "#dc2626"],
};

function getBadgeClass(type, value) {
  const v = (value || "").toLowerCase();
  if (type === "sentiment") {
    if (v === "positive") return "badge-positive";
    if (v === "negative") return "badge-negative";
    return "badge-neutral";
  }
  if (type === "urgency") {
    if (v === "urgent") return "badge-urgent";
    if (v === "high") return "badge-high";
    return "badge-normal";
  }
  return "badge-neutral";
}

function formatTime(ts) {
  if (!ts) return "—";
  const d = new Date(ts);
  return isNaN(d) ? ts : d.toLocaleString(undefined, {
    month: "short", day: "numeric",
    hour: "2-digit", minute: "2-digit"
  });
}

function getTopKey(counts) {
  if (!counts) return "—";
  const entries = Object.entries(counts).filter(([, v]) => v > 0);
  if (!entries.length) return "—";
  return entries.sort((a, b) => b[1] - a[1])[0][0];
}

function renderChart(id, config) {
  const canvas = document.getElementById(id);
  if (!canvas) return;
  const existing = Chart.getChart(canvas);
  if (existing) existing.destroy();
  return new Chart(canvas.getContext("2d"), config);
}

function doughnutCenter(total, label) {
  return {
    id: "centerText",
    beforeDraw(chart) {
      const { ctx, chartArea: { width, height, top } } = chart;
      ctx.save();
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      const cx = width / 2;
      const cy = top + height / 2;
      ctx.font = "600 22px Inter, system-ui";
      ctx.fillStyle = "#0f172a";
      ctx.fillText(total, cx, cy - 8);
      ctx.font = "400 11px Inter, system-ui";
      ctx.fillStyle = "#94a3b8";
      ctx.fillText(label, cx, cy + 12);
      ctx.restore();
    }
  };
}

async function fetchStats() {
  try {
    const res = await fetch("/dashboard/stats");
    if (!res.ok) return;
    const data = await res.json();

    document.getElementById("total-articles").textContent =
      data.total_articles ?? "—";
    document.getElementById("avg-latency").textContent =
      data.avg_latency_ms != null
        ? Number(data.avg_latency_ms).toFixed(2)
        : "—";
    document.getElementById("top-sentiment").textContent =
      getTopKey(data.sentiment_counts);
    document.getElementById("top-urgency").textContent =
      getTopKey(data.urgency_counts);
    document.getElementById("last-updated").textContent =
      new Date().toLocaleTimeString();

    const sentimentLabels = ["positive", "neutral", "negative"];
    const sentimentValues = sentimentLabels.map(l => data.sentiment_counts?.[l] || 0);
    const sentimentTotal = sentimentValues.reduce((a, b) => a + b, 0);

    renderChart("sentimentChart", {
      type: "doughnut",
      plugins: [doughnutCenter(sentimentTotal, "articles")],
      data: {
        labels: sentimentLabels,
        datasets: [{
          data: sentimentValues,
          backgroundColor: COLORS.sentimentColors,
          borderWidth: 3,
          borderColor: "#f0f4f8",
          hoverOffset: 6,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: "72%",
        plugins: {
          legend: {
            position: "bottom",
            labels: { color: "#475569" }
          }
        }
      }
    });

    const catLabels = Object.keys(data.category_counts || {});
    const catValues = catLabels.map(l => data.category_counts[l]);

    renderChart("categoryChart", {
      type: "bar",
      data: {
        labels: catLabels,
        datasets: [{
          label: "Articles",
          data: catValues,
          backgroundColor: COLORS.bluePalette.slice(0, catLabels.length),
          borderRadius: 6,
          borderSkipped: false,
          barThickness: 48,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: ctx => ` ${ctx.parsed.y} articles`
            }
          }
        },
        scales: {
          x: {
            grid: { display: false },
            ticks: { color: "#64748b", font: { size: 12 } }
          },
          y: {
            beginAtZero: true,
            grid: { color: "rgba(0,0,0,0.04)" },
            ticks: {
              color: "#94a3b8",
              stepSize: 1,
              font: { size: 11 }
            }
          }
        }
      }
    });

    const urgencyLabels = ["normal", "high", "urgent"];
    const urgencyValues = urgencyLabels.map(l => data.urgency_counts?.[l] || 0);
    const urgencyTotal = urgencyValues.reduce((a, b) => a + b, 0);

    renderChart("urgencyChart", {
      type: "doughnut",
      plugins: [doughnutCenter(urgencyTotal, "total")],
      data: {
        labels: urgencyLabels,
        datasets: [{
          data: urgencyValues,
          backgroundColor: COLORS.urgencyColors,
          borderWidth: 3,
          borderColor: "#f0f4f8",
          hoverOffset: 6,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: "72%",
        plugins: {
          legend: {
            position: "bottom",
            labels: { color: "#475569" }
          }
        }
      }
    });

    const sources = (data.top_sources || []).slice(0, 8);
    renderChart("sourcesChart", {
      type: "bar",
      data: {
        labels: sources.map(s => s.source),
        datasets: [{
          data: sources.map(s => s.count),
          backgroundColor: "#2563eb",
          borderRadius: 4,
          borderSkipped: false,
          barThickness: 32,
        }]
      },
      options: {
        indexAxis: "y",
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: ctx => ` ${ctx.parsed.x} articles`
            }
          }
        },
        scales: {
          x: {
            beginAtZero: true,
            grid: { color: "rgba(0,0,0,0.04)" },
            ticks: { color: "#94a3b8", stepSize: 1 }
          },
          y: {
            grid: { display: false },
            ticks: { color: "#475569", font: { size: 12 } }
          }
        }
      }
    });

  } catch (e) {
    console.error(e);
  }
}

async function fetchArticles() {
  try {
    const res = await fetch("/dashboard/articles");
    if (!res.ok) return;
    const articles = await res.json();
    const tbody = document.getElementById("articles-tbody");
    if (!tbody) return;

    if (!articles.length) {
      tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;padding:32px;color:#94a3b8">No articles yet</td></tr>`;
      return;
    }

    tbody.innerHTML = articles.map(a => `
      <tr class="article-row" data-id="${a.id}" style="cursor:pointer">
        <td><span class="article-title-cell">${a.title || "—"}</span></td>
        <td>${a.source || "—"}</td>
        <td style="white-space:nowrap;color:#94a3b8">${formatTime(a.timestamp)}</td>
        <td><span class="badge ${getBadgeClass("sentiment", a.sentiment)}">${a.sentiment || "—"}</span></td>
        <td><span class="badge ${getBadgeClass("urgency", a.urgency)}">${a.urgency || "—"}</span></td>
      </tr>
    `).join("");

    document.querySelectorAll(".article-row").forEach(row => {
      row.addEventListener("click", () => showArticleDetail(row.dataset.id));
    });
  } catch (e) {
    console.error(e);
  }
}

function showArticleDetail(id) {
  window.location.href = `/article/${id}`;
}

async function loadDashboard() {
  await Promise.all([fetchStats(), fetchArticles()]);
}

document.addEventListener("DOMContentLoaded", () => {
  loadDashboard();
  setInterval(loadDashboard, 10000);
});