# ---- Frontend: build بـ Vite ثم serve عبر Nginx (بدون أي CDN خارجي) ----
FROM node:20-alpine AS build
WORKDIR /web
COPY package.json package-lock.json* ./
RUN npm install || npm install --no-audit --no-fund
COPY . .
RUN npm run build

FROM nginx:1.25-alpine AS runtime
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /web/dist /usr/share/nginx/html
# خط تجوال محلي يُنسخ ضمن dist عبر public/fonts
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
