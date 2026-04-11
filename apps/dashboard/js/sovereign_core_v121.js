const API = '/api/v1';
let wsConn = null;

// Capability flags for dynamic UI (Phase 4/5)
let CAPS = {
  supports_cancel: false,
  supports_pause: false,
  supports_resume: false
};

async function loadBackups() {
  const container = safeGet('backup-list');
  if (!container) return;
  try {
    const list = await api('/monitoring/backups');
    if (!Array.isArray(list)) throw new Error('Yedek listesi formatı hatalı');
    
    if (list.length === 0) {
      container.innerHTML = '<div style="padding:20px; text-align:center; color:var(--muted); font-size:12px;">Aktif gölge yedek bulunmuyor.</div>';
      return;
    }

    container.innerHTML = `
      <table style="width:100%; font-size:11px;">
        <thead>
          <tr style="text-align:left; color:var(--muted); border-bottom:1px solid var(--border);">
            <th style="padding:8px;">Dosya</th>
            <th style="padding:8px;">Boyut</th>
            <th style="padding:8px;">Tarih</th>
          </tr>
        </thead>
        <tbody>
          ${list.map(b => `
            <tr style="border-bottom:1px solid rgba(255,255,255,0.02);">
              <td style="padding:8px; font-family:var(--mono); color:var(--accent);">${b.filename}</td>
              <td style="padding:8px; color:var(--muted);">${(b.size / 1024).toFixed(1)} KB</td>
              <td style="padding:8px; color:var(--text2);">${new Date(b.created_at).toLocaleString('tr-TR')}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;
  } catch (e) {
    container.innerHTML = `<div style="padding:20px; color:var(--red); font-size:11px;">Yedekler yüklenemedi: ${e.message}</div>`;
  }
}

// Unified UI Status Labels (Phase 12.1)
const STATUS_LABELS = {
  'pending': 'Bekliyor',
  'queued': 'Kuyrukta',
  'running': 'Çalışıyor',
  'pending_approval': 'Onay Bekliyor',
  'completed': 'Tamamlandı',
  'done': 'Başarılı',
  'partial_complete': 'Kısmi Başarı',
  'error': 'Hatalı',
  'failed': 'Hatalı',
  'cancelled': 'İptal Edildi',
  'paused': 'Duraklatıldı'
};

/**
 * DASHBOARD HONESTY & STABILITY GUARDS
 * Prevents "Silent Errors" and "False Positives" due to missing DOM elements.
 */
