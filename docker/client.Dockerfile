FROM oven/bun:1.1.38
WORKDIR /app
COPY package.json /app/package.json
COPY apps/client/package.json /app/apps/client/package.json
COPY packages/shared/package.json /app/packages/shared/package.json
RUN bun install
COPY apps/client /app/apps/client
COPY packages/shared /app/packages/shared
WORKDIR /app/apps/client
CMD ["bun", "run", "dev", "--host", "0.0.0.0", "--port", "5173"]
