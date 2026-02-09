const state = {
  rows: [],
  columns: [],
  config: {},
  file: null
};

const elements = {
  uploadArea: document.getElementById("upload-area"),
  csvFile: document.getElementById("csv-file"),
  fileInfo: document.getElementById("file-info"),
  fileName: document.getElementById("file-name"),
  clearFile: document.getElementById("clear-file"),
  parseBtn: document.getElementById("parse-btn"),
  csvFormat: document.getElementById("csv-format"),
  maxSize: document.getElementById("max-size"),
  previewHead: document.getElementById("preview-head"),
  previewBody: document.getElementById("preview-body"),
  rowCount: document.getElementById("row-count"),
  importBtn: document.getElementById("import-btn"),
  backStep2: document.getElementById("back-step2"),
  importAgain: document.getElementById("import-again-btn"),
  fireflyLink: document.getElementById("firefly-link"),
  loadingOverlay: document.getElementById("loading-overlay"),
  loadingText: document.getElementById("loading-text"),
  connectionIndicator: document.getElementById("connection-indicator"),
  connectionText: document.getElementById("connection-text"),
  summaryImported: document.getElementById("summary-imported"),
  summarySkipped: document.getElementById("summary-skipped"),
  summaryCreated: document.getElementById("summary-created"),
  summaryRate: document.getElementById("summary-rate"),
  importedSection: document.getElementById("imported-section"),
  importedList: document.getElementById("imported-list"),
  errorsSection: document.getElementById("errors-section"),
  errorsList: document.getElementById("errors-list"),
  accountsSection: document.getElementById("accounts-section"),
  accountsList: document.getElementById("accounts-list"),
  alertsContainer: document.getElementById("alerts-container")
};

const mappingFields = [
  "date",
  "amount",
  "description",
  "source_account",
  "destination_account",
  "type",
  "category",
  "tags",
  "notes",
  "external_id"
];

const mappingSelects = {
  date: document.getElementById("map-date"),
  amount: document.getElementById("map-amount"),
  description: document.getElementById("map-description"),
  source_account: document.getElementById("map-source-account"),
  destination_account: document.getElementById("map-destination-account"),
  type: document.getElementById("map-type"),
  category: document.getElementById("map-category"),
  tags: document.getElementById("map-tags"),
  notes: document.getElementById("map-notes"),
  external_id: document.getElementById("map-external-id")
};

function showAlert(type, message) {
  const alert = document.createElement("div");
  alert.className = `alert ${type}`;
  alert.textContent = message;
  elements.alertsContainer.appendChild(alert);
  setTimeout(() => alert.remove(), 6000);
}

function setLoading(isLoading, text = "Processing...") {
  elements.loadingOverlay.classList.toggle("hidden", !isLoading);
  elements.loadingText.textContent = text;
}

function setStep(step) {
  document.querySelectorAll(".step").forEach((section) => {
    section.classList.add("hidden");
  });
  document.getElementById(step).classList.remove("hidden");
}

function updateConnection(status, text) {
  elements.connectionIndicator.classList.remove("ok", "error");
  if (status) {
    elements.connectionIndicator.classList.add("ok");
  } else if (status === false) {
    elements.connectionIndicator.classList.add("error");
  }
  elements.connectionText.textContent = text;
}

async function loadConfig() {
  try {
    const response = await fetch("/api/config");
    const data = await response.json();
    state.config = data;
    elements.maxSize.textContent = data.max_upload_size_mb || 10;
    if (data.firefly_url) {
      elements.fireflyLink.href = data.firefly_url;
    }
    if (!data.configured) {
      updateConnection(false, "Missing configuration");
      showAlert("error", "Firefly III is not configured in the add-on options.");
      return;
    }
    await testConnection();
  } catch (error) {
    updateConnection(false, "Config error");
  }
}

async function testConnection() {
  updateConnection(null, "Checking...");
  try {
    const response = await fetch("/api/test-connection", { method: "POST" });
    const data = await response.json();
    if (response.ok && data.success) {
      updateConnection(true, `Connected as ${data.user}`);
    } else {
      updateConnection(false, data.error || "Connection failed");
    }
  } catch (error) {
    updateConnection(false, "Connection failed");
  }
}

