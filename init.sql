CREATE DATABASE IF NOT EXISTS webapp_db;
USE webapp_db;

CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(50) NOT NULL UNIQUE,
  password VARCHAR(100) NOT NULL
);

-- Create a dedicated application user
REVOKE ALL PRIVILEGES, GRANT OPTION FROM 'app_user'@'%';

-- Grant strictly necessary data manipulation privileges (avoid ALL PRIVILEGES if DDL is not needed)
GRANT SELECT, INSERT, UPDATE, CREATE, ALTER, INDEX, REFERENCES ON webapp_db.* TO 'app_user'@'%';

FLUSH PRIVILEGES;