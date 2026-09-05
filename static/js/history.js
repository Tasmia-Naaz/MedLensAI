let historyReports = [];
let comparisonChartInstance = null;

document.addEventListener('DOMContentLoaded', async () => {
  await loadHistoryData();

  // Compare Button
  const compareBtn = document.getElementById('compareReportsBtn');
  if (compareBtn) {
    compareBtn.addEventListener('click', runReportComparison);
  }

  // Search & Filter event listeners
  const searchInput = document.getElementById('historySearchInput');
  const typeFilter = document.getElementById('typeFilter');
  const statusFilter = document.getElementById('statusFilter');

  if (searchInput) searchInput.addEventListener('input', applyHistoryFilters);
  if (typeFilter) typeFilter.addEventListener('change', applyHistoryFilters);
  if (statusFilter) statusFilter.addEventListener('change', applyHistoryFilters);
});

async function loadHistoryData() {
  try {
    const res = await fetch('/api/history');
    if (res.ok) {
      const data = await res.json();
      historyReports = data.reports || [];
      const timeline = data.timeline || [];

      populateComparisonDropdowns(historyReports);
      renderHistoryTable(historyReports);
      renderTimeline(timeline);

      // Trigger default comparison if at least 2 reports exist
      if (historyReports.length >= 2) {
        // Find June report (previous) and September report (current) or top 2
        const prevSelect = document.getElementById('prevReportSelect');
        const currSelect = document.getElementById('currReportSelect');

        // Set previous to older report, current to newer report
        currSelect.value = historyReports[0].id;
        prevSelect.value = historyReports[historyReports.length - 1].id;

        // Try to match June and September if available
        const junRep = historyReports.find(r => r.original_filename.includes('Jun'));
        const sepRep = historyReports.find(r => r.original_filename.includes('Blood_Report.pdf'));
        if (junRep && sepRep) {
          prevSelect.value = junRep.id;
          currSelect.value = sepRep.id;
        }

        await runReportComparison();
      }
    }
  } catch (err) {
    console.error('Error loading history:', err);
  }
}

function populateComparisonDropdowns(reports) {
  const prevSelect = document.getElementById('prevReportSelect');
  const currSelect = document.getElementById('currReportSelect');
  if (!prevSelect || !currSelect) return;

  if (reports.length === 0) {
    prevSelect.innerHTML = '<option value="">No reports available</option>';
    currSelect.innerHTML = '<option value="">No reports available</option>';
    return;
  }

  const options = reports.map(r => `
    <option value="${r.id}">
      ${r.original_filename} (${r.report_type} — ${formatDate(r.report_date)})
    </option>
  `).join('');

  prevSelect.innerHTML = options;
  currSelect.innerHTML = options;
}

async function runReportComparison() {
  const prevId = document.getElementById('prevReportSelect').value;
  const currId = document.getElementById('currReportSelect').value;

  if (!prevId || !currId) {
    showToast('Please select both a previous and current report to compare.', 'warning');
    return;
  }

  if (prevId === currId) {
    showToast('Please select two different reports to perform a comparative delta.', 'warning');
    return;
  }

  try {
    const res = await fetch('/api/compare', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        previous_report_id: parseInt(prevId),
        current_report_id: parseInt(currId)
      })
    });

    if (res.ok) {
      const data = await res.json();
      renderComparisonResults(data);
      renderComparisonChart(data.chart_data, data.previous_report, data.current_report);
    } else {
      showToast('Error comparing reports', 'error');
    }
  } catch (err) {
    showToast('Failed to perform comparative analysis', 'error');
  }
}

function renderComparisonResults(data) {
  const tbody = document.getElementById('comparisonTableBody');
  if (!tbody) return;

  const rows = data.comparisons || [];
  if (rows.length === 0) {
    tbody.innerHTML = `<tr><td colspan="5" class="text-center py-4 text-muted">No comparable tests between selected reports.</td></tr>`;
    return;
  }

  tbody.innerHTML = rows.map(r => {
    let deltaBadgeClass = 'text-secondary';
    if (r.change.startsWith('+')) deltaBadgeClass = 'text-primary fw-bold';
    else if (r.change.startsWith('-')) deltaBadgeClass = 'text-danger fw-bold';

    return `
      <tr>
        <td class="ps-3 fw-bold text-dark">${r.test_name} <span class="text-muted small">(${r.unit})</span></td>
        <td class="fw-semibold">${r.previous_value !== null ? r.previous_value : '—'}</td>
        <td class="fw-bold text-dark">${r.current_value !== null ? r.current_value : '—'}</td>
        <td class="${deltaBadgeClass}">${r.change}</td>
        <td class="pe-3 small text-muted">
          <i class="bi bi-info-circle me-1 text-secondary"></i>
          "${r.neutral_statement}"
        </td>
      </tr>
    `;
  }).join('');
}

