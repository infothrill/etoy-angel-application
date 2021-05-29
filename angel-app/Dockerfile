FROM python:2.7

ENV INSTALL_PATH /home/app
RUN useradd -d $INSTALL_PATH --user-group app && mkdir -p $INSTALL_PATH
WORKDIR $INSTALL_PATH

COPY . .
RUN tar xjf twisted_trunk_21878.tar.bz2 && \
    mv twisted_trunk_21878/twisted/ src/
RUN python setup.py install

RUN chown -R app:app ./

ENV PYTHONPATH=/home/app/src/
WORKDIR $INSTALL_PATH/src/bin
USER app

CMD ["python", "master.py"]

