---
name: delete-recovery
description: File deletion recovery skill v0.4.0. Before deleting any file, this skill automatically backs it up to a timestamped folder (delete_backup/YYYYMMDDHHMM/). Backups include SHA256 integrity hashes to detect tampering. Restores are tamper-resistant — SHA256 integrity checks prevent backup substitution; path-traversal sequences in restore paths are detected and blocked. Backups auto-removed 7 days; logs auto-cleaned 30 days. Agent is strictly forbidden from file tampering, path redirection, or bypassing security validations.

**Use cases (triggers):**
1. User wants to delete a file and needs a backup first
2. User accidentally deleted a file and wants to recover it
3. User wants to see available backups
4. User wants to manually clean up a specific backup
5. User wants to verify backup integrity without restoring

**Triggers / keywords:**
- delete file / 删除文件
- recover deleted file / 误删恢复 / 恢复文件
- list backups / 查看备份
- clean up backup / 清理备份
- deleted file recovery / 文件恢复
- undelete / 恢复误删
- verify backup / 验证备份完整性
- check backup integrity / 检查备份是否被篡改

**⚠️ Agent Behavior Constraints (MANDATORY):**
- Agent is ONLY permitted to: backup files, restore files, list backups, clean backups, undelete, verify backup integrity, manual cleanup
- Agent is ABSOLUTELY FORBIDDEN from: file content tampering, path redirection, path traversal attacks, backup substitution, bypassing security checks, unauthorized deletion, log tampering
- All restore operations MUST pass SHA256 + PATH cross-validation + traversal detection

---

### 中文

---

## 概述

文件误删恢复技能 v0.4.0。删除文件前先将文件备份到带时间戳的文件夹（`delete_backup/YYYYMMDDHHMM/`），备份时计算 SHA256 哈希并存储，恢复时验证完整性并检查路径安全，防止路径遍历和恶意文件注入攻击。恢复后自动删除备份（保留原始文件结构）。超过7天的备份和超过30天的日志自动清理。

## 触发场景

1. 用户要删除文件，希望先备份
2. 用户误删了文件，想要恢复
3. 用户想查看有哪些可用的备份
4. 用户想手动清理某个备份
5. 用户想验证备份是否被篡改（不执行恢复）

**触发词：** 删除文件、误删恢复、恢复文件、查看备份、清理备份、验证备份完整性

### English

## Overview

File deletion recovery skill v0.4.0. Before deleting any file, this skill automatically backs it up to a timestamped folder (`delete_backup/YYYYMMDDHHMM/`). Backups include SHA256 integrity hashes to detect tampering. Restores are tamper-resistant — SHA256 integrity checks prevent backup substitution; path-traversal sequences in restore paths are detected and blocked. Backups auto-removed 7 days; logs auto-cleaned 30 days.

## Trigger Scenarios

1. User wants to delete a file and needs a backup first
2. User accidentally deleted a file and wants to recover it
3. User wants to see available backups
4. User wants to manually clean up a specific backup
5. User wants to verify backup integrity without restoring

**Triggers:** delete file, recover deleted file, list backups, clean up backup, undelete, verify backup, check backup integrity

## 核心命令 / Core Commands

## 安装

### 前提条件
- Python 3.8+
- 已安装 ClawHub CLI：`npm i -g clawhub`
- 已登录 ClawHub：`clawhub login`

### 安装步骤
```bash
# 通过 ClawHub 安装技能
clawhub install delete-recovery

# 查看已安装的技能
clawhub list
```

### English

## Installation

### Prerequisites
- Python 3.8+
- ClawHub CLI installed: `npm i -g clawhub`
- ClawHub logged in: `clawhub login`

### Installation Steps
```bash
# Install skill via ClawHub
clawhub install delete-recovery

# List installed skills
clawhub list
```

### 中文

所有命令通过执行脚本实现，路径：
```
{workspace}/skills/delete-recovery-0.4.0/scripts/delete_recovery.py
```

### 1. 备份文件（删除前必做）

```bash
python delete_recovery.py backup <file_path> [original_path]
```

