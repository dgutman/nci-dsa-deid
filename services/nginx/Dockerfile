# Custom nginx image with NCI DSA DeID routing baked in (no bind mounts).
FROM nginx:1.27.1
COPY nginx.conf /etc/nginx/nginx.conf
COPY redirect_http.conf /etc/nginx/conf.d/redirect_http.conf
COPY use_https.conf /etc/nginx/conf.d/use_https.conf
COPY index.html /etc/nginx/html/index.html
