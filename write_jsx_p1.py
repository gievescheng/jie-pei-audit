# -*- coding: utf-8 -*-
dest = 'C:/Users/USER/Desktop/\u81ea\u52d5\u7a3d\u6838\u7a0b\u5f0f/audit-dashboard.jsx'

L = []
A = L.append

A('import { useState, useEffect, useCallback } from "react";')
A('')
A('// \u2500\u2500\u2500 INITIAL DATA \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500')
A('const initialInstruments = [')
A('  { id: "QI-001", name: "AOI \u81ea\u52d5\u5149\u5b78\u6aa2\u6e2c\u5100", type: "AOI", location: "\u54c1\u4fdd\u8ab2", calibratedDate: "2025-06-15", intervalDays: 365, status: "\u5408\u683c", needsMSA: true },')
A('  { id: "QI-002", name: "TTV \u539a\u5ea6\u91cf\u6e2c\u5100", type: "TTV", location: "\u54c1\u4fdd\u8ab2", calibratedDate: "2025-09-01", intervalDays: 365, status: "\u5408\u683c", needsMSA: true },')
A('  { id: "QI-003", name: "\u6e38\u6a19\u5361\u5c3a #1", type: "\u5361\u5c3a", location: "\u751f\u7522\u8ab2", calibratedDate: "2025-11-01", intervalDays: 180, status: "\u5408\u683c", needsMSA: false },')
A('  { id: "QI-004", name: "\u6e38\u6a19\u5361\u5c3a #2", type: "\u5361\u5c3a", location: "\u751f\u7522\u8ab2", calibratedDate: "2025-08-20", intervalDays: 180, status: "\u5408\u683c", needsMSA: false },')
A('  { id: "QI-005", name: "\u96fb\u5b50\u79e4 #1", type: "\u79e4", location: "\u8cc7\u6750\u8ab2", calibratedDate: "2025-10-10", intervalDays: 365, status: "\u5408\u683c", needsMSA: false },')
A('  { id: "QI-006", name: "\u6eab\u5ea6\u8a08 #1", type: "\u6eab\u5ea6\u8a08", location: "\u751f\u7522\u8ab2", calibratedDate: "2024-12-01", intervalDays: 365, status: "\u514d\u6821\u6b63", needsMSA: false },')
A('  { id: "QI-007", name: "\u624b\u6301\u5f0f\u5fae\u7c92\u5b50\u8a08\u6578\u5668 TSI-9303", type: "\u7c92\u5b50\u8a08\u6578\u5668", location: "\u751f\u7522\u8ab2", calibratedDate: "2025-03-15", intervalDays: 365, status: "\u5408\u683c", needsMSA: false },')
A('];')
A('')
A('const initialDocuments = [')
A('  { id: "MM-01", name: "\u54c1\u8cea\u624b\u518a", type: "\u7ba1\u7406\u624b\u518a", version: "2.0", department: "\u7ba1\u7406\u90e8", createdDate: "2025-10-01", author: "\u8521\u6709\u70ba", retentionYears: 16 },')
A('  { id: "MP-01", name: "\u6587\u4ef6\u5316\u8cc7\u8a0a\u7ba1\u5236\u7a0b\u5e8f", type: "\u7ba1\u7406\u7a0b\u5e8f", version: "2.0", department: "\u7ba1\u7406\u90e8", createdDate: "2025-12-01", author: "\u8521\u6709\u70ba", retentionYears: 16 },')
A('  { id: "MP-02", name: "\u7d44\u7e54\u74b0\u5883\u8207\u7e3e\u6548\u8a55\u4f30\u7ba1\u7406\u7a0b\u5e8f", type: "\u7ba1\u7406\u7a0b\u5e8f", version: "2.0", department: "\u7ba1\u7406\u90e8", createdDate: "2025-10-01", author: "\u8521\u6709\u70ba", retentionYears: 16 },')
A('  { id: "MP-03", name: "\u4eba\u529b\u8cc7\u6e90\u53ca\u8a13\u7df4\u7ba1\u7406\u7a0b\u5e8f", type: "\u7ba1\u7406\u7a0b\u5e8f", version: "1.0", department: "\u7ba1\u7406\u90e8", createdDate: "2025-07-01", author: "\u8521\u6709\u70ba", retentionYears: 16 },')
A('  { id: "MP-04", name: "\u8a2d\u65bd\u8a2d\u5099\u7ba1\u7406\u7a0b\u5e8f", type: "\u7ba1\u7406\u7a0b\u5e8f", version: "2.0", department: "\u7ba1\u7406\u90e8", createdDate: "2025-12-01", author: "\u8521\u6709\u70ba", retentionYears: 16 },')
A('  { id: "MP-05", name: "\u91cf\u6e2c\u8cc7\u6e90\u7ba1\u7406\u7a0b\u5e8f", type: "\u7ba1\u7406\u7a0b\u5e8f", version: "2.0", department: "\u54c1\u7ba1\u8ab2", createdDate: "2025-12-01", author: "\u7a0b\u9f0e\u667a", retentionYears: 16 },')
A('  { id: "MP-06", name: "\u5de5\u4f5c\u74b0\u5883\u7ba1\u7406\u7a0b\u5e8f", type: "\u7ba1\u7406\u7a0b\u5e8f", version: "1.0", department: "\u7ba1\u7406\u90e8", createdDate: "2025-07-01", author: "\u8521\u6709\u70ba", retentionYears: 16 },')
A('  { id: "MP-09", name: "\u5167\u90e8\u7a3d\u6838\u7ba1\u7406\u7a0b\u5e8f", type: "\u7ba1\u7406\u7a0b\u5e8f", version: "2.0", department: "\u7ba1\u7406\u90e8", createdDate: "2025-10-01", author: "\u8521\u6709\u70ba", retentionYears: 16 },')
A('  { id: "MP-10", name: "\u63a1\u8cfc\u53ca\u4f9b\u61c9\u5546\u7ba1\u7406\u7a0b\u5e8f", type: "\u7ba1\u7406\u7a0b\u5e8f", version: "1.0", department: "\u8cc7\u6750\u8ab2", createdDate: "2025-07-01", author: "\u8521\u6709\u70ba", retentionYears: 16 },')
A('  { id: "MP-15", name: "\u4e0d\u7b26\u5408\u53ca\u77ef\u6b63\u63aa\u65bd\u7ba1\u7406\u7a0b\u5e8f", type: "\u7ba1\u7406\u7a0b\u5e8f", version: "1.0", department: "\u54c1\u7ba1\u8ab2", createdDate: "2025-07-01", author: "\u7a0b\u9f0e\u667a", retentionYears: 16 },')
A('];')
A('')
print('Script part 1 OK, lines so far:', len(L))
