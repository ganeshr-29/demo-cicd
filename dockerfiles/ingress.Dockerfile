FROM nginx:stable-alpine3.24-perl

COPY nginx-conf-files/ingress.conf /etc/nginx/conf.d/default.conf
COPY Application-Source-Code/signup.html /usr/share/nginx/html/index.html 
COPY Application-Source-Code/style.css /usr/share/nginx/html/style.css

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]

