const _metaConfig = document.querySelector('meta[name="medlens-config"]');
let currentReportId = (_metaConfig && _metaConfig.dataset.initialReportId) ? parseInt(_metaConfig.dataset.initialReportId, 10) : null;
let currentReportData = null;
let currentResults = [];
let allReports = [];
let selectedUploadFile = null;

document.addEventListener('DOMContentLoaded', async () => {
  setupFileUpload();
  await loadReportsList();

  if (currentReportId) {
    await loadReportDetails(currentReportId);
  } else if (allReports.length > 0) {
    await loadReportDetails(allReports[0].id);
  }

  // Active Report selector change event
  const selectEl = document.getElementById('activeReportSelect');
  if (selectEl) {
    selectEl.addEventListener('change', async (e) => {
      const id = e.target.value;
      if (id) {
        await loadReportDetails(id);
      }
    });
  }

  // Summary refresh button
  const refreshSummaryBtn = document.getElementById('refreshSummaryBtn');
  if (refreshSummaryBtn) {
    refreshSummaryBtn.addEventListener('click', () => {
      if (currentReportId) loadSummary(currentReportId);
    });
  }

  // Edit result form submission
  const editResultForm = document.getElementById('editResultForm');
  if (editResultForm) {
    editResultForm.addEventListener('submit', handleResultEditSubmit);
  }
});

// ----------------- Reports Listing & Selector -----------------

async function loadReportsList() {
  try {
    const res = await fetch('/api/reports');
    if (res.ok) {
      allReports = await res.json();
      const selectEl = document.getElementById('activeReportSelect');
      if (!selectEl) return;

      if (allReports.length === 0) {
        selectEl.innerHTML = '<option value="">No reports uploaded</option>';
        return;
      }

      selectEl.innerHTML = allReports.map(r => `
        <option value="${r.id}" ${r.id === currentReportId ? 'selected' : ''}>
          ${r.original_filename} (${r.report_date})
        </option>
      `).join('');
    }
  } catch (err) {
    console.error('Error loading reports list:', err);
  }
}

async function loadReportDetails(reportId) {
  try {
    currentReportId = reportId;
    const res = await fetch(`/api/reports/${reportId}`);
    if (res.ok) {
      currentReportData = await res.json();
      currentResults = currentReportData.results || [];

      // Update dropdown selector
      const selectEl = document.getElementById('activeReportSelect');
      if (selectEl) selectEl.value = reportId;

      renderExtractedDataTab(currentReportData, currentResults);
      renderStructuredRecordTab(currentResults);
      renderVerificationTab(currentResults);
      loadConflicts();
      loadSummary(reportId);
    }
  } catch (err) {
    console.error('Error loading report details:', err);
  }
}

// ----------------- Tab 1: Upload & Pipeline Execution -----------------

function setupFileUpload() {
  const dropzone = document.getElementById('uploadDropzone');
  const fileInput = document.getElementById('fileInput');
  const selectedFileCard = document.getElementById('selectedFileCard');
  const processReportBtn = document.getElementById('processReportBtn');

  if (!dropzone || !fileInput) return;

  dropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropzone.classList.add('dragover');
  });

  dropzone.addEventListener('dragleave', () => {
    dropzone.classList.remove('dragover');
  });

  dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropzone.classList.remove('dragover');
    if (e.dataTransfer.files.length > 0) {
      handleFileSelected(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
      handleFileSelected(e.target.files[0]);
    }
  });

  if (processReportBtn) {
    processReportBtn.addEventListener('click', executeProcessingPipeline);
  }
}

function handleFileSelected(file) {
  selectedUploadFile = file;
  const selectedFileCard = document.getElementById('selectedFileCard');
  const selectedFileName = document.getElementById('selectedFileName');
  const selectedFileSize = document.getElementById('selectedFileSize');
  const selectedFileType = document.getElementById('selectedFileType');

  selectedFileName.textContent = file.name;
  selectedFileSize.textContent = `${(file.size / 1024).toFixed(1)} KB`;
  selectedFileType.textContent = file.name.split('.').pop().toUpperCase();
  selectedFileCard.classList.remove('d-none');
}

async function loadSampleReport(sampleFilename) {
  try {
    showToast(`Selecting sample ${sampleFilename}...`, 'info');
    const formData = new FormData();
    formData.append('sample_file', sampleFilename);

    const res = await fetch('/api/reports/upload', {
      method: 'POST',
      body: formData
    });

    const data = await res.json();
    if (res.ok && data.success) {
      currentReportId = data.report_id;
      showToast(`${sampleFilename} loaded. Starting AI extraction pipeline...`, 'success');
      await executeProcessingForId(data.report_id);
    } else {
      showToast(data.error || 'Failed to select sample report', 'error');
    }
  } catch (err) {
    showToast('Error loading sample report', 'error');
  }
}

