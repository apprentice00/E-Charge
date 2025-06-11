"""
计费服务 - 实现动态计费和电价计算
"""

from datetime import datetime, time
from typing import Tuple, Dict, List
from config import get_config

class BillingService:
    """计费服务类"""
    
    def __init__(self):
        self.config = get_config()
        self.billing_config = self.config.BILLING_CONFIG
    
    def get_current_electricity_rate(self, charge_time: datetime = None) -> Tuple[float, str]:
        """
        获取指定时间的电价
        
        Args:
            charge_time: 充电时间，默认为当前时间
            
        Returns:
            (电价, 时段类型) 的元组
        """
        if charge_time is None:
            charge_time = datetime.now()
        
        hour = charge_time.hour
        
        # 检查峰时
        for start, end in self.billing_config['peak_hours']:
            if start <= hour < end:
                return self.billing_config['peak_rate'], '峰时'
        
        # 检查平时
        for start, end in self.billing_config['normal_hours']:
            if start <= hour < end:
                return self.billing_config['normal_rate'], '平时'
        
        # 检查谷时（跨日期的特殊处理）
        for start, end in self.billing_config['valley_hours']:
            if start > end:  # 跨日期，如23:00-7:00
                if hour >= start or hour < end:
                    return self.billing_config['valley_rate'], '谷时'
            else:
                if start <= hour < end:
                    return self.billing_config['valley_rate'], '谷时'
        
        # 默认返回平时电价
        return self.billing_config['normal_rate'], '平时'
    
    def calculate_charging_cost(self, energy_amount: float, start_time: datetime, 
                              end_time: datetime) -> Dict[str, float]:
        """
        计算充电费用
        
        Args:
            energy_amount: 充电量（度）
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            包含各项费用的字典
        """
        if energy_amount <= 0:
            return {
                'charge_cost': 0.0,
                'service_cost': 0.0,
                'total_cost': 0.0,
                'average_rate': 0.0
            }
        
        # 如果充电时间很短，直接按开始时间的电价计算
        duration_hours = (end_time - start_time).total_seconds() / 3600
        if duration_hours <= 1.0:
            rate, _ = self.get_current_electricity_rate(start_time)
            charge_cost = energy_amount * rate
        else:
            # 对于较长的充电时间，需要按时段分别计算
            charge_cost = self._calculate_time_based_cost(energy_amount, start_time, end_time)
        
        # 计算服务费
        service_cost = energy_amount * self.billing_config['service_rate']
        
        # 计算总费用
        total_cost = charge_cost + service_cost
        
        # 计算平均电价
        average_rate = charge_cost / energy_amount if energy_amount > 0 else 0.0
        
        return {
            'charge_cost': round(charge_cost, 2),
            'service_cost': round(service_cost, 2),
            'total_cost': round(total_cost, 2),
            'average_rate': round(average_rate, 2)
        }
    
    def _calculate_time_based_cost(self, energy_amount: float, start_time: datetime, 
                                 end_time: datetime) -> float:
        """
        按时段计算充电费用（用于长时间充电）
        
        Args:
            energy_amount: 充电量（度）
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            充电费用
        """
        total_cost = 0.0
        duration_hours = (end_time - start_time).total_seconds() / 3600
        
        # 简化计算：按小时分段计算
        current_time = start_time
        remaining_energy = energy_amount
        
        while current_time < end_time and remaining_energy > 0:
            # 计算这一小时的充电量（假设均匀充电）
            hour_duration = min(1.0, (end_time - current_time).total_seconds() / 3600)
            hour_energy = (hour_duration / duration_hours) * energy_amount
            
            # 获取当前小时的电价
            rate, _ = self.get_current_electricity_rate(current_time)
            
            # 计算这一小时的费用
            hour_cost = hour_energy * rate
            total_cost += hour_cost
            
            # 更新时间和剩余电量
            current_time = current_time.replace(hour=current_time.hour + 1, minute=0, second=0, microsecond=0)
            remaining_energy -= hour_energy
        
        return total_cost
    
    def estimate_charging_cost(self, energy_amount: float, charge_type: str = 'fast') -> Dict[str, float]:
        """
        估算充电费用（用于前端显示）
        
        Args:
            energy_amount: 充电量（度）
            charge_type: 充电类型（fast/trickle）
            
        Returns:
            包含估算费用的字典
        """
        # 使用当前时间的电价进行估算
        rate, time_type = self.get_current_electricity_rate()
        
        # 估算充电时长
        system_params = self.config.SYSTEM_PARAMS
        if charge_type == 'fast':
            duration_hours = energy_amount / system_params['fast_charging_power']
        else:
            duration_hours = energy_amount / system_params['trickle_charging_power']
        
        # 简单估算（可能跨时段）
        charge_cost = energy_amount * rate
        service_cost = energy_amount * self.billing_config['service_rate']
        total_cost = charge_cost + service_cost
        
        return {
            'charge_cost': round(charge_cost, 2),
            'service_cost': round(service_cost, 2),
            'total_cost': round(total_cost, 2),
            'current_rate': rate,
            'time_type': time_type,
            'estimated_duration': round(duration_hours, 2)
        }
    
    def get_daily_price_schedule(self) -> List[Dict[str, any]]:
        """
        获取一天的电价时段表
        
        Returns:
            包含时段信息的列表
        """
        schedule = []
        current_hour = datetime.now().hour
        
        # 峰时
        for start, end in self.billing_config['peak_hours']:
            schedule.append({
                'time_range': f"{start:02d}:00 - {end:02d}:00",
                'price': self.billing_config['peak_rate'],
                'type': '峰时',
                'is_current': start <= current_hour < end
            })
        
        # 平时
        for start, end in self.billing_config['normal_hours']:
            schedule.append({
                'time_range': f"{start:02d}:00 - {end:02d}:00",
                'price': self.billing_config['normal_rate'],
                'type': '平时',
                'is_current': start <= current_hour < end
            })
        
        # 谷时
        for start, end in self.billing_config['valley_hours']:
            if start > end:  # 跨日期
                schedule.append({
                    'time_range': f"{start:02d}:00 - 次日{end:02d}:00",
                    'price': self.billing_config['valley_rate'],
                    'type': '谷时',
                    'is_current': current_hour >= start or current_hour < end
                })
            else:
                schedule.append({
                    'time_range': f"{start:02d}:00 - {end:02d}:00",
                    'price': self.billing_config['valley_rate'],
                    'type': '谷时',
                    'is_current': start <= current_hour < end
                })
        
        # 按时间排序
        schedule.sort(key=lambda x: int(x['time_range'].split(':')[0]))
        
        return schedule
    
    def calculate_optimal_charging_time(self, energy_amount: float, charge_type: str = 'fast') -> Dict[str, any]:
        """
        计算最优充电时间（最低费用）
        
        Args:
            energy_amount: 充电量（度）
            charge_type: 充电类型
            
        Returns:
            最优充电时间建议
        """
        system_params = self.config.SYSTEM_PARAMS
        
        # 计算充电时长
        if charge_type == 'fast':
            duration_hours = energy_amount / system_params['fast_charging_power']
        else:
            duration_hours = energy_amount / system_params['trickle_charging_power']
        
        # 找到谷时时段
        valley_hours = self.billing_config['valley_hours']
        min_rate = self.billing_config['valley_rate']
        optimal_start_time = None
        
        for start, end in valley_hours:
            if start > end:  # 跨日期
                valley_duration = (24 - start) + end
            else:
                valley_duration = end - start
            
            # 如果充电时间可以完全在谷时内完成
            if duration_hours <= valley_duration:
                optimal_start_time = start
                break
        
        if optimal_start_time is None:
            # 如果无法在谷时完成，选择当前时间
            optimal_start_time = datetime.now().hour
        
        # 计算在最优时间的费用
        charge_cost = energy_amount * min_rate
        service_cost = energy_amount * self.billing_config['service_rate']
        total_cost = charge_cost + service_cost
        
        return {
            'optimal_start_hour': optimal_start_time,
            'estimated_cost': round(total_cost, 2),
            'savings': round((energy_amount * self.billing_config['peak_rate'] + service_cost) - total_cost, 2),
            'duration_hours': round(duration_hours, 2)
        } 