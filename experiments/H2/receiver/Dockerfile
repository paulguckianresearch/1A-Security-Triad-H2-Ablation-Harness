FROM python:3.10-slim

RUN useradd --uid 10002 --create-home h2
WORKDIR /app

COPY receiver.py internal_probe.py admin.py entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh && chown -R h2:h2 /app

EXPOSE 8080
# Starts as root to set the baseline access-control state, then runs the
# receiver as h2 (see entrypoint.sh). admin.py is executed separately as root.
CMD ["/app/entrypoint.sh"]
