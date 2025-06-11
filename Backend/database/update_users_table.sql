-- 更新用户表结构
USE echarge;

-- 先修改表结构，删除外键约束（如果存在）
SET FOREIGN_KEY_CHECKS = 0;

-- 删除旧的用户表
DROP TABLE IF EXISTS users;

-- 创建新的用户表
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    user_type ENUM('user', 'admin') NOT NULL DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_username (username),
    INDEX idx_user_type (user_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 插入默认用户
INSERT INTO users (username, password, user_type) VALUES 
('admin', 'admin123', 'admin'),
('test_user', 'user123', 'user');

-- 重新添加外键约束
ALTER TABLE charging_piles 
ADD CONSTRAINT charging_piles_ibfk_1 
FOREIGN KEY (`current_user`) REFERENCES users(username) ON DELETE SET NULL;

ALTER TABLE charge_requests 
ADD CONSTRAINT charge_requests_ibfk_1 
FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE;

ALTER TABLE charge_records 
ADD CONSTRAINT charge_records_ibfk_1 
FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE;

SET FOREIGN_KEY_CHECKS = 1; 