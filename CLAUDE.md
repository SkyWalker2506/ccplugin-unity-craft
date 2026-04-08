# ccplugin-unity-craft

Claude Code plugin for CRAFT — safe Unity scene manipulation via MCP tools.

## Bu plugin ne yapar

Unity MCP uzerinden sahne islemleri yapilirken CRAFT tool'larini kullanmasi icin Claude'u yonlendirir. SKILL.md icinde:
- Transaction-safe islem yapma kurallari
- Tool usage patterns (Create, Modify, Delete, Query, Rollback)
- Error handling ve response format

## Dependency

- Unity projede `com.skywalker.craft` package'i kurulu olmali
- Unity MCP bridge aktif olmali (`com.unity.ai.assistant`)

## Install

```bash
./install.sh
```
