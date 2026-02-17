-- db_setup.sql
-- Creates the `helpticket_system` database and an application user with password.
-- Run these commands as a MySQL root user (example commands below).

CREATE DATABASE IF NOT EXISTS `helpticket_system` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;

-- Create an application user (optional). Password requested: Jace102020.
CREATE USER IF NOT EXISTS 'helpticket_system'@'localhost' IDENTIFIED BY 'Jace102020.';
GRANT ALL PRIVILEGES ON `helpticket_system`.* TO 'helpticket_system'@'localhost';

FLUSH PRIVILEGES;

-- NOTE: This file only creates the database and a helper DB user. The provided
-- MySQL dump `helpticket_system.sql` (already in the repository) should be
-- imported into the `helpticket_system` database using the commands below.

-- Example import commands (run from shell / PowerShell):
-- Import the DB creation / user setup (if you created this file locally):
-- mysql -u root -p -P 3307 < db_setup.sql

-- Import full schema+data into the new database (use the dump file in repo):
-- mysql -u root -p -P 3307 helpticket_system < helpticket_system.sql

-- If you prefer to connect the application using root (as requested), ensure
-- you run the import using the root account:
-- mysql -u root -p -P 3307 < helpticket_system.sql