async function executeProcessingPipeline() {
  if (!selectedUploadFile) return;

  const processBtn = document.getElementById('processReportBtn');
  const spinner = document.getElementById('processSpinner');
  const icon = document.getElementById('processIcon');

  processBtn.disabled = true;
  spinner.classList.remove('d-none');
  icon.classList.add('d-none');

  try {
    const formData = new FormData();
    formData.append('file', selectedUploadFile);

    const uploadRes = await fetch('/api/reports/upload', {
      method: 'POST',
      body: formData
    });

    const uploadData = await uploadRes.json();
    if (!uploadRes.ok || !uploadData.success) {
      showToast(uploadData.error || 'Upload failed', 'error');
      return;
    }

    currentReportId = uploadData.report_id;
    await executeProcessingForId(uploadData.report_id);

  } catch (err) {
    showToast('Error during document processing pipeline', 'error');
  } finally {
    processBtn.disabled = false;
    spinner.classList.add('d-none');
    icon.classList.remove('d-none');
  }
}

async function executeProcessingForId(reportId) {
  try {
    // Switch to Extracted Data Tab to see pipeline status
    const extractedTabBtn = document.getElementById('extracted-tab');
    if (extractedTabBtn) {
      const tab = new bootstrap.Tab(extractedTabBtn);
      tab.show();
    }

    const processRes = await fetch(`/api/reports/${reportId}/process`, {
      method: 'POST'
    });

    const processData = await processRes.json();
    if (processRes.ok && processData.success) {
      showToast('Document processed and verified against reference ranges!', 'success');
      await loadReportsList();
      await loadReportDetails(reportId);
    } else {
      showToast(processData.error || 'Extraction failed', 'error');
    }
  } catch (err) {
    showToast('Error in extraction pipeline', 'error');
  }
}

// ----------------- Tab 2: Extracted Data -----------------

function renderExtractedDataTab(report, tests) {
  const tbody = document.getElementById('extractedResultsTableBody');
  const modeBadge = document.getElementById('extractionModeBadge');
  if (!tbody) return;

  if (modeBadge) {
    modeBadge.textContent = report.report_type || 'Processed';
  }

  if (tests.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" class="text-center py-4 text-muted">No test parameters found. Process the report to view extracted data.</td></tr>`;
    return;
  }

  tbody.innerHTML = tests.map(t => {
    const statusBadgeClass = t.status === 'NORMAL'
      ? 'badge-status-normal'
      : (t.status === 'LOW' ? 'badge-status-low' : (t.status === 'HIGH' ? 'badge-status-high' : 'badge-status-unknown'));

    const confPercent = Math.round((t.confidence || 0.95) * 100);

    return `
      <tr>
        <td class="ps-3 fw-bold text-dark">${t.test_name}</td>
        <td class="fw-bold fs-6 text-primary">${t.edited_value !== null && t.edited_value !== undefined ? t.edited_value : t.value}</td>
        <td class="text-muted small">${t.unit || '—'}</td>
        <td class="fw-medium">${t.reference_range || '<span class="text-muted">Not provided</span>'}</td>
        <td>
          <span class="badge-status ${statusBadgeClass}">${t.status}</span>
        </td>
        <td>
          <div class="d-flex align-items-center gap-1">
            <span class="small fw-semibold text-secondary">${confPercent}%</span>
            <div class="progress flex-grow-1" style="height: 5px; width: 45px;">
              <div class="progress-bar ${confPercent >= 95 ? 'bg-success' : 'bg-warning'}" style="width: ${confPercent}%;"></div>
            </div>
          </div>
        </td>
        <td>
          <span class="badge-provenance badge-report">
            ${report.original_filename} (Pg ${t.source_page || 1})
          </span>
        </td>
        <td class="text-end pe-3">
          <button type="button" class="btn btn-sm btn-outline-secondary" onclick="openSideBySideModal(${t.id})">
            <i class="bi bi-box-arrow-up-right me-1"></i>View Source
          </button>
        </td>
      </tr>
    `;
  }).join('');
}

// ----------------- Tab 3: Structured Medical Record -----------------