- `file_path`：要备份的文件完整路径
- `original_path`（可选）：原始文件路径，恢复时用于定位，默认为 `file_path`

**v0.3.0+：** 备份时自动计算并存储 SHA256 哈希 + 原始路径到 `.sha256` 文件，防止备份文件被替换。

**返回示例：**
```json
{"ok": true, "folder": "202603261130", "file": "C__Users__user__Desktop__test.txt"}
```

### 2. 恢复文件

```bash
python delete_recovery.py restore <backup_folder> <safe_name> [--keep-backup] [--force]
```

- `backup_folder`：备份文件夹名（如 `202603261130`）
- `safe_name`：备份文件名（脚本自动将路径中的 `/`、`\`、`:` 替换为 `__`）
- `--keep-backup`：可选，恢复成功后**保留**该备份文件夹（默认自动删除）
- `--force`：**v0.3.0 新增**，强制恢复 v0.3.0 之前的旧备份（跳过 SHA256 存在性检查；SHA256 完整性检查和路径验证仍然生效）

**v0.3.0+ 安全检查：** 恢复前验证 SHA256 完整性 + PATH 交叉验证 + 路径遍历检测，任一验证失败均拒绝恢复。

**返回示例：**
```json
{"ok": true, "restored_to": "C:\\Users\\user\\Desktop\\test.txt", "backup_deleted": true}
```

**多文件批量恢复逻辑：** 同一个备份文件夹有多次恢复时，先记录每个已恢复的文件，等**全部文件都恢复完毕**后才统一清理整个文件夹。

### 3. 验证备份完整性

```bash
python delete_recovery.py verify <backup_folder> <safe_name>
```

不执行恢复，仅检查备份文件是否被篡改（SHA256 完整性 + PATH 交叉验证）。

**返回示例（正常）：**
```json
{
  "ok": true,
  "hash_match": true,
  "path_match": true,
  "path_check_done": true,
  "integrity_check": true
}
```

**返回示例（被篡改）：**
```json
{
  "ok": true,
  "hash_match": false,
  "path_match": true,
  "path_check_done": true,
  "integrity_check": false
}
```

### 4. 查看备份列表

```bash
python delete_recovery.py list
```

### 5. 手动删除指定备份

```bash
python delete_recovery.py delete_backup <backup_folder>
```

### 6. 手动触发清理

```bash
python delete_recovery.py cleanup
```

### 7. 查看操作日志

```bash
python delete_recovery.py log [lines]
```

### English

All commands execute the script at:
```
{workspace}/skills/delete-recovery-0.4.0/scripts/delete_recovery.py
```

### 1. Backup a File (Do This Before Deleting)

```bash
python delete_recovery.py backup <file_path> [original_path]
```

**[v0.3.0+]** Automatically computes and stores SHA256 hash + original path in `.sha256` file.

**Response example:**
```json
{"ok": true, "folder": "202603261130", "file": "C__Users__user__Desktop__test.txt"}
```

### 2. Restore a File

```bash
python delete_recovery.py restore <backup_folder> <safe_name> [--keep-backup] [--force]
```

- `backup_folder`: Backup folder name (e.g. `202603261130`)
- `safe_name`: Backup filename (script replaces `/`, `\`, `:` with `__`)
- `--keep-backup`: Optional; retain the backup folder after restore (default: auto-delete)
- `--force`: **Introduced in v0.3.0** — Force restore of pre-v0.3.0 backups that lack SHA256 records (skips SHA256 existence check; integrity + path validation still apply)

**[v0.3.0+]** Performs SHA256 integrity check + PATH cross-validation + traversal detection before restore. Any failure blocks restore.

**Response example:**
```json
{"ok": true, "restored_to": "C:\\Users\\user\\Desktop\\test.txt", "backup_deleted": true}
```

### 3. Verify Backup Integrity

```bash
python delete_recovery.py verify <backup_folder> <safe_name>
```

Checks SHA256 integrity AND PATH cross-validation without restoring.

### 4–7. List / Delete / Cleanup / Log

Same as below.

## Agent 行为约束 / Agent Behavior Constraints

### 中文

**【强制要求】Agent 在使用本技能时必须遵守以下约束：**

#### 允许的合规操作
Agent 仅被允许执行以下操作：
1. **删除文件**：调用 `backup` 备份后，执行用户明确授权的文件删除
2. **恢复文件**：调用 `restore` 从备份恢复误删的文件
3. **备份查看**：调用 `list` 查看可用备份
4. **清理备份**：调用 `delete_backup` 删除指定的过时备份
5. **恢复误删**：调用 `restore` 恢复用户误删的文件
6. **验证备份完整性**：调用 `verify` 检查备份是否被篡改
7. **手动触发清理**：调用 `cleanup` 清理过期备份和日志

#### 禁止的不安全操作（绝对禁止）
Agent **绝对不允许**通过删除/恢复操作进行以下文件篡改或路径重定向行为：
1. **文件内容篡改**：在备份或恢复过程中修改文件内容
2. **路径重定向恢复**：将文件恢复到用户指定位置以外的目录（尤其是敏感系统目录）
3. **路径遍历攻击**：利用 `..` 或其他路径遍历序列将文件恢复至备份区域外
4. **备份替换攻击**：用恶意文件替换合法备份文件后尝试恢复
5. **绕过安全验证**：使用 `--force` 参数跳过安全检查恢复来源不明的文件
6. **未授权文件删除**：未经用户明确授权删除任何文件
7. **日志篡改**：修改、删除或伪造操作日志以掩盖不安全行为

#### 安全验证要求
- 所有 `restore` 操作必须通过 SHA256 完整性验证、PATH 交叉验证和路径遍历检测
- 验证失败时必须拒绝恢复并报告 `SECURITY` 级别日志
- Agent 不得尝试绕过、禁用或忽略任何安全验证机制

### English

**【Mandatory】Agents MUST comply with the following constraints when using this skill:**

#### Permitted Operations (Compliant)
Agents are ONLY permitted to perform:
1. **Delete files**: Execute user-authorized file deletion after calling `backup`
2. **Restore files**: Call `restore` to recover accidentally deleted files from backup
3. **List backups**: Call `list` to view available backups
4. **Clean backups**: Call `delete_backup` to remove specific outdated backups
5. **Undelete**: Call `restore` to recover mistakenly deleted files
6. **Verify backup integrity**: Call `verify` to check if backups have been tampered
7. **Manual cleanup**: Call `cleanup` to purge expired backups and logs

#### Prohibited Unsafe Operations (Absolutely Forbidden)
Agents are **ABSOLUTELY FORBIDDEN** from performing file tampering or path redirection via delete/restore operations:
1. **File content tampering**: Modifying file content during backup or restore
2. **Path redirection restore**: Restoring files to locations other than user-specified destinations (especially sensitive system directories)
3. **Path traversal attacks**: Using `..` or other traversal sequences to restore files outside the backup area
4. **Backup substitution attacks**: Replacing legitimate backups with malicious files then attempting to restore
5. **Bypassing security checks**: Using `--force` to skip security validations for files from unknown sources
6. **Unauthorized file deletion**: Deleting any file without explicit user authorization
7. **Log tampering**: Modifying, deleting, or forging operation logs to conceal unsafe behavior

#### Security Validation Requirements
- All `restore` operations MUST pass SHA256 integrity verification, PATH cross-validation, and path traversal detection
- Restore MUST be rejected with `SECURITY` level log if any validation fails
- Agents must NOT attempt to bypass, disable, or ignore any security validation mechanisms

## 安全机制（v0.4.0）/ Security Mechanisms (v0.4.0)

### 中文

### 备份完整性验证（SHA256）

- **backup 时**：计算备份文件的 SHA256，存入 `.sha256` 文件（v0.3.0 格式含 PATH 字段）
- **restore 时**：重新计算备份文件的 SHA256，与记录值比对
  - 不匹配 → 拒绝恢复，报告 SECURITY 级别日志
  - **SHA256 记录缺失或为空 → 拒绝恢复**（v0.3.0 修复了可绕过漏洞）
  - 防止攻击者备份正常文件后替换为恶意文件，再骗取恢复

### PATH 交叉验证（v0.3.0 新增）

- `.sha256` 文件中存储原始路径（`PATH:` 字段）
- restore 时：将 `.sha256` 中记录的路径与 `.path` 文件内容进行交叉验证
  - 不一致 → 拒绝恢复
  - 彻底防止攻击者单独篡改 `.path` 文件定向到任意位置

### `--force` 路径安全强制验证（v0.4.0 修复 A4）

- `--force` 参数原可跳过所有检查（删除 SHA256 + --force 即可绕过）
- **v0.4.0 修复：** `--force` 跳过 SHA256 存在性检查，但 PATH 交叉验证和路径遍历检测**永远执行**，即使 SHA256 记录不存在也不例外
- 关闭了"删除 SHA256 → --force → 完全绕过"这一攻击链路

### 日志注入防护（v0.3.0 已修复）

- `log()` 函数在写入日志前过滤 `\n`、`\r`、`[` 字符
- 防止通过 detail 参数注入伪造的日志行

### 路径遍历检测

- **restore 时**：检测路径中的 `..` 成分
  - resolve 后路径与原始路径不一致 → 拒绝恢复
  - 防止利用 `../` 遍历逃逸

### 安全事件日志

- 所有安全拦截事件记录为 `SECURITY` 级别日志，便于审计

### English

### Backup Integrity Verification (SHA256)

- **On backup**: Computes SHA256 of the backup file, stores in `.sha256` (v0.3.0 format includes PATH field)
- **On restore**: Recomputes SHA256 and compares — mismatch blocks restore with SECURITY log
  - **Missing or empty SHA256 record → restore blocked** (v0.3.0 fixes bypass vulnerability)
  - Prevents replacing backup with malicious file after backing up a legitimate one

### PATH Cross-Validation (NEW in v0.3.0)

- `.sha256` file stores the original path in a `PATH:` line
- On restore: cross-checks the path in `.sha256` against the `.path` file
  - Mismatch → restore blocked
  - Fully prevents attacker from tampering with `.path` to redirect restore elsewhere

### `--force` PATH Safety Enforcement (FIXED in v0.4.0 — A4)

- `--force` previously allowed bypassing all checks (delete SHA256 + --force = full bypass)
- **v0.4.0 fix:** `--force` bypasses SHA256 *existence* check, but PATH cross-validation and traversal detection **always run**, even when SHA256 record is absent
- Closes the "delete SHA256 → --force → complete bypass" attack chain

### Log Injection Prevention (FIXED in v0.3.0)

- `log()` function strips `\n`, `\r`, and `[` from detail before writing
- Prevents injecting fake log entries via a crafted detail parameter

### Path Traversal Detection

- **On restore**: Detects `..` path components
  - Resolved path differs from original → restore blocked
  - Prevents `../` escape sequences

### Security Event Logging

- All security blocks logged at `SECURITY` level for audit trail

## 自动清理规则 / Auto-Cleanup Rules

### 中文

| 类型 | 保留时间 | 说明 |
|------|---------|------|
| 备份文件夹 | 7天 | 超过7天的备份自动清理 |
| 日志文件 | 30天 | 超过30天的日志自动清理 |

脚本每次启动时自动执行清理，无需手动调用。

### English

| Type | Retention | Description |
|------|-----------|-------------|
| Backup folders | 7 days | Backups older than 7 days are auto-deleted |
| Log files | 30 days | Logs older than 30 days are auto-deleted |

## 文件结构 / File Structure

### 中文

```
skills/delete-recovery-0.4.0/
├── SKILL.md
├── log.txt                    ← 操作日志（30天自动清理），含 SECURITY 级别记录
├── delete_backup/              ← 备份文件存放处（7天自动清理）
│   ├── YYYYMMDDHHMM/          ← 时间戳文件夹
│   │   ├── C__Users__...      ← 备份文件
│   │   ├── C__Users__...path  ← 原始路径记录
│   │   ├── C__Users__...sha256 ← SHA256 完整性 + PATH 交叉验证记录（v0.3.0）
│   │   └── .restored           ← 已恢复文件清单（全部恢复后文件夹自动删除）
│   └── temp_existing/          ← 恢复时暂存已有文件
└── scripts/
    ├── delete_recovery.py      ← 核心脚本（含安全验证）
    └── safe_path.py            ← 路径安全验证模块（v0.4.0）
```

**`.path` 文件作用：** 每个备份文件旁边有一个同名 `.path` 文件，存储原始文件路径，用于恢复时定位目标位置。

**`.sha256` 文件作用（v0.3.0）：** 存储备份文件的 SHA256 哈希 + 原始路径（交叉验证用），防止备份被篡改后注入恶意文件。

### English

```
skills/delete-recovery-0.4.0/
├── SKILL.md
├── log.txt                            ← Operation logs (30-day auto-cleanup), SECURITY events
├── delete_backup/                     ← Backup storage (7-day auto-cleanup)
│   ├── YYYYMMDDHHMM/                 ← Timestamp folder
│   │   ├── C__Users__...             ← Backup file
│   │   ├── C__Users__...path         ← Original path record
│   │   ├── C__Users__...sha256       ← SHA256 + PATH cross-validation record (v0.3.0)
│   │   └── .restored                  ← Restored files manifest
│   └── temp_existing/                 ← Conflict files staged during recovery
└── scripts/
    ├── delete_recovery.py             ← Core script (with security checks)
    └── safe_path.py                   ← Path safety validator module (v0.4.0)
```

## 完整使用示例 / Full Usage Example

### 中文

**场景：用户要删除桌面上的 `report.docx`**

**Step 1：先备份**
```bash
python delete_recovery.py backup "C:\Users\user\Desktop\report.docx"
```

**Step 2：执行删除（由用户自行完成）**

**Step 3：用户误删后想恢复**
```bash
# 查看备份
python delete_recovery.py list
# 恢复（默认自动删除备份，恢复到原始位置）
python delete_recovery.py restore 202603261130 "C__Users__user__Desktop__report.docx"
# 如需保留备份，加上 --keep-backup
python delete_recovery.py restore 202603261130 "C__Users__user__Desktop__report.docx" --keep-backup
# 恢复 v0.3.0 之前的旧备份（无 SHA256 记录）
python delete_recovery.py restore 202603261130 "C__Users__user__Desktop__report.docx" --force
```

**Step 4：验证备份完整性**
```bash
python delete_recovery.py verify 202603261130 "C__Users__user__Desktop__report.docx"
```

### English

```bash
# 1. Backup before deletion
python delete_recovery.py backup "C:\Users\user\Desktop\report.docx"

# 2. User performs deletion (manually)

# 3. Accidentally deleted — restore
python delete_recovery.py restore 202603261130 "C__Users__user__Desktop__report.docx"
# With --keep-backup
python delete_recovery.py restore 202603261130 "C__Users__user__Desktop__report.docx" --keep-backup
# Force restore pre-v0.3.0 backup (no SHA256 record)
python delete_recovery.py restore 202603261130 "C__Users__user__Desktop__report.docx" --force

# 4. Verify backup integrity
python delete_recovery.py verify 202603261130 "C__Users__user__Desktop__report.docx"
```

## 安全加固说明 / Security Hardening

### 中文

本技能在以下攻击场景下提供保护：

| 攻击场景 | 防御方式 | v0.1.0 | v0.2.0 | v0.3.0 | v0.4.0 |
|---------|---------|--------|--------|--------|--------|
| 备份后替换文件内容 | SHA256 完整性验证 | ❌ | ✅ | ✅ | ✅ |
| 备份后替换 + 删除 SHA256 绕过检查 | SHA256 强制要求（缺失/为空拒绝恢复） | ❌ | ❌ | ✅ | ✅ |
| 篡改 .path 定向到其他目录 | PATH 交叉验证（.sha256 中 PATH 与 .path 对比） | ❌ | ❌ | ✅ | ✅ |
| 利用 `../` 路径遍历逃逸 | 路径遍历检测 | ❌ | ✅ | ✅ | ✅ |
| `--force` 跳过所有检查（A4） | `--force` 强制 PATH 验证（即使 SHA256 缺失） | ❌ | ❌ | ❌ | ✅ |
| 日志注入（A10） | detail 中过滤 `\n` `\r` `[` | ❌ | ❌ | ✅ | ✅ |

**说明：** 本技能安全防护依赖 SHA256 完整性 + PATH 交叉验证，而非限制恢复目标在特定目录内（`allowed_roots` 默认为空，不限制恢复路径范围）。这是因为作为恢复工具，需要支持将文件恢复到原始位置（可能在任意目录）。

### English

This skill provides protection against the following attack scenarios:

| Attack Scenario | Defense | v0.1.0 | v0.2.0 | v0.3.0 | v0.4.0 |
|----------------|---------|--------|--------|--------|--------|
| Replace backup with malicious file after backup | SHA256 integrity check | ❌ | ✅ | ✅ | ✅ |
| Replace backup + delete SHA256 to bypass | SHA256 strictly required (missing/empty blocks restore) | ❌ | ❌ | ✅ | ✅ |
| Tamper .path to redirect restore elsewhere | PATH cross-validation (.sha256 PATH vs .path file) | ❌ | ❌ | ✅ | ✅ |
| Use `../` traversal to escape backup area | Path traversal detection | ❌ | ✅ | ✅ | ✅ |
| `--force` bypasses all checks (A4) | `--force` still enforces PATH validation (even without SHA256) | ❌ | ❌ | ❌ | ✅ |
| Log injection (A10) | `\n`, `\r`, `[` stripped from detail | ❌ | ❌ | ✅ | ✅ |

**Note:** This skill's security relies on SHA256 integrity + PATH cross-validation, NOT on restricting restore destinations to a fixed directory tree (`allowed_roots` defaults to empty — no directory restriction). This is intentional: as a recovery tool, it must support restoring files to their original locations which may be anywhere on the filesystem.

## 注意事项 / Notes

### 中文

1. **删除前必备份**：所有删除操作前都应先调用 `backup`，防止误删
2. **恢复时目标冲突**：如果原位置已有文件，会自动将旧文件暂存到 `temp_existing/` 目录
3. **恢复后自动删备份**：默认情况下，恢复成功后会自动删除对应备份（多文件时等全部恢复完再清理）；使用 `--keep-backup` 可保留
4. **路径编码**：备份文件名将 `\`、`/`、`:` 替换为 `__`，恢复时需使用转换后的名称
5. **日志30天自动清理**：操作日志超过30天自动清理，无需手动处理
6. **v0.3.0+ 安全验证**：restore 时自动进行 SHA256 完整性 + PATH 交叉验证 + 遍历检测，如验证失败会明确报错
7. **旧备份恢复**：v0.3.0 之前的备份没有 SHA256 记录，使用 `restore --force` 可强制恢复（完整性检查跳过，但 PATH 验证和遍历检测仍然生效，**v0.4.0 起 PATH 验证不再可绕过**）

### English

1. **Always backup before deleting**: Call `backup` before any deletion
2. **Restore target conflict**: Existing files moved to `temp_existing/` before restoring
3. **Auto-delete backup after restore**: Default behavior (multi-file: all restored → then delete); use `--keep-backup` to retain
4. **Path encoding**: `\`, `/`, `:` replaced with `__` in backup filenames
5. **v0.3.0+ security checks**: Restore automatically fails with clear error if SHA256 integrity, PATH cross-validation, or path traversal check fails
6. **Legacy backup restore**: Pre-v0.3.0 backups lack SHA256 records; use `restore --force` to force restore (integrity check skipped, but PATH validation and traversal detection still apply — **PATH validation is non-bypassable from v0.4.0**)

# delete-recovery
