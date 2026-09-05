"""
Sentinel — Coordinated Payment Abuse Intelligence
Module: LLM Investigator (llm_investigator.py)

Purpose:
Translates structured InvestigationCase evidence objects produced by upstream deterministic
Sentinel components into objective, human-readable InvestigationReport JSON documents.

Architectural Guarantees:
------------------------
1. EXPLANATION LAYER ONLY: The LLM is an investigation report generator, NOT a fraud detector.
2. DECISION AUTHORITY: The deterministic Fusion Risk Engine owns the risk_score, risk_level, and action.
   The LLM preserves them EXACTLY and can NEVER alter them or output 'BLOCK'.
3. GRAPH REASONING GUARDRAIL: Enforces GRAPH CONNECTION != FRAUD. Distinguishes infrastructure
   connectivity from behavioral/ML fraud evidence.
4. ABSOLUTE EVIDENCE AUTHORITY: Never invents facts, timestamps, locations, or ground-truth labels.
5. SAFE FAILURE BEHAVIOR: Provider errors or validation failures raise controlled exceptions
   without hiding or corrupting access to the deterministic decision.
"""

import json
import os
from typing import Dict, Any, Optional

try:
    from .report_schema import InvestigationReport, RiskAssessment, SupportingEvidence
    from .validate_report import validate_investigation_report
except ImportError:
    from report_schema import InvestigationReport, RiskAssessment, SupportingEvidence
    from validate_report import validate_investigation_report


class LLMInvestigatorError(Exception):
    """
    Raised when LLM investigation report generation or validation fails.
    """
    pass


# ==============================================================================
# 1. LLM PROVIDER ABSTRACTION
# ==============================================================================

class LLMProvider:
    """
    Abstract base class for LLM API providers.
    """
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        raise NotImplementedError("Subclasses must implement generate()")


class MockLLMProvider(LLMProvider):
    """
    Deterministic fallback LLM Provider for testing, offline execution, and environment setup
    where API keys are unavailable. Generates compliant InvestigationReport JSON strictly derived
    from the input InvestigationCase facts.
    """
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        # Extract the case dictionary string from user_prompt
        try:
            start_idx = user_prompt.find("{")
            end_idx = user_prompt.rfind("}")
            if start_idx != -1 and end_idx != -1:
                case_json_str = user_prompt[start_idx:end_idx + 1]
                case = json.loads(case_json_str)
            else:
                raise ValueError("No JSON object found in prompt")
        except Exception as e:
            raise LLMInvestigatorError(f"MockLLMProvider failed to parse input case JSON: {e}")

        case_id = case.get("case_id", "CASE_UNKNOWN")
        dec = case.get("decision", {})
        tsum = case.get("transaction_summary", {})
        ml_ev = case.get("ml_evidence", {})
        g_ev = case.get("graph_evidence", {})
        b_ev = case.get("behavioral_evidence", {})
        ben_ev = case.get("benign_evidence", {})
        items = case.get("evidence_items", [])

        risk_score = float(dec.get("risk_score", 0.0))
        risk_level = str(dec.get("risk_level", "LOW"))
        action = str(dec.get("action", "ALLOW"))
        threshold = float(dec.get("threshold_applied", 0.45))

        target_txn = tsum.get("target_transaction_id", "N/A")
        target_usr = tsum.get("target_user_id", "N/A")
        amt = tsum.get("amount", 0.0)

        # 1. Generate why_flagged bullet points from observable evidence items
        why_flagged = []
        for item in items:
            desc = item.get("description")
            if desc:
                why_flagged.append(desc)

        if not why_flagged:
            why_flagged.append("Transaction metrics evaluated cleanly across all pipeline dimensions.")

        # 2. Supporting Evidence Layer Summaries
        ml_prob = ml_ev.get("predicted_probability", 0.0)
        ml_summary = f"RandomForestClassifier predicted anomaly probability of {ml_prob * 100:.1f}% for transaction {target_txn}."

        u_cnt = g_ev.get("users_count", 1)
        d_cnt = g_ev.get("devices_count", 1)
        ip_cnt = g_ev.get("ips_count", 1)
        c_cnt = g_ev.get("cards_count", 1)
        m_conc = g_ev.get("merchant_concentration", 0.0)
        top_m = g_ev.get("top_merchant_id", "N/A")

        graph_summary = (
            f"Infrastructure cluster links {u_cnt} user(s) across {d_cnt} device(s), {ip_cnt} IP address(es), "
            f"and {c_cnt} card(s). Merchant concentration for {top_m} is {m_conc * 100:.1f}%."
        )

        acc_age = b_ev.get("account_age_days", 0)
        tx_hr = b_ev.get("transactions_last_hour", 0)
        tx_dy = b_ev.get("transactions_last_day", 0)
        failed_tx = b_ev.get("failed_transactions", 0)
        behavioral_summary = (
            f"Target account age is {acc_age} day(s) with velocity of {tx_hr} txns/hr ({tx_dy} txns/day) "
            f"and {failed_tx} recent payment declines."
        )

        # 3. Benign Considerations
        is_benign = ben_ev.get("is_benign_pattern_detected", False)
        benign_signals = ben_ev.get("benign_signals", [])

        if is_benign:
            benign_summary = (
                f"Benign network pattern detected: {'; '.join(benign_signals)}. "
                "Infrastructure sharing in this context exhibits metrics consistent with legitimate shared usage (e.g. office/household network)."
            )
        else:
            benign_summary = "No evidence of benign network suppression patterns identified in the connected cluster."

        # 4. Investigation Summary
        if action == "INVESTIGATE":
            inv_summary = (
                f"Case {case_id} for user {target_usr} (${amt:.2f}) was flagged for manual investigation "
                f"with a deterministic combined risk score of {risk_score:.4f} (level: {risk_level}). "
                f"Elevated risk is driven by multi-signal evidence from single-transaction ML ({ml_prob*100:.1f}%) "
                f"and graph infrastructure density."
            )
            analyst_rec = (
                f"Recommend manual risk analyst review for transaction {target_txn}. "
                "Inspect connected payment instruments and shared device fingerprints before final authorization. "
                f"Preserve deterministic engine action '{action}'."
            )
        elif action == "MONITOR":
            inv_summary = (
                f"Case {case_id} for user {target_usr} (${amt:.2f}) returned a moderate risk score of {risk_score:.4f} "
                f"(level: {risk_level}) and was routed for monitoring."
            )
            analyst_rec = f"Monitor upcoming transaction velocity for user {target_usr}. No immediate blocking action required."
        else:
            inv_summary = (
                f"Case {case_id} for user {target_usr} (${amt:.2f}) evaluated as LOW risk (score: {risk_score:.4f})."
            )
            analyst_rec = "Transaction exhibits normal profile. Allow transaction execution."

        limitations = (
            "Graph infrastructure connectivity alone is contextual evidence and does NOT prove fraudulent intent. "
            "Available evidence cannot establish unobserved offline relationships or intent."
        )

        report_dict = {
            "case_id": case_id,
            "investigation_summary": inv_summary,
            "risk_assessment": {
                "risk_score": risk_score,
                "risk_level": risk_level,
                "action": action,
                "threshold_applied": threshold
            },
            "why_flagged": why_flagged,
            "supporting_evidence": {
                "ml_evidence": ml_summary,
                "graph_evidence": graph_summary,
                "behavioral_evidence": behavioral_summary
            },
            "benign_considerations": benign_summary,
            "analyst_recommendation": analyst_rec,
            "limitations": limitations
        }

        return json.dumps(report_dict, indent=2)


