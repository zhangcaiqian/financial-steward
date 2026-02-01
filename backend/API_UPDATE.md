# AKShare API 更新说明

## 问题描述

在运行示例时遇到错误：`module 'akshare' has no attribute 'macro_china_m1'`

这是因为 AKShare 库已经更新了API接口名称和数据格式。

## 已修复的API变更

### 1. M1/M2 货币供应量

**旧接口（已废弃）：**
```python
ak.macro_china_m1()  # ❌ 不存在
ak.macro_china_m2()  # ❌ 不存在
```

**新接口：**
```python
ak.macro_china_money_supply()  # ✅ 统一的货币供应量接口
```

**数据格式：**
```python
列名: ['月份', '货币和准货币(M2)-数量(亿元)', '货币和准货币(M2)-同比增长', 
      '货币和准货币(M2)-环比增长', '货币(M1)-数量(亿元)', '货币(M1)-同比增长', 
      '货币(M1)-环比增长', '流通中的现金(M0)-数量(亿元)', 
      '流通中的现金(M0)-同比增长', '流通中的现金(M0)-环比增长']
```

### 2. PMI 制造业采购经理指数

**旧接口：**
```python
ak.macro_china_pmi()
# 返回数据需要筛选: df[df['指标'] == '制造业']
```

**新接口（相同名称，但数据格式变化）：**
```python
ak.macro_china_pmi()  # ✅ 接口名称未变，但返回格式改变
```

**数据格式：**
```python
列名: ['月份', '制造业-指数', '制造业-同比增长', '非制造业-指数', '非制造业-同比增长']
# 不再需要筛选，直接包含制造业和非制造业数据
```

### 3. 社会融资规模

**旧接口（已废弃）：**
```python
ak.macro_china_shrzgm()  # ❌ 不存在
```

**新接口：**
```python
ak.macro_china_new_financial_credit()  # ✅ 新增信贷数据
```

**数据格式：**
```python
列名: ['月份', '当月', '当月-同比增长', '当月-环比增长', '累计', '累计-同比增长']
# 使用'累计-同比增长'作为社融趋势指标
```

### 4. CPI/PPI 价格指数

**旧接口：**
```python
ak.macro_china_cpi()  # 需要筛选
ak.macro_china_ppi()  # 需要筛选
```

**新接口：**
```python
ak.macro_china_cpi_yearly()  # ✅ CPI年率（同比）
ak.macro_china_ppi_yearly()  # ✅ PPI年率（同比）
```

**数据格式：**
```python
列名: ['商品', '日期', '今值', '预测值', '前值']
# '今值'即为同比数据
```

## 代码修改总结

### collector.py 主要修改

1. **get_m1_m2()**: 改用 `macro_china_money_supply()`
2. **get_pmi()**: 适配新的数据格式，不再需要筛选
3. **get_shrzgm()**: 改用 `macro_china_new_financial_credit()`
4. **get_cpi_ppi()**: 改用 `macro_china_cpi_yearly()` 和 `macro_china_ppi_yearly()`

### analyzer.py 主要修改

1. **analyze_shrzgm_trend()**: 适配新的社融数据列名（'社融同比'）

## 测试结果

✅ 所有数据接口测试通过：
- M1/M2 数据获取成功
- PMI 数据获取成功
- 社融数据获取成功
- CPI/PPI 数据获取成功
- GDP 数据获取成功

✅ 完整示例运行成功，经济周期判断正常

## 当前AKShare版本

```
AKShare版本: 1.18.8
```

## 注意事项

1. **数据列名变化**：新接口的列名更加规范和详细
2. **数据格式统一**：不再需要通过筛选'指标'列来获取特定数据
3. **向后兼容性**：旧代码需要更新才能使用新版本的AKShare

## 相关资源

- [AKShare 官方文档](https://akshare.akfamily.xyz/)
- [AKShare GitHub](https://github.com/akfamily/akshare)

## 更新日期

2026-01-08

