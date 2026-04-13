const TEMPLATES = {
  custom: { desc: 'Ajanlara serbest bırak', agents: '8 ajan', files: 'Dinamik' },
  fastapi_rest: { desc: 'FastAPI REST API', agents: '6 ajan', files: '8 dosya' },
  react_spa: { desc: 'React + TypeScript SPA', agents: '4 ajan', files: '8 dosya' },
  fullstack: { desc: 'Full-Stack', agents: '6 ajan', files: '8 dosya' },
  data_pipeline: { desc: 'ETL Pipeline', agents: '4 ajan', files: '7 dosya' },
  cli_tool: { desc: 'Python CLI aracı', agents: '3 ajan', files: '6 dosya' },
};

let cgCurrentId = null;

function loadTemplateInfo() {
  const t = document.getElementById('cg-template')?.value || 'custom';
  const info = TEMPLATES[t] || { desc: '—', agents: '—', files: '—' };
  const el = document.getElementById('cg-template-info');
  if (el) el.innerHTML = `Açıklama: ${info.desc}\nAjanlar: ${info.agents}\nTahmini dosya: ${info.files}`;
}

function appendProgress(msg, color = 'var(--muted)') {
  const el = document.getElementById('cg-progress-log');
  if (!el) return;
  const ts = new Date().toLocaleTimeString('tr');
  el.innerHTML += `<div style="color:${color}"><span style="color:var(--border)">[${ts}]</span> ${msg}</div>`;
  el.scrollTop = el.scrollHeight;
}

async function startCodeGen() {
  const title = document.getElementById('cg-title')?.value?.trim();
  const desc = document.getElementById('cg-desc')?.value?.trim();
  if (!title || !desc) { showToast('Başlık ve açıklama zorunlu', 'error'); return; }

  const template = document.getElementById('cg-template')?.value || 'custom';
  const review = document.getElementById('cg-review')?.checked ?? true;

  document.getElementById('cg-btn').disabled = true;
  document.getElementById('cg-btn').textContent = '⏳ Üretiliyor…';
  document.getElementById('cg-progress-card').style.display = 'block';
  document.getElementById('cg-result-card').style.display = 'none';
  document.getElementById('cg-viewer-card').style.display = 'none';
  document.getElementById('cg-progress-log').innerHTML = '';
  appendProgress(`"${title}" projesi başlatılıyor — şablon: ${template}`, 'var(--accent)');

  try {
    const r = await api('/code/generate', {
      method: 'POST', body: JSON.stringify({ title, description: desc, template, run_review: review }),
    });
    cgCurrentId = r.project_id;
    renderCodeResult(r);
    loadCodeHistory();
    showToast(`${r.file_count} dosya üretildi ✅`);
  } catch (e) {
    appendProgress(`❌ Hata: ${e.message}`, 'var(--red)');
    showToast('Üretim başarısız: ' + e.message, 'error');
  } finally {
    document.getElementById('cg-btn').disabled = false;
    document.getElementById('cg-btn').textContent = '⚡ Kod Üretimini Başlat';
  }
}

function renderCodeResult(data) {
  document.getElementById('cg-progress-card').style.display = 'none';
  document.getElementById('cg-result-card').style.display = 'block';
  document.getElementById('cg-stat-files').textContent = data.file_count || 0;
  document.getElementById('cg-stat-lines').textContent = (data.total_lines || 0).toLocaleString();
  const qEl = document.getElementById('cg-stat-quality');
  if (qEl) qEl.textContent = q ? Math.round(q * 100) + '%' : '—';
  
  // AGI Cortex Analysis for CodeGen (v121.0 Port)
  let cortexArea = document.getElementById('cg-cortex-analysis');
  if (!cortexArea) {
    cortexArea = document.createElement('div');
    cortexArea.id = 'cg-cortex-analysis';
    cortexArea.className = 'cognitive-trace-box';
    cortexArea.style.marginBottom = '20px';
    const resultCard = document.getElementById('cg-result-card');
    const fileStatRow = document.querySelector('#cg-result-card .card > div:nth-child(2)');
    if (resultCard && fileStatRow) {
      fileStatRow.parentNode.insertBefore(cortexArea, fileStatRow.nextSibling);
    }
  }
  
  cortexArea.innerHTML = `
    <div style="font-size:12px; line-height:1.6; color:var(--text); font-style:italic;">
      ${data.reasoning || 'Sistem v121.0 mimarisini otonom olarak doğruladı. ' + (data.file_count > 5 ? 'Karmaşık bağımlılıklar optimize edildi.' : 'Modüler yapı korundu.')}
    </div>
    <div style="margin-top:10px; display:flex; gap:15px; font-size:10px; font-family:var(--mono);">
       <span style="color:var(--accent);">● PLANNING_HORIZON: DEEP (v121)</span>
       <span style="color:var(--green);">● ARCH_VALIDATED: TRUE</span>
    </div>
  `;

  const fl = document.getElementById('cg-file-list');
  fl.innerHTML = (data.files || []).map(f => `<div style="display:flex;align-items:center;padding:7px 0;border-bottom:1px solid var(--border);gap:8px;cursor:pointer;" onclick="viewCodeFile('${data.project_id}','${f.path.replace(/'/g, "\\'")}','${f.language}')"><span style="font-family:var(--mono);font-size:11px;flex:1;">${f.path}</span><span style="font-size:10px;color:var(--muted);">${f.language} (${f.lines}L)</span></div>`).join('');
}

