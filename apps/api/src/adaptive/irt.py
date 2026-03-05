"""IRT 2PL (Two-Parameter Logistic) model implementation.

Core functions for:
- Item response probability
- Fisher information
- Theta (ability) estimation via MLE (Newton-Raphson)
- Standard error of theta
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ItemParams:
    """IRT item parameters."""

    item_id: str
    a: float  # discrimination (> 0)
    b: float  # difficulty


def probability(theta: float, a: float, b: float) -> float:
    """P(correct | theta, a, b) using the 2PL model.

    P = 1 / (1 + exp(-a * (theta - b)))
    """
    z = a * (theta - b)
    # Clamp to avoid overflow
    z = max(-30.0, min(30.0, z))
    return 1.0 / (1.0 + math.exp(-z))


def fisher_information(theta: float, a: float, b: float) -> float:
    """Fisher information of an item at a given theta.

    I(theta) = a^2 * P(theta) * (1 - P(theta))
    """
    p = probability(theta, a, b)
    return a * a * p * (1.0 - p)


def log_likelihood(
    theta: float,
    responses: list[tuple[float, float, float]],
) -> float:
    """Log-likelihood of responses given theta.

    Args:
        theta: Ability estimate.
        responses: List of (a, b, correct) tuples where correct is 0 or 1.
    """
    ll = 0.0
    for a, b, correct in responses:
        p = probability(theta, a, b)
        # Clamp to avoid log(0)
        p = max(1e-15, min(1.0 - 1e-15, p))
        if correct >= 0.5:
            ll += math.log(p)
        else:
            ll += math.log(1.0 - p)
    return ll


def _mle_derivatives(
    theta: float,
    responses: list[tuple[float, float, float]],
) -> tuple[float, float]:
    """First and second derivatives of the log-likelihood w.r.t. theta."""
    d1 = 0.0
    d2 = 0.0
    for a, b, correct in responses:
        p = probability(theta, a, b)
        residual = correct - p
        d1 += a * residual
        d2 -= a * a * p * (1.0 - p)
    return d1, d2


def estimate_theta_mle(
    responses: list[tuple[float, float, float]],
    initial_theta: float = 0.0,
    max_iter: int = 50,
    tol: float = 1e-5,
    theta_min: float = -4.0,
    theta_max: float = 4.0,
) -> float:
    """Estimate theta via Maximum Likelihood (Newton-Raphson).

    Args:
        responses: List of (a, b, correct) tuples.
        initial_theta: Starting theta estimate.
        max_iter: Maximum Newton-Raphson iterations.
        tol: Convergence tolerance.
        theta_min: Lower bound for theta.
        theta_max: Upper bound for theta.

    Returns:
        Estimated theta, clamped to [theta_min, theta_max].
    """
    if not responses:
        return initial_theta

    # All correct or all incorrect -> clamp to boundary
    all_correct = all(c >= 0.5 for _, _, c in responses)
    all_incorrect = all(c < 0.5 for _, _, c in responses)
    if all_correct:
        return theta_max
    if all_incorrect:
        return theta_min

    theta = initial_theta
    for _ in range(max_iter):
        d1, d2 = _mle_derivatives(theta, responses)
        if abs(d2) < 1e-15:
            break
        delta = d1 / d2
        theta -= delta
        theta = max(theta_min, min(theta_max, theta))
        if abs(delta) < tol:
            break

    return theta


def estimate_theta_eap(
    responses: list[tuple[float, float, float]],
    prior_mean: float = 0.0,
    prior_sd: float = 1.0,
    n_points: int = 61,
    theta_min: float = -4.0,
    theta_max: float = 4.0,
) -> float:
    """Estimate theta via Expected A Posteriori (EAP).

    Uses numerical integration over a grid of theta values with
    a normal prior.

    Args:
        responses: List of (a, b, correct) tuples.
        prior_mean: Mean of the normal prior.
        prior_sd: Standard deviation of the normal prior.
        n_points: Number of quadrature points.
        theta_min: Lower bound of integration grid.
        theta_max: Upper bound of integration grid.

    Returns:
        EAP theta estimate.
    """
    if not responses:
        return prior_mean

    step = (theta_max - theta_min) / (n_points - 1)
    numerator = 0.0
    denominator = 0.0
    max_log_post = -math.inf

    for i in range(n_points):
        t = theta_min + i * step
        log_prior = -0.5 * ((t - prior_mean) / prior_sd) ** 2
        ll = log_likelihood(t, responses)
        log_post = ll + log_prior
        max_log_post = max(max_log_post, log_post)

    # Second pass: compute weighted sums with offset
    for i in range(n_points):
        t = theta_min + i * step
        log_prior = -0.5 * ((t - prior_mean) / prior_sd) ** 2
        ll = log_likelihood(t, responses)
        log_post = ll + log_prior
        w = math.exp(log_post - max_log_post)
        numerator += t * w
        denominator += w

    if denominator < 1e-15:
        return prior_mean

    return numerator / denominator


def standard_error(
    theta: float,
    items: list[tuple[float, float]],
) -> float:
    """Standard error of the theta estimate.

    SE(theta) = 1 / sqrt(sum of Fisher information)

    Args:
        theta: Current theta estimate.
        items: List of (a, b) tuples for administered items.

    Returns:
        Standard error. Returns a large value if information is near zero.
    """
    total_info = sum(fisher_information(theta, a, b) for a, b in items)
    if total_info < 1e-15:
        return 10.0
    return 1.0 / math.sqrt(total_info)


def select_next_item(
    theta: float,
    available_items: list[ItemParams],
    top_k: int = 5,
) -> list[ItemParams]:
    """Select the best next items by maximizing Fisher information.

    Returns up to top_k items sorted by Fisher information (descending).

    Args:
        theta: Current ability estimate.
        available_items: Items not yet administered.
        top_k: Number of top candidates to return.

    Returns:
        List of up to top_k ItemParams, sorted by information (highest first).
    """
    if not available_items:
        return []

    scored = [
        (fisher_information(theta, item.a, item.b), item)
        for item in available_items
    ]
    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored[:top_k]]
