import inspect
import os
import sys
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import Mock, patch


BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
os.environ.setdefault("GROQ_API_KEY", "test-key")

import Services.expertReview as expert_review_module
from graph.candidate import CandidateMetrics, CandidateState
from llm.provider import LLMResponse
from Services.diagramOrchestrator import OrchestrationResult
from Services.expertReview import (
    ExpertReviewConfig,
    ExpertReviewResult,
    LLMExpertReviewAgent,
    fallback_select_candidate,
)
from Services.expertReviewService import ExpertReviewService
from Services.multiAgentGeneration import MultiAgentGenerationResult
from Services.umlService import UMLService


class FakeProvider:
    def __init__(self, content: str | None = None, error: Exception | None = None):
        self.content = content or (
            '{"selected_candidate_id":"candidate_1","reason":"best consistency","confidence":0.8}'
        )
        self.error = error
        self.calls = []

    def complete(self, *, model, messages, temperature, max_tokens):
        self.calls.append({
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        })
        if self.error:
            raise self.error
        return LLMResponse(
            content=self.content,
            provider="fake-expert-provider",
            model=model,
            input_tokens=11,
            output_tokens=12,
            total_tokens=23,
            latency_ms=45.0,
        )


def validation(passed=True, errors=None, total_checks=3, passed_checks=3):
    return {
        "passed": passed,
        "errors": errors or [],
        "warnings": [],
        "total_checks": total_checks,
        "passed_checks": passed_checks,
    }


def candidate(
    candidate_id: str,
    status: str = "valid",
    error_severity: str | None = None,
    passed_checks: int = 3,
) -> CandidateState:
    name = candidate_id.replace("_", "").title()
    errors = []
    if error_severity:
        errors.append({
            "rule_id": "TEST",
            "severity": error_severity,
            "message": f"{candidate_id} validation issue",
        })
    return CandidateState(
        candidate_id=candidate_id,
        provider=f"provider-{candidate_id}",
        model=f"model-{candidate_id}",
        status=status,
        class_diagram={
            "classes": [{"name": name, "attributes": ["id"], "methods": ["save()"]}],
            "relationships": [],
        },
        er_diagram={
            "entities": [{"name": name, "attributes": ["id"], "primary_key": "id"}],
            "relationships": [],
        },
        sequence_diagrams=[{
            "name": f"Save {name}",
            "participants": [name],
            "messages": [{"from": name, "to": name, "message": "save()"}],
        }],
        class_validation=validation(
            passed=error_severity is None,
            errors=errors,
            passed_checks=passed_checks,
        ),
        er_validation=validation(),
        sequence_validation=validation(),
        final_ir={
            "class_diagram": {"classes": [{"name": name}], "relationships": []},
            "er_diagram": {"entities": [{"name": name}], "relationships": []},
            "sequence_diagrams": [{"name": f"Save {name}"}],
        } if status != "failed" else None,
        metrics=CandidateMetrics(
            total_tokens=30,
            total_latency_ms=300.0,
            model_call_count=3,
        ),
    )


def orchestration(*states: CandidateState) -> OrchestrationResult:
    candidates = {state.candidate_id: state for state in states}
    return OrchestrationResult(
        candidates=candidates,
        total_agents=len(candidates),
        completed_agents=len(candidates),
        valid_agents=sum(1 for state in states if state.status == "valid"),
        invalid_agents=sum(1 for state in states if state.status == "invalid"),
        failed_agents=sum(1 for state in states if state.status == "failed"),
        total_model_calls=9,
        total_tokens=90,
        total_latency_ms=900.0,
    )