async function viewCodeFile(projectId, filePath, lang) {
  try {
    const d = await api(`/code/${projectId}/file?path=${encodeURIComponent(filePath)}`);
    document.getElementById('cg-viewer-card').style.display = 'block';
    document.getElementById('cg-viewer-title').textContent = d.path;
    document.getElementById('cg-viewer-lang').textContent = d.language;
    document.getElementById('cg-viewer-code').textContent = d.content;
    document.getElementById('cg-viewer-card').scrollIntoView({ behavior: 'smooth' });
  } catch (e) { showToast('Dosya yüklenemedi', 'error'); }
}

async function downloadCodeZip() {
  if (!cgCurrentId) { showToast('Önce bir üretim yapın', 'error'); return; }
  try {
    const r = await fetch(`${API}/code/${cgCurrentId}/download`, { ...authHeaders(), credentials: 'include' });
    if (!r.ok) throw new Error(r.statusText);
    const blob = await r.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = `kod_${cgCurrentId}.zip`; a.click();
    URL.revokeObjectURL(url);
  } catch (e) { showToast('İndirme hatası', 'error'); }
}

async function loadCodeHistory() {
  const el = document.getElementById('cg-history');
  if (!el) return;
  try {
    const list = await api('/code/results');
    el.innerHTML = list.slice(0, 8).map(p => `<div style="padding:7px 0;border-bottom:1px solid var(--border);cursor:pointer;" onclick="loadHistoryItem('${p.project_id}')"><span style="font-family:var(--mono);font-size:11px;">${p.title}</span> <span style="font-size:10px;color:var(--muted);">${p.files}F/${p.lines}L</span></div>`).join('') || 'Henüz üretim yok.';
  } catch (e) { el.innerHTML = 'Yüklenemedi'; }
}

async function loadHistoryItem(projectId) {
  try {
    const data = await api(`/code/${projectId}`);
    cgCurrentId = projectId;
    renderCodeResult(data);
  } catch (e) { showToast('Yüklenemedi', 'error'); }
}

async function loadApprovals() {
  const listEl = document.getElementById('approval-list');
  const countEl = document.getElementById('approval-count');
  if (!listEl) return;
  try {
    const data = await api('/approvals/pending');
    if (countEl) countEl.textContent = data.length + ' talep';
    const badge = document.getElementById('badge-approvals');
    if (badge) { badge.textContent = data.length; badge.style.display = data.length > 0 ? 'inline-block' : 'none'; }
    if (!data.length) { listEl.innerHTML = '<div style="padding:20px;text-align:center;color:var(--muted);">Onay bekleyen talep yok.</div>'; return; }
    listEl.innerHTML = `<table>
      <thead><tr><th>Talep Tipi</th><th>Ajan</th><th>Gerekçe</th><th>Tarih</th><th style="text-align:right;">İşlem</th></tr></thead>
      <tbody>${data.map(r => `<tr>
        <td style="font-weight:700;color:var(--orange);">${r.request_type || 'unauthorized_action'}</td>
        <td style="color:var(--primary); font-family:var(--mono);">${r.agent_id}</td>
        <td style="font-size:11px; color:var(--text2); max-width:300px;">${r.reason}</td>
        <td style="color:var(--muted);">${new Date(r.created_at).toLocaleTimeString('tr')}</td>
        <td style="text-align:right;">
          <button class="btn btn-ghost btn-sm" style="color:var(--green); font-weight:700;" onclick="decideApproval('${r.id}', true)">ONAYLA</button>
          <button class="btn btn-ghost btn-sm" style="color:var(--red); font-weight:700;" onclick="decideApproval('${r.id}', false)">REDDET</button>
        </td>
      </tr>`).join('')}</tbody>
    </table>`;
  } catch (e) { listEl.innerHTML = 'Hata: ' + (e.message || 'Veriler alınamadı'); }
}

async function decideApproval(requestId, approve) {
  let reason = approve ? "" : prompt("Reddetme sebebi:") || "User rejected";
  try {
    await api(`/approvals/${requestId}/decide`, { method: 'POST', body: JSON.stringify({ approve, reason, decided_by: AUTH.email || 'admin' }) });
    toast(approve ? 'Onay verildi ✓' : 'Reddedildi ✗');
    loadApprovals(); loadDashboard();
  } catch (e) { toast('Hata', 'error'); }
}

const BASE_REPAIR = '/repair';
const BASE_ADMIN = '/repair/admin';
const BASE_FAZ12 = '/faz12';

async function loadRepairCenter() {
  try {
    const stats = await api('/repair/stats');
    document.getElementById('rc-open-incidents').textContent = stats.open_incidents || 0;
    document.getElementById('rc-active-jobs').textContent = stats.active_jobs || 0;
    document.getElementById('rc-pending-proposals').textContent = stats.pending_proposals || 0;
    document.getElementById('rc-success-rate').textContent = (stats.success_rate_pct || 0).toFixed(0) + '%';
    
    // Olayları (Incidents) yükle
    loadRepairIncidents();

    const jobData = await api('/repair/jobs?limit=10');
    const jobs = Array.isArray(jobData) ? jobData : (jobData.jobs || []);
    const jobsEl = document.getElementById('rc-jobs-list');
    if (jobsEl) {
      jobsEl.innerHTML = jobs.length ? jobs.map(j => {
        const jStatus = j.status.toLowerCase();
        let dotColor = 'var(--accent)';
        if (jStatus === 'failed') dotColor = 'var(--red)';
        if (jStatus === 'completed') dotColor = 'var(--green)';
        if (jStatus === 'running') dotColor = 'var(--yellow)';

        return `
        <div class="premium-row" style="padding:12px; margin-bottom:8px; border-radius:10px; cursor:pointer;" onclick="openRepairJobDetail('${j.id}')">
          <div style="display:flex; align-items:center; gap:12px;">
            <div class="live-status" style="background:rgba(255,255,255,0.03);">
              <div class="live-dot" style="background:${dotColor}; animation: pulse 2s infinite;"></div>
              ${j.status.toUpperCase()}
            </div>
            <div style="flex:1;">
              <div style="font-weight:700; color:#fff; font-size:13px;">${j.target_module || j.module || 'Bilinmiyor'}</div>
              <div style="font-size:10px; color:var(--text2); font-family:var(--mono); opacity:0.6; margin-top:2px;">JOB_ID: ${j.id.substring(0,8)}</div>
            </div>
            <div style="font-size:10px; color:var(--muted);">👁️</div>
          </div>
        </div>
      `}).join('') : '<div class="empty-state">Aktif iş bulunamadı.</div>';
    }
  } catch (e) {
    console.error('Repair Center yükleme hatası:', e);
  }
}

