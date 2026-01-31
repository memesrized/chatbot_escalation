"""Metrics calculation for escalation decisions."""

from dataclasses import dataclass


@dataclass
class ConfusionMatrix:
    """Container for confusion matrix values."""

    true_positives: int
    true_negatives: int
    false_positives: int
    false_negatives: int

    @property
    def total(self) -> int:
        """Total number of predictions."""
        return (
            self.true_positives
            + self.true_negatives
            + self.false_positives
            + self.false_negatives
        )

    @property
    def correct(self) -> int:
        """Number of correct predictions."""
        return self.true_positives + self.true_negatives


@dataclass
class ClassificationMetrics:
    """Classification metrics for escalation decisions."""

    accuracy: float
    precision: float
    recall: float
    f1_score: float
    confusion_matrix: ConfusionMatrix


@dataclass
class EarlyEscalationMetrics:
    """Metrics for early escalation timing."""

    true_positive_count: int
    true_positive_avg_turns_early: float
    true_positive_median_turns_early: float
    false_positive_count: int
    false_positive_avg_turns_early: float
    false_positive_median_turns_early: float


class EscalationMetrics:
    """Calculate evaluation metrics for escalation decisions."""

    @staticmethod
    def calculate_confusion_matrix(
        y_true: list[bool], y_pred: list[bool]
    ) -> ConfusionMatrix:
        """
        Calculate confusion matrix from predictions.

        Args:
            y_true: Expected escalation decisions
            y_pred: Predicted escalation decisions

        Returns:
            ConfusionMatrix with TP, TN, FP, FN counts
        """
        tp = sum(1 for t, p in zip(y_true, y_pred) if t and p)
        tn = sum(1 for t, p in zip(y_true, y_pred) if not t and not p)
        fp = sum(1 for t, p in zip(y_true, y_pred) if not t and p)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t and not p)
        return ConfusionMatrix(tp, tn, fp, fn)

    @staticmethod
    def calculate_metrics(
        y_true: list[bool], y_pred: list[bool]
    ) -> ClassificationMetrics:
        """
        Calculate classification metrics.

        Args:
            y_true: Expected escalation decisions
            y_pred: Predicted escalation decisions

        Returns:
            ClassificationMetrics with accuracy, precision, recall, F1
        """
        cm = EscalationMetrics.calculate_confusion_matrix(y_true, y_pred)

        # Calculate accuracy
        accuracy = cm.correct / cm.total if cm.total > 0 else 0.0

        # Calculate precision, recall, F1
        precision = (
            cm.true_positives / (cm.true_positives + cm.false_positives)
            if (cm.true_positives + cm.false_positives) > 0
            else 0.0
        )
        recall = (
            cm.true_positives / (cm.true_positives + cm.false_negatives)
            if (cm.true_positives + cm.false_negatives) > 0
            else 0.0
        )
        f1_score = (
            2 * (precision * recall) / (precision + recall)
            if (precision + recall) > 0
            else 0.0
        )

        return ClassificationMetrics(
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1_score=f1_score,
            confusion_matrix=cm,
        )

    @staticmethod
    def _calculate_median(values: list[int | float]) -> float:
        """Calculate median of a list of values."""
        if not values:
            return 0.0
        sorted_values = sorted(values)
        n = len(sorted_values)
        if n % 2 == 1:
            return float(sorted_values[n // 2])
        return (sorted_values[n // 2 - 1] + sorted_values[n // 2]) / 2

    @staticmethod
    def calculate_early_escalation_metrics(
        early_escalations_when_needed: list[int],
        false_escalations: list[int],
    ) -> EarlyEscalationMetrics:
        """
        Calculate early escalation timing metrics.

        Args:
            early_escalations_when_needed: Turns before end for correct escalations
            false_escalations: Turns before end for incorrect escalations

        Returns:
            EarlyEscalationMetrics with timing statistics
        """
        # True positive metrics
        tp_count = len(early_escalations_when_needed)
        tp_avg = sum(early_escalations_when_needed) / tp_count if tp_count > 0 else 0.0
        tp_median = EscalationMetrics._calculate_median(early_escalations_when_needed)

        # False positive metrics
        fp_count = len(false_escalations)
        fp_avg = sum(false_escalations) / fp_count if fp_count > 0 else 0.0
        fp_median = EscalationMetrics._calculate_median(false_escalations)

        return EarlyEscalationMetrics(
            true_positive_count=tp_count,
            true_positive_avg_turns_early=tp_avg,
            true_positive_median_turns_early=tp_median,
            false_positive_count=fp_count,
            false_positive_avg_turns_early=fp_avg,
            false_positive_median_turns_early=fp_median,
        )
