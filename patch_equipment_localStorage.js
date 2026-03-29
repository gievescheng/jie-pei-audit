// patch_equipment_localStorage.js
// 在瀏覽器 F12 → Console 頁籤貼上此腳本後按 Enter
// 將四台設備的最近保養日期和週期更新為正確值，不影響其他設備資料
(function () {
  const KEY = 'audit_equipment';
  const FIX = {
    'JE-001': '2025-12-01',
    'JE-002': '2025-12-01',
    'JE-003': '2025-12-01',
    'JE-004': '2025-12-01',
  };
  const INTERVAL = 365;  // 年保養

  let eqs = [];
  try { eqs = JSON.parse(localStorage.getItem(KEY) || '[]'); } catch (e) {}

  if (eqs.length === 0) {
    console.log('[INFO] localStorage 無設備資料，請重新整理頁面後再執行一次。');
    return;
  }

  let updated = 0;
  eqs = eqs.map(e => {
    if (FIX[e.id]) {
      updated++;
      return { ...e, lastMaintenance: FIX[e.id], intervalDays: INTERVAL };
    }
    return e;
  });

  localStorage.setItem(KEY, JSON.stringify(eqs));
  console.log(`[OK] 已更新 ${updated} 台設備（JE-001~JE-004）`);
  console.log('[OK] 最近保養日：2025-12-01，下次保養：2026-12-01，剩約 265 天');
  console.log('[OK] 請重新整理頁面以套用變更');
})();
