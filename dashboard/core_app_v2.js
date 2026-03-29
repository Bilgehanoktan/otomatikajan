const API = '/api/v1';
let wsConn = null;

// Capability flags for dynamic UI (Phase 4/5)
let CAPS = {
  supports_cancel: false,
  supports_pause: false,
  supports_resume: false
};

/**
 * DASHBOARD HONESTY & STABILITY GUARDS
 * Prevents "Silent Errors" and "False Positives" due to missing DOM elements.
 */
function safeGet(id) { 
  const el = document.getElementById(id);
  if (!el && !id.startsWith('badge-')) {
    // Console only for development or debug
    // console.warn(`[DOM Guard] Request for missing element: #${id}`);
  }
  return el;
}

function safeSetText(id, text) {
  const el = safeGet(id);
  if (el) el.textContent = text;
}

function safeSetHTML(id, html) {
  const el = safeGet(id);
  if (el) el.innerHTML = html;
}

function safeStyle(id, styleObj) {
  const el = safeGet(id);
  if (el) Object.assign(el.style, styleObj);
}

/**
 * Görev kontrol butonlarını (iptal, duraklat vb.) sistem kabiliyetine göre gizler/gösterir.
 * Optimistik UI yerine 'Honest UI' yaklaşımı için gereklidir.
 */
function applyCapabilityVisibility() {
  const taskDetail = safeGet('modal-detail-content');
  if (taskDetail) {
    // Detay modalındaki butonlar
    const cancelBtn = taskDetail.querySelector('button[onclick*="cancelTask"]');
    if (cancelBtn) cancelBtn.style.display = CAPS.supports_cancel ? 'inline-block' : 'none';
    
    const pauseBtn = taskDetail.querySelector('button[onclick*="pauseTask"]');
    if (pauseBtn) pauseBtn.style.display = CAPS.supports_pause ? 'inline-block' : 'none';
    
    const resumeBtn = taskDetail.querySelector('button[onclick*="resumeTask"]');
    if (resumeBtn) resumeBtn.style.display = CAPS.supports_resume ? 'inline-block' : 'none';
  }

  // Görev tablosundaki butonlar için loadTasks içinde zaten kontrol var (inline check), 
  // ancak dinamik güncellemelerde loadTasks'ı tekrar tetiklemek en garantisidir.
}

function refreshAll() {
  console.log('Refreshing all system data...');
  const activePage = document.querySelector('.page.active');
  if (activePage) {
    const name = activePage.id.replace('page-', '');
    showPage(name);
  } else {
    showPage('dashboard');
  }
  toast('Sistem verileri tazelendi ✓', 'success');
}

function showPage(name) {
  console.log('Switching to page:', name);
  document.querySelectorAll('.page').forEach(p => {
    p.classList.remove('active');
    p.style.display = 'none'; // Force hide
  });
  const targetPage = document.getElementById('page-' + name);
  if (targetPage) {
    targetPage.classList.add('active');
    targetPage.style.display = 'block'; // Force show
  } else {
    console.error('Page not found:', 'page-' + name);
  }
  document.querySelectorAll('.nav-item').forEach(n => {
    n.classList.remove('active');
    // onclick="showPage('name')" formatından name'i çekmeye çalış
    const clickAttr = n.getAttribute('onclick');
    if (clickAttr && clickAttr.includes(`'${name}'`)) {
      n.classList.add('active');
    }
  });

  const labels = {
    dashboard: 'Dashboard', tasks: 'Görevler', agents: 'Ajan Birimleri', queue: 'İş Kuyruğu',
    monitoring: 'Sistem İzleme', telegram: 'Telegram', codegen: 'Kod Üretimi', logs: 'Sistem Kayıtları',
    'repair-center': 'Onarım Merkezi', 'repair-proposals': 'Onarım Teklifleri',
    'repair-metrics': 'Onarım Metrikleri', 'repair-policies': 'Politika Kuralları',
    'specialists': 'Uzman Kütüphanesi', debate: 'Münazara Motoru',
    'sandbox': 'Sandbox Çalıştırıcı', 'model-router': 'Model Yönlendirici',
    'vector-lessons': 'Vektör Belleği', ceo: 'CEO Denetimi',
    'self-update': 'Öz-Güncelleme', improvement: 'Sistem İyileştirme',
    'approvals': 'Onay Bekleyenler', 'admin': 'Yönetici Paneli',
    'finance': 'Maliyet Kontrolü'
  };
  document.getElementById('page-title').textContent = labels[name] || name;
  document.getElementById('page-sub').textContent = 'Son güncelleme: ' + new Date().toLocaleTimeString('tr-TR');

  switch (name) {
    case 'dashboard': loadDashboard().catch(err => toast('Dashboard yüklenemedi: ' + err.message, 'error')); break;
    case 'tasks': loadTasks().catch(err => toast('Görevler yüklenemedi: ' + err.message, 'error')); break;
    case 'agents': loadAgents().catch(err => toast('Ajanlar yüklenemedi: ' + err.message, 'error')); break;
    case 'queue': loadQueue().catch(err => toast('Kuyruk yüklenemedi: ' + err.message, 'error')); break;
    case 'monitoring': loadMonitoring().catch(err => toast('Monitoring yüklenemedi: ' + err.message, 'error')); break;
    case 'telegram': loadTelegram().catch(err => toast('Telegram yüklenemedi: ' + err.message, 'error')); break;
    case 'codegen': { loadCodeHistory().catch(err => toast('Geçmiş yüklenemedi: ' + err.message, 'error')); loadTemplateInfo(); } break;
    case 'logs': initWS(); break;
    case 'repair-center': loadRepairCenter().catch(err => toast('Repair Center yüklenemedi: ' + err.message, 'error')); break;
    case 'repair-proposals': loadProposals().catch(err => toast('Proposals yüklenemedi: ' + err.message, 'error')); break;
    case 'repair-metrics': loadRepairMetrics().catch(err => toast('Metrics yüklenemedi: ' + err.message, 'error')); break;
    case 'repair-policies': loadPolicies().catch(err => toast('Policies yüklenemedi: ' + err.message, 'error')); break;
    case 'debate': loadDebatePage().catch(err => toast('Debate yüklenemedi: ' + err.message, 'error')); break;
    case 'sandbox': loadSandboxPage().catch(err => toast('Sandbox yüklenemedi: ' + err.message, 'error')); break;
    case 'model-router': loadModelRouterPage().catch(err => toast('Router yüklenemedi: ' + err.message, 'error')); break;
    case 'vector-lessons': loadVectorLessonsPage().catch(err => toast('Lessons yüklenemedi: ' + err.message, 'error')); break;
    case 'admin': loadAdminUsers().catch(err => toast('Admin paneli yüklenemedi: ' + err.message, 'error')); break;
    case 'specialists': loadSpecialists().catch(err => toast('Uzmanlar yüklenemedi: ' + err.message, 'error')); break;
    case 'ceo': loadCEOFindings().catch(err => toast('CEO bulguları yüklenemedi: ' + err.message, 'error')); break;
    case 'self-update': loadSelfUpdateHistory().catch(err => toast('Güncelleme geçmişi yüklenemedi: ' + err.message, 'error')); break;
    case 'approvals': loadApprovals().catch(err => toast('Onaylar yüklenemedi: ' + err.message, 'error')); break;
    case 'finance': loadFinancePage().catch(err => toast('Finansal veriler yüklenemedi: ' + err.message, 'error')); break;
    case 'improvement': scanImprovements().catch(err => {
      console.error('Improvement page load failed', err);
      const el = safeGet('imp-opportunities-list');
      if (el) el.innerHTML = `<div class="loading" style="color:var(--red);">Yüklenemedi: ${err.message}</div>`;
      toast('İyileştirme taraması başarısız: ' + err.message, 'error');
    }); break;
  }
  
  // Dashboard Integrity Patch: Hide broken UI components if feature is disabled
  // ... future flag logic ...
}

function openModal(id) { document.getElementById(id).classList.add('open') }
function closeModal(id) { document.getElementById(id).classList.remove('open') }

function toast(msg, type = 'success') {
  const el = document.getElementById('toast');
  if (!el) return;
  el.textContent = msg; el.className = 'show ' + type;
  setTimeout(() => { el.className = '' }, 3000);
}
function showToast(msg, type = 'success') { toast(msg, type); }

const AUTH = {
  get token() { return null; },
  get email() { return sessionStorage.getItem('ai_email'); },
  get isAdmin() { return sessionStorage.getItem('ai_is_admin') === 'true'; },
  save(email, isAdmin) {
    sessionStorage.setItem('ai_email', email);
    sessionStorage.setItem('ai_is_admin', isAdmin);
  },
  clear() {
    sessionStorage.removeItem('ai_email');
    sessionStorage.removeItem('ai_is_admin');
  }
};

function authHeaders(extra = {}) {
  return { 'Content-Type': 'application/json', ...extra };
}

