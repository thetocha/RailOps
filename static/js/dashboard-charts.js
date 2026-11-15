(function () {
  function readJson(id) {
    var node = document.getElementById(id);
    if (!node) {
      return null;
    }
    try {
      return JSON.parse(node.textContent);
    } catch (error) {
      return null;
    }
  }

  function drawChart(canvasId, dataId, type) {
    var canvas = document.getElementById(canvasId);
    var payload = readJson(dataId);
    if (!canvas || !payload || typeof Chart === "undefined") {
      return;
    }
    if (!payload.values || !payload.values.some(function (value) { return value > 0; })) {
      return;
    }
    new Chart(canvas, {
      type: type,
      data: {
        labels: payload.labels,
        datasets: [{ data: payload.values, backgroundColor: ["#6c757d", "#ffc107", "#dc3545", "#212529", "#0d6efd"] }],
      },
      options: {
        responsive: true,
        plugins: { legend: { display: type === "doughnut" } },
      },
    });
  }

  drawChart("severity-chart", "severity-chart-data", "doughnut");
  drawChart("trend-chart", "trend-chart-data", "bar");
})();
