from flask import Flask, render_template, request, jsonify
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
import json
import os

from models import db, AirdropProject, ActivityLog

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///airdrop_tracker.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# 初始化数据库
with app.app_context():
    db.create_all()

# X内容生成器
class XContentGenerator:
    """X内容自动生成器"""

    @staticmethod
    def generate_daily_projects(projects):
        """生成今日撸毛机会推文"""
        active_projects = [p for p in projects if p.status == 'tracking']
        if not active_projects:
            # 没有项目时的通用内容
            return "🎯 今日撸毛机会更新 | ZYER\n\n正在寻找新的空投机会... 🕵️\n\n不擅长但能做好，持续寻找机会中 🚀\n\n💬 有什么好项目推荐吗？\n\n🔗 https://x.com/ZYER55\n\n#Airdrop #Crypto #WAGMI #执行力"

        high_potential = [p for p in active_projects if p.potential == 'high']
        medium_potential = [p for p in active_projects if p.potential == 'medium']

        content = f"🎯 今日撸毛机会更新 | ZYER\n\n"
        content += f"追踪中: {len(active_projects)}个项目 | 不擅长但能做好 🚀\n\n"

        if high_potential:
            content += "🔥 高潜力:\n"
            for p in high_potential[:3]:
                progress = f"{p.tasks_completed}/{p.total_tasks}" if p.total_tasks > 0 else "进行中"
                content += f"• {p.name} ({p.chain}) - {progress}\n"
            content += "\n"

        if medium_potential:
            content += "⭐ 中等潜力:\n"
            for p in medium_potential[:3]:
                progress = f"{p.tasks_completed}/{p.total_tasks}" if p.total_tasks > 0 else "进行中"
                content += f"• {p.name} ({p.chain})\n"

        content += f"\n💬 哪个项目你最看好？\n\n🔗 https://x.com/ZYER55\n\n#Airdrop #Crypto #WAGMI #执行力"

        return content

    @staticmethod
    def generate_roi_report(projects):
        """生成ROI报告推文"""
        claimed_projects = [p for p in projects if p.actual_reward > 0]
        active_projects = [p for p in projects if p.status == 'tracking']

        if claimed_projects:
            # 有实际收益时显示真实数据
            total_investment = sum(p.investment for p in claimed_projects)
            total_reward = sum(p.actual_reward for p in claimed_projects)
            total_roi = round((total_reward - total_investment) / total_investment * 100, 2) if total_investment > 0 else 0

            content = f"📊 撸毛收益报告 | ZYER\n\n"
            content += f"✅ 已申领项目: {len(claimed_projects)}\n"
            content += f"💰 总投入: ${total_investment:.2f}\n"
            content += f"💵 总收益: ${total_reward:.2f}\n"
            content += f"📈 总ROI: {total_roi}%\n\n"

            top_projects = sorted(claimed_projects, key=lambda x: x.calculate_roi(), reverse=True)[:3]
            content += "🏆 最佳项目:\n"
            for p in top_projects:
                content += f"• {p.name}: {p.calculate_roi()}% ROI\n"

            content += f"\n坚持执行，持续迭代 | 小步快跑 🚀\n\n🔗 https://x.com/ZYER55\n\n#Airdrop #Crypto #WAGMI #定投"

        elif active_projects:
            # 没有实际收益但有进行中项目，显示预期收益
            total_investment = sum(p.investment for p in active_projects)
            expected_reward = sum(p.reward for p in active_projects if p.reward > 0)
            expected_roi = round((expected_reward - total_investment) / total_investment * 100, 2) if total_investment > 0 else 0

            content = f"📊 撸毛预期报告 | ZYER\n\n"
            content += f"🔄 进行中项目: {len(active_projects)}\n"
            content += f"💰 总投入: ${total_investment:.2f}\n"
            content += f"🎁 预期收益: ${expected_reward:.2f}\n"
            content += f"📈 预期ROI: {expected_roi}%\n\n"
            content += f"⏳ 等待空投申领中...\n\n"
            content += f"耐心等待，持续执行 🚀\n\n🔗 https://x.com/ZYER55\n\n#Airdrop #Crypto #WAGMI #定投"

        else:
            # 没有任何项目
            content = f"📊 撸毛收益报告 | ZYER\n\n"
            content += f"暂无项目数据 📊\n\n"
            content += f"正在寻找优质空投机会... 🕵️\n\n"
            content += f"不擅长但能做好，持续探索中 🚀\n\n"
            content += f"💬 有什么好项目推荐吗？\n\n"
            content += f"🔗 https://x.com/ZYER55\n\n#Airdrop #Crypto #WAGMI"

        return content

    @staticmethod
    def generate_project_spotlight(project):
        """生成项目亮点推文"""
        if not project:
            return None

        content = f"🔍 项目分析: {project.name} | ZYER\n\n"

        if project.description:
            content += f"{project.description}\n\n"

        content += f"🔗 链条: {project.chain}\n"
        content += f"📂 类别: {project.category}\n"
        content += f"💎 潜力: {project.potential.upper()}\n"

        if project.total_tasks > 0:
            progress = int(project.tasks_completed / project.total_tasks * 100)
            content += f"📊 进度: {progress}% ({project.tasks_completed}/{project.total_tasks})\n"

        if project.investment > 0:
            content += f"💵 投入: ${project.investment:.2f}\n"
        if project.reward > 0:
            content += f"🎁 预期: ${project.reward:.2f}\n"

        if project.deadline:
            days_left = (project.deadline - datetime.now()).days
            if days_left > 0:
                content += f"⏰ 剩余: {days_left}天\n"

        content += f"\n💬 你在参与这个项目吗？\n\n🔗 https://x.com/ZYER55\n\n#Crypto #Airdrop #WAGMI"

        return content

    @staticmethod
    def generate_thread(projects):
        """生成完整Thread"""
        active_projects = [p for p in projects if p.status == 'tracking']

        if not active_projects:
            # 没有项目时生成通用Thread
            thread = [
                "🧵 我的撸毛策略 | ZYER\n\n"
                "不擅长但能做好，分享我的方法 👇\n\n"
                "🔗 https://x.com/ZYER55",

                "1/ 寻找项目\n\n"
                "• 关注Twitter #Airdrop\n"
                "• 查看CoinGecko新币\n"
                "• 加入项目Discord\n"
                "• 参考空投聚合网站",

                "2/ 评估项目\n\n"
                "✅ 团队背景\n"
                "✅ 融资情况\n"
                "✅ 社区活跃度\n"
                "✅ 技术创新性",

                "3/ 风险管理\n\n"
                "⚠️ 小资金多项目\n"
                "⚠️ 谨防钓鱼\n"
                "⚠️ 长期持有\n"
                "⚠️ 定期清理",

                "📌 总结\n\n"
                "执行力 > 完美主义 💪\n\n"
                "小步快跑，复利增长 📈\n\n"
                "💬 你的策略是什么？\n\n"
                "🔗 https://x.com/ZYER55\n\n"
                "#Airdrop #Crypto #WAGMI #执行力"
            ]
            return thread

        thread = []

        # 第1条：引言
        total_potential = sum(p.reward for p in active_projects if p.reward > 0)
        thread.append(f"🧵 当前撸毛组合 | ZYER\n\n"
                     f"追踪中: {len(active_projects)}个项目\n"
                     f"💰 总预期收益: ${total_potential:.0f}\n"
                     f"🔥 高潜力项目数: {len([p for p in active_projects if p.potential == 'high'])}\n\n"
                     f"👇 详细分析\n\n"
                     f"不擅长但能做好 🚀\n\n"
                     f"🔗 https://x.com/ZYER55")

        # 中间条目：按类别分组
        categories = {}
        for p in active_projects:
            cat = p.category or '其他'
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(p)

        for category, projects_in_cat in categories.items():
            tweet = f"📂 {category} ({len(projects_in_cat)}个)\n\n"
            for p in projects_in_cat[:3]:
                tweet += f"• {p.name} ({p.chain})\n"
            if len(projects_in_cat) > 3:
                tweet += f"...还有 {len(projects_in_cat) - 3} 个"
            thread.append(tweet)

        # 最后1条：总结
        thread.append("📌 总结 | ZYER\n\n"
                     "✅ 坚持执行\n"
                     "✅ 分散投资\n"
                     "✅ 及时复投\n\n"
                     "小步快跑，复利增长 📈\n\n"
                     "💬 你的策略是什么？\n\n"
                     "🔗 https://x.com/ZYER55\n\n"
                     "#Airdrop #Crypto #WAGMI #执行力")

        return thread

    @staticmethod
    def generate_gm_check(projects):
        """生成GM打卡推文"""
        from datetime import datetime
        import random

        active_count = len([p for p in projects if p.status == 'tracking'])

        if active_count == 0:
            # 没有项目时的GM推文
            gm_templates = [
                "GM! ☀️\n\nZYER ready to build! 🚀\n\n今日计划：\n✅ 寻找新机会\n✅ 定投执行\n✅ 学习提升\n✅ 坚持GM打卡\n\n不擅长但能做好 | 执行力 🔥\n\n🔗 https://x.com/ZYER55\n\n#GM #Crypto #WAGMI #执行力",

                f"GM! Day {datetime.now().strftime('%j')} of the year 🌅\n\n定投 + 学习 = 持续成长 📈\n小步快跑，持续迭代 🚀\n\n💬 你的今日GM是什么？\n\n🔗 https://x.com/ZYER55\n\n#GM #Crypto #定投"
            ]
        else:
            gm_templates = [
                f"GM! ☀️\n\nZYER ready to grind! 🚀\n\n今日计划：\n✅ 追踪{active_count}个撸毛项目\n✅ 定投执行\n✅ 学习提升\n✅ 坚持GM打卡\n\n不擅长但能做好 | 执行力 🔥\n\n🔗 https://x.com/ZYER55\n\n#GM #Crypto #WAGMI #执行力",

                f"GM! Day {datetime.now().strftime('%j')} of the year 🌅\n\n定投 + 撸毛 = 复利增长 📈\n\n当前追踪：{active_count}个项目\n小步快跑，持续迭代 🚀\n\n💬 你的今日GM是什么？\n\n🔗 https://x.com/ZYER55\n\n#GM #Crypto #定投",

                f"GM! ☕\n\n又是一个崭新的开始 ✨\n\nZYER的今日专注：\n• {active_count}个空投项目追踪中\n• 坚持定投计划\n• 持续学习成长\n\n不擅长但能做好 🎯\n\n🔗 https://x.com/ZYER55\n\n#GM #Crypto #执行力 #WAGMI"
            ]

        return random.choice(gm_templates)

    @staticmethod
    def generate_weekly_summary(projects):
        """生成周总结推文"""
        active_projects = [p for p in projects if p.status == 'tracking']
        claimed_projects = [p for p in projects if p.status == 'claimed']

        total_investment = sum(p.investment for p in projects)
        expected_reward = sum(p.reward for p in active_projects if p.reward > 0)
        actual_reward = sum(p.actual_reward for p in claimed_projects)

        content = f"📊 本周撸毛总结 | ZYER\n\n"
        content += f"📱 追踪中: {len(active_projects)}个项目\n"
        content += f"✅ 已申领: {len(claimed_projects)}个\n\n"
        content += f"💰 总投入: ${total_investment:.2f}\n"
        content += f"🎁 预期收益: ${expected_reward:.2f}\n"

        if actual_reward > 0:
            content += f"💵 已到账: ${actual_reward:.2f}\n"

        content += f"\n坚持执行，持续迭代 🚀\n\n"
        content += f"💬 本周最大的收获是什么？\n\n"
        content += f"🔗 https://x.com/ZYER55\n\n"
        content += f"#Crypto #Airdrop #WAGMI #定投"

        return content

    @staticmethod
    def generate_motivation_quote(projects):
        """生成励志语录推文"""
        import random

        quotes = [
            "不擅长但能做好，这就是执行力 🔥\n\n坚持定投，坚持撸毛，坚持GM打卡\n小步快跑，复利增长 📈\n\nZYER | 一直在路上 🚀\n\n🔗 https://x.com/ZYER55\n\n#Crypto #Motivation #WAGMI",

            "开始是最好的时机 🔥\n\n不管行情如何，坚持定投\n不管项目多小，坚持追踪\n不管多忙，坚持GM打卡\n\nZYER | 不擅长但能做好 💪\n\n🔗 https://x.com/ZYER55\n\n#Crypto #执行力 #定投",

            "复利的力量 📈\n\n每天进步1%，一年后你会强大37倍\n• 每日GM打卡\n• 每周项目追踪\n• 每月定投执行\n\nZYER | 小步快跑，持续迭代 🚀\n\n🔗 https://x.com/ZYER55\n\n#Crypto #WAGMI #成长",

            "执行力 > 完美主义 💪\n\n不等待完美的时机\n不追求完美的开始\n只需要完美的执行\n\nZYER | 定投 + 撸毛双轮驱动 🚀\n\n🔗 https://x.com/ZYER55\n\n#Crypto #执行力 #定投"
        ]

        return random.choice(quotes)