async function api(path, opts = {}) {
  const merged = {
    ...opts,
    headers: authHeaders(opts.headers || {}),
    credentials: 'include'
  };
  const controller = new AbortController();
  const requestTimeout = opts.timeout || 60000; // Default 60s
  const timeout = setTimeout(() => controller.abort(), requestTimeout); 
  try {
    const r = await fetch(API + path, { ...merged, signal: controller.signal });
    clearTimeout(timeout);

    if (r.status === 401) {
      AUTH.clear();
      if (path !== '/auth/me' && !path.includes('/auth/login')) location.reload();
      else showLogin();
      throw new Error('Oturum sona erdi');
    }
    
    if (r.status === 403) { throw new Error('Bu işlem için yetkiniz yok (Erişim Engellendi)'); }
    if (r.status === 503) { throw new Error('Sistem koruma modunda (Sağlık Skoru Düşük). Lütfen 30 saniye bekleyin.'); }
    
    if (!r.ok) {
      const errorText = await r.text();
      let errorMsg = `HTTP ${r.status}`;
      try {
        const errJson = JSON.parse(errorText);
        errorMsg = errJson.detail || errJson.message || errorMsg;
      } catch (ex) { }
      throw new Error(errorMsg);
    }
    
    return r.json();
  } catch (e) {
    clearTimeout(timeout);
    if (e.name === 'AbortError') throw new Error(`İstek zaman aşımına uğradı (${Math.round(requestTimeout/1000)}s)`);
    if (e.message && e.message.includes('Failed to fetch')) {
      throw new Error('Backend bağlantısı kurulamadı. Sunucu kapalı veya internet erişimi yok.');
    }
    throw e;
  }
}

async function doLogin() {
  const email = document.getElementById('login-email').value.trim();
  const pass = document.getElementById('login-pass').value;
  const errEl = document.getElementById('login-error');
  errEl.style.display = 'none';

  const btn = document.getElementById('login-btn');
  const btnText = btn.innerHTML;

  if (window.location.protocol === 'file:') {
    errEl.textContent = 'Hata: Dashboard doğrudan dosya olarak açılmış. Lütfen sunucu üzerinden erişiniz.';
    errEl.style.display = 'block';
    return;
  }

  // Loading state
  btn.disabled = true;
  btn.classList.add('btn-loading');
  btn.innerHTML = '<div class="spinner-sm"></div> <span>İşleniyor...</span>';

  try {
    const r = await fetch(API + '/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password: pass }),
      credentials: 'include'
    });

    if (!r.ok) {
      const t = await r.text();
      let msg = t;
      try { msg = JSON.parse(t).detail || t; } catch (e) { }
      throw new Error(msg);
    }

    const data = await r.json();
    AUTH.save(email, data.is_admin);
    document.getElementById('modal-login').classList.remove('open');
    checkAuth();
    showPage('dashboard');
    toast('Giriş başarılı ✓');
  } catch (e) {
    let msg = e.message || e;
    if (msg.includes('Failed to fetch')) msg = 'Sunucuya bağlanılamadı.';
    errEl.textContent = 'Hata: ' + msg;
    errEl.style.display = 'block';
  } finally {
    btn.disabled = false;
    btn.classList.remove('btn-loading');
    btn.innerHTML = btnText;
  }
}

async function logout() {
  try { await api('/auth/logout', { method: 'POST' }); } catch (e) { console.warn(e); }
  AUTH.clear();
  document.getElementById('user-info').style.display = 'none';
  showLogin();
}

function toggleAuthMode() {
  const isLogin = document.getElementById('auth-title').textContent === 'Giriş Yap';
  document.getElementById('auth-title').textContent = isLogin ? 'Kayıt Ol' : 'Giriş Yap';
  document.getElementById('login-btn').querySelector('span').textContent = isLogin ? 'Hesap Oluştur' : 'Giriş Yap';
  document.getElementById('toggle-auth-btn').innerHTML = isLogin ? 
    'Zaten hesabınız var mı? <span style="color:var(--primary); font-weight:700; margin-left:4px;">Giriş Yap</span>' : 
    'Hesabınız yok mu? <span style="color:var(--primary); font-weight:700; margin-left:4px;">Kayıt Ol</span>';
  document.getElementById('login-error').style.display = 'none';
}

async function doRegister() {
  const email = document.getElementById('login-email').value.trim();
  const pass = document.getElementById('login-pass').value;
  const errEl = document.getElementById('login-error');
  errEl.style.display = 'none';

  if (!email || !pass) { errEl.textContent = 'E-posta ve parola gerekli'; errEl.style.display = 'block'; return; }

  const btn = document.getElementById('login-btn');
  const btnText = btn.innerHTML;
  btn.disabled = true;
  btn.classList.add('btn-loading');
  btn.innerHTML = '<div class="spinner-sm"></div> <span>Hesap Oluşturuluyor...</span>';

  try {
    const r = await fetch(API + '/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password: pass })
    });
    if (!r.ok) { const t = await r.text(); throw new Error(t); }
    toast('Kayıt başarılı! Giriş yapılıyor…');
    await doLogin();
  } catch (e) { 
    errEl.textContent = 'Hata: ' + (e.message || e); 
    errEl.style.display = 'block'; 
  } finally {
    btn.disabled = false;
    btn.classList.remove('btn-loading');
    btn.innerHTML = btnText;
  }
}

function handleAuthAction() {
    // Robust check for login vs register
    const titleText = document.getElementById('auth-title').textContent;
    const isLogin = titleText.includes('Giriş');
  if (isLogin) doLogin(); else doRegister();
}

function showLogin() { document.getElementById('modal-login').classList.add('open'); }

function checkAuth() {
  if (!AUTH.email) {
    document.getElementById('user-info').style.display = 'none';
    const authBtn = document.getElementById('sidebar-auth-btn');
    if (authBtn) authBtn.style.display = 'block';
    const navAdmin = document.getElementById('nav-admin');
    if (navAdmin) navAdmin.style.display = 'none';
    showLogin();
    return false;
  }
  document.getElementById('sidebar-auth-btn').style.display = 'none';
  document.getElementById('user-info').style.display = 'block';
  document.getElementById('user-email').textContent = AUTH.email;
  // Ensure login modal is closed if it was opened during check
  const loginModal = document.getElementById('modal-login');
  if (loginModal) loginModal.classList.remove('open');
  
  const adminBadge = document.getElementById('admin-badge');
  if (adminBadge) adminBadge.style.display = AUTH.isAdmin ? 'inline-block' : 'none';
  const navAdmin = document.getElementById('nav-admin');
  if (navAdmin) navAdmin.style.display = AUTH.isAdmin ? 'block' : 'none';
  initWS();
  return true;
}

