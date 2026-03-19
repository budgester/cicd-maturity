from app.services.recommendation_service import (
    RECOMMENDATIONS,
    get_next_level_guidance,
    get_quick_wins,
    get_recommendations,
)


def test_get_recommendations_returns_sorted(sample_assessment):
    recs = get_recommendations(sample_assessment)
    assert len(recs) > 0
    priorities = [r["priority"] for r in recs]
    order = {"high": 0, "medium": 1, "low": 2}
    assert priorities == sorted(priorities, key=lambda p: order[p])


def test_get_recommendations_targets_next_level(sample_assessment):
    recs = get_recommendations(sample_assessment)
    for rec in recs:
        assert rec["target_level"] == rec["current_score"] + 1


def test_get_recommendations_skips_level_5(app, db, sample_pipeline):
    from app.models import MaturityAssessment

    assessment = MaturityAssessment(
        pipeline_id=sample_pipeline.id,
        overall_score=5,
        version_control_score=5,
        build_process_score=5,
        testing_score=5,
        deployment_score=5,
        monitoring_score=5,
        security_score=5,
        configuration_management_score=5,
        feedback_loops_score=5,
    )
    db.session.add(assessment)
    db.session.commit()

    recs = get_recommendations(assessment)
    assert len(recs) == 0


def test_get_next_level_guidance():
    guidance = get_next_level_guidance("version_control", 2)
    assert guidance is not None
    assert "title" in guidance
    assert "actions" in guidance


def test_get_next_level_guidance_at_max():
    assert get_next_level_guidance("version_control", 5) is None


def test_get_quick_wins_returns_max_3(sample_assessment):
    wins = get_quick_wins(sample_assessment)
    assert len(wins) <= 3


def test_all_dimensions_have_recommendations():
    from app.models.pipeline import MaturityAssessment
    for dim in MaturityAssessment.DIMENSIONS:
        assert dim in RECOMMENDATIONS, f"Missing recommendations for {dim}"
        for level in range(2, 6):
            assert level in RECOMMENDATIONS[dim], f"Missing level {level} for {dim}"
