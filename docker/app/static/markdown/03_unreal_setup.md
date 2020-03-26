# Unreal 工程设置

### 获取工程文件

[点击此处](https://tortoisesvn.net/downloads.html)下载SVN客户端并安装。

安装完成后在适当的本地目录处新建一个文件夹，并给与一个有可读性的项目名称。进入文件夹，在空白处右键 SVN Checkout：

![](/static/images/03_001.png)

SVN 地址请通过技术支持人员获悉：

![](/static/images/03_002.png)

![](/static/images/03_003.png)

双击 .uproject 文件即可打开 Unreal 工程：

![](/static/images/03_004.png)

### 设置工程

在 UE 编辑器中开始连接 SVN 服务器：

![](/static/images/03_005.png)

选择 Subversion 作为版本控制，并填入 SVN 地址：

![](/static/images/03_006.png)

### 提交变更

当你完成对 UE 资产的变更后，可通过此处将所有变更加入提交列表：

![](/static/images/03_007.png)

通过此处进行提交：

![](/static/images/03_008.png)

变更描述是必填项，否则无法提交。请尽量完整清晰地描述当前变更的内容，便于未来进行历史追溯：

![](/static/images/03_009.png)

### 同步工程文件

当其他人提交变更后，需要同步工程文件。
在 Unreal 工程目录空白处右键 SVN Update 即可：

![](/static/images/03_010.png)

<b style="color:red">注意：提交变更请在 UE 编辑器中进行，不要在资源管理器中进行提交，以保证服务端工程文件的规整。</b>