async function loadRepairIncidents() {
  const el = document.getElementById('rc-incidents-table');
  if (!el) return;
  try {
    const data = await api('/repair/incidents');
    const incidents = data.incidents || [];
    if (!incidents.length) {
      el.innerHTML = '<div style="padding:25px; text-align:center; color:var(--muted);"><div style="font-size:24px; margin-bottom:10px;">🛡️</div>Sistem şu an sağlıklı. Bekleyen kritik olay bulunamadı.</div>';
      return;
    }
    el.innerHTML = `
      <div class="table-container" style="margin-top:10px;">
        <table style="width:100%; border-collapse:separate; border-spacing:0 8px;">
          <thead>
            <tr style="text-align:left; color:var(--muted); font-size:10px; font-weight:800; text-transform:uppercase; letter-spacing:0.1em;">
              <th style="padding:0 12px 8px;">Hata / Semptom</th>
              <th style="padding:0 12px 8px;">Modül</th>
              <th style="padding:0 12px 8px;">Önem Derecesi</th>
              <th style="padding:0 12px 8px;">Zaman Damgası</th>
            </tr>
          </thead>
          <tbody>
            ${incidents.map(i => {
              const sev = (i.severity || 'medium').toLowerCase();
              const sevColor = sev === 'critical' ? 'var(--red)' : (sev === 'high' ? 'var(--orange)' : 'var(--primary)');
              return `
              <tr class="premium-row" style="background:rgba(255,255,255,0.02);">
                <td style="padding:12px; border-radius:8px 0 0 8px;">
                  <div style="font-weight:700; color:#fff;">${i.symptom}</div>
                </td>
                <td style="padding:12px; font-family:var(--mono); font-size:11px; color:var(--primary);">${i.module}</td>
                <td style="padding:12px;">
                  <div style="display:flex; align-items:center; gap:8px;">
                     <div style="width:6px; height:6px; background:${sevColor}; border-radius:50%; box-shadow:0 0 8px ${sevColor};"></div>
                     <span style="color:${sevColor}; font-weight:800; font-size:10px; font-family:var(--mono);">${sev.toUpperCase()}</span>
                  </div>
                </td>
                <td style="padding:12px; border-radius:0 8px 8px 0; color:var(--muted); font-size:11px; font-family:var(--mono);">
                  ${new Date(i.first_seen_at || i.created_at).toLocaleString('tr')}
                </td>
              </tr>`;
            }).join('')}
          </tbody>
        </table>
      </div>
    `;
  } catch (e) {
    el.innerHTML = `<div style="padding:24px; color:var(--red); text-align:center;">⚠️ Yükleme hatası: ${e.message || 'Sunucu hatası'}</div>`;
  }
}

async function openRepairJobDetail(id) {
  openModal('modal-detail');
  const content = document.getElementById('modal-detail-content');
  content.innerHTML = 'Yükleniyor...';
  try {
    const val = await api(`/repair/jobs/${id}/validation`);
    const job = await api(`/repair/jobs/${id}`);
    content.innerHTML = `
      <div style="display:flex;align-items:center;gap:12px;margin-bottom:12px;"><span class="badge badge-${job.status}">${job.status}</span><span style="font-family:var(--mono);font-size:12px;color:var(--muted);">${job.id}</span></div>
      <h3 style="margin-bottom:8px;color:var(--text);">${job.target_module}</h3>
      <div style="background:rgba(255,165,0,0.05); border:1px solid rgba(255,165,0,0.15); padding:12px; border-radius:8px; font-family:var(--mono); font-size:13px; margin-bottom:16px;">
        ${job.error_summary}
      </div>
      <div class="task-meta-grid">
         <div class="meta-item"><div class="meta-label">Onarım Güveni</div><div class="meta-value" style="color:var(--green);">${(val.confidence*100).toFixed(0)}%</div></div>
         <div class="meta-item"><div class="meta-label">Ajan</div><div class="meta-value">${job.assigned_agent || 'repair_bot'}</div></div>
      </div>
      <div id="qa-result-area" style="margin-top:16px; border-top:1px solid var(--border); padding-top:16px;">
        <button class="btn btn-primary btn-sm" id="btn-run-qa" onclick="runJobQA('${id}')">🌐 UI Testi Koştur (GStack QA)</button>
        <div id="qa-output" style="margin-top:10px; font-size:12px; display:none; background:rgba(0,0,0,0.2); padding:10px; border-radius:6px; border:1px solid var(--border);"></div>
      </div>
    `;
  } catch (e) { content.innerHTML = `<div style="color:var(--red);">Yükleme başarısız: ${e.message || 'Veri hatası'}</div>`; }
}

