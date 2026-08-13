# build frontend
FROM node:22-alpine3.24
WORKDIR /tmp
COPY --parents public/ /tmp/
RUN npm install --global typescript
RUN tsc -p /tmp/public/js/tsconfig.json

# actual image
FROM python:3.12-alpine3.24

# main working directory
WORKDIR /app

# copy files to dir
COPY --parents requirements.txt main.py build.py launch.json assets/ cards/ core/ data/ deck/ engine/ game/ /app/
# copy compiled frontend
COPY --from=0 /tmp/public/ /app/public/
# replace localhost with 0.0.0.0 so one can access server from outside the container
RUN sed -i "s|127.0.0.1|0.0.0.0|g" launch.json

# create volume for assets cache
VOLUME /app/assets/cache

# install requirements
RUN pip install -r requirements.txt

# open port 2345
EXPOSE 2345
# run main.py
CMD ["python", "main.py"]
