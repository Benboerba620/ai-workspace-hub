# config

本地配置目录。

这里放 watchlist、工具参数、API key 示例副本等用户自己的配置。真实 API key 不应该提交到 GitHub；公开仓库里只保留模板或占位文件。

`config/pod2wiki.env` 目前是 Hub 的共享 LLM 配置，wiki 自动标签和 podcast 摘要共同读取它。文件名为兼容旧工作区保留；不要为两个功能复制两份 key。
