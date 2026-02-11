# Host nginx setup (for the server in front of Docker)

Use this on the **host** nginx (the one that proxies to `http://localhost:8090/`). It works with the container nginx and fixes redirects so links stay on your public host (e.g. `wsi-deid.pathology.emory.edu`) instead of going to localhost.

## Option A: Replace the `location /` block

Use this entire `location /` block (and remove any existing one for `/`):

```nginx
    location / {
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_pass http://localhost:8090/;
        proxy_redirect http://localhost:8090/ $scheme://$host/;
        proxy_redirect http://localhost/ $scheme://$host/;
        proxy_redirect https://localhost:8090/ $scheme://$host/;
        proxy_redirect https://localhost/ $scheme://$host/;
        proxy_buffering off;
        proxy_cache off;
        proxy_set_header Connection '';
        proxy_http_version 1.1;
        chunked_transfer_encoding off;
        proxy_read_timeout 600s;
        proxy_send_timeout 600s;
        proxy_request_buffering off;
    }
```

## Option B: Minimal changes to an existing block

If the host nginx already has a `location /` that does `proxy_pass http://localhost:8090/;`:

1. **Use the request host (not the proxy host)**  
   Ensure you have:
   - `proxy_set_header Host $host;`  
   - `proxy_set_header X-Forwarded-Host $host;`  
   - `proxy_set_header X-Forwarded-Proto $scheme;`  
   (Do **not** use `Host $proxy_host`.)

2. **Add redirect rewriting**  
   Right after `proxy_pass http://localhost:8090/;`, add:
   ```nginx
        proxy_redirect http://localhost:8090/ $scheme://$host/;
        proxy_redirect http://localhost/ $scheme://$host/;
        proxy_redirect https://localhost:8090/ $scheme://$host/;
        proxy_redirect https://localhost/ $scheme://$host/;
   ```

Then run:

```bash
sudo nginx -t && sudo systemctl reload nginx
```

Users may need to clear cache or use a private window once so old 301 redirects to localhost are not reused.

## Full example

See [host-nginx-example.conf](./host-nginx-example.conf) for a complete server block including SSL and optional `/dryad/` location.
