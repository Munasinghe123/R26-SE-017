from typing import Any


class SequenceEvaluator:
    """
    Reference-based evaluation for Sequence Diagrams.

    Evaluates:
        - Participants
        - Messages
        - Message source/target
        - Message ordering
    """

    @staticmethod
    def _normalize(value: Any) -> str:
        return str(value).strip().lower()

    @staticmethod
    def _prf(
        generated: set[str],
        reference: set[str]
    ) -> dict:

        true_positive = len(generated & reference)
        false_positive = len(generated - reference)
        false_negative = len(reference - generated)

        precision = (
            true_positive / (true_positive + false_positive)
            if true_positive + false_positive > 0
            else 0.0
        )

        recall = (
            true_positive / (true_positive + false_negative)
            if true_positive + false_negative > 0
            else 0.0
        )

        f1 = (
            2 * precision * recall / (precision + recall)
            if precision + recall > 0
            else 0.0
        )

        return {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "true_positive": true_positive,
            "false_positive": false_positive,
            "false_negative": false_negative,
        }

    def _message_signature(self, message: dict) -> str:
        sender = self._normalize(
            message.get(
                "from_participant",
                message.get("from", "")
            )
        )

        receiver = self._normalize(
            message.get(
                "to_participant",
                message.get("to", "")
            )
        )

        method = self._normalize(
            message.get("method", message.get("message", ""))
        )

        return f"{sender}->{receiver}:{method}"

    def evaluate(
        self,
        generated: dict,
        reference: dict
    ) -> dict:

        generated_sequences = generated.get(
            "sequences",
            []
        ) or []

        reference_sequences = reference.get(
            "sequences",
            []
        ) or []

        # ---------------------------------------------------------
        # Participants
        # ---------------------------------------------------------

        generated_participants = set()
        reference_participants = set()

        for sequence in generated_sequences:
            for participant in sequence.get(
                "participants",
                []
            ) or []:
                generated_participants.add(
                    self._normalize(participant)
                )

        for sequence in reference_sequences:
            for participant in sequence.get(
                "participants",
                []
            ) or []:
                reference_participants.add(
                    self._normalize(participant)
                )

        participant_result = self._prf(
            generated_participants,
            reference_participants
        )

        # ---------------------------------------------------------
        # Messages
        # ---------------------------------------------------------

        generated_messages = set()
        reference_messages = set()

        for sequence in generated_sequences:
            for message in sequence.get(
                "messages",
                []
            ) or []:

                if isinstance(message, dict):
                    generated_messages.add(
                        self._message_signature(message)
                    )

        for sequence in reference_sequences:
            for message in sequence.get(
                "messages",
                []
            ) or []:

                if isinstance(message, dict):
                    reference_messages.add(
                        self._message_signature(message)
                    )

        message_result = self._prf(
            generated_messages,
            reference_messages
        )

        # ---------------------------------------------------------
        # Message ordering
        # ---------------------------------------------------------

        generated_order = []

        for sequence in generated_sequences:
            for message in sequence.get(
                "messages",
                []
            ) or []:

                if isinstance(message, dict):
                    generated_order.append(
                        self._message_signature(message)
                    )

        reference_order = []

        for sequence in reference_sequences:
            for message in sequence.get(
                "messages",
                []
            ) or []:

                if isinstance(message, dict):
                    reference_order.append(
                        self._message_signature(message)
                    )

        order_score = self._calculate_order_score(
            generated_order,
            reference_order
        )

        # ---------------------------------------------------------
        # Overall Sequence score
        # ---------------------------------------------------------

        overall_f1 = (
            participant_result["f1"] * 0.4
            + message_result["f1"] * 0.4
            + order_score * 0.2
        )

        return {
            "participants": participant_result,
            "messages": message_result,
            "message_order": {
                "score": round(order_score, 4)
            },
            "overall_f1": round(overall_f1, 4),
        }

    @staticmethod
    def _calculate_order_score(
        generated: list[str],
        reference: list[str]
    ) -> float:

        if not reference:
            return 1.0 if not generated else 0.0

        if not generated:
            return 0.0

        common = [
            message
            for message in reference
            if message in generated
        ]

        if len(common) <= 1:
            return (
                1.0
                if common == reference
                else len(common) / len(reference)
            )

        generated_positions = {
            message: index
            for index, message in enumerate(generated)
        }

        correct_pairs = 0
        total_pairs = 0

        for i in range(len(common)):
            for j in range(i + 1, len(common)):
                first = common[i]
                second = common[j]

                total_pairs += 1

                if (
                    generated_positions[first]
                    < generated_positions[second]
                ):
                    correct_pairs += 1

        if total_pairs == 0:
            return 0.0

        return correct_pairs / total_pairs