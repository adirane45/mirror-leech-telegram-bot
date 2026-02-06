# TLS Certificates Directory

Place your SSL certificates here:
- certs/server.crt - Server certificate
- certs/server.key - Private key

Generate self-signed for testing:
openssl req -x509 -newkey rsa:4096 -keyout certs/server.key -out certs/server.crt -days 365 -nodes