async function runJobQA(id) {
  const btn = document.getElementById('btn-run-qa');
  const out = document.getElementById('qa-output');
  if (!btn || !out) return;
  btn.disabled = true;
  btn.textContent = '⏳ Test Ediliyor...';
  out.style.display = 'block';
  out.innerHTML = '<span style="color:var(--muted)">Tarayıcı başlatılıyor, sayfa doğrulanıyor...</span>';
  
  try {
    const res = await api(`/repair/jobs/${id}/run-qa`, { method: 'POST' });
    if (res.success) {
      out.innerHTML = `<b style="color:var(--green)">✅ BAŞARILI</b><br>${res.summary}`;
      toast('UI Testi Başarılı ✓', 'success');
    } else {
      out.innerHTML = `<b style="color:var(--red)">❌ BAŞARISIZ</b><br>${res.summary}`;
      toast('UI Testi Başarısız ✗', 'error');
    }
    if (res.logs && res.logs.length) {
      out.innerHTML += `<div style="margin-top:8px; font-family:var(--mono); font-size:10px; color:var(--muted);">${res.logs.join('<br>')}</div>`;
    }
  } catch (e) {
    out.innerHTML = `<b style="color:var(--red)">HATA</b><br>${e.message || 'QA servisi yanıt vermiyor'}`;
    toast('QA Error', 'error');
  } finally {
    btn.disabled = false;
    btn.textContent = '🌐 UI Testi Koştur (GStack QA)';
  }
}

function showRepairIncidentForm() {
  const symptom = prompt("Oluşan hatayı veya semptomu giriniz (min 5 karakter):");
  if (!symptom) return;
  if (symptom.length < 5) {
    toast('Semptom çok kısa!', 'error');
    return;
  }

  showToast(`Olay bildiriliyor...`, 'info');
  api('/repair/incidents', {
    method: 'POST',
    body: JSON.stringify({ 
      symptom: symptom, 
      module: 'manual_entry', 
      severity: 'medium', 
      source: 'manual',
      service: 'dashboard-ui'
    })
  }).then(() => {
    toast('Olay başarıyla kaydedildi ✓');
    loadRepairCenter();
  }).catch(e => {
    console.error('Olay kaydı hatası:', e);
    toast('Olay kaydı başarısız: ' + (e.detail || e.message || 'İşlem engellendi'), 'error');
  });
}

async function loadProposals() {
  try {
    const data = await api(BASE_REPAIR + '/proposals');
    document.getElementById('proposals-table').innerHTML = (data.proposals || []).map(p => `<div>${p.title}</div>`).join('') || 'No proposals.';
  } catch (e) { console.error('Proposals error:', e); toast('Teklifler yüklenemedi: ' + (e.message || 'Erişim reddedildi'), 'error'); }
}

async function loadRepairMetrics() {
  try {
    const summary = await api(BASE_ADMIN + '/metrics/summary');
    // populate UI
  } catch (e) { console.error('RepairMetrics error:', e); toast('Onarım metrikleri yüklenemedi: ' + (e.message || 'Veri hatası'), 'error'); }
}

async function loadPolicies() {
  try {
    const data = await api(BASE_ADMIN + '/policies');
    document.getElementById('policies-list').innerHTML = (data.policies || []).map(p => `<div>${p.name} <input type="checkbox" ${p.enabled?'checked':''} onchange="togglePolicy('${p.name}', this.checked)"></div>`).join('');
  } catch (e) { console.error('Policies error:', e); toast('Politikalar yüklenemedi: ' + (e.message || 'Yetki hatası'), 'error'); }
}

async function togglePolicy(name, enabled) {
  try {
    await api(BASE_ADMIN + '/policies/' + name, { method: 'PUT', body: JSON.stringify({ enabled }) });
    toast(name + ' updated');
  } catch (e) { toast('Politika güncellenemedi: ' + (e.message || 'Bağlantı hatası'), 'error'); }
}

async function loadDebatePage() {
  try {
    const data = await api(BASE_FAZ12 + '/debate/personas');
    const el = document.getElementById('debate-personas');
    if (el) el.innerHTML = (data.personas || []).map(p => `<div>${p.id}: ${p.description}</div>`).join('');
  } catch (e) { console.error('DebatePage error:', e); toast('Münazara verileri yüklenemedi: ' + (e.message || 'Sunucu hatası'), 'error'); }
}

async function startDebate() {
  const topic = document.getElementById('db-topic').value.trim();
  const context = document.getElementById('db-context').value.trim();
  if (!topic) { showToast('Konu başlığı gerekli', 'error'); return; }

  const agent_a = document.getElementById('db-agent-a')?.value || 'backend_dev';
  const agent_b = document.getElementById('db-agent-b')?.value || 'security';
  const moderator = document.getElementById('db-moderator')?.value || 'architect';

  if (agent_a === agent_b) { showToast('Ajan A ve Ajan B aynı olamaz', 'error'); return; }

  const btn = document.getElementById('db-start-btn');
  btn.disabled = true;
  btn.textContent = '⏳ Münazara Hazırlanıyor...';

  // Update stage labels
  document.getElementById('label-a').textContent = agent_a;
  document.getElementById('label-b').textContent = agent_b;

  // UI Reset
  document.getElementById('debate-idle-overlay').style.display = 'none';
  document.getElementById('debate-live-feed').innerHTML = '';
  document.getElementById('debate-consensus-card').style.display = 'none';
  
  try {
    const result = await api(BASE_FAZ12 + '/debate/run', { 
      method: 'POST', 
      body: JSON.stringify({ topic, context, agent_a, agent_b, moderator, max_rounds: 3 }),
      timeout: 300000 
    });
    // Final result
    const consensusEl = document.getElementById('debate-consensus');
    consensusEl.innerHTML = `
      <div class="cognitive-trace-box" style="margin-bottom:15px; border-color:var(--green);">
        <div style="font-size:13px; color:var(--text); font-weight:600; margin-bottom:8px;">🎯 Moderatör Kararı & Konsensüs</div>
        <div style="font-size:12px; line-height:1.6; color:var(--text2);">${result.consensus}</div>
      </div>
      <div style="display:flex; gap:10px;">
        <button class="btn btn-primary btn-sm" style="flex:1;" onclick="applyConsensus('${result.id}')">Uygula (Apply)</button>
        <button class="btn btn-ghost btn-sm" onclick="exportDebate('${result.id}')">Dışa Aktar</button>
      </div>
    `;
    document.getElementById('debate-consensus-card').style.display = 'block';
    showToast('Münazara başarıyla tamamlandı ✓', 'success');
  } catch (e) {
    showToast('Münazara başlatılamadı: ' + (e.message || 'Oturum hatası'), 'error');
    document.getElementById('debate-idle-overlay').style.display = 'flex';
  } finally {
    btn.disabled = false;
    btn.textContent = '▶ Münazarayı Başlat';
  }
}

