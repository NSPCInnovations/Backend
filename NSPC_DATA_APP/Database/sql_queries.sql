-- Create the user and grant privileges
SELECT * FROM mysql.user;
CREATE USER 'NSPC_Admin'@'localhost' IDENTIFIED BY 'NSPC@2024_admin!';
GRANT ALL PRIVILEGES ON *.* TO 'NSPC_Admin'@'localhost' WITH GRANT OPTION;
FLUSH PRIVILEGES;
SHOW GRANTS FOR 'NSPC_Admin'@'localhost';