async function loadDashboard() {
  try {
    const s = await api('/tasks/stats/summary');
    // Map stats to UI elements, including cost and partial_complete
    ['total', 'pending', 'queued', 'running', 'pending_approval', 'completed', 'partial_complete', 'error', 'cost', 'paused'].forEach(key => {
      const id = key === 'partial_complete' ? 's-partial' : 's-' + key;
      let val = s[key] ?? s[key.replace('_complete', '')] ?? '—';
      if (key === 'cost' && typeof val === 'number') val = '$' + val.toFixed(2);
      safeSetText(id, val);
    });
    
    // Update badge in sidebar with Honest UI logic
    const badgePending = safeGet('badge-pending');
    if (badgePending) {
        const pCount = s.pending ?? 0;
        badgePending.textContent = pCount;
        badgePending.style.display = pCount > 0 ? 'inline-block' : 'none';
        if (s.is_fallback) {
           badgePending.title = 'Veri in-memory memory (DB bypass)';
           badgePending.style.border = '1px dashed var(--yellow)';
        } else {
           badgePending.title = 'Real-time database count';
           badgePending.style.border = '';
        }
    }
  } catch (e) { 
    console.error('Stats load failed:', e);
    // Silent fail for stats is better than crash, but show '—'
    ['total', 'pending', 'running', 'completed', 's-partial', 'error'].forEach(id => {
       const el = safeGet('s-' + id) || safeGet(id);
       if (el && el.textContent === '...') el.textContent = '—';
    });
  }

  try {
    const apprRes = await api('/approvals/pending');
    const apprs = Array.isArray(apprRes) ? apprRes : [];
    const badge = document.getElementById('badge-approvals');
    if (badge) {
      const count = apprs.length || 0;
      badge.textContent = count;
      badge.style.display = count > 0 ? 'inline-block' : 'none';
    }
  } catch (e) { console.warn('Approvals fetch failed', e); }

  try {
    const ov = await api('/monitoring/overview');
    const svc = ov.services || {};
    const pillsEl = document.getElementById('service-pills');
    if (pillsEl) {
      pillsEl.innerHTML = Object.entries(svc).map(([n, i]) => {
        const st = i.status === 'online' ? 'online' : (i.status === 'not_configured' ? 'neutral' : (i.status === 'offline' ? 'offline' : 'warn'));
        const label = i.status === 'not_configured' ? n + ' (N/A)' : n;
        return `<span class="service-pill ${st}" title="${i.error || ''}"><span class="service-dot"></span>${label}</span>`;
      }).join('') || '<span style="color:var(--muted);font-size:11px;">Aktif servis yok</span>';
    }
    // Map health score (Computed vs Agent fallback)
    const hs = ov.metrics?.system_score ?? ov.agents?.system_score;
    const hsLabel = document.getElementById('health-score-label');
    if (hsLabel && hs != null) {
      const p = typeof hs === 'number' ? Math.round(hs) : 0;
      hsLabel.textContent = p + '%';
      hsLabel.style.color = p > 80 ? 'var(--green)' : p > 50 ? 'var(--yellow)' : 'var(--red)';
    }
    const qSummary = document.getElementById('queue-summary');
    if (qSummary) {
      const q = ov.queue || {};
      const keys = [['queue_size', 'Bekleyen'], ['running', 'Çalışan'], ['completed', 'Tamamlanan'], ['error', 'Hatalı'], ['total', 'Toplam']];
      qSummary.innerHTML = keys.map(([k, label]) => `<div style="display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid var(--border);"><span style="color:var(--muted);">${label}</span><span>${q[k] ?? 0}</span></div>`).join('');
    }
    if (ov.metrics?.uptime_hms) {
      const uptimeEl = document.getElementById('sidebar-uptime');
      if (uptimeEl) uptimeEl.textContent = ov.metrics.uptime_hms;
    }

    // Update global capabilities from queue stats
    const qState = ov.queue || {};
    CAPS.supports_cancel = qState.supports_cancel ?? false;
    CAPS.supports_pause = qState.supports_pause ?? false;
    CAPS.supports_resume = qState.supports_resume ?? false;

    // Confirm with explicit endpoint
    try {
      const caps = await api('/tasks/capabilities');
      CAPS.supports_cancel = caps.supports_cancel ?? CAPS.supports_cancel;
      CAPS.supports_pause = caps.supports_pause ?? CAPS.supports_pause;
      CAPS.supports_resume = caps.supports_resume ?? CAPS.supports_resume;
    } catch (e) { console.warn('/tasks/capabilities fetch failed'); }

    applyCapabilityVisibility();

    // Faz 12.1 Integrity Patch: Render capability status
    if (ov.integrity) {
      renderIntegrityStatus(ov.integrity);
    }
  } catch (e) { }

  try {
    const d = await api('/tasks?limit=8');
    const tasks = d.tasks || [];
    const recentEl = document.getElementById('recent-tasks');
    if (recentEl) {
      recentEl.innerHTML = tasks.length ? tasks.map(t => `
        <div style="display:flex;align-items:center;gap:8px;padding:8px 0;border-bottom:1px solid rgba(26,34,48,.5);cursor:pointer;" onclick="openTaskDetail('${t.id}')">
          <span class="badge badge-${t.status}" style="width:60px;text-align:center;">${t.status}</span>
          <span style="flex:1;font-size:11px;font-family:var(--mono);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${t.title}</span>
          <span class="badge badge-${t.priority}">${t.priority}</span>
        </div>
      `).join('') : '<div style="color:var(--muted);font-size:11px;padding:12px 0;">Henüz görev yok</div>';
    }
  } catch (e) { }

  try {
    const h = await api('/health');
    const dot = document.getElementById('sidebar-status-dot');
    const txt = document.getElementById('sidebar-status-text');
    const alertBar = document.getElementById('memory-leak-alert');
    if (dot && txt) {
      const isDegraded = h.status === 'degraded';
      const isLeak = isDegraded && h.reason === 'memory_leak';
      
      dot.style.background = isDegraded ? 'var(--yellow)' : 'var(--green)';
      dot.style.animation = isDegraded ? 'pulseRed 2s infinite' : 'pulse 2s infinite';
      
      txt.textContent = isLeak ? 'Bellek Sızıntısı!' : (isDegraded ? 'Sistem Degraded' : 'Sistem Aktif');
      txt.style.color = isDegraded ? (isLeak ? 'var(--red)' : 'var(--yellow)') : '';
      
      if (alertBar) {
        alertBar.style.display = isLeak ? 'block' : 'none';
      }
    }
  } catch (e) { 
    const txt = document.getElementById('sidebar-status-text');
    if (txt) txt.textContent = 'Bağlantı Yok';
  }

  try {
    const sysH = await api('/system/health');
    const wBadge = document.getElementById('health-worker-badge');
    const tBadge = document.getElementById('health-tg-badge');
    
    if (wBadge) {
      const status = sysH.celery_workers?.status;
      if (status === 'UP') {
        wBadge.textContent = 'ONLINE';
        wBadge.className = 'badge badge-completed';
      } else if (status === 'NOT_CONFIGURED') {
        wBadge.textContent = 'N/A';
        wBadge.className = 'badge badge-neutral';
        wBadge.title = 'Queue backend in-process modunda';
      } else {
        wBadge.textContent = 'OFFLINE';
        wBadge.className = 'badge badge-error';
      }
    }
    if (tBadge) {
      const status = sysH.telegram_bot?.status;
      if (status === 'UP') {
        tBadge.textContent = 'AKTİF (' + new Date().toLocaleTimeString().slice(0,5) + ')';
        tBadge.className = 'badge badge-completed';
      } else if (status === 'NOT_CONFIGURED') {
        tBadge.textContent = 'DEV_ONLY';
        tBadge.className = 'badge badge-neutral';
        tBadge.title = 'Telegram bot token konfigüre edilmedi';
      } else {
        tBadge.textContent = 'TEPKİ YOK';
        tBadge.className = 'badge badge-error';
      }
    }
  } catch(e) { console.warn('/system/health', e); }

  // Akıllı Bütçe Takibi (Rota 2)
  if (typeof loadBudgetStatus === 'function') {
    loadBudgetStatus().catch(e => console.warn('Budget status fetch error', e));
  }
}

async function loadTasks() {
  try {
    const p = new URLSearchParams({ limit: 100 });
    ['status', 'priority', 'source'].forEach(k => {
      const val = document.getElementById('task-filter-' + k)?.value;
      if (val) p.append(k, val);
    });
    const se = document.getElementById('task-search')?.value;
    if (se) p.append('search', se);
    const data = await api('/tasks?' + p);
    const tasks = data.tasks || [];
    document.getElementById('task-count').textContent = (data.total ?? tasks.length) + ' görev';
    if (!tasks.length) { document.getElementById('task-table').innerHTML = '<div class="loading">Görev bulunamadı</div>'; return; }
    const statusLabels = {
      'pending': 'Bekliyor',
      'queued': 'Kuyrukta',
      'running': 'Çalışıyor',
      'pending_approval': 'Onay Bekliyor',
      'completed': 'Tamamlandı',
      'partial_complete': 'Kısmi Başarı',
      'error': 'Hatalı',
      'cancelled': 'İptal Edildi',
      'paused': 'Duraklatıldı'
    };
    document.getElementById('task-table').innerHTML = `<table><thead><tr><th>ID</th><th>Başlık</th><th>Durum</th><th>Öncelik</th><th>Kaynak</th><th>İlerleme</th><th>Tarih</th><th>İşlem</th></tr></thead><tbody>${tasks.map(t => `<tr onclick="openTaskDetail('${t.id}')" style="cursor:pointer;"><td style="color:var(--muted);">${t.id.substring(0, 8)}</td><td style="max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="${t.title}">${t.title}</td><td><span class="badge badge-${t.status}">${statusLabels[t.status] || t.status}</span></td><td><span class="badge badge-${t.priority}">${t.priority}</span></td><td style="color:var(--muted);">${t.source}</td><td style="min-width:80px;"><div class="progress-bar"><div class="progress-fill" style="width:${t.progress_pct || 0}%"></div></div><span style="font-size:9px;color:var(--muted);">${t.progress_pct || 0}%</span></td><td style="color:var(--muted);">${t.created_at ? new Date(t.created_at).toLocaleDateString('tr-TR') : '—'}</td><td onclick="event.stopPropagation();"><div style="display:flex;gap:4px;">
      ${t.status === 'error' ? `<button type="button" class="btn btn-ghost btn-sm" style="color:var(--green);" onclick="retryTask('${t.id}')" title="Yeniden Dene">↻</button>` : ''}
      ${(t.status === 'running' && CAPS.supports_pause) ? `<button type="button" class="btn btn-ghost btn-sm" style="color:var(--yellow);" onclick="pauseTask('${t.id}')" title="Duraklat">⏸</button>` : ''}
      ${(t.status === 'paused' && CAPS.supports_resume) ? `<button type="button" class="btn btn-ghost btn-sm" style="color:var(--green);" onclick="resumeTask('${t.id}')" title="Devam Ettir">▶</button>` : ''}
      ${(['pending', 'queued', 'running', 'paused', 'pending_approval'].includes(t.status) && CAPS.supports_cancel) ? `<button type="button" class="btn btn-ghost btn-sm" style="color:var(--orange);" onclick="cancelTask('${t.id}')" title="İptal Et">■</button>` : ''}
      <button type="button" class="btn btn-ghost btn-sm" onclick="copyTask('${t.id}')" title="Kopyala">⧉</button>
      <button type="button" class="btn btn-ghost btn-sm" style="color:var(--red);" onclick="deleteTask('${t.id}')" title="Sil">🗑</button>
    </div></td></tr>`).join('')}</tbody></table>`;
  } catch (e) { document.getElementById('task-table').innerHTML = `<div class="loading" style="color:var(--red);">Hata: ${e.message}</div>`; }
}