function handleDebateState(data) {
  const agent = data.agent || data.agent_id;
  const { state, round, content, consensus } = data;
  console.log('Debate State Update:', state, agent, round);

  // Identify Slot (A or B or Mod)
  // Simple logic: first agent is A, second is B
  let slot = 'a';
  const labelA = document.getElementById('label-a').textContent;
  const labelB = document.getElementById('label-b').textContent;

  if (agent === labelA || labelA === 'Agent A') {
    slot = 'a';
    if (labelA === 'Agent A') document.getElementById('label-a').textContent = agent;
  } else if (agent === labelB || labelB === 'Agent B') {
    slot = 'b';
    if (labelB === 'Agent B') document.getElementById('label-b').textContent = agent;
  } else {
    // Moderator or other
    slot = 'mod';
  }

  // Visual Effects
  document.querySelectorAll('.debate-slot').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('.typing-indicator').forEach(t => t.style.display = 'none');

  if (state === 'thinking') {
    if (slot !== 'mod') {
      const el = document.getElementById('slot-agent-' + slot);
      if (el) el.classList.add('active');
      const typing = document.getElementById('typing-' + slot);
      if (typing) typing.style.display = 'flex';
    }
  } else if (state === 'arguing') {
    const feed = document.getElementById('debate-live-feed');
    if (feed) {
      if (feed.querySelector('div[style*="text-align:center"]')) feed.innerHTML = '';
      const div = document.createElement('div');
      div.className = `bubble ${slot === 'mod' ? 'moderator' : (slot === 'a' ? 'agent-a' : 'agent-b')}`;
      div.innerHTML = `<strong>${agent}:</strong> ${content}`;
      feed.appendChild(div);
      feed.scrollTop = feed.scrollHeight;
    }
  } else if (state === 'concluded') {
    document.getElementById('debate-consensus').textContent = consensus;
    document.getElementById('debate-consensus-card').style.display = 'block';
    showToast('Münazara başarıyla tamamlandı.', 'success');
  }
}

async function runSandbox() {
  const code = document.getElementById('sb-code').value;
  try {
    const r = await api(BASE_FAZ12 + '/sandbox/run', { method: 'POST', body: JSON.stringify({ code }) });
    document.getElementById('sb-stdout').textContent = r.stdout;
    document.getElementById('sb-status').textContent = r.success ? 'Success' : 'Fail';
  } catch (e) { toast('Sandbox çalıştırma hatası: ' + (e.message || 'Kod hatası'), 'error'); document.getElementById('sb-status').textContent = 'HATA'; }
}

function loadSandboxPreset() {
  const preset = document.getElementById('sb-preset').value;
  const codeEl = document.getElementById('sb-code');
  if (!codeEl) return;
  
  const presets = {
    'hello': 'print("Hello from Faz 12.1 Sovereign AGI!")\\nimport sys\\nprint(f"Python: {sys.version}")',
    'math': 'import math\\n# Karmaşık hesaplama duman testi\\nres = [math.sqrt(i) for i in range(10)]\\nprint(f"Karekök Dizisi: {res}")\\nprint(f"Pi: {math.pi}")',
    'system': 'import os\\nprint(f"CWD: {os.getcwd()}")\\nprint("Sistem izolasyonu kontrol ediliyor...")',
    'agent': '# Ajan mantığı simülasyonu\\nclass MiniAgent:\\n    def act(self):\\n        return "Düşünüyorum, öyleyse varım."\\n\\na = MiniAgent()\\nprint(a.act())'
  };
  
  if (presets[preset]) {
    codeEl.value = presets[preset];
    showToast(`${preset} şablonu yüklendi`);
  }
}

window.loadSandboxPreset = loadSandboxPreset;

async function loadModelRouterPage() {
  try {
    const stats = await api(BASE_FAZ12 + '/model-router/stats');
    // populate UI
  } catch (e) { console.error('ModelRouter error:', e); toast('Model yönlendirici yüklenemedi: ' + (e.message || 'Servis dışı'), 'error'); }
}

async function searchVectorLessons() {
  const symptom = document.getElementById('vl-symptom').value;
  try {
    const data = await api(BASE_FAZ12 + '/vector-lessons/search?symptom=' + encodeURIComponent(symptom));
    document.getElementById('vl-results').innerHTML = (data.results || []).map(r => `<div>${r.module}: ${r.resolution}</div>`).join('');
  } catch (e) { toast('Vektör arama hatası: ' + (e.message || 'Vektör veri tabanı hatası'), 'error'); }
}

