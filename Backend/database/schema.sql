-- E-Charge 智能充电系统数据库表结构
-- 创建数据库
CREATE DATABASE IF NOT EXISTS echarge DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE echarge;

-- 用户表
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

-- 充电桩表
CREATE TABLE IF NOT EXISTS charging_piles (
    id INT PRIMARY KEY,  -- 充电桩ID，由配置文件指定
    name VARCHAR(100) NOT NULL,
    pile_type ENUM('fast', 'trickle') NOT NULL,
    power DECIMAL(10,2) NOT NULL COMMENT '充电功率(kW)',
    status ENUM('AVAILABLE', 'CHARGING', 'FAULT', 'OFFLINE') NOT NULL DEFAULT 'OFFLINE',
    `current_user` VARCHAR(50) NULL,
    total_charges INT DEFAULT 0 COMMENT '总充电次数',
    total_energy DECIMAL(15,2) DEFAULT 0.00 COMMENT '总充电量(度)',
    total_hours DECIMAL(15,2) DEFAULT 0.00 COMMENT '总运行时间(小时)',
    last_heartbeat TIMESTAMP NULL COMMENT '最后心跳时间',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_pile_type (pile_type),
    INDEX idx_status (status),
    INDEX idx_current_user (`current_user`),
    FOREIGN KEY (`current_user`) REFERENCES users(username) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 充电请求表
CREATE TABLE IF NOT EXISTS charge_requests (
    id VARCHAR(50) PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    charge_type ENUM('fast', 'trickle') NOT NULL,
    energy_amount DECIMAL(10,2) NOT NULL COMMENT '请求充电量(度)',
    status ENUM('waiting', 'queued', 'charging', 'completed', 'cancelled', 'interrupted') NOT NULL DEFAULT 'waiting',
    pile_id INT NULL COMMENT '分配的充电桩ID',
    queue_number VARCHAR(20) NULL COMMENT '排队号码',
    position INT NULL COMMENT '排队位置',
    estimated_start_time TIMESTAMP NULL COMMENT '预计开始时间',
    estimated_wait_minutes INT NULL COMMENT '预计等待时间(分钟)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_username (username),
    INDEX idx_status (status),
    INDEX idx_charge_type (charge_type),
    INDEX idx_pile_id (pile_id),
    INDEX idx_created_at (created_at),
    FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE,
    FOREIGN KEY (pile_id) REFERENCES charging_piles(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 充电记录表
CREATE TABLE IF NOT EXISTS charge_records (
    id VARCHAR(50) PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    pile_id INT NOT NULL,
    request_id VARCHAR(50) NULL COMMENT '关联的充电请求ID',
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NULL,
    energy_amount DECIMAL(10,2) NOT NULL DEFAULT 0.00 COMMENT '实际充电量(度)',
    duration_hours DECIMAL(10,3) NOT NULL DEFAULT 0.000 COMMENT '充电时长(小时)',
    electricity_cost DECIMAL(10,2) NOT NULL DEFAULT 0.00 COMMENT '电费(元)',
    service_cost DECIMAL(10,2) NOT NULL DEFAULT 0.00 COMMENT '服务费(元)',
    total_cost DECIMAL(10,2) NOT NULL DEFAULT 0.00 COMMENT '总费用(元)',
    status ENUM('completed', 'cancelled', 'interrupted') NOT NULL DEFAULT 'completed',
    cancel_reason VARCHAR(255) NULL COMMENT '取消原因',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_username (username),
    INDEX idx_pile_id (pile_id),
    INDEX idx_request_id (request_id),
    INDEX idx_start_time (start_time),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at),
    FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE,
    FOREIGN KEY (pile_id) REFERENCES charging_piles(id) ON DELETE CASCADE,
    FOREIGN KEY (request_id) REFERENCES charge_requests(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 系统配置表
CREATE TABLE IF NOT EXISTS system_config (
    config_key VARCHAR(100) PRIMARY KEY,
    config_value TEXT NOT NULL,
    description VARCHAR(255) NULL,
    config_type ENUM('string', 'int', 'float', 'boolean', 'json') DEFAULT 'string',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 故障日志表
CREATE TABLE IF NOT EXISTS fault_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    pile_id INT NOT NULL,
    fault_reason VARCHAR(255) NOT NULL,
    fault_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    recovery_time TIMESTAMP NULL,
    duration_minutes INT NULL COMMENT '故障持续时间(分钟)',
    status ENUM('active', 'recovered') DEFAULT 'active',
    created_by ENUM('system', 'admin', 'simulator') DEFAULT 'system',
    
    INDEX idx_pile_id (pile_id),
    INDEX idx_fault_time (fault_time),
    INDEX idx_status (status),
    FOREIGN KEY (pile_id) REFERENCES charging_piles(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 插入默认数据

-- 插入管理员用户
INSERT IGNORE INTO users (username, password, user_type) VALUES 
('admin', 'admin123', 'admin'),
('test_user', 'user123', 'user');

-- 插入充电桩数据（根据配置文件）
INSERT IGNORE INTO charging_piles (id, name, pile_type, power, status) VALUES 
(1, '快充桩A', 'fast', 30.00, 'AVAILABLE'),
(2, '快充桩B', 'fast', 30.00, 'AVAILABLE'),
(3, '慢充桩A', 'trickle', 7.00, 'AVAILABLE'),
(4, '慢充桩B', 'trickle', 7.00, 'AVAILABLE'),
(5, '慢充桩C', 'trickle', 7.00, 'AVAILABLE');

-- 插入系统配置
INSERT IGNORE INTO system_config (config_key, config_value, description, config_type) VALUES 
('peak_electricity_rate', '1.2', '峰时电价(元/度)', 'float'),
('normal_electricity_rate', '0.8', '平时电价(元/度)', 'float'),
('valley_electricity_rate', '0.4', '谷时电价(元/度)', 'float'),
('service_fee_rate', '0.8', '服务费率(元/度)', 'float'),
('peak_hours', '["08:00-11:30", "18:00-23:00"]', '峰时时段', 'json'),
('valley_hours', '["23:00-07:00"]', '谷时时段', 'json'),
('max_queue_size', '10', '最大排队数量', 'int'),
('fault_dispatch_strategy', 'priority', '故障调度策略', 'string');

-- 创建视图：充电统计视图
CREATE OR REPLACE VIEW charge_statistics AS
SELECT 
    u.username,
    COUNT(cr.id) as total_charges,
    COALESCE(SUM(cr.energy_amount), 0) as total_energy,
    COALESCE(SUM(cr.total_cost), 0) as total_cost,
    COALESCE(SUM(cr.duration_hours), 0) as total_hours,
    MAX(cr.end_time) as last_charge_time
FROM users u
LEFT JOIN charge_records cr ON u.username = cr.username AND cr.status = 'COMPLETED'
WHERE u.user_type = 'user'
GROUP BY u.username;

-- 创建视图：充电桩统计视图
CREATE OR REPLACE VIEW pile_statistics AS
SELECT 
    cp.id,
    cp.name,
    cp.pile_type,
    cp.status,
    COUNT(cr.id) as total_charges,
    COALESCE(SUM(cr.energy_amount), 0) as total_energy,
    COALESCE(SUM(cr.total_cost), 0) as total_revenue,
    COALESCE(SUM(cr.duration_hours), 0) as total_hours,
    COUNT(CASE WHEN cr.start_time >= CURDATE() THEN 1 END) as today_charges
FROM charging_piles cp
LEFT JOIN charge_records cr ON cp.id = cr.pile_id AND cr.status = 'COMPLETED'
GROUP BY cp.id, cp.name, cp.pile_type, cp.status;

-- 注意：存储过程暂时注释掉，避免语法错误
-- 如果需要可以手动在MySQL中创建
/*
DELIMITER //
CREATE PROCEDURE IF NOT EXISTS CleanExpiredData(IN days_to_keep INT)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    -- 清理过期的已完成充电记录（保留指定天数）
    DELETE FROM charge_records 
    WHERE status IN ('COMPLETED', 'CANCELLED') 
    AND created_at < DATE_SUB(NOW(), INTERVAL days_to_keep DAY);
    
    -- 清理过期的充电请求
    DELETE FROM charge_requests 
    WHERE status IN ('COMPLETED', 'CANCELLED') 
    AND created_at < DATE_SUB(NOW(), INTERVAL days_to_keep DAY);
    
    -- 清理过期的故障日志
    DELETE FROM fault_logs 
    WHERE status = 'RECOVERED' 
    AND recovery_time < DATE_SUB(NOW(), INTERVAL days_to_keep DAY);
    
    COMMIT;
END //
DELIMITER ;
*/ 