function agentEmoji(id) { return { architect: '🏛️', backend_dev: '⚙️', frontend_dev: '🎨', qa_engineer: '🧪', devops: '🚀', security: '🔒', data_eng: '🗄️', tech_writer: '📝' }[id] || '🤖'; }

async function openTaskDetail(id) {
  openModal('modal-detail');
  const contentEl = document.getElementById('modal-detail-content');
  contentEl.innerHTML = '<div class="loading">Sistem verileri çözümleniyor…</div>';
  try {
    const t = await api('/tasks/' + id);
    const subtasks = t.subtasks || []; 
    const logs = t.logs || [];
    const doneS = subtasks.filter(s => s.status === 'completed').length;
    
    // Markdown rendering for report
    let reportHtml = '';
    if (t.report && t.report.trim()) {
      try {
        if (typeof marked !== 'undefined') {
          // Supporting both marked.parse(text) and marked(text)
          if (typeof marked.parse === 'function') {
            reportHtml = marked.parse(t.report);
          } else {
            reportHtml = marked(t.report);
          }
        } else {
          reportHtml = `<div style="white-space:pre-wrap;">${t.report}</div>`;
        }
      } catch (e) {
        console.error('Markdown parse error:', e);
        reportHtml = `<div style="white-space:pre-wrap;">${t.report}</div>`;
      }
    }

    contentEl.innerHTML = `
      <div class="task-detail-header" style="margin-bottom:20px;">
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">
          <span class="badge badge-${t.status}">${t.status === 'partial_complete' ? 'Part. Succ.' : t.status}</span>
          <span class="badge badge-${t.priority}">${t.priority}</span>
          <span style="font-size:12px;color:var(--muted);font-family:var(--mono);">${t.source}</span>
        </div>
        <h2 style="font-size:24px;font-weight:800;margin:10px 0;color:#fff;font-family:var(--header-font);line-height:1.2;">${t.title}</h2>
      </div>

      <div class="task-meta-grid" style="display:grid;grid-template-columns:repeat(auto-fit, minmax(140px, 1fr));gap:12px;margin-bottom:24px;padding:16px;background:rgba(255,255,255,0.02);border-radius:12px;border:1px solid var(--border);">
        <div class="meta-item"><div class="meta-label" style="font-size:9px;color:var(--muted);text-transform:uppercase;letter-spacing:0.05em;">GÖREV ID</div><div class="meta-value" style="font-family:var(--mono);font-size:12px;color:var(--primary);">${t.id.substring(0, 16)}</div></div>
        <div class="meta-item"><div class="meta-label" style="font-size:9px;color:var(--muted);text-transform:uppercase;letter-spacing:0.05em;">İLERLEME</div><div class="meta-value" style="font-weight:700;">${t.progress_pct || 0}%</div></div>
        <div class="meta-item"><div class="meta-label" style="font-size:9px;color:var(--muted);text-transform:uppercase;letter-spacing:0.05em;">MALİYET</div><div class="meta-value" style="color:var(--green);font-weight:700;">$${(t.total_cost || 0).toFixed(4)}</div></div>
        <div class="meta-item"><div class="meta-label" style="font-size:9px;color:var(--muted);text-transform:uppercase;letter-spacing:0.05em;">TARİH</div><div class="meta-value" style="font-size:12px;color:var(--text2);">${t.created_at ? new Date(t.created_at).toLocaleDateString('tr-TR') : '—'}</div></div>
        <div class="meta-item"><div class="meta-label" style="font-size:9px;color:var(--orange);text-transform:uppercase;letter-spacing:0.05em;">İŞ AKIŞI</div><div class="meta-value" style="font-size:12px;text-transform:capitalize;">${t.workflow_template || 'default'}</div></div>
        <div class="meta-item"><div class="meta-label" style="font-size:9px;color:var(--cyan);text-transform:uppercase;letter-spacing:0.05em;">KALİTE PROFİLİ</div><div class="meta-value" style="font-size:12px;text-transform:capitalize;">${t.quality_profile || 'standard'}</div></div>
      </div>

      <!-- AGI MISSION CONTROL: BİLİŞSEL ÇEKİRDEK VERİLERİ -->
      ${t.agi_metadata ? `
      <div class="agi-mission-control" style="margin-bottom:32px; padding:20px; background:linear-gradient(135deg, rgba(14,165,233,0.05) 0%, rgba(139,92,246,0.05) 100%); border:1px solid rgba(14,165,233,0.2); border-radius:16px; box-shadow:0 8px 32px rgba(0,0,0,0.2); position:relative; overflow:hidden;">
        <div style="position:absolute; top:0; right:0; width:100px; height:100px; background:radial-gradient(circle, rgba(14,165,233,0.1) 0%, transparent 70%); pointer-events:none;"></div>
        
        <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:16px;">
          <div>
            <div style="font-size:10px; font-weight:800; color:var(--accent); text-transform:uppercase; letter-spacing:0.1em; margin-bottom:4px;">Bilişsel Çekirdek (Cognitive Core)</div>
            <h3 style="font-size:18px; font-weight:800; color:#fff; margin:0;">Misyon Analizi</h3>
          </div>
          <div style="text-align:right;">
             <div style="font-size:10px; color:var(--muted); margin-bottom:4px;">Reality Score</div>
             <div style="font-size:24px; font-weight:900; color:${t.agi_metadata.verification?.reality_score >= 0.8 ? 'var(--green)' : 'var(--yellow)'}; font-family:var(--header-font);">
               ${((t.agi_metadata.verification?.reality_score || 0) * 100).toFixed(0)}%
             </div>
          </div>
        </div>

        <div class="agi-grid" style="display:grid; grid-template-columns: 1fr 1fr; gap:16px;">
          <div class="agi-card-mini" style="background:rgba(0,0,0,0.2); padding:12px; border-radius:10px; border-left:3px solid var(--accent);">
            <div style="font-size:9px; color:var(--muted); margin-bottom:4px;">PROBLEM ÇERÇEVESİ</div>
            <div style="font-size:12px; color:var(--text); font-weight:600;">${t.agi_metadata.frame?.objective || 'Tanımlanmadı'}</div>
            <div style="font-size:10px; color:var(--muted); margin-top:4px;">Risk Seviyesi: <span style="color:${t.agi_metadata.frame?.risk_level === 'critical' ? 'var(--red)' : 'var(--yellow)'}">${t.agi_metadata.frame?.risk_level || 'N/A'}</span></div>
          </div>
          <div class="agi-card-mini" style="background:rgba(0,0,0,0.2); padding:12px; border-radius:10px; border-left:3px solid var(--purple);">
            <div style="font-size:9px; color:var(--muted); margin-bottom:4px;">DENETİM ÖZETİ</div>
            <div style="font-size:11px; color:var(--text2); line-height:1.4;">${t.agi_metadata.verification?.summary || 'Denetim raporu bekleniyor...'}</div>
          </div>
        </div>

        <div style="margin-top:16px; padding:10px; background:rgba(255,255,255,0.02); border-radius:8px; font-family:var(--mono); font-size:10px; color:var(--muted);">
          <span style="color:var(--accent);">[LEARNING]</span> Episode ID: ${t.agi_metadata.episode_id || 'N/A'} | Strateji: ${t.agi_metadata.plan?.strategy_id || 'Otonom'}
        </div>
      </div>
      ` : ''}

      ${t.error_detail ? `<div style="background:rgba(239,68,68,.07);border:1px solid rgba(239,68,68,.2);border-radius:12px;padding:16px;margin-bottom:24px;font-family:var(--mono);font-size:13px;color:var(--red);"><div style="font-weight:800;margin-bottom:4px;">❌ HATA DETAYI</div>${t.error_detail}</div>` : ''}
      
      ${reportHtml ? `
        <div class="task-result-section" style="margin-bottom:32px;">
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;">
            <div style="width:24px;height:24px;background:var(--green);border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:12px;box-shadow:0 0 10px rgba(16,185,129,0.3);">✓</div>
            <div style="font-size:14px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:var(--green);font-family:var(--header-font);">Görev Sonuç Raporu</div>
          </div>
          <div class="task-result-box markdown-content">
            ${reportHtml}
          </div>
        </div>
      ` : ''}

      ${subtasks.length ? `
        <div style="margin-bottom:32px;">
          <div class="card-title" style="margin-bottom:12px;display:flex;align-items:center;gap:8px;font-size:14px;">
            <span>🤖 Alt Görev Dağılımı</span>
            <span style="font-size:11px;color:var(--muted);font-weight:400;">(${doneS}/${subtasks.length} tamamlandı)</span>
          </div>
          <div style="display:flex;flex-direction:column;gap:8px;">
            ${subtasks.map(s => `
              <div class="subtask-row" style="display:flex;flex-direction:column;gap:8px;padding:12px;background:rgba(255,255,255,0.02);border:1px solid var(--border);border-radius:10px;">
                <div style="display:flex;align-items:center;gap:12px;">
                  <span style="font-size:18px;">${agentEmoji(s.agent_id)}</span>
                  <span class="subtask-agent" style="flex:1;font-weight:600;font-size:13px;text-transform:capitalize;">${s.agent_id.replace(/_/g, ' ')}</span>
                  <div class="subtask-bar" style="width:120px;">
                    <div class="progress-bar" style="height:6px;background:rgba(255,255,255,0.05);">
                      <div class="progress-fill" style="width:${s.status === 'completed' ? 100 : s.status === 'running' ? 50 : 0}%;background:${s.status === 'completed' ? 'var(--green)' : s.status === 'error' ? 'var(--red)' : 'var(--accent)'};box-shadow:0 0 10px ${s.status === 'completed' ? 'rgba(16,185,129,0.3)' : 'rgba(14,165,233,0.3)'};"></div>
                    </div>
                  </div>
                  <span class="badge badge-${s.status}" style="min-width:70px;text-align:center;">${s.status}</span>
                </div>
                ${s.quality_score ? `
                <div style="display:flex;flex-wrap:wrap;align-items:center;gap:8px;font-size:11px;color:var(--muted);padding-left:30px;">
                  <span style="display:flex;align-items:center;gap:4px;">🎯 Kalite Skoru: <strong style="color:${s.quality_score >= 0.6 ? 'var(--green)' : 'var(--orange)'}">${(s.quality_score * 100).toFixed(0)}%</strong></span>
                  ${s.reviewed ? `<span class="badge" style="font-size:9px;background:var(--blue);color:#fff;">👀 Revize Edildi</span>` : ''}
                  ${s.review_notes && s.review_notes.length ? `<span style="font-size:10px;font-style:italic;">"${s.review_notes[s.review_notes.length-1].substring(0, 60)}..."</span>` : ''}
                </div>
                ` : ''}
              </div>
            `).join('')}
          </div>
        </div>
      ` : ''}

      ${logs.length ? `
        <div style="margin-top:32px;">
          <div class="card-title" style="margin-bottom:12px;font-size:14px;">📜 Operasyonel Loglar</div>
          <div style="background:#020617;border:1px solid var(--border);border-radius:12px;padding:12px;max-height:250px;overflow-y:auto;box-shadow:inset 0 0 20px rgba(0,0,0,0.5);">
            ${logs.slice(0, 20).map(l => `
              <div class="log-entry ${l.level}" style="font-family:var(--mono);font-size:11px;margin-bottom:4px;padding:4px 8px;border-left-width:3px;">
                <span class="log-time" style="color:var(--muted);margin-right:8px;">${l.created_at ? new Date(l.created_at).toLocaleTimeString('tr-TR') : ''}</span>
                <span style="color:var(--primary);margin-right:6px;font-weight:700;">[${l.event}]</span>
                <span style="color:#cbd5e1;">${l.message}</span>
              </div>
            `).join('')}
          </div>
        </div>
      ` : ''}

      <div id="skill-logs-container" style="margin-top:32px;">
        <div class="card-title" style="margin-bottom:12px;font-size:14px;display:flex;align-items:center;gap:8px;">
           <span style="color:var(--accent);">🧩 Zekâ / Beceri İzlenebilirliği</span>
           <span class="badge" style="font-size:9px;background:rgba(14,165,233,0.1);color:var(--accent);border:1px solid rgba(14,165,233,0.2);">SKILL LAYER</span>
        </div>
        <div id="skill-logs-content" style="background:rgba(255,255,255,0.02);border:1px solid var(--border);border-radius:12px;padding:16px;">
           <div class="loading" style="font-size:11px;padding:10px 0;">Beceri kullanımları taranıyor...</div>
        </div>
      </div>

      <div class="modal-actions" style="display:flex;gap:12px;margin-top:32px;padding-top:20px;border-top:1px solid var(--border);flex-wrap:wrap;">
        ${t.status === 'error' ? `<button type="button" class="btn btn-primary btn-sm" style="background:var(--green);box-shadow:0 4px 12px rgba(16,185,129,0.2);" onclick="retryTask('${t.id}');closeModal('modal-detail')">↻ Tekrar Dene</button>` : ''}
        ${(['pending', 'running', 'paused'].includes(t.status) && CAPS.supports_cancel) ? `<button type="button" class="btn btn-ghost btn-sm" style="color:var(--red);border-color:rgba(239,68,68,0.2);" onclick="cancelTask('${t.id}');closeModal('modal-detail')">■ Görevi Durdur</button>` : ''}
        <button type="button" class="btn btn-ghost btn-sm" onclick="copyTask('${t.id}')">⧉ Kopyala</button>
        <button type="button" class="btn btn-ghost btn-sm" style="margin-left:auto;color:var(--muted);" onclick="deleteTask('${t.id}')">🗑 Sil</button>
      </div>`;

    // Fetch skill logs asynchronously after basic render
    try {
       const sLogs = await api('/skills/logs?project_id=' + t.id);
       const scBox = document.getElementById('skill-logs-content');
       if (!sLogs || sLogs.length === 0) {
          scBox.innerHTML = '<div style="color:var(--muted);font-size:11px;text-align:center;padding:10px 0;">Bu görevde özel bir beceri kullanılmadı.</div>';
       } else {
          scBox.innerHTML = '<div style="display:flex;flex-direction:column;gap:8px;">' + sLogs.map(sl => `
             <div style="background:rgba(0,0,0,0.2);border-radius:8px;padding:12px;border-left:3px solid ${sl.success ? 'var(--green)' : 'var(--red)'};">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
                   <div style="display:flex;align-items:center;gap:8px;">
                      <span style="font-size:12px;font-weight:700;color:var(--text);font-family:var(--mono);">${sl.skill_id.toUpperCase().replace('_', ' ')}</span>
                      <span style="font-size:10px;color:var(--muted);">${sl.agent_id ? '(' + sl.agent_id + ')' : ''}</span>
                   </div>
                   <div style="font-size:10px;font-family:var(--mono);color:var(--muted);">
                      ${sl.duration_s ? sl.duration_s.toFixed(2) + 's' : ''}
                   </div>
                </div>
                <div style="font-size:11px;color:${sl.success ? 'var(--text2)' : 'var(--red)'};line-height:1.5;">${sl.summary}</div>
             </div>
          `).join('') + '</div>';
       }
    } catch(err) {
       console.warn("Skill logs couldn't be fetched:", err);
       document.getElementById('skill-logs-content').innerHTML = '<div style="color:var(--red);font-size:11px;">İzlenebilirlik verisi çekilemedi.</div>';
    }

  } catch (e) { contentEl.innerHTML = `<div style="padding:40px;text-align:center;color:var(--red);"><div style="font-size:40px;margin-bottom:20px;">⚠️</div><div>Hata oluştu: ${e.message}</div></div>`; }
}

