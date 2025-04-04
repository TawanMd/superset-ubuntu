# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.


print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
print("!!! EXECUTANDO A VERSÃO MAIS RECENTE DE API.PY !!!")
print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")


print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
print("!!! EXECUTANDO A VERSÃO MAIS RECENTE DE API.PY !!!")
print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")


print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
print("!!! EXECUTANDO A VERSÃO MAIS RECENTE DE API.PY !!!")
print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")


import logging
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import timedelta
from typing import Any

from flask import current_app, make_response, request, Response
# Core FAB and corrected imports
from flask_appbuilder import const as fab_const
from flask_appbuilder.api import expose, protect, rison, safe
from flask_appbuilder.hooks import before_request
# Keep in case it's used indirectly elsewhere
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_babel import gettext as __, lazy_gettext as _
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    set_access_cookies,
    set_refresh_cookies,
    unset_jwt_cookies,
)
from flask_login import login_user, logout_user
from marshmallow import fields, Schema, validate
from marshmallow_sqlalchemy.schema import SQLAlchemySchema
# Werkzeug check is needed by the manager
from werkzeug.security import check_password_hash

# Use the main security_manager instance from superset
from superset import security_manager
from superset.constants import MODEL_API_RW_METHOD_PERMISSION_MAP, RouteMethod
# Import other necessary extensions/utils
from superset.extensions import event_logger
from superset.utils.core import parse_boolean_string
from superset.views.base_api import BaseSupersetApi, requires_json, statsd_metrics

# Import the constant for hardcoded user logic
from .manager import HARDCODED_USERNAME


User = security_manager.user_model
Role = security_manager.role_model

logger = logging.getLogger(__name__)


# Removed redundant check_username_password function

@contextmanager
def statsd_login_or_refresh(cmd_name: str) -> Iterator[None]:
    """Increment a counter based on user activity when accessing Superset."""
    # (No changes needed in this context manager)
    @statsd_metrics.counter(f"requests.{cmd_name}.count")
    def incr_request_count() -> None: ...
    @statsd_metrics.counter(f"requests.{cmd_name}.failure")
    def incr_failure() -> None: ...
    @statsd_metrics.counter(f"requests.{cmd_name}.success")
    def incr_success() -> None: ...

    incr_request_count()
    try:
        yield
        incr_success()
    except Exception as ex:
        incr_failure()
        raise ex


class UserInfoSchema(SQLAlchemySchema):
    # (No changes needed)
    class Meta:
        model = User
        fields = ("id", "username", "first_name", "last_name", "email", "is_active",
                  "created_on", "last_login", "login_count", "fail_login_count", "changed_on")
    first_name = fields.String(required=True)
    last_name = fields.String(required=True)


class UserRolesSchema(SQLAlchemySchema):
    # (No changes needed)
    class Meta:
        model = Role
        fields = ("id", "name")


class AuthSchema(Schema):
    username = fields.String(required=True, validate=[validate.Length(min=1)])
    password = fields.String(required=True, validate=[validate.Length(min=1)])
    # Provider type validated as string 'db' or 'ldap'
    provider = fields.String(
        required=True,
        validate=[
            validate.Length(min=1),
            validate.OneOf(["db", "ldap"]),  # Validates the string value
        ],
    )
    refresh = fields.Bool(load_default=False)


class RefreshRequestSchema(Schema):
    refresh_token = fields.String(required=True, validate=[
                                  validate.Length(min=1)])


