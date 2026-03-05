"""Tests for IRT 2PL core functions."""

import math

import pytest

from src.adaptive.irt import (
    ItemParams,
    estimate_theta_eap,
    estimate_theta_mle,
    fisher_information,
    log_likelihood,
    probability,
    select_next_item,
    standard_error,
)

# --- probability ---


class TestProbability:
    def test_at_difficulty(self) -> None:
        """When theta == b, probability should be 0.5 regardless of a."""
        assert probability(0.0, 1.0, 0.0) == pytest.approx(0.5)
        assert probability(2.0, 1.5, 2.0) == pytest.approx(0.5)

    def test_high_theta(self) -> None:
        """High ability should give high probability."""
        p = probability(3.0, 1.0, 0.0)
        assert p > 0.95

    def test_low_theta(self) -> None:
        """Low ability should give low probability."""
        p = probability(-3.0, 1.0, 0.0)
        assert p < 0.05

    def test_higher_discrimination_steeper(self) -> None:
        """Higher a should give steeper ICC — more extreme P for same distance."""
        p_low_a = probability(1.0, 0.5, 0.0)
        p_high_a = probability(1.0, 2.0, 0.0)
        # Both > 0.5 since theta > b, but high-a should be more extreme
        assert p_high_a > p_low_a

    def test_symmetry(self) -> None:
        """P(theta, a, b) should be symmetric around b."""
        p_above = probability(1.0, 1.0, 0.0)
        p_below = probability(-1.0, 1.0, 0.0)
        assert p_above + p_below == pytest.approx(1.0)

    def test_overflow_protection(self) -> None:
        """Extreme values should not cause overflow."""
        p = probability(100.0, 10.0, 0.0)
        assert p == pytest.approx(1.0)
        p = probability(-100.0, 10.0, 0.0)
        assert p == pytest.approx(0.0)

    def test_returns_float(self) -> None:
        assert isinstance(probability(0.0, 1.0, 0.0), float)


# --- fisher_information ---


class TestFisherInformation:
    def test_max_at_theta_equals_b(self) -> None:
        """Fisher info is maximized when theta == b."""
        info_at_b = fisher_information(0.0, 1.0, 0.0)
        info_away = fisher_information(2.0, 1.0, 0.0)
        assert info_at_b > info_away

    def test_proportional_to_a_squared(self) -> None:
        """Info should scale with a^2 at the same theta-b."""
        info_a1 = fisher_information(0.0, 1.0, 0.0)
        info_a2 = fisher_information(0.0, 2.0, 0.0)
        assert info_a2 == pytest.approx(info_a1 * 4.0)

    def test_max_value(self) -> None:
        """Maximum info at theta=b is a^2 * 0.25."""
        a = 1.5
        info = fisher_information(0.0, a, 0.0)
        assert info == pytest.approx(a * a * 0.25)

    def test_always_positive(self) -> None:
        for theta in [-3, -1, 0, 1, 3]:
            assert fisher_information(theta, 1.0, 0.0) > 0


# --- log_likelihood ---


class TestLogLikelihood:
    def test_all_correct_higher_theta_better(self) -> None:
        """All-correct responses should have higher LL for higher theta."""
        responses = [(1.0, 0.0, 1.0)] * 5
        ll_low = log_likelihood(-1.0, responses)
        ll_high = log_likelihood(1.0, responses)
        assert ll_high > ll_low

    def test_all_incorrect_lower_theta_better(self) -> None:
        responses = [(1.0, 0.0, 0.0)] * 5
        ll_low = log_likelihood(-1.0, responses)
        ll_high = log_likelihood(1.0, responses)
        assert ll_low > ll_high

    def test_empty_responses(self) -> None:
        assert log_likelihood(0.0, []) == 0.0


# --- estimate_theta_mle ---


class TestEstimateThetaMLE:
    def test_all_correct_returns_max(self) -> None:
        responses = [(1.0, 0.0, 1.0)] * 10
        theta = estimate_theta_mle(responses, theta_max=4.0)
        assert theta == 4.0

    def test_all_incorrect_returns_min(self) -> None:
        responses = [(1.0, 0.0, 0.0)] * 10
        theta = estimate_theta_mle(responses, theta_min=-4.0)
        assert theta == -4.0

    def test_mixed_converges_near_zero(self) -> None:
        """50% correct on items with b=0 should yield theta near 0."""
        responses = [(1.0, 0.0, 1.0)] * 5 + [(1.0, 0.0, 0.0)] * 5
        theta = estimate_theta_mle(responses)
        assert abs(theta) < 0.5

    def test_high_ability_pattern(self) -> None:
        """Correct on easy + hard items should yield high theta."""
        responses = [
            (1.0, -2.0, 1.0),
            (1.0, -1.0, 1.0),
            (1.0, 0.0, 1.0),
            (1.0, 1.0, 1.0),
            (1.0, 2.0, 0.0),
        ]
        theta = estimate_theta_mle(responses)
        assert theta > 0.5

    def test_empty_returns_initial(self) -> None:
        theta = estimate_theta_mle([], initial_theta=1.5)
        assert theta == 1.5

    def test_respects_bounds(self) -> None:
        responses = [(1.0, 0.0, 1.0)] * 20
        theta = estimate_theta_mle(responses, theta_max=3.0)
        assert theta <= 3.0


