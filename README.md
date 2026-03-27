# delete-recovery v0.4.0

### 中文

文件删除安全网——备份、恢复、SHA256完整性校验、路径交叉验证、全自动清理。

### English

A safety net for file deletion — backup, recovery, SHA256 integrity verification, path cross-validation, and fully automatic cleanup.

---

### 中文

一款轻量的 OpenClaw skill，在删除文件前自动将其备份到带时间戳的文件夹。**v0.4.0 修复了 `--force` 可绕过 PATH 交叉验证的安全漏洞（A4）**，配合 v0.3.0 的 SHA256 强制校验 + PATH 交叉验证，形成完整的安全防护体系。误删后一键恢复，过期备份和日志全自动清理，无需人工干预。

### English

A lightweight OpenClaw skill that automatically backs up files to timestamped folders before deletion. **v0.4.0 fixes the `--force` bypass vulnerability in PATH cross-validation (A4)**, combining with v0.3.0's mandatory SHA256 integrity checks and PATH cross-validation to form a complete security defense system. Recover accidentally deleted files with one click, and expired backups and logs are automatically cleaned up without manual intervention.

---

## 功能特性 / Features

### 中文

- **删除前自动备份** — 删除任何文件前，自动备份到带时间戳的文件夹
- **SHA256 强制校验（v0.3.0 修复）** — 备份时计算哈希，恢复时验证；SHA256 记录缺失或为空时 restore 默认阻止
- **PATH 交叉验证（v0.3.0 新增）** — `.sha256` 文件中绑定原始路径，恢复时双向交叉验证，彻底防止 `.path` 文件被篡改定向到任意位置
- **`--force` 路径安全强制验证（v0.4.0 修复 A4）** — `--force` 跳过 SHA256 存在性检查，但 PATH 交叉验证和路径遍历检测永远执行，即使 SHA256 记录不存在也不例外
- **日志注入防护（v0.3.0 已修复）** — detail 中过滤 `\n`、`\r`、`[`，防止伪造日志行
- **路径遍历防护** — 检测 `../` 逃逸序列，拒绝恢复目标超出合法范围
- **一键恢复** — 将误删文件恢复到原始位置
- **多文件安全处理** — 同一备份文件夹含多文件时，须全部恢复完毕才删除备份
- **自动清理** — 备份7天后自动删除，日志30天后自动删除，完全自动化
- **冲突保护恢复** — 恢复时若目标位置已有文件，自动移到 `temp_existing/` 暂存
- **完整操作日志** — 每次备份、恢复、清理、安全拦截操作均有记录（含 SECURITY 级别）
- **`--force` 恢复旧备份（v0.3.0 新增）** — 对 v0.3.0 之前创建的旧备份（无 SHA256 记录），可用 `--force` 强制恢复（SHA256 存在性跳过，但 PATH 验证和遍历检测永远生效，v0.4.0 起不可绕过）

### English

- **Automatic backup before deletion** — Automatically backs up any file to a timestamped folder before deletion
- **Mandatory SHA256 integrity check (fixed in v0.3.0)** — Computes hash during backup and verifies during recovery; missing or empty SHA256 record now blocks restore by default
- **PATH cross-validation (NEW in v0.3.0)** — SHA256 file stores FILE_HASH + PATH; restore performs cross-check between `.sha256` record and `.path` file, fully preventing `.path` redirection attacks
- **`--force` PATH safety enforcement (FIXED in v0.4.0 — A4)** — `--force` bypasses SHA256 *existence* check, but PATH cross-validation and traversal detection always run, even when SHA256 record is absent
- **Log injection prevention (fixed in v0.3.0)** — `\n`, `\r`, `[` stripped from detail, preventing fake log entries
- **Path traversal protection** — Detects `../` escape sequences and blocks restores outside the valid directory range
- **One-click recovery** — Restores accidentally deleted files to their original location
- **Multi-file safe handling** — When a backup folder contains multiple files, all must be restored before deleting the backup
- **Automatic cleanup** — Backups are deleted after 7 days and logs after 30 days, fully automated
- **Conflict-protected recovery** — If a file already exists at the restore destination, it is automatically moved to `temp_existing/` for staging
- **Complete operation logs** — Every backup, restore, cleanup, and security interception operation is logged (including SECURITY level)
- **`--force` for legacy backups (NEW in v0.3.0)** — Use `--force` to restore pre-v0.3.0 backups that lack SHA256 records (SHA256 existence check bypassed; PATH validation and traversal detection always run and are non-bypassable from v0.4.0)

