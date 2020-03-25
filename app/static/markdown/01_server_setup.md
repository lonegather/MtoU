# ������ά��

####<b style="color:red">�����ĵ�����ϵͳ����Ա�ο�ʹ��</b>

### ���ʹ���ն˿��� NAS ������

��¼ DSM�� �ڿ��������ѡ�� <b>�ն˻���SNMP</b>��
����Ҳ�����ѡ��������Ͻ��л����߼�ģʽ<br>
��ȷ����ѡ�� <b>���� SSH ����</b>����ע��˿ںţ�һ��Ϊ22��<br>
��ʹ�� SSH �ͻ��˵�¼ NAS �������Ƽ�ʹ�� [PuTTY](https://the.earth.li/~sgtatham/putty/latest/w64/putty-64bit-0.73-installer.msi)��

### ���� Docker ����
��¼��ʹ�� `cd` ������� samkit ����Ŀ¼��ͨ�� DSM File Station ���õ�Ŀ¼һ��λ�� `/volume#`��

```bash
docker build -f Dockerfile_Local -t samkit .
docker run -d -p 8000:80 samkit
```

### ���� Docker ����

```bash
docker restart <id>
```
`restart` ������Ҫ����ID��Ϊ��������ͨ�� `docker container list` ������

### ��ν��� Docker ����������

```bash
docker exec -it <name> /bin/bash
```
`exec` ������Ҫ����������Ϊ��������ͨ�� `docker container list` ������

### Django Admin ��ʼ��

```bash
docker exec -it <name> /bin/bash
cd /home/docker/code/app
python3 manage.py collectstatic
python3 manage.py createsuperuser
```

### Django ���ݿ�����

```bash
docker exec -it <name> /bin/bash
cd /home/docker/code/app
python3 manage.py makemigrations --empty main
python3 manage.py makemigrations
python3 manage.py migrate
python3 manage.py setup
```

### �������� SVN �� UE ����

�����δ�� DSM �а�װ SVN Server�������׼�������������װ��<br>
��Ӧÿ��UE���̣�������һ��SVN�⣬����¼������ַ��

![](/static/images/01_001.png)

���������Ȩ������Ϊ�ɶ�д������Ҫ�κ���Ȩ������ UE ���ύ�����

���� Epic Launcher������һ��4.23�汾�Ĺ��̡�

![](/static/images/01_002.png)

������ɺ�ر� Unreal �༭����

�� `Samkit/unreal/` �е� `Content` �� `Plugins` ���Ƶ� Unreal ����Ŀ¼�У�
���� `Plugins` �ļ����е�ѹ���ļ���ѹ����ǰ�ļ��С���ѹ��Ϻ�ɾ��ѹ������

![](/static/images/01_003.png)

Unreal ����Ŀ¼�У�ɾ�� `Config`��`Intermediate` �� `Saved` �ļ��У�Ȼ���ڿհ״��Ҽ�SVN Checkout��

![](/static/images/01_004.png)
![](/static/images/01_005.png)

SVN����ʾ�ļ��зǿգ����������ģ����Checkout��

![](/static/images/01_006.png)
![](/static/images/01_007.png)

Unreal ����Ŀ¼�У��ڿհ״��Ҽ�SVN Commit��

![](/static/images/01_008.png)

�� Message һ�������ύ��Ϣ���� Check һ����� All ��ťѡ�������ļ���Ȼ���� OK ��ʼ�ϴ���

![](/static/images/01_009.png)
![](/static/images/01_010.png)

�����ļ��϶࣬���в���Ӧ��������֣����������ģ����ĵȴ����ɷ��Ӽ��ɡ�
