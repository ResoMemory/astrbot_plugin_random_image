# 随机二次元图片插件 - README
从 yppp.net 获取随机二次元图片，支持多张发送、方向偏好选择。

## 【功能】
- 发送随机二次元图片（横图/竖图/随机）
- 支持数量参数，上限 15 张
- 多张图片合并为一条消息发送
- 本地缓存 URL，减少 API 调用
- 分批发送，内存友好

## 【安装】
将插件放入 `AstrBot/data/plugins/` 目录，在 WebUI 中重载插件。

## 【使用】
示例：
- `/图图`      发送 1 张
- `/图图 3`    发送 3 张

## 【配置】
在 WebUI 插件配置中调整：
| 参数名         | 说明             | 默认值 |
| -------------- | ---------------- | ------ |
| max_count      | 单次最大数量     | 15     |
| default_count  | 默认数量         | 1      |
| orientation    | 方向偏好         | random |
| api_timeout    | 请求超时（秒）   | 10     |
| headers_json   | 自定义请求头     | User-Agent, Accept |

方向可选值：`random`（随机）/ `pc`（横屏）/ `pe`（竖屏）

## 【数据源】
yppp.net (https://api.yppp.net/)

## 【依赖】
aiohttp >= 3.8.0