async function submitCreateTask() {
  const btn = document.getElementById('btn-submit-task');
  const title = document.getElementById('f-title').value.trim();
  if (!title) return toast('Başlık gerekli', 'error');

  if (btn) { btn.disabled = true; btn.textContent = '⌛ Gönderiliyor...'; }

  try {
    let description = document.getElementById('f-desc').value.trim();
    const imageFile = document.getElementById('f-image')?.files[0];
    
    // 1. Dosya yükleme varsa önce onu yap
    if (imageFile) {
      const formData = new FormData();
      formData.append('file', imageFile);
      try {
        const uploadRes = await fetch(API + '/storage/upload', {
          method: 'POST',
          body: formData,
          credentials: 'include',
          // Note: Browser sets multipart boundary automatically
        });
        if (!uploadRes.ok) throw new Error('Fotoğraf yüklenemedi');
        const uploadData = await uploadRes.json();
        if (uploadData.url) {
          description += `\n\n![Ekli Görsel](${uploadData.url})`;
        }
      } catch (err) {
        if (btn) { btn.disabled = false; btn.textContent = '⚡ Görevi Başlat'; }
        return toast('Fotoğraf yükleme hatası: ' + err.message, 'error');
      }
    }

    const tagsValue = document.getElementById('f-tags')?.value || '';
    const tags = tagsValue.split(',').map(t => t.trim()).filter(t => t.length > 0);

    const payload = { 
      title, 
      description: description, 
      priority: document.getElementById('f-priority').value, 
      assigned_agent: document.getElementById('f-agent').value, 
      tags, 
      context: document.getElementById('f-context').value.trim(), 
      source: 'manual',
      workflow_template: document.getElementById('f-workflow')?.value || 'default',
      quality_profile: document.getElementById('f-quality-profile')?.value || 'standard'
    };
    
    // Add acceptance criteria if defined
    const criteriaStr = document.getElementById('f-criteria')?.value.trim();
    if (criteriaStr) {
        payload.acceptance_criteria = criteriaStr.split('\\n').filter(c => c.trim().length > 0);
    }
    
    const dl = document.getElementById('f-deadline').value;
    if (dl) payload.deadline = new Date(dl).toISOString();

    await api('/tasks', { method: 'POST', body: JSON.stringify(payload) });
    
    toast('Görev başarıyla oluşturuldu ✓');
    console.log('Task created successfully:', payload.title);
    closeModal('modal-create');
    
    // Form temizle
    ['f-title', 'f-desc', 'f-tags', 'f-context', 'f-image'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.value = '';
    });
    const preview = document.getElementById('f-image-preview');
    if (preview) { preview.innerHTML = ''; preview.style.display = 'none'; }
    
    loadTasks(); loadDashboard();
  } catch (e) { 
    console.error('Task submission failed:', e);
    // Detail check for FastAPI errors
    const msg = e.detail || e.message || 'Görev oluşturulamadı';
    toast('Hata: ' + msg, 'error'); 
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = '⚡ Görevi Başlat'; }
  }
}