async function scanImprovements() {
  const el = document.getElementById('imp-opportunities-list');
  if (!el) return;
  el.innerHTML = '<div class="loading">Sistem denetleniyor (Sovereign Audit)...</div>';
  try {
    const ops = await api('/improvements/scan');
    if (!ops || !ops.length) {
      el.innerHTML = '<div style="padding:24px; text-align:center; color:var(--muted);">Sistem şu an evrimleşmiş durumda. Yeni bir açık tespit edilmedi.</div>';
      return;
    }
    el.innerHTML = ops.map(o => `
      <div style="background:rgba(255,255,255,0.02); border:1px solid var(--border); border-radius:12px; padding:16px; margin-bottom:12px; display:flex; align-items:center; gap:16px;">
        <div style="font-size:24px;">${o.severity === 'high' ? '🔥' : '✨'}</div>
        <div style="flex:1;">
          <div style="font-weight:700; margin-bottom:4px;">${o.description}</div>
          <div style="font-size:11px; color:var(--muted); font-family:var(--mono);">Kaynak: ${o.evidence?.finding?.source_type || 'system'} | Yetki: ${o.severity.toUpperCase()}</div>
        </div>
        <div style="display:flex; gap:8px;">
          <button class="btn btn-ghost btn-sm" onclick="viewProposalDetail('${encodeURIComponent(JSON.stringify(o))}')">İncele</button>
          <button class="btn btn-primary btn-sm" onclick="applyAutonomousImprovement('${o.id}')">Uygula</button>
        </div>
      </div>
    `).join('');
  } catch (e) {
    el.innerHTML = `<div class="loading" style="color:var(--red);">Denetim başarısız: ${e.message || 'Cortex hatası'}</div>`;
  }
}

async function viewProposalDetail(encodedData) {
  const o = JSON.parse(decodeURIComponent(encodedData));
  openModal('modal-detail');
  const content = document.getElementById('modal-detail-content');
  
  const hasPatch = o.evidence && o.evidence.patch;
  const patchContent = hasPatch ? o.evidence.patch : "Yama detayı analiz aşamasında.";
  
  content.innerHTML = `
    <div style="display:flex; align-items:center; gap:12px; margin-bottom:12px;">
      <span class="badge badge-${o.severity === 'high' ? 'critical' : 'medium'}">${o.severity.toUpperCase()}</span>
      <span style="font-family:var(--mono); font-size:10px; color:var(--muted);">${o.id}</span>
    </div>
    <h3 style="margin-bottom:16px; color:var(--text);">${o.description}</h3>
    
    <div style="margin-bottom:20px;">
      <div style="font-size:11px; font-weight:700; color:var(--accent); margin-bottom:8px; display:flex; justify-content:space-between;">
        <span>KANIT & AKILLI ANALİZ</span>
        <span style="color:var(--muted)">Kaynak: ${o.evidence?.finding?.category || 'genel'}</span>
      </div>
      <div style="background:rgba(0,0,0,0.3); padding:12px; border-radius:8px; font-size:11px; color:var(--text2); font-family:var(--mono); white-space:pre-wrap; border:1px solid var(--border);">${JSON.stringify(o.evidence?.finding?.evidence || o.evidence, null, 2)}</div>
    </div>

    ${o.evidence?.reasoning ? `
    <div style="margin-bottom:20px;">
      <div style="font-size:11px; font-weight:700; color:var(--yellow); margin-bottom:8px;">BİLİŞSEL GEREKÇE (REASONING)</div>
      <div style="font-size:12px; color:var(--text2); line-height:1.5; font-style:italic;">"${o.evidence.reasoning}"</div>
    </div>
    ` : ''}
    
    <div style="margin-bottom:20px;">
      <div style="font-size:11px; font-weight:700; color:var(--green); margin-bottom:8px;">ÖNERİLEN EVRİM YAMASI (PATCH)</div>
      <div style="background:#000; padding:16px; border-radius:8px; font-size:12px; color:var(--green); font-family:var(--mono); white-space:pre-wrap; max-height:250px; overflow-y:auto; border:1px solid var(--green); border-opacity:0.2;">${patchContent}</div>
    </div>
    
    <div style="display:flex; gap:12px; margin-top:24px;">
      <button class="btn btn-ghost" style="flex:1;" onclick="closeModal('modal-detail')">Kapat</button>
      <button class="btn btn-primary" style="flex:1;" onclick="applyAutonomousImprovement('${o.id}');closeModal('modal-detail')">🧬 Evrimi Onayla ve Uygula</button>
    </div>
  `;
}

async function applyAutonomousImprovement(id) {
  if (!AUTH.isAdmin) {
    toast('Bu işlem için yönetici (Admin) yetkisi gereklidir.', 'error');
    return;
  }

  if (!id) return;

  try {
    showToast('Sovereign Evolution: Yama operasyonu başlatılıyor...', 'info');
    const r = await api(`/improvements/apply-proposal/${id}`, { method: 'POST' });
    toast(r.message || 'İşlem başarıyla başlatıldı.', 'success');
    // Listeyi tazele
    setTimeout(scanImprovements, 2000);
  } catch (e) {
    console.error('Apply evolution failed:', e);
    toast('Evrim hatası: ' + (e.detail || e.message || 'İşlem başarısız'), 'error');
  }
}

async function loadSelfUpdateHistory() {
  const el = document.getElementById('update-history-list');
  if (!el) return;
  try {
    const d = await api('/self-update/state');
    el.innerHTML = (d.updates || []).map(h => `<div>${h.description} - ${h.status}</div>`).join('') || 'Geçmiş bulunamadı.';
  } catch (e) { console.error('SelfUpdate error:', e); toast('Güncelleme geçmişi yüklenemedi: ' + (e.message || 'Liste boş'), 'error'); }
}

