# 更新日志

## [1.0.1] - 2026-01-08

### 🐛 Bug修复
- 修复 AKShare API 接口变更导致的数据获取失败问题
- 修复可视化模块中的数据格式错误
- 适配 AKShare 1.18.8+ 版本的新接口

### 🔄 API更新
- **M1/M2**: `macro_china_m1/m2()` → `macro_china_money_supply()`
- **社融**: `macro_china_shrzgm()` → `macro_china_new_financial_credit()`
- **CPI/PPI**: 改用 `macro_china_cpi_yearly()` 和 `macro_china_ppi_yearly()`
- **PMI**: 适配新的数据格式，不再需要筛选'指标'列

### 📝 文档更新
- 新增 `API_UPDATE.md` - API变更详细说明
- 新增 `CHANGELOG.md` - 版本更新日志
- 更新 `README.md` - 添加API版本说明

### ✅ 测试结果
- 所有数据采集接口测试通过
- 示例程序运行成功
- 经济周期判断功能正常

---

## [1.0.0] - 2026-01-08

### 🎉 初始版本
- 实现宏观经济数据采集器
- 实现经济周期分析器
- 实现自动监控系统
- 实现数据可视化模块
- 支持5种经济周期判断（强复苏、弱复苏、弱衰退、强衰退、混沌期）
- 提供资产配置建议
- 支持定时任务和报告生成