class GeminiProvider(LLMProvider):
    """
    LLM Provider integrating with Google GenAI / Gemini API if GEMINI_API_KEY is configured.
    """
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise LLMInvestigatorError("GEMINI_API_KEY environment variable is missing.")

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        try:
            from google import genai
            client = genai.Client(api_key=self.api_key)
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=f"{system_prompt}\n\n{user_prompt}"
            )
            return response.text
        except Exception as e:
            raise LLMInvestigatorError(f"Gemini API invocation failed: {e}")


class OpenAIProvider(LLMProvider):
    """
    LLM Provider integrating with OpenAI API if OPENAI_API_KEY is configured.
    """
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise LLMInvestigatorError("OPENAI_API_KEY environment variable is missing.")

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"}
            )
            return response.choices[0].message.content
        except Exception as e:
            raise LLMInvestigatorError(f"OpenAI API invocation failed: {e}")


class AutoLLMProvider(LLMProvider):
    """
    Automatic LLM Provider: selects GeminiProvider or OpenAIProvider if credentials exist,
    otherwise cleanly falls back to MockLLMProvider for offline deterministic execution.
    """
    def __init__(self):
        if os.environ.get("GEMINI_API_KEY"):
            print("[AutoLLMProvider] Initializing GeminiProvider with environment API key...")
            self._provider = GeminiProvider()
        elif os.environ.get("OPENAI_API_KEY"):
            print("[AutoLLMProvider] Initializing OpenAIProvider with environment API key...")
            self._provider = OpenAIProvider()
        else:
            print("[AutoLLMProvider] No API keys found in environment. Using MockLLMProvider (deterministic offline mode)...")
            self._provider = MockLLMProvider()

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        return self._provider.generate(system_prompt, user_prompt)


# ==============================================================================
# 2. SYSTEM PROMPT WITH STRICT GUARDRAILS
# ==============================================================================

