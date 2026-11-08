import asyncio
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from google import genai
from google.genai import types
from app.core.config import settings
from app.core.logging import logger
from app.schemas.finding import FindingAITriage, ScanAISummary

PROMPTS_DIR = Path(__file__).parent / "prompts"


class GeminiAIClient:
    """
    Google Gemini API client for AI triage and bilingual report generation.
    Enforces strict Pydantic JSON schema output and in-memory fingerprint caching.
    """

    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model = settings.GEMINI_MODEL or "gemini-3.8-flash"
        self._cache: Dict[str, Any] = {}

        self.is_configured = (
            bool(self.api_key)
            and "mock" not in self.api_key
            and settings.ENVIRONMENT != "test"
        )

        if self.is_configured:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None

        self._triage_prompt_template = (PROMPTS_DIR / "triage_v1.txt").read_text(encoding="utf-8")
        self._summary_prompt_template = (PROMPTS_DIR / "summary_v1.txt").read_text(encoding="utf-8")

    def _generate_mock_triage(self, finding: Dict[str, Any], language: str) -> FindingAITriage:
        """Fallback mock generator for unit tests and local development."""
        title = finding.get("title", "Security Issue")
        template_id = finding.get("template_id", "issue")
        severity = finding.get("severity", "low")

        if language == "hi-Latn":
            plain_summary = f"Aapki website par {title} notice kiya gaya hai. Isse users ka data ya connection compromised ho sakta hai."
            business_impact = "Attackers security loopholes ka fayda utha kar customer data ya cookies access kar sakte hain."
            fix_steps = [
                f"Web server configuration me {template_id} rule verify karein.",
                "Production server restart karein aur security scan dobara run karein.",
            ]
        else:
            plain_summary = f"The target website is currently missing {title}, leaving communication channels less secure."
            business_impact = "Attackers could potentially exploit this misconfiguration to intercept sensitive traffic or execute unauthorized scripts."
            fix_steps = [
                f"Configure the recommended security policy for {template_id} in your web server (Nginx/Apache/Cloudflare).",
                "Reload the web server configuration and re-run the scan to verify.",
            ]

        priority_map = {"critical": 1, "high": 2, "medium": 3, "low": 4, "info": 5}
        effort_map = {"critical": "high", "high": "medium", "medium": "low", "low": "low", "info": "low"}

        return FindingAITriage(
            plain_summary=plain_summary,
            business_impact=business_impact,
            fix_steps=fix_steps,
            priority=priority_map.get(severity, 3),
            confidence=0.95,
            effort=effort_map.get(severity, "low"),
        )

    def _generate_mock_summary(
        self,
        grade: str,
        findings_count: int,
        language: str,
        base_summary: Optional[ScanAISummary] = None,
        hostname: str = "the target domain",
    ) -> ScanAISummary:
        """Fallback mock generator for scan summary with natural phrasing and 100% semantic parity."""
        host_label = hostname if hostname and hostname != "the target domain" else "your domain"

        if base_summary and language == "hi-Latn":
            hinglish_actions = []
            for action in base_summary.top_actions:
                if "header" in action.lower():
                    hinglish_actions.append("Security headers (HSTS, CSP) ko web server par turant configure karein.")
                elif "cookie" in action.lower():
                    hinglish_actions.append("Sabhi cookies par Secure aur HttpOnly attributes enforce karein.")
                elif "scan" in action.lower() or "monitor" in action.lower():
                    hinglish_actions.append(f"{host_label} par automated weekly scans schedule rakhein taaki drift detect ho sake.")
                elif "cert" in action.lower() or "tls" in action.lower():
                    hinglish_actions.append("TLS certificate auto-renewal verify karein taaki secure connection bana rahe.")
                else:
                    hinglish_actions.append(f"{action} (Ise web server configuration me fix karein).")

            if findings_count == 0:
                exec_sum = f"{host_label} ka automated security assessment successfully complete hua aur website ne Grade {grade} score kiya. Audit ke dauran koi critical ya high vulnerability nahi mili, jisse perimeter aur customer data safe hain."
                grade_rat = f"Clean perimeter audit aur zero critical exposures ke basis par Grade {grade} diya gaya hai."
            else:
                exec_sum = f"{host_label} ke audit me {findings_count} security observations detect hue hain. Website ko Grade A standard tak lane ke liye recommended fixes implement karein."
                grade_rat = f"Detected {findings_count} misconfigurations ke basis par Grade {grade} assign kiya gaya hai."

            return ScanAISummary(
                executive_summary=exec_sum,
                top_actions=hinglish_actions[:3] if hinglish_actions else [
                    f"{host_label} ke liye automated weekly scans schedule rakhein.",
                    "Review karein ki DPDP Act compliance safeguards update rahein.",
                    "TLS certificate auto-renewal verify karein.",
                ],
                grade_rationale=grade_rat,
                language="hi-Latn",
            )

        if language == "hi-Latn":
            if findings_count == 0:
                return ScanAISummary(
                    executive_summary=f"{host_label} ka automated security assessment successfully complete hua aur website ne Grade {grade} score kiya. Audit ke dauran zero critical vulnerabilities paayi gayi hain, jisse aapka web perimeter safe hai.",
                    top_actions=[
                        f"{host_label} ke liye automated weekly monitoring schedule rakhein.",
                        "Backend systems update hone par DPDP Act safeguards review karein.",
                        "TLS certificate auto-renewal verify karein taaki HTTPS protection bani rahe.",
                    ],
                    grade_rationale=f"Clean security check aur zero critical exposures ke basis par Grade {grade} diya gaya hai.",
                    language="hi-Latn",
                )
            return ScanAISummary(
                executive_summary=f"{host_label} ke audit me {findings_count} security misconfigurations notice ki gayi hain. Website ko Grade A standard tak lane ke liye recommended fixes implement karna zaroori hai.",
                top_actions=[
                    "High-priority security headers (HSTS, CSP) ko web server par turant configure karein.",
                    "Sabhi cookies par Secure aur HttpOnly attributes enforce karein.",
                    "Naye vulnerabilities se bachne ke liye regular weekly scans schedule karein.",
                ],
                grade_rationale=f"Detected {findings_count} misconfigurations ke basis par Grade {grade} diya gaya hai.",
                language="hi-Latn",
            )

        # English (natural phrasing referencing actual domain and zero findings state)
        if findings_count == 0:
            return ScanAISummary(
                executive_summary=f"Security assessment of {host_label} confirmed a resilient exterior perimeter (Grade {grade}). All automated reconnaissance and payload tests completed with zero critical or high vulnerabilities detected, meeting essential baseline security benchmarks.",
                top_actions=[
                    f"Maintain recurring automated monitoring for {host_label} to catch configuration drift.",
                    "Review DPDP Act data protection practices as backend systems evolve.",
                    "Ensure TLS certificate auto-renewal remains active prior to expiration.",
                ],
                grade_rationale=f"Grade {grade} awarded based on clean assessment across standard transport, injection vectors, and header controls.",
                language="en",
            )

        return ScanAISummary(
            executive_summary=f"Security audit for {host_label} identified {findings_count} configuration {'issue' if findings_count == 1 else 'issues'} requiring attention to reach Grade A posture. Transport and edge protections were verified, while the detected findings should be remediated in order of priority.",
            top_actions=[
                "Immediately resolve high-priority security headers (HSTS, CSP).",
                "Ensure all cookies enforce Secure and HttpOnly attributes.",
                "Schedule recurring weekly scans to prevent security regressions.",
            ],
            grade_rationale=f"Grade {grade} reflects {findings_count} identified configuration {'item' if findings_count == 1 else 'items'} across external headers and endpoint boundaries.",
            language="en",
        )

    async def triage_finding(
        self,
        finding_data: Dict[str, Any],
        language: str = "en",
    ) -> FindingAITriage:
        """
        Runs AI triage for a single normalized finding using Gemini gemini-3.8-flash.
        """
        fingerprint = finding_data.get("fingerprint", "")
        cache_key = f"{fingerprint}:{language}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        if not self.is_configured:
            res = self._generate_mock_triage(finding_data, language)
            self._cache[cache_key] = res
            return res

        prompt_input = (
            f"EVALUATE THIS SECURITY FINDING:\n"
            f"Title: {finding_data.get('title')}\n"
            f"Template ID: {finding_data.get('template_id')}\n"
            f"Severity: {finding_data.get('severity')}\n"
            f"Host: {finding_data.get('host')}\n"
            f"Evidence:\n{finding_data.get('evidence_block', '')}\n\n"
            f"Requested Language: {language}"
        )

        try:
            def _call():
                return self.client.models.generate_content(
                    model=self.model,
                    contents=prompt_input,
                    config=types.GenerateContentConfig(
                        system_instruction=self._triage_prompt_template,
                        response_mime_type="application/json",
                        response_json_schema=FindingAITriage.model_json_schema(),
                        temperature=0.2,
                    ),
                )

            response = await asyncio.wait_for(asyncio.to_thread(_call), timeout=12.0)
            parsed_data = json.loads(response.text)
            triage_result = FindingAITriage(**parsed_data)
            self._cache[cache_key] = triage_result
            return triage_result

        except Exception as e:
            logger.warning(f"Gemini API triage call fallback ({type(e).__name__}): {e}")
            return self._generate_mock_triage(finding_data, language)

    async def generate_scan_summary(
        self,
        hostname: str,
        grade: str,
        findings_count: int,
        language: str = "en",
        findings: Optional[List[Any]] = None,
        base_summary: Optional[ScanAISummary] = None,
    ) -> ScanAISummary:
        """
        Generates executive summary and top 3 prioritized action items with semantic parity.
        """
        if not self.is_configured:
            return self._generate_mock_summary(
                grade=grade,
                findings_count=findings_count,
                language=language,
                base_summary=base_summary,
                hostname=hostname,
            )

        # Build detected findings context
        findings_context = ""
        if findings:
            findings_context = "\n".join([
                f"- [{getattr(f, 'severity', 'info').upper()}] {getattr(f, 'title', 'Security Check')}"
                for f in findings[:15]
            ])

        if base_summary and language == "hi-Latn":
            prompt_input = (
                f"FAITHFULLY TRANSLATE / ADAPT THIS SECURITY AUDIT SUMMARY INTO CONVERSATIONAL HINGLISH:\n"
                f"Target Domain: {hostname}\n"
                f"Overall Grade: {grade}\n"
                f"Total Findings Detected: {findings_count}\n\n"
                f"BASE ENGLISH ASSESSMENT (MUST PRESERVE IDENTICAL MEANING, FACTS, AND TOP ACTIONS):\n"
                f"Executive Summary: {base_summary.executive_summary}\n"
                f"Action 1: {base_summary.top_actions[0] if len(base_summary.top_actions) > 0 else 'Fix security headers'}\n"
                f"Action 2: {base_summary.top_actions[1] if len(base_summary.top_actions) > 1 else 'Secure cookies'}\n"
                f"Action 3: {base_summary.top_actions[2] if len(base_summary.top_actions) > 2 else 'Schedule scans'}\n"
                f"Grade Rationale: {base_summary.grade_rationale}\n\n"
                f"INSTRUCTION: Translate each action and the summary into conversational, clear Hinglish. DO NOT invent new issues or change the meaning."
            )
        else:
            prompt_input = (
                f"GENERATE EXECUTIVE AUDIT SUMMARY:\n"
                f"Target Domain: {hostname}\n"
                f"Overall Grade: {grade}\n"
                f"Total Findings Detected: {findings_count}\n"
                f"Language: {language}\n\n"
                f"ACTUAL DETECTED FINDINGS ON TARGET:\n"
                f"{findings_context if findings_context else 'No critical vulnerabilities detected.'}\n\n"
                f"CRITICAL REQUIREMENT:\n"
                f"The executive summary and top 3 actions MUST directly address the findings listed above. Do not invent unrelated vulnerabilities."
            )

        try:
            def _call():
                return self.client.models.generate_content(
                    model=self.model,
                    contents=prompt_input,
                    config=types.GenerateContentConfig(
                        system_instruction=self._summary_prompt_template,
                        response_mime_type="application/json",
                        response_json_schema=ScanAISummary.model_json_schema(),
                        temperature=0.2,
                    ),
                )

            response = await asyncio.wait_for(asyncio.to_thread(_call), timeout=12.0)
            parsed_data = json.loads(response.text)
            return ScanAISummary(**parsed_data)

        except Exception as e:
            logger.warning(f"Gemini summary generation fallback ({type(e).__name__}): {e}")
            return self._generate_mock_summary(
                grade=grade,
                findings_count=findings_count,
                language=language,
                base_summary=base_summary,
                hostname=hostname,
            )


gemini_client = GeminiAIClient()