class ExpertReviewAgentTests(unittest.TestCase):
    def test_expert_review_agent_uses_injected_provider_and_config(self):
        provider = FakeProvider(
            '{"selected_candidate_id":"candidate_2","reason":"best validation","confidence":0.91}'
        )
        config = ExpertReviewConfig("fake", "expert-model", temperature=0.2, max_tokens=777)

        result = LLMExpertReviewAgent(config, provider).review(
            requirements="Build ordering.",
            orchestration_result=orchestration(
                candidate("candidate_1"),
                candidate("candidate_2"),
                candidate("candidate_3"),
            ),
        )

        self.assertEqual(result.selected_candidate_id, "candidate_2")
        self.assertEqual(result.reason, "best validation")
        self.assertEqual(result.confidence, 0.91)
        self.assertFalse(result.fallback_used)
        self.assertEqual(result.metrics.provider, "fake-expert-provider")
        self.assertEqual(result.metrics.model, "expert-model")
        self.assertEqual(result.metrics.total_tokens, 23)
        self.assertEqual(result.metrics.model_call_count, 1)
        self.assertEqual(provider.calls[0]["model"], "expert-model")
        self.assertEqual(provider.calls[0]["temperature"], 0.2)
        self.assertEqual(provider.calls[0]["max_tokens"], 777)

    def test_expert_review_agent_has_no_provider_factory_env_or_groq_dependency(self):
        source = inspect.getsource(expert_review_module)

        self.assertNotIn("get_llm_provider", source)
        self.assertNotIn("os.getenv", source)
        self.assertNotIn("Groq(", source)

    def test_prompt_includes_requirements_all_candidates_and_validation_summaries(self):
        provider = FakeProvider()

        LLMExpertReviewAgent(ExpertReviewConfig("fake", "expert-model"), provider).review(
            requirements="Build invoicing with payments.",
            orchestration_result=orchestration(
                candidate("candidate_1", error_severity="high"),
                candidate("candidate_2"),
                candidate("candidate_3", status="invalid", error_severity="medium"),
            ),
        )

        prompt = provider.calls[0]["messages"][1]["content"]
        self.assertIn("Build invoicing with payments.", prompt)
        self.assertIn('"candidate_1"', prompt)
        self.assertIn('"candidate_2"', prompt)
        self.assertIn('"candidate_3"', prompt)
        self.assertIn('"class_diagram"', prompt)
        self.assertIn('"er_diagram"', prompt)
        self.assertIn('"sequence_diagrams"', prompt)
        self.assertIn('"summary"', prompt)
        self.assertIn('"high_errors"', prompt)

    def test_expert_can_select_candidate_1_2_or_3(self):
        for candidate_id in ["candidate_1", "candidate_2", "candidate_3"]:
            provider = FakeProvider(
                f'{{"selected_candidate_id":"{candidate_id}","reason":"chosen","confidence":0.7}}'
            )
            result = LLMExpertReviewAgent(
                ExpertReviewConfig("fake", "expert-model"),
                provider,
            ).review(
                "requirements",
                orchestration(candidate("candidate_1"), candidate("candidate_2"), candidate("candidate_3")),
            )
            self.assertEqual(result.selected_candidate_id, candidate_id)
            self.assertFalse(result.fallback_used)

    def test_expert_does_not_mutate_candidate_state(self):
        result_set = orchestration(candidate("candidate_1"), candidate("candidate_2"), candidate("candidate_3"))
        before = deepcopy(result_set.candidates["candidate_2"])

        LLMExpertReviewAgent(
            ExpertReviewConfig("fake", "expert-model"),
            FakeProvider('{"selected_candidate_id":"candidate_2","reason":"chosen","confidence":0.7}'),
        ).review("requirements", result_set)

        self.assertEqual(result_set.candidates["candidate_2"], before)

    def test_malformed_json_triggers_fallback(self):
        result = LLMExpertReviewAgent(
            ExpertReviewConfig("fake", "expert-model"),
            FakeProvider("not json"),
        ).review(
            "requirements",
            orchestration(
                candidate("candidate_1", status="invalid", error_severity="medium"),
                candidate("candidate_2"),
                candidate("candidate_3", status="failed"),
            ),
        )

        self.assertTrue(result.fallback_used)
        self.assertEqual(result.selected_candidate_id, "candidate_2")
        self.assertIn("Expert review failed", result.reason)

    def test_provider_exception_triggers_fallback(self):
        result = LLMExpertReviewAgent(
            ExpertReviewConfig("fake", "expert-model"),
            FakeProvider(error=RuntimeError("expert unavailable")),
        ).review(
            "requirements",
            orchestration(candidate("candidate_1"), candidate("candidate_2", status="invalid"), candidate("candidate_3", status="failed")),
        )

        self.assertTrue(result.fallback_used)
        self.assertEqual(result.selected_candidate_id, "candidate_1")
        self.assertIn("expert unavailable", result.reason)

    def test_invalid_candidate_id_triggers_fallback(self):
        result = LLMExpertReviewAgent(
            ExpertReviewConfig("fake", "expert-model"),
            FakeProvider('{"selected_candidate_id":"candidate_99","reason":"chosen","confidence":0.6}'),
        ).review(
            "requirements",
            orchestration(candidate("candidate_1", status="invalid"), candidate("candidate_2"), candidate("candidate_3")),
        )

        self.assertTrue(result.fallback_used)
        self.assertEqual(result.selected_candidate_id, "candidate_2")
        self.assertIn("unknown candidate", result.reason)

    def test_failed_expert_selection_triggers_fallback_when_usable_exists(self):
        result = LLMExpertReviewAgent(
            ExpertReviewConfig("fake", "expert-model"),
            FakeProvider('{"selected_candidate_id":"candidate_3","reason":"chosen","confidence":0.6}'),
        ).review(
            "requirements",
            orchestration(candidate("candidate_1", status="invalid"), candidate("candidate_2"), candidate("candidate_3", status="failed")),
        )

        self.assertTrue(result.fallback_used)
        self.assertEqual(result.selected_candidate_id, "candidate_2")
        self.assertIn("failed candidate", result.reason)

    def test_expert_null_selection_with_all_failed_is_allowed(self):
        result = LLMExpertReviewAgent(
            ExpertReviewConfig("fake", "expert-model"),
            FakeProvider('{"selected_candidate_id":null,"reason":"all failed","confidence":0}'),
        ).review(
            "requirements",
            orchestration(
                candidate("candidate_1", status="failed"),
                candidate("candidate_2", status="failed"),
                candidate("candidate_3", status="failed"),
            ),
        )

        self.assertIsNone(result.selected_candidate_id)
        self.assertFalse(result.fallback_used)
        self.assertEqual(result.confidence, 0)


