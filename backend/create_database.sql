-- ============================================================
-- YottaPay AI – MySQL Database Initialisation Script
-- Run this script in MySQL Workbench or mysql CLI BEFORE
-- running the Python init_db.py script.
-- ============================================================

-- Create the database schema
CREATE DATABASE IF NOT EXISTS `yottapay`
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

-- Create a dedicated application user (optional, recommended for production)
-- Replace 'yottapay_user' and 'strong_password' with actual credentials.
-- If you prefer to use the root user, skip this block.
-- CREATE USER IF NOT EXISTS 'yottapay_user'@'localhost' IDENTIFIED BY 'strong_password';
-- GRANT ALL PRIVILEGES ON yottapay.* TO 'yottapay_user'@'localhost';
-- FLUSH PRIVILEGES;

USE `yottapay`;

-- Confirm
SELECT 'YottaPay database ready.' AS status;