---

## 安装方式 / Installation

### 中文

### 通过 ClawdHub 安装（推荐）

```bash
# 安装最新版（v0.4.0）
clawdhub install delete-recovery

# 安装指定版本
clawdhub install delete-recovery --version 0.4.0
```

### 手动安装

将 `delete-recovery-0.4.0` 文件夹复制到本地 Agent 的 OpenClaw workspace 的 `skills/` 目录下。

### English

### Install via ClawdHub (Recommended)

```bash
# Install latest version (v0.4.0)
clawdhub install delete-recovery

# Install specific version
clawdhub install delete-recovery --version 0.4.0
```

### Manual Installation

Copy the `delete-recovery-0.4.0` folder to the `skills/` directory in your local Agent's OpenClaw workspace.

---

## 快速开始 / Quick Start

### 中文

### 1. 删除前备份

```bash
python delete_recovery.py backup <file_path> [original_path]
```

```bash
# 示例
python delete_recovery.py backup "C:\Users\user\Desktop\report.docx"
# → {"ok": true, "folder": "202603261130", "file": "C__Users__user__Desktop__report.docx"}
```

### 2. 恢复误删文件

```bash
python delete_recovery.py restore <backup_folder> <safe_name> [--keep-backup] [--force]
```

```bash
python delete_recovery.py restore 202603261130 "C__Users__user__Desktop__report.docx"
# → {"ok": true, "restored_to": "C:\\Users\\user\\Desktop\\report.docx", "backup_deleted": true}

# 恢复 v0.3.0 之前的旧备份（无 SHA256 记录）
python delete_recovery.py restore 202603261130 "C__Users__user__Desktop__report.docx" --force
```

### 3. 验证备份完整性

```bash
python delete_recovery.py verify <backup_folder> <safe_name>
```

不执行恢复，仅检查备份文件是否被篡改（SHA256 完整性 + PATH 交叉验证）。

### 4. 查看所有备份

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

### 1. Backup Before Deletion

```bash
python delete_recovery.py backup <file_path> [original_path]
```

```bash
# Example
python delete_recovery.py backup "C:\Users\user\Desktop\report.docx"
# → {"ok": true, "folder": "202603261130", "file": "C__Users__user__Desktop__report.docx"}
```

### 2. Restore Accidentally Deleted Files

```bash
python delete_recovery.py restore <backup_folder> <safe_name> [--keep-backup] [--force]
```

```bash
python delete_recovery.py restore 202603261130 "C__Users__user__Desktop__report.docx"
# → {"ok": true, "restored_to": "C:\\Users\\user\\Desktop\\report.docx", "backup_deleted": true}

# Restore pre-v0.3.0 backup (no SHA256 record) using --force
python delete_recovery.py restore 202603261130 "C__Users__user__Desktop__report.docx" --force
```

### 3. Verify Backup Integrity

```bash
python delete_recovery.py verify <backup_folder> <safe_name>
```

Does not perform recovery. Checks SHA256 integrity AND PATH cross-validation to detect any tampering.

### 4. List All Backups

```bash
python delete_recovery.py list
```

### 5. Manually Delete Specified Backup

```bash
python delete_recovery.py delete_backup <backup_folder>
```

### 6. Manually Trigger Cleanup

```bash
python delete_recovery.py cleanup
```

### 7. View Operation Logs

```bash
python delete_recovery.py log [lines]
```

---

## 安全机制详解（v0.4.0）/ Security Mechanisms Explained (v0.4.0)

### 中文

### 场景1：备份被替换

攻击者先备份一个正常文件，然后用恶意文件替换备份目录中的文件，诱导恢复。

**防御：** backup 时计算 SHA256 并存储；restore 时验证哈希，不匹配则拒绝恢复。即使攻击者删除了 `.sha256` 文件，restore 也会被阻止（除非使用 `--force`，但 PATH 验证和遍历检测仍然生效，v0.4.0 起不可绕过）。

### 场景2：.path 文件被篡改

攻击者修改 `.path` 文件内容，将恢复目标指向系统目录（如 `C:\Windows\System32\evil.exe`）。

