FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV MCP_TRANSPORT=streamable-http
ENV FASTMCP_HOST=0.0.0.0
ENV FASTMCP_PORT=8000
ENV FASTMCP_STATELESS_HTTP=true
ENV PUBLIC_DATA_API_KEY=3df0792127f858443da07e62416744a514a11032db285e96aaffdb7a98e7858c

EXPOSE 8000

CMD ["python", "server.py"]
