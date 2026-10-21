from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from tickets.models import (
    Category,
    Comment,
    Priority,
    Role,
    StatusLog,
    Ticket,
    TicketStatus,
    UserProfile,
)

User = get_user_model()


class Command(BaseCommand):
    help = "创建演示用户、分类和工单"

    def handle(self, *args, **options):
        admin = self._user("admin", "admin@example.com", "admin123", Role.ADMIN, superuser=True)
        agent = self._user("agent", "agent@example.com", "agent123", Role.AGENT)
        employee = self._user("employee", "employee@example.com", "employee123", Role.EMPLOYEE)

        categories = {}
        for index, name in enumerate(["网络", "设备", "账号", "其他"]):
            category, _ = Category.objects.get_or_create(name=name, defaults={"sort": index})
            categories[name] = category

        if Ticket.objects.exists():
            self.stdout.write("工单已存在，跳过工单创建")
        else:
            now = timezone.now()
            tickets = [
                (
                    "办公室无线网络频繁掉线",
                    "三楼东侧办公室 Wi-Fi 每隔十几分钟断一次，重启路由器后短暂恢复。",
                    "网络",
                    Priority.HIGH,
                    TicketStatus.OPEN,
                    None,
                    None,
                ),
                (
                    "打印机无法连接",
                    "财务室打印机在电脑上显示离线，重启打印机无效。",
                    "设备",
                    Priority.MEDIUM,
                    TicketStatus.IN_PROGRESS,
                    agent,
                    None,
                ),
                (
                    "邮箱密码需要重置",
                    "无法登录公司邮箱，提示密码错误。",
                    "账号",
                    Priority.URGENT,
                    TicketStatus.RESOLVED,
                    agent,
                    now - timedelta(hours=5),
                ),
                (
                    "申请安装办公软件",
                    "新电脑需要安装 Office 和内部 VPN 客户端。",
                    "其他",
                    Priority.LOW,
                    TicketStatus.CLOSED,
                    agent,
                    now - timedelta(days=1),
                ),
            ]
            for title, description, category_name, priority, status, assigned_to, resolved_at in tickets:
                ticket = Ticket.objects.create(
                    title=title,
                    description=description,
                    category=categories[category_name],
                    priority=priority,
                    status=status,
                    created_by=employee,
                    assigned_to=assigned_to,
                    resolved_at=resolved_at,
                )
                StatusLog.objects.create(
                    ticket=ticket,
                    from_status="",
                    to_status=TicketStatus.OPEN,
                    operator=employee,
                    note="创建工单",
                )
                if assigned_to:
                    StatusLog.objects.create(
                        ticket=ticket,
                        from_status=TicketStatus.OPEN,
                        to_status=TicketStatus.IN_PROGRESS,
                        operator=admin,
                        note=f"指派给 {assigned_to.username}",
                    )
                if status in (TicketStatus.RESOLVED, TicketStatus.CLOSED):
                    StatusLog.objects.create(
                        ticket=ticket,
                        from_status=TicketStatus.IN_PROGRESS,
                        to_status=TicketStatus.RESOLVED,
                        operator=agent,
                        note="问题已处理",
                    )
                if status == TicketStatus.CLOSED:
                    StatusLog.objects.create(
                        ticket=ticket,
                        from_status=TicketStatus.RESOLVED,
                        to_status=TicketStatus.CLOSED,
                        operator=employee,
                        note="确认关闭",
                    )
                if status == TicketStatus.RESOLVED:
                    Comment.objects.create(
                        ticket=ticket,
                        author=agent,
                        content="已重置密码，请用新密码登录后及时修改。",
                    )

        self.stdout.write(self.style.SUCCESS("seed ok"))
        self.stdout.write("admin    / admin123")
        self.stdout.write("agent    / agent123")
        self.stdout.write("employee / employee123")

    def _user(self, username, email, password, role, superuser=False):
        user = User.objects.filter(username=username).first()
        if user is None:
            if superuser:
                user = User.objects.create_superuser(username=username, email=email, password=password)
            else:
                user = User.objects.create_user(username=username, email=email, password=password)
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.role = role
        profile.save()
        return user
