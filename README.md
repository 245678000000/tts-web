# TTS 网页版（本机使用）

这是一个面向小白的中文 TTS 小工具：把文字粘贴到网页，点击按钮即可生成语音并下载 MP3。

## 1) 安装依赖

```bash
python3 -m pip install -r requirements.txt
```

## 2) 启动网页

```bash
python3 web_app.py
```

启动后打开浏览器访问：`http://127.0.0.1:5000`

## 3) 页面功能

- 输入文本（支持长文本自动分段）
- 选择音色、风格、语速、音调
- 生成后可直接试听和下载 MP3

## 4) 保留命令行脚本

原有命令行方式继续可用：

```bash
python3 main.py
```

## 5) 常见问题

- 如果提示网络错误：请先检查本机网络是否可访问 Azure 接口。
- 如果返回参数错误：确认语速/音调范围在 `-100 ~ 100`。
- 如果页面打不开：确认 `python web_app.py` 正在运行且端口 `5000` 未被占用。

## 6) 部署到 Vercel

本项目已包含 `vercel.json` 和 `api/index.py`，可直接部署为 Vercel Python 服务。

你可以用 Codex 的部署脚本一键发布（会返回预览地址和认领地址）：

```bash
bash /Users/tiantian/.codex/skills/vercel-deploy/scripts/deploy.sh /Users/tiantian/Desktop/TTS
```
