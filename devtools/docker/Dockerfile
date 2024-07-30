FROM molssi/mamba141

LABEL org.opencontainers.image.authors="psaxe@molssi.org"

COPY ./dftbplus_step/data/seamm-dftbplus.yml /root/environment.yml

RUN mamba env update -f /root/environment.yml

RUN apt-get install -qy curl

RUN mkdir /root/Parameters \
 && cd /root/Parameters \
 && curl 'https://dftb.org/fileadmin/DFTB/public/slako-unpacked.tar.xz' -o slako-unpacked.tar.xz \
 && tar -x -o -p -f slako-unpacked.tar.xz \
 && chmod -R go+rX . \
 && rm slako-unpacked.tar.xz

WORKDIR /home
CMD ["dftb+"]