function resetFile() {
  state.file = null;
  state.rows = [];
  state.columns = [];
  elements.csvFile.value = "";
  elements.fileInfo.classList.add("hidden");
  elements.fileName.textContent = "";
  elements.parseBtn.disabled = true;
}

function handleFileSelect(file) {
  if (!file) {
    return;
  }
  const maxSizeBytes = (state.config.max_upload_size_mb || 10) * 1024 * 1024;
  if (!file.name.toLowerCase().endsWith(".csv")) {
    showAlert("error", "Please select a CSV file.");
    return;
  }
  if (file.size > maxSizeBytes) {
    showAlert("error", `File is too large. Max ${state.config.max_upload_size_mb || 10}MB.`);
    return;
  }
  state.file = file;
  elements.fileInfo.classList.remove("hidden");
  elements.fileName.textContent = file.name;
  elements.parseBtn.disabled = false;
}

function setMappingOptions(columns) {
  Object.values(mappingSelects).forEach((select) => {
    select.innerHTML = "<option value=\"\">-- Select Column --</option>";
    columns.forEach((col) => {
      const option = document.createElement("option");
      option.value = col;
      option.textContent = col;
      select.appendChild(option);
    });
  });
}

function normalize(text) {
  return text.toLowerCase().replace(/[^a-z0-9]/g, "");
}

function detectMapping(columns, format) {
  const patterns = {
    date: ["date", "transactiondate", "posteddate"],
    amount: ["amount", "value", "total", "money"],
    description: ["description", "memo", "details", "narrative"],
    source_account: ["source", "from", "account", "asset"],
    destination_account: ["destination", "to", "counterparty", "merchant", "payee"],
    type: ["type", "transactiontype"],
    category: ["category", "group"],
    tags: ["tags", "labels"],
    notes: ["notes", "note"],
    external_id: ["externalid", "uniqueid", "id", "reference"]
  };

  const formatHints = {
    bank: {
      source_account: ["account", "accountname"],
      destination_account: ["payee", "merchant", "counterparty"],
      description: ["description", "details", "memo"],
      amount: ["amount", "debit", "credit"],
      date: ["date", "posteddate"]
    },
    pocketsmith: {
      date: ["date"],
      amount: ["amount"],
      description: ["note", "description"],
      source_account: ["account"],
      destination_account: ["payee"],
      category: ["category"],
      type: ["type", "transactiontype"]
    },
    generic: {}
  };

  const selected = {};
  const normalizedColumns = columns.map((col) => ({
    raw: col,
    norm: normalize(col)
  }));

  const lookup = (field, hints) => {
    for (const hint of hints) {
      const match = normalizedColumns.find((col) => col.norm.includes(hint));
      if (match) {
        return match.raw;
      }
    }
    return "";
  };

  mappingFields.forEach((field) => {
    const formatHint = formatHints[format]?.[field] || [];
    const combinedHints = [...formatHint, ...patterns[field]];
    selected[field] = lookup(field, combinedHints);
  });

  return selected;
}

function applyMapping(mapping) {
  Object.entries(mapping).forEach(([field, column]) => {
    if (mappingSelects[field] && column) {
      mappingSelects[field].value = column;
    }
  });
}

function renderPreview(columns, rows) {
  elements.previewHead.innerHTML = "";
  elements.previewBody.innerHTML = "";
  const headerRow = document.createElement("tr");
  columns.forEach((col) => {
    const th = document.createElement("th");
    th.textContent = col;
    headerRow.appendChild(th);
  });
  elements.previewHead.appendChild(headerRow);

  rows.forEach((row) => {
    const tr = document.createElement("tr");
    columns.forEach((col) => {
      const td = document.createElement("td");
      td.textContent = row[col] || "";
      tr.appendChild(td);
    });
    elements.previewBody.appendChild(tr);
  });
}

function collectMapping() {
  const mapping = {};
  mappingFields.forEach((field) => {
    const select = mappingSelects[field];
    if (select && select.value) {
      mapping[field] = select.value;
    }
  });
  return mapping;
}

