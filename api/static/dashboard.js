let sentimentChart;
let categoryChart;
let urgencyChart;
let sourcesChart;

function getBadgeClass(type, value) {
  const normalized = (value || "").toString().toLowerCase();
  if (type === "sentiment") {
    if (normalized === "positive") return "badge-positive";
    if (normalized === "negative") return "badge-negative";
    return "badge-neutral";
  }

  if (type === "urgency") {
    if (normalized === "urgent") return "badge-urgent";
    if (normalized === "high") return "badge-high";
    return "badge-normal";
  }

  return "";
}

function formatTimestamp(ts) {
  if (!ts) return "--";
  const date = new Date(ts);
  if (Number.isNaN(date.getTime())) return ts;
  return date.toLocaleString();
}

function getTopKey(counts) {
  if (!counts || typeof counts !== "object") return "--";
  const entries = Object.entries(counts).filter(([, value]) => Number.isFinite(Number(value)));
  if (!entries.length) return "--";
  entries.sort((a, b) => Number(b[1]) - Number(a[1]));
  return entries[0][0];
}

function updateStatCards(stats) {
  document.getElementById("total-articles").textContent = stats.total_articles ?? 0;
  document.getElementById("avg-latency").textContent =
    stats.avg_latency_ms != null ? Number(stats.avg_latency_ms).toFixed(2) : "0.00";
  document.getElementById("top-sentiment").textContent = getTopKey(stats.sentiment_counts) || "--";
  document.getElementById("top-urgency").textContent = getTopKey(stats.urgency_counts) || "--";
  document.getElementById("last-updated").textContent = new Date().toLocaleTimeString();
}

function renderChart(canvasId, config) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;

  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  const chartInstance = Chart.getChart(canvas);
  if (chartInstance) {
    chartInstance.destroy();
  }

  return new Chart(ctx, config);
}