# --- estimate_theta_eap ---


class TestEstimateThetaEAP:
    def test_empty_returns_prior_mean(self) -> None:
        theta = estimate_theta_eap([], prior_mean=0.5)
        assert theta == 0.5

    def test_all_correct_positive(self) -> None:
        responses = [(1.0, 0.0, 1.0)] * 10
        theta = estimate_theta_eap(responses)
        assert theta > 1.0

    def test_all_incorrect_negative(self) -> None:
        responses = [(1.0, 0.0, 0.0)] * 10
        theta = estimate_theta_eap(responses)
        assert theta < -1.0

    def test_mixed_near_zero(self) -> None:
        responses = [(1.0, 0.0, 1.0)] * 5 + [(1.0, 0.0, 0.0)] * 5
        theta = estimate_theta_eap(responses)
        assert abs(theta) < 0.5

    def test_eap_does_not_reach_boundary(self) -> None:
        """EAP with prior should not reach extremes like MLE does."""
        responses = [(1.0, 0.0, 1.0)] * 10
        theta = estimate_theta_eap(responses)
        assert theta < 4.0


# --- standard_error ---


class TestStandardError:
    def test_no_items_large_se(self) -> None:
        se = standard_error(0.0, [])
        assert se == 10.0

    def test_more_items_lower_se(self) -> None:
        items_few = [(1.0, 0.0)] * 3
        items_many = [(1.0, 0.0)] * 30
        se_few = standard_error(0.0, items_few)
        se_many = standard_error(0.0, items_many)
        assert se_many < se_few

    def test_high_discrimination_lower_se(self) -> None:
        se_low_a = standard_error(0.0, [(0.5, 0.0)] * 10)
        se_high_a = standard_error(0.0, [(2.0, 0.0)] * 10)
        assert se_high_a < se_low_a

    def test_se_positive(self) -> None:
        se = standard_error(0.0, [(1.0, 0.0)] * 5)
        assert se > 0

    def test_formula_correct(self) -> None:
        """SE = 1/sqrt(sum I)."""
        items = [(1.0, 0.0)]
        info = fisher_information(0.0, 1.0, 0.0)
        expected = 1.0 / math.sqrt(info)
        assert standard_error(0.0, items) == pytest.approx(expected)


# --- select_next_item ---


class TestSelectNextItem:
    def test_selects_most_informative(self) -> None:
        """Item with b closest to theta should be first."""
        items = [
            ItemParams("easy", 1.0, -2.0),
            ItemParams("medium", 1.0, 0.0),
            ItemParams("hard", 1.0, 2.0),
        ]
        result = select_next_item(0.0, items, top_k=1)
        assert len(result) == 1
        assert result[0].item_id == "medium"

    def test_respects_top_k(self) -> None:
        items = [
            ItemParams(f"q{i}", 1.0, float(i - 5))
            for i in range(10)
        ]
        result = select_next_item(0.0, items, top_k=3)
        assert len(result) == 3

    def test_empty_items(self) -> None:
        result = select_next_item(0.0, [], top_k=5)
        assert result == []

    def test_single_item(self) -> None:
        items = [ItemParams("only", 1.0, 0.0)]
        result = select_next_item(0.0, items)
        assert len(result) == 1
        assert result[0].item_id == "only"

    def test_high_discrimination_preferred(self) -> None:
        """Between items at same difficulty, higher a should rank first."""
        items = [
            ItemParams("low_a", 0.5, 0.0),
            ItemParams("high_a", 2.0, 0.0),
        ]
        result = select_next_item(0.0, items, top_k=2)
        assert result[0].item_id == "high_a"

    def test_returns_top_k_or_fewer(self) -> None:
        items = [ItemParams(f"q{i}", 1.0, 0.0) for i in range(3)]
        result = select_next_item(0.0, items, top_k=10)
        assert len(result) == 3