async function retryTask(id) { try { await api('/tasks/' + id + '/retry', { method: 'POST' }); toast('↻ Yeniden başlatıldı'); loadTasks(); loadDashboard(); } catch (e) { toast('Hata: ' + e.message, 'error'); } }
async function pauseTask(id) { try { await api('/tasks/' + id + '/pause', { method: 'POST' }); toast('⏸ Duraklatıldı'); loadTasks(); loadDashboard(); } catch (e) { toast('Hata: ' + e.message, 'error'); } }
async function resumeTask(id) { try { await api('/tasks/' + id + '/resume', { method: 'POST' }); toast('▶ Devam ettiriliyor'); loadTasks(); loadDashboard(); } catch (e) { toast('Hata: ' + e.message, 'error'); } }
async function cancelTask(id) { if (!confirm('Görevi iptal etmek istediğinize emin misiniz?')) return; try { await api('/tasks/' + id + '/cancel', { method: 'POST', body: JSON.stringify({ cancelled_by: 'dashboard' }) }); toast('İptal edildi'); closeModal('modal-detail'); loadTasks(); loadDashboard(); } catch (e) { toast('Hata: ' + e.message, 'error'); } }
async function deleteTask(id) { if (!confirm('Bu görevi silmek istediğinize emin misiniz?')) return; try { await api('/tasks/' + id, { method: 'DELETE' }); toast('Görev silindi'); closeModal('modal-detail'); setTimeout(() => { loadTasks(); loadDashboard(); }, 100); } catch (e) { toast('Hata: ' + e.message, 'error'); } }
async function copyTask(id) { try { const r = await api('/tasks/' + id + '/copy', { method: 'POST', body: '{}' }); toast('Kopyalandı ✓'); loadTasks(); } catch (e) { toast('Hata: ' + e.message, 'error'); } }

async function loadAgents() {
  try {
    const d = await api('/monitoring/agents');
    const agents = d.agents || {};
    const scoreEl = document.getElementById('system-score');
    if (scoreEl) scoreEl.textContent = d.system_score != null ? Math.round(d.system_score * 100) + '%' : '—';
    
    const ec = { architect: '🏛️', backend_dev: '⚙️', frontend_dev: '🎨', qa_engineer: '🧪', devops: '🚀', security: '🔒', data_eng: '🗄️', tech_writer: '📝' };
    const sc = { healthy: 'var(--green)', degraded: 'var(--yellow)', recovering: 'var(--primary)', critical: 'var(--red)', backup: 'var(--orange)' };
    
    const cardsEl = document.getElementById('agent-cards');
    if (cardsEl) {
      cardsEl.innerHTML = Object.entries(agents).map(([id, a]) => `
        <div class="agent-card ${a.state === 'critical' ? 'danger-pulse' : ''}">
          <div class="agent-header">
            <div class="agent-emoji">${ec[id] || '🤖'}</div>
            <div class="agent-info">
              <div class="agent-name" style="display:flex; align-items:center; gap:6px;">
                 ${id.replace(/_/g, ' ')}
                 ${a.active_task ? '<span class="pulse-small" title="Görev Başında"></span>' : ''}
              </div>
              <div class="agent-state" style="color:${sc[a.state] || 'var(--muted)'}; font-size:10px; font-weight:700;">${(a.state || 'active').toUpperCase()}</div>
            </div>
          </div>
          <div class="progress-bar" style="width:100%;height:4px;margin:12px 0; background:rgba(255,255,255,0.05); border-radius:2px; overflow:hidden;">
            <div class="progress-fill" style="width:${Math.round((a.health_score || 1) * 100)}%;background:${sc[a.state] || 'var(--primary)'}; box-shadow:0 0 8px ${sc[a.state] || 'var(--primary)'}; opacity:0.8;"></div>
          </div>
          <div class="agent-stats" style="display:grid; grid-template-columns: 1fr 1fr; gap:8px;">
            <div class="agent-stat-item" style="background:rgba(255,255,255,0.02); padding:6px; border-radius:6px; text-align:center;">
              <span class="agent-stat-label" style="display:block; font-size:9px; color:var(--muted);">BAŞARI</span>
              <span class="agent-stat-value" style="font-weight:700; color:var(--green);">${a.success || 0}</span>
            </div>
            <div class="agent-stat-item" style="background:rgba(255,255,255,0.02); padding:6px; border-radius:6px; text-align:center;">
              <span class="agent-stat-label" style="display:block; font-size:9px; color:var(--muted);">HATA</span>
              <span class="agent-stat-value" style="font-weight:700; color:var(--red);">${a.failure || 0}</span>
            </div>
          </div>
          ${a.last_action ? `<div style="margin-top:10px; font-size:9px; color:var(--muted); font-style:italic; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">Son: ${a.last_action}</div>` : ''}
        </div>
      `).join('') || '<div class="loading">Sistemde aktif ajan bulunamadı.</div>';
    }

    const eventsEl = document.getElementById('heal-events');
    if (eventsEl) {
      const events = d.recent_events || [];
      eventsEl.innerHTML = events.length ? events.slice(0, 15).map(e => `
        <div class="activity-item">
          <div class="activity-dot ${e.severity || 'info'}"></div>
          <div style="flex:1;">
            <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
              <span style="font-size:10px;font-weight:700;color:var(--primary);text-transform:uppercase;">${e.type || 'EVENT'}</span>
              <span style="font-size:10px;color:var(--muted);">${e.timestamp ? new Date(e.timestamp).toLocaleTimeString('tr-TR') : ''}</span>
            </div>
            <div class="activity-msg">${e.message || ''}</div>
          </div>
        </div>
      `).join('') : '<div style="color:var(--muted);font-size:11px;padding:12px 0;">Olay kaydı yok.</div>';
    }
  } catch (e) { console.error('Agent load failed', e); }
}

async function loadQueue() {
  try {
    const d = await api('/monitoring/queue');
    const statsEl = document.getElementById('queue-stats');
    if (statsEl) {
      statsEl.innerHTML = [['total', 'Toplam', 'cyan'], ['queue_size', 'Bekleyen', 'yellow'], ['running', 'Çalışan', 'orange'], ['done', 'Tamamlanan', 'green'], ['failed', 'Hatalı', 'red']].map(([k, l, c]) => `
        <div class="stat-card ${c}">
          <div class="stat-label">${l}</div>
          <div class="stat-value">${d[k] ?? 0}</div>
        </div>
      `).join('');
    }
    const jobs = d.recent_jobs || [];
    const jobsEl = document.getElementById('queue-jobs');
    if (jobsEl) {
      jobsEl.innerHTML = jobs.length ? `<table><thead><tr><th>ID</th><th>Başlık</th><th>Durum</th><th>Deneme</th><th>Başlangıç</th><th>Bitiş</th></tr></thead><tbody>${jobs.map(j => `<tr><td style="color:var(--muted);">${j.id}</td><td>${j.title || j.type}</td><td><span class="badge badge-${j.status}">${j.status}</span></td><td style="color:var(--muted);">${j.attempts}</td><td style="color:var(--muted);">${j.started_at ? new Date(j.started_at).toLocaleTimeString('tr-TR') : '—'}</td><td style="color:var(--muted);">${j.completed_at ? new Date(j.completed_at).toLocaleTimeString('tr-TR') : '—'}</td></tr>`).join('')}</tbody></table>` : '<div class="loading">Kuyrukta iş yok</div>';
    }
  } catch (e) { }
}

