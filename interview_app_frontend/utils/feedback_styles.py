FEEDBACK_STYLES = """
.feedback-main {
    display: grid;
    gap: 1.05rem;
}
.feedback-card {
    border: 1px solid #cad4e5;
    border-radius: 10px;
    overflow: hidden;
    background: #ffffff;
}
.feedback-card__header {
    display: flex;
    align-items: center;
    gap: 0.95rem;
    min-height: 64px;
    padding: 0.8rem 1.15rem 0.7rem;
    background: #f3f6fe;
    border-bottom: 1px solid #cfd9ea;
    flex-wrap: wrap;
}
.feedback-card__header-icon {
    width: 28px;
    height: 28px;
    border-radius: 7px;
    background: #2454c8;
    color: #ffffff;
    position: relative;
}
.feedback-card__header-icon::before {
    content: "!";
    position: absolute;
    inset: 0;
    display: grid;
    place-items: center;
    font-size: 0.95rem;
    font-weight: 800;
}
.feedback-card__header h2 {
    margin: 0;
    color: #2454c8;
    font-size: 1.58rem;
    line-height: 1.05;
    font-weight: 800;
}
.feedback-card__body,
.answer-card__body {
    padding: 1.25rem 1.35rem 1.45rem;
}
.feedback-copy {
    color: #1b2b54;
    font-size: 1.02rem;
    line-height: 1.55;
}
.feedback-answer {
    white-space: pre-wrap;
    overflow-wrap: anywhere;
}
.feedback-section-title {
    margin: 1rem 0 0.55rem;
    color: #2454c8;
    font-size: 1.02rem;
    font-weight: 800;
}
.feedback-breakdown {
    display: grid;
    gap: 0.72rem;
}
.feedback-breakdown-row {
    display: grid;
    grid-template-columns: minmax(176px, 220px) minmax(0, 1fr) max-content;
    gap: 0.8rem;
    align-items: center;
}
.feedback-breakdown-label,
.feedback-breakdown-score {
    color: #14224b;
    font-size: 0.96rem;
    font-weight: 700;
}
.feedback-breakdown-track {
    height: 14px;
    border-radius: 999px;
    background: #e6ebf4;
    overflow: hidden;
}
.feedback-breakdown-fill {
    height: 100%;
    border-radius: inherit;
    background: linear-gradient(90deg, #2f66e6 0%, #5e7dff 100%);
}
.feedback-trust {
    display: grid;
    gap: 0.35rem;
    margin: 0.1rem 0 0.8rem;
    padding: 0.85rem 1rem;
    border-radius: 12px;
    background: #eef4ff;
    border: 1px solid #d6e2ff;
    color: #1d2d52;
}
.feedback-trust__item,
.feedback-trust__note {
    font-size: 0.93rem;
    line-height: 1.4;
}
.feedback-trust__note {
    color: #4d5f86;
}
.feedback-reliability {
    display: grid;
    gap: 0.3rem;
    margin: 0.05rem 0 0.8rem;
    padding: 0.72rem 0.9rem;
    border-radius: 10px;
    background: #f7f9fc;
    border: 1px solid #d9e0ea;
    color: #1d2d52;
}
.feedback-reliability__title {
    font-size: 0.9rem;
    line-height: 1.3;
    font-weight: 800;
    color: #16224a;
}
.feedback-reliability__row,
.feedback-reliability__note {
    font-size: 0.88rem;
    line-height: 1.35;
}
.feedback-reliability__note {
    color: #4d5f86;
}
.feedback-reliability__dot { display: inline-block; width: 0.5rem; height: 0.5rem; margin-right: 0.45rem; border-radius: 999px; vertical-align: middle; }
.feedback-key-takeaway {
    margin: 0 0 0.85rem;
    padding: 0.85rem 1rem;
    border-radius: 12px;
    border: 1px solid #d6e2ff;
    background: #f7faff;
    color: #16356c;
    font-size: 0.95rem;
    line-height: 1.45;
    font-weight: 700;
}
.feedback-consistency {
    margin: 0 0 0.85rem;
    padding: 0.85rem 1rem;
    border-radius: 12px;
    border: 1px solid #f2cf7d;
    background: #fff8e6;
    color: #6b4d10;
    font-size: 0.93rem;
    line-height: 1.45;
}
.feedback-decision-confidence {
    display: inline-flex;
    align-items: center;
    min-height: 1.8rem;
    padding: 0 0.55rem;
    border-radius: 999px;
    background: #eef2ff;
    color: #3730a3;
    font-weight: 800;
}
.feedback-decision-confidence--low {
    background: #fff4db;
    color: #8a5b00;
}
.feedback-decision-confidence--high {
    background: #dff5e7;
    color: #0f5132;
}
.feedback-panel {
    padding: 0.95rem 1rem;
    border: 1px solid #dbe3f0;
    border-radius: 12px;
    background: #f8fbff;
}
.feedback-card__subtitle {
    margin: 0.1rem 0 0 2.55rem;
    color: #4d5f86;
    font-size: 0.82rem;
    line-height: 1.25;
    font-weight: 600;
}
.feedback-panel h3 {
    margin: 0 0 0.7rem;
    color: #14224b;
    font-size: 1rem;
    font-weight: 800;
}
.feedback-list {
    margin: 0;
    padding-left: 1.1rem;
    color: #24324a;
    line-height: 1.5;
}
.feedback-list li + li {
    margin-top: 0.35rem;
}
.feedback-pill-list {
    display: flex;
    flex-wrap: wrap;
    gap: 0.45rem;
}
.feedback-pill {
    display: inline-flex;
    align-items: center;
    min-height: 2rem;
    padding: 0.25rem 0.7rem;
    border-radius: 999px;
    background: #eaf1ff;
    color: #16356c;
    font-size: 0.92rem;
    line-height: 1.2;
    border: 1px solid #d6e2ff;
}
.feedback-empty {
    color: #64748b;
    font-size: 0.92rem;
    line-height: 1.4;
}
.feedback-panel--reasoning {
    margin-top: 0.85rem;
}
.feedback-reasoning p {
    margin: 0 0 0.5rem;
    color: #24324a;
    line-height: 1.45;
}
.feedback-reasoning p:last-child {
    margin-bottom: 0;
}
@media (max-width: 1080px) {
    .feedback-breakdown-row {
        grid-template-columns: 1fr;
        gap: 0.35rem;
    }
}
"""