function updateStatsCharts(stats) {
  const sentimentLabels = ["positive", "neutral", "negative"];
  const sentimentValues = sentimentLabels.map((label) => Number(stats.sentiment_counts?.[label] || 0));

  sentimentChart = renderChart("sentimentChart", {
    type: "pie",
    data: {
      labels: sentimentLabels,
      datasets: [{
        data: sentimentValues,
        backgroundColor: ["#2ecc71", "#8892a4", "#e74c3c"]
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { position: "bottom" } }
    }
  });

  const categoryLabels = Object.keys(stats.category_counts || {});
  const categoryValues = categoryLabels.map((label) => Number(stats.category_counts[label] || 0));

  categoryChart = renderChart("categoryChart", {
    type: "bar",
    data: {
      labels: categoryLabels,
      datasets: [{
        label: "Articles",
        data: categoryValues,
        backgroundColor: "#4f8ef7"
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: { y: { beginAtZero: true } }
    }
  });

  const urgencyLabels = ["normal", "high", "urgent"];
  const urgencyValues = urgencyLabels.map((label) => Number(stats.urgency_counts?.[label] || 0));

  urgencyChart = renderChart("urgencyChart", {
    type: "pie",
    data: {
      labels: urgencyLabels,
      datasets: [{
        data: urgencyValues,
        backgroundColor: ["#2ecc71", "#f39c12", "#e74c3c"]
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { position: "bottom" } }
    }
  });

  const sourceEntries = (stats.top_sources || []).slice(0, 5);
  const sourceLabels = sourceEntries.map((item) => item.source || "Unknown");
  const sourceValues = sourceEntries.map((item) => Number(item.count || 0));

  sourcesChart = renderChart("sourcesChart", {
    type: "bar",
    data: {
      labels: sourceLabels,
      datasets: [{
        label: "Articles",
        data: sourceValues,
        backgroundColor: "#4f8ef7"
      }]
    },
    options: {
      indexAxis: "y",
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: { x: { beginAtZero: true } }
    }
  });
}

async function fetchStats() {
  try {
    const response = await fetch("/dashboard/stats");
    if (!response.ok) throw new Error("Failed to load stats");
    const stats = await response.json();
    updateStatCards(stats);
    updateStatsCharts(stats);
  } catch (error) {
    console.error(error);
  }
}

function truncateText(value, maxLength = 50) {
  if (!value) return "--";
  return value.length > maxLength ? `${value.slice(0, maxLength)}...` : value;
}

async function fetchArticles() {
  try {
    const response = await fetch("/dashboard/articles");
    if (!response.ok) throw new Error("Failed to load articles");
    const articles = await response.json();
    const tbody = document.getElementById("articles-tbody");
    if (!tbody) return;

    if (!articles.length) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;color:var(--text-secondary)">No articles found</td></tr>`;
      return;
    }

    tbody.innerHTML = articles.map((article) => `
      <tr onclick="showArticleDetail('${article.id}')">
        <td>${article.id || "--"}</td>
        <td>${truncateText(article.title, 50)}</td>
        <td>${article.source || "--"}</td>
        <td>${formatTimestamp(article.timestamp)}</td>
        <td><span class="badge ${getBadgeClass("sentiment", article.sentiment)}">${article.sentiment || "unknown"}</span></td>
        <td><span class="badge ${getBadgeClass("urgency", article.urgency)}">${article.urgency || "unknown"}</span></td>
      </tr>
    `).join("");
  } catch (error) {
    console.error(error);
  }
}

async function showArticleDetail(articleId) {
  const overlay = document.getElementById("modal-overlay");
  if (!overlay) return;

  overlay.classList.add("open");
  document.getElementById("modal-title").textContent = "Loading...";
  document.getElementById("modal-body").innerHTML = "<p>Loading article details...</p>";

  try {
    const response = await fetch(`/dashboard/articles/${articleId}`);
    if (!response.ok) throw new Error("Failed to load article details");

    const article = await response.json();
    const keywords = Array.isArray(article.keywords) ? article.keywords : [];
    const categories = Array.isArray(article.categories) ? article.categories : [];
    const companies = Array.isArray(article.companies) ? article.companies : [];

    document.getElementById("modal-title").textContent = article.title || "Article Details";
    document.getElementById("modal-body").innerHTML = `
      <div class="detail-row"><strong>Source:</strong> ${article.source || "--"}</div>
      <div class="detail-row"><strong>Timestamp:</strong> ${formatTimestamp(article.timestamp)}</div>
      <div class="detail-row"><strong>Sentiment:</strong> <span class="badge ${getBadgeClass("sentiment", article.sentiment)}">${article.sentiment || "unknown"}</span></div>
      <div class="detail-row"><strong>Urgency:</strong> <span class="badge ${getBadgeClass("urgency", article.urgency)}">${article.urgency || "unknown"}</span></div>
      <div class="detail-row"><strong>Content:</strong> ${article.content || "--"}</div>
      <div class="detail-row"><strong>Summary:</strong> ${article.summary || "--"}</div>
      <div class="detail-row"><strong>Keywords:</strong> ${keywords.join(", ") || "--"}</div>
      <div class="detail-row"><strong>Categories:</strong> ${categories.join(", ") || "--"}</div>
      <div class="detail-row"><strong>Companies:</strong> ${companies.join(", ") || "--"}</div>
      <div class="detail-row"><strong>Importance Score:</strong> ${article.importance_score != null ? `${Number(article.importance_score * 100).toFixed(2)}%` : "--"}</div>
    `;
  } catch (error) {
    console.error(error);
    document.getElementById("modal-body").innerHTML = "<p>Unable to load article details.</p>";
  }
}

function closeModal() {
  const overlay = document.getElementById("modal-overlay");
  if (overlay) {
    overlay.classList.remove("open");
  }
}

async function loadDashboard() {
  await Promise.all([fetchStats(), fetchArticles()]);
}

document.addEventListener("DOMContentLoaded", () => {
  loadDashboard();
  setInterval(loadDashboard, 10000);

  const overlay = document.getElementById("modal-overlay");
  if (overlay) {
    overlay.addEventListener("click", (event) => {
      if (event.target.id === "modal-overlay") {
        closeModal();
      }
    });
  }

  const closeButton = document.getElementById("modal-close");
  if (closeButton) {
    closeButton.addEventListener("click", closeModal);
  }
});