# Custom nginx image with baked-in configuration
# This ensures consistent routing across all deployments
FROM nginx:1.27.1

# Copy all nginx configuration files
COPY nginx.conf /etc/nginx/nginx.conf
COPY redirect_http.conf /etc/nginx/conf.d/redirect_http.conf
COPY use_https.conf /etc/nginx/conf.d/use_https.conf
COPY index.html /etc/nginx/html/index.html

# Expose port 80
EXPOSE 80

# Use default nginx entrypoint and command
