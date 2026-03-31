# GPUArchitect

GPUArchitect 是一个面向单机单卡 GPU 架构研究的本地优先研究工作流脚手架。它强调：

- 可复现实验
- 证据可追溯 claim
- append-only 历史记录
- 面向人和 agent 的知识输出
- 可在 workflow 中演化的 agent 输入结构

当前版本已经实现一个最小但完整的纵切面：

- 研究问题进入系统
- Planner 生成结构化实验规格
- Executor 运行受预算约束的 benchmark
- Analyzer 从原始输出提取 observation 并生成 claim candidate
- Verifier 做独立复验并给出 `accepted | disputed | pending`
- Curator 将结果写入 append-only 历史并生成知识库
- Next-step agent 生成下一步 workflow proposal

## 目录结构

- `src/gpu_research_agent/`：Python 工作流、schema、存储、CLI、站点生成
- `agent_runtime/`：基于 Codex SDK 的本地 agent runtime
- `workflow/`：当前启用的 workflow 定义，包括每个 agent 的输入结构
- `docs/`：架构文档
- `tests/`：测试
- `data/`：append-only 历史记录
- `knowledge/`：派生的 Markdown 知识库
- `exports/`：派生的 YAML 导出
- `site/`：派生的静态 dashboard

## 安装

1. 安装 Python 依赖：

```bash
uv pip install -e .
```

2. 安装本地 Codex runtime 依赖：

```bash
npm install --prefix agent_runtime
```

如果当前 shell 没有显式设置 `CODEX_API_KEY` 或 `OPENAI_API_KEY`，运行时还会默认尝试读取 `~/.codex/auth.json` 中同名字段。

## 初始化

```bash
gpuarchitect init
```

## 跑一轮研究

```bash
gpuarchitect run-round --question "How does the synthetic memory probe react to larger working sets?"
```

## 常用命令

- `gpuarchitect init`
- `gpuarchitect run-round --question "..."`
- `gpuarchitect verify-claim --claim-id <id>`
- `gpuarchitect rebuild-site`
- `gpuarchitect status`
- `gpuarchitect show-workflow`

## Agent 输入结构如何演化

agent 的输入结构不只存在于代码中，也存在于 `workflow/active.yaml` 中。每个角色都声明：

- `instructions`
- `context_sections`
- `sandbox_mode`
- `web_search_enabled`

运行时会按这些声明组装输入 payload。每轮计划目录下都会保存 `workflow_snapshot.yaml`，用于记录当时的 workflow 版本。

系统还允许 next-step proposal 提出：

- 哪个 role 的输入结构要改
- 为什么改
- 新的 `context_sections`
- 是否开 web search
- sandbox 模式
- 补充 instruction note

这些提案只会进入历史记录，不会自动修改 workflow。

## 知识库与历史记录的区别

这两者不是同一个东西。

### Append-only 历史记录

历史记录在 `data/` 下，是系统的事实来源，包括：

- `data/plans/`：问题、实验规格、workflow 快照、planner 输出、next-step proposal
- `data/runs/`：原始 stdout/stderr、analysis、verification、复验结果
- `data/records/*.jsonl`：结构化 append-only 日志

### 知识库

知识库在 `knowledge/` 和 `exports/knowledge.yaml` 下，是从历史中派生出的“整理后结果”，用于：

- 人类阅读
- 下游 agent 消费
- claim 导航和摘要查看

知识库可以重建，历史记录不应被覆盖。

## 架构文档

见 [docs/architecture.md](docs/architecture.md)。

## 当前限制

- 当前 benchmark 仍是 synthetic probe，不是真实 CUDA/profiler 实验
- 还没有长期运行调度器
- 还没有 workflow proposal 的审批与合并执行器
- 还没有 kernel backtesting loop

## 适合现在做什么

当前版本适合：

- 验证研究 workflow 是否闭环
- 验证 append-only 记录与知识导出是否分离
- 验证 Codex agent 角色输入结构是否可配置
- 为后续接入真实 CUDA experiment family 打基础

当前版本还不适合直接产出可信的 GPU 架构研究结论。

## 运行时调试输出

`gpuarchitect run-round` 在执行过程中会把关键阶段和 backend 信息打印到 `stderr`，包括：

- 当前 stage 是否开始/完成
- executor 退出码和耗时
- 各 agent 是否走 Codex SDK 还是 fallback
- Codex thread id 与事件数量

这样可以监控运行进度，同时不会破坏 `stdout` 上的 JSON 结果。
