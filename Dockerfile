FROM ubuntu:latest
LABEL authors="thatt"

ENTRYPOINT ["top", "-b"]