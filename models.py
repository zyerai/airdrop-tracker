from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class AirdropProject(db.Model):
    """撸毛项目模型"""
    __tablename__ = 'airdrop_projects'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    chain = db.Column(db.String(50))  # 链名称：ETH, BSC, SOL等
    category = db.Column(db.String(100))  # 类别：DeFi, NFT, GameFi等
    status = db.Column(db.String(20), default='tracking')  # tracking, claimed, ended
    potential = db.Column(db.String(20))  # high, medium, low
    investment = db.Column(db.Float, default=0.0)  # 投资金额（USD）
    reward = db.Column(db.Float, default=0.0)  # 预期奖励（USD）
    actual_reward = db.Column(db.Float, default=0.0)  # 实际奖励（USD）
    deadline = db.Column(db.DateTime)  # 截止日期
    reminder_date = db.Column(db.DateTime)  # 提醒日期
    tasks_completed = db.Column(db.Integer, default=0)  # 已完成任务数
    total_tasks = db.Column(db.Integer, default=0)  # 总任务数
    links = db.Column(db.Text)  # 相关链接（JSON格式）
    notes = db.Column(db.Text)  # 备注
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'chain': self.chain,
            'category': self.category,
            'status': self.status,
            'potential': self.potential,
            'investment': self.investment,
            'reward': self.reward,
            'actual_reward': self.actual_reward,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'reminder_date': self.reminder_date.isoformat() if self.reminder_date else None,
            'tasks_completed': self.tasks_completed,
            'total_tasks': self.total_tasks,
            'links': self.links,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'roi': self.calculate_roi()
        }

    def calculate_roi(self):
        """计算ROI"""
        if self.investment > 0:
            if self.actual_reward > 0:
                return round((self.actual_reward - self.investment) / self.investment * 100, 2)
            elif self.reward > 0:
                return round((self.reward - self.investment) / self.investment * 100, 2)
        return 0.0

class ActivityLog(db.Model):
    """活动日志模型"""
    __tablename__ = 'activity_logs'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('airdrop_projects.id'), nullable=True)
    action = db.Column(db.String(100), nullable=False)  # 动作类型
    description = db.Column(db.Text)  # 描述
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'action': self.action,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
