# 免费设备接入：Windows 候选与 Ubuntu 证据缺口

研究日期：2026-10-07。条件：软件免费、无 Mac、无付费开发者账号；普通 Apple 账户侧载仍待用户决定。本轮只读研究，未登录、注册、安装、侧载或连接手机。

## 结论

**已找到具体到源码和作者实机记录的 Windows 免费 Apple 账户 WDA 候选：SideTap。** 它值得进入设备技术验证，尚不能作为当前数独 App 已兼容的结论。纯 Ubuntu 首次取得免费签名资产、安装与运行的完整链仍缺证据；免费投屏也需要独立的代码输入通道。

## 免费 WDA 的新增依据

本轮固定 SideTap commit `bc43e6f56b199a28c44ca6f696fba42e5f2194a4`；许可为 MIT，免费核心流程可独立于可选扩展运行。[许可](https://github.com/ucsandman/SideTap/blob/bc43e6f56b199a28c44ca6f696fba42e5f2194a4/LICENSE)

真实 `signing.py` 的免费流程是：用户先在 Sideloadly 用普通 Apple 账户签名安装；读取 Windows `%APPDATA%/Sideloadly/key.pem` 与 `cert-*.pem`，用 OpenSSL 导出 P12；通过 pymobiledevice3 `MisagentService.copy_all()` 从手机读回 provisioning profile；检查有效期、UDID和App ID，再用 go-ios 重签整包。`device.py` 确实传递 `sign app --p12file --profile --bundleid --install`，随后启动 WDA并检查可达。[签名源码](https://github.com/ucsandman/SideTap/blob/bc43e6f56b199a28c44ca6f696fba42e5f2194a4/src/phone_harness/signing.py)、[设备调用源码](https://github.com/ucsandman/SideTap/blob/bc43e6f56b199a28c44ca6f696fba42e5f2194a4/src/phone_harness/device.py)

作者的 `ERRORS.md` 记录：2026-08-16，Sideloadly0.60 在 iOS26.6 完成安装后，WDA仍报测试包加载错误103；从手机取得7日profile再重签，11项检查通过。后续记录有重签后WDA响应，以及特定App可访问性调用挂起的实机问题。**这是同一作者的报告案例，与源码构成实现和案例两类证据；本轮没有复测，也没有独立兼容统计。**[作者实机记录](https://github.com/ucsandman/SideTap/blob/bc43e6f56b199a28c44ca6f696fba42e5f2194a4/docs/ERRORS.md)

作者把问题归因于 Sideloadly未签嵌套 `.xctest`，由 go-ios 深签修复。Sideloadly官网只证明普通IPA免费侧载和7日有效期；当前官网显示0.70.1，作者0.60的现象不能直接推广为新版行为。初次签名仍需用户向Apple认证；后续本地重签也沿用原profile有效期。[Sideloadly官方说明](https://sideloadly.io/)

## 产物、版本与平台条件

**产物准备仍有具体缺口。** SideTap setup让用户下载官方WDA `*.ipa`，固定commit的仓库没有该IPA，安装脚本也没有生成它。本轮官方WDA `v16.14.1`实际发布真机 `WebDriverAgentRunner-Runner.zip`；流水线以iOS真机、arm64、关闭签名构建。把当前ZIP封装为SideTap所需IPA，或使用go-ios支持的`.app`，必须核验目录、嵌套签名和最终安装结果。[SideTap setup](https://github.com/ucsandman/SideTap/blob/bc43e6f56b199a28c44ca6f696fba42e5f2194a4/docs/setup-windows.md)、[官方产物](https://github.com/appium/WebDriverAgent/releases/tag/v16.14.1)、[真机构建脚本](https://github.com/appium/WebDriverAgent/blob/v16.14.1/Scripts/ci/build-real.sh)

SideTap声明Windows10/11与iOS17+，具体案例集中在作者iOS26.6；当前Appium非macOS模式另要求iOS18+。pymobiledevice3的iOS17.0–17.3.1与17.4+隧道路径也不同。**iOS17、18、26应分别按所选工具核验，版本号本身不证明最新产物兼容。** 手机还需信任电脑、开启Developer Mode并重启确认，设备相关动作均未执行。[Appium范围](https://appium.github.io/appium-xcuitest-driver/11.17/guides/non-macos-hosts/)、[iOS17隧道](https://github.com/doronz88/pymobiledevice3/blob/90b8d44c83999db6c57e5fbcd5b796be5567de3f/docs/guides/ios17-tunnels.md)、[Apple开发者模式](https://developer.apple.com/documentation/xcode/enabling-developer-mode-on-a-device)

Apple确认免费Personal Team有7日profile及App/设备数量限制。SideTap读取证书的路径、驱动安装和若干进程管理步骤以Windows为主；Sideloadly官网仅列Windows/macOS下载。跨平台go-ios能使用已有资产，尚不证明Ubuntu能完成免费首次资产获取。[Apple免费账号限制](https://developer.apple.com/help/account/basics/developer-account-overview)

## 免费画面与独立输入

SideTap `capture.py`在WDA不可用时调用 `ios screenshot`；作者说明这需要开发者镜像和解锁，可先于App签名取画面，输入仍需要WDA。[截图源码](https://github.com/ucsandman/SideTap/blob/bc43e6f56b199a28c44ca6f696fba42e5f2194a4/src/phone_harness/capture.py)

UxPlay提供免费AirPlay画面接收；Apple支持AssistiveTouch鼠标输入。ESP32 BLE HID库的作者声称iOS26.3测试并提供点击/位移API。电脑串口→固件→BLE输入是可研究组合，尚未验证；它涉及外设和固件，不能由开源许可或投屏成功推出纯软件双向数独同步。[UxPlay](https://github.com/FDH2/UxPlay)、[Apple指针输入](https://support.apple.com/en-us/111775)、[BLE HID维护者项目](https://github.com/HijelHub/HijelHID_BLEMouse)

## 后续验证与完成状态

研究问题已回答：Windows有明确候选；Ubuntu全链、当前手机和数独App待验证。若用户选择普通Apple账户侧载，先核验手机版本、当前WDA产物、免费profile和一次可恢复点击，再检查数字与笔记读写及手机手动变化。若该条件未选定，继续已授权的棋盘识别与电脑端能力研究。

本轮系统代理读回仍为 `127.0.0.1:47891`，AnySearch code发现、检索和SideTap提取成功；固定commit源码均经同代理直接GET200。没有新增HTTP访问失败。对viewer.py产物关键词搜索无匹配（rg退出1），只作为未找到相关构建逻辑的范围证据；产物缺口结论结合仓库tree与安装脚本，未由单次零匹配推出全仓不存在能力。
