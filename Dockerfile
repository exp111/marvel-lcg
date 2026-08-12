FROM python:3.14.7-alpine3.24

# main working directory
WORKDIR /app

# copy files to dir
COPY --parents requirements.txt main.py build.py launch.json assets/ cards/ core/ data/ deck/ engine/ game/ public/ /app/
# replace localhost with 0.0.0.0 so one can access server from outside the container
RUN sed -i "s|127.0.0.1|0.0.0.0|g" launch.json

# create volume for assets cache
VOLUME /app/assets/cache
#TODO: volume launch.json + campaign config

#TODO: compile frontend?
#RUN tsc -p public/lib/tsconfig.json

# install requirements
RUN pip install -r requirements.txt

# open port 2345
EXPOSE 2345
# run main.py
CMD ["python", "main.py"]
