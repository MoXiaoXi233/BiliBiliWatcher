# BiliBiliWatcher

BiliBiliWatcher 是一个用于监控 B 站直播状态的插件。
但是功能没写完，没时间搞，先放着

## 安装

配置完成 [QChatGPT](https://github.com/RockChinQ/QChatGPT) 主程序后使用管理员账号向机器人发送命令即可安装：

```
!plugin get https://github.com/MoXiaoXi233/BiliBiliWatcher
```
或查看详细的[插件安装说明](https://github.com/RockChinQ/QChatGPT/wiki/5-%E6%8F%92%E4%BB%B6%E4%BD%BF%E7%94%A8)

## 功能
监控指定的 Bilibili 用户的直播状态  
在用户开播或结束直播时通知指定的用户和群组（暂时不可用）  
动态添加或删除监控的 Bilibili 用户 UID  
动态添加或删除通知的用户和群组  
查看当前监控的 Bilibili 用户和通知列表  

## 使用
### 查看当前直播状态
发送：
```
直播状态
```
### 添加UID <UID>
例如：
```
添加UID 12345678
删除UID 12345678
```
添加和删除通知用户
### 添加通知用户
例如：
```
添加通知用户 123456
删除通知用户 123456
```
### 添加和删除通知群组
例如：
```
添加通知群组 654321
删除通知群组 654321
```
### 查看通知列表
```
查看通知列表: 查看通知列表
```
