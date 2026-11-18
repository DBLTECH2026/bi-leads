FROM nginx:1.29-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY index.html app.js config.js estilo.css /usr/share/nginx/html/
COPY img /usr/share/nginx/html/img
COPY vendor /usr/share/nginx/html/vendor
