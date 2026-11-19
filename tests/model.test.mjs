import test from 'node:test';
import assert from 'node:assert/strict';
import {unpack,datesFor,period} from '../web/model.mjs';
test('preserve survey frequency and gaps',()=>{assert.deepEqual(datesFor('2025-10','2026-04','Quarterly'),['2025-10','2026-01','2026-04']);assert.deepEqual(datesFor('2024','2026','Annual'),['2024','2025','2026']);assert.equal(period('2026-04','Quarterly'),'2026 Q2');});
test('quality and missing observations',()=>{assert.deepEqual(unpack([null,'F']),[null,'F']);assert.deepEqual(unpack(0),[0,'']);});
