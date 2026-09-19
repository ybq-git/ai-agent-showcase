from dataclasses import dataclass, field
from datetime import datetime
import hashlib, json

@dataclass
class ActionTicket:
    action: str          # 什么操作："publish_listing"
    target: str          # 对谁："B0WATER02"
    params: dict         # 参数：{"asin": "B0WATER02"}
    status: str          # "PENDING_HUMAN_APPROVAL"（待人工）或 "APPROVED" 等
    request_hash: str    # 请求指纹（幂等用）
    created_at: str      # 创建时间


def hash_request(action: str, params: dict) -> str:
    """把"操作+参数"变成唯一指纹：同一操作同一参数 => 同一个哈希。"""
    payload = json.dumps({"action": action, "params": params}, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
_seen_requests = {}     # request_hash -> ticket，模拟数据库

WRITE_ACTIONS = {"publish_listing", "change_price"}   # 哪些是写操作

def create_action_ticket(action: str, params: dict) -> ActionTicket:
    """写操作的唯一入口：先查重（幂等），再只建审批单，绝不真执行。"""
    req_hash = hash_request(action, params)

    # 1) 幂等查重：这个请求见过吗？
    if req_hash in _seen_requests:
        old = _seen_requests[req_hash]
        return ActionTicket(
            action=old.action, target=old.target, params=old.params,
            status="DUPLICATE_BLOCKED", request_hash=req_hash,
            created_at=old.created_at,
    )


    # 2) 写操作 => 只建审批单，不执行
    ticket = ActionTicket(
        action=action,
        target=str(params.get("asin", params.get("target", ""))),
        params=params,
        status="PENDING_HUMAN_APPROVAL",
        request_hash=req_hash,
        created_at=datetime.now().isoformat(),
    )
    _seen_requests[req_hash] = ticket
    return ticket
