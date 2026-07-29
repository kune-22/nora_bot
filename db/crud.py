from db.crud_base import CRUDBase
from db.models import User, CustomRole, CustomRoleLink

user_crud = CRUDBase(User)
custom_role_crud = CRUDBase(CustomRole)
custom_role_link_crud = CRUDBase(CustomRoleLink)