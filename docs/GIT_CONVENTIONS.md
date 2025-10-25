# Git 提交规范

## 分支管理策略

### 主要分支

- **main**: 主分支，始终保持稳定可发布状态
- **develop**: 开发分支，日常开发的主要分支
- **release/***: 发布分支，用于版本发布准备
- **hotfix/***: 热修复分支，用于紧急bug修复

### 功能分支

- **feature/***: 功能开发分支
- **bugfix/***: bug修复分支
- **docs/***: 文档更新分支
- **refactor/***: 重构分支
- **test/***: 测试相关分支

### 分支命名规范

```
feature/模块名-功能描述
bugfix/issue编号-问题描述
docs/文档类型-更新内容
refactor/模块名-重构内容
test/测试类型-测试内容
```

**示例**:
```
feature/llm-openai-adapter
feature/tool-registry-system
bugfix/issue-123-memory-leak
docs/api-reference-update
refactor/planner-module-cleanup
test/integration-multi-agent
```

---

## Commit Message 规范

### 格式

遵循 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type 类型

| Type | 说明 | 示例 |
|------|------|------|
| feat | 新功能 | `feat(llm): add OpenAI streaming support` |
| fix | Bug修复 | `fix(memory): resolve context overflow issue` |
| docs | 文档更新 | `docs(readme): update installation guide` |
| style | 代码格式（不影响功能） | `style(core): format code with black` |
| refactor | 重构（不改变功能） | `refactor(tool): simplify registry logic` |
| perf | 性能优化 | `perf(rag): optimize embedding cache` |
| test | 测试相关 | `test(planner): add unit tests for decomposer` |
| build | 构建系统或依赖更新 | `build(deps): upgrade langchain to 0.1.0` |
| ci | CI/CD配置 | `ci(github): add automated testing workflow` |
| chore | 其他修改（不涉及src或test） | `chore(gitignore): add .env to ignore list` |
| revert | 回滚之前的commit | `revert: revert "feat(llm): add streaming"` |

### Scope 范围

按照项目模块划分：

- `core`: 核心模块
- `llm`: LLM相关
- `tool`: 工具系统
- `memory`: 记忆系统
- `rag`: RAG系统
- `planner`: 规划器
- `executor`: 执行器
- `multi-agent`: 多Agent
- `observability`: 可观测性
- `api`: API接口
- `cli`: 命令行工具
- `config`: 配置系统
- `deps`: 依赖管理
- `*`: 影响多个模块时使用

### Subject 主题

- 使用祈使句，现在时态
- 不要大写首字母
- 结尾不加句号
- 简明扼要（不超过50字符）
- 中英文均可，建议使用英文

**Good ✅**:
```
feat(llm): add support for Azure OpenAI
fix(memory): prevent duplicate entries in cache
docs(api): update tool registration examples
```

**Bad ❌**:
```
feat(llm): Added support for Azure OpenAI.  # 时态错误
Fix memory bug  # 缺少scope，首字母大写
update docs  # type错误，应该是docs
完善功能  # 描述不清晰
```

### Body 正文（可选）

- 详细描述修改内容
- 说明为什么做这个修改
- 与之前的实现有何不同
- 每行不超过72字符

示例：
```
feat(rag): implement query rewriting module

Add a query rewriting module to improve retrieval accuracy.
This module uses LLM to rephrase user queries before
vector search, which helps handle ambiguous or poorly
structured questions.

The implementation includes:
- Query expansion with synonyms
- Question normalization
- Multi-query generation for complex questions
```

### Footer 页脚（可选）

用于关联issue或注明破坏性变更：

```
Closes #123
Fixes #456
Refs #789

BREAKING CHANGE: The Tool.register() method signature has changed.
Migration: Use @tool decorator instead of manual registration.
```

---

## Commit 最佳实践

### 1. 提交频率

- ✅ 小步提交，每个commit只做一件事
- ✅ 功能完整时提交，确保每个commit可编译运行
- ❌ 避免"大杂烩"式提交
- ❌ 避免未完成功能提交到develop分支

### 2. 原子性

每个commit应该是独立、完整的单元：

```bash
# Good ✅
git commit -m "feat(llm): add OpenAI provider"
git commit -m "test(llm): add tests for OpenAI provider"
git commit -m "docs(llm): document OpenAI configuration"

# Bad ❌
git commit -m "add openai support and fix memory bug and update docs"
```

### 3. 关联性

相关的修改应该在一个commit中：

```bash
# Good ✅
# 一个commit包含函数修改和对应的测试更新
git add src/llm/base.py tests/llm/test_base.py
git commit -m "refactor(llm): simplify provider interface"

# Bad ❌
git commit -m "update base.py"
# ... (later)
git commit -m "update test"
```

### 4. 提交前检查

在提交前确保：

```bash
# 1. 代码格式化
black src/
isort src/

# 2. 代码检查
flake8 src/
mypy src/

# 3. 运行测试
pytest tests/

# 4. 查看修改内容
git diff --staged

# 5. 提交
git commit
```

---

## 工作流程

### 功能开发流程

```bash
# 1. 从develop创建功能分支
git checkout develop
git pull origin develop
git checkout -b feature/llm-openai-adapter

# 2. 开发过程中频繁提交
git add src/llm/providers/openai.py
git commit -m "feat(llm): add OpenAI provider base class"

git add src/llm/providers/openai.py
git commit -m "feat(llm): implement streaming for OpenAI"

git add tests/llm/test_openai.py
git commit -m "test(llm): add OpenAI provider tests"

# 3. 保持与develop同步
git fetch origin
git rebase origin/develop

# 4. 推送到远程
git push origin feature/llm-openai-adapter

# 5. 创建Pull Request
# 在GitHub/GitLab上创建PR，等待代码审查

# 6. 合并后删除分支
git checkout develop
git pull origin develop
git branch -d feature/llm-openai-adapter
```

### Bug修复流程

```bash
# 1. 从develop创建bugfix分支
git checkout develop
git pull origin develop
git checkout -b bugfix/issue-123-memory-leak

# 2. 修复bug并提交
git add src/memory/working.py
git commit -m "fix(memory): resolve memory leak in context cache

The cache was not properly clearing expired entries,
causing memory to grow unbounded over time.

Closes #123"

# 3. 添加测试
git add tests/memory/test_working.py
git commit -m "test(memory): add regression test for cache cleanup"

# 4. 推送并创建PR
git push origin bugfix/issue-123-memory-leak
```

### 紧急热修复流程

```bash
# 1. 从main创建hotfix分支
git checkout main
git pull origin main
git checkout -b hotfix/critical-security-issue

# 2. 快速修复
git add src/tools/sandbox.py
git commit -m "fix(tool): patch security vulnerability in sandbox

SECURITY: Prevents arbitrary code execution through
tool parameter injection.

Fixes #999"

# 3. 合并到main和develop
git checkout main
git merge --no-ff hotfix/critical-security-issue
git tag -a v1.0.1 -m "Security hotfix"
git push origin main --tags

git checkout develop
git merge --no-ff hotfix/critical-security-issue
git push origin develop

# 4. 删除hotfix分支
git branch -d hotfix/critical-security-issue
```

---

## Pull Request 规范

### PR标题

格式与commit message保持一致：

```
feat(llm): add Azure OpenAI support
fix(memory): resolve context overflow
docs(api): update tool system documentation
```

### PR描述模板

```markdown
## 描述
简要描述这个PR的目的和内容

## 变更类型
- [ ] 新功能 (feat)
- [ ] Bug修复 (fix)
- [ ] 文档更新 (docs)
- [ ] 代码重构 (refactor)
- [ ] 性能优化 (perf)
- [ ] 测试 (test)
- [ ] 构建/依赖 (build)
- [ ] CI/CD (ci)
- [ ] 其他 (chore)

## 变更内容
- 添加了XXX功能
- 修复了XXX问题
- 重构了XXX模块

## 测试
- [ ] 添加了单元测试
- [ ] 添加了集成测试
- [ ] 手动测试通过
- [ ] 所有现有测试通过

## 相关Issue
Closes #123
Refs #456

## 截图（如适用）
<!-- 添加截图或GIF演示 -->

## 检查清单
- [ ] 代码遵循项目规范
- [ ] 已添加必要的测试
- [ ] 已更新相关文档
- [ ] 所有测试通过
- [ ] 代码已经过self-review
- [ ] 已添加必要的注释
```

### PR审查规范

审查者应该检查：

- ✅ 代码质量和可读性
- ✅ 测试覆盖率
- ✅ 是否遵循项目规范
- ✅ 是否有安全隐患
- ✅ 性能影响
- ✅ 文档完整性

---

## Git Hooks

### Pre-commit Hook

在`.git/hooks/pre-commit`中配置：

```bash
#!/bin/bash

echo "Running pre-commit checks..."

# 代码格式化
echo "Formatting code..."
black src/
isort src/

# 代码检查
echo "Linting code..."
flake8 src/
if [ $? -ne 0 ]; then
    echo "Flake8 check failed. Please fix the issues."
    exit 1
fi

# 类型检查
echo "Type checking..."
mypy src/
if [ $? -ne 0 ]; then
    echo "Type check failed. Please fix the issues."
    exit 1
fi

# 运行测试
echo "Running tests..."
pytest tests/ -v
if [ $? -ne 0 ]; then
    echo "Tests failed. Please fix the issues."
    exit 1
fi

echo "All checks passed!"
```

### Commit-msg Hook

在`.git/hooks/commit-msg`中配置：

```bash
#!/bin/bash

commit_msg=$(cat "$1")

# 检查commit message格式
if ! echo "$commit_msg" | grep -qE "^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\(.+\))?: .{1,50}"; then
    echo "Error: Invalid commit message format"
    echo "Format: <type>(<scope>): <subject>"
    echo "Example: feat(llm): add OpenAI support"
    exit 1
fi

echo "Commit message format is valid"
```

---

## 常用命令速查

```bash
# 查看状态
git status

# 查看差异
git diff
git diff --staged

# 暂存修改
git add <file>
git add .

# 提交
git commit -m "feat(llm): add new feature"
git commit --amend  # 修改上一次commit

# 分支操作
git branch  # 查看本地分支
git branch -a  # 查看所有分支
git checkout -b <branch>  # 创建并切换分支
git branch -d <branch>  # 删除分支

# 同步更新
git fetch origin
git pull origin develop
git rebase origin/develop

# 撤销操作
git reset HEAD <file>  # 取消暂存
git checkout -- <file>  # 放弃工作区修改
git reset --soft HEAD~1  # 撤销commit，保留修改
git reset --hard HEAD~1  # 撤销commit，放弃修改

# 查看历史
git log --oneline --graph
git log --author="name"
git log --since="2 weeks ago"

# 储藏工作
git stash  # 储藏当前工作
git stash pop  # 恢复储藏
git stash list  # 查看储藏列表

# 标签
git tag v1.0.0
git push origin --tags
```

---

## 常见问题

### 如何修改最后一次commit？

```bash
# 修改commit message
git commit --amend -m "new message"

# 添加遗漏的文件
git add forgotten_file
git commit --amend --no-edit
```

### 如何合并多个commit？

```bash
# 交互式rebase最近3个commit
git rebase -i HEAD~3

# 在编辑器中将要合并的commit标记为squash或fixup
# 保存后按提示操作
```

### 如何解决冲突？

```bash
# 1. 拉取最新代码产生冲突
git pull origin develop

# 2. 查看冲突文件
git status

# 3. 手动解决冲突，编辑文件

# 4. 标记为已解决
git add <resolved-file>

# 5. 继续操作
git rebase --continue
# 或
git merge --continue
```

### 如何回滚某个commit？

```bash
# 创建新的commit来回滚
git revert <commit-hash>

# 回滚最近的commit
git revert HEAD
```

---

**最后更新**: 2025-10-25
**维护者**: Rookie Agent Team