function renderComparisonChart(chartData, prevReport, currReport) {
  const ctx = document.getElementById('comparisonChart');
  if (!ctx) return;

  if (comparisonChartInstance) {
    comparisonChartInstance.destroy();
  }

  const prevLabel = prevReport ? `${prevReport.original_filename} (${formatDate(prevReport.report_date)})` : 'Previous';
  const currLabel = currReport ? `${currReport.original_filename} (${formatDate(currReport.report_date)})` : 'Current';

  comparisonChartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: chartData.labels,
      datasets: [
        {
          label: prevLabel,
          data: chartData.previous,
          backgroundColor: 'rgba(148, 163, 184, 0.7)',
          borderColor: 'rgb(148, 163, 184)',
          borderWidth: 1,
          borderRadius: 4
        },
        {
          label: currLabel,
          data: chartData.current,
          backgroundColor: 'rgba(2, 132, 199, 0.8)',
          borderColor: 'rgb(2, 132, 199)',
          borderWidth: 1,
          borderRadius: 4
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top',
          labels: { font: { family: 'Plus Jakarta Sans', size: 12 } }
        },
        tooltip: {
          callbacks: {
            footer: () => 'Neutral parameter tracking without diagnostic interpretation.'
          }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          grid: { color: '#f1f5f9' }
        },
        x: {
          grid: { display: false }
        }
      }
    }
  });
}

// ----------------- Report History Archive Table -----------------

function renderHistoryTable(reports) {
  const tbody = document.getElementById('historyTableBody');
  if (!tbody) return;

  if (reports.length === 0) {
    tbody.innerHTML = `<tr><td colspan="5" class="text-center py-4 text-muted">No historical reports match the filters.</td></tr>`;
    return;
  }

  tbody.innerHTML = reports.map(r => {
    const statusBadge = r.status === 'Verified'
      ? '<span class="badge bg-success-subtle text-success border">Verified</span>'
      : '<span class="badge bg-info-subtle text-info border">Processed</span>';

    return `
      <tr>
        <td class="ps-4">
          <div class="d-flex align-items-center gap-2">
            <i class="bi bi-file-earmark-pdf-fill text-danger fs-5"></i>
            <div>
              <div class="fw-semibold">${r.original_filename}</div>
              <div class="text-muted small">${(r.file_size / 1024).toFixed(1)} KB · ${r.page_count || 1} pg</div>
            </div>
          </div>
        </td>
        <td><span class="badge bg-light text-dark border">${r.report_type}</span></td>
        <td>${formatDate(r.report_date)}</td>
        <td>${statusBadge}</td>
        <td class="text-end pe-4">
          <a href="/report/${r.id}" class="btn btn-sm btn-outline-primary">
            <i class="bi bi-eye me-1"></i>View
          </a>
        </td>
      </tr>
    `;
  }).join('');
}

function applyHistoryFilters() {
  const query = (document.getElementById('historySearchInput').value || '').toLowerCase().trim();
  const typeVal = document.getElementById('typeFilter').value;
  const statusVal = document.getElementById('statusFilter').value;

  const filtered = historyReports.filter(r => {
    const matchesQuery = !query ||
      r.original_filename.toLowerCase().includes(query) ||
      r.report_type.toLowerCase().includes(query);

    const matchesType = typeVal === 'ALL' || r.report_type.toLowerCase() === typeVal.toLowerCase();
    const matchesStatus = statusVal === 'ALL' || r.status.toLowerCase() === statusVal.toLowerCase();

    return matchesQuery && matchesType && matchesStatus;
  });

  renderHistoryTable(filtered);
}

// ----------------- Patient Timeline (Section 4) -----------------

function renderTimeline(timelineEvents) {
  const container = document.getElementById('patientTimelineContainer');
  if (!container) return;

  if (timelineEvents.length === 0) {
    container.innerHTML = '<div class="text-muted small">No chronological events found.</div>';
    return;
  }

  container.innerHTML = timelineEvents.map(item => `
    <div class="timeline-item" onclick="window.location.href='/report/${item.report_id}'" title="Click to view report">
      <div class="timeline-dot"></div>
      <div class="timeline-content">
        <div class="d-flex justify-content-between align-items-center mb-1">
          <span class="fw-bold small text-primary">${item.display_date}</span>
          <span class="badge bg-light text-secondary small border">${item.status}</span>
        </div>
        <div class="fw-semibold text-dark small">${item.title}</div>
        <div class="text-muted" style="font-size: 0.75rem;">
          <i class="bi bi-file-earmark-pdf me-1"></i>${item.filename}
        </div>
      </div>
    </div>
  `).join('');
}

function formatDate(dateStr) {
  if (!dateStr) return 'N/A';
  try {
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
  } catch {
    return dateStr;
  }
}