class SecurityApi(BaseSupersetApi):
    """API endpoints for Superset security features."""
    # Corrected route methods
    include_route_methods = {RouteMethod.GET, RouteMethod.POST}
    allow_browser_login = True
    openapi_spec_tag = "Security"

    def get_user_info(self, user: User, include_perms: bool = False) -> dict[str, Any]:
        # (No significant changes needed)
        roles_result: list[dict[str, Any]] = UserRolesSchema().dump(
            user.roles, many=True)
        roles_dict = {role.get("name"): str(role.get(
            "id")) for role in roles_result if role.get("name") and role.get("id") is not None}

        result = {
            "username": user.username,
            "firstName": user.first_name,
            "lastName": user.last_name,
            "userId": user.id,
            "isActive": user.is_active,
            "email": user.email,
            "roles": {role.name for role in user.roles},
        }

        if include_perms:
            permissions_dict = {}
            perms = security_manager.get_user_permissions(user)
            if "all_datasource_access" in {p[1] for p in perms}:
                perms.add(('datasource_access', ''))

            for view_menu, permission_name in perms:
                if view_menu not in permissions_dict:
                    permissions_dict[view_menu] = []
                permissions_dict[view_menu].append(permission_name)
            result["permissions"] = permissions_dict
        return result

    @staticmethod
    def _get_identity(user: User) -> int | str:
        return user.get_id()

    # Corrected @before_request
    @before_request(only=("me", "csrf_token"))
    @protect(allow_browser_login=True)
    @expose("/me/", methods=("GET",))
    def me(self) -> Response:
        """Get information about the current logged-in user."""
        user = security_manager.get_current_user()
        if user.is_anonymous:
            user = security_manager.get_anonymous_user()
        user_info = self.get_user_info(user, include_perms=True)
        return self.response(200, user=user_info)

    @expose("/csrf_token/", methods=("GET",))
    @protect()
    def csrf_token(self) -> Response:
        """Obtain the CSRF token."""
        return self.response(200, result=self._csrf)

    @expose("/login", methods=("POST",))
    @requires_json
    @event_logger.log_this_with_context(action="login", object_ref=False, log_to_statsd=False)
    def login(self) -> Response:
        """Authenticates and logs the user in. Issues JWT security tokens."""
        security_config = current_app.config["FAB_SECURITY_MANAGER"]
        with statsd_login_or_refresh("login"):
            # 1. Validate request body
            try:
                login_payload_validated = AuthSchema().load(request.json)
            except validate.ValidationError as err:
                logger.warning(
                    "Login schema validation failed: %s", err.messages)
                return self.response(422, message=err.messages)

            username = login_payload_validated["username"]
            password = login_payload_validated["password"]
            remember = parse_boolean_string(
                str(login_payload_validated.get("refresh", False)))

            # 2. Authenticate user via Security Manager (handles hardcoded logic first)
            logger.debug(f"Attempting authentication for user: {username}")
            user = security_manager.auth_user_db(username, password)

            # <<< LOG PARA VERIFICAR OBJETO USER RECEBIDO (Importante) >>>
            if user:
                logger.info(
                    f"!!! Objeto User obtido em api.py: ID={user.id}, Username='{user.username}', Active={user.is_active}")
            else:
                logger.error(
                    f"!!! auth_user_db retornou None ou False para usuário '{username}' em api.py !!!")
            # <<< FIM DO LOG >>>

            # 3. Check authentication result
            if not user:
                event_logger.log_event("login_failure", username=username)
                logger.warning("Invalid login attempt for user: %s", username)
                return self.response_401(message="Invalid credentials")

            # 4. Log user into session
            login_user(user, remember=remember)
            event_logger.log_event("login_success", username=username)
            logger.info(f"User successfully logged in: {username}")

            # 5. Prepare response payload
            response_payload = {}
            access_token = create_access_token(identity=self._get_identity(
                user), fresh=True, expires_delta=security_config.access_token_expires)
            response_payload["access_token"] = access_token
            if security_config.use_refresh_token:
                refresh_token = create_refresh_token(identity=self._get_identity(
                    user), expires_delta=security_config.refresh_token_expires)
                response_payload["refresh_token"] = refresh_token

            # --- LEITURA DOS ATRIBUTOS INJETADOS (Workaround) ---
            # Log mantido
            logger.info(
                f"Checking for injected attributes on user object: {user.username}")
            # Usar hasattr para verificar ANTES de tentar ler com getattr
            if user.username == HARDCODED_USERNAME and hasattr(user, 'tenantUuid') and hasattr(user, 'sistema'):
                # Log mantido
                logger.info(
                    f"Reading injected attributes from user object '{user.username}'")
                # Lê os atributos que FORAM injetados no manager.py
                response_payload["tenantUuid"] = getattr(
                    user, 'tenantUuid', 'ERROR_READING_ATTR')  # Adiciona ao payload da resposta
                response_payload["sistema"] = getattr(
                    user, 'sistema', 'ERROR_READING_ATTR')  # Adiciona ao payload da resposta
            else:
                # Este log será útil para saber por que não adicionou
                logger.info(
                    f"Did not add custom fields. User matches: {user.username == HARDCODED_USERNAME}, Has tenantUuid: {hasattr(user, 'tenantUuid')}, Has sistema: {hasattr(user, 'sistema')}")
            # --- FIM DA LEITURA ---

            # 6. Create response using the (potentially) modified payload
            resp = self.response(200, **response_payload)

            # 7. Handle cookies
            if security_config.send_auth_cookie:
                access_max_age = security_config.access_token_expires if not remember else None
                set_access_cookies(resp, access_token, max_age=access_max_age)
                if security_config.use_refresh_token and "refresh_token" in response_payload:
                    refresh_max_age = security_config.refresh_token_expires if not remember else None
                    set_refresh_cookies(
                        resp, response_payload["refresh_token"], max_age=refresh_max_age)
            return resp

    @expose("/refresh", methods=("POST",))
    @protect(allow_browser_login=True)  # Decorator corrigido
    @requires_json
    def refresh(self) -> Response:
        """Issues a new access token based on the refresh token."""
        # (Sem alterações significativas)
        try:
            RefreshRequestSchema().load(request.json)
        except validate.ValidationError as err:
            logger.warning(
                "Refresh schema validation failed: %s", err.messages)
            return self.response(422, message=err.messages)
        security_config = current_app.config["FAB_SECURITY_MANAGER"]
        if not security_config.use_refresh_token:
            logger.warning("Refresh disabled.")
            return self.response(405, message="Refresh tokens are not enabled.")
        with statsd_login_or_refresh("refresh"):
            user_id = get_jwt_identity()
            if not user_id:
                logger.warning("Invalid refresh token identity.")
                return self.response_401(message="Invalid refresh token")
            user = security_manager.get_user_by_id(user_id)
            if not user or not user.is_active:
                logger.warning(
                    f"Refresh attempt for invalid/inactive user ID: {user_id}")
                return self.response_401(message="Invalid user for refresh token")
            access_token = create_access_token(
                identity=user_id, fresh=False, expires_delta=security_config.access_token_expires)
            payload = {"access_token": access_token}
            resp = self.response(200, **payload)
            if security_config.send_auth_cookie:
                set_access_cookies(
                    resp, access_token, max_age=security_config.access_token_expires)
            return resp

    @expose("/logout", methods=("GET",))
    @protect()
    @event_logger.log_this
    def logout(self) -> Response:
        # (Sem alterações necessárias)
        """User logout. Unsets the JWT tokens."""
        resp = self.response(200, message="OK")
        if current_app.config["FAB_SECURITY_MANAGER"].send_auth_cookie:
            unset_jwt_cookies(resp)
        logout_user()
        return resp

    # --- Restante do arquivo (schemas, /permissions, /roles, /sync_roles) sem alterações ---
    class RolesSchema(SQLAlchemySchema):
        class Meta:
            model = Role
            fields = ("id", "name", "users", "human_name", "permission_name")
        users = fields.List(fields.Integer(), required=True,
                            validate=validate.Length(min=1))
        name = fields.String(required=True, validate=validate.Length(min=1))

    class AvailablePermissionsSchema(Schema):
        actions = fields.Dict(keys=fields.String(
            # Validação OneOf removida
            required=True), values=fields.Bool(), required=True)

    class PermissionsSchema(Schema):
        actions = fields.List(fields.String(), required=True)
        datasource_name = fields.String(required=True)

    class SecurityAccessSchema(Schema):
        grantees = fields.List(fields.Dict(
            keys=fields.String(), values=fields.String()), required=True)
        object_id = fields.Integer(required=True)
        object_type = fields.String(
            required=True, validate=validate.OneOf(("query", "chart", "dashboard")))
        owners = fields.List(fields.Dict(
            keys=fields.String(), values=fields.String()), required=True)
        permissions = fields.List(fields.String())

    @expose("/permissions", methods=("GET", "POST",))
    @protect(allow_browser_login=True)
    @safe
    def permissions(self) -> Response:
        if request.method == "GET":
            with current_app.app_context():
                try:
                    return self.response(200, **security_manager.get_all_permissions())
                except Exception as e:
                    logger.error("Failed to get permissions: %s",
                                 e, exc_info=True)
                    return self.response_500("Failed to retrieve permissions.")
        return self.response_405(message="POST method not supported for /permissions")

    @expose("/roles", methods=("GET",))
    @protect()
    @safe
    # @statsd_metrics.timer("api.security.roles") # Comentado
    def roles(self) -> Response:
        with current_app.app_context():
            try:
                return self.response(200, **security_manager.get_all_roles_permissions())
            except RuntimeError as ex:
                logger.error("Error fetching roles/permissions: %s", ex)
                return self.response_400(message=str(ex))

    class PermissionRequestSchema(Schema):
        role = fields.String(required=True)
        permission = fields.String(required=True)
        view_menu = fields.String(required=True)

    @protect()
    @expose("/sync_roles/", methods=("POST",))
    # @statsd_metrics.timer("api.security.sync_roles") # Comentado
    def sync_roles(self) -> Response:
        try:
            payload = request.get_json(force=True)
            assert payload is not None
        except Exception as e:
            logger.warning("Invalid JSON: %s", e)
            return self.response(400, error="Invalid JSON payload")
        role_names: list[str] | None = payload.get("names")
        if not role_names or not isinstance(role_names, list):
            return self.response(400, error=_("Missing 'names': list"))
        if not security_manager.is_admin():
            return self.response(403, error=_("Admin required"))
        missing_roles = [name for name in role_names if not security_manager.get_role(
            name)]  # Check existence properly
        if missing_roles:
            logger.warning("Roles not found: %s", missing_roles)
            return self.response(404, message=f"Roles not found: {', '.join(missing_roles)}")
        try:
            with current_app.app_context():
                for name in role_names:
                    logger.info("Updating Role: %s", name)
                    security_manager.update_role_permissions(name)
            return self.response(200, success=_("Role(s) permissions updated."))
        except Exception as e:
            logger.error("Error syncing: %s", e, exc_info=True)
            return self.response_500("Sync error.")