# 路由
@app.route('/')
def index():
    """首页"""
    return render_template('index.html')

@app.route('/api/projects', methods=['GET'])
def get_projects():
    """获取所有项目"""
    projects = AirdropProject.query.order_by(AirdropProject.created_at.desc()).all()
    return jsonify({
        'success': True,
        'projects': [p.to_dict() for p in projects]
    })

@app.route('/api/projects', methods=['POST'])
def create_project():
    """创建新项目"""
    data = request.json

    try:
        project = AirdropProject(
            name=data.get('name'),
            description=data.get('description'),
            chain=data.get('chain'),
            category=data.get('category'),
            potential=data.get('potential'),
            investment=float(data.get('investment', 0)),
            reward=float(data.get('reward', 0)),
            total_tasks=int(data.get('total_tasks', 0)),
            tasks_completed=int(data.get('tasks_completed', 0)),
            deadline=datetime.fromisoformat(data['deadline']) if data.get('deadline') else None,
            reminder_date=datetime.fromisoformat(data['reminder_date']) if data.get('reminder_date') else None,
            links=json.dumps(data.get('links', [])),
            notes=data.get('notes')
        )

        db.session.add(project)
        db.session.commit()

        # 记录活动日志
        log = ActivityLog(
            project_id=project.id,
            action='created',
            description=f'创建项目: {project.name}'
        )
        db.session.add(log)
        db.session.commit()

        return jsonify({
            'success': True,
            'project': project.to_dict()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/projects/<int:project_id>', methods=['PUT'])
def update_project(project_id):
    """更新项目"""
    project = AirdropProject.query.get_or_404(project_id)
    data = request.json

    try:
        project.name = data.get('name', project.name)
        project.description = data.get('description', project.description)
        project.chain = data.get('chain', project.chain)
        project.category = data.get('category', project.category)
        project.status = data.get('status', project.status)
        project.potential = data.get('potential', project.potential)
        project.investment = float(data.get('investment', project.investment))
        project.reward = float(data.get('reward', project.reward))
        project.actual_reward = float(data.get('actual_reward', project.actual_reward))
        project.tasks_completed = int(data.get('tasks_completed', project.tasks_completed))
        project.total_tasks = int(data.get('total_tasks', project.total_tasks))

        if data.get('deadline'):
            project.deadline = datetime.fromisoformat(data['deadline'])
        if data.get('reminder_date'):
            project.reminder_date = datetime.fromisoformat(data['reminder_date'])

        project.links = json.dumps(data.get('links', []))
        project.notes = data.get('notes', project.notes)

        db.session.commit()

        # 记录活动日志
        log = ActivityLog(
            project_id=project.id,
            action='updated',
            description=f'更新项目: {project.name}'
        )
        db.session.add(log)
        db.session.commit()

        return jsonify({
            'success': True,
            'project': project.to_dict()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/projects/<int:project_id>', methods=['DELETE'])
def delete_project(project_id):
    """删除项目"""
    project = AirdropProject.query.get_or_404(project_id)

    try:
        project_name = project.name
        db.session.delete(project)
        db.session.commit()

        # 记录活动日志
        log = ActivityLog(
            action='deleted',
            description=f'删除项目: {project_name}'
        )
        db.session.add(log)
        db.session.commit()

        return jsonify({
            'success': True
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """获取统计信息"""
    projects = AirdropProject.query.all()

    active_projects = [p for p in projects if p.status == 'tracking']
    claimed_projects = [p for p in projects if p.status == 'claimed']

    total_investment = sum(p.investment for p in projects)
    total_reward = sum(p.actual_reward for p in projects)
    expected_reward = sum(p.reward for p in active_projects if p.reward > 0)

    return jsonify({
        'success': True,
        'stats': {
            'total_projects': len(projects),
            'active_projects': len(active_projects),
            'claimed_projects': len(claimed_projects),
            'total_investment': round(total_investment, 2),
            'total_reward': round(total_reward, 2),
            'expected_reward': round(expected_reward, 2),
            'roi': round((total_reward - total_investment) / total_investment * 100, 2) if total_investment > 0 else 0
        }
    })

@app.route('/api/generate-content', methods=['POST'])
def generate_content():
    """生成X内容"""
    data = request.json
    content_type = data.get('type', 'daily')
    project_id = data.get('project_id')

    projects = AirdropProject.query.all()

    generator = XContentGenerator()

    if content_type == 'daily':
        content = generator.generate_daily_projects(projects)
    elif content_type == 'roi':
        content = generator.generate_roi_report(projects)
    elif content_type == 'spotlight':
        project = AirdropProject.query.get(project_id) if project_id else None
        content = generator.generate_project_spotlight(project)
    elif content_type == 'thread':
        content = generator.generate_thread(projects)
    elif content_type == 'gm':
        content = generator.generate_gm_check(projects)
    elif content_type == 'weekly':
        content = generator.generate_weekly_summary(projects)
    elif content_type == 'motivation':
        content = generator.generate_motivation_quote(projects)
    else:
        return jsonify({
            'success': False,
            'error': 'Invalid content type'
        }), 400

    if content:
        return jsonify({
            'success': True,
            'content': content
        })
    else:
        return jsonify({
            'success': False,
            'error': 'No content generated'
        }), 400

@app.route('/api/logs', methods=['GET'])
def get_logs():
    """获取活动日志"""
    logs = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(50).all()
    return jsonify({
        'success': True,
        'logs': [log.to_dict() for log in logs]
    })

# 定时任务：检查提醒
def check_reminders():
    """检查需要提醒的项目"""
    with app.app_context():
        now = datetime.now()
        upcoming = now + timedelta(hours=24)

        projects = AirdropProject.query.filter(
            AirdropProject.reminder_date.between(now, upcoming),
            AirdropProject.status == 'tracking'
        ).all()

        for project in projects:
            log = ActivityLog(
                project_id=project.id,
                action='reminder',
                description=f'提醒: {project.name} 需要关注'
            )
            db.session.add(log)
        db.session.commit()

# 启动定时任务
scheduler = BackgroundScheduler()
scheduler.add_job(func=check_reminders, trigger="interval", hours=1)
scheduler.start()

atexit.register(lambda: scheduler.shutdown())

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
