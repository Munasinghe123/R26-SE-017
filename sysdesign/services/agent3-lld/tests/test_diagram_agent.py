import inspect
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch


BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
os.environ.setdefault("GROQ_API_KEY", "test-key")

import graph.diagram_agent as diagram_agent_module
from graph.candidate import CandidateConfig, CandidateState
from graph.diagram_agent import CandidateDiagramAgent, DiagramGenerationAgent
from llm.provider import LLMResponse
from Services.candidateService import CandidateService


VALID_CLASS = (
    '{"class_diagram":{"classes":['
    '{"name":"Order","attributes":["id"],"methods":["createOrder()"]},'
    '{"name":"OrderRepository","attributes":["storage"],"methods":["saveOrder()"]}'
    '],"relationships":[{"source":"OrderRepository","target":"Order","type":"association","cardinality":"1"}]}}'
)
VALID_ER = (
    '{"er_diagram":{"entities":['
    '{"name":"Order","attributes":["id"],"primary_key":"id"}'
    '],"relationships":[]}}'
)
VALID_SEQUENCE = (
    '{"sequence_diagrams":[{"name":"Create Order","description":"Create order flow",'
    '"participants":["Order","OrderRepository"],'
    '"messages":[{"from":"Order","to":"OrderRepository","message":"saveOrder()"}]}]}'
)


class FakeProvider:
    def __init__(self):
        self.outputs = [VALID_CLASS, VALID_ER, VALID_SEQUENCE]
        self.calls = []

    def complete(self, *, model, messages, temperature, max_tokens):
        self.calls.append({
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        })
        return LLMResponse(
            content=self.outputs.pop(0),
            provider="fake-provider",
            model=model,
        )


class CandidateDiagramAgentTests(unittest.TestCase):
    def test_candidate_diagram_agent_implements_generation_contract(self):
        agent = CandidateDiagramAgent(
            config=CandidateConfig("candidate_1", "fake", "model-a"),
            provider=FakeProvider(),
        )

        self.assertIsInstance(agent, DiagramGenerationAgent)

    def test_agent_keeps_injected_config_and_provider(self):
        config = CandidateConfig(
            candidate_id="candidate_1",
            provider="configured-provider",
            model="configured-model",
            temperature=0.25,
            max_tokens=2048,
        )
        provider = FakeProvider()

        agent = CandidateDiagramAgent(config=config, provider=provider)

        self.assertIs(agent.config, config)
        self.assertIs(agent.provider, provider)

    def test_generate_delegates_to_existing_candidate_pipeline(self):
        config = CandidateConfig("candidate_1", "fake", "model-a")
        provider = FakeProvider()
        expected_state = CandidateState(
            candidate_id="candidate_1",
            provider="fake",
            model="model-a",
            status="valid",
        )

        with patch.object(
            diagram_agent_module,
            "run_candidate",
            return_value=expected_state,
        ) as run_candidate:
            state = CandidateDiagramAgent(config, provider).generate(
                requirements="Build ordering.",
                requirement_ids=["REQ-001"],
            )

        run_candidate.assert_called_once_with(
            config=config,
            requirements="Build ordering.",
            requirement_ids=["REQ-001"],
            provider=provider,
        )
        self.assertIs(state, expected_state)

    def test_fake_provider_can_be_injected_without_real_llm_call(self):
        provider = FakeProvider()
        agent = CandidateDiagramAgent(
            config=CandidateConfig(
                candidate_id="candidate_1",
                provider="fake",
                model="model-a",
                temperature=0.4,
                max_tokens=900,
            ),
            provider=provider,
        )

        state = agent.generate("Build ordering.", ["REQ-001"])

        self.assertEqual(state.status, "valid")
        self.assertIsNotNone(state.final_ir)
        self.assertEqual(len(provider.calls), 3)
        self.assertEqual([call["model"] for call in provider.calls], ["model-a"] * 3)
        self.assertEqual([call["temperature"] for call in provider.calls], [0.4] * 3)
        self.assertEqual([call["max_tokens"] for call in provider.calls], [900] * 3)

    def test_switching_provider_and_model_requires_no_agent_code_change(self):
        provider_a = FakeProvider()
        provider_b = FakeProvider()

        agent_a = CandidateDiagramAgent(
            config=CandidateConfig("candidate_1", "provider-a", "model-a"),
            provider=provider_a,
        )
        agent_b = CandidateDiagramAgent(
            config=CandidateConfig("candidate_2", "provider-b", "model-b"),
            provider=provider_b,
        )

        state_a = agent_a.generate("Build ordering.", [])
        state_b = agent_b.generate("Build ordering.", [])

        self.assertEqual(state_a.model, "model-a")
        self.assertEqual(state_b.model, "model-b")
        self.assertEqual(provider_a.calls[0]["model"], "model-a")
        self.assertEqual(provider_b.calls[0]["model"], "model-b")

    def test_agent_has_no_provider_factory_env_or_groq_dependency(self):
        source = inspect.getsource(diagram_agent_module)

        self.assertNotIn("get_llm_provider", source)
        self.assertNotIn("os.getenv", source)
        self.assertNotIn("Groq(", source)


class CandidateServiceAgentInjectionTests(unittest.TestCase):
    def test_candidate_service_resolves_provider_and_injects_agent_dependencies(self):
        config = CandidateConfig(
            candidate_id="candidate_1",
            provider="configured-provider",
            model="configured-model",
        )
        provider = Mock()
        expected_state = CandidateState(
            candidate_id="candidate_1",
            provider="configured-provider",
            model="configured-model",
            status="valid",
        )
        agent = Mock()
        agent.generate.return_value = expected_state

        with patch(
            "Services.candidateService.get_llm_provider",
            return_value=provider,
        ) as get_provider, patch(
            "Services.candidateService.CandidateDiagramAgent",
            return_value=agent,
        ) as agent_cls:
            state = CandidateService.run_candidate_internal(
                requirements="Build ordering.",
                requirement_ids=["REQ-001"],
                candidate_config=config,
            )

        get_provider.assert_called_once_with("configured-provider")
        agent_cls.assert_called_once_with(config=config, provider=provider)
        agent.generate.assert_called_once_with(
            requirements="Build ordering.",
            requirement_ids=["REQ-001"],
        )
        self.assertIs(state, expected_state)

    def test_candidate_service_uses_injected_provider_without_factory_call(self):
        config = CandidateConfig("candidate_1", "configured-provider", "configured-model")
        provider = Mock()
        expected_state = CandidateState(
            candidate_id="candidate_1",
            provider="configured-provider",
            model="configured-model",
            status="valid",
        )
        agent = Mock()
        agent.generate.return_value = expected_state

        with patch("Services.candidateService.get_llm_provider") as get_provider, patch(
            "Services.candidateService.CandidateDiagramAgent",
            return_value=agent,
        ) as agent_cls:
            state = CandidateService.run_candidate_internal(
                requirements="Build ordering.",
                requirement_ids=None,
                candidate_config=config,
                provider=provider,
            )

        get_provider.assert_not_called()
        agent_cls.assert_called_once_with(config=config, provider=provider)
        agent.generate.assert_called_once_with(
            requirements="Build ordering.",
            requirement_ids=[],
        )
        self.assertIs(state, expected_state)


if __name__ == "__main__":
    unittest.main()
