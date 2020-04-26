# 服务器维护

####<b style="color:red">以下文档仅供系统管理员参考使用</b>

### 如何使用终端控制 NAS 服务器

登录 DSM， 在控制面板中选择 <b>终端机和SNMP</b>。
如果找不到该选项，请点击右上角切换至高级模式<br>
请确保勾选了 <b>启动 SSH 功能</b>，并注意端口号（一般为22）<br>
请使用 SSH 客户端登录 NAS 主机（推荐使用 [PuTTY](https://the.earth.li/~sgtatham/putty/latest/w64/putty-64bit-0.73-installer.msi)）

### 创建 Docker 容器
登录后使用 `cd` 命令进入 mtou 所在目录（通过 DSM File Station 设置的目录一般位于 `/volume#`）

```bash
docker build -f Dockerfile_Local -t mtou .
docker run -d -p 8000:80 mtou
```

### 重启 Docker 容器

```bash
docker restart <id>
```
`restart` 命令需要容器ID作为参数，可通过 `docker container list` 命令获得

### 如何进入 Docker 容器命令行

```bash
docker exec -it <name> /bin/bash
```
`exec` 命令需要容器名称作为参数，可通过 `docker container list` 命令获得

### Django Admin 初始化

```bash
docker exec -it <name> /bin/bash
cd /home/docker/code/app
python3 manage.py createsuperuser
```

### Django 数据库重置

```bash
docker exec -it <name> /bin/bash
cd /home/docker/code/app
python3 manage.py makemigrations --empty main
python3 manage.py makemigrations
python3 manage.py migrate
python3 manage.py setup
```

### 创建基于 SVN 的 UE 工程

如果还未在 DSM 中安装 SVN Server，请在套件中心搜索并安装。<br>
对应每个UE工程，各创建一个SVN库，并记录访问网址。

![](/static/images/01_001.png)

如果将匿名权限设置为可读写，则不需要任何授权即可在 UE 中提交变更。

启动 Epic Launcher，创建工程。

![](/static/images/01_002.png)

创建完成后关闭 Unreal 编辑器。

将 `Samkit/unreal/` 中的 `Content` 和 `Plugins` 复制到 Unreal 工程目录中，
并将 `Plugins` 文件夹中的压缩文件解压至当前文件夹。解压完毕后删除压缩包：

![](/static/images/01_003.png)

Unreal 工程目录中，删除 `Config`、`Intermediate` 和 `Saved` 文件夹，然后在空白处右键SVN Checkout：

![](/static/images/01_004.png)
![](/static/images/01_005.png)

SVN会提示文件夹非空，这是正常的，点击Checkout：

![](/static/images/01_006.png)
![](/static/images/01_007.png)

Unreal 工程目录中，在空白处右键SVN Commit：

![](/static/images/01_008.png)

在 Message 一栏填入提交信息，在 Check 一栏点击 All 按钮选中所有文件，然后点击 OK 开始上传：

![](/static/images/01_009.png)
![](/static/images/01_010.png)

由于文件较多，会有不响应的情况出现，这是正常的，耐心等待若干分钟即可。
