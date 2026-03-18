from enum import Enum
from typing import Callable
from fastapi import Depends, HTTPException, status


class Role(str, Enum):
    SYSTEM_ADMIN = "system_admin"
    ADMIN = "admin"
    ICB_MANAGER = "icb_manager"
    ICB_LEADER = "icb_leader"
    ICB_PHARMACIST = "icb_pharmacist"
    SUB_ICB_LEAD = "sub_icb_lead"
    PCN_PHARMACIST = "pcn_pharmacist"
    PRACTICE_PHARMACIST = "practice_pharmacist"
    PHARMACY_TECHNICIAN = "pharmacy_technician"
    PHARMACIST = "pharmacist"
    TECHNICIAN = "technician"
    GP = "gp"
    PRACTICE_USER = "practice_user"


# Roles that can see ICB-level aggregate data (Zone 1)
ZONE_1_ROLES = list(Role)

# Roles that can see practice-level data (Zone 2)
ZONE_2_ROLES = [
    Role.SYSTEM_ADMIN, Role.ADMIN, Role.ICB_MANAGER, Role.ICB_LEADER,
    Role.ICB_PHARMACIST, Role.SUB_ICB_LEAD, Role.PCN_PHARMACIST,
    Role.PRACTICE_PHARMACIST, Role.PHARMACIST, Role.GP,
]

# Roles that can see patient PII (Zone 3)
ZONE_3_ROLES = [
    Role.SYSTEM_ADMIN, Role.ADMIN, Role.ICB_PHARMACIST,
    Role.PCN_PHARMACIST, Role.PRACTICE_PHARMACIST, Role.PHARMACIST, Role.GP,
]


def requires_roles(*roles: Role) -> Callable:
    """FastAPI dependency factory — restricts endpoint to specified roles."""
    from app.dependencies import get_current_active_user

    async def role_checker(current_user=Depends(get_current_active_user)):
        if current_user.role not in [r.value for r in roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role}' is not permitted for this action.",
            )
        return current_user

    return role_checker
