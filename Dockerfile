FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN useradd -m soln && mkdir -p /app/data && chown -R soln:soln /app/data
USER soln
ENV PYTHONUNBUFFERED=1 SOLN_HTTP_HOST=0.0.0.0 SOLN_ALLOW_PUBLIC_READONLY=1
EXPOSE 8080
CMD ["python","-m","server.http"]