function renderStructuredRecordTab(tests) {
  const tbody = document.getElementById('structuredRecordTableBody');
  if (!tbody) return;

  if (tests.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" class="text-center py-4 text-muted">No clinical results available.</td></tr>`;
    return;
  }

  tbody.innerHTML = tests.map(t => {
    const statusBadgeClass = t.status === 'NORMAL'
      ? 'badge-status-normal'
      : (t.status === 'LOW' ? 'badge-status-low' : (t.status === 'HIGH' ? 'badge-status-high' : 'badge-status-unknown'));

    const isVerified = t.is_verified === 1;
    const verifiedBadge = isVerified
      ? '<span class="badge-provenance badge-verified">🟨 Human Verified</span>'
      : '<span class="badge bg-light text-muted border">Pending Review</span>';

    return `
      <tr>
        <td class="fw-semibold">${t.test_name}</td>
        <td class="fw-bold">${t.edited_value !== null && t.edited_value !== undefined ? t.edited_value : t.value} ${t.unit || ''}</td>
        <td>${t.reference_range || 'Not provided'}</td>
        <td><span class="badge-status ${statusBadgeClass}">${t.status}</span></td>
        <td>
          <span class="badge-provenance badge-report">
            ${currentReportData ? currentReportData.original_filename : 'Report'} (Pg ${t.source_page || 1})
          </span>
        </td>
        <td>${verifiedBadge}</td>
      </tr>
    `;
  }).join('');
}

// ----------------- Tab 4: Verification & Conflict Detection -----------------

function renderVerificationTab(tests) {
  const container = document.getElementById('verificationCardsContainer');
  const unverifiedBadge = document.getElementById('unverifiedBadge');
  if (!container) return;

  const unverifiedCount = tests.filter(t => !t.is_verified).length;
  if (unverifiedBadge) {
    if (unverifiedCount > 0) {
      unverifiedBadge.textContent = unverifiedCount;
      unverifiedBadge.classList.remove('d-none');
    } else {
      unverifiedBadge.classList.add('d-none');
    }
  }

  if (tests.length === 0) {
    container.innerHTML = '<div class="col-12 text-center text-muted py-4">No tests to verify.</div>';
    return;
  }

  container.innerHTML = tests.map(t => {
    const isVerified = t.is_verified === 1;
    const conf = t.confidence || 0.95;
    const lowConfWarning = conf < 0.93
      ? `<div class="alert alert-warning py-1 px-2 mb-2 small d-flex align-items-center gap-1">
           <i class="bi bi-exclamation-triangle-fill"></i>
           <span><strong>⚠ Low Extraction Confidence:</strong> Please verify this information against the original report.</span>
         </div>`
      : '';

    const verifiedBadge = isVerified
      ? '<span class="badge-provenance badge-verified"><i class="bi bi-check2-circle me-1"></i>Human Verified</span>'
      : '<span class="badge bg-secondary-subtle text-secondary small">Review Needed</span>';

    return `
      <div class="col-md-6 col-lg-4">
        <div class="card card-med h-100 ${isVerified ? 'border-success-subtle bg-light' : ''}">
          <div class="card-body p-3">
            <div class="d-flex justify-content-between align-items-start mb-2">
              <h6 class="fw-bold text-dark mb-0">${t.test_name}</h6>
              ${verifiedBadge}
            </div>

            ${lowConfWarning}

            <div class="mb-2">
              <span class="text-muted small">Reported Value: </span>
              <span class="fw-bold fs-6 text-primary">${t.edited_value !== null && t.edited_value !== undefined ? t.edited_value : t.value} ${t.unit || ''}</span>
              ${t.edited_value !== null && t.edited_value !== undefined ? '<span class="badge bg-info-subtle text-info small ms-1">(Edited)</span>' : ''}
            </div>

            <div class="mb-2 text-muted small">
              Reference: <strong class="text-dark">${t.reference_range || 'Not provided'}</strong>
            </div>

            <div class="mb-3 text-muted small d-flex justify-content-between">
              <span>Confidence: <strong>${Math.round(conf * 100)}%</strong></span>
              <span>Source: <strong>Page ${t.source_page || 1}</strong></span>
            </div>

            <div class="d-flex gap-2">
              <button type="button" class="btn btn-sm ${isVerified ? 'btn-outline-success' : 'btn-success'} flex-grow-1" onclick="verifyResultDirectly(${t.id})">
                <i class="bi bi-check-lg me-1"></i>${isVerified ? 'Re-verify' : 'Verify'}
              </button>
              <button type="button" class="btn btn-sm btn-outline-primary" onclick="openEditResultModal(${t.id})">
                <i class="bi bi-pencil me-1"></i>Edit
              </button>
              <button type="button" class="btn btn-sm btn-outline-secondary" onclick="openSideBySideModal(${t.id})">
                <i class="bi bi-eye"></i>
              </button>
            </div>
          </div>
        </div>
      </div>
    `;
  }).join('');
}

