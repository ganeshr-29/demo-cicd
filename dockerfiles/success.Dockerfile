FROM nginx:stable-alpine3.24-perl

COPY Application-Source-Code/success.html /usr/share/nginx/html/index.html 

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