async function parseCsv() {
  if (!state.file) {
    return;
  }
  setLoading(true, "Parsing CSV...");
  const formData = new FormData();
  formData.append("file", state.file);
  try {
    const response = await fetch("/api/parse-csv", {
      method: "POST",
      body: formData
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "Unable to parse CSV.");
    }
    state.rows = data.all_rows || [];
    state.columns = data.columns || [];
    setMappingOptions(state.columns);
    const mapping = detectMapping(state.columns, elements.csvFormat.value);
    applyMapping(mapping);
    renderPreview(state.columns, data.preview || []);
    elements.rowCount.textContent = `${data.total_rows || 0} rows detected`;
    setStep("step-2");
  } catch (error) {
    showAlert("error", error.message);
  } finally {
    setLoading(false);
  }
}

function renderResults(results, summary) {
  elements.summaryImported.textContent = summary.imported || 0;
  elements.summarySkipped.textContent = summary.skipped || 0;
  elements.summaryCreated.textContent = summary.accounts_created || 0;
  elements.summaryRate.textContent = summary.success_rate || "0%";

  elements.importedList.innerHTML = "";
  elements.errorsList.innerHTML = "";
  elements.accountsList.innerHTML = "";

  elements.importedSection.classList.toggle("hidden", !(results.transactions || []).length);
  elements.errorsSection.classList.toggle("hidden", !(results.errors || []).length);
  elements.accountsSection.classList.toggle("hidden", !(results.accounts_created || []).length);

  (results.transactions || []).forEach((item) => {
    const entry = document.createElement("div");
    entry.className = "result-item";
    entry.textContent = `Row ${item.row}: ${item.description} (${item.amount})`;
    elements.importedList.appendChild(entry);
  });

  (results.errors || []).forEach((item) => {
    const entry = document.createElement("div");
    entry.className = "result-item";
    entry.textContent = `Row ${item.row}: ${item.reason}`;
    elements.errorsList.appendChild(entry);
  });

  (results.accounts_created || []).forEach((item) => {
    const entry = document.createElement("div");
    entry.className = "result-item";
    entry.textContent = item;
    elements.accountsList.appendChild(entry);
  });
}

async function importTransactions() {
  const mapping = collectMapping();
  const required = ["date", "amount", "description", "source_account", "destination_account"];
  const missing = required.filter((field) => !mapping[field]);
  if (missing.length) {
    showAlert("error", `Missing required mappings: ${missing.join(", ")}`);
    return;
  }
  if (!state.rows.length) {
    showAlert("error", "No rows available for import.");
    return;
  }
  setLoading(true, "Importing transactions...");
  try {
    const response = await fetch("/api/import-transactions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        rows: state.rows,
        mapping: mapping
      })
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "Import failed.");
    }
    renderResults(data.results, data.summary);
    setStep("step-3");
  } catch (error) {
    showAlert("error", error.message);
  } finally {
    setLoading(false);
  }
}

function resetFlow() {
  resetFile();
  setStep("step-1");
  elements.previewHead.innerHTML = "";
  elements.previewBody.innerHTML = "";
  elements.rowCount.textContent = "";
}

elements.uploadArea.addEventListener("click", () => elements.csvFile.click());

elements.uploadArea.addEventListener("dragover", (event) => {
  event.preventDefault();
  elements.uploadArea.classList.add("dragover");
});

elements.uploadArea.addEventListener("dragleave", () => {
  elements.uploadArea.classList.remove("dragover");
});

elements.uploadArea.addEventListener("drop", (event) => {
  event.preventDefault();
  elements.uploadArea.classList.remove("dragover");
  handleFileSelect(event.dataTransfer.files[0]);
});

elements.csvFile.addEventListener("change", (event) => {
  handleFileSelect(event.target.files[0]);
});

elements.clearFile.addEventListener("click", resetFile);

elements.parseBtn.addEventListener("click", parseCsv);

elements.csvFormat.addEventListener("change", () => {
  if (!state.columns.length) {
    return;
  }
  const mapping = detectMapping(state.columns, elements.csvFormat.value);
  applyMapping(mapping);
});

elements.importBtn.addEventListener("click", importTransactions);

elements.backStep2.addEventListener("click", () => setStep("step-1"));

elements.importAgain.addEventListener("click", resetFlow);

loadConfig();
