import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional
import httpx
from app.core.config import settings
from app.core.logging import logger
from app.db.models import DomainModel, OrderModel, ReportModel, ScanDiffModel, ScanModel, UserModel
from app.schemas.finding import Finding


class DomainRepository:
    """
    Data repository for Domains, Scans, and Users.
    Uses Supabase REST API in production or an in-memory fallback for testing/offline dev.
    """

    def __init__(self):
        self._in_memory_domains: Dict[str, DomainModel] = {}
        self._in_memory_scans: Dict[str, ScanModel] = {}
        self._in_memory_findings: Dict[str, List[Finding]] = {}
        self._in_memory_reports: Dict[str, ReportModel] = {}
        self._in_memory_orders: Dict[str, OrderModel] = {}
        self._in_memory_diffs: Dict[str, ScanDiffModel] = {}
        self._in_memory_users: Dict[str, UserModel] = {}
        self.is_supabase_configured = (
            bool(settings.SUPABASE_URL)
            and "mock" not in settings.SUPABASE_URL
            and bool(settings.SUPABASE_SERVICE_ROLE_KEY)
            and "mock" not in settings.SUPABASE_SERVICE_ROLE_KEY
        )

    # ----------------- User Methods -----------------
    async def get_or_create_user(self, user_id: str, email: str, plan: str = "free") -> UserModel:
        if self.is_supabase_configured:
            headers = {
                "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
                "Content-Type": "application/json",
                "Prefer": "return=representation",
            }
            async with httpx.AsyncClient(timeout=20.0) as client:
                res = await client.get(
                    f"{settings.SUPABASE_URL}/rest/v1/users?id=eq.{user_id}",
                    headers=headers,
                )
                if res.status_code == 200 and res.json():
                    row = res.json()[0]
                    return UserModel(
                        id=row["id"],
                        email=row["email"],
                        plan=row.get("plan", "free"),
                        razorpay_customer_id=row.get("razorpay_customer_id"),
                    )

                # Insert if not present
                insert_res = await client.post(
                    f"{settings.SUPABASE_URL}/rest/v1/users",
                    headers=headers,
                    json={"id": user_id, "email": email, "plan": plan},
                )
                if insert_res.status_code in (200, 201) and insert_res.json():
                    row = insert_res.json()[0]
                    return UserModel(
                        id=row["id"],
                        email=row["email"],
                        plan=row.get("plan", "free"),
                    )

        # Fallback in-memory
        if user_id not in self._in_memory_users:
            self._in_memory_users[user_id] = UserModel(
                id=user_id,
                email=email,
                plan=plan,
                created_at=datetime.now(timezone.utc),
            )
        return self._in_memory_users[user_id]

    async def get_user(self, user_id: str) -> Optional[UserModel]:
        if self.is_supabase_configured:
            headers = {
                "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
            }
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    res = await client.get(
                        f"{settings.SUPABASE_URL}/rest/v1/users?id=eq.{user_id}",
                        headers=headers,
                    )
                    if res.status_code == 200 and res.json():
                        row = res.json()[0]
                        return UserModel(
                            id=row["id"],
                            email=row["email"],
                            plan=row.get("plan", "free"),
                            razorpay_customer_id=row.get("razorpay_customer_id"),
                        )
            except Exception as e:
                logger.warning(f"Supabase get_user request failed: {e}. Falling back to in-memory store.")

        return self._in_memory_users.get(user_id)

    async def update_user_plan(self, user_id: str, plan: str) -> Optional[UserModel]:
        now = datetime.now(timezone.utc)
        if self.is_supabase_configured:
            headers = {
                "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
                "Content-Type": "application/json",
                "Prefer": "return=representation",
            }
            async with httpx.AsyncClient(timeout=20.0) as client:
                res = await client.patch(
                    f"{settings.SUPABASE_URL}/rest/v1/users?id=eq.{user_id}",
                    headers=headers,
                    json={"plan": plan, "updated_at": now.isoformat()},
                )
                if res.status_code == 200 and res.json():
                    row = res.json()[0]
                    return UserModel(
                        id=row["id"],
                        email=row["email"],
                        plan=row.get("plan", plan),
                        razorpay_customer_id=row.get("razorpay_customer_id"),
                    )

        user = self._in_memory_users.get(user_id)
        if user:
            user.plan = plan
            user.updated_at = now
            return user
        else:
            new_user = UserModel(id=user_id, email=f"{user_id}@example.com", plan=plan, created_at=now, updated_at=now)
            self._in_memory_users[user_id] = new_user
            return new_user


    # ----------------- Domain Methods -----------------
    async def create_domain(
        self,
        user_id: str,
        hostname: str,
        verify_token: str,
    ) -> DomainModel:
        domain_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        if self.is_supabase_configured:
            headers = {
                "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
                "Content-Type": "application/json",
                "Prefer": "return=representation",
            }
            payload = {
                "id": domain_id,
                "user_id": user_id,
                "hostname": hostname,
                "verify_token": verify_token,
                "status": "pending",
            }
            async with httpx.AsyncClient(timeout=20.0) as client:
                res = await client.post(
                    f"{settings.SUPABASE_URL}/rest/v1/domains",
                    headers=headers,
                    json=payload,
                )
                if res.status_code in (200, 201) and res.json():
                    row = res.json()[0]
                    return DomainModel(
                        id=row["id"],
                        user_id=row["user_id"],
                        hostname=row["hostname"],
                        verify_token=row["verify_token"],
                        status=row["status"],
                        created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")),
                    )
                else:
                    logger.error(f"Failed to create domain in Supabase: {res.text}")

        domain = DomainModel(
            id=domain_id,
            user_id=user_id,
            hostname=hostname,
            verify_token=verify_token,
            status="pending",
            created_at=now,
            updated_at=now,
        )
        self._in_memory_domains[domain_id] = domain
        return domain

    async def list_domains_by_user(self, user_id: str) -> List[DomainModel]:
        if self.is_supabase_configured:
            headers = {
                "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
            }
            try:
                async with httpx.AsyncClient(timeout=20.0) as client:
                    res = await client.get(
                        f"{settings.SUPABASE_URL}/rest/v1/domains?user_id=eq.{user_id}&order=created_at.desc",
                        headers=headers,
                    )
                    if res.status_code == 200:
                        rows = res.json()
                        if rows:
                            return [
                                DomainModel(
                                    id=row["id"],
                                    user_id=row["user_id"],
                                    hostname=row["hostname"],
                                    verify_token=row["verify_token"],
                                    status=row["status"],
                                    verified_at=datetime.fromisoformat(row["verified_at"].replace("Z", "+00:00")) if row.get("verified_at") else None,
                                    created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")) if row.get("created_at") else None,
                                )
                                for row in rows
                            ]
            except Exception:
                pass

        return [d for d in self._in_memory_domains.values() if d.user_id == user_id]

    async def get_domain(self, domain_id: str, user_id: Optional[str] = None) -> Optional[DomainModel]:
        if self.is_supabase_configured:
            headers = {
                "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
            }
            url = f"{settings.SUPABASE_URL}/rest/v1/domains?id=eq.{domain_id}"
            if user_id:
                url += f"&user_id=eq.{user_id}"
            async with httpx.AsyncClient(timeout=20.0) as client:
                res = await client.get(url, headers=headers)
                if res.status_code == 200 and res.json():
                    row = res.json()[0]
                    return DomainModel(
                        id=row["id"],
                        user_id=row["user_id"],
                        hostname=row["hostname"],
                        verify_token=row["verify_token"],
                        status=row["status"],
                        verified_at=datetime.fromisoformat(row["verified_at"].replace("Z", "+00:00")) if row.get("verified_at") else None,
                        created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")) if row.get("created_at") else None,
                    )

        domain = self._in_memory_domains.get(domain_id)
        if domain and (user_id is None or domain.user_id == user_id):
            return domain
        return None

    async def get_domain_by_hostname(self, user_id: str, hostname: str) -> Optional[DomainModel]:
        if self.is_supabase_configured:
            headers = {
                "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
            }
            async with httpx.AsyncClient(timeout=20.0) as client:
                res = await client.get(
                    f"{settings.SUPABASE_URL}/rest/v1/domains?user_id=eq.{user_id}&hostname=eq.{hostname}",
                    headers=headers,
                )
                if res.status_code == 200 and res.json():
                    row = res.json()[0]
                    return DomainModel(
                        id=row["id"],
                        user_id=row["user_id"],
                        hostname=row["hostname"],
                        verify_token=row["verify_token"],
                        status=row["status"],
                        verified_at=datetime.fromisoformat(row["verified_at"].replace("Z", "+00:00")) if row.get("verified_at") else None,
                        created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")) if row.get("created_at") else None,
                    )

        for d in self._in_memory_domains.values():
            if d.user_id == user_id and d.hostname == hostname:
                return d
        return None

    async def update_domain_status(
        self,
        domain_id: str,
        status: str,
        verified_at: Optional[datetime] = None,
    ) -> Optional[DomainModel]:
        now = datetime.now(timezone.utc)
        if self.is_supabase_configured:
            headers = {
                "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
                "Content-Type": "application/json",
                "Prefer": "return=representation",
            }
            payload = {
                "status": status,
                "verified_at": verified_at.isoformat() if verified_at else None,
                "updated_at": now.isoformat(),
            }
            async with httpx.AsyncClient(timeout=20.0) as client:
                res = await client.patch(
                    f"{settings.SUPABASE_URL}/rest/v1/domains?id=eq.{domain_id}",
                    headers=headers,
                    json=payload,
                )
                if res.status_code == 200 and res.json():
                    row = res.json()[0]
                    return DomainModel(
                        id=row["id"],
                        user_id=row["user_id"],
                        hostname=row["hostname"],
                        verify_token=row["verify_token"],
                        status=row["status"],
                        verified_at=datetime.fromisoformat(row["verified_at"].replace("Z", "+00:00")) if row.get("verified_at") else None,
                        created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")) if row.get("created_at") else None,
                    )

        domain = self._in_memory_domains.get(domain_id)
        if domain:
            domain.status = status
            domain.verified_at = verified_at
            domain.updated_at = now
            return domain
        return None

    async def delete_domain(self, domain_id: str, user_id: str) -> bool:
        if domain_id in self._in_memory_domains:
            if self._in_memory_domains[domain_id].user_id == user_id:
                del self._in_memory_domains[domain_id]

        if self.is_supabase_configured:
            headers = {
                "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
            }
            try:
                async with httpx.AsyncClient(timeout=20.0) as client:
                    res = await client.delete(
                        f"{settings.SUPABASE_URL}/rest/v1/domains?id=eq.{domain_id}&user_id=eq.{user_id}",
                        headers=headers,
                    )
                    return res.status_code in (200, 204)
            except Exception:
                pass
        return True

    async def update_domain_monitoring(
        self,
        domain_id: str,
        is_monitored: bool,
        user_id: Optional[str] = None,
    ) -> Optional[DomainModel]:
        now = datetime.now(timezone.utc)
        if self.is_supabase_configured:
            headers = {
                "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
                "Content-Type": "application/json",
                "Prefer": "return=representation",
            }
            url = f"{settings.SUPABASE_URL}/rest/v1/domains?id=eq.{domain_id}"
            if user_id:
                url += f"&user_id=eq.{user_id}"
            payload = {
                "is_monitored": is_monitored,
                "updated_at": now.isoformat(),
            }
            async with httpx.AsyncClient(timeout=20.0) as client:
                res = await client.patch(url, headers=headers, json=payload)
                if res.status_code == 200 and res.json():
                    row = res.json()[0]
                    return DomainModel(
                        id=row["id"],
                        user_id=row["user_id"],
                        hostname=row["hostname"],
                        verify_token=row["verify_token"],
                        status=row["status"],
                        is_monitored=row.get("is_monitored", is_monitored),
                        last_monitored_at=datetime.fromisoformat(row["last_monitored_at"].replace("Z", "+00:00")) if row.get("last_monitored_at") else None,
                        verified_at=datetime.fromisoformat(row["verified_at"].replace("Z", "+00:00")) if row.get("verified_at") else None,
                        created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")) if row.get("created_at") else None,
                    )

        domain = self._in_memory_domains.get(domain_id)
        if domain and (user_id is None or domain.user_id == user_id):
            domain.is_monitored = is_monitored
            domain.updated_at = now
            return domain
        return None

    async def update_domain_last_monitored(self, domain_id: str) -> None:
        now = datetime.now(timezone.utc)
        if self.is_supabase_configured:
            headers = {
                "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
                "Content-Type": "application/json",
            }
            async with httpx.AsyncClient(timeout=20.0) as client:
                await client.patch(
                    f"{settings.SUPABASE_URL}/rest/v1/domains?id=eq.{domain_id}",
                    headers=headers,
                    json={"last_monitored_at": now.isoformat()},
                )
        domain = self._in_memory_domains.get(domain_id)
        if domain:
            domain.last_monitored_at = now

    async def list_monitored_domains_due(self, days: int = 7) -> List[DomainModel]:
        from datetime import timedelta
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        if self.is_supabase_configured:
            headers = {
                "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
            }
            async with httpx.AsyncClient(timeout=20.0) as client:
                res = await client.get(
                    f"{settings.SUPABASE_URL}/rest/v1/domains?is_monitored=eq.true&status=eq.verified",
                    headers=headers,
                )
                if res.status_code == 200:
                    due = []
                    for row in res.json():
                        l_at = datetime.fromisoformat(row["last_monitored_at"].replace("Z", "+00:00")) if row.get("last_monitored_at") else None
                        if l_at is None or l_at <= cutoff:
                            due.append(DomainModel(
                                id=row["id"],
                                user_id=row["user_id"],
                                hostname=row["hostname"],
                                verify_token=row["verify_token"],
                                status=row["status"],
                                is_monitored=True,
                                last_monitored_at=l_at,
                            ))
                    return due

        due = []
        for d in self._in_memory_domains.values():
            if d.is_monitored and d.status == "verified":
                if d.last_monitored_at is None or d.last_monitored_at <= cutoff:
                    due.append(d)
        return due


    # ----------------- Scan Methods -----------------
    async def create_scan(
        self,
        domain_id: str,
        user_id: str,
        hostname: str,
        profile: str = "free",
    ) -> ScanModel:
        scan_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        if self.is_supabase_configured:
            headers = {
                "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
                "Content-Type": "application/json",
                "Prefer": "return=representation",
            }
            payload = {
                "id": scan_id,
                "domain_id": domain_id,
                "user_id": user_id,
                "profile": profile,
                "status": "queued",
                "progress": 0,
                "stage_message": "Queued for security scan",
            }
            async with httpx.AsyncClient(timeout=20.0) as client:
                res = await client.post(
                    f"{settings.SUPABASE_URL}/rest/v1/scans",
                    headers=headers,
                    json=payload,
                )
                if res.status_code in (200, 201) and res.json():
                    row = res.json()[0]
                    return ScanModel(
                        id=row["id"],
                        domain_id=row["domain_id"],
                        user_id=row["user_id"],
                        hostname=hostname,
                        profile=row["profile"],
                        status=row["status"],
                        progress=row["progress"],
                        stage_message=row.get("stage_message"),
                        grade=row.get("grade"),
                        findings_count=row.get("findings_count", 0),
                        created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")),
                    )

        scan = ScanModel(
            id=scan_id,
            domain_id=domain_id,
            user_id=user_id,
            hostname=hostname,
            profile=profile,
            status="queued",
            progress=0,
            stage_message="Queued for security scan",
            created_at=now,
            updated_at=now,
        )
        self._in_memory_scans[scan_id] = scan
        return scan

    async def get_scan(self, scan_id: str, user_id: Optional[str] = None) -> Optional[ScanModel]:
        if self.is_supabase_configured:
            headers = {
                "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
            }
            url = f"{settings.SUPABASE_URL}/rest/v1/scans?id=eq.{scan_id}"
            if user_id:
                url += f"&user_id=eq.{user_id}"
            async with httpx.AsyncClient(timeout=20.0) as client:
                res = await client.get(url, headers=headers)
                if res.status_code == 200 and res.json():
                    row = res.json()[0]
                    # Get hostname from domain
                    domain = await self.get_domain(row["domain_id"])
                    hostname = domain.hostname if domain else "unknown"
                    return ScanModel(
                        id=row["id"],
                        domain_id=row["domain_id"],
                        user_id=row["user_id"],
                        hostname=hostname,
                        profile=row["profile"],
                        status=row["status"],
                        progress=row["progress"],
                        stage_message=row.get("stage_message"),
                        grade=row.get("grade"),
                        findings_count=row.get("findings_count", 0),
                        started_at=datetime.fromisoformat(row["started_at"].replace("Z", "+00:00")) if row.get("started_at") else None,
                        finished_at=datetime.fromisoformat(row["finished_at"].replace("Z", "+00:00")) if row.get("finished_at") else None,
                        error=row.get("error"),
                        created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")) if row.get("created_at") else None,
                    )

        scan = self._in_memory_scans.get(scan_id)
        if scan and (user_id is None or scan.user_id == user_id):
            return scan
        return None

    async def list_scans_by_domain(self, domain_id: str, user_id: Optional[str] = None) -> List[ScanModel]:
        if self.is_supabase_configured:
            headers = {
                "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
            }
            url = f"{settings.SUPABASE_URL}/rest/v1/scans?domain_id=eq.{domain_id}&order=created_at.desc"
            if user_id:
                url += f"&user_id=eq.{user_id}"
            async with httpx.AsyncClient(timeout=20.0) as client:
                res = await client.get(url, headers=headers)
                if res.status_code == 200:
                    domain = await self.get_domain(domain_id)
                    hostname = domain.hostname if domain else "unknown"
                    return [
                        ScanModel(
                            id=row["id"],
                            domain_id=row["domain_id"],
                            user_id=row["user_id"],
                            hostname=hostname,
                            profile=row["profile"],
                            status=row["status"],
                            progress=row["progress"],
                            stage_message=row.get("stage_message"),
                            grade=row.get("grade"),
                            findings_count=row.get("findings_count", 0),
                            started_at=datetime.fromisoformat(row["started_at"].replace("Z", "+00:00")) if row.get("started_at") else None,
                            finished_at=datetime.fromisoformat(row["finished_at"].replace("Z", "+00:00")) if row.get("finished_at") else None,
                            error=row.get("error"),
                            created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")) if row.get("created_at") else None,
                        )
                        for row in res.json()
                    ]

        return [
            s for s in self._in_memory_scans.values()
            if s.domain_id == domain_id and (user_id is None or s.user_id == user_id)
        ]

    async def update_scan_progress(
        self,
        scan_id: str,
        status: str,
        progress: int,
        stage_message: Optional[str] = None,
        grade: Optional[str] = None,
        findings_count: Optional[int] = None,
        started_at: Optional[datetime] = None,
        finished_at: Optional[datetime] = None,
        error: Optional[str] = None,
    ) -> Optional[ScanModel]:
        now = datetime.now(timezone.utc)
        payload = {
            "status": status,
            "progress": progress,
            "updated_at": now.isoformat(),
        }
        if stage_message is not None:
            payload["stage_message"] = stage_message
        if grade is not None:
            payload["grade"] = grade
        if findings_count is not None:
            payload["findings_count"] = findings_count
        if started_at is not None:
            payload["started_at"] = started_at.isoformat()
        if finished_at is not None:
            payload["finished_at"] = finished_at.isoformat()
        if error is not None:
            payload["error"] = error

        if self.is_supabase_configured:
            headers = {
                "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
                "Content-Type": "application/json",
                "Prefer": "return=representation",
            }
            async with httpx.AsyncClient(timeout=20.0) as client:
                res = await client.patch(
                    f"{settings.SUPABASE_URL}/rest/v1/scans?id=eq.{scan_id}",
                    headers=headers,
                    json=payload,
                )
                if res.status_code == 200 and res.json():
                    row = res.json()[0]
                    domain = await self.get_domain(row["domain_id"])
                    hostname = domain.hostname if domain else "unknown"
                    return ScanModel(
                        id=row["id"],
                        domain_id=row["domain_id"],
                        user_id=row["user_id"],
                        hostname=hostname,
                        profile=row["profile"],
                        status=row["status"],
                        progress=row["progress"],
                        stage_message=row.get("stage_message"),
                        grade=row.get("grade"),
                        findings_count=row.get("findings_count", 0),
                        started_at=datetime.fromisoformat(row["started_at"].replace("Z", "+00:00")) if row.get("started_at") else None,
                        finished_at=datetime.fromisoformat(row["finished_at"].replace("Z", "+00:00")) if row.get("finished_at") else None,
                        error=row.get("error"),
                        created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")) if row.get("created_at") else None,
                    )

        scan = self._in_memory_scans.get(scan_id)
        if scan:
            scan.status = status
            scan.progress = progress
            if stage_message is not None:
                scan.stage_message = stage_message
            if grade is not None:
                scan.grade = grade
            if findings_count is not None:
                scan.findings_count = findings_count
            if started_at is not None:
                scan.started_at = started_at
            if finished_at is not None:
                scan.finished_at = finished_at
            if error is not None:
                scan.error = error
            scan.updated_at = now
            return scan
        return None

    # ----------------- Finding Methods -----------------
    async def save_findings(self, scan_id: str, findings: List[Finding]) -> List[Finding]:
        if self.is_supabase_configured:
            headers = {
                "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
                "Content-Type": "application/json",
                "Prefer": "resolution=merge-duplicates",
            }
            payload = [
                {
                    "scan_id": scan_id,
                    "source_tool": f.source_tool,
                    "template_id": f.template_id,
                    "title": f.title,
                    "severity": f.severity,
                    "host": f.host,
                    "evidence": f.evidence,
                    "raw_ref": f.raw_ref,
                    "fingerprint": f.fingerprint,
                }
                for f in findings
            ]
            if payload:
                async with httpx.AsyncClient(timeout=20.0) as client:
                    await client.post(
                        f"{settings.SUPABASE_URL}/rest/v1/findings",
                        headers=headers,
                        json=payload,
                    )

        # In-memory store
        self._in_memory_findings[scan_id] = findings
        return findings

    async def list_findings_by_scan(self, scan_id: str) -> List[Finding]:
        if self.is_supabase_configured:
            headers = {
                "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
            }
            async with httpx.AsyncClient(timeout=20.0) as client:
                res = await client.get(
                    f"{settings.SUPABASE_URL}/rest/v1/findings?scan_id=eq.{scan_id}&order=severity.desc",
                    headers=headers,
                )
                if res.status_code == 200:
                    return [Finding(**row) for row in res.json()]

        return self._in_memory_findings.get(scan_id, [])

    # ----------------- Report Methods -----------------
    async def create_or_update_report(
        self,
        scan_id: str,
        language: str = "en",
        pdf_url: Optional[str] = None,
        html_url: Optional[str] = None,
        summary_json: Optional[dict] = None,
    ) -> ReportModel:
        now = datetime.now(timezone.utc)
        report_id = str(uuid.uuid4())

        if self.is_supabase_configured:
            headers = {
                "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
                "Content-Type": "application/json",
                "Prefer": "resolution=merge-duplicates,return=representation",
            }
            payload = {
                "scan_id": scan_id,
                "language": language,
                "pdf_url": pdf_url,
                "html_url": html_url,
                "summary_json": summary_json,
                "updated_at": now.isoformat(),
            }
            async with httpx.AsyncClient(timeout=20.0) as client:
                res = await client.post(
                    f"{settings.SUPABASE_URL}/rest/v1/reports",
                    headers=headers,
                    json=payload,
                )
                if res.status_code in (200, 201) and res.json():
                    row = res.json()[0]
                    return ReportModel(
                        id=row["id"],
                        scan_id=row["scan_id"],
                        language=row.get("language", language),
                        pdf_url=row.get("pdf_url"),
                        html_url=row.get("html_url"),
                        summary_json=row.get("summary_json"),
                        created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")) if row.get("created_at") else None,
                        updated_at=datetime.fromisoformat(row["updated_at"].replace("Z", "+00:00")) if row.get("updated_at") else None,
                    )

        # In-memory store
        key = f"{scan_id}:{language}"
        existing = self._in_memory_reports.get(key)
        if existing:
            existing.pdf_url = pdf_url or existing.pdf_url
            existing.html_url = html_url or existing.html_url
            existing.summary_json = summary_json or existing.summary_json
            existing.updated_at = now
            return existing

        new_report = ReportModel(
            id=report_id,
            scan_id=scan_id,
            language=language,
            pdf_url=pdf_url,
            html_url=html_url,
            summary_json=summary_json,
            created_at=now,
            updated_at=now,
        )
        self._in_memory_reports[key] = new_report
        return new_report

    async def get_report_by_scan_and_language(self, scan_id: str, language: str = "en") -> Optional[ReportModel]:
        if self.is_supabase_configured:
            headers = {
                "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
            }
            async with httpx.AsyncClient(timeout=20.0) as client:
                res = await client.get(
                    f"{settings.SUPABASE_URL}/rest/v1/reports?scan_id=eq.{scan_id}&language=eq.{language}",
                    headers=headers,
                )
                if res.status_code == 200 and res.json():
                    row = res.json()[0]
                    return ReportModel(
                        id=row["id"],
                        scan_id=row["scan_id"],
                        language=row.get("language", language),
                        pdf_url=row.get("pdf_url"),
                        html_url=row.get("html_url"),
                        summary_json=row.get("summary_json"),
                        created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")) if row.get("created_at") else None,
                        updated_at=datetime.fromisoformat(row["updated_at"].replace("Z", "+00:00")) if row.get("updated_at") else None,
                    )

        return self._in_memory_reports.get(f"{scan_id}:{language}")

    async def list_reports_by_scan(self, scan_id: str) -> List[ReportModel]:
        if self.is_supabase_configured:
            headers = {
                "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
            }
            async with httpx.AsyncClient(timeout=20.0) as client:
                res = await client.get(
                    f"{settings.SUPABASE_URL}/rest/v1/reports?scan_id=eq.{scan_id}",
                    headers=headers,
                )
                if res.status_code == 200:
                    return [
                        ReportModel(
                            id=row["id"],
                            scan_id=row["scan_id"],
                            language=row.get("language", "en"),
                            pdf_url=row.get("pdf_url"),
                            html_url=row.get("html_url"),
                            summary_json=row.get("summary_json"),
                        )
                        for row in res.json()
                    ]

        return [r for k, r in self._in_memory_reports.items() if k.startswith(f"{scan_id}:")]

    # ----------------- Order & Billing Methods -----------------
    async def create_order(
        self,
        user_id: str,
        razorpay_order_id: str,
        plan: str,
        amount: int,
        currency: str = "INR",
        domain_id: Optional[str] = None,
    ) -> OrderModel:
        now = datetime.now(timezone.utc)
        order_id = str(uuid.uuid4())

        if self.is_supabase_configured:
            headers = {
                "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
                "Content-Type": "application/json",
                "Prefer": "return=representation",
            }
            payload = {
                "id": order_id,
                "user_id": user_id,
                "domain_id": domain_id,
                "razorpay_order_id": razorpay_order_id,
                "plan": plan,
                "amount": amount,
                "currency": currency,
                "status": "created",
            }
            async with httpx.AsyncClient(timeout=20.0) as client:
                res = await client.post(
                    f"{settings.SUPABASE_URL}/rest/v1/orders",
                    headers=headers,
                    json=payload,
                )
                if res.status_code in (200, 201) and res.json():
                    row = res.json()[0]
                    return OrderModel(
                        id=row["id"],
                        user_id=row["user_id"],
                        domain_id=row.get("domain_id"),
                        razorpay_order_id=row["razorpay_order_id"],
                        plan=row["plan"],
                        amount=row["amount"],
                        currency=row.get("currency", currency),
                        status=row.get("status", "created"),
                    )

        order = OrderModel(
            id=order_id,
            user_id=user_id,
            domain_id=domain_id,
            razorpay_order_id=razorpay_order_id,
            plan=plan,
            amount=amount,
            currency=currency,
            status="created",
            created_at=now,
            updated_at=now,
        )
        self._in_memory_orders[razorpay_order_id] = order
        return order

    async def get_order_by_razorpay_id(self, razorpay_order_id: str) -> Optional[OrderModel]:
        if self.is_supabase_configured:
            headers = {
                "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
            }
            async with httpx.AsyncClient(timeout=20.0) as client:
                res = await client.get(
                    f"{settings.SUPABASE_URL}/rest/v1/orders?razorpay_order_id=eq.{razorpay_order_id}",
                    headers=headers,
                )
                if res.status_code == 200 and res.json():
                    row = res.json()[0]
                    return OrderModel(
                        id=row["id"],
                        user_id=row["user_id"],
                        domain_id=row.get("domain_id"),
                        razorpay_order_id=row["razorpay_order_id"],
                        razorpay_payment_id=row.get("razorpay_payment_id"),
                        plan=row["plan"],
                        amount=row["amount"],
                        currency=row.get("currency", "INR"),
                        status=row.get("status", "created"),
                    )

        return self._in_memory_orders.get(razorpay_order_id)

    async def update_order_payment(
        self,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        status: str = "paid",
    ) -> Optional[OrderModel]:
        now = datetime.now(timezone.utc)
        if self.is_supabase_configured:
            headers = {
                "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
                "Content-Type": "application/json",
                "Prefer": "return=representation",
            }
            payload = {
                "razorpay_payment_id": razorpay_payment_id,
                "status": status,
                "updated_at": now.isoformat(),
            }
            async with httpx.AsyncClient(timeout=20.0) as client:
                res = await client.patch(
                    f"{settings.SUPABASE_URL}/rest/v1/orders?razorpay_order_id=eq.{razorpay_order_id}",
                    headers=headers,
                    json=payload,
                )
                if res.status_code == 200 and res.json():
                    row = res.json()[0]
                    return OrderModel(
                        id=row["id"],
                        user_id=row["user_id"],
                        domain_id=row.get("domain_id"),
                        razorpay_order_id=row["razorpay_order_id"],
                        razorpay_payment_id=row.get("razorpay_payment_id"),
                        plan=row["plan"],
                        amount=row["amount"],
                        currency=row.get("currency", "INR"),
                        status=row.get("status", status),
                    )

        order = self._in_memory_orders.get(razorpay_order_id)
        if order:
            order.razorpay_payment_id = razorpay_payment_id
            order.status = status
            order.updated_at = now
            return order
        return None

    async def list_orders_by_user(self, user_id: str) -> List[OrderModel]:
        if self.is_supabase_configured:
            headers = {
                "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
            }
            url = f"{settings.SUPABASE_URL}/rest/v1/orders?user_id=eq.{user_id}&order=created_at.desc"
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    res = await client.get(url, headers=headers)
                    if res.status_code == 200:
                        rows = res.json()
                        orders = []
                        for row in rows:
                            created_dt = None
                            if row.get("created_at"):
                                try:
                                    created_dt = datetime.fromisoformat(row["created_at"].replace("Z", "+00:00"))
                                except Exception:
                                    pass
                            updated_dt = None
                            if row.get("updated_at"):
                                try:
                                    updated_dt = datetime.fromisoformat(row["updated_at"].replace("Z", "+00:00"))
                                except Exception:
                                    pass
                            orders.append(
                                OrderModel(
                                    id=row["id"],
                                    user_id=row["user_id"],
                                    domain_id=row.get("domain_id"),
                                    razorpay_order_id=row["razorpay_order_id"],
                                    razorpay_payment_id=row.get("razorpay_payment_id"),
                                    plan=row["plan"],
                                    amount=row["amount"],
                                    currency=row.get("currency", "INR"),
                                    status=row.get("status", "created"),
                                    created_at=created_dt,
                                    updated_at=updated_dt,
                                )
                            )
                        return orders
            except Exception as e:
                logger.warning(f"Supabase list_orders_by_user failed: {e}. Falling back to in-memory store.")

        user_orders = [o for o in self._in_memory_orders.values() if o.user_id == user_id]
        user_orders.sort(key=lambda x: x.created_at or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
        return user_orders

    async def check_scan_quota(
        self,
        user_id: str,
        domain_id: str,
    ) -> tuple[bool, str, Optional[int]]:
        """
        Enforces scan quotas:
        - Pro, Business, Monitor, Full plans: unlimited scans.
        - Free plan: 1 scan per verified domain per 7 days.
        Returns (is_allowed, reason, seconds_remaining).
        """
        user = await self.get_user(user_id)
        plan = user.plan if user else "free"

        if plan in ("pro", "business", "monitor", "full"):
            return True, f"Paid '{plan}' plan active: unlimited scans allowed.", None

        # Free tier: Check past scans for this domain within 7 days
        from datetime import timedelta
        scans = await self.list_scans_by_domain(domain_id=domain_id, user_id=user_id)
        recent_scans = [
            s for s in scans
            if s.status in ("completed", "queued", "recon", "scanning", "scoring")
        ]

        if not recent_scans:
            return True, "Free scan quota available.", None

        now = datetime.now(timezone.utc)
        seven_days_ago = now - timedelta(days=7)

        latest_scan = max(
            recent_scans,
            key=lambda s: s.created_at if s.created_at else datetime.min.replace(tzinfo=timezone.utc),
        )

        scan_time = latest_scan.created_at or latest_scan.started_at
        if not scan_time:
            return True, "Free scan quota available.", None

        if scan_time.tzinfo is None:
            scan_time = scan_time.replace(tzinfo=timezone.utc)

        if scan_time > seven_days_ago:
            elapsed = (now - scan_time).total_seconds()
            wait_seconds = max(1, int((7 * 86400) - elapsed))
            hours_left = max(1, wait_seconds // 3600)
            return (
                False,
                f"Free tier limit reached: 1 free scan per domain every 7 days. Next scan available in ~{hours_left} hours. Upgrade to Pro for instant unlimited scans.",
                wait_seconds,
            )

        return True, "Free scan quota available.", None

    # ----------------- Diff & Monitoring Methods -----------------
    async def get_previous_completed_scan(self, domain_id: str, current_scan_id: str) -> Optional[ScanModel]:
        scans = await self.list_scans_by_domain(domain_id=domain_id)
        completed = [
            s for s in scans
            if s.id != current_scan_id and s.status == "completed"
        ]
        if not completed:
            return None
        return max(
            completed,
            key=lambda s: s.finished_at or s.created_at or datetime.min.replace(tzinfo=timezone.utc),
        )

    async def save_scan_diff(
        self,
        scan_id: str,
        domain_id: str,
        previous_scan_id: Optional[str],
        grade_change: str,
        new_findings_count: int,
        resolved_findings_count: int,
        persistent_findings_count: int,
        diff_json: dict,
    ) -> ScanDiffModel:
        now = datetime.now(timezone.utc)
        diff_id = str(uuid.uuid4())

        if self.is_supabase_configured:
            headers = {
                "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
                "Content-Type": "application/json",
                "Prefer": "resolution=merge-duplicates,return=representation",
            }
            payload = {
                "id": diff_id,
                "scan_id": scan_id,
                "domain_id": domain_id,
                "previous_scan_id": previous_scan_id,
                "grade_change": grade_change,
                "new_findings_count": new_findings_count,
                "resolved_findings_count": resolved_findings_count,
                "persistent_findings_count": persistent_findings_count,
                "diff_json": diff_json,
            }
            async with httpx.AsyncClient(timeout=20.0) as client:
                res = await client.post(
                    f"{settings.SUPABASE_URL}/rest/v1/scan_diffs",
                    headers=headers,
                    json=payload,
                )
                if res.status_code in (200, 201) and res.json():
                    row = res.json()[0]
                    return ScanDiffModel(
                        id=row["id"],
                        scan_id=row["scan_id"],
                        domain_id=row["domain_id"],
                        previous_scan_id=row.get("previous_scan_id"),
                        grade_change=row.get("grade_change", "unchanged"),
                        new_findings_count=row.get("new_findings_count", 0),
                        resolved_findings_count=row.get("resolved_findings_count", 0),
                        persistent_findings_count=row.get("persistent_findings_count", 0),
                        diff_json=row.get("diff_json"),
                        created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")) if row.get("created_at") else None,
                    )

        diff = ScanDiffModel(
            id=diff_id,
            scan_id=scan_id,
            domain_id=domain_id,
            previous_scan_id=previous_scan_id,
            grade_change=grade_change,
            new_findings_count=new_findings_count,
            resolved_findings_count=resolved_findings_count,
            persistent_findings_count=persistent_findings_count,
            diff_json=diff_json,
            created_at=now,
        )
        self._in_memory_diffs[scan_id] = diff
        return diff

    async def get_scan_diff(self, scan_id: str) -> Optional[ScanDiffModel]:
        if self.is_supabase_configured:
            headers = {
                "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
            }
            async with httpx.AsyncClient(timeout=20.0) as client:
                res = await client.get(
                    f"{settings.SUPABASE_URL}/rest/v1/scan_diffs?scan_id=eq.{scan_id}",
                    headers=headers,
                )
                if res.status_code == 200 and res.json():
                    row = res.json()[0]
                    return ScanDiffModel(
                        id=row["id"],
                        scan_id=row["scan_id"],
                        domain_id=row["domain_id"],
                        previous_scan_id=row.get("previous_scan_id"),
                        grade_change=row.get("grade_change", "unchanged"),
                        new_findings_count=row.get("new_findings_count", 0),
                        resolved_findings_count=row.get("resolved_findings_count", 0),
                        persistent_findings_count=row.get("persistent_findings_count", 0),
                        diff_json=row.get("diff_json"),
                    )

        return self._in_memory_diffs.get(scan_id)





repo = DomainRepository()