**防御：** v0.3.0 新增 `.sha256` 文件中的 PATH 字段。restore 时读取 `.sha256` 中存储的原始路径，与 `.path` 文件内容进行交叉验证，二者不一致则拒绝恢复。

### 场景3：SHA256 记录被删除绕过

攻击者直接删除或置空 `.sha256` 文件，试图绕过完整性检查。

**防御：** v0.3.0 修复此漏洞——SHA256 记录缺失或为空时，restore 默认阻止并报错，不再跳过完整性检查。唯一出口是 `--force`，但 PATH 交叉验证和遍历检测永远执行，v0.4.0 起不可绕过。

### 场景4：路径遍历

攻击者在目标路径中构造 `../../../dangerous/evil.exe`，试图逃逸到合法目录范围外。

**防御：** `_is_path_safe()` 检测 `..` 成分，resolve 后路径不在合法范围则拒绝。

### English

### Scenario 1: Backup Replaced

An attacker first backs up a normal file, then replaces the file in the backup directory with a malicious one to induce recovery.

**Defense:** Compute and store SHA256 during backup; verify hash during restore and reject if mismatched. If the attacker also deletes the `.sha256` file, restore is still blocked by default (unless `--force` is used, and PATH validation and traversal detection always run and are non-bypassable from v0.4.0).

### Scenario 2: .path File Tampered

An attacker modifies the `.path` file content to point the restore target to a system directory (e.g., `C:\Windows\System32\evil.exe`).

**Defense:** v0.3.0 stores the original path in the `.sha256` file (in the `PATH:` line). On restore, the path from `.sha256` is cross-checked against the `.path` file — any mismatch is blocked.

### Scenario 3: SHA256 Record Deleted to Bypass Check

An attacker deletes or empties the `.sha256` file to bypass integrity checks.

**Defense:** v0.3.0 fixes this — missing or empty SHA256 record now blocks restore by default. The only escape hatch is `--force`, but PATH cross-validation and traversal detection always run and are non-bypassable from v0.4.0.

### Scenario 4: Path Traversal

An attacker constructs `../../../dangerous/evil.exe` in the target path to escape outside the allowed directory.

**Defense:** `_is_path_safe()` detects `..` components and rejects if the resolved path is outside the valid range.

---

## SHA256 文件格式（v0.3.0）/ SHA256 File Format (v0.3.0)

### 中文

`.sha256` 文件采用结构化格式，同时存储文件哈希和原始路径：

```
#v3
FILE_HASH:9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08
PATH:C:\Users\user\Desktop\report.docx
```

- **`#v3`**：格式版本号，用于未来兼容升级
- **`FILE_HASH:`**：备份文件的 SHA256 哈希（64位十六进制）
- **`PATH:`**：备份时的原始文件路径（与 `.path` 文件内容一致，用于交叉验证）

### English

The `.sha256` file uses a structured format that stores both the file hash and original path:

```
#v3
FILE_HASH:9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08
PATH:C:\Users\user\Desktop\report.docx
```

- **`#v3`**: Format version marker for future compatibility
- **`FILE_HASH:`**: SHA256 hash of the backup file (64 hex characters)
- **`PATH:`**: Original file path at backup time (mirrors `.path` file; used for cross-validation)

---

## 文件结构 / File Structure

### 中文

```
delete-recovery-0.4.0/
├── SKILL.md                          — Skill 定义
├── README.md                          — 使用指南（本文）
├── CLAWDHUB.md                        — ClawdHub 发布元数据
├── log.txt                            — 操作日志（30天自动清理）
├── delete_backup/                     — 备份存储（7天自动清理）
│   ├── YYYYMMDDHHMM/                — 时间戳备份文件夹
│   │   ├── C__Users__...            — 备份文件
│   │   ├── C__Users__...path         — 原始路径记录
│   │   ├── C__Users__...sha256       — SHA256 完整性 + PATH 交叉验证记录（v0.3.0）
│   │   └── .restored                 — 已恢复文件清单
│   └── temp_existing/                 — 恢复时暂存冲突文件
└── scripts/
    ├── delete_recovery.py            — 核心脚本（含安全验证）
    └── safe_path.py                  — 路径安全验证模块（v0.4.0）
```

### English

