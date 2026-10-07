FROM nginx:stable-alpine3.24-perl

COPY Application-Source-Code/signup.html /usr/share/nginx/html/index.html 
COPY Application-Source-Code/style.css /usr/share/nginx/html/style.css

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]