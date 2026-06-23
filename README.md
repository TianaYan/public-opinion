# 个人舆情监控系统

> 自用、免费、自动化的多平台舆情监控小工具。

## ⚡ 5 分钟部署到线上(免费)

### 一、准备 GitHub 仓库

1. 注册 GitHub(https://github.com)
2. 创建新仓库 `public-opinion`,**选 Private**(私有)
3. 把这个项目推到 GitHub(下面有命令)

### 二、部署后端到 Render(免费)

1. 访问 https://render.com,用 GitHub 登录
2. 右上角 **New +** → **Blueprint**
3. 选你的 `public-opinion` 仓库
4. Render 自动读取 `render.yaml`,点击 **Apply**
5. 等 5-10 分钟部署完成
6. 拿到后端 URL,形如 `https://opinion-backend-xxxx.onrender.com`
7. (可选)Environment → 加 `DEEPSEEK_API_KEY` 环境变量,启用 AI 情感分析

### 三、部署前端到 Vercel(免费)

1. 访问 https://vercel.com,用 GitHub 登录
2. **Add New...** → **Project** → 选 `public-opinion` 仓库
3. **Framework Preset** 选 `Other`
4. **Root Directory** 填 `frontend`
5. 点击 **Deploy**
6. 拿到前端 URL,形如 `https://public-opinion-xxx.vercel.app`

### 四、联调(让前端连上后端)

打开 `frontend/index.html`,把第 281 行附近:

```js
const DEPLOYED_API = "";  // ← 改成你的 Render URL
```

改成:

```js
const DEPLOYED_API = "https://opinion-backend-xxxx.onrender.com";
```

然后 `git push`,Vercel 自动重新部署。

### 五、搞定!

打开你的 Vercel URL,就能用全网都能访问的舆情监控系统了。

---

## 💻 本地开发

### 1. 安装 Python 3.10+

去 [python.org](https://www.python.org/downloads/) 下载安装,Windows 安装时记得勾 **"Add to PATH"**。

### 2. 安装依赖

```powershell
cd public-opinion\backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3. 配置环境变量(可选,推荐)

```powershell
copy ..\.env.example ..\.env
notepad ..\.env
```

**DeepSeek API key 获取**(2 分钟):
1. 访问 https://platform.deepseek.com/
2. 注册并实名
3. 左侧菜单 "API Keys" → "Create new secret key"
4. 复制 key,粘贴到 `.env` 的 `DEEPSEEK_API_KEY=sk-xxx`
5. 免费额度:注册送 ¥10

### 4. 启动后端

```powershell
cd public-opinion\backend
.\venv\Scripts\Activate.ps1
python main.py
```

### 5. 启动前端(新开终端)

```powershell
cd public-opinion\frontend
python -m http.server 3000
```

浏览器打开 **http://127.0.0.1:3000**

---

## ⚙️ 详细部署步骤(从零开始)

### 步骤 1:安装 Git

Windows: https://git-scm.com/download/win

### 步骤 2:配置 Git

```powershell
git config --global user.name "你的名字"
git config --global user.email "你的邮箱@example.com"
```

### 步骤 3:创建 GitHub 仓库

1. 打开 https://github.com/new
2. Repository name: `public-opinion`
3. 选 **Private**(私有)
4. **不要**勾选 "Add a README file"
5. 点击 **Create repository**

### 步骤 4:推送代码

```powershell
cd C:\Users\严添辰\.mavis\agents\coder\workspace\public-opinion
git init
git add .
git commit -m "feat: 初始版本"
git branch -M main
git remote add origin https://github.com/你的用户名/public-opinion.git
git push -u origin main
```

> 推送时输入 GitHub 用户名 + Personal Access Token(不是密码)。
> 怎么获取 Token:GitHub → Settings → Developer settings → Personal access tokens → Generate new token → 勾 `repo`

### 步骤 5:Render 部署

1. 访问 https://render.com → Sign Up → Sign in with GitHub
2. 右上角 **New +** → **Blueprint**
3. 选 `public-opinion` 仓库
4. 看到自动识别到 `render.yaml`,点 **Apply**
5. 等构建完成(看 Logs 标签)
6. 成功后页面顶部会显示 URL:`https://opinion-backend-xxxx.onrender.com`
7. **第一次访问会慢 30-50 秒**(免费档冷启动)

### 步骤 6:Vercel 部署前端

1. 访问 https://vercel.com → Sign Up → Continue with GitHub
2. **Add New...** → **Project**
3. **Import** `public-opinion` 仓库
4. **Configure Project**:
   - Framework Preset: **Other**
   - Root Directory: 点 **Edit** → 填 `frontend`
5. 点 **Deploy**
6. 等 1-2 分钟,会显示 Vercel URL

### 步骤 7:联调

把 `frontend/index.html` 第 281 行:

```js
const DEPLOYED_API = "https://opinion-backend-xxxx.onrender.com";
```

替换成你 Render 给的 URL,保存,`git push`,等 Vercel 自动重新部署。

### 步骤 8:打开你的 Vercel URL

跨设备、跨网络都能用!

---

## 🗂 项目结构

```
public-opinion/
├── backend/                  # FastAPI 后端
│   ├── main.py               # 入口(支持 PORT 环境变量)
│   ├── config.py
│   ├── db.py
│   ├── analyzer.py
│   ├── scheduler.py
│   ├── crawlers/
│   │   ├── weibo.py
│   │   ├── zhihu.py
│   │   ├── bilibili.py
│   │   └── baidu.py
│   ├── requirements.txt
│   └── runtime.txt
├── frontend/                 # 单 HTML 前端
│   └── index.html
├── data/                     # SQLite 数据(部署时持久化)
├── render.yaml               # Render 部署配置
├── vercel.json               # Vercel 部署配置
├── Procfile                  # Heroku 风格部署
├── .env.example              # 环境变量模板
├── .gitignore
└── README.md
```

---

## 数据源说明

| 平台 | 数据源 | 实时性 | 是否需要登录 |
|---|---|---|---|
| B 站 | bilibili.com 公开 API | ⭐⭐⭐ | ❌ |
| 微博 | **百度 site:weibo.com** | ⭐⭐ | ❌ |
| 知乎 | **百度 site:zhihu.com** | ⭐⭐ | ❌ |
| 小红书 | **百度 site:xiaohongshu.com** | ⭐⭐ | ❌ |
| 抖音 | **百度 site:douyin.com** | ⭐⭐ | ❌ |

**为什么小红书/抖音/微博/知乎走百度?**
这些平台反爬极严,直接抓要登录且易封号。利用百度的索引能力,用 `site:xxx.com 关键词` 拿到相关内容,代价是只能拿到摘要前 200 字,无法拿到点赞评论。

---

## 常见问题

### Q: 部署后第一次访问很慢?

A: Render 免费档 15 分钟无访问会休眠,首次访问要 30-50 秒冷启动。点击"立即抓取"后会保持活跃。

### Q: SQLite 数据会丢吗?

A: 配了 Render Disk(1GB 免费),数据持久化。免费档休眠重启也不会丢。

### Q: DeepSeek API 怎么配?

A: Render Dashboard → 你的服务 → Environment → Add Environment Variable:
- Key: `DEEPSEEK_API_KEY`
- Value: `sk-xxxxxxxx`

不配也能用(规则模式情感分析)。

### Q: 多久抓取一次?

A: 默认 30 分钟一轮。在 `backend/config.py` 或 Render Environment 改 `CRAWL_INTERVAL` 环境变量(秒)。

### Q: 数据合规吗?

A:
- 微博/知乎/B 站:只抓公开页面,无登录,**合规**
- 百度:搜索结果是百度主动给你看的,**合规**
- 数据仅做个人研究,不要二次分发或商业牟利

---

## License

仅供个人学习研究使用。
