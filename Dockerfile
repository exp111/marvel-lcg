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
# edit launch.json
# replace localhost with 0.0.0.0 so one can access server from outside the container
# add custom deck folder to launch json
RUN python -c "import json; f=open('launch.json'); j=json.load(f); f.close(); j['server_addresses']=['0.0.0.0:2345']; j['deck_folders']=['./deck/','./deck/custom/']; f=open('launch.json','w'); json.dump(j,f,indent=2); f.close()"

# create volume for assets cache + custom decks
VOLUME /app/assets/cache
VOLUME /app/deck/custom

# install requirements
RUN pip install -r requirements.txt

# open port 2345
EXPOSE 2345
# run main.py
CMD ["python", "main.py"]
