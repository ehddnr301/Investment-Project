FROM ehddnr/ticker:1.0.0

USER root

COPY . .

RUN fluent-gem install fluent-plugin-opensearch
RUN apt-get update && apt-get install -y python3 && apt-get install -y python3-pip
RUN pip3 install -r requirements.txt

COPY fluent.conf /fluentd/etc/fluent.conf

ENTRYPOINT ["/start.sh"]