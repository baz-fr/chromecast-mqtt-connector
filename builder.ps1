#docker run --privileged --rm tonistiigi/binfmt --install all
docker buildx build --platform=linux/arm64 --progress=plain -t nas.lenfer.fr:9500/baz/mqtt2chromecast -t nas.lenfer.fr:9500/baz/mqtt2chromecast:1.0 --output=type=registry,name=nas.lenfer.fr:9500/baz/mqtt2chromecast,push=true,registry.insecure=true .

# Exemple de base
# docker buildx create --name mybuilder
# docker buildx use mybuilder
# docker buildx build \
#     --platform linux/amd64,linux/arm/v7 \
#     -t baz/chromecast-mqtt-smarthome-connector \
#     -t baz/chromecast-mqtt-smarthome-connector:1 \
#     -t baz/chromecast-mqtt-smarthome-connector:1.3 \
#     -t baz/chromecast-mqtt-smarthome-connector:1.3.2 \
#     --push .