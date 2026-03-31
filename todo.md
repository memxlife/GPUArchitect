# to think by human, ai agent don't follow this

- 整理代码结构，能够在独立 workspace 运行，包括 agent workflow 修改。要不直接创个 branch 跑。
- 取消 fallback，确保运行稳定性。
- 考虑替换 agent 架构，用更轻量可控的 pi 之类，codex 仅作为前期测试。
- 优化 prompt ，约束具体行为，控制 workflow 修改强度和行为，文档导出格式等。
- 把联网搜索或者 deepresearch 独立出来作为 stage，明确行为和可预测性
- 网页前后端架构/框架优化/美化
- 结构化 workflow 行为（权限和 prompt），方便自迭代
- stdout做的漂亮一点，现在太难看懂了
- 可能需要一个高层的任务控制，避免在某些topic 上钻牛角尖
- 给 stdout 增加一个简化模式或者沉默模式，不然太长