```
delete-recovery-0.4.0/
├── SKILL.md                          — Skill definition
├── README.md                          — User guide (this document)
├── CLAWDHUB.md                        — ClawdHub publishing metadata
├── log.txt                            — Operation logs (auto-cleaned after 30 days)
├── delete_backup/                     — Backup storage (auto-cleaned after 7 days)
│   ├── YYYYMMDDHHMM/                — Timestamped backup folder
│   │   ├── C__Users__...            — Backup file
│   │   ├── C__Users__...path         — Original path record
│   │   ├── C__Users__...sha256       — SHA256 + PATH cross-validation record (v0.3.0)
│   │   └── .restored                 — Restored files manifest
│   └── temp_existing/                 — Conflict files staged during recovery
└── scripts/
    ├── delete_recovery.py            — Core script (with security checks)
    └── safe_path.py                  — Path safety validation module (v0.4.0)
```

---

## 工作流程 / Workflow

### 中文

```
用户决定删除文件
        │
        ▼
  ① backup 命令          ← 第一步必须做（v0.3.0 自动生成 SHA256 + PATH 记录）
        │
        ▼
  ② 用户执行删除操作
        │
        ▼（后续如需恢复）
  ③ restore 命令         ← v0.3.0+：完整性 + PATH 交叉验证 + 遍历检测（v0.4.0 起 PATH 验证不可绕过）
        │
        ▼
  备份自动删除            ←（除非使用了 --keep-backup）
```

### English

```
User decides to delete file
        │
        ▼
  ① backup command    ← Must do first (v0.3.0 auto-generates SHA256 + PATH record)
        │
        ▼
  ② User performs deletion
        │
        ▼（If recovery needed later）
  ③ restore command ← v0.3.0+: integrity + PATH cross-validation + traversal detection
        │              (PATH validation is non-bypassable from v0.4.0)
        ▼
  Backup auto-deleted  ←（Unless --keep-backup is used）
```

---

## 依赖环境 / Dependencies

### 中文

- Python 3.6+
- OpenClaw 1.0+（含 skill 支持）

### English

- Python 3.6+
- OpenClaw 1.0+ (with skill support)

---

## 更新日志 / Changelog

### 中文

### v0.4.0（2026-03-27） — 当前版本

**安全修复：**

- 【A4 修复 — 关键】`--force` 参数不再能绕过所有检查 — SHA256 缺失时，PATH 交叉验证和路径遍历检测**永远执行**，关闭了"删除 SHA256 → --force → 完全绕过"这一攻击链路
- 【A10 说明】日志注入防护（`\n` `\r` `[` 过滤）已在 v0.3.0 代码中存在，渗透测试时针对的是更早版本，当前版本不受影响

**完整变更：**
- `safe_path.py`：重写 `verify_integrity_and_path()` 中 SHA256 缺失分支，新增"无 SHA256 时强制 PATH 安全验证"逻辑，版本升至 v0.3.1
- `delete_recovery.py`：版本注释同步更新至 v0.4.0
- 更新 SKILL.md / README.md

### v0.3.0（2026-03-27） — 上一版本

**安全修复：**

- 【最关键】SHA256 记录改为**强制要求** — 缺失或为空时 restore **默认阻止**，修复了"删除 `.sha256` 文件即可绕过完整性检查"的严重漏洞
- 【安全增强】`.sha256` 文件新增 `PATH:` 行 — restore 时双向交叉验证 `.sha256` 中存储的路径与 `.path` 文件内容，彻底防止 `.path` 篡改攻击
- 【Bug 修复】修复 `allowed_roots` 死代码 — `allowed_roots=[]`（空列表）现正确表示"无路径限制"（不再误判为禁止所有路径）
- 【安全调整】`allowed_roots` 默认为空 — 安全防护主要依赖完整性 + 路径交叉验证，而非固定目录限制，更适合恢复工具的实际场景
- 【接口变更】restore 新增 `--force` 参数 — 跳过 SHA256 存在性检查，用于强制恢复 v0.3.0 之前的旧备份（路径验证仍生效）
- 【Bug 修复】`verify` 命令新增 PATH 交叉验证结果 — 同时报告 hash_match 和 path_match 两个检查的结果
- 【安全修复】日志注入防护 — `log()` 函数过滤 detail 中的 `\n`、`\r`、`[`