function safeGet(id) { 
  const el = document.getElementById(id);
  if (!el && !id.startsWith('badge-')) {
    console.debug(`[DOM Guard] Missing element: #${id}`);
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

function renderLoading(id) { 
  const el = safeGet(id); 
  if (el) el.innerHTML = '<div class="loading"><div class="spinner-sm"></div> Bilişsel veri senkronize ediliyor...</div>'; 
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
    // [RECOVERY] If page not found, go back to dashboard and notify
    if (name !== 'dashboard') {
      showToast(`'${name}' sayfası bulunamadı. Ana sayfaya dönülüyor.`, 'warning');
      showPage('dashboard');
    }
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
    'vector-lessons': 'Vektör Belleği', ceo: 'CEO Denetimi',
    'self-update': 'Öz-Güncelleme', improvement: 'Sistem İyileştirme',
    'approvals': 'Onay Bekleyenler', 'admin': 'Yönetici Paneli',
    'finance': 'Maliyet Kontrolü'
  };
  document.getElementById('page-title').textContent = labels[name] || name;
  document.getElementById('page-sub').textContent = 'Son güncelleme: ' + new Date().toLocaleTimeString('tr-TR');

  switch (name) {
    case 'dashboard': renderLoading('recent-tasks'); loadDashboard().catch(err => toast('Dashboard yüklenemedi: ' + err.message, 'error')); break;
    case 'tasks': 
    case 'jobs': renderLoading('task-table'); loadTasks().catch(err => toast('Görevler yüklenemedi: ' + err.message, 'error')); break;
    case 'agents': renderLoading('agent-cards'); loadAgents().catch(err => toast('Ajanlar yüklenemedi: ' + err.message, 'error')); break;
    case 'queue': renderLoading('queue-stats'); loadQueue().catch(err => toast('Kuyruk yüklenemedi: ' + err.message, 'error')); break;
    case 'monitoring': {
      renderLoading('monitoring-stats');
      loadMonitoring().catch(err => toast('Monitoring yüklenemedi: ' + err.message, 'error'));
      loadBackups().catch(err => console.warn('Backups load failed', err));
    } break;
    case 'telegram': loadTelegram().catch(err => toast('Telegram yüklenemedi: ' + err.message, 'error')); break;
    case 'codegen': { loadCodeHistory().catch(err => toast('Geçmiş yüklenemedi: ' + err.message, 'error')); loadTemplateInfo(); } break;
    case 'logs': initWS(); break;
    case 'repair-center': renderLoading('rc-incidents-table'); loadRepairCenter().catch(err => toast('Repair Center yüklenemedi: ' + err.message, 'error')); break;
    case 'repair-proposals': loadProposals().catch(err => toast('Proposals yüklenemedi: ' + err.message, 'error')); break;
    case 'repair-metrics': loadRepairMetrics().catch(err => toast('Metrics yüklenemedi: ' + err.message, 'error')); break;
    case 'repair-policies': loadPolicies().catch(err => toast('Policies yüklenemedi: ' + err.message, 'error')); break;
    case 'debate': loadDebatePage().catch(err => toast('Debate yüklenemedi: ' + err.message, 'error')); break;
    case 'sandbox': toast('Önizleme Aşamasında', 'info'); break;
    case 'model-router': loadModelRouterPage().catch(err => toast('Router yüklenemedi: ' + err.message, 'error')); break;
    case 'vector-lessons': loadVectorLessonsPage().catch(err => toast('Lessons yüklenemedi: ' + err.message, 'error')); break;
    case 'admin': loadAdminUsers().catch(err => toast('Admin paneli yüklenemedi: ' + err.message, 'error')); break;
    case 'specialists': 
    case 'skills': toast('Yetenekler Modülü Yakında Gelecek', 'info'); break;
    case 'ceo': renderLoading('ceo-findings-body'); loadCEOFindings().catch(err => toast('CEO bulguları yüklenemedi: ' + err.message, 'error')); break;
    case 'self-update': loadSelfUpdateHistory().catch(err => toast('Güncelleme geçmişi yüklenemedi: ' + err.message, 'error')); break;
    case 'approvals': renderLoading('approval-list'); loadApprovals().catch(err => toast('Onaylar yüklenemedi: ' + err.message, 'error')); break;
    case 'finance': loadFinancePage().catch(err => toast('Finansal veriler yüklenemedi: ' + err.message, 'error')); break;
    case 'architect': toast('Mimari Gözlemci Aktif Değil', 'warning'); break;
    case 'knowledge': toast('Bilgi Bankası Hazırlanıyor', 'info'); break;
    case 'runbooks': toast('Runbooklar Yükleniyor...', 'info'); break;
    case 'pacing': toast('Metabolik Kontrol: Normal', 'info'); break;
    case 'governance': toast('Öz-Yönetişim Aktif ve Denetliyor', 'success'); break;
    case 'improvement': renderLoading('imp-opportunities-list'); scanImprovements().catch(err => {
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
  el.textContent = msg; 
  el.className = 'show ' + type;
  setTimeout(() => { el.className = '' }, 3000);

  // Honest UI: Bildirimleri sistem günlüklerine de işle
  if (typeof addLog === 'function') {
    addLog({
      message: msg,
      severity: type === 'error' ? 'error' : (type === 'warning' ? 'warning' : 'info'),
      agent_id: 'DASHBOARD'
    });
  }
}
function showToast(msg, type = 'success') { toast(msg, type); }

const AUTH = {
  get token() { return sessionStorage.getItem('ai_token'); },
  get email() { return sessionStorage.getItem('ai_email'); },
  get isAdmin() { return sessionStorage.getItem('ai_is_admin') === 'true'; },
  save(email, isAdmin, token = null) {
    sessionStorage.setItem('ai_email', email);
    sessionStorage.setItem('ai_is_admin', isAdmin);
    if (token) sessionStorage.setItem('ai_token', token);
  },
  clear() {
    sessionStorage.removeItem('ai_email');
    sessionStorage.removeItem('ai_is_admin');
    sessionStorage.removeItem('ai_token');
  }
};

/* 
  Phase 56: Inactivity Guard System 
  Oturum aşımını (15m) takip eder, kullanıcı aktifken sessizce yeniler.
*/
const InactivityMonitor = {
  idleTime: 0,
  maxIdle: 13 * 60, // 13 dakika (15dk dolmadan 2dk önce uyarı)
  warningTime: 60,  // Uyarı süresi (saniye)
  interval: null,
  isWarning: false,

  init() {
    ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart'].forEach(evt => {
      document.addEventListener(evt, () => this.reset(), true);
    });
    this.start();
    console.info("[InactivityMonitor] Aktif.");
  },

  reset() {
    this.idleTime = 0;
    if (this.isWarning) {
      this.resume();
    }
  },

  start() {
    if (this.interval) clearInterval(this.interval);
    this.interval = setInterval(() => this.check(), 1000);
  },

  async check() {
    if (!AUTH.token) return;
    this.idleTime++;

    // Aktif Operasyon Kontrolü: Eğer çalışan bir görev varsa süreyi otomatik sıfırla ve oturumu yenile
    const runningTask = document.querySelector('.status-running') || document.querySelector('.badge-running');
    if (runningTask) {
      if (this.idleTime > 60) { // Her dakika bir yenileme yeterli
         await this.silentRefresh();
         this.idleTime = 0;
      }
      return;
    }

    if (this.idleTime >= this.maxIdle && !this.isWarning) {
      this.showWarning();
    }
  },

  showWarning() {
    this.isWarning = true;
    openModal('modal-inactivity');
    let remaining = this.warningTime;
    const countdownEl = document.getElementById('inactivity-countdown');
    
    this.warningInterval = setInterval(() => {
      remaining--;
      if (countdownEl) countdownEl.textContent = remaining;
      if (remaining <= 0) {
        clearInterval(this.warningInterval);
        logout();
      }
    }, 1000);
  },

  async resume() {
    clearInterval(this.warningInterval);
    this.isWarning = false;
    closeModal('modal-inactivity');
    this.idleTime = 0;
    await this.silentRefresh();
  },

  async silentRefresh() {
    try {
      console.log("[InactivityMonitor] Oturum tazeleniyor...");
      // Backend'deki yeni cookie tabanlı refresh endpoint'ini çağır
      await api('/auth/refresh', { method: 'POST', body: JSON.stringify({}) });
    } catch (e) {
      console.warn("Silent refresh failed:", e);
    }
  }
};

function authHeaders(extra = {}) {
  const h = { 'Content-Type': 'application/json', ...extra };
  if (AUTH.token) h['Authorization'] = `Bearer ${AUTH.token}`;
  return h;
}

async function api(path, opts = {}) {
  const merged = {
    ...opts,
    headers: authHeaders(opts.headers || {}),
    credentials: 'include'
  };
  const controller = new AbortController();
  const requestTimeout = opts.timeout || 60000; 
  const timeout = setTimeout(() => controller.abort(), requestTimeout); 
  
  try {
    const r = await fetch(API + path, { ...merged, signal: controller.signal });
    clearTimeout(timeout);
    
    // Recovery: If we get any successful response, hide degraded mode warnings
    if (r.ok) hideDegradedMode();

    if (r.status === 401) {
      // 401 Unauthorized: Oturum gerçekten düşmüşse temizle
      // Ancak InactivityMonitor tarafından tetiklenen bir 401 (refresh hatası) ise sessiz kal
      if (path === '/auth/refresh') throw new Error('Refresh failed');

      AUTH.clear();
      const isBackground = path.includes('/monitoring/') || path.includes('/stats') || path.includes('/health');
      
      if (!isBackground && path !== '/auth/me' && !path.includes('/auth/login')) {
         location.reload();
      } else {
         showLogin();
      }
      throw new Error('Oturum sona erdi');
    }
    
    if (r.status === 403) throw new Error('Erişim engellendi.');
    if (r.status === 503) {
      showDegradedMode('Sistem yoğun/kısıtlı modda. Lütfen bekleyin.');
      throw new Error('Sistem koruma modunda.');
    }
    
    // Critical Failure: 5xx
    if (r.status >= 500) {
      showDegradedMode(`Kritik Sunucu Hatası (HTTP ${r.status}). Sistem limitli modda.`);
    }
    
    if (!r.ok) {
      const errorText = await r.text();
      let errorMsg = `HTTP ${r.status}`;
      try {
        const errJson = JSON.parse(errorText);
        errorMsg = errJson.detail || errJson.message || errorMsg;
      } catch (ex) { }
      
      // Critical Audit: Log failed API calls to the UI for user visibility
      if (r.status >= 400 && r.status !== 401) {
        console.error(`[API-CRITICAL] Path: ${path} Status: ${r.status} Error: ${errorMsg}`);
        // Only show toast if not a background/silent request
        if (!path.includes('/monitoring/') && !path.includes('/health')) {
          showToast(`Sistem Hatası (${r.status}): ${errorMsg}`, 'error');
        }
      }
      
      throw new Error(errorMsg);
    }
    
    return r.json();
  } catch (e) {
    clearTimeout(timeout);
    if (e.name === 'AbortError') {
      showDegradedMode('Backend isteği zaman aşımına uğradı. Veriler gecikmeli gelebilir.');
      throw new Error(`Zaman aşımı (${Math.round(requestTimeout/1000)}s)`);
    }
    if (e.message && (e.message.includes('Failed to fetch') || e.message.includes('NetworkError'))) {
      showDegradedMode('Backend bağlantısı koptu. Sistem çevrimdışı.');
      throw new Error('Bağlantı hatası.');
    }
    throw e;
  }
}

function showDegradedMode(msg) {
  const el = document.getElementById('integrity-alert');
  if (el) {
    el.innerHTML = `⚠️ <b>SİSTEM KISITLI MODDA:</b> ${msg} <button class="btn btn-ghost btn-sm" style="color:#fff; padding:2px 8px; border-color:rgba(255,255,255,0.3); margin-left:12px;" onclick="location.reload()">↻ Yenile</button>`;
    el.style.display = 'block';
  }
}

function hideDegradedMode() {
  const el = document.getElementById('integrity-alert');
  if (el) el.style.display = 'none';
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
    AUTH.save(email, data.is_admin, data.access_token);
    document.getElementById('modal-login').classList.remove('open');
    checkAuth();
    showPage('dashboard');
    toast('Giriş başarılı ✓');
  } catch (e) {
    let msg = e.message || (typeof e === 'string' ? e : 'Bilinmeyen hata');
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
    errEl.textContent = 'Hata: ' + (e.message || (typeof e === 'string' ? e : 'Bilinmeyen hata')); 
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
    }

    // Phase 41, 42 & 43: Governance Health & Reinforcement
    if (s.governance) {
        const g = s.governance;
        const health = (g.health_score || g.score || 1.0) * 100;
        safeSetText('gov-health-value', `${health.toFixed(0)}%`);
        
        const gLabel = safeGet('gov-status-label');
        if (gLabel) {
            if (health >= 90) {
                gLabel.textContent = 'KURAL UYUMLU';
                gLabel.style.color = 'var(--safe)';
            } else {
                gLabel.textContent = 'MİMARİ RİSK';
                gLabel.style.color = 'var(--danger)';
            }
        }
        
        // Phase 42: Instinct Count
        safeSetText('instinct-count', g.instinct_count ?? 0);
        // Phase 43: Prevented Count
        safeSetText('prevented-count', g.prevented_count ?? 0);
    }

    // Phase 12.1: Integrity Check (State Awareness)
    if (s.is_fallback || s.degraded) {
        renderIntegrityStatus({
            db: s.source_of_truth === 'sqlite_fallback' ? 'fallback' : 'ok',
            is_fallback: s.is_fallback,
            source: s.source_of_truth
        });
    } else {
        const alertEl = safeGet('integrity-alert');
        if (alertEl) alertEl.style.display = 'none';
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
    const opt = ov.optional_services || {};
    
    // Merge optional services with standard ones for unified display
    const allSvc = { ...svc, ...Object.fromEntries(Object.entries(opt).map(([k, v]) => [k, { status: v }])) };
    
    const pillsEl = document.getElementById('service-pills');
    if (pillsEl) {
      pillsEl.innerHTML = Object.entries(allSvc).map(([n, i]) => {
        const st = i.status === 'online' ? 'online' : (i.status === 'not_configured' ? 'neutral' : (i.status === 'offline' ? 'offline' : 'warn'));
        const label = i.status === 'not_configured' ? n + ' (N/A)' : n;
        return `<span class="service-pill ${st}" title="${i.error || ''}"><span class="service-dot"></span>${label}</span>`;
      }).join('') || '<span style="color:var(--muted);font-size:11px;">Aktif servis yok</span>';
    }
    
    // Phase 60.5: Reality Grounding & Dissonance Sync
    if (ov.agi) {
      if (ov.agi.version) safeSetText('sovereign-version', ov.agi.version);
      
      const gScore = ov.agi.grounding_score ?? 1.0;
      const pReal = Math.round(gScore * 100);
      safeSetText('sovereign-reality-val', pReal + '%');
      safeStyle('sovereign-reality-fill', { 
        width: pReal + '%',
        background: pReal > 80 ? 'var(--gold)' : (pReal > 40 ? 'var(--orange)' : 'var(--red)')
      });

      const dBadge = safeGet('sovereign-dissonance-badge');
      if (dBadge) {
        if (ov.agi.dissonance_count > 0) {
          dBadge.style.display = 'inline-block';
          dBadge.textContent = `ÇELİŞKİ DETEKTÖRÜ (${ov.agi.dissonance_count})`;
        } else {
          dBadge.style.display = 'none';
        }
      }

      // Phase 61: Consensus Gating visualization
      const cScore = ov.agi.consensus_score ?? 1.0;
      const pCons = Math.round(cScore * 100);
      safeSetText('sovereign-consensus-val', pCons + '%');
      safeStyle('sovereign-consensus-fill', { 
        width: pCons + '%',
        background: pCons > 80 ? 'var(--cyan)' : (pCons > 60 ? 'var(--yellow)' : 'var(--red)')
      });

      // Phase 62: Deep Traceability score
      const tScore = ov.agi.traceability_score ?? 0.5;
      const pTrace = Math.round(tScore * 100);
      safeSetText('sovereign-traceability-val', pTrace + '%');
      safeStyle('sovereign-traceability-fill', { width: pTrace + '%' });

      // Phase 65: Cognitive Blackboard Sync
      const activeGoalId = ov.active_task_id || (ov.queue?.running_ids ? ov.queue.running_ids[0] : null);
      if (activeGoalId) {
        updateCognitiveBlackboard(activeGoalId);
      }
    }

    // Map health score (Computed vs Agent fallback)
    const hs = ov.metrics?.system_score ?? ov.agents?.system_score;
    const hsLabel = document.getElementById('health-score-label');
    if (hsLabel && hs != null) {
      const p = typeof hs === 'number' ? Math.round(hs * 100) : 0;
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

    // --- Faz 28/29: AGI Core Status Sync ---
    try {
      const agi = await api('/monitoring/agi/state');
      if (agi && !agi.error) {
        safeSetText('agi-mood-badge', agi.mood || 'NEUTRAL');
        
        const mot = agi.motivation || {};
        const pMot = Math.round(mot.level * 100);
        const pRes = Math.round(mot.resilience * 100);
        const pStr = Math.round(mot.internal_stress * 100);
        const pEn  = Math.round(mot.energy_reserve * 100);
        
        safeSetText('agi-motivation-val', pMot + '%');
        safeStyle('agi-motivation-fill', { width: pMot + '%' });
        
        safeSetText('agi-resilience-val', pRes + '%');
        safeStyle('agi-resilience-fill', { width: pRes + '%' });
        
        safeSetText('agi-stress-val', pStr + '%');
        safeStyle('agi-stress-fill', { width: pStr + '%', background: pStr > 70 ? 'var(--red)' : (pStr > 40 ? 'var(--orange)' : 'var(--yellow)') });
        
        safeSetText('agi-persistence-policy', mot.persistence_policy || 'BALANCED');
        safeSetText('agi-energy-val', pEn + '%');
        const enLabel = safeGet('agi-energy-val');
        if (enLabel) enLabel.style.color = pEn > 80 ? 'var(--green)' : (pEn > 40 ? 'var(--yellow)' : 'var(--red)');

        // Phase 54: Metabolic Metabolism Sync
        if (agi.metabolic_mode) {
          const modeEl = safeGet('agi-metabolic-mode');
          if (modeEl) {
            modeEl.textContent = agi.metabolic_mode.toUpperCase();
            modeEl.className = 'badge badge-' + agi.metabolic_mode.toLowerCase();
          }
          if (agi.metabolic_score != null) {
            safeSetText('agi-metabolic-val', agi.metabolic_score.toFixed(1));
            safeStyle('agi-metabolic-fill', { 
               width: Math.min(agi.metabolic_score * 100, 100) + '%',
               background: agi.metabolic_score > 0.8 ? 'var(--accent)' : (agi.metabolic_score > 0.4 ? 'var(--yellow)' : 'var(--orange)')
            });
          }
        }

        // --- Phase 34/35: Cognitive & Safety ---
        const cog = agi.cognitive || {};
        if (cog.reality_grounding_score != null) {
          const pReal = Math.round(cog.reality_grounding_score * 100);
          safeSetText('sovereign-reality-val', pReal + '%');
          safeStyle('sovereign-reality-fill', { width: pReal + '%' });
        }
      }
    } catch (e) {
      console.warn('AGI state fetch failed', e);
    }

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
      recentEl.innerHTML = tasks.length ? tasks.map(t => {
        const label = STATUS_LABELS[t.status] || t.status;
        return `
        <div style="display:flex;align-items:center;gap:8px;padding:8px 0;border-bottom:1px solid rgba(26,34,48,.5);cursor:pointer;" onclick="openTaskDetail('${t.id}')">
          <span class="badge badge-${t.status}" style="width:75px;text-align:center;">${label}</span>
          <span style="flex:1;font-size:11px;font-family:var(--mono);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${t.title}</span>
          <span class="badge badge-${t.priority}">${t.priority}</span>
        </div>`;
      }).join('') : '<div style="color:var(--muted);font-size:11px;padding:12px 0;">Henüz görev yok</div>';
    }
  } catch (e) { }

function renderIntegrityStatus(integrity) {
  const alertEl = safeGet('integrity-alert');
  const dot = safeGet('sidebar-status-dot');
  const txt = safeGet('sidebar-status-text');

  if (!alertEl) return;

  let msg = '';
  let severity = 'orange';

  if (integrity.db === 'fallback' || integrity.source === 'sqlite_fallback') {
    msg = '⚠️ DİKKAT: Veritabanı bağlantısı kısıtlı (SQLite Fallback aktif). Yazma işlemleri geçicidir.';
    severity = 'orange';
  } else if (integrity.is_fallback) {
    msg = '⚠️ SİSTEM KISITLI MODDA: Bazı servisler yerel bypass modunda çalışıyor.';
    severity = 'yellow';
  }

  if (msg) {
    alertEl.innerHTML = msg;
    alertEl.style.display = 'block';
    alertEl.style.background = severity === 'orange' ? 'var(--orange)' : 'var(--yellow)';
    alertEl.style.color = '#000';
    
    if (dot) dot.style.background = severity === 'orange' ? 'var(--orange)' : 'var(--yellow)';
    if (txt) txt.textContent = 'Sistem Kısıtlı';
  } else {
    alertEl.style.display = 'none';
    if (dot) dot.style.background = 'var(--green)';
    if (txt) txt.textContent = 'Sistem Aktif';
  }
}
  try {
    const h = await api('/health');
    const dot = safeGet('sidebar-status-dot');
    const txt = safeGet('sidebar-status-text');
    const alertBar = safeGet('memory-leak-alert');
    
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
    const txt = safeGet('sidebar-status-text');
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

  // Phase 45.0 Sovereign AGI Evolution Monitoring
  loadSovereignEvolution().catch(e => console.warn('Sovereign evolution load failed:', e));
}

async function loadSovereignEvolution() {
  const container = safeGet('sovereign-evolution-logs');
  const pulse = document.querySelector('.evolution-pulse');
  const statusLabel = safeGet('sovereign-status-label');
  
  if (!container) return;

  try {
    const records = await api('/monitoring/agi/evolution?limit=5');
    
    if (!records || records.length === 0) {
      container.innerHTML = '<div style="color:var(--muted); font-size:11px; padding:10px; text-align:center;">Henüz evrimsel iz kaydı bulunmuyor.</div>';
      if (statusLabel) statusLabel.textContent = 'IDLE';
      if (pulse) pulse.classList.remove('active');
      return;
    }

    if (statusLabel) statusLabel.textContent = 'STABLE (v121.0)';
    if (pulse) pulse.classList.add('active');

    container.innerHTML = records.map(r => `
      <div class="sovereign-log-item" onclick="showSovereignDetail('${r.id}')" title="Gerekçe: ${r.reason}">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
          <span style="font-size:11px; font-weight:700; color:var(--gold); font-family:var(--mono);">${r.file_path ? r.file_path.split('/').pop() : 'System'}</span>
          <span style="font-size:9px; color:var(--muted);">${new Date(r.timestamp).toLocaleTimeString('tr-TR')}</span>
        </div>
        <div style="font-size:10px; color:var(--text2); overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">
          ${r.reason || 'Otonom iyileştirme uygulandı.'}
        </div>
        <div style="display:flex; gap:6px; margin-top:6px;">
          <span class="badge" style="font-size:8px; padding:2px 4px; background:rgba(182, 122, 255, 0.1); color:var(--ultraviolet);">PATCH</span>
          <span class="badge" style="font-size:8px; padding:2px 4px; background:rgba(212, 175, 55, 0.1); color:var(--gold);">PROVENANCE</span>
        </div>
      </div>
    `).join('');
  } catch (err) {
    console.error('Sovereign load err:', err);
    container.innerHTML = `<div style="color:var(--red); font-size:10px; padding:10px;">Bağlantı hatası: ${err.message}</div>`;
  }
}

async function showSovereignDetail(id) {
  openModal('modal-detail');
  const el = document.getElementById('modal-detail-content');
  el.innerHTML = '<div class="loading">Sovereign veri kanıtı (Provenance) yükleniyor...</div>';
  try {
    const data = await api('/monitoring/agi/evolution?limit=100');
    const item = data.find(r => r.id === id);
    if (!item) throw new Error('Kayıt bulunamadı.');
    
    el.innerHTML = `
      <div style="margin-bottom:20px; border-bottom:1px solid var(--border); padding-bottom:15px;">
        <div style="font-size:10px; color:var(--accent); font-family:var(--mono); margin-bottom:4px;">PROVENANCE_ID: ${item.id}</div>
        <h2 class="glow-text-gold" style="font-size:20px;">Otonom Evrim Kaydı</h2>
      </div>
      
      <div class="cognitive-trace-box" style="margin-bottom:24px;">
        <div style="font-size:12px; line-height:1.6; color:var(--text);">${item.reason || 'Sistem otonom bir iyileştirme kararı aldı.'}</div>
      </div>
      
      <div style="display:grid; grid-template-columns: 1fr 1fr; gap:16px; margin-bottom:24px;">
        <div class="glass-panel" style="padding:15px; border-color:var(--orange);">
          <div style="font-size:9px; color:var(--muted); margin-bottom:4px;">HEDEF DOSYA</div>
          <div style="font-family:var(--mono); font-size:11px; color:var(--orange);">${item.file_path || 'Global System'}</div>
        </div>
        <div class="glass-panel" style="padding:15px; border-color:var(--secondary);">
          <div style="font-size:9px; color:var(--muted); margin-bottom:4px;">SÜRÜM / POLİTİKA</div>
          <div style="font-family:var(--mono); font-size:11px; color:var(--secondary);">${item.version || 'v121.0'} / ${item.policy_id || 'DEFAULT'}</div>
        </div>
        <div class="glass-panel" style="padding:15px; border-color:var(--green); grid-column: span 2;">
          <div style="font-size:9px; color:var(--muted); margin-bottom:4px;">AUTONOMOUS_LEVEL</div>
          <div style="font-family:var(--mono); font-size:11px; color:var(--green);">${item.autonomous_level || 'Sovereign (v121.0)'} [Impact: ${Math.round((item.impact_score || 0.95)*100)}%]</div>
        </div>
      </div>
      
      ${item.diff ? `
      <div style="margin-bottom:20px;">
        <div style="font-size:11px; font-weight:700; color:var(--green); margin-bottom:8px;">YAMA ÖZETİ (PATCH SUMMARY)</div>
        <div style="background:#000; padding:16px; border-radius:8px; font-size:11px; color:var(--green); font-family:var(--mono); white-space:pre-wrap; border:1px solid var(--border);">${item.diff}</div>
      </div>
      ` : ''}
      
      <div class="modal-actions">
        <button class="btn btn-ghost" onclick="closeModal('modal-detail')">Kapat</button>
      </div>
    `;
  } catch (e) {
    el.innerHTML = `<div class="error-msg">${e.message}</div>`;
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
    document.getElementById('task-table').innerHTML = `<table><thead><tr><th>ID</th><th>Başlık</th><th>Durum</th><th>Öncelik</th><th>Kaynak</th><th>İlerleme</th><th>Tarih</th><th>İşlem</th></tr></thead><tbody>${tasks.map(t => `<tr onclick="openTaskDetail('${t.id}')" style="cursor:pointer;"><td style="color:var(--muted);">${t.id.substring(0, 8)}</td><td style="max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="${t.title}">${t.title}</td><td><span class="badge badge-${t.status}">${STATUS_LABELS[t.status] || t.status}</span></td><td><span class="badge badge-${t.priority}">${t.priority}</span></td><td style="color:var(--muted);">${t.source}</td><td style="min-width:80px;"><div class="progress-bar"><div class="progress-fill" style="width:${t.progress_pct || 0}%"></div></div><span style="font-size:9px;color:var(--muted);">${t.progress_pct || 0}%</span></td><td style="color:var(--muted);">${t.created_at ? new Date(t.created_at).toLocaleDateString('tr-TR') : '—'}</td><td onclick="event.stopPropagation();"><div style="display:flex;gap:4px;">
      ${t.status === 'error' ? `<button type="button" class="btn btn-ghost btn-sm" style="color:var(--green);" onclick="retryTask('${t.id}')" title="Yeniden Dene">↻</button>` : ''}
      ${(t.status === 'running' && CAPS.supports_pause) ? `<button type="button" class="btn btn-ghost btn-sm" style="color:var(--yellow);" onclick="pauseTask('${t.id}')" title="Duraklat">⏸</button>` : ''}
      ${(t.status === 'paused' && CAPS.supports_resume) ? `<button type="button" class="btn btn-ghost btn-sm" style="color:var(--green);" onclick="resumeTask('${t.id}')" title="Devam Ettir">▶</button>` : ''}
      ${(['pending', 'queued', 'running', 'paused', 'pending_approval'].includes(t.status) && CAPS.supports_cancel) ? `<button type="button" class="btn btn-ghost btn-sm" style="color:var(--orange);" onclick="cancelTask('${t.id}')" title="İptal Et">■</button>` : ''}
      <button type="button" class="btn btn-ghost btn-sm" onclick="copyTask('${t.id}')" title="Kopyala">⧉</button>
      <button type="button" class="btn btn-ghost btn-sm" style="color:var(--red);" onclick="deleteTask('${t.id}')" title="Sil">🗑</button>
    </div></td></tr>`).join('')}</tbody></table>`;
  } catch (e) { document.getElementById('task-table').innerHTML = `<div class="loading" style="color:var(--red);">Hata: ${e.message}</div>`; }
}

function agentEmoji(id) { return { self_governor: '⚖️', architect: '🏛️', backend_dev: '⚙️', frontend_dev: '🎨', qa_engineer: '🧪', devops: '🚀', security: '🔒', data_eng: '🗄️', tech_writer: '📝' }[id] || '🤖'; }

async function openTaskDetail(id) {
  openModal('modal-detail');
  const contentEl = document.getElementById('modal-detail-content');
  contentEl.innerHTML = '<div class="loading">Bilişsel veriler senkronize ediliyor…</div>';
  
  try {
    const t = await api('/tasks/' + id);
    const subtasks = t.subtasks || []; 
    const logs = t.logs || [];
    
    // 1. Report Markdown
    let reportHtml = '';
    if (t.report && t.report.trim()) {
      try {
        if (typeof marked !== 'undefined') {
          reportHtml = typeof marked.parse === 'function' ? marked.parse(t.report) : marked(t.report);
        } else {
          reportHtml = '<div style="white-space:pre-wrap;">' + t.report + '</div>';
        }
      } catch (e) {
        reportHtml = '<div style="white-space:pre-wrap;">' + t.report + '</div>';
      }
    }

    // 2. AGI Mission Control Header
    let agiHeader = '';
    if (t.agi_metadata) {
      const rScore = (t.agi_metadata.verification?.reality_score || 0) * 100;
      agiHeader = `
        <div class="agi-mission-control sovereign-card" style="margin-bottom:32px; padding:20px; border-radius:16px;">
          <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:16px;">
            <div>
              <div style="font-size:10px; font-weight:800; color:var(--accent); text-transform:uppercase; letter-spacing:0.1em; margin-bottom:4px;">Cortex v121.0</div>
              <h3 style="font-size:18px; font-weight:800; color:#fff; margin:0;">Misyon Analizi</h3>
            </div>
            <div style="text-align:right;">
               <div style="font-size:10px; color:var(--muted); margin-bottom:4px;">Reality Score</div>
               <div style="font-size:24px; font-weight:900; color:${rScore >= 80 ? 'var(--green)' : 'var(--yellow)'}; font-family:var(--header-font);">${rScore.toFixed(0)}%</div>
            </div>
          </div>
          <div style="display:grid; grid-template-columns: 1fr 1fr; gap:16px;">
            <div style="background:rgba(0,0,0,0.2); padding:12px; border-radius:10px; border-left:3px solid var(--accent);">
              <div style="font-size:9px; color:var(--muted); margin-bottom:4px;">PROBLEM HEDEFİ</div>
              <div style="font-size:12px; color:var(--text); font-weight:600;">${t.agi_metadata.frame?.objective || 'Tanımlanmadı'}</div>
            </div>
            <div style="background:rgba(0,0,0,0.2); padding:12px; border-radius:10px; border-left:3px solid var(--purple);">
              <div style="font-size:9px; color:var(--muted); margin-bottom:4px;">VERIFICATION</div>
              <div style="font-size:11px; color:var(--text2); line-height:1.4;">${t.agi_metadata.verification?.summary || 'Analiz sürüyor...'}</div>
            </div>
          </div>
        </div>`;
    }

    // 3. Reasoning Trace
    let reasoningBlock = '';
    const reasoning = t.reflective_reasoning || t.reflection || t.agi_metadata?.reflection || t.agi_metadata?.reasoning;
    if (reasoning) {
      reasoningBlock = `
        <div class="cognitive-trace-box" style="margin-bottom:24px;">
          <div style="font-size:13px; font-weight:700; color:var(--accent); margin-bottom:8px; display:flex; align-items:center; gap:8px;">
            <span class="evolution-pulse active" style="width:8px; height:8px;"></span> Bilişsel İz (Reflective Reasoning)
          </div>
          <div style="font-size:12px; line-height:1.6; color:var(--text2); font-style:italic;">"${reasoning}"</div>
        </div>`;
    }

    // 4. Planning Hierarchy (Phase 54: Recursive Support)
    let planningHtml = '';
    if (subtasks && subtasks.length > 0) {
        // Calculate depths based on parent_id relations
        const depthMap = {};
        subtasks.forEach(s => {
          if (!s.parent_id) depthMap[s.id] = 0;
        });
        // Simplistic multi-pass resolution for depth (2 passes usually enough for demo)
        for(let i=0; i<3; i++) {
          subtasks.forEach(s => {
            if (s.parent_id && depthMap[s.parent_id] != null) {
              depthMap[s.id] = depthMap[s.parent_id] + 1;
            }
          });
        }

        planningHtml = `
          <div style="margin-top:32px; margin-bottom:32px;">
            <h3 style="font-size:16px; margin-bottom:16px; display:flex; align-items:center; gap:8px;">
              <span class="glow-text-purple">🗺️ Planlama Derinliği (Recursive Flow)</span>
            </h3>
            <div class="subtask-hierarchy">
              ${subtasks.map((s, idx) => {
                const depth = depthMap[s.id] || 0;
                return `
                <div class="subtask-node recursive-depth-${Math.min(depth, 3)}" style="padding:15px; background:rgba(255,255,255,0.01); border:1px solid ${s.status === 'completed' ? 'var(--green)' : 'var(--border)'}; border-radius:12px; margin-bottom:12px; position:relative; padding-left:45px;">
                  <div style="position:absolute; left:12px; top:18px; width:24px; height:24px; background:${s.status === 'completed' ? 'var(--green)' : 'var(--bg2)'}; color:${s.status === 'completed' ? '#000' : 'var(--text)'}; border-radius:50%; display:flex; align-items:center; justify-content:center; font-weight:800; font-size:11px; border:1px solid var(--border);">${idx + 1}</div>
                  <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                    <div style="display:flex; align-items:center;">
                      <span style="font-size:13px; font-weight:700; color:${s.status === 'completed' ? 'var(--green)' : '#fff'};">${s.title || (s.agent_id ? s.agent_id.toUpperCase() : 'Alt Görev')}</span>
                      ${s.is_complex ? '<span class="badge badge-recursive">RECURSIVE</span>' : ''}
                    </div>
                    <span class="badge" style="font-size:9px; background:rgba(255,255,255,0.05);">${agentEmoji(s.agent_id)} ${s.agent_id}</span>
                  </div>
                  <div style="font-size:11px; color:var(--muted);">${s.description || 'Analiz ediliyor...'}</div>
                  ${s.quality_score ? `<div style="margin-top:6px; font-size:10px; color:var(--green);">🎯 Hassasiyet Skoru: %${(s.quality_score*100).toFixed(0)}</div>` : ''}
                </div>
              `}).join('')}
            </div>
          </div>`;
    }

    // 5. Final Assembly
    contentEl.innerHTML = `
      <div class="task-detail-header" style="margin-bottom:20px;">
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">
          <span class="badge badge-${t.status}">${STATUS_LABELS[t.status] || t.status}</span>
          <span class="badge badge-${t.priority}">${t.priority}</span>
          <span style="font-size:12px;color:var(--muted);font-family:var(--mono);">${t.source}</span>
        </div>
        <h2 style="font-size:24px;font-weight:800;margin:10px 0;color:#fff;font-family:var(--header-font);line-height:1.2;">${t.title}</h2>
      </div>

      <div class="task-meta-grid" style="display:grid;grid-template-columns:repeat(auto-fit, minmax(140px, 1fr));gap:12px;margin-bottom:24px;padding:16px;background:rgba(255,255,255,0.02);border-radius:12px;border:1px solid var(--border);">
        <div class="meta-item"><div class="meta-label">ID</div><div class="meta-value" style="font-family:var(--mono);font-size:11px;color:var(--primary);">${t.id.substring(0, 16)}</div></div>
        <div class="meta-item"><div class="meta-label">İLERLEME</div><div class="meta-value" style="font-weight:700;">${t.progress_pct || 0}%</div></div>
        <div class="meta-item"><div class="meta-label">MALİYET</div><div class="meta-value" style="color:var(--green);font-weight:700;">$${(t.total_cost || 0).toFixed(4)}</div></div>
        <div class="meta-item"><div class="meta-label">İŞ AKIŞI</div><div class="meta-value" style="font-size:12px;">${t.workflow_template || 'default'}</div></div>
      </div>

      ${agiHeader}
      ${reasoningBlock}

      ${t.error_detail ? `<div style="background:rgba(239,68,68,.07);border:1px solid rgba(239,68,68,.2);border-radius:12px;padding:16px;margin-bottom:24px;font-family:var(--mono);font-size:13px;color:var(--red);"><div style="font-weight:800;margin-bottom:4px;">❌ HATA DETAYI</div>${t.error_detail}</div>` : ''}
      
      ${planningHtml}

      ${reportHtml ? `
        <div class="task-result-section" style="margin-top:32px;">
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px; font-size:14px; font-weight:700; color:var(--green);">
            <span>✓</span> SONUÇ RAPORU
          </div>
          <div class="markdown-content" style="background:rgba(255,255,255,0.01); border:1px solid var(--border); padding:20px; border-radius:12px;">
            ${reportHtml}
          </div>
        </div>` : ''}

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
        ${t.status === 'error' ? `<button class="btn btn-primary btn-sm" style="background:var(--green);" onclick="retryTask('${t.id}');closeModal('modal-detail')">↻ Tekrar Dene</button>` : ''}
        ${(['pending', 'running', 'paused'].includes(t.status) && CAPS.supports_cancel) ? `<button class="btn btn-ghost btn-sm" style="color:var(--red);" onclick="cancelTask('${t.id}');closeModal('modal-detail')">■ Görevi Durdur</button>` : ''}
        <button class="btn btn-ghost btn-sm" onclick="copyTask('${t.id}')">⧉ Kopyala</button>
        <button class="btn btn-ghost btn-sm" style="margin-left:auto;color:var(--muted);" onclick="deleteTask('${t.id}')">🗑 Sil</button>
      </div>`;

    // Fetch skill logs asynchronously after basic render
    api('/skills/logs?project_id=' + t.id).then(sLogs => {
       const scBox = document.getElementById('skill-logs-content');
       if (!scBox) return;
       if (!sLogs || sLogs.length === 0) {
          scBox.innerHTML = '<div style="color:var(--muted);font-size:11px;text-align:center;padding:10px 0;">Özel bir beceri kullanılmadı.</div>';
       } else {
          scBox.innerHTML = '<div style="display:flex;flex-direction:column;gap:8px;">' + sLogs.map(sl => `
             <div style="background:rgba(0,0,0,0.2);border-radius:8px;padding:12px;border-left:3px solid ${sl.success ? 'var(--green)' : 'var(--red)'}; cursor:pointer;" onclick="const d=this.querySelector('.skill-detail-json'); d.style.display=d.style.display==='none'?'block':'none';">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
                    <span style="font-size:12px;font-weight:700;color:var(--text);font-family:var(--mono);">${sl.skill_id.toUpperCase()}</span>
                    <span style="font-size:10px;color:var(--muted);">${sl.duration_s ? sl.duration_s.toFixed(2) + 's' : ''}</span>
                </div>
                <div style="font-size:11px;color:var(--text2);">${sl.summary}</div>
                <div class="skill-detail-json" style="display:none; margin-top:10px; padding:10px; background:#000; font-size:10px; font-family:var(--mono);">
                   <pre style="margin:0; overflow-x:auto;">${JSON.stringify(sl.data, null, 2)}</pre>
                </div>
             </div>
          `).join('') + '</div>';
       }
    }).catch(err => {
       const scBox = document.getElementById('skill-logs-content');
       if (scBox) scBox.innerHTML = '<div style="color:var(--red);font-size:11px;">İzleme verisi alınamadı.</div>';
    });

  } catch (e) { 
    contentEl.innerHTML = `<div style="padding:40px;text-align:center;color:var(--red); font-size:13px;">⚠️ Hata oluştu: ${e.message}</div>`; 
  }
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
    const msg = e.detail || e.message || (typeof e === 'string' ? e : 'Görev oluşturulamadı');
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
      const circuitInfo = l.circuit_status || {};
      const providers = Array.isArray(circuitInfo) ? circuitInfo : (circuitInfo.providers || []);
      const metabolicMode = circuitInfo.metabolic_mode || 'NORMAL';
      const metabolicScore = circuitInfo.metabolic_score || 0;

      llmEl.innerHTML = `
        <div style="margin-bottom:16px;font-family:var(--mono);font-size:11px;">
          <div style="display:flex;justify-content:space-between;margin-bottom:4px;"><span>Top. Çağrı</span><span>${l.total_llm_calls || 0}</span></div>
          <div style="display:flex;justify-content:space-between;margin-bottom:4px;"><span>Başarı %</span><span>${l.llm_success_rate || 0}%</span></div>
          <div style="display:flex;justify-content:space-between;padding-top:8px;border-top:1px solid rgba(255,255,255,0.05);margin-top:4px;">
            <span>Metabolizma</span>
            <span class="badge ${metabolicMode === 'ECO' ? 'badge-error' : (metabolicMode === 'TURBO' ? 'badge-completed' : 'badge-neutral')}" style="font-size:9px;">
              ${metabolicMode} (${(metabolicScore * 100).toFixed(0)}%)
            </span>
          </div>
        </div>
        ${providers.map(cs => `
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
               <span>ms: ${cs.avg_latency_s ? cs.avg_latency_s.toFixed(2) : '0.00'}</span>
            </div>
          </div>
        `).join('')}
      `;
    }
  } catch (e) { console.warn('LLM monitoring failed:', e); }

  try {
    const s = await api('/monitoring/system');
    const resEl = document.getElementById('system-resources');
    if (resEl) {
      resEl.innerHTML = s.available ? `
        <div class="metric-hologram" style="display:grid;grid-template-columns:repeat(3,1fr);gap:16px;">
          <div class="agent-stat-item"><span class="agent-stat-label">CPU</span><span class="agent-stat-value">${s.cpu_pct ?? '—'}%</span></div>
          <div class="agent-stat-item"><span class="agent-stat-label">RAM</span><span class="agent-stat-value">${s.ram_used_gb ?? '—'}GB</span></div>
          <div class="agent-stat-item"><span class="agent-stat-label">DISK</span><span class="agent-stat-value">${s.disk_pct ?? '—'}%</span></div>
          <div class="agent-stat-item" style="grid-column: span 3;"><span class="agent-stat-label">Uptime</span><span class="agent-stat-value" style="font-size:12px;">${s.boot_time || '—'}</span></div>
        </div>
      ` : '<div style="color:var(--muted);text-align:center;padding:24px;font-size:11px;">🛠️ Sistem metrikleri şu an kullanılamıyor (psutil eksik)</div>';
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
  if (wsConn && (wsConn.readyState === 1 || wsConn.readyState === 0)) return;
  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  const token = AUTH.token;
  const wsUrl = `${proto}://${location.host}/ws/logs${token ? '?token=' + encodeURIComponent(token) : ''}`;
  
  console.log('Connecting to WebSocket...');
  wsConn = new WebSocket(wsUrl);
  const statusEl = document.getElementById('ws-status');
  wsConn.onopen = () => { if (statusEl) statusEl.textContent = '● CANLI BAĞLANTI'; statusEl.style.color = 'var(--primary)'; };
  wsConn.onclose = () => { if (statusEl) statusEl.textContent = '○ KESİLDİ'; statusEl.style.color = 'var(--muted)'; setTimeout(initWS, 3000); };
  wsConn.onmessage = (e) => {
    try {
      const d = JSON.parse(e.data);
      if (d.error === 'Unauthorized') {
        if (statusEl) { statusEl.textContent = '○ YETKİ YOK'; statusEl.style.color = '#ef4444'; }
        return;
      }
      if (d.event === 'live_patch') handleLivePatch(d);
      else if (d.event === 'approval.needed') { toast('⚠️ Onay Talebi Geldi', 'warning'); loadApprovals(); }
      else if (d.event === 'debate_state') { if (typeof handleDebateState === 'function') handleDebateState(d); }
      else if (d.event === 'job_progress') {
        const idShort = d.job_id ? d.job_id.substring(0, 8) : '...';
        toast(`🔨 Onarım: ${idShort} -> ${d.status}`, 'info');
        const activePage = document.querySelector('.page.active')?.id;
        if (activePage === 'page-repair-center') loadRepairCenter();
        if (activePage === 'page-dashboard') loadDashboard();
        if (activePage === 'page-tasks') loadTasks();
      }
      else { addLog(d); updateFeed(d); }
    } catch (err) { console.error('WS Error:', err); }
  };
}

function addLog(evt) {
  const feed = document.getElementById('log-feed');
  if (!feed) return;
  if (feed.querySelector('.loading')) feed.innerHTML = '';
  if (evt.error && !evt.severity) evt.severity = 'error'; 
  // Hata objelerini de log olarak basmak için kontrole ekleme yapıyoruz
  const isErr = !!evt.error;
  
  const div = document.createElement('div');
  div.className = `log-entry ${evt.severity || 'info'}`;
  
  // Ajan ID formatla (yoksa SYSTEM)
  const agentId = evt.agent_id || 'SYSTEM';
  const tagClass = evt.agent_id ? 'log-tag agent' : 'log-tag system';
  const tag = `<span class="${tagClass}">[${agentId}]</span>`;
  
  // Mesaj içeriğini belirle (message öncelikli, sonra error)
  const content = evt.message || evt.error || evt.event || evt.type || '';
  if (!content) return; // İçerik yoksa basma

  div.innerHTML = `<span class="log-time">${new Date().toLocaleTimeString('tr-TR')}</span> ${tag} <span class="log-msg">${content}</span>`;
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
window.InactivityMonitor = InactivityMonitor;
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
window.loadSandboxPage = async () => {
    // Sandbox sayfa yükleme mantığı — Şimdilik sadece duman testi
    safeSetText('sb-status', 'HAZIR');
    const codeEl = document.getElementById('sb-code');
    if (codeEl && !codeEl.value) {
        codeEl.value = 'print("Faz 12.1 Devotee: Sistem hazir.")';
    }
};
window.loadVectorLessonsPage = async () => {
    // Vektör dersleri duman testi
    const stats = await api('/faz12/vector-lessons/stats');
    safeSetHTML('vl-results', '<div style="color:var(--muted); font-size:11px; padding:10px;">Vektör tabanında ' + (stats.total_lessons || 0) + ' ders var. Semptom araması yapınız.</div>');
};

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

async function updateAGIState() {
  try {
    const data = await api('/monitoring/agi/state');
    if (data.error) return;

    const mot = data.motivation || {};
    
    // Update Bars
    const motFill = document.getElementById('agi-motivation-fill');
    if (motFill) motFill.style.width = (mot.level * 100) + '%';
    safeSetText('agi-motivation-val', (mot.level * 100).toFixed(0) + '%');

    const resFill = document.getElementById('agi-resilience-fill');
    if (resFill) resFill.style.width = (mot.resilience * 100) + '%';
    safeSetText('agi-resilience-val', (mot.resilience * 100).toFixed(0) + '%');

    const stressFill = document.getElementById('agi-stress-fill');
    if (stressFill) stressFill.style.width = (mot.internal_stress * 100) + '%';
    safeSetText('agi-stress-val', (mot.internal_stress * 100).toFixed(0) + '%');

    // Update Meta
    safeSetText('agi-mood-badge', data.mood || 'NEUTRAL');
    safeSetText('agi-persistence-policy', mot.persistence_policy || 'BALANCED');
    safeSetText('agi-energy-val', (mot.energy_reserve * 100).toFixed(0) + '%');

    // Color coordination for stress
    if (motFill) {
      if (mot.level > 0.8) motFill.style.background = 'var(--green)';
      else if (mot.level > 0.4) motFill.style.background = 'var(--yellow)';
      else motFill.style.background = 'var(--red)';
    }

  } catch (e) {
    console.warn('AGI state sync failed:', e);
  }
}

// Initial state and loops
document.addEventListener('DOMContentLoaded', () => {
  if (checkAuth()) {
    InactivityMonitor.init(); // Phase 56: İnyaktivite korumasını başlat
    setInterval(updateFreshness, 5000);
    setInterval(updateAGIState, 5000); // Poll AGI state every 5s
    setInterval(() => {
      if (document.visibilityState === 'visible') {
        const active = document.querySelector('.page.active');
        if (active && active.id === 'page-dashboard') loadDashboard();
      }
    }, 30000); // Background refresh every 30s
  }
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
/**
 * Phase 65: Bilişsel Karatahta (Working Memory) Güncelleme
 */
async function updateCognitiveBlackboard(goalId) {
  const container = document.getElementById('sovereign-blackboard-container');
  if (!container) return;

  try {
    const data = await api('/monitoring/blackboard/' + goalId);
    if (data.error) throw new Error(data.error);

    let html = '';
    
    // 1. Warnings (Priority)
    if (data.critical_warnings && data.critical_warnings.length > 0) {
      data.critical_warnings.forEach(w => {
        html += `<div style="color:var(--red); margin-bottom:4px;">[WARN] ${w.content}</div>`;
      });
    }

    // 2. Hypothesis
    if (data.current_hypothesis) {
      html += `<div style="color:var(--gold); border-bottom:1px solid rgba(255,255,255,0.05); padding-bottom:4px; margin-bottom:8px;">[IDEA] ${data.current_hypothesis.content}</div>`;
    }

    // 3. Discoveries
    if (data.active_discoveries && data.active_discoveries.length > 0) {
      data.active_discoveries.reverse().forEach(d => {
        html += `<div style="color:var(--text2); opacity:0.8;">> ${d.content}</div>`;
      });
    }

    if (!html) html = '<div style="color:var(--muted); font-style:italic;">Henüz aktif keşif yok. Modeller analiz ediyor...</div>';
    
    // Reasoning Accuracy (Phase 68: Eval Harness)
    try {
      const scoreData = await api('/monitoring/agi/cognitive_score');
      if (scoreData && scoreData.overall_cognitive_score !== undefined) {
        const acc = Math.round(scoreData.overall_cognitive_score * 100);
        safeSetText('sovereign-reasoning-accuracy', 'ACC: ' + acc + '%');
        safeStyle('sovereign-reasoning-accuracy', { color: acc > 80 ? 'var(--gold)' : 'var(--red)' });
      }
    } catch (e) {
      console.warn('Cognitive score fetch failed');
    }

  } catch (e) {
    console.error('Blackboard fetch error:', e);
    container.innerHTML = '<div style="color:var(--muted);">Karatahta erişilemez durumda.</div>';
  }
}
/**
 * SOVEREIGN DASHBOARD ENTRY POINT (Phase 12.1)
 * Bridges the gap between a static modular shell and a live cognitive engine.
 */
function initializeDashboard() {
  console.log('[Sovereign] Orchestrating cognitive startup...');
  
  // 1. Check Auth first
  if (!checkAuth()) {
    console.warn('[Auth] No session found. Redirecting to entry...');
    // In production, this would redirect to login or show overlay
    return;
  }

  // 2. Determine initial page and show it
  // This triggers loadDashboard() or equivalent via showPage switch
  const urlParams = new URLSearchParams(window.location.search);
  const startPage = urlParams.get('p') || 'dashboard';
  showPage(startPage);

  // 3. Start high-frequency background syncs if on dashboard
  if (startPage === 'dashboard') {
    updateAGIState();
    loadDashboard();
  }

  // 4. Initialize Core Modules
  try {
    InactivityMonitor.init();
    setInterval(updateFreshness, 5000);
    setInterval(updateAGIState, 8000); 
  } catch (e) {
    console.error('[Sovereign] Core Module Init Failed:', e);
  }

  console.log('[Sovereign] Entry point stabilized ✓');
}

// Ensure globally accessible for index.html
window.initializeDashboard = initializeDashboard;
