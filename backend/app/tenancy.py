"""Which tenant a request belongs to.

A fixed stub: the Next.js proxy always sends X-Tenant-Id: dev. The project has
no login (decided 2026-09-11), so there is one tenant.
"""

import re
from typing import Annotated

from fastapi import Header, HTTPException, status

# A letter or digit, then letters, digits, dash, underscore: 1 to 64 characters.
# The value is written to logs and used as the AgentCore Memory actor id (which must
# start with a letter or digit), so anything else is rejected before it can fake a
# log line or break a call.
_TENANT_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}")


def get_tenant_id(x_tenant_id: Annotated[str | None, Header()] = None) -> str:
    # The parameter name x_tenant_id is read from the "x-tenant-id" header.
    # https://fastapi.tiangolo.com/tutorial/header-params/
    # ponytail: trusts the header. Ceiling: any caller can claim any tenant.
    # Upgrade: read the tenant from a verified login token (for example Cognito).
    if x_tenant_id is None or not _TENANT_ID.fullmatch(x_tenant_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Tenant-Id header missing or invalid",
        )
    return x_tenant_id
