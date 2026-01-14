// 全局变量
let projects = [];

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', function() {
    loadProjects();
    loadStats();
    loadLogs();

    // 添加textarea监听器
    const textarea = document.getElementById('contentText');
    if (textarea) {
        textarea.addEventListener('input', updateCharCount);
    }
});

// 加载项目列表
async function loadProjects() {
    try {
        const response = await fetch('/api/projects');
        const data = await response.json();

        if (data.success) {
            projects = data.projects;
            displayProjects(projects);
        }
    } catch (error) {
        console.error('加载项目失败:', error);
    }
}

// 显示项目列表
function displayProjects(projects) {
    const container = document.getElementById('projectsList');

    if (!projects || projects.length === 0) {
        container.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 40px; color: var(--text-secondary);">暂无项目，点击上方按钮添加第一个项目</div>';
        return;
    }

    container.innerHTML = projects.map(project => `
        <div class="project-card">
            <div class="project-header">
                <div>
                    <div class="project-title">${project.name}</div>
                    <div class="project-meta">
                        <span class="badge badge-chain">${project.chain || 'N/A'}</span>
                        <span class="badge badge-category">${project.category || '其他'}</span>
                        <span class="badge badge-status-${project.status}">${getStatusText(project.status)}</span>
                        ${project.potential ? `<span class="badge badge-potential-${project.potential}">${getPotentialText(project.potential)}</span>` : ''}
                    </div>
                </div>
            </div>

            ${project.description ? `<div class="project-description">${project.description}</div>` : ''}

            <div class="project-stats">
                <div class="stat-item">
                    <span>投入:</span>
                    <span>$${project.investment.toFixed(2)}</span>
                </div>
                <div class="stat-item">
                    <span>预期:</span>
                    <span>$${project.reward.toFixed(2)}</span>
                </div>
                ${project.actual_reward > 0 ? `
                <div class="stat-item">
                    <span>实际:</span>
                    <span>$${project.actual_reward.toFixed(2)}</span>
                </div>
                ` : ''}
                ${project.roi !== 0 ? `
                <div class="stat-item">
                    <span>ROI:</span>
                    <span style="color: ${project.roi >= 0 ? 'var(--success-color)' : 'var(--danger-color)'}">${project.roi}%</span>
                </div>
                ` : ''}
                ${project.total_tasks > 0 ? `
                <div class="stat-item" style="grid-column: 1/-1;">
                    <span>进度:</span>
                    <span>${project.tasks_completed}/${project.total_tasks}</span>
                </div>
                ` : ''}
            </div>

            ${project.deadline ? `
            <div style="margin-bottom: 15px; font-size: 0.875rem; color: var(--text-secondary);">
                ⏰ 截止: ${formatDate(project.deadline)}
            </div>
            ` : ''}

            <div class="project-actions">
                <button class="btn btn-primary btn-sm" onclick="editProject(${project.id})">编辑</button>
                <button class="btn btn-outline btn-sm" onclick="generateSpotlight(${project.id})">生成推文</button>
                <button class="btn btn-danger btn-sm" onclick="deleteProject(${project.id})">删除</button>
            </div>
        </div>
    `).join('');
}

// 加载统计信息
async function loadStats() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();

        if (data.success) {
            const stats = data.stats;
            document.getElementById('totalProjects').textContent = stats.total_projects;
            document.getElementById('activeProjects').textContent = stats.active_projects;
            document.getElementById('claimedProjects').textContent = stats.claimed_projects;
            document.getElementById('totalInvestment').textContent = `$${stats.total_investment.toFixed(2)}`;
            document.getElementById('totalReward').textContent = `$${stats.total_reward.toFixed(2)}`;
            document.getElementById('totalROI').textContent = `${stats.roi}%`;
            document.getElementById('totalROI').style.color = stats.roi >= 0 ? 'var(--success-color)' : 'var(--danger-color)';
        }
    } catch (error) {
        console.error('加载统计失败:', error);
    }
}

// 加载活动日志
async function loadLogs() {
    try {
        const response = await fetch('/api/logs');
        const data = await response.json();

        if (data.success) {
            displayLogs(data.logs);
        }
    } catch (error) {
        console.error('加载日志失败:', error);
    }
}