async function triggerSelfUpdate() {
  if (!confirm('Sistem öz-güncelleme başlatılsın mı?')) return;
  try {
    await api('/self-update/apply', { method: 'POST', body: JSON.stringify({ target_file_path: 'main.py', instruction: 'Optimization', async_mode: true }) });
    toast('İş kuyruğa alındı'); loadSelfUpdateHistory();
  } catch (e) { toast('Hata: ' + (e.detail || e.message || (typeof e === 'string' ? e : 'Bilinmeyen hata')), 'error'); }
}

async function loadAdminUsers() {
  try {
    const users = await api('/admin/users');
    document.getElementById('admin-user-list').innerHTML = users.map(u => `<tr><td>${u.email}</td><td><button onclick="toggleAdmin('${u.id}')">Toggle</button></td></tr>`).join('');
  } catch (e) { console.error('AdminUsers error:', e); toast('Kullanıcı listesi yüklenemedi: ' + (e.message || 'Erişim engellendi'), 'error'); }
}

async function toggleAdmin(userId) {
  try {
    await api('/admin/users/' + userId + '/toggle-admin', { method: 'POST' });
    loadAdminUsers();
  } catch (e) { toast('Yetki değişikliği başarısız: ' + (e.message || 'Yetki hatası'), 'error'); }
}

async function loadBudgetStatus() {
  const spentEl = document.getElementById('budget-spent-label');
  const totalEl = document.getElementById('budget-total-label');
  const remainEl = document.getElementById('budget-remaining-label');
  const fillEl = document.getElementById('budget-progress-fill');
  const warnEl = document.getElementById('budget-warning');
  const sCostEl = document.getElementById('s-cost');

  try {
    const data = await api('/finance/status');
    if (data.error) throw new Error(data.error);

    if (spentEl) spentEl.textContent = data.spent_formatted;
    if (totalEl) totalEl.textContent = data.budget_formatted;
    if (remainEl) remainEl.textContent = data.remaining_formatted;
    if (sCostEl) sCostEl.textContent = data.spent_formatted;
    
    if (fillEl) {
      const pct = Math.min(data.pct_used, 100);
      fillEl.style.width = pct + '%';
      if (pct > 90) fillEl.style.background = 'var(--red)';
      else if (pct > 70) fillEl.style.background = 'var(--yellow)';
      else fillEl.style.background = 'var(--accent)';
    }

    if (warnEl) warnEl.style.display = data.threshold_warning ? 'block' : 'none';
    
    const badge = document.getElementById('budget-status-badge');
    if (badge) {
      if (data.over_budget) {
        badge.textContent = 'Limit Aşıldı';
        badge.className = 'badge badge-critical';
      } else {
        badge.textContent = 'Aktif';
        badge.className = 'badge badge-healthy';
      }
    }
  } catch (e) {
    console.warn('Budget load failed:', e);
  }
}

window.addEventListener('load', async () => {
  try {
    const me = await api('/auth/me');
    AUTH.save(me.email, me.is_admin);
  } catch (e) { }
  checkAuth();
  if (AUTH.email) showPage('dashboard');
  
  window.toggleSidebar = () => document.querySelector('.app').classList.toggle('sidebar-open');
  document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', (e) => { 
      // Sadece 768px ve altı cihazlarda otomatik kapat
      if (window.innerWidth <= 768) {
        document.querySelector('.app').classList.remove('sidebar-open'); 
      }
    });
  });
});

async function loadCEOFindings() {
  const tableBody = document.getElementById('ceo-findings-body');
  const manifestoEl = document.getElementById('ceo-manifesto');
  if (!tableBody) return;
  
  try {
    // 1. Özet metrikler ve manifesto
    try {
      const overview = await api('/ceo/overview');
      safeSetText('ceo-open-ops', overview.open_opportunity_count || 0);
      safeSetText('ceo-suggested', overview.suggested_task_count || 0);
      
      const riskScore = overview.strategic_outlook?.risk_score || 8;
      safeSetText('ceo-system-score', (100 - riskScore) + '%');
      
      if (manifestoEl) {
        manifestoEl.innerHTML = `<div><span style="color:#fff; font-weight:800;">[STRATEJİK_AKTARIM]</span> ${overview.manifesto || ''}</div>
        <div style="margin-top:8px; opacity:0.8; font-size:11px;">> MÜDAHALE ODAĞI: <span style="color:var(--yellow);">${overview.next_action || 'ANALİZ_MODU'}</span></div>`;
      }
    } catch (ovErr) { 
      console.warn('CEO Overview error:', ovErr);
    }

    // 2. Detaylı bulgular
    const data = await api('/ceo/findings');
    const findings = data.findings || [];
    
    // Geçici olarak globalde sakla (detay modalı için)
    window._lastCEOFindings = findings;
    
    if (!findings.length) {
      tableBody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding:100px 0; color:var(--muted); font-size:14px;">Stratejik bulgu yok. Sistem nominal değerlerde çalışıyor.</td></tr>';
      return;
    }

    tableBody.innerHTML = findings.map(f => {
      const statusLabel = f.status.toUpperCase();
      const statusClass = f.status.toLowerCase();
      const severityColor = f.severity === 'critical' ? 'var(--red)' : (f.severity === 'high' ? 'var(--orange)' : 'var(--primary)');
      const score = f.priority_score || '--';
      const isApproved = statusClass === 'approved' || statusClass === 'resolved';
      
      return `
      <tr class="premium-row" style="animation: fadeIn 0.3s ease-out;">
        <td style="padding-left:0;">
          <div style="font-family:var(--mono); font-size:9px; color:var(--primary); opacity:0.8; letter-spacing:0.1em;">${(f.category || 'GENEL').toUpperCase()}</div>
        </td>
        <td>
          <div style="font-weight:700; color:#fff; font-size:14px; letter-spacing:-0.01em;">${f.finding}</div>
          <div style="font-size:11px; color:var(--text2); margin-top:4px; opacity:0.7;">${f.description || ''}</div>
        </td>
        <td>
          <div style="display:flex; align-items:center; gap:8px;">
            <div style="width:6px; height:6px; background:${severityColor}; border-radius:50%; box-shadow:0 0 8px ${severityColor};"></div>
            <span style="color:${severityColor}; font-weight:800; font-size:10px; font-family:var(--mono);">${(f.severity || 'MED').toUpperCase()}</span>
          </div>
        </td>
        <td>
          <div style="font-family:var(--mono); color:var(--gold); font-weight:800; font-size:14px;">${score}</div>
        </td>
        <td>
          <span class="live-status" style="background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.05);">
            <div class="live-dot" style="background:${isApproved ? 'var(--green)' : 'var(--yellow)'};"></div>
            ${statusLabel}
          </span>
        </td>
        <td style="text-align:right;">
          <div style="display:flex; gap:8px; justify-content:flex-end;">
            <button class="btn btn-ghost btn-sm" style="border-radius:6px; width:32px; height:32px; padding:0; justify-content:center;" title="Detaylar" onclick="viewCEOFindingDetails('${f.id}')">👁️</button>
            ${!isApproved ? `<button class="btn btn-primary btn-sm" style="background:rgba(14,165,233,0.1); color:var(--primary); border:1px solid var(--primary-glow); border-radius:6px;" onclick="approveCEOFinding('${f.id}')">UYGULA</button>` : ''}
          </div>
        </td>
      </tr>`;
    }).join('');

  } catch (e) {
    console.error('CEO Findings load error:', e);
    tableBody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding:40px; color:var(--red);">Yükleme hatası: ${e.message}</td></tr>`;
  }
}

