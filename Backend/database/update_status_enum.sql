-- 更新充电桩表的状态枚举
ALTER TABLE charging_piles MODIFY COLUMN status ENUM('AVAILABLE', 'CHARGING', 'FAULT', 'OFFLINE') NOT NULL DEFAULT 'OFFLINE';

-- 更新现有数据
UPDATE charging_piles SET status = 'AVAILABLE' WHERE status = 'available';
UPDATE charging_piles SET status = 'CHARGING' WHERE status = 'in_use'; 