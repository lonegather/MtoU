# Maya to Unreal Pipeline Tools

## Server Builds (Docker Container)
### Build and run locally
```shell
docker build -f Dockerfile_Local -t image_name .
docker run -d -p 80:80 image_name
```
Go to 127.0.0.1 to see if it works

### Server initialization
```shell
docker exec -it container_name /bin/bash
cd /home/docker/code/app
python3 manage.py collectstatic
python3 manage.py makemigrations --empty app_name
python3 manage.py makemigrations
python3 manage.py migrate
python3 manage.py createsuperuser
```
This docker image build refers to [dockerfiles/django-uwsgi-nginx](https://github.com/dockerfiles/django-uwsgi-nginx), replacing all download sources with Chinese websites to solve connection issues (local build). For DockerHub Autobuild, use the original Dockerfile.


## Data Setup
Save `/app/setup_template.csv` as `/app/setup.csv` and fill in the data
```shell
docker exec -it container_name /bin/bash
```
Or start a bash console if you are using DSM OS.
```shell
cd /home/docker/code/app
python3 manage.py makemigrations
python3 manage.py migrate
python3 manage.py shell
```
```python
import main
main.reset()
```