async function loadMonitoring() {
  try {
    const a = await api('/monitoring/api/stats?hours=24');
    const statsEl = document.getElementById('monitoring-stats');
    if (statsEl) {
      statsEl.innerHTML = `
        <div class="stat-card cyan"><div class="stat-label">Toplam İstek</div><div class="stat-value">${a.total_requests || 0}</div></div>
        <div class="stat-card red"><div class="stat-label">Hata</div><div class="stat-value">${a.total_errors || 0}</div></div>
        <div class="stat-card yellow"><div class="stat-label">Hata %</div><div class="stat-value">${a.error_rate_pct || 0}%</div></div>
        <div class="stat-card green"><div class="stat-label">Yanıt Süresi</div><div class="stat-value">${a.avg_response_ms || 0}ms</div></div>
      `;
    }
    const ep = a.endpoints || [];
    const epEl = document.getElementById('endpoint-stats');
    if (epEl) {
      epEl.innerHTML = ep.length ? `<table><thead><tr><th>Endpoint</th><th>Metod</th><th>İstek</th><th>Hata</th><th>ms</th></tr></thead><tbody>${ep.slice(0, 15).map(e => `<tr><td style="font-size:10px;">${e.endpoint}</td><td>${e.method}</td><td>${e.total}</td><td>${e.errors}</td><td>${e.avg_ms}</td></tr>`).join('')}</tbody></table>` : '<div class="loading">API verisi yok</div>';
    }
  } catch (e) { }

  try {
    const l = await api('/monitoring/llm');
    const pr = l.providers || {};
    const llmEl = document.getElementById('llm-stats');
    if (llmEl) {
      llmEl.innerHTML = `
        <div style="margin-bottom:16px;font-family:var(--mono);font-size:11px;">
          <div style="display:flex;justify-content:space-between;margin-bottom:4px;"><span>Top. Çağrı</span><span>${l.total_llm_calls || 0}</span></div>
          <div style="display:flex;justify-content:space-between;"><span>Başarı %</span><span>${l.llm_success_rate || 0}%</span></div>
        </div>
        ${(l.circuit_status || []).map(cs => `
          <div style="background:rgba(255,255,255,0.02);padding:10px;margin-bottom:8px;border-radius:8px;border:1px solid ${cs.quarantined ? 'rgba(239,68,68,0.4)' : (cs.circuit === 'open' ? 'var(--yellow)' : 'var(--border)')};">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
              <span style="font-size:11px;font-weight:700;">${cs.name.toUpperCase()}</span>
              <span class="badge" style="font-size:8px; background:${cs.quarantined ? 'var(--red)' : (cs.circuit === 'open' ? 'var(--yellow)' : 'var(--green)')}; color:#fff;">
                ${cs.quarantined ? 'YASAKLI (BAN)' : cs.circuit.toUpperCase()}
              </span>
            </div>
            <div class="progress-bar" style="width:100%;height:4px;margin-bottom:6px;">
              <div class="progress-fill" style="width:${(cs.health_score * 100).toFixed(0)}%; background:${cs.health_score > 0.7 ? 'var(--green)' : 'var(--yellow)'};"></div>
            </div>
            <div style="display:flex;justify-content:space-between;font-size:9px;color:var(--muted);font-family:var(--mono);">
               <span>Sağlık: ${(cs.health_score * 100).toFixed(0)}%</span>
               <span>Başarı: ${cs.success}</span>
               <span>ms: ${cs.avg_latency_s.toFixed(2)}</span>
            </div>
          </div>
        `).join('')}
      `;
    }
  } catch (e) { }

  try {
    const s = await api('/monitoring/system');
    const resEl = document.getElementById('system-resources');
    if (resEl) {
      resEl.innerHTML = s.available ? `
        <div class="metric-hologram" style="display:grid;grid-template-columns:repeat(3,1fr);gap:16px;">
          <div class="agent-stat-item"><span class="agent-stat-label">CPU</span><span class="agent-stat-value">${s.cpu_pct}%</span></div>
          <div class="agent-stat-item"><span class="agent-stat-label">RAM</span><span class="agent-stat-value">${s.ram_used_gb}GB</span></div>
          <div class="agent-stat-item"><span class="agent-stat-label">DISK</span><span class="agent-stat-value">${s.disk_pct}%</span></div>
        </div>
      ` : '<div class="loading">Kaynak verisi alınamadı</div>';
    }
  } catch (e) { }
}

/**
 * Faz 12.1 Integrity Patch: Sistem bütünlüğünü analiz eder ve bildirim yönetir.
 * 'Honest UI' yaklaşımı için eksik bileşenleri kullanıcıya şeffafça sunar.
 */
