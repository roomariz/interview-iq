QUESTION_STYLES = """
.question-shell {
    display: grid;
    grid-template-columns: minmax(238px, 272px) minmax(0, 1fr);
    gap: 2.25rem;
    align-items: start;
}
.question-sidebar {
    min-height: calc(100vh - 8rem);
    padding: 0.25rem 0 0;
    border-right: 1px solid #e3e8f0;
}
.question-sidebar-brand {
    display: flex;
    align-items: flex-start;
    gap: 0.8rem;
    padding: 0.1rem 0 1.15rem;
    border-bottom: 1px solid #dfe5ee;
    margin: 0 1.1rem 1.1rem 0;
}
.question-sidebar-logo {
    width: 50px;
    height: 50px;
    border-radius: 11px;
    background: #2454c8;
    position: relative;
    flex: 0 0 auto;
}
.question-sidebar-logo::before {
    content: "";
    position: absolute;
    inset: 11px;
    border-radius: 50%;
    background: #ffffff;
}
.question-sidebar-logo::after {
    content: "★";
    position: absolute;
    inset: 0;
    display: grid;
    place-items: center;
    color: #2454c8;
    font-size: 1rem;
    font-weight: 900;
}
.question-sidebar-title {
    color: #12244b;
    font-size: 1.02rem;
    line-height: 1.15;
    font-weight: 800;
    padding-top: 0.1rem;
}
.question-sidebar-section {
    margin: 0.4rem 0 0.75rem;
    color: #5d6d84;
    font-size: 0.86rem;
    font-weight: 800;
    letter-spacing: 0.02em;
    text-transform: uppercase;
}
.question-sidebar-item {
    display: grid;
    grid-template-columns: 22px minmax(0, 1fr);
    gap: 0.8rem;
    margin: 0.82rem 0 1.02rem;
}
.question-sidebar-copy strong,
.question-sidebar-copy span {
    display: block;
}
.question-sidebar-copy strong {
    color: #14224b;
    font-size: 0.97rem;
    font-weight: 700;
    margin-bottom: 0.1rem;
}
.question-sidebar-copy span {
    color: #152446;
    font-size: 0.94rem;
    line-height: 1.28;
}
.question-sidebar-status {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    margin-left: 0.4rem;
    color: #137c3a;
    font-weight: 700;
}
.question-sidebar-status::before {
    content: "✓";
    width: 18px;
    height: 18px;
    border-radius: 50%;
    background: #1f9d53;
    color: #ffffff;
    display: inline-grid;
    place-items: center;
    font-size: 0.75rem;
    line-height: 1;
}
.question-sidebar-button {
    display: flex;
    align-items: center;
    gap: 0.72rem;
    min-height: 52px;
    margin: 0.62rem 0;
    padding: 0.72rem 0.95rem;
    border: 1px solid #dbe2ed;
    border-radius: 8px;
    background: #f7f9fd;
    color: #16224a;
    font-size: 0.98rem;
    font-weight: 700;
}
.question-sidebar-icon,
.question-card__header-icon,
.question-warning__icon {
    display: inline-grid;
    place-items: center;
    flex: 0 0 auto;
}
.question-sidebar-icon {
    width: 22px;
    height: 22px;
    color: #5f6f86;
    position: relative;
}
.question-sidebar-icon::before,
.question-sidebar-icon::after {
    content: "";
    position: absolute;
}
.question-sidebar-icon--briefcase::before {
    inset: 4px 2px 5px;
    border: 1.7px solid currentColor;
    border-radius: 4px;
}
.question-sidebar-icon--briefcase::after {
    left: 7px;
    top: 2px;
    width: 8px;
    height: 4px;
    border: 1.7px solid currentColor;
    border-bottom: 0;
    border-radius: 4px 4px 0 0;
}
.question-sidebar-icon--bars::before {
    left: 4px;
    right: 4px;
    top: 5px;
    height: 2px;
    background: currentColor;
    box-shadow: 0 5px 0 currentColor, 0 10px 0 currentColor;
}
.question-sidebar-icon--user::before {
    left: 6px;
    top: 2px;
    width: 8px;
    height: 8px;
    border: 1.7px solid currentColor;
    border-radius: 50%;
}
.question-sidebar-icon--user::after {
    left: 3px;
    bottom: 2px;
    width: 14px;
    height: 7px;
    border: 1.7px solid currentColor;
    border-top: 0;
    border-radius: 0 0 8px 8px;
}
.question-sidebar-icon--chat::before {
    inset: 4px 3px 5px;
    border: 1.7px solid currentColor;
    border-radius: 4px;
}
.question-sidebar-icon--chat::after {
    left: 7px;
    bottom: 2px;
    width: 6px;
    height: 6px;
    border-left: 1.7px solid currentColor;
    border-bottom: 1.7px solid currentColor;
    transform: rotate(45deg);
}
.question-sidebar-icon--doc::before {
    left: 5px;
    top: 2px;
    width: 11px;
    height: 14px;
    border: 1.7px solid currentColor;
    border-radius: 2px;
}
.question-sidebar-icon--doc::after {
    right: 5px;
    top: 2px;
    width: 5px;
    height: 5px;
    background: currentColor;
    transform: rotate(45deg);
}
.question-sidebar-icon--temp::before {
    left: 8px;
    top: 1px;
    width: 4px;
    height: 13px;
    border: 1.7px solid currentColor;
    border-radius: 3px;
}
.question-sidebar-icon--temp::after {
    left: 5px;
    bottom: 1px;
    width: 10px;
    height: 10px;
    border: 1.7px solid currentColor;
    border-radius: 50%;
}
.question-sidebar-icon--restart::before {
    left: 4px;
    top: 4px;
    width: 12px;
    height: 12px;
    border: 2px solid currentColor;
    border-right-color: transparent;
    border-radius: 50%;
}
.question-sidebar-icon--restart::after {
    right: 2px;
    top: 3px;
    width: 0;
    height: 0;
    border-left: 5px solid currentColor;
    border-top: 4px solid transparent;
    border-bottom: 4px solid transparent;
}
.question-sidebar-icon--exit::before {
    left: 3px;
    top: 4px;
    width: 10px;
    height: 8px;
    border: 1.7px solid currentColor;
    border-left: 0;
}
.question-sidebar-icon--exit::after {
    right: 1px;
    top: 5px;
    width: 8px;
    height: 2px;
    background: currentColor;
    box-shadow: 0 4px 0 currentColor;
}
.question-main {
    display: grid;
    gap: 1.4rem;
}
.question-main--loading {
    filter: blur(2px);
    opacity: 0.28;
    pointer-events: none;
}
.answer-card {
    margin-top: 1.4rem;
}
.question-card,
.answer-card {
    border: 1px solid #ced8e7;
    border-radius: 10px;
    overflow: hidden;
    background: #ffffff;
}
.question-card__header {
    display: flex;
    align-items: center;
    gap: 0.95rem;
    min-height: 80px;
    padding: 1rem 1.3rem;
    background: #f6f8ff;
    border-bottom: 1px solid #d7deea;
}
.question-card__header-icon {
    width: 30px;
    height: 30px;
    border-radius: 8px;
    background: #2454c8;
    position: relative;
    display: grid;
    place-items: center;
    color: #ffffff;
    font-size: 0.78rem;
    font-weight: 900;
}
.question-card__header-icon::before {
    content: "";
    position: absolute;
    left: 7px;
    top: 6px;
    width: 12px;
    height: 12px;
    border: 2px solid #ffffff;
    border-radius: 50%;
}
.question-card__header-icon::after {
    content: "";
    position: absolute;
    left: 12px;
    bottom: 5px;
    width: 5px;
    height: 5px;
    background: #ffffff;
    transform: rotate(45deg);
    border-radius: 1px;
}
.question-card__header h1 {
    margin: 0;
    color: #2454c8;
    font-size: 1.55rem;
    line-height: 1.05;
    font-weight: 800;
}
.question-card__body {
    padding: 1.25rem 1.38rem 1.45rem;
}
.question-card__meta {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.55rem 0.95rem;
    color: #2454c8;
    font-size: 1rem;
}
.question-meta-item {
    display: inline-flex;
    align-items: baseline;
    gap: 0.35rem;
}
.question-card__meta strong,
.question-card__focus strong {
    color: #2454c8;
}
.question-meta-item span {
    color: #14224b;
}
.question-card__divider {
    width: 1px;
    height: 1.1rem;
    background: #2454c8;
    margin: 0 0.2rem;
}
.question-card__focus {
    margin-top: 0.75rem;
    color: #2454c8;
    font-size: 0.98rem;
}
.question-card__question {
    margin-top: 1.15rem;
    padding-top: 1.25rem;
    border-top: 1px solid #e5eaf2;
    color: #1b2b54;
    font-size: clamp(1.42rem, 1.55vw, 1.82rem);
    line-height: 1.5;
    font-weight: 800;
    max-width: 900px;
}
.question-generation-meta {
    margin: 0.6rem 0 0;
    color: #64748b;
    font-size: 0.86rem;
    font-weight: 600;
}
.question-answer-card__title {
    margin: 0 0 1rem;
    color: #16224a;
    font-size: 1.46rem;
    line-height: 1.15;
    font-weight: 800;
}
.answer-card {
    padding: 1.28rem 1.38rem 1.48rem;
}
.answer-card h2 {
    margin: 0 0 1rem;
    color: #16224a;
    font-size: 1.46rem;
    line-height: 1.15;
    font-weight: 800;
}
.question-actions-divider {
    margin: 0.78rem 0 0.85rem;
    border-top: 1px solid #e5eaf2;
}
[data-testid="stElementContainer"].st-key-question_back button,
[data-testid="stElementContainer"].st-key-question_submit_answer button,
[data-testid="stElementContainer"].st-key-question_clear_answer button {
    min-height: 40px;
    padding: 0.45rem 0.75rem;
}
.question-warning {
    display: flex;
    align-items: flex-start;
    gap: 0.8rem;
    margin-bottom: 1rem;
    padding: 0.98rem 1.08rem;
    border: 1px solid #f4deb0;
    border-radius: 8px;
    background: #fff7e6;
    color: #24324a;
    font-size: 0.98rem;
    line-height: 1.45;
}
.question-warning__icon {
    width: 20px;
    height: 20px;
    color: #f2a000;
    font-size: 1.2rem;
    font-weight: 800;
}
.answer-field textarea {
    width: 100%;
    min-height: 208px;
    border: 1px solid #cdd8e8;
    border-radius: 10px;
    padding: 1rem 1.05rem;
    color: #12244b;
    font: inherit;
    font-size: 1rem;
    line-height: 1.5;
    resize: vertical;
}
.answer-field textarea::placeholder {
    color: #677794;
}
.question-count {
    margin-top: 0.85rem;
    color: #66758d;
    font-size: 0.92rem;
}
.question-validation-error {
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
    margin-top: 0.85rem;
    padding: 0.95rem 1rem;
    border: 1px solid #f1b0b7;
    border-radius: 8px;
    background: #fff5f6;
    color: #7a2430;
    font-size: 1rem;
    line-height: 1.45;
}
.question-validation-error__icon {
    width: 20px;
    height: 20px;
    border-radius: 50%;
    background: #d92d20;
    color: #ffffff;
    display: inline-grid;
    place-items: center;
    flex: 0 0 auto;
    font-size: 0.9rem;
    font-weight: 800;
}
.question-actions {
    display: grid;
    grid-template-columns: 220px 122px;
    gap: 1rem;
    margin-top: 1.35rem;
    align-items: center;
}
[data-testid="stElementContainer"].st-key-question_submit_answer button,
[data-testid="stElementContainer"].st-key-question_clear_answer button {
    min-height: 54px;
    border-radius: 8px;
    font-size: 1rem;
    font-weight: 700;
}
[data-testid="stElementContainer"].st-key-question_submit_answer button {
    border: 1px solid #1d4ed8;
    background: #1d4ed8;
    color: #ffffff;
}
[data-testid="stElementContainer"].st-key-question_submit_answer button:disabled {
    opacity: 1;
}
[data-testid="stElementContainer"].st-key-question_clear_answer button {
    border: 1.5px solid #2454c8;
    background: #ffffff;
    color: #2454c8;
}
[data-testid="stTextArea"] textarea[aria-label="Write your answer here..."] {
    min-height: 208px;
    border: 1px solid #cdd8e8;
    border-radius: 10px;
    padding: 1rem 1.05rem;
    color: #12244b;
    font: inherit;
    font-size: 1rem;
    line-height: 1.5;
    resize: vertical;
}
[data-testid="stTextArea"] textarea[aria-label="Write your answer here..."]::placeholder {
    color: #677794;
}
@media (max-width: 1080px) {
    .question-shell {
        grid-template-columns: 1fr;
    }
    .question-sidebar {
        min-height: auto;
        border-right: 0;
        border-bottom: 1px solid #dce3ef;
        padding-bottom: 1rem;
    }
}
"""