// 显示日志
function displayLogs(logs) {
    const container = document.getElementById('activityLog');

    if (!logs || logs.length === 0) {
        container.innerHTML = '<div style="padding: 20px; text-align: center; color: var(--text-secondary);">暂无活动记录</div>';
        return;
    }

    container.innerHTML = logs.map(log => `
        <div class="log-entry">
            <div class="log-time">${formatDateTime(log.created_at)}</div>
            <div class="log-action">${getActionText(log.action)}</div>
            <div style="color: var(--text-secondary);">${log.description}</div>
        </div>
    `).join('');
}

// 显示添加模态框
function showAddModal() {
    document.getElementById('modalTitle').textContent = '新增项目';
    document.getElementById('projectForm').reset();
    document.getElementById('projectId').value = '';
    document.getElementById('projectModal').style.display = 'block';
}

// 编辑项目
function editProject(projectId) {
    const project = projects.find(p => p.id === projectId);
    if (!project) return;

    document.getElementById('modalTitle').textContent = '编辑项目';
    document.getElementById('projectId').value = project.id;
    document.getElementById('projectName').value = project.name;
    document.getElementById('projectDescription').value = project.description || '';
    document.getElementById('projectChain').value = project.chain || '';
    document.getElementById('projectCategory').value = project.category || '';
    document.getElementById('projectStatus').value = project.status;
    document.getElementById('projectPotential').value = project.potential || '';
    document.getElementById('projectInvestment').value = project.investment;
    document.getElementById('projectReward').value = project.reward;
    document.getElementById('projectActualReward').value = project.actual_reward;
    document.getElementById('projectTotalTasks').value = project.total_tasks;
    document.getElementById('projectTasksCompleted').value = project.tasks_completed;

    if (project.deadline) {
        document.getElementById('projectDeadline').value = project.deadline.substring(0, 16);
    }
    if (project.reminder_date) {
        document.getElementById('projectReminder').value = project.reminder_date.substring(0, 16);
    }

    document.getElementById('projectNotes').value = project.notes || '';
    document.getElementById('projectModal').style.display = 'block';
}

// 保存项目
async function saveProject(event) {
    event.preventDefault();

    const projectId = document.getElementById('projectId').value;
    const data = {
        name: document.getElementById('projectName').value,
        description: document.getElementById('projectDescription').value,
        chain: document.getElementById('projectChain').value,
        category: document.getElementById('projectCategory').value,
        status: document.getElementById('projectStatus').value,
        potential: document.getElementById('projectPotential').value,
        investment: parseFloat(document.getElementById('projectInvestment').value) || 0,
        reward: parseFloat(document.getElementById('projectReward').value) || 0,
        actual_reward: parseFloat(document.getElementById('projectActualReward').value) || 0,
        total_tasks: parseInt(document.getElementById('projectTotalTasks').value) || 0,
        tasks_completed: parseInt(document.getElementById('projectTasksCompleted').value) || 0,
        deadline: document.getElementById('projectDeadline').value || null,
        reminder_date: document.getElementById('projectReminder').value || null,
        notes: document.getElementById('projectNotes').value
    };

    try {
        const url = projectId ? `/api/projects/${projectId}` : '/api/projects';
        const method = projectId ? 'PUT' : 'POST';

        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (result.success) {
            closeModal();
            loadProjects();
            loadStats();
            loadLogs();
            alert('保存成功！');
        } else {
            alert('保存失败: ' + result.error);
        }
    } catch (error) {
        console.error('保存失败:', error);
        alert('保存失败: ' + error.message);
    }
}

// 删除项目
async function deleteProject(projectId) {
    if (!confirm('确定要删除这个项目吗？')) return;

    try {
        const response = await fetch(`/api/projects/${projectId}`, {
            method: 'DELETE'
        });

        const result = await response.json();

        if (result.success) {
            loadProjects();
            loadStats();
            loadLogs();
            alert('删除成功！');
        } else {
            alert('删除失败: ' + result.error);
        }
    } catch (error) {
        console.error('删除失败:', error);
        alert('删除失败: ' + error.message);
    }
}

