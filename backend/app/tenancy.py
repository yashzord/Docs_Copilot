"""Which tenant a request belongs to.

D1 stub: the caller states it in the X-Tenant-Id header. D2 replaces this with
the tenant claim from a verified Cognito token, and the header goes away.
"""

import re
from typing import Annotated

from fastapi import Header, HTTPException, status

# Letters, digits, dash, underscore, 1 to 64 characters. The value is written to
# logs, so anything else (newlines, spaces) is rejected before it can fake a log line.
_TENANT_ID = re.compile(r"[A-Za-z0-9_-]{1,64}")


def get_tenant_id(x_tenant_id: Annotated[str | None, Header()] = None) -> str:
    # The parameter name x_tenant_id is read from the "x-tenant-id" header.
    # https://fastapi.tiangolo.com/tutorial/header-params/
    # ponytail: trusts the header. Ceiling: any caller can claim any tenant.
    # Upgrade: read the tenant from a verified Cognito JWT in D2.
    if x_tenant_id is None or not _TENANT_ID.fullmatch(x_tenant_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Tenant-Id header missing or invalid",
        )
    return x_tenant_id
