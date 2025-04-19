# 前端样式重构计划

## 项目概述
将体育非遗数字展示平台的CSS样式从单一的`style.css`文件重构为模块化的SCSS架构，提高代码可维护性和扩展性。

## 当前状态分析
- 项目使用单一的`style.css`文件，包含约2100行代码
- 项目基于Bootstrap 5框架，有大量自定义样式覆盖
- 项目有10个主要模板目录，共44个HTML模板文件
- 已有空的SCSS目录结构，但没有实际内容

## 目标
1. 将`style.css`中的样式按功能和组件拆分到SCSS文件中
2. 使用SCSS的嵌套、变量、混合器等特性使代码更易维护
3. 建立一个模块化的SCSS架构，便于后续扩展和维护
4. 确保所有模板文件的样式正确应用，不破坏现有功能

## SCSS文件结构
```
heritage_platform/app/static/scss/
├── main.scss                  # 主SCSS文件，导入所有其他文件
├── base/                      # 基础样式
│   ├── _reset.scss            # 重置和基础样式
│   ├── _typography.scss       # 排版样式
│   ├── _variables.scss        # 变量定义
│   ├── _mixins.scss           # 混合器
│   └── _responsive.scss       # 响应式混合器
├── components/                # 组件样式
│   ├── _buttons.scss          # 按钮样式
│   ├── _cards.scss            # 卡片样式
│   ├── _forms.scss            # 表单样式
│   ├── _badges.scss           # 徽章样式
│   ├── _alerts.scss           # 提醒样式
│   ├── _modals.scss           # 模态框样式
│   ├── _dropdowns.scss        # 下拉菜单样式
│   ├── _pagination.scss       # 分页样式
│   ├── _toast.scss            # Toast通知样式
│   ├── _gallery.scss          # 图片画廊样式
│   └── _stats.scss            # 统计卡片样式
├── layout/                    # 布局样式
│   ├── _header.scss           # 头部/导航栏样式
│   ├── _footer.scss           # 页脚样式
│   ├── _sidebar.scss          # 侧边栏样式
│   └── _bottom-nav.scss       # 底部导航栏样式
└── pages/                     # 页面特定样式
    ├── _home.scss             # 首页样式
    ├── _heritage.scss         # 非遗项目页面样式
    ├── _content.scss          # 内容页面样式
    ├── _forum.scss            # 论坛页面样式
    ├── _user.scss             # 用户页面样式
    ├── _message.scss          # 消息页面样式
    ├── _notification.scss     # 通知页面样式
    └── _auth.scss             # 认证页面样式
```

## 实施步骤

### 阶段1: 准备工作
- [x] 创建SCSS目录结构
- [x] 创建编译脚本`compile-scss.bat`
- [x] 创建基础变量文件`_variables.scss`，提取颜色、字体、间距等变量
- [x] 创建混合器文件`_mixins.scss`和`_responsive.scss`

### 阶段2: 基础样式迁移
- [x] 创建`_reset.scss`，迁移全局重置样式
- [x] 创建`_typography.scss`，迁移排版相关样式

### 阶段3: 组件样式迁移
- [x] 迁移按钮样式到`_buttons.scss`
- [x] 迁移卡片样式到`_cards.scss`
- [x] 迁移表单样式到`_forms.scss`
- [x] 迁移徽章样式到`_badges.scss`
- [x] 迁移提醒样式到`_alerts.scss`
- [x] 迁移模态框样式到`_modals.scss`
- [x] 迁移下拉菜单样式到`_dropdowns.scss`
- [x] 迁移分页样式到`_pagination.scss`
- [x] 迁移Toast通知样式到`_toast.scss`
- [x] 迁移图片画廊样式到`_gallery.scss`
- [x] 迁移统计卡片样式到`_stats.scss`

### 阶段4: 布局样式迁移
- [x] 迁移头部/导航栏样式到`_header.scss`
- [x] 迁移页脚样式到`_footer.scss`
- [x] 迁移侧边栏样式到`_sidebar.scss`
- [x] 迁移底部导航栏样式到`_bottom-nav.scss`