async function verifyResultDirectly(resultId) {
  try {
    const res = await fetch(`/api/verification/${resultId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ verify: true })
    });

    if (res.ok) {
      showToast('Result marked as Human Verified!', 'success');
      await loadReportDetails(currentReportId);
    }
  } catch (err) {
    showToast('Error verifying result', 'error');
  }
}

function openEditResultModal(resultId) {
  const result = currentResults.find(r => r.id === resultId);
  if (!result) return;

  document.getElementById('editResultId').value = result.id;
  document.getElementById('editResultTestName').value = `${result.test_name} (${result.unit || ''})`;
  document.getElementById('editResultOriginalValue').value = result.value;
  document.getElementById('editResultNewValue').value = result.edited_value !== null ? result.edited_value : result.value;
  document.getElementById('editResultNotes').value = '';

  const modal = new bootstrap.Modal(document.getElementById('editResultModal'));
  modal.show();
}

async function handleResultEditSubmit(e) {
  e.preventDefault();
  const resultId = document.getElementById('editResultId').value;
  const rawValue = document.getElementById('editResultNewValue').value.trim();
  const numValue = parseFloat(rawValue);
  const newValue = (!isNaN(numValue) && String(numValue) === rawValue) ? numValue : rawValue;
  const notes = document.getElementById('editResultNotes').value.trim();

  try {
    const res = await fetch(`/api/verification/${resultId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        edited_value: newValue,
        notes: notes,
        verify: true
      })
    });

    if (res.ok) {
      const modalEl = document.getElementById('editResultModal');
      const modalInstance = bootstrap.Modal.getInstance(modalEl);
      if (modalInstance) modalInstance.hide();

      showToast('Extracted value updated and verified against reference range!', 'success');
      await loadReportDetails(currentReportId);
    }
  } catch (err) {
    showToast('Error updating result', 'error');
  }
}

// ----------------- Conflicts API & Resolution -----------------

async function loadConflicts() {
  try {
    const res = await fetch('/api/conflicts');
    if (res.ok) {
      const conflicts = await res.json();
      const container = document.getElementById('conflictAlertsContainer');
      if (!container) return;

      const activeConflicts = conflicts.filter(c => c.status === 'detected' || c.status === 'reviewed');

      if (activeConflicts.length === 0) {
        container.innerHTML = `
          <div class="alert alert-success border-success-subtle py-2 px-3 small d-flex align-items-center gap-2">
            <i class="bi bi-shield-check text-success fs-5"></i>
            <span>No unresolved inconsistencies detected between patient profile and clinical documents.</span>
          </div>
        `;
        return;
      }

      container.innerHTML = activeConflicts.map(c => `
        <div class="card border-warning border-opacity-50 bg-warning-subtle mb-3">
          <div class="card-body p-3">
            <div class="d-flex flex-column flex-md-row justify-content-between align-items-md-start gap-3">
              <div>
                <h6 class="fw-bold text-dark mb-1 d-flex align-items-center gap-2">
                  <i class="bi bi-exclamation-triangle-fill text-warning"></i>
                  ${c.conflict_type}
                  <span class="badge bg-warning text-dark small" style="font-size: 0.7rem;">Status: ${c.status.toUpperCase()}</span>
                </h6>
                <p class="mb-0 small text-dark" style="line-height: 1.4;">
                  "${c.description}"
                </p>
                <div class="text-muted mt-1" style="font-size: 0.72rem;">
                  Source: ${c.report_name || 'Uploaded Document'}
                </div>
              </div>
              <div class="d-flex gap-2 flex-shrink-0">
                <button type="button" class="btn btn-sm btn-outline-dark" onclick="updateConflict(${c.id}, 'reviewed')">Review</button>
                <button type="button" class="btn btn-sm btn-success" onclick="updateConflict(${c.id}, 'resolved')">Resolve</button>
                <button type="button" class="btn btn-sm btn-secondary" onclick="updateConflict(${c.id}, 'ignored')">Ignore</button>
              </div>
            </div>
          </div>
        </div>
      `).join('');
    }
  } catch (err) {
    console.error('Error loading conflicts:', err);
  }
}

