# Ruo Flutter App

Ruo AI 智能投顾系统 - Flutter 移动端

## 📱 项目概述

这是 Ruo AI 智能投顾系统的 Flutter 移动端应用,提供股票行情查询、持仓管理、AI 新闻分析等功能。

## 🚀 快速开始

### 环境要求

- Flutter SDK >= 3.0.0
- Dart SDK >= 3.0.0
- iOS: Xcode >= 14.0
- Android: Android Studio >= 2022.1

### 安装 Flutter (macOS)

```bash
# 1. 下载 Flutter SDK
cd ~/development
git clone https://github.com/flutter/flutter.git -b stable

# 2. 配置环境变量
echo 'export PATH="$PATH:$HOME/development/flutter/bin"' >> ~/.zshrc
source ~/.zshrc

# 3. 验证安装
flutter doctor

# 4. 接受 Android 许可
flutter doctor --android-licenses
```

### 项目安装

```bash
# 1. 进入项目目录
cd frontend/ruo_app

# 2. 安装依赖
flutter pub get

# 3. 运行项目
flutter run
```

## 📁 项目结构

```
lib/
├── main.dart                    # 应用入口
├── app.dart                     # 应用配置
├── config/                      # 配置文件
│   ├── theme.dart               # 主题配置
│   ├── constants.dart           # 常量定义
│   └── routes.dart              # 路由配置
├── models/                      # 数据模型
│   ├── stock.dart               # 股票模型
│   ├── portfolio.dart           # 持仓模型
│   └── news.dart                # 新闻模型
├── services/                    # 服务层
│   ├── api_service.dart         # API 服务基类
│   ├── stock_service.dart       # 股票服务
│   ├── portfolio_service.dart   # 持仓服务
│   └── news_service.dart        # 新闻服务
├── providers/                   # 状态管理 (Provider)
│   ├── portfolio_provider.dart  # 持仓状态
│   ├── stock_provider.dart      # 股票状态
│   └── news_provider.dart       # 新闻状态
├── screens/                     # 页面
│   ├── home/                    # 首页
│   │   ├── home_screen.dart
│   │   └── widgets/
│   ├── portfolio/               # 持仓页
│   │   ├── portfolio_screen.dart
│   │   └── widgets/
│   ├── stock_detail/            # 股票详情页
│   │   ├── stock_detail_screen.dart
│   │   └── widgets/
│   ├── news/                    # 新闻页
│   │   ├── news_screen.dart
│   │   └── widgets/
│   └── add_portfolio/           # 添加持仓页
│       └── add_portfolio_screen.dart
└── widgets/                     # 公共组件
    ├── stock_card.dart          # 股票卡片
    ├── portfolio_card.dart      # 持仓卡片
    ├── news_card.dart           # 新闻卡片
    └── profit_indicator.dart    # 盈亏指示器
```

## 🎨 主要功能

### 1. 首页 (持仓列表)
- ✅ 显示所有持仓股票
- ✅ 实时盈亏计算
- ✅ 总市值/总盈亏统计
- ✅ 下拉刷新

### 2. 添加持仓
- ✅ 股票搜索(自动补全)
- ✅ 输入成本价和股数
- ✅ 选择策略标签(打板/低吸/趋势)
- ✅ 表单验证

### 3. 股票详情
- ✅ 实时行情展示
- ✅ K 线图(日/周/月)
- ✅ 持仓信息
- ✅ 盈亏分析

### 4. 新闻资讯
- ✅ 个股新闻列表
- ✅ AI 情感分析标签
- ✅ 新闻详情查看

## 🔧 技术栈

- **框架**: Flutter 3.0+
- **语言**: Dart 3.0+
- **状态管理**: Provider
- **网络请求**: dio
- **图表**: fl_chart
- **本地存储**: shared_preferences
- **UI 组件**: Material Design 3

## 📦 依赖包

```yaml
dependencies:
  flutter:
    sdk: flutter

  # 状态管理
  provider: ^6.1.1

  # 网络请求
  dio: ^5.4.0

  # 图表
  fl_chart: ^0.65.0

  # 本地存储
  shared_preferences: ^2.2.2

  # 下拉刷新
  pull_to_refresh: ^2.0.0

  # 加载指示器
  flutter_spinkit: ^5.2.0

  # 日期时间
  intl: ^0.18.1
```

## 🌐 API 配置

在 `lib/config/constants.dart` 中配置后端 API 地址:

```dart
class ApiConstants {
  static const String baseUrl = 'http://localhost:8300/api/v1';

  // 或使用实际服务器地址
  // static const String baseUrl = 'https://your-domain.com/api/v1';
}
```

## 🎯 开发指南

### 运行开发服务器

```bash
# 运行在 iOS 模拟器
flutter run -d ios

# 运行在 Android 模拟器
flutter run -d android

# 运行在 Chrome (Web)
flutter run -d chrome
```

### 构建发布版本

```bash
# iOS
flutter build ios --release

# Android
flutter build apk --release
flutter build appbundle --release
```

## 📖 使用说明

1. **启动后端 API**
   ```bash
   cd backend
   uvicorn main:app --reload --port 8300
   ```

2. **配置 API 地址**
   - 修改 `lib/config/constants.dart` 中的 `baseUrl`
   - iOS 模拟器使用: `http://localhost:8300`
   - Android 模拟器使用: `http://10.0.2.2:8300`

3. **运行 App**
   ```bash
   flutter run
   ```

## 🐛 常见问题

### Flutter 未找到
```bash
# 确保添加到 PATH
export PATH="$PATH:$HOME/development/flutter/bin"
```

### iOS 构建失败
```bash
# 更新 CocoaPods
cd ios
pod install
cd ..
```

### Android 许可未接受
```bash
flutter doctor --android-licenses
```

## 📝 下一步计划

- [ ] 添加用户登录/注册
- [ ] 集成图表库展示 K 线
- [ ] 添加消息推送
- [ ] 优化 UI/UX 设计
- [ ] 添加暗黑模式

## 🤝 贡献

欢迎提交 Issue 和 Pull Request!

## 📄 许可证

MIT License

---

**Ruo - 让 AI 成为您的投资副驾!** 🚀