### 阶段5: 页面特定样式迁移
- [x] 迁移首页样式到`_home.scss`
- [x] 迁移非遗项目页面样式到`_heritage.scss`
- [x] 迁移内容页面样式到`_content.scss`
- [x] 迁移论坛页面样式到`_forum.scss`
- [x] 迁移用户页面样式到`_user.scss`
- [x] 迁移消息页面样式到`_message.scss`
- [x] 迁移通知页面样式到`_notification.scss`
- [x] 迁移认证页面样式到`_auth.scss`

### 阶段6: 集成与测试
- [x] 创建`main.scss`，导入所有SCSS文件
- [x] 编译SCSS为CSS
- [x] 修夌SCSS文件中的UTF-8编码问题
- [x] 修夌模板文件中的CSS引用，从`style.css`改为`main.css`
- [x] 添加缺失的头像样式
- [x] 修复英雄区背景图片路径问题
- [ ] 测试样式在各个页面的表现
- [ ] 修复可能出现的问题

### 阶段7: 优化与完善
- [x] 优化英雄区样式，提升视觉效果
- [ ] 优化其他SCSS代码，减少重复
- [ ] 添加注释，提高可读性
- [ ] 确保响应式设计在各种设备上正常工作
- [ ] 最终测试并部署

## 进度追踪

| 日期 | 完成的任务 | 备注 |
|------|------------|------|
| 2025/4/20 | 创建SCSS目录结构 | 已创建基本目录 |
| 2025/4/20 | 创建编译脚本 | 创建了compile-scss.bat脚本，并处理了中文编码问题 |
| 2025/4/20 | 创建基础变量和混合器文件 | 创建了_variables.scss、_mixins.scss和_responsive.scss |
| 2025/4/20 | 创建基础样式文件 | 创建了_reset.scss和_typography.scss |
| 2025/4/20 | 创建组件样式文件 | 创建了_buttons.scss、_cards.scss、_forms.scss、_badges.scss、_alerts.scss、_modals.scss、_dropdowns.scss、_pagination.scss、_toast.scss、_gallery.scss和_stats.scss |
| 2025/4/20 | 创建布局样式文件 | 创建了_header.scss、_footer.scss、_sidebar.scss和_bottom-nav.scss |
| 2025/4/20 | 创建页面特定样式文件 | 创建了_home.scss、_heritage.scss、_content.scss、_forum.scss、_user.scss、_message.scss、_notification.scss和_auth.scss |
| 2025/4/20 | 创建主样式文件 | 创建了main.scss，导入所有其他SCSS文件 |
| 2025/4/20 | 编译SCSS为CSS | 成功编译生成main.css文件 |
| 2025/4/20 | 修夌SCSS文件中的UTF-8编码问题 | 修夌了多个SCSS文件中的编码问题，并添加了正确的导入语句 |
| 2025/4/20 | 修夌模板文件中的CSS引用 | 将base.html中的style.css引用改为main.css |
| 2025/4/20 | 添加缺失的头像样式 | 创建了_avatars.scss文件，并添加了头像相关的样式 |
| 2025/4/20 | 修复英雄区背景图片问题 | 将背景图片设置为项目中已有的default-heritage.jpg，并修改首页模板文件使用自定义的hero-section类 |
| 2025/4/20 | 优化英雄区样式 | 增强英雄区的视觉效果，添加渐变背景、文字效果和动画 |
| 2025/4/20 | 进一步优化英雄区样式 | 使用clip-path创建非矩形形状，添加玻璃态效果，优化按钮和文字样式 |

## 注意事项
1. 保持与Bootstrap框架的兼容性
2. 确保样式迁移不破坏现有功能
3. 使用SCSS的@use和@forward代替已弃用的@import
4. 注意中文编码问题，确保编译脚本使用正确的编码
5. 编译前需要先安装Sass：`npm install -g sass`
6. 在SCSS文件中使用命名空间引用变量和混合器，例如`@include resp.respond-to('md')`
7. 确保所有HTML模板文件引用新的`main.css`文件，而不是原来的`style.css`
