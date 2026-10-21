import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from tickets.models import (
    Attachment,
    Category,
    Comment,
    Priority,
    Role,
    StatusLog,
    Ticket,
    TicketStatus,
)

User = get_user_model()


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class TicketBaseTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser("admin", "admin@example.com", "admin123")
        cls.agent = User.objects.create_user("agent", "agent@example.com", "agent123")
        cls.employee = User.objects.create_user("employee", "employee@example.com", "employee123")
        cls.employee2 = User.objects.create_user("employee2", "employee2@example.com", "employee123")

        cls.agent.profile.role = Role.AGENT
        cls.agent.profile.save()
        cls.employee2.profile.role = Role.EMPLOYEE
        cls.employee2.profile.save()

        cls.category = Category.objects.create(name="网络", sort=0)
        cls.ticket = Ticket.objects.create(
            title="办公室网络掉线",
            description="三楼 Wi-Fi 频繁断开",
            category=cls.category,
            priority=Priority.HIGH,
            created_by=cls.employee,
        )
        cls.other_ticket = Ticket.objects.create(
            title="打印机离线",
            description="财务室打印机显示离线",
            category=cls.category,
            priority=Priority.MEDIUM,
            created_by=cls.employee2,
        )

    def setUp(self):
        cache.clear()
        mail.outbox = []

    def login(self, username, password):
        self.assertTrue(self.client.login(username=username, password=password))


class AuthAndVisibilityTests(TicketBaseTestCase):
    def test_pages_render(self):
        self.assertEqual(self.client.get(reverse("login")).status_code, 200)

        self.login("employee", "employee123")
        self.assertEqual(self.client.get(reverse("ticket_list")).status_code, 200)
        self.assertEqual(self.client.get(reverse("ticket_create")).status_code, 200)
        self.assertEqual(
            self.client.get(reverse("ticket_detail", args=[self.ticket.pk])).status_code, 200
        )

        self.login("agent", "agent123")
        self.assertEqual(
            self.client.get(reverse("ticket_detail", args=[self.ticket.pk])).status_code, 200
        )
        self.assertEqual(self.client.get(reverse("dashboard")).status_code, 200)

    def test_login_required(self):
        response = self.client.get(reverse("ticket_list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_employee_sees_only_own_tickets(self):
        self.login("employee", "employee123")
        response = self.client.get(reverse("ticket_list"))
        self.assertContains(response, "办公室网络掉线")
        self.assertNotContains(response, "打印机离线")

    def test_agent_sees_all_tickets(self):
        self.login("agent", "agent123")
        response = self.client.get(reverse("ticket_list"))
        self.assertContains(response, "办公室网络掉线")
        self.assertContains(response, "打印机离线")

    def test_employee_cannot_view_other_ticket(self):
        self.login("employee", "employee123")
        response = self.client.get(reverse("ticket_detail", args=[self.other_ticket.pk]))
        self.assertEqual(response.status_code, 403)


class TicketWorkflowTests(TicketBaseTestCase):
    def test_create_ticket_sets_creator_and_log(self):
        self.login("employee", "employee123")
        response = self.client.post(
            reverse("ticket_create"),
            {
                "title": "账号无法登录",
                "description": "OA 账号提示密码错误",
                "category": self.category.pk,
                "priority": Priority.URGENT,
            },
        )
        self.assertEqual(response.status_code, 302)
        ticket = Ticket.objects.get(title="账号无法登录")
        self.assertEqual(ticket.created_by, self.employee)
        self.assertEqual(ticket.status, TicketStatus.OPEN)
        self.assertTrue(StatusLog.objects.filter(ticket=ticket).exists())

    def test_agent_assigns_and_notification_is_sent(self):
        self.login("agent", "agent123")
        response = self.client.post(
            reverse("ticket_assign", args=[self.ticket.pk]),
            {"agent": self.agent.pk},
        )
        self.assertEqual(response.status_code, 302)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.assigned_to, self.agent)
        self.assertEqual(self.ticket.status, TicketStatus.IN_PROGRESS)
        self.assertTrue(StatusLog.objects.filter(ticket=self.ticket, note__contains="指派").exists())
        self.assertTrue(mail.outbox)

    def test_status_machine(self):
        self.login("agent", "agent123")
        self.ticket.status = TicketStatus.OPEN
        self.ticket.save()

        invalid = self.client.post(
            reverse("ticket_update_status", args=[self.ticket.pk]),
            {"status": TicketStatus.CLOSED},
        )
        self.assertEqual(invalid.status_code, 302)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, TicketStatus.OPEN)

        self.client.post(
            reverse("ticket_update_status", args=[self.ticket.pk]),
            {"status": TicketStatus.IN_PROGRESS},
        )
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, TicketStatus.IN_PROGRESS)

        self.client.post(
            reverse("ticket_update_status", args=[self.ticket.pk]),
            {"status": TicketStatus.RESOLVED},
        )
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, TicketStatus.RESOLVED)
        self.assertIsNotNone(self.ticket.resolved_at)

        self.client.post(
            reverse("ticket_update_status", args=[self.ticket.pk]),
            {"status": TicketStatus.CLOSED},
        )
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, TicketStatus.CLOSED)

    def test_employee_cannot_assign_or_change_status(self):
        self.login("employee", "employee123")
        self.assertEqual(
            self.client.post(
                reverse("ticket_assign", args=[self.ticket.pk]), {"agent": self.agent.pk}
            ).status_code,
            403,
        )
        self.assertEqual(
            self.client.post(
                reverse("ticket_update_status", args=[self.ticket.pk]),
                {"status": TicketStatus.IN_PROGRESS},
            ).status_code,
            403,
        )


class CommentAttachmentTests(TicketBaseTestCase):
    def test_comment_and_attachment(self):
        self.login("employee", "employee123")
        response = self.client.post(
            reverse("add_comment", args=[self.ticket.pk]),
            {"content": "补充：重启路由器后仍然掉线"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Comment.objects.filter(ticket=self.ticket).exists())

        media_root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, media_root, ignore_errors=True)
        with override_settings(MEDIA_ROOT=media_root):
            upload = SimpleUploadedFile("log.txt", b"network log", content_type="text/plain")
            response = self.client.post(
                reverse("add_attachment", args=[self.ticket.pk]),
                {"file": upload},
            )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Attachment.objects.filter(ticket=self.ticket).exists())


class DashboardAndAdminTests(TicketBaseTestCase):
    def test_dashboard_permissions(self):
        self.login("employee", "employee123")
        self.assertEqual(self.client.get(reverse("dashboard")).status_code, 403)

        self.login("agent", "agent123")
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "平均解决时长")

    def test_user_management_admin_only(self):
        self.login("agent", "agent123")
        self.assertEqual(self.client.get(reverse("user_management")).status_code, 403)

        self.login("admin", "admin123")
        response = self.client.get(reverse("user_management"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "用户管理")

    def test_admin_changes_role_and_toggles_user(self):
        self.login("admin", "admin123")
        self.client.post(
            reverse("change_role", args=[self.employee2.pk]),
            {"role": Role.AGENT},
        )
        self.employee2.profile.refresh_from_db()
        self.assertEqual(self.employee2.profile.role, Role.AGENT)

        self.client.post(reverse("toggle_user", args=[self.employee2.pk]))
        self.employee2.refresh_from_db()
        self.assertFalse(self.employee2.is_active)
