FROM python:2.7

ADD init-app.sh /usr/local/bin/
ADD backports.list /etc/apt/sources.list.d/

# Install some useful libraries for computer vision applications.
RUN apt-get update && \
    apt-get install -y \
        cmake \
        iptables \
        libboost-python-dev \
        libopenblas-dev \
        liblapack-dev \
        sudo

#RUN git clone https://github.com/davisking/dlib /opt/dlib && \
#        cd /opt/dlib && \
#        sed "s/SSE4/SSE2/g" -i tools/python/CMakeLists.txt && \
#        mkdir build && \
#        cd build && \
#        cmake .. && \
#        cmake -- build . && \
#        make install && \
#        cd .. && \
#        python setup.py install --yes USE_SSE2_INSTRUCTIONS

# Build dlib with SSE2 instructions. The packaged version uses SSE4
# instructions, which our APU devices do not support.
#
# References:
# https://github.com/ageitgey/face_recognition/issues/11
# https://github.com/ageitgey/face_recognition/blob/master/Dockerfile
RUN git clone -b 'v19.7' --single-branch https://github.com/davisking/dlib.git /opt/dlib/ && \
        cd /opt/dlib && \
        sed "s/SSE4/SSE2/g" -i tools/python/CMakeLists.txt && \
#        mkdir build && \
#        cd build && \
#        cmake .. && \
#        cmake -- build . && \
#        make install && \
#        cd .. && \
        python setup.py install --yes && \
        rm -rf /opt/dlib

RUN pip install \
        face-recognition~=1.0.0 \
        numpy~=1.13.1 \
        opencv-python~=3.3.0.10 \
        Pillow~=4.2.1 \
        scipy~=0.19.1 && \
    mkdir -p /usr/share/openface-models/

RUN git clone https://github.com/torch/distro.git /opt/torch --recursive && \
    cd /opt/torch && \
    bash install-deps && \
    ./install.sh && \
    /opt/torch/install/bin/luarocks install torch && \
    /opt/torch/install/bin/luarocks install nn && \
    /opt/torch/install/bin/luarocks install dpnn

RUN git clone https://github.com/cmusatyalab/openface.git /opt/openface && \
    cd /opt/openface && \
    ./models/get-models.sh && \
    pip install -r requirements.txt && \
    python setup.py install

# Download openface neural network model.
#ADD https://storage.cmusatyalab.org/openface-models/nn4.small2.v1.t7 /usr/share/openface-models/

# Set up an unprivileged user so that we can drop out of root.
# Make /home/paradrop so that pip can drop some files in there.
# Make /opt/paradrop/app for installing the app files.
# Add cap_net_bind_service to python so that it can bind to ports 1-1024.
RUN useradd --system --uid 999 paradrop && \
    mkdir -p /home/paradrop && \
    chown paradrop /home/paradrop && \
    mkdir -p /opt/paradrop/app && \
    chown paradrop /opt/paradrop/app && \
    chmod a+s /opt/paradrop/app && \
    setcap 'cap_net_bind_service=+ep' /usr/local/bin/python2.7

# Defang setuid/setgid binaries.
RUN find / -perm +6000 -type f -exec chmod a-s {} \; || true

WORKDIR /opt/paradrop/app
ENV PATH $PATH:/opt/torch/install/bin

# Copy paradrop.yaml and requirements.txt, the latter only if it exists.  Then
# call init-app.sh to install dependencies. These layers will be cached as long
# as the requirements do not change.
ONBUILD COPY paradrop.yaml requirements.tx[t] /opt/paradrop/app/
ONBUILD RUN init-app.sh

# Now copy the rest of the files.
ONBUILD COPY . /opt/paradrop/app/
ONBUILD RUN chown paradrop:paradrop -R /opt/paradrop/app

ONBUILD USER paradrop
