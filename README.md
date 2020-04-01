# Maya to Unreal Pipeline Tools

## Server Builds (Docker Container)
### Build and run locally
```
docker build -f Dockerfile_Local -t mtou .
docker run -d -p 8000:80 mtou
```
Go to 127.0.0.1 to see if it works

### Server initialization
```
docker exec -it container_name /bin/bash
cd /home/docker/code/app
python3 manage.py collectstatic
python3 manage.py makemigrations --empty app_name
python3 manage.py makemigrations
python3 manage.py migrate
python3 manage.py createsuperuser
python3 manage.py setup
```
