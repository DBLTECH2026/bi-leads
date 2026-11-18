FROM nginx:1.29-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY index.html app.js config.js estilo.css /usr/share/nginx/html/
COPY img /usr/share/nginx/html/img
COPY vendor /usr/share/nginx/html/vendor
# Cada imagen nueva pone su propia versión en los enlaces de CSS y JS (rompe la caché vieja del navegador)
RUN sed -i "s/__VERSION__/$(date +%Y%m%d%H%M%S)/g" /usr/share/nginx/html/index.html