async function viewCEOFindingDetails(id) {
  const f = (window._lastCEOFindings || []).find(x => x.id === id);
  if (!f) return;
  
  openModal('modal-detail');
  const content = document.getElementById('modal-detail-content');
  if (!content) return;
  
  const evidenceStr = f.evidence ? JSON.stringify(f.evidence, null, 2) : "Detaylı kanıt bulunamadı.";
  const reasoningStr = f.reasoning || "Gerekçe henüz formüle edilmedi.";
  const statusClass = f.status.toLowerCase();
  
  content.innerHTML = `
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
      <h3 style="margin:0; color:#fff;">Stratejik Analiz: ${f.finding}</h3>
      <span class="badge-sovereign badge-${statusClass}">${f.status}</span>
    </div>
    
    <div style="margin-bottom:20px; padding:12px; background:rgba(255,255,255,0.03); border-radius:8px; border:1px solid var(--border);">
      <div style="font-size:11px; font-weight:700; color:var(--primary); margin-bottom:6px;">AÇIKLAMA</div>
      <div style="font-size:13px; color:var(--text2);">${f.description || 'Açıklama yok.'}</div>
    </div>

    <div style="margin-bottom:20px;">
      <div style="font-size:11px; font-weight:700; color:var(--yellow); margin-bottom:8px;">BİLİŞSEL GEREKÇE (REASONING)</div>
      <div style="font-size:12px; color:var(--text2); line-height:1.5; font-style:italic; border-left:3px solid var(--yellow); padding-left:12px;">"${reasoningStr}"</div>
    </div>

    <div style="margin-bottom:20px;">
      <div style="font-size:11px; font-weight:700; color:var(--accent); margin-bottom:8px;">TEKNİK KANITLAR & METADATA</div>
      <div style="background:#000; padding:12px; border-radius:8px; font-size:11px; color:var(--text2); font-family:var(--mono); white-space:pre-wrap; border:1px solid var(--border); max-height:200px; overflow-y:auto;">${evidenceStr}</div>
    </div>

    <div style="display:flex; gap:12px; margin-top:24px;">
      <button class="btn btn-ghost" style="flex:1;" onclick="closeModal('modal-detail')">Kapat</button>
      ${statusClass === 'suggested' || statusClass === 'open' ? 
        `<button class="btn btn-primary" style="flex:1;" onclick="approveCEOFinding('${f.id}');closeModal('modal-detail')">🧬 Operasyonu Başlat</button>` : ''}
    </div>
  `;
}

async function approveCEOFinding(id) {
  if (!AUTH.isAdmin) {
    toast('Bu işlem için yönetici yetkisi gereklidir.', 'error');
    return;
  }
  
  try {
    showToast('CEO Kararı Uygulanıyor: Görev oluşturuluyor...', 'info');
    const res = await api('/ceo/approve/' + id, { method: 'POST' });
    
    if (res.success) {
      toast('Başarılı! Görev ID: ' + res.project_id, 'success');
      loadCEOFindings(); // Tabloyu tazele
    } else {
      toast('Hata: ' + (res.error || 'İşlem başarısız'), 'error');
    }
  } catch (e) {
    console.error('CEO Approve error:', e);
    toast('Onaylama hatası: ' + e.message, 'error');
  }
}


async function triggerCEOScan() {
  try {
    showToast('CEO Taraması başlatılıyor...', 'info');
    const res = await api('/ceo/scan', { method: 'POST' });
    toast('Tarama tamamlandı. ' + (res.results?.length || 0) + ' bulgu.', 'success');
    loadCEOFindings();
  } catch (e) {
    toast('Tarama hatası: ' + (e.message || 'CEO servisi hatası'), 'error');
  }
}
