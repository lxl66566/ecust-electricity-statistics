# ecust-electricity-statistics
华东理工大学电费统计：拒绝一切不透明操作。通过 Github Actions 自动获取并记录每天的宿舍电量剩余。

## 开始记录
1. 华理信息办 - 微门户 - 电费充值 - 查询您的宿舍电量 - 复制链接。（本例中宿舍为随机选出）

<img alt="复制链接" src="https://user-images.githubusercontent.com/88281489/205481212-aaca1699-79ef-4c17-b3e3-a7e477ad55db.png"  width="30%" height="30%"/>

2. 右上角 fork 仓库

![fork](https://user-images.githubusercontent.com/88281489/205480982-a221a67c-c789-4298-9a45-34a35c820b71.png)

3. 在 Code 界面下，点击 `data.js` ，将其删除。

![删除 AbsoluteX 的数据](https://user-images.githubusercontent.com/88281489/205482133-a769645f-e106-453b-9fb1-09ec95664236.png)

4. Settings - Secrets and variables - Actions - New repository secret
* Name 填写 `URL`，Secret 填写 第一步复制的链接

![找到 Secrets](https://user-images.githubusercontent.com/88281489/205481390-292a3fc3-fa69-4c2f-886c-b0bc573f5470.png)
![填写](https://user-images.githubusercontent.com/88281489/205481486-3b5cafc9-f00d-4ca3-a0d8-eaedfffff7df.png)

5. Settings - Actions - General 界面，拉到最下，选择 Workflow permissions 为 Read and write permissions

<img alt="界面" src="https://user-images.githubusercontent.com/88281489/229278107-8a623cea-0ff9-435c-b729-e248c17ae827.png"  width="70%" height="70%"/>

![选择权限](https://user-images.githubusercontent.com/88281489/229278162-e65383df-17a4-4b66-8981-5fc23d2413a7.png)

6. Actions - enable them，然后在 AutoRecord 下点击 Enable workflow

![image](https://user-images.githubusercontent.com/88281489/229278566-17ec1798-5e26-4c42-8f82-91386955d4fc.png)
![image](https://user-images.githubusercontent.com/88281489/205481894-022e114f-5023-45d5-881d-d5fbc9d4a6ba.png)

## 查看数据
### Github Pages（推荐）
使用 Github Pages 构建。请确保您已获取到电量数据。

Settings - Pages - Deploy from a branch - 选中 main - Save

等待网站构建完毕后（约 1 min），刷新页面，点击 Visit site 即可查看数据。

![image](https://user-images.githubusercontent.com/88281489/205528351-399f221b-96e8-4ca5-86d0-32eb6cdb9286.png)

### 图表
1. 使用 `git clone` 或下载 zip
2. 解压，双击打开 `index.html` 文件
### 生数据
直接点击 `data.js` 查看
## 注意事项
fork 此仓库后请不要再次 sync fork，否则可能会造成数据丢失。若确实需要更新到最新版本，请自行备份`data.js`并使用 git 恢复数据。