**完整变更：**
- `safe_path.py`：完全重写 `verify_integrity_and_path()`，新增 `write_sha256_file()` / `read_sha256_file()`，格式改为 `#v3 / FILE_HASH: / PATH:`
- `delete_recovery.py`：集成新版安全 API，`--force` 参数，`verify` 返回 path_match
- 更新 SKILL.md / README.md / CLAWDHUB.md

### v0.2.0（2026-03-26）— 更早版本

- 新增 `safe_path.py` 路径安全验证模块
- backup 时自动计算并存储 SHA256 哈希（`.sha256` 文件）
- restore 时验证备份完整性（SHA256 比对），完整性不符拒绝恢复
- restore 时验证恢复路径（防止 `.path` 篡改 + 路径遍历）
- 所有安全拦截事件记录为 `SECURITY` 级别日志
- 新增 `verify` 命令：手动检查备份完整性（不执行恢复）
- 新增 `safe_path.py` 独立工具：可单独调用 `compute <file_path>` 计算 SHA256

### v0.1.0（2026-03-26）— 初始版本

- 基础备份/恢复/清理功能
- 7天自动清理备份，30天自动清理日志
- 多文件批量恢复保护
- 冲突保护恢复

### English

### v0.4.0 (2026-03-27) — Current Version

**Security fixes:**

- 【A4 fix — Critical】`--force` can no longer bypass all checks — When SHA256 is absent, PATH cross-validation and traversal detection **always run**, closing the "delete SHA256 → --force → complete bypass" attack chain
- 【A10 note】Log injection prevention (`\n` `\r` `[` stripping) was already present in v0.3.0 code; the penetration test targeted an earlier version

**Complete changes:**
- `safe_path.py`: Rewrote the SHA256-absent branch in `verify_integrity_and_path()`, added mandatory PATH safety validation when SHA256 is missing, version bumped to v0.3.1
- `delete_recovery.py`: Version comment updated to v0.4.0
- Updated SKILL.md / README.md

### v0.3.0 (2026-03-27) — Previous Version

**Security fixes:**

- 【Critical】SHA256 record is now **STRICTLY REQUIRED** — missing or empty SHA256 blocks restore by default, fixing the critical bypass vulnerability where deleting `.sha256` disabled integrity checks
- 【Security enhancement】`.sha256` file now stores `PATH:` line — restore performs cross-check between the path stored in `.sha256` and the `.path` file, fully preventing `.path` redirection attacks
- 【Bug fix】Fixed `allowed_roots` dead code — `allowed_roots=[]` (empty list) now correctly means "no restriction" (previously falsely blocked all paths)
- 【Security adjustment】`allowed_roots` defaults to empty — primary security comes from integrity + path cross-validation rather than fixed directory restrictions
- 【Interface change】restore command gains `--force` flag — bypasses SHA256 existence check to restore pre-v0.3.0 backups (path validation still applies)
- 【Bug fix】`verify` command now reports PATH cross-validation result — returns both hash_match and path_match
- 【Security fix】Log injection prevention — `log()` strips `\n`, `\r`, `[` from detail

**Complete changes:**
- `safe_path.py`: Fully rewritten `verify_integrity_and_path()`, new `write_sha256_file()` / `read_sha256_file()`, format changed to `#v3 / FILE_HASH: / PATH:`
- `delete_recovery.py`: Integrated new security API, `--force` flag, `verify` returns path_match
- Updated SKILL.md / README.md / CLAWDHUB.md

### v0.2.0 (2026-03-26) — Earlier Version

- Added `safe_path.py` path safety validation module
- SHA256 hash computed and stored on backup (`.sha256` file)
- Restore verifies SHA256 integrity — blocks restore if hash mismatch
- Restore validates destination path — prevents `.path` tampering and path traversal
- All security blocks logged at `SECURITY` level
- Added `verify` command: manually check backup integrity without restoring
- Added `safe_path.py` standalone tool: `python safe_path.py compute <file>`

### v0.1.0 (2026-03-26) — Initial Version

- Basic backup/restore/cleanup functionality
- 7-day auto backup cleanup, 30-day auto log cleanup
- Multi-file batch recovery protection
- Conflict-protected recovery

---

### 中文

*如有问题或建议，欢迎反馈！*

### English

*For questions or suggestions, feedback is welcome!*
