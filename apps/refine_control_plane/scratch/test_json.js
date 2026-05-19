/* eslint-disable @typescript-eslint/no-require-imports */
const fs = require('fs');
const tr = JSON.parse(fs.readFileSync('e:/ai_company_faz12.1/apps/refine_control_plane/src/messages/tr.json', 'utf8'));
console.log('Sidebar exists:', !!tr.sidebar);
console.log('Dashboard exists:', !!tr.dashboard);
console.log('Dashboard.engineVersion:', tr.dashboard?.engineVersion);
console.log('Quorum exists:', !!tr.quorum);
console.log('Training exists:', !!tr.training);
console.log('Safety.badge:', tr.safety?.badge);