class ExpertFallbackTests(unittest.TestCase):
    def test_fallback_prefers_valid_over_invalid(self):
        result = fallback_select_candidate(
            orchestration(
                candidate("candidate_1", status="invalid"),
                candidate("candidate_2", status="valid"),
                candidate("candidate_3", status="failed"),
            ),
            "fallback",
        )

        self.assertTrue(result.fallback_used)
        self.assertEqual(result.selected_candidate_id, "candidate_2")

    def test_fallback_prefers_invalid_over_failed(self):
        result = fallback_select_candidate(
            orchestration(
                candidate("candidate_1", status="failed"),
                candidate("candidate_2", status="invalid"),
                candidate("candidate_3", status="failed"),
            ),
            "fallback",
        )

        self.assertEqual(result.selected_candidate_id, "candidate_2")

    def test_fallback_uses_validation_evidence_for_multiple_valid_candidates(self):
        result = fallback_select_candidate(
            orchestration(
                candidate("candidate_1", status="valid", error_severity="high", passed_checks=1),
                candidate("candidate_2", status="valid", error_severity="medium", passed_checks=2),
                candidate("candidate_3", status="valid", passed_checks=3),
            ),
            "fallback",
        )

        self.assertEqual(result.selected_candidate_id, "candidate_3")

    def test_all_three_failed_returns_no_candidate(self):
        result = fallback_select_candidate(
            orchestration(
                candidate("candidate_1", status="failed"),
                candidate("candidate_2", status="failed"),
                candidate("candidate_3", status="failed"),
            ),
            "fallback",
        )

        self.assertTrue(result.fallback_used)
        self.assertIsNone(result.selected_candidate_id)
        self.assertEqual(result.confidence, 0)


class ExpertReviewServiceTests(unittest.TestCase):
    def test_service_resolves_config_provider_and_injects_agent(self):
        config = ExpertReviewConfig("configured-provider", "configured-model")
        provider = Mock()
        expected = ExpertReviewResult("candidate_1", "reason", 0.8)
        agent = Mock()
        agent.review.return_value = expected
        orchestration_result = orchestration(candidate("candidate_1"))

        with patch("Services.expertReviewService.get_llm_provider", return_value=provider) as get_provider, \
             patch("Services.expertReviewService.LLMExpertReviewAgent", return_value=agent) as agent_cls:
            result = ExpertReviewService.review_candidates_internal(
                requirements="requirements",
                orchestration_result=orchestration_result,
                config=config,
            )

        get_provider.assert_called_once_with("configured-provider")
        agent_cls.assert_called_once_with(config=config, provider=provider)
        agent.review.assert_called_once_with(
            requirements="requirements",
            orchestration_result=orchestration_result,
        )
        self.assertIs(result, expected)

    def test_service_uses_injected_provider_without_factory_call(self):
        config = ExpertReviewConfig("configured-provider", "configured-model")
        provider = Mock()
        agent = Mock()
        agent.review.return_value = ExpertReviewResult("candidate_1", "reason", 0.8)

        with patch("Services.expertReviewService.get_llm_provider") as get_provider, \
             patch("Services.expertReviewService.LLMExpertReviewAgent", return_value=agent):
            ExpertReviewService.review_candidates_internal(
                requirements="requirements",
                orchestration_result=orchestration(candidate("candidate_1")),
                config=config,
                provider=provider,
            )

        get_provider.assert_not_called()

    def test_uml_service_multi_agent_internal_returns_orchestration_review_and_selected_candidate(self):
        orchestration_result = orchestration(candidate("candidate_1"), candidate("candidate_2"), candidate("candidate_3"))
        expert_result = ExpertReviewResult("candidate_2", "best", 0.9)
        expected = MultiAgentGenerationResult(
            orchestration=orchestration_result,
            expert_review=expert_result,
            selected_candidate=orchestration_result.candidates["candidate_2"],
        )

        with patch("Services.umlService.CandidateService.get_candidate_configs", return_value=[]), \
             patch("Services.umlService.run_multi_agent_graph", return_value=expected):
            result = UMLService.generate_multi_agent_internal("requirements", ["REQ-001"])

        self.assertIsInstance(result, MultiAgentGenerationResult)
        self.assertIs(result.orchestration, orchestration_result)
        self.assertIs(result.expert_review, expert_result)
        self.assertIs(result.selected_candidate, orchestration_result.candidates["candidate_2"])


if __name__ == "__main__":
    unittest.main()
