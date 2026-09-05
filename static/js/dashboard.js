document.addEventListener('DOMContentLoaded', () => {
  loadDashboardData();

  // Handle Edit Patient Form
  const editPatientForm = document.getElementById('editPatientForm');
  if (editPatientForm) {
    editPatientForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const saveBtn = document.getElementById('savePatientBtn');
      saveBtn.disabled = true;

      const payload = {
        name: document.getElementById('inputPatientName').value.trim(),
        age: parseInt(document.getElementById('inputPatientAge').value) || 0,
        sex: document.getElementById('inputPatientSex').value,
        symptoms: document.getElementById('inputPatientSymptoms').value.trim(),
        conditions: document.getElementById('inputPatientConditions').value.trim(),
        allergies: document.getElementById('inputPatientAllergies').value.trim(),
        medications: document.getElementById('inputPatientMedications').value.trim(),
      };

      try {
        const res = await fetch('/api/patient', {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });

        const data = await res.json();
        if (res.ok && data.success) {
          // Update displayed values
          document.getElementById('displayPatientName').textContent = payload.name;
          document.getElementById('displayPatientAgeSex').textContent = `${payload.age} yrs / ${payload.sex}`;
          document.getElementById('displayPatientSymptoms').textContent = payload.symptoms || 'None reported';
          document.getElementById('displayPatientConditions').textContent = payload.conditions || 'None reported';
          document.getElementById('displayPatientAllergies').textContent = payload.allergies || 'None reported';
          document.getElementById('displayPatientMedications').textContent = payload.medications || 'None reported';

          // Close modal
          const modalEl = document.getElementById('editPatientModal');
          const modalInstance = bootstrap.Modal.getInstance(modalEl);
          if (modalInstance) modalInstance.hide();

          showToast('Patient information updated successfully!', 'success');
          loadAuditLogs();
        } else {
          showToast(data.message || 'Failed to update patient profile', 'error');
        }
      } catch (err) {
        showToast('Error saving patient information', 'error');
      } finally {
        saveBtn.disabled = false;
      }
    });
  }
});

async function loadDashboardData() {
  await Promise.all([
    loadMetrics(),
    loadRecentReports(),
    loadAuditLogs()
  ]);
}

async function loadMetrics() {
  try {
    const res = await fetch('/api/dashboard/metrics');
    if (res.ok) {
      const data = await res.json();
      document.getElementById('metricReports').textContent = data.reports_count;
      document.getElementById('metricResults').textContent = data.extracted_results_count;
      document.getElementById('metricVerification').textContent = data.needs_verification_count;
      document.getElementById('metricConflicts').textContent = data.potential_conflicts_count;
    }
  } catch (err) {
    console.error('Error loading metrics:', err);
  }
}

async function loadRecentReports() {
  try {
    const res = await fetch('/api/reports');
    if (res.ok) {
      const reports = await res.json();
      const tbody = document.getElementById('recentReportsTableBody');
      if (!tbody) return;

      if (reports.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" class="text-center py-4 text-muted">No medical reports uploaded yet. Click "+ Upload Medical Report" above to begin.</td></tr>`;
        return;
      }

      tbody.innerHTML = reports.slice(0, 5).map(r => {
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
              <a href="/report/${r.id}" class="btn btn-sm btn-outline-primary">View</a>
            </td>
          </tr>
        `;
      }).join('');
    }
  } catch (err) {
    console.error('Error loading recent reports:', err);
  }
}

async function loadAuditLogs() {
  try {
    const res = await fetch('/api/audit');
    if (res.ok) {
      const logs = await res.json();
      const listEl = document.getElementById('auditEventsList');
      if (!listEl) return;

      if (logs.length === 0) {
        listEl.innerHTML = '<li class="text-muted small py-2">No recent audit activity.</li>';
        return;
      }

      listEl.innerHTML = logs.map(l => {
        let icon = 'bi-activity text-secondary';
        if (l.action.includes('uploaded')) icon = 'bi-cloud-upload text-info';
        else if (l.action.includes('extraction')) icon = 'bi-robot text-primary';
        else if (l.action.includes('verified')) icon = 'bi-check-circle-fill text-success';
        else if (l.action.includes('conflict')) icon = 'bi-exclamation-triangle-fill text-danger';

        return `
          <li class="d-flex gap-3 mb-3 pb-2 border-bottom">
            <i class="bi ${icon} fs-5"></i>
            <div>
              <div class="fw-semibold small">${l.action}</div>
              <div class="text-muted small">${l.details || ''}</div>
              <div class="text-secondary" style="font-size: 0.7rem;">${l.timestamp}</div>
            </div>
          </li>
        `;
      }).join('');
    }
  } catch (err) {
    console.error('Error loading audit events:', err);
  }
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
