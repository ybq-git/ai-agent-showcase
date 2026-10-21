from tickets.models import Role, Ticket, TicketStatus, TRANSITIONS, UserProfile


def get_role(user) -> str:
    if not user.is_authenticated:
        return ""
    if user.is_superuser:
        return Role.ADMIN
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile.role


def is_agent(user) -> bool:
    return get_role(user) in (Role.AGENT, Role.ADMIN)


def is_admin(user) -> bool:
    return get_role(user) == Role.ADMIN


def can_view_ticket(user, ticket: Ticket) -> bool:
    if not user.is_authenticated:
        return False
    if is_agent(user):
        return True
    return ticket.created_by_id == user.id


def can_assign(user) -> bool:
    return is_agent(user)


def can_change_status(user) -> bool:
    return is_agent(user)


def can_edit_ticket(user, ticket: Ticket) -> bool:
    if is_agent(user):
        return True
    return ticket.created_by_id == user.id and ticket.status == TicketStatus.OPEN


def valid_transition(current: str, target: str) -> bool:
    return target in TRANSITIONS.get(current, set())