// 生成X内容
async function generateContent(type) {
    try {
        // 显示加载状态
        const textarea = document.getElementById('contentText');
        textarea.value = '⏳ 正在生成内容...';
        textarea.disabled = true;

        const response = await fetch('/api/generate-content', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ type })
        });

        const result = await response.json();

        if (result.success) {
            const container = document.getElementById('generatedContent');

            if (Array.isArray(result.content)) {
                textarea.value = result.content.join('\n\n---\n\n');
            } else {
                textarea.value = result.content;
            }

            textarea.disabled = false;
            updateCharCount();
            container.style.display = 'block';

            // 滚动到生成内容
            textarea.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        } else {
            textarea.value = '';
            textarea.disabled = false;
            alert('生成失败: ' + result.error);
        }
    } catch (error) {
        console.error('生成失败:', error);
        const textarea = document.getElementById('contentText');
        textarea.value = '';
        textarea.disabled = false;
        alert('生成失败: ' + error.message);
    }
}

// 更新字符计数
function updateCharCount() {
    const textarea = document.getElementById('contentText');
    const charCount = document.getElementById('charCount');
    const count = textarea.value.length;

    charCount.textContent = `${count} 字符`;

    // X推文限制是280字符，Thread每条也是
    if (count > 280) {
        charCount.style.color = 'var(--danger-color)';
    } else if (count > 250) {
        charCount.style.color = 'var(--warning-color)';
    } else {
        charCount.style.color = 'var(--text-secondary)';
    }
}

// 生成项目亮点推文
async function generateSpotlight(projectId) {
    try {
        const response = await fetch('/api/generate-content', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                type: 'spotlight',
                project_id: projectId
            })
        });

        const result = await response.json();

        if (result.success) {
            const container = document.getElementById('generatedContent');
            document.getElementById('contentText').value = result.content;
            container.style.display = 'block';
        } else {
            alert('生成失败: ' + result.error);
        }
    } catch (error) {
        console.error('生成失败:', error);
        alert('生成失败: ' + error.message);
    }
}

// 复制内容
function copyContent() {
    const textarea = document.getElementById('contentText');
    textarea.select();
    textarea.setSelectionRange(0, 99999); // 兼容移动设备

    try {
        navigator.clipboard.writeText(textarea.value).then(() => {
            // 显示成功提示
            const btn = event.target;
            const originalText = btn.innerHTML;
            btn.innerHTML = '✅ 已复制！';
            btn.disabled = true;

            setTimeout(() => {
                btn.innerHTML = originalText;
                btn.disabled = false;
            }, 2000);
        });
    } catch (err) {
        // 降级方案
        document.execCommand('copy');
        alert('已复制到剪贴板！');
    }
}

// 清空内容
function clearContent() {
    document.getElementById('contentText').value = '';
    updateCharCount();
}

// 打开X发布
function openInX() {
    const textarea = document.getElementById('contentText');
    const content = textarea.value.trim();

    if (!content) {
        alert('请先生成或输入内容！');
        return;
    }

    // X的发布URL
    const twitterUrl = `https://twitter.com/intent/tweet?text=${encodeURIComponent(content)}`;
    window.open(twitterUrl, '_blank');
}

// 关闭模态框
function closeModal() {
    document.getElementById('projectModal').style.display = 'none';
}

// 点击模态框外部关闭
window.onclick = function(event) {
    const modal = document.getElementById('projectModal');
    if (event.target == modal) {
        modal.style.display = 'none';
    }
}

// 工具函数
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
    });
}

function formatDateTime(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN', {
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function getStatusText(status) {
    const statusMap = {
        'tracking': '进行中',
        'claimed': '已申领',
        'ended': '已结束'
    };
    return statusMap[status] || status;
}

function getPotentialText(potential) {
    const potentialMap = {
        'high': '高潜力',
        'medium': '中潜力',
        'low': '低潜力'
    };
    return potentialMap[potential] || potential;
}

function getActionText(action) {
    const actionMap = {
        'created': '✅ 创建',
        'updated': '✏️ 更新',
        'deleted': '🗑️ 删除',
        'reminder': '⏰ 提醒'
    };
    return actionMap[action] || action;
}