SYSTEM_PROMPT = """You are an investigation report generator for a fraud-risk system, NOT a fraud detector.

Your core responsibility is to translate structured InvestigationCase evidence JSON into an objective, factual, human-readable InvestigationReport JSON for human risk analysts.

STRICT MANDATORY RULES & GUARDRAILS:
------------------------------------
1. EVIDENCE AUTHORITY: The provided evidence JSON is the complete factual basis for your report. Do not cite facts outside the JSON.
2. NO FABRICATION: Never invent timestamps, user identities, relationships, intent, history, geographic locations, merchant relationships, or ground-truth labels.
3. NO UNSUPPORTED INFERENCE: You may explain implications of evidence, but clearly distinguish observed facts from interpretation.
4. GRAPH CAUTION (GRAPH CONNECTION != FRAUD): Shared infrastructure or graph connectivity alone is NOT proof of fraud. You MUST explicitly distinguish infrastructure connectivity evidence from behavioral/ML fraud evidence.
5. DECISION AUTHORITY: The deterministic risk engine owns risk_score, risk_level, and action. You MUST preserve them EXACTLY in the risk_assessment field. You MUST NOT change them and MUST NEVER output 'BLOCK'.
6. HUMAN OVERSIGHT: You provide an investigation report for a human analyst. You do not execute enforcement actions.
7. UNCERTAINTY & LIMITATIONS: When evidence is insufficient or conflicting, explicitly state the limitation.

REQUIRED OUTPUT JSON FORMAT:
----------------------------
Return ONLY valid JSON matching this exact structure:
{
  "case_id": "<string matching input>",
  "investigation_summary": "<summary text>",
  "risk_assessment": {
    "risk_score": <float matching input exact value>,
    "risk_level": "<string matching input exact value>",
    "action": "<string matching input exact value>",
    "threshold_applied": <float matching input exact value>
  },
  "why_flagged": ["<bullet point 1>", "<bullet point 2>"],
  "supporting_evidence": {
    "ml_evidence": "<factual ML model prediction summary>",
    "graph_evidence": "<factual graph connectivity summary>",
    "behavioral_evidence": "<factual behavioral velocity summary>"
  },
  "benign_considerations": "<summary of benign network signals if present>",
  "analyst_recommendation": "<recommendation aligned strictly with deterministic action>",
  "limitations": "<statement of what evidence cannot establish>"
}
"""


# ==============================================================================
# 3. LLM INVESTIGATOR CLASS
# ==============================================================================

class LLMInvestigator:
    """
    Generates structured InvestigationReport objects from validated InvestigationCase evidence.
    """
    def __init__(self, provider: Optional[LLMProvider] = None):
        self.provider = provider or AutoLLMProvider()

    def generate_report(self, case: Any) -> InvestigationReport:
        """
        Generates and validates an InvestigationReport from an input InvestigationCase object or dict.
        
        Args:
            case (Any): InvestigationCase object or dictionary representation.
            
        Returns:
            InvestigationReport: Validated, standard JSON-serializable InvestigationReport object.
            
        Raises:
            LLMInvestigatorError: If provider fails or generated report violates schema/decision authority.
        """
        # Format case input as dict
        if hasattr(case, "to_dict"):
            case_dict = case.to_dict()
        elif isinstance(case, dict):
            case_dict = case
        else:
            raise LLMInvestigatorError("Input case must be an InvestigationCase object or dictionary.")

        user_prompt = f"Target InvestigationCase Evidence JSON:\n{json.dumps(case_dict, indent=2)}"

        # Invoke LLM provider safely
        try:
            raw_response = self.provider.generate(SYSTEM_PROMPT, user_prompt)
        except Exception as e:
            raise LLMInvestigatorError(f"LLM Provider invocation failed: {e}")

        # Parse JSON response
        try:
            clean_str = raw_response.strip()
            if clean_str.startswith("```json"):
                clean_str = clean_str[7:]
            if clean_str.endswith("```"):
                clean_str = clean_str[:-3]
            clean_str = clean_str.strip()

            report_dict = json.loads(clean_str)
        except Exception as e:
            raise LLMInvestigatorError(f"Failed to parse LLM provider response as valid JSON: {e}\nRaw output:\n{raw_response}")

        # Validate report against schema and decision authority
        is_valid, errors = validate_investigation_report(report_dict, expected_case=case_dict)
        if not is_valid:
            raise LLMInvestigatorError(f"Generated InvestigationReport failed validation: {errors}")

        # Construct InvestigationReport dataclass
        risk_ass_dict = report_dict["risk_assessment"]
        risk_assessment = RiskAssessment(
            risk_score=float(risk_ass_dict["risk_score"]),
            risk_level=str(risk_ass_dict["risk_level"]),
            action=str(risk_ass_dict["action"]),
            threshold_applied=float(risk_ass_dict["threshold_applied"])
        )

        supp_ev_dict = report_dict["supporting_evidence"]
        supporting_evidence = SupportingEvidence(
            ml_evidence=str(supp_ev_dict["ml_evidence"]),
            graph_evidence=str(supp_ev_dict["graph_evidence"]),
            behavioral_evidence=str(supp_ev_dict["behavioral_evidence"])
        )

        return InvestigationReport(
            case_id=str(report_dict["case_id"]),
            investigation_summary=str(report_dict["investigation_summary"]),
            risk_assessment=risk_assessment,
            why_flagged=list(report_dict["why_flagged"]),
            supporting_evidence=supporting_evidence,
            benign_considerations=str(report_dict["benign_considerations"]),
            analyst_recommendation=str(report_dict["analyst_recommendation"]),
            limitations=str(report_dict["limitations"])
        )