async function updateConflict(conflictId, status) {
  try {
    const res = await fetch(`/api/conflicts/${conflictId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status })
    });

    if (res.ok) {
      showToast(`Inconsistency marked as ${status}`, 'info');
      await loadConflicts();
    }
  } catch (err) {
    showToast('Error updating inconsistency status', 'error');
  }
}

function reviewConflict() {
  showToast('Please cross-reference the patient profile allergy against the uploaded document.', 'info');
}

function resolveConflict(conflictId = 1) {
  updateConflict(conflictId, 'resolved');
}

function ignoreConflict(conflictId = 1) {
  updateConflict(conflictId, 'ignored');
}

// ----------------- Tab 5: AI Summary -----------------

async function loadSummary(reportId) {
  try {
    const overviewEl = document.getElementById('summaryOverviewText');
    const obsContainer = document.getElementById('summaryObservationsContainer');
    const subtitle = document.getElementById('summarySubtitle');

    if (!overviewEl || !obsContainer) return;

    overviewEl.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Synthesizing neutral patient-friendly summary...';

    const res = await fetch(`/api/summary?report_id=${reportId}`);
    if (res.ok) {
      const data = await res.json();
      overviewEl.textContent = data.overview;
      subtitle.textContent = `Report: ${data.report_name || 'Document'}`;

      if (!data.observations || data.observations.length === 0) {
        obsContainer.innerHTML = '<div class="text-muted small">No specific observations for this report.</div>';
        return;
      }

      obsContainer.innerHTML = data.observations.map(obs => {
        const badgeColor = obs.badge_class === 'danger'
          ? 'badge-status-low'
          : (obs.badge_class === 'warning' ? 'badge-status-high' : (obs.badge_class === 'success' ? 'badge-status-normal' : 'badge-status-unknown'));

        return `
          <div class="card p-3 border bg-white">
            <div class="d-flex align-items-center justify-content-between mb-1">
              <span class="badge-status ${badgeColor}">${obs.badge}</span>
              <span class="badge-provenance badge-report small">${obs.source}</span>
            </div>
            <p class="mb-0 text-dark fw-medium fs-6 mt-1">${obs.text}</p>
          </div>
        `;
      }).join('');
    }
  } catch (err) {
    console.error('Error loading AI summary:', err);
  }
}

// ----------------- Side-by-Side Traceability Modal (Requirement 6) -----------------

function openSideBySideModal(resultId) {
  const result = currentResults.find(r => r.id === resultId);
  if (!result || !currentReportData) return;

  const docBadge = document.getElementById('sourceDocBadge');
  const sourcePane = document.getElementById('sourceDocumentPane');

  docBadge.textContent = `${currentReportData.original_filename} (Page ${result.source_page || 1})`;

  // Realistic mock excerpt of original report text with exact highlighted snippet
  const sourceText = result.source_text || `${result.test_name}: ${result.value} ${result.unit || ''}`;
  sourcePane.innerHTML = `METROPATH CLINICAL LABORATORIES — DIAGNOSTIC REPORT
Accession: ${currentReportData.original_filename}
Patient: Demo Patient (45 Y, Female)
Collection Date: ${currentReportData.report_date}

[PAGE ${result.source_page || 1} EXCERPT]
-----------------------------------------------------------
TEST NAME                RESULT    UNITS    REFERENCE RANGE
-----------------------------------------------------------
<span class="source-highlight">${sourceText}</span>
-----------------------------------------------------------
Physician Notes:
Routine clinical monitoring. Parameter verified against
CLIA reference limits. No therapeutic recommendations provided.

* Electronic Signature Recorded on File *
`;

  // Populate Right Pane
  document.getElementById('sideTestName').textContent = result.test_name;
  document.getElementById('sideTestValue').textContent = `${result.edited_value !== null ? result.edited_value : result.value} ${result.unit || ''}`;
  document.getElementById('sideTestUnit').textContent = result.unit || 'Not specified';
  document.getElementById('sideTestRange').textContent = result.reference_range || 'Not provided in source';

  const statusBadgeClass = result.status === 'NORMAL'
    ? 'badge-status-normal'
    : (result.status === 'LOW' ? 'badge-status-low' : (result.status === 'HIGH' ? 'badge-status-high' : 'badge-status-unknown'));

  document.getElementById('sideTestStatus').innerHTML = `<span class="badge-status ${statusBadgeClass}">${result.status}</span>`;
  document.getElementById('sideTestConfidence').textContent = `${Math.round((result.confidence || 0.95) * 100)}%`;
  document.getElementById('sideTestSourceDoc').textContent = currentReportData.original_filename;
  document.getElementById('sideTestSourcePage').textContent = `Page ${result.source_page || 1}`;

  const modal = new bootstrap.Modal(document.getElementById('sourceModal'));
  modal.show();
}
