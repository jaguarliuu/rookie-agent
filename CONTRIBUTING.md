# 贡献指南

感谢你对 Rookie Agent 项目的关注！我们欢迎所有形式的贡献。

## 行为准则

请阅读并遵守我们的 [行为准则](CODE_OF_CONDUCT.md)。

## 如何贡献

### 报告 Bug

如果你发现了 bug，请：

1. 检查 [Issue](https://github.com/your-org/rookie-agent/issues) 中是否已有相关报告
2. 如果没有，创建新的 Issue，包含：
   - 清晰的标题和描述
   - 复现步骤
   - 期望行为 vs 实际行为
   - 环境信息（Python版本、操作系统等）
   - 相关代码片段或错误信息

### 提出新功能

1. 先在 [Discussions](https://github.com/your-org/rookie-agent/discussions) 中讨论
2. 获得认可后创建 Issue 详细说明
3. 等待维护者反馈

### 提交代码

#### 开发流程

1. **Fork 项目**
   ```bash
   # 点击 GitHub 上的 Fork 按钮
   git clone https://github.com/YOUR-USERNAME/rookie-agent.git
   cd rookie-agent
   ```

2. **设置开发环境**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements-dev.txt
   pre-commit install
   ```

3. **创建分支**
   ```bash
   git checkout -b feature/your-feature-name
   ```

4. **编写代码**
   - 遵循 [代码规范](docs/CODE_STYLE.md)
   - 编写测试
   - 更新文档

5. **运行测试**
   ```bash
   pytest tests/
   black src/ tests/
   flake8 src/ tests/
   mypy src/
   ```

6. **提交更改**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```
   遵循 [Git 提交规范](docs/GIT_CONVENTIONS.md)

7. **推送并创建 PR**
   ```bash
   git push origin feature/your-feature-name
   # 在 GitHub 上创建 Pull Request
   ```

#### Pull Request 指南

- 填写完整的 PR 模板
- 确保所有测试通过
- 保持 PR 小而专注
- 及时回应审查意见
- 保持代码库整洁

### 代码审查

所有代码都需要经过审查才能合并：

- 至少一位维护者批准
- 所有 CI 检查通过
- 无未解决的对话
- 文档完整

## 开发指南

### 项目结构

详见 [项目结构文档](docs/PROJECT_STRUCTURE.md)

### 代码规范

详见 [代码规范](docs/CODE_STYLE.md)

### 测试规范

- 所有新功能必须有测试
- 测试覆盖率应 >80%
- 使用有意义的测试名称
- 遵循 AAA 模式（Arrange-Act-Assert）

### 文档规范

- 公共 API 必须有 docstring
- 复杂逻辑需要注释说明
- 新功能需要更新相关文档
- 使用清晰的 Markdown 格式

## 发布流程

（仅限维护者）

1. 更新版本号
2. 更新 CHANGELOG.md
3. 创建 release 分支
4. 测试验证
5. 合并到 main
6. 打标签并发布

## 获取帮助

- 查看 [文档](docs/)
- 在 [Discussions](https://github.com/your-org/rookie-agent/discussions) 提问
- 加入我们的社区

## 许可证

贡献的代码将采用与项目相同的 [MIT](LICENSE) 许可证。

---

再次感谢你的贡献！
