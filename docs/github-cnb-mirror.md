# GitHub 主仓库与 CNB 自动镜像

本项目采用单向同步：

```text
本地与各类 AI Agent → GitHub（唯一主仓库）→ GitHub Actions → CNB（只读镜像）
```

日常只向 GitHub 的 `origin` 提交和推送。不要在 CNB 网页直接修改镜像仓库，也不要为 CNB 配置反向同步，以免两边产生分叉或循环覆盖。

## 固定地址

- GitHub 主仓库：`https://github.com/leeperfect/PeopleDailyMaterial.git`
- CNB 镜像仓库：`https://cnb.cool/PerfectAcademy.Pro/PeopleDailyMaterial.git`
- 自动同步流程：`.github/workflows/sync_to_cnb.yml`
- GitHub Secret：`CNB_TOKEN`

## 首次启用

### 1. 创建空的 CNB 镜像仓库

在 `PerfectAcademy.Pro` 组织下创建普通仓库 `PeopleDailyMaterial`。仓库应保持为空，不要初始化 README；建议使用私有可见性，并明确标注“GitHub 自动镜像，请勿直接编辑”。

### 2. 创建 CNB 最小权限访问令牌

在 CNB 个人设置中创建仅能向上述仓库写入代码的访问令牌。当前令牌名称为 `GitHub Actions - PeopleDailyMaterial 镜像`，资源范围仅限 `PerfectAcademy.Pro/PeopleDailyMaterial`，只有 `repo-code` 读写权限，不具备仓库删除、设置、Issue、PR、组织或制品权限。

当前令牌于 2026 年 11 月 18 日 23:59:59 过期。到期前应在 CNB 重新生成同等最小权限令牌，并通过 GitHub 的 `CNB_TOKEN` 编辑入口替换；旧令牌确认不再使用后再撤销。不要把令牌写入本地文件、聊天、提交记录或工作流正文。

### 3. 把令牌保存到 GitHub Actions Secret

进入 GitHub 仓库：

`Settings → Secrets and variables → Actions → New repository secret`

名称固定填写 `CNB_TOKEN`，值填写上一步生成的 CNB 令牌。

### 4. 首次同步

把本工作流合并到 GitHub 后，任意一次 push 都会触发同步；也可以在 GitHub 的 `Actions → Sync GitHub to CNB → Run workflow` 手动执行。

## 日常使用

所有 AI Agent 继续使用普通 Git 命令：

```bash
git pull
git add <文件>
git commit
git push origin <当前分支>
```

GitHub push 成功后，CNB 同步在云端异步执行，不增加本地 Git 操作的等待时间。工作流监听所有分支和标签推送，并按 GitHub 状态强制刷新 CNB 镜像。

## 本地应急通道

只有 GitHub 网络异常且确实需要临时把已提交内容送到 CNB 时，才使用本地 `cnb` remote：

```bash
git remote add cnb https://cnb.cool/PerfectAcademy.Pro/PeopleDailyMaterial.git
git push cnb <当前分支>
git push cnb --tags
```

应急 push 后，GitHub 仍是唯一事实源。网络恢复后先把同一提交推到 GitHub，再手动运行一次镜像工作流。不要从 CNB 向 GitHub 反推。

## 状态反馈

- GitHub 仓库的 Actions 页面显示每次同步的成功、失败、耗时和日志。
- 成功标准：工作流为绿色，并且 CNB 对应分支的最新 commit SHA 与 GitHub 完全一致。
- 失败不会影响已经完成的 GitHub push；修复后可在 Actions 页面点击 `Re-run jobs`。

## 验证命令

公开仓库或已配置本机凭据时，可比较远端 SHA：

```bash
git ls-remote origin refs/heads/main
git ls-remote cnb refs/heads/main
```

两行开头的 40 位 commit SHA 应一致。还应抽查标签：

```bash
git ls-remote --tags origin
git ls-remote --tags cnb
```

## 异常处理

1. `Authentication failed`：检查 GitHub 的 `CNB_TOKEN` 是否存在、过期，以及 CNB 令牌是否有目标仓库写权限。
2. `Repository not found`：检查 CNB 仓库是否已创建，组织和仓库名大小写是否与工作流一致。
3. `non-fast-forward`：说明 CNB 镜像被单独修改。确认 GitHub 内容正确后重新运行工作流；工作流的 `PLUGIN_FORCE=true` 会以 GitHub 为准覆盖分叉。
4. 标签缺失：检查日志中的 tag push；当前工作流已设置 `PLUGIN_PUSH_TAGS=true`。
5. 同步任务拥堵：同一时间只运行一个镜像任务，后续 push 会排队，最终以较新的 GitHub 状态为准。
6. Git LFS 文件缺失：普通 Git 同步不等于 LFS 对象迁移。需要在 CNB 单独启用 LFS，并增加 LFS 对象同步与验证。

## 扩展到其他项目

复制工作流后只需修改 `PLUGIN_TARGET_URL`。每个 GitHub 项目使用独立的 CNB 仓库和独立 Secret；如后续仓库数量较多，再集中制作可复用工作流，统一管理版本和权限。