function renderIntegrityStatus(data) {
  const missing = Object.entries(data).filter(([k, v]) => !v.status);
  const alertBar = safeGet('integrity-alert');
  
  if (missing.length > 0) {
    if (alertBar) {
      alertBar.style.display = 'block';
      alertBar.innerHTML = `⚠️ <b>Sistem Kısıtılı Mod:</b> ${missing.length} kritik bileşen (Onarım Pipeline vb.) şu an stub/pasif modda. <a href="#" onclick="showPage('repair-center')" style="color:#fff; text-decoration:underline; margin-left:8px;">Detayları Gör</a>`;
    }
  } else if (alertBar) {
    alertBar.style.display = 'none';
  }

  // Repair Center sayfasında detaylı tabloyu güncelle (Eğer o sayfadaysak)
  const integrityTable = safeGet('rc-integrity-table');
  if (integrityTable) {
    integrityTable.innerHTML = `
      <div style="font-size:11px; margin-top:20px; border:1px solid var(--border); border-radius:12px; overflow:hidden;">
        <div style="background:rgba(255,255,255,0.02); padding:10px 16px; font-weight:700; border-bottom:1px solid var(--border);">Sistem Bütünlük Matrisi</div>
        <table style="width:100%; font-size:11px; border-collapse:collapse;">
          <thead style="background:rgba(0,0,0,0.2);">
            <tr><th style="padding:8px; text-align:left;">Bileşen</th><th style="padding:8px; text-align:left;">Durum</th><th style="padding:8px; text-align:left;">Hata / Not</th></tr>
          </thead>
          <tbody>
            ${Object.entries(data).map(([k, v]) => `
              <tr style="border-top:1px solid var(--border);">
                <td style="padding:8px; font-family:var(--mono);">${k}</td>
                <td style="padding:8px;"><span class="badge badge-${v.status ? 'completed' : 'error'}" style="font-size:9px;">${v.status ? 'REAL' : 'STUB'}</span></td>
                <td style="padding:8px; color:var(--muted); font-size:10px;">${v.error || 'Aktif/Entegre'}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    `;
  }
}

async function loadTelegram() {
  try {
    const info = await api('/telegram/info');
    const infoEl = document.getElementById('telegram-info');
    if (infoEl) infoEl.innerHTML = info.configured ? `<div style="font-family:var(--mono);">Ağ Bağlantısı: @${info.bot?.username || 'bot'}</div>` : 'Yapılandırılmadı';
  } catch (e) { }
}

function initWS() {
  if (wsConn && wsConn.readyState === 1) return;
  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  wsConn = new WebSocket(`${proto}://${location.host}/ws/logs`);
  const statusEl = document.getElementById('ws-status');
  wsConn.onopen = () => { if (statusEl) statusEl.textContent = '● CANLI BAĞLANTI'; statusEl.style.color = 'var(--primary)'; };
  wsConn.onclose = () => { if (statusEl) statusEl.textContent = '○ KESİLDİ'; statusEl.style.color = 'var(--muted)'; setTimeout(initWS, 3000); };
  wsConn.onmessage = (e) => {
    try {
      const d = JSON.parse(e.data);
      if (d.event === 'live_patch') handleLivePatch(d);
      else if (d.event === 'approval.needed') { toast('⚠️ Onay Talebi Geldi', 'warning'); loadApprovals(); }
      else if (d.event === 'debate_state') { if (typeof handleDebateState === 'function') handleDebateState(d); }
      else if (d.event === 'job_progress') {
        const idShort = d.job_id ? d.job_id.substring(0, 8) : '...';
        toast(`🔨 Onarım: ${idShort} -> ${d.status}`, 'info');
        // Sayfa bazlı otomatik yenileme (Data Freshness)
        const activePage = document.querySelector('.page.active')?.id;
        if (activePage === 'page-repair-center') loadRepairCenter();
        if (activePage === 'page-dashboard') loadDashboard();
        if (activePage === 'page-tasks') loadTasks();
      }
      else { addLog(d); updateFeed(d); }
    } catch { }
  };
}

function addLog(evt) {
  const feed = document.getElementById('log-feed');
  if (!feed) return;
  if (feed.querySelector('.loading')) feed.innerHTML = '';
  const div = document.createElement('div');
  div.className = `log-entry ${evt.severity || 'info'}`;
  const tag = evt.agent_id ? `<span class="log-tag">[${evt.agent_id}]</span>` : '<span class="log-tag">[SYSTEM]</span>';
  div.innerHTML = `<span class="log-time">${new Date().toLocaleTimeString('tr-TR')}</span> ${tag} ${evt.message || evt.event || ''}`;
  feed.insertBefore(div, feed.firstChild);
  if (feed.children.length > 300) feed.removeChild(feed.lastChild);
}

function updateFeed(evt) {
  const feed = document.getElementById('activity-feed');
  if (!feed) return;
  if (feed.querySelector('.loading')) feed.innerHTML = '';
  const div = document.createElement('div');
  div.className = 'activity-item';
  div.innerHTML = `<span class="activity-dot info"></span><span class="activity-msg">${evt.message?.substring(0, 100) || ''}</span>`;
  feed.insertBefore(div, feed.firstChild);
  if (feed.children.length > 25) feed.removeChild(feed.lastChild);
}

async function loadFinancePage() {
  try {
    // 1. Status & Budget
    const s = await api('/finance/status');
    safeSetText('f-spent-formatted', s.spent_formatted || '—');
    safeSetText('f-budget-formatted', s.budget_formatted || '—');
    safeSetText('f-remaining-formatted', s.remaining_formatted || '—');
    safeSetText('f-usage-pct', (s.pct_used || 0).toFixed(1) + '%');
    
    const progressEl = safeGet('f-budget-progress');
    if (progressEl) progressEl.style.width = (s.pct_used > 100 ? 100 : s.pct_used) + '%';
    
    const warningEl = safeGet('f-threshold-warning');
    if (warningEl) warningEl.style.display = s.threshold_warning ? 'block' : 'none';

    // 2. Top Costly Tasks
    const top = await api('/finance/top-tasks?limit=5');
    const topEl = safeGet('f-top-tasks-list');
    if (topEl) {
      topEl.innerHTML = top.length ? `
        <table style="width:100%; font-size:12px; border-collapse:collapse;">
          <tbody>
            ${top.map(t => `
              <tr style="border-bottom:1px solid var(--border2);">
                <td style="padding:10px 0; color:var(--text1);">${t.title}</td>
                <td style="padding:10px 0; text-align:right; font-weight:700; color:var(--red);">$${t.cost.toFixed(4)}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      ` : '<div style="color:var(--muted); font-size:12px; padding:10px 0;">Harcama gerektiren görev bulunamadı.</div>';
    }

    // 3. History
    const history = await api('/finance/history?days=7');
    const histEl = safeGet('f-history-list');
    if (histEl) {
      histEl.innerHTML = history.length ? `
        <table style="width:100%; font-size:12px; border-collapse:collapse;">
          <thead style="color:var(--muted); font-size:11px;">
            <tr><th style="padding:10px 0; text-align:left;">Tarih</th><th style="padding:10px 0; text-align:center;">İstek</th><th style="padding:10px 0; text-align:right;">Maliyet</th></tr>
          </thead>
          <tbody>
            ${history.map(h => `
              <tr style="border-bottom:1px solid var(--border2);">
                <td style="padding:10px 0; color:var(--text2);">${new Date(h.date).toLocaleDateString('tr-TR')}</td>
                <td style="padding:10px 0; text-align:center; color:var(--text1); font-family:var(--mono);">${h.calls}</td>
                <td style="padding:10px 0; text-align:right; font-weight:600; color:var(--accent);">$${h.cost.toFixed(4)}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      ` : '<div style="color:var(--muted); font-size:12px; padding:10px 0;">Son 7 güne ait veri yok.</div>';
    }
  } catch (e) {
    console.error('Finance page load failed', e);
    toast('Maliyet verileri yüklenemedi: ' + e.message, 'error');
  }
}

let _loadedSpecialists = [];

async function loadSpecialists() {
  const el = document.getElementById('specialist-grid');
  if (!el) return;
  try {
    const data = await api('/specialists');
    _loadedSpecialists = data.specialists || [];
    el.innerHTML = _loadedSpecialists.map(s => `
      <div class="agent-card">
         <div class="agent-header">
           <div class="agent-emoji">${s.emoji || '📂'}</div>
           <div class="agent-info">
             <div class="agent-name">${s.name}</div>
             <div class="agent-state" style="color:var(--primary);">${s.role}</div>
           </div>
         </div>
         <p style="font-size:11px; color:var(--muted); line-height:1.4; margin-bottom:12px; height:32px; overflow:hidden; text-overflow:ellipsis;">${s.description}</p>
         <div class="agent-stats">
            <div class="agent-stat-item">
              <span class="agent-stat-label">Beceriler</span>
              <span class="agent-stat-value">${s.skills?.length || 0} Araç</span>
            </div>
            <div class="agent-stat-item" style="text-align:right; justify-content:center;">
              <button class="btn btn-ghost btn-sm" style="color:var(--primary); padding:0; height:auto;" onclick="copySpecialistPrompt('${s.id}')">Promt</button>
            </div>
         </div>
      </div>
    `).join('') || '<div style="padding:40px; text-align:center; color:var(--muted);">Kütüphanede kayıtlı uzman bulunamadı.</div>';
  } catch (e) {
    console.error(e);
    el.innerHTML = `<div class="loading" style="color:var(--red);">Yükleme Hatası: ${e.message}</div>`;
  }
}

async function copySpecialistPrompt(id) {
  const s = _loadedSpecialists.find(x => x.id === id);
  if (!s || !s.prompt) return toast('Promt bulunamadı!', 'error');
  try {
    await navigator.clipboard.writeText(s.prompt);
    toast('Promt kopyalandı!');
  } catch (err) {
    console.error('Copy failed', err);
    toast('Kopyalama başarısız!', 'error');
  }
}

// Image Preview Utility
function previewImage(input, previewId) {
  const preview = document.getElementById(previewId);
  if (!preview) return;
  const file = input.files[0];
  if (file && file.type.startsWith('image/')) {
    const reader = new FileReader();
    reader.onload = (e) => {
      preview.style.display = 'block';
      preview.innerHTML = `<img src="${e.target.result}" alt="Preview">`;
    };
    reader.readAsDataURL(file);
  } else {
    preview.style.display = 'none';
    preview.innerHTML = '';
  }
}

// --- Global Error Boundary for Dashboard ---
window.onerror = function(msg, url, line, col, error) {
  console.error('[Dashboard Error]', { msg, url, line, col, error });
  // Don't show toast for every error to avoid noise, but log it
};

// Global functions for nav item sync - MOVE TO TOP TO PREVENT ReferenceError
window.showPage = showPage;
window.previewImage = previewImage;
window.submitCreateTask = submitCreateTask;
window.toggleAuthMode = toggleAuthMode;
window.handleAuthAction = handleAuthAction;
window.openModal = openModal;
window.closeModal = closeModal;
window.logout = logout;
window.refreshAll = refreshAll;
window.loadQueue = loadQueue;
window.loadTasks = loadTasks;
window.loadDashboard = loadDashboard;
window.loadAgents = loadAgents;
window.loadMonitoring = loadMonitoring;
window.loadSpecialists = loadSpecialists;
window.copySpecialistPrompt = copySpecialistPrompt;
window.toast = toast;
window.showToast = showToast;
window.api = api;
window.openTaskDetail = openTaskDetail;

// --- Faz 12.1 Freshness & Heartbeat ---
let _lastSyncTime = new Date();

function updateFreshness() {
  const el = safeGet('freshness-label');
  if (!el) return;
  const now = new Date();
  const diff = Math.floor((now - _lastSyncTime) / 1000);
  
  if (diff < 15) {
    el.textContent = 'SYNC';
    el.parentElement.style.opacity = '1';
  } else if (diff < 60) {
    el.textContent = `${diff}s`;
    el.parentElement.style.opacity = '0.8';
  } else {
    el.textContent = 'STALE';
    el.parentElement.style.opacity = '0.5';
  }
}

// Intercept window.api to update sync time
const _originalApi = window.api;
window.api = async function(...args) {
  const res = await _originalApi(...args);
  _lastSyncTime = new Date();
  updateFreshness();
  return res;
};

// Initial state and loops
document.addEventListener('DOMContentLoaded', () => {
  checkAuth();
  setInterval(updateFreshness, 5000);
  setInterval(() => {
    if (document.visibilityState === 'visible') {
      const active = document.querySelector('.page.active');
      if (active && active.id === 'page-dashboard') loadDashboard();
    }
  }, 30000); // Background refresh every 30s
});

function applyCapabilityVisibility() {
  const cancelButtons = document.querySelectorAll('[data-action="cancel"]');
  const pauseButtons = document.querySelectorAll('[data-action="pause"]');
  const resumeButtons = document.querySelectorAll('[data-action="resume"]');

  cancelButtons.forEach(btn => {
    btn.style.display = CAPS.supports_cancel ? '' : 'none';
    btn.disabled = !CAPS.supports_cancel;
  });

  pauseButtons.forEach(btn => {
    btn.style.display = CAPS.supports_pause ? '' : 'none';
    btn.disabled = !CAPS.supports_pause;
  });

  resumeButtons.forEach(btn => {
    btn.style.display = CAPS.supports_resume ? '' : 'none';
    btn.disabled = !CAPS.supports_resume;
  });
}
