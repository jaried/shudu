# 核验无 Mac 和开发者账号的免费设备接入

Type: research
Mode: AFK
Labels: wayfinder:research
Status: resolved
Assignee: Codex ios_research
Parent: ../map.md
Blocked by:

## Question

在软件免费、没有开发者账号和 Mac 的条件下，现有工具能否读取 iPhone 画面并用代码点击、滑动、输入数字与切换笔记？分别核验普通 Apple 账户免费侧载 WDA 的签名/安装/运行证据，以及免费投屏与独立输入通道。允许普通 Apple 账户侧载属于待用户决定的条件，本票只读研究。

研究区分：上游文档声明、维护者源码路径、发布产物、已报告真机案例和本用户实测。取得目标设备前，仅形成版本条件与证据缺口，不宣布兼容。

## Comments

通用研究已确认官方 WDA 真机预编译包和跨平台运行工具存在。此前有证据的 go-ios 签名路线要求签名资产，普通 IPA 免费侧载尚未证明 WDA 嵌套 XCTest runner 可用。

## Answer

研究已完成，见 [免费设备接入研究](../research/free-device-control.md)。本轮新增明确 Windows 候选 SideTap，固定 commit `bc43e6f56b199a28c44ca6f696fba42e5f2194a4`：免费流程从 Sideloadly 本机证书/私钥和手机 profile 取得资产，通过 go-ios 深签 WDA；作者记录 iOS26.6、Sideloadly0.60 的安装失败、重签恢复和 WDA 响应。许可证、真实调用源码、官方 WDA 发布产物与作者报告案例已分别核验。

当前官方 WDA 真机 ZIP 与 SideTap 文档预期 IPA 存在准备缺口；新版 Sideloadly、当前手机、目标数独 App、Ubuntu免费首次签名全链均未验证。Status resolved 表示研究问题已回答和证据缺口已定位；普通 Apple 账户侧载仍待用户决定，设备接入和双向同步尚未实施或验收。保留软件免费条件，后续按所选候选执行设备技术验证